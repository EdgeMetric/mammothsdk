"""Which dataset holds a view, remembered on disk between commands.

Many view commands address a view by its id alone, and the SDK finds the dataset it lives in
with ``GET resources/dataview/{id}`` before the real request. A view never moves to another
dataset, so the answer is kept in the user cache dir and the lookup is skipped next time.

One file per credential: ``view-datasets-<fingerprint>.json``, the fingerprint naming the
token (or key pair), profile, server and workspace, so one credential never reads another's
answers. The file is owner-only (0600) and replaced atomically. The cache is a hint, never
authority: the server checks access on every request. When a request made with a remembered
dataset is answered 404 the entry is dropped and the lookup runs once more (see
``SdkMammothService``). ``auth login`` and ``auth logout`` clear it, and
``MAMMOTH_CLI_VIEW_DATASET_CACHE=0`` (also false, no, off) turns it off.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import cache_dir
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.token_scope import _fingerprint

#: Set to 0, false, no or off to ask the server on every command.
VIEW_DATASET_CACHE_ENV = "MAMMOTH_CLI_VIEW_DATASET_CACHE"
_PREFIX = "view-datasets-"
#: Newest entries kept per credential; the oldest go first.
MAX_ENTRIES = 5000


def cache_enabled() -> bool:
    """False when ``MAMMOTH_CLI_VIEW_DATASET_CACHE`` switches the cache off."""
    value = os.environ.get(VIEW_DATASET_CACHE_ENV, "1")
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _is_id(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


class ViewDatasetStore:
    """One credential's view -> dataset answers, in a file. Implements ``DataviewDatasetStore``."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: dict[str, int] | None = None

    @staticmethod
    def _key(project_id: int, dataview_id: int) -> str:
        return f"{project_id}:{dataview_id}"

    def _read(self) -> dict[str, int]:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            entries = raw["entries"]
            if not isinstance(entries, dict):
                return {}
            return {k: v for k, v in entries.items() if isinstance(k, str) and _is_id(v)}
        except (OSError, ValueError, KeyError, TypeError):
            return {}

    def _loaded(self) -> dict[str, int]:
        if self._entries is None:
            self._entries = self._read()
        return self._entries

    def _write(self, entries: dict[str, int]) -> None:
        """Replace the file atomically, owner-only; a file that cannot be written is skipped."""
        try:
            self._path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self._path.parent, prefix=self._path.name, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump({"entries": entries}, handle)
                os.chmod(tmp, 0o600)
                os.replace(tmp, self._path)
            except BaseException:
                Path(tmp).unlink(missing_ok=True)
                raise
        except OSError:
            return

    def get(self, workspace_id: int, project_id: int, dataview_id: int) -> int | None:
        """The remembered dataset id of a view, or None."""
        return self._loaded().get(self._key(project_id, dataview_id))

    def put(self, workspace_id: int, project_id: int, dataview_id: int, dataset_id: int) -> None:
        """Remember a dataset the server just named (merged with what another process wrote)."""
        key = self._key(project_id, dataview_id)
        if self._loaded().get(key) == dataset_id:
            return
        merged = self._read()
        merged.pop(key, None)  # re-insert last: the newest entry is the last one
        merged[key] = dataset_id
        while len(merged) > MAX_ENTRIES:
            del merged[next(iter(merged))]
        self._entries = merged
        self._write(merged)

    def drop(self, workspace_id: int, project_id: int, dataview_id: int) -> None:
        """Forget a view whose remembered dataset the server contradicted."""
        key = self._key(project_id, dataview_id)
        merged = self._read()
        merged.pop(key, None)
        self._loaded().pop(key, None)
        self._write(merged)


def store_for(auth: ResolvedAuth, profile: str | None) -> ViewDatasetStore | None:
    """The store for this credential, or None (disabled, embedded, or no stable identity)."""
    if embedded.active() or not cache_enabled():
        return None
    try:
        fingerprint = _fingerprint(auth, profile)
    except CliError:
        return None
    if fingerprint is None:
        return None
    return ViewDatasetStore(cache_dir() / f"{_PREFIX}{fingerprint}.json")


def forget_view_datasets() -> None:
    """Drop every remembered answer: a sign-in or sign-out may change what a credential reaches."""
    try:
        for path in cache_dir().glob(f"{_PREFIX}*.json"):
            path.unlink(missing_ok=True)
    except OSError:
        return
