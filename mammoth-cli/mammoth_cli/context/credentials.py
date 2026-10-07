"""Secret credential storage: OS keyring first, permission-checked file second.

Stores a JSON blob ``{"api_token": ...}`` (the ``mm_...`` Bearer token), a
browser login ``{"access": ..., "refresh": ..., "expires_at": ..., "client_id":
...}``, or the deprecated ``{"api_key": ..., "api_secret": ...}`` under keyring service
``mammoth-cli`` with the profile name as username. When no keyring
backend is available, an explicit or interactively-approved fallback stores
the same blob in ``credentials.toml`` beside ``profiles.toml``, with
directory mode ``0700`` and file mode ``0600`` on POSIX. A secret value is
never logged or included in any rendered output.

An OS keyring can block indefinitely: macOS shows a Keychain access dialog
(or cannot, over SSH), and a Linux Secret Service waits on an unlock prompt.
Every keyring call is therefore bounded by a timeout, a store is read back
before it is trusted, and a profile present in the file store is loaded
without touching the keyring at all.
"""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import tomlkit
from tomlkit import TOMLDocument

from mammoth_cli.context import keyring_backend
from mammoth_cli.context.profiles import config_dir
from mammoth_cli.errors.envelope import EXIT_USAGE, CliError

KEYRING_SERVICE = "mammoth-cli"
CREDENTIALS_FILENAME = "credentials.toml"

StorageMode = Literal["auto", "keyring", "file"]

# Backends that exist but cannot hold a credential: ``fail`` refuses every
# call and ``null`` silently discards what it is given.
_UNUSABLE_BACKEND_MODULES = frozenset({"keyring.backends.fail", "keyring.backends.null"})

# Long enough for a person to answer a macOS Keychain dialog; a keyring that
# has not answered by then is treated as unavailable rather than waited on.
KEYRING_TIMEOUT_SECONDS = 60.0
# How long a keyring call may take before the waiting person is told why.
_KEYRING_NOTICE_AFTER_SECONDS = 2.0

# Set once a keyring call times out: its thread is still blocked, so later
# calls in the same process fail fast instead of waiting out another timeout.
_keyring_timed_out = False


class KeyringUnresponsiveError(Exception):
    """The OS keyring raised, timed out, or did not return what was stored."""


def keyring_unavailable_error() -> CliError:
    """Build the stable error for a missing or unusable OS keyring backend."""
    return CliError(
        code="keyring_unavailable",
        message="No OS keyring is available to store the credential.",
        exit_status=EXIT_USAGE,
        hint="Store the credential in a permission-checked file instead.",
        recovery_commands=["mammoth auth login --storage file"],
    )


def keyring_unresponsive_error() -> CliError:
    """Build the stable error for an OS keyring that hung, failed, or lost data."""
    return CliError(
        code="keyring_unresponsive",
        message="The OS keyring did not respond or could not be used for the credential.",
        exit_status=EXIT_USAGE,
        hint=(
            "On macOS, unlock the login keychain and choose 'Always Allow' when asked "
            "about 'mammoth-cli'; over SSH the Keychain cannot prompt. Or store the "
            "credential in a permission-checked file instead."
        ),
        recovery_commands=["mammoth auth login --storage file"],
    )


def _keyring_available() -> bool:
    import keyring
    import keyring.errors

    keyring_backend.install_cached()
    try:
        backend = keyring.get_keyring()
    except keyring.errors.NoKeyringError:
        return False
    usable = type(backend).__module__ not in _UNUSABLE_BACKEND_MODULES
    if usable:
        keyring_backend.remember(backend)
    return usable


def _bounded_keyring_call[T](call: Callable[[], T]) -> T:
    """Run one keyring call with a timeout, surfacing any failure uniformly.

    The call runs on a daemon thread so a keyring that never answers cannot
    hold the process past the timeout. When it is slow, a one-line notice on
    an interactive stderr says what is being waited on.

    Raises:
        KeyringUnresponsiveError: The call raised or did not finish in time.
    """
    global _keyring_timed_out
    if _keyring_timed_out:
        raise KeyringUnresponsiveError("timed out earlier")
    outcome: dict[str, object] = {}

    def _run() -> None:
        try:
            outcome["value"] = call()
        except BaseException as exc:  # noqa: BLE001 - re-raised as one failure type
            outcome["error"] = exc

    worker = threading.Thread(target=_run, name="mammoth-keyring", daemon=True)
    worker.start()
    worker.join(_KEYRING_NOTICE_AFTER_SECONDS)
    if worker.is_alive():
        if sys.stderr.isatty():
            sys.stderr.write(
                "Waiting for the OS keyring. On macOS, answer the Keychain dialog "
                "for 'mammoth-cli' (choose Always Allow)...\n"
            )
            sys.stderr.flush()
        worker.join(max(KEYRING_TIMEOUT_SECONDS - _KEYRING_NOTICE_AFTER_SECONDS, 0.0))
    if worker.is_alive():
        _keyring_timed_out = True
        raise KeyringUnresponsiveError("timed out")
    if "error" in outcome:
        raise KeyringUnresponsiveError(type(outcome["error"]).__name__)
    return outcome["value"]  # type: ignore[return-value]


@dataclass(frozen=True)
class OAuthSession:
    """A browser login's tokens: a short-lived access token and its refresh token.

    ``expires_at`` is a Unix timestamp in whole seconds. ``grant_id`` is the
    server-side connection id, used to revoke it on logout. ``workspace_id`` and
    ``project_id`` are the scope the server pinned the grant to at login; they are
    adopted into the profile then and are not stored with the credential.
    """

    access: str
    refresh: str
    expires_at: int
    client_id: str
    grant_id: int | None = None
    workspace_id: int | None = None
    project_id: int | None = None

    def document(self) -> dict[str, str | int]:
        document: dict[str, str | int] = {
            "access": self.access,
            "refresh": self.refresh,
            "expires_at": self.expires_at,
            "client_id": self.client_id,
        }
        if self.grant_id is not None:
            document["grant_id"] = self.grant_id
        return document

    @classmethod
    def from_document(cls, data: Any) -> OAuthSession | None:
        access, refresh = data.get("access"), data.get("refresh")
        expires_at, client_id = data.get("expires_at"), data.get("client_id")
        if not (access and refresh and client_id) or isinstance(expires_at, bool):
            return None
        if not isinstance(expires_at, int):
            return None
        grant_id = data.get("grant_id")
        return cls(
            access=str(access),
            refresh=str(refresh),
            expires_at=expires_at,
            client_id=str(client_id),
            grant_id=int(grant_id) if isinstance(grant_id, int) else None,
        )


@dataclass(frozen=True)
class Credential:
    """One stored credential: a Bearer token, a browser login, or a deprecated key + secret."""

    api_token: str | None = None
    api_key: str | None = None
    api_secret: str | None = None
    oauth: OAuthSession | None = None

    def __post_init__(self) -> None:
        if self.oauth is not None:
            if (
                self.api_token is not None
                or self.api_key is not None
                or self.api_secret is not None
            ):
                raise ValueError("a credential is one of: oauth session, token, key + secret")
        elif self.api_token is not None:
            if self.api_key is not None or self.api_secret is not None:
                raise ValueError("a credential is a token or a key + secret, not both")
        elif not self.api_key or not self.api_secret:
            raise ValueError("a credential needs a token or both a key and a secret")

    @property
    def kind(self) -> str:
        """``"oauth"``, ``"token"`` or ``"key_secret"`` (never the value)."""
        if self.oauth is not None:
            return "oauth"
        return "token" if self.api_token is not None else "key_secret"

    def document(self) -> dict[str, str | int]:
        if self.oauth is not None:
            return self.oauth.document()
        if self.api_token is not None:
            return {"api_token": self.api_token}
        return {"api_key": str(self.api_key), "api_secret": str(self.api_secret)}

    @classmethod
    def from_document(cls, data: Any) -> Credential | None:
        if not hasattr(data, "get"):
            return None
        session = OAuthSession.from_document(data)
        if session is not None:
            return cls(oauth=session)
        token = data.get("api_token")
        if token:
            return cls(api_token=str(token))
        key, secret = data.get("api_key"), data.get("api_secret")
        if key and secret:
            return cls(api_key=str(key), api_secret=str(secret))
        return None


def credentials_path() -> Path:
    """Return the path to the file-fallback credential store."""
    return config_dir() / CREDENTIALS_FILENAME


def _store_keyring(profile: str, credential: Credential) -> None:
    """Store and read back one credential; a keyring that loses it is unusable.

    Raises:
        KeyringUnresponsiveError: The keyring hung, raised, or did not return
            the stored credential.
    """
    import keyring

    payload = json.dumps(credential.document())
    _bounded_keyring_call(lambda: keyring.set_password(KEYRING_SERVICE, profile, payload))
    stored = _bounded_keyring_call(lambda: keyring.get_password(KEYRING_SERVICE, profile))
    if stored != payload:
        raise KeyringUnresponsiveError("read-back mismatch")


def _load_keyring(profile: str) -> Credential | None:
    """Load one credential from the keyring.

    Raises:
        KeyringUnresponsiveError: The keyring hung or raised.
    """
    import keyring

    raw = _bounded_keyring_call(lambda: keyring.get_password(KEYRING_SERVICE, profile))
    if raw is None:
        return None
    return Credential.from_document(json.loads(raw))


def _delete_keyring(profile: str) -> bool:
    import keyring

    try:
        _bounded_keyring_call(lambda: keyring.delete_password(KEYRING_SERVICE, profile))
        return True
    except KeyringUnresponsiveError:
        return False


def _insecure_file_error(reason: str) -> CliError:
    """Return a secret-safe error for an unsafe POSIX credential store."""
    return CliError(
        code="insecure_credential_file",
        message="The file-backed credential store is not safe to use.",
        exit_status=EXIT_USAGE,
        hint=(
            f"Secure {credentials_path().parent} and its credential file: "
            "the directory and file must be owned by this user and private "
            "(mode 0700/0600)."
        ),
        details={"reason": reason},
    )


def _check_private_directory(directory: Path) -> None:
    """Reject an unsafe config directory without changing its permissions."""
    try:
        directory_stat = os.lstat(directory)
    except FileNotFoundError:
        return
    except OSError:
        raise _insecure_file_error("directory_unreadable") from None
    if not stat.S_ISDIR(directory_stat.st_mode):
        raise _insecure_file_error("directory_not_directory")
    if directory_stat.st_uid != os.geteuid():
        raise _insecure_file_error("directory_wrong_owner")
    if directory_stat.st_mode & 0o077:
        raise _insecure_file_error("directory_permissions")


def _read_file_bytes(path: Path) -> bytes | None:
    """Read the credential file with POSIX ownership and race checks."""
    directory_fd = -1
    fd = -1
    try:
        directory_flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_DIRECTORY", 0)
        )
        directory_fd = os.open(path.parent, directory_flags)
    except FileNotFoundError:
        return None
    except OSError:
        raise _insecure_file_error("file_unreadable") from None
    try:
        directory_stat = os.fstat(directory_fd)
        if not stat.S_ISDIR(directory_stat.st_mode):
            raise _insecure_file_error("directory_not_directory")
        if directory_stat.st_uid != os.geteuid():
            raise _insecure_file_error("directory_wrong_owner")
        if directory_stat.st_mode & 0o077:
            raise _insecure_file_error("directory_permissions")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path.name, flags, dir_fd=directory_fd)
        except FileNotFoundError:
            return None
        except OSError:
            raise _insecure_file_error("file_unreadable") from None
        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            raise _insecure_file_error("file_not_regular")
        if file_stat.st_uid != os.geteuid():
            raise _insecure_file_error("file_wrong_owner")
        if file_stat.st_mode & 0o077:
            raise _insecure_file_error("file_permissions")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            raw = handle.read()
        # The file descriptor cannot be redirected, but make the corresponding
        # path-entry identity explicit before the caller parses its contents.
        # This also detects a replacement between open and validation.
        try:
            path_stat = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError:
            raise _insecure_file_error("file_identity_changed") from None
        if (path_stat.st_dev, path_stat.st_ino) != (file_stat.st_dev, file_stat.st_ino):
            raise _insecure_file_error("file_identity_changed")
        if not stat.S_ISREG(path_stat.st_mode):
            raise _insecure_file_error("file_not_regular")
        if path_stat.st_uid != os.geteuid():
            raise _insecure_file_error("file_wrong_owner")
        if path_stat.st_mode & 0o077:
            raise _insecure_file_error("file_permissions")
        return raw
    finally:
        if fd != -1:
            os.close(fd)
        if directory_fd != -1:
            os.close(directory_fd)


def _load_file_document() -> TOMLDocument:
    path = credentials_path()
    if os.name != "posix":
        if not path.exists():
            return tomlkit.document()
        return tomlkit.parse(path.read_text(encoding="utf-8"))
    raw = _read_file_bytes(path)
    if raw is None:
        return tomlkit.document()
    return tomlkit.parse(raw.decode("utf-8"))


def _write_file_document(document: TOMLDocument) -> None:
    directory = config_dir()
    directory.mkdir(mode=stat.S_IRWXU, parents=True, exist_ok=True)
    if os.name == "posix":
        _check_private_directory(directory)
        os.chmod(directory, stat.S_IRWXU)
    fd, tmp_name = tempfile.mkstemp(dir=str(directory), prefix=".credentials-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(tomlkit.dumps(document))
        if os.name == "posix":
            os.chmod(tmp_name, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_name, credentials_path())
    except BaseException:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def _store_file(profile: str, credential: Credential) -> None:
    document = _load_file_document()
    table = document.get("profiles")
    if table is None:
        table = tomlkit.table()
        document["profiles"] = table
    entry = tomlkit.table()
    for field, value in credential.document().items():
        entry[field] = value
    table[profile] = entry
    _write_file_document(document)


def _load_file(profile: str) -> Credential | None:
    document = _load_file_document()
    table = document.get("profiles")
    if not table or profile not in table:
        return None
    return Credential.from_document(table[profile])


def _delete_file(profile: str) -> bool:
    document = _load_file_document()
    table = document.get("profiles")
    if not table or profile not in table:
        return False
    del table[profile]
    if table:
        _write_file_document(document)
    else:
        credentials_path().unlink()
    return True


def store_credentials(
    profile: str,
    api_key: str | None = None,
    api_secret: str | None = None,
    storage: StorageMode = "auto",
    *,
    interactive: bool = False,
    api_token: str | None = None,
    oauth: OAuthSession | None = None,
) -> str:
    """Store one profile's secret credential.

    Args:
        profile: The (already-validated) profile name.
        api_key: The deprecated Mammoth API key (with ``api_secret``).
        api_secret: The deprecated Mammoth API secret (with ``api_key``).
        storage: ``"auto"`` prefers the OS keyring and falls back to the file
            store only when interactive; ``"keyring"`` requires the keyring;
            ``"file"`` uses the permission-checked fallback file explicitly.
        interactive: Whether the current process has an interactive TTY.
            Only consulted by ``"auto"`` when no keyring backend exists.
        api_token: The ``mm_...`` Bearer token, instead of a key + secret.
        oauth: A browser login's tokens, instead of a token or key + secret.

    Returns:
        The storage backend actually used: ``"keyring"`` or ``"file"``.

    Raises:
        CliError: ``keyring_unavailable`` when keyring storage is required (or
            selected by ``"auto"`` noninteractively) but no backend exists;
            ``keyring_unresponsive`` when the keyring hangs, fails, or loses
            the credential and no file fallback is allowed.
    """
    credential = Credential(
        api_token=api_token, api_key=api_key, api_secret=api_secret, oauth=oauth
    )
    if storage == "file":
        _store_file(profile, credential)
        return "file"
    if storage == "keyring":
        if not _keyring_available():
            raise keyring_unavailable_error()
        try:
            _store_keyring(profile, credential)
        except KeyringUnresponsiveError:
            raise keyring_unresponsive_error() from None
        _delete_file(profile)
        return "keyring"
    if _keyring_available():
        try:
            _store_keyring(profile, credential)
        except KeyringUnresponsiveError:
            if not interactive:
                raise keyring_unresponsive_error() from None
            sys.stderr.write(
                "The OS keyring did not respond; storing the credential in "
                f"{credentials_path()} (owner-only) instead.\n"
            )
        else:
            # The file store is read first, so a stale file entry would
            # otherwise shadow the credential just stored in the keyring.
            _delete_file(profile)
            return "keyring"
    if interactive:
        _store_file(profile, credential)
        return "file"
    raise keyring_unavailable_error()


def load_credential(profile: str) -> Credential | None:
    """Load one profile's secret credential (token or key + secret).

    Tries the file store first, so a file-stored profile never waits on the
    OS keyring, then the keyring.

    Raises:
        CliError: ``keyring_unresponsive`` when the keyring hangs or fails.
    """
    found = _load_file(profile)
    if found is not None:
        return found
    if not _keyring_available():
        return None
    try:
        return _load_keyring(profile)
    except KeyringUnresponsiveError:
        raise keyring_unresponsive_error() from None


def replace_oauth_session(profile: str, session: OAuthSession) -> str:
    """Overwrite a profile's OAuth session in the backend that already holds it.

    A refresh must not move the credential between the keyring and the file.

    Returns:
        ``"file"`` or ``"keyring"``, the backend written.

    Raises:
        CliError: ``keyring_unresponsive`` when the keyring hangs or fails.
    """
    credential = Credential(oauth=session)
    if _load_file(profile) is not None:
        _store_file(profile, credential)
        return "file"
    try:
        _store_keyring(profile, credential)
    except KeyringUnresponsiveError:
        raise keyring_unresponsive_error() from None
    return "keyring"


def load_credentials(profile: str) -> tuple[str, str] | None:
    """Load a profile's deprecated ``(api_key, api_secret)`` pair.

    Returns None for a token credential; use :func:`load_credential`.
    """
    credential = load_credential(profile)
    if credential is None or credential.api_token is not None:
        return None
    return str(credential.api_key), str(credential.api_secret)


def has_credentials(profile: str) -> bool:
    """Return True if a secret credential is stored for ``profile``.

    Args:
        profile: The profile name.

    Raises:
        CliError: ``keyring_unresponsive`` when the keyring hangs or fails.
    """
    return load_credential(profile) is not None


def delete_credentials(profile: str) -> bool:
    """Delete one profile's secret credential from both backends.

    Args:
        profile: The profile name.

    Returns:
        True if a credential was removed from either backend.
    """
    removed_file = _delete_file(profile)
    removed_keyring = _delete_keyring(profile) if _keyring_available() else False
    return removed_keyring or removed_file
