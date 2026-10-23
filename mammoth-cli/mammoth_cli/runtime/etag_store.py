"""The bodies of ETag'd reads, kept on disk so the next command can revalidate them.

The SDK sends ``If-None-Match`` on a read it has a tag for and reuses the kept body on a
304 (:mod:`mammoth.etag`). Its default store lives as long as the client, which for the
CLI is one command. This store keeps them between commands, so an agent that lists the
same projects, datasets or views again downloads them only when they changed.

One directory per credential: ``etags-<fingerprint>/``, the fingerprint naming the token
(or key pair, or OAuth connection), profile, server and workspace, so one credential
never reads another's bodies. One file per URL, owner-only (0600), replaced atomically:
a JSON header line (tag, content type), then the body. The server decides freshness on
every read; a write through this credential empties the directory first (the SDK calls
:meth:`DiskETagStore.clear`). ``auth login`` and ``auth logout`` remove every directory,
and ``MAMMOTH_CLI_ETAG_CACHE=0`` (also false, no, off) keeps the bodies in memory only.

An embedded call never touches the disk: its host serves many users from one process.
The host's :class:`~mammoth_cli.runtime.embed_pool.EmbedRuntime` keeps one cache in
memory, and each caller reads and writes only their own scope of it, named by a digest
of their credential (:func:`caller_scope`). The scope matters for correctness, not only
privacy: a listing's tag names the listed resource, while its body is filtered by the
caller's permissions, so two users can hold the same tag for different bodies.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from mammoth.etag import MAX_BODY_BYTES, CachedResponse, ETagCache

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import cache_dir
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.embed_pool import EmbedRuntime
from mammoth_cli.runtime.switches import switched_on
from mammoth_cli.runtime.token_scope import _fingerprint

#: Set to 0, false, no or off to keep the bodies for one command only.
ETAG_CACHE_ENV = "MAMMOTH_CLI_ETAG_CACHE"
_PREFIX = "etags-"
#: Forwarded headers that carry a caller's credential, and so name the caller.
_CREDENTIAL_HEADERS = frozenset({"authorization", "cookie", "x-api-key", "x-api-secret"})
#: Most files kept per credential; the least recently written go first.
MAX_ENTRIES = 500


class DiskETagStore:
    """One credential's ETag'd bodies, one file per URL. Implements ``mammoth.etag.ETagCache``.

    Args:
        directory: The credential's own directory; created on the first write.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def _path(self, key: str) -> Path:
        return self._directory / (hashlib.sha256(key.encode()).hexdigest()[:32] + ".etag")

    def get(self, key: str) -> CachedResponse | None:
        """Return the body kept for ``key``.

        Args:
            key: The full request URL, query string included.

        Returns:
            The kept tag and body, or None when there is none or the file is unreadable.
        """
        try:
            raw = self._path(key).read_bytes()
            header, _, content = raw.partition(b"\n")
            meta = json.loads(header)
            if meta.get("key") != key or not isinstance(meta.get("etag"), str):
                return None
            content_type = meta.get("content_type")
            return CachedResponse(
                etag=meta["etag"],
                content=content,
                headers={"content-type": content_type} if isinstance(content_type, str) else {},
            )
        except (OSError, ValueError, AttributeError):
            return None

    def put(self, key: str, response: CachedResponse) -> None:
        """Keep ``response`` for ``key``; a file that cannot be written is skipped.

        Args:
            key: The full request URL, query string included.
            response: The tag and body to keep.
        """
        if len(response.content) > MAX_BODY_BYTES:
            return
        header = {
            "key": key,
            "etag": response.etag,
            "content_type": response.headers.get("content-type"),
        }
        path = self._path(key)
        try:
            self._directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self._directory, prefix=path.name, suffix=".tmp")
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(json.dumps(header).encode() + b"\n" + response.content)
                # mkstemp creates the file 0600: owner-only from the start.
                os.replace(tmp, path)
            except BaseException:
                Path(tmp).unlink(missing_ok=True)
                raise
            self._prune()
        except OSError:
            return

    def clear(self) -> None:
        """Drop every kept body of this credential: a write may have changed any of them."""
        shutil.rmtree(self._directory, ignore_errors=True)

    def _prune(self) -> None:
        files = list(self._directory.glob("*.etag"))
        if len(files) <= MAX_ENTRIES:
            return
        files.sort(key=lambda found: found.stat().st_mtime)
        for stale in files[: len(files) - MAX_ENTRIES]:
            stale.unlink(missing_ok=True)


def store_for(auth: ResolvedAuth, profile: str | None) -> DiskETagStore | None:
    """Return the store for this credential.

    Args:
        auth: The resolved credential.
        profile: The profile it came from, if any.

    Returns:
        The credential's store, or None when the cache is switched off, the call is
        embedded (one process serves many users), or the credential has no stable identity.
    """
    if embedded.active() or not switched_on(ETAG_CACHE_ENV):
        return None
    try:
        fingerprint = _fingerprint(auth, profile)
    except CliError:
        return None
    if fingerprint is None:
        return None
    return DiskETagStore(cache_dir() / f"{_PREFIX}{fingerprint}")


def forget_etags() -> None:
    """Drop every kept body: a sign-in or sign-out may change what a credential reaches."""
    try:
        for directory in cache_dir().glob(f"{_PREFIX}*"):
            shutil.rmtree(directory, ignore_errors=True)
    except OSError:
        return


def caller_scope(auth: ResolvedAuth) -> str | None:
    """Name the caller of an embedded call, for their scope of the runtime's cache.

    Args:
        auth: The call's resolved credential.

    Returns:
        A digest of the credential (token, key pair or forwarded credential headers),
        server and workspace; None when the call carries no credential to name it by.
    """
    material = [
        f"{name.lower()}={value}"
        for name, value in sorted((auth.headers or {}).items())
        if name.lower() in _CREDENTIAL_HEADERS
    ]
    if auth.api_token is not None:
        material.append(f"token={auth.api_token}")
    if auth.api_key is not None:
        material.append(f"key={auth.api_key}:{auth.api_secret}")
    if not material:
        return None
    parts = (*material, auth.base_url, str(auth.workspace_id))
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()[:32]


def cache_for(
    auth: ResolvedAuth, profile: str | None, runtime: EmbedRuntime | None
) -> ETagCache | None:
    """Choose where a service keeps its ETag'd bodies.

    Args:
        auth: The resolved credential.
        profile: The profile it came from, if any.
        runtime: The embedding host's shared runtime, for an embedded call that has one.

    Returns:
        The caller's scope of the host's cache for an embedded call, this credential's
        disk store for a CLI command, or None to keep the SDK's own in-memory cache.
    """
    if embedded.active():
        if runtime is None:
            return None
        scope = caller_scope(auth)
        return runtime.etag_cache.scoped(scope) if scope is not None else None
    return store_for(auth, profile)
