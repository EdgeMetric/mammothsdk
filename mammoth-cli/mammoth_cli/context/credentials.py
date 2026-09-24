"""Secret credential storage: OS keyring first, permission-checked file second.

Stores a JSON blob ``{"api_key": ..., "api_secret": ...}`` under keyring
service ``mammoth-cli`` with the profile name as username. When no keyring
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
from pathlib import Path
from typing import Literal

import keyring
import keyring.errors
import tomlkit
from tomlkit import TOMLDocument

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
    try:
        backend = keyring.get_keyring()
    except keyring.errors.NoKeyringError:
        return False
    return type(backend).__module__ not in _UNUSABLE_BACKEND_MODULES


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


def credentials_path() -> Path:
    """Return the path to the file-fallback credential store."""
    return config_dir() / CREDENTIALS_FILENAME


def _store_keyring(profile: str, api_key: str, api_secret: str) -> None:
    """Store and read back one credential; a keyring that loses it is unusable.

    Raises:
        KeyringUnresponsiveError: The keyring hung, raised, or did not return
            the stored credential.
    """
    payload = json.dumps({"api_key": api_key, "api_secret": api_secret})
    _bounded_keyring_call(lambda: keyring.set_password(KEYRING_SERVICE, profile, payload))
    stored = _bounded_keyring_call(lambda: keyring.get_password(KEYRING_SERVICE, profile))
    if stored != payload:
        raise KeyringUnresponsiveError("read-back mismatch")


def _load_keyring(profile: str) -> tuple[str, str] | None:
    """Load one credential from the keyring.

    Raises:
        KeyringUnresponsiveError: The keyring hung or raised.
    """
    raw = _bounded_keyring_call(lambda: keyring.get_password(KEYRING_SERVICE, profile))
    if raw is None:
        return None
    data = json.loads(raw)
    return str(data["api_key"]), str(data["api_secret"])


def _delete_keyring(profile: str) -> bool:
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


def _store_file(profile: str, api_key: str, api_secret: str) -> None:
    document = _load_file_document()
    table = document.get("profiles")
    if table is None:
        table = tomlkit.table()
        document["profiles"] = table
    entry = tomlkit.table()
    entry["api_key"] = api_key
    entry["api_secret"] = api_secret
    table[profile] = entry
    _write_file_document(document)


def _load_file(profile: str) -> tuple[str, str] | None:
    document = _load_file_document()
    table = document.get("profiles")
    if not table or profile not in table:
        return None
    entry = table[profile]
    return str(entry["api_key"]), str(entry["api_secret"])


def _delete_file(profile: str) -> bool:
    document = _load_file_document()
    table = document.get("profiles")
    if not table or profile not in table:
        return False
    del table[profile]
    _write_file_document(document)
    return True


def store_credentials(
    profile: str,
    api_key: str,
    api_secret: str,
    storage: StorageMode = "auto",
    *,
    interactive: bool = False,
) -> str:
    """Store one profile's secret credential.

    Args:
        profile: The (already-validated) profile name.
        api_key: The Mammoth API key.
        api_secret: The Mammoth API secret.
        storage: ``"auto"`` prefers the OS keyring and falls back to the file
            store only when interactive; ``"keyring"`` requires the keyring;
            ``"file"`` uses the permission-checked fallback file explicitly.
        interactive: Whether the current process has an interactive TTY.
            Only consulted by ``"auto"`` when no keyring backend exists.

    Returns:
        The storage backend actually used: ``"keyring"`` or ``"file"``.

    Raises:
        CliError: ``keyring_unavailable`` when keyring storage is required (or
            selected by ``"auto"`` noninteractively) but no backend exists;
            ``keyring_unresponsive`` when the keyring hangs, fails, or loses
            the credential and no file fallback is allowed.
    """
    if storage == "file":
        _store_file(profile, api_key, api_secret)
        return "file"
    if storage == "keyring":
        if not _keyring_available():
            raise keyring_unavailable_error()
        try:
            _store_keyring(profile, api_key, api_secret)
        except KeyringUnresponsiveError:
            raise keyring_unresponsive_error() from None
        _delete_file(profile)
        return "keyring"
    if _keyring_available():
        try:
            _store_keyring(profile, api_key, api_secret)
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
        _store_file(profile, api_key, api_secret)
        return "file"
    raise keyring_unavailable_error()


def load_credentials(profile: str) -> tuple[str, str] | None:
    """Load one profile's secret credential.

    Tries the file store first, so a file-stored profile never waits on the
    OS keyring, then the keyring.

    Args:
        profile: The profile name.

    Returns:
        ``(api_key, api_secret)`` if a credential is stored, else None.

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


def has_credentials(profile: str) -> bool:
    """Return True if a secret credential is stored for ``profile``.

    Args:
        profile: The profile name.

    Raises:
        CliError: ``keyring_unresponsive`` when the keyring hangs or fails.
    """
    return load_credentials(profile) is not None


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
