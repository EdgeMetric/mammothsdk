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


def _load_file_document() -> TOMLDocument:
    path = credentials_path()
    if not path.exists():
        return tomlkit.document()
    return tomlkit.parse(path.read_text(encoding="utf-8"))


def _write_file_document(document: TOMLDocument) -> None:
    directory = config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
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
    removed_keyring = _delete_keyring(profile) if _keyring_available() else False
    removed_file = _delete_file(profile)
    return removed_keyring or removed_file
