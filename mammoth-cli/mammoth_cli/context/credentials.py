"""Secret credential storage: OS keyring first, permission-checked file second.

Stores a JSON blob ``{"api_key": ..., "api_secret": ...}`` under keyring
service ``mammoth-cli`` with the profile name as username. When no keyring
backend is available, an explicit or interactively-approved fallback stores
the same blob in ``credentials.toml`` beside ``profiles.toml``, with
directory mode ``0700`` and file mode ``0600`` on POSIX. A secret value is
never logged or included in any rendered output.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
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

_FAIL_BACKEND_MODULE = "keyring.backends.fail"


def keyring_unavailable_error() -> CliError:
    """Build the stable error for a missing or unusable OS keyring backend."""
    return CliError(
        code="keyring_unavailable",
        message="No OS keyring is available to store the credential.",
        exit_status=EXIT_USAGE,
        hint="Store the credential in a permission-checked file instead.",
        recovery_commands=["mammoth auth login --storage file"],
    )


def _keyring_available() -> bool:
    try:
        backend = keyring.get_keyring()
    except keyring.errors.NoKeyringError:
        return False
    return type(backend).__module__ != _FAIL_BACKEND_MODULE


def credentials_path() -> Path:
    """Return the path to the file-fallback credential store."""
    return config_dir() / CREDENTIALS_FILENAME


def _store_keyring(profile: str, api_key: str, api_secret: str) -> None:
    payload = json.dumps({"api_key": api_key, "api_secret": api_secret})
    keyring.set_password(KEYRING_SERVICE, profile, payload)


def _load_keyring(profile: str) -> tuple[str, str] | None:
    try:
        raw = keyring.get_password(KEYRING_SERVICE, profile)
    except keyring.errors.KeyringError:
        return None
    if raw is None:
        return None
    data = json.loads(raw)
    return str(data["api_key"]), str(data["api_secret"])


def _delete_keyring(profile: str) -> bool:
    try:
        keyring.delete_password(KEYRING_SERVICE, profile)
        return True
    except keyring.errors.KeyringError:
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
            selected by ``"auto"`` noninteractively) but no backend exists.
    """
    if storage == "file":
        _store_file(profile, api_key, api_secret)
        return "file"
    if storage == "keyring":
        if not _keyring_available():
            raise keyring_unavailable_error()
        _store_keyring(profile, api_key, api_secret)
        return "keyring"
    if _keyring_available():
        _store_keyring(profile, api_key, api_secret)
        return "keyring"
    if interactive:
        _store_file(profile, api_key, api_secret)
        return "file"
    raise keyring_unavailable_error()


def load_credentials(profile: str) -> tuple[str, str] | None:
    """Load one profile's secret credential.

    Tries the OS keyring first, then the file fallback.

    Args:
        profile: The profile name.

    Returns:
        ``(api_key, api_secret)`` if a credential is stored, else None.
    """
    if _keyring_available():
        found = _load_keyring(profile)
        if found is not None:
            return found
    return _load_file(profile)


def has_credentials(profile: str) -> bool:
    """Return True if a secret credential is stored for ``profile``.

    Args:
        profile: The profile name.
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
