"""Non-secret profile store.

Stores named profiles (workspace id, optional one-label server prefix, active
project id) and profile-scoped settings (output mode, timeouts) in
``platformdirs.user_config_dir("mammoth-cli", "Mammoth")/profiles.toml``,
plus a top-level ``selected`` profile pointer. Secrets never live here; see
:mod:`mammoth_cli.context.credentials`. Writes are atomic (temp file plus
``os.replace``) and, on POSIX, the directory is mode ``0700`` and the file is
mode ``0600``.
"""

from __future__ import annotations

import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import platformdirs
import tomlkit
from tomlkit import TOMLDocument

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError

PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
DEFAULT_PROFILE_NAME = "default"
PROFILES_FILENAME = "profiles.toml"

# A canonical Mammoth endpoint, e.g. ``https://release.mammoth.io/api/v2``. A
# legacy profile that stored such a base url is migrated to its server prefix on
# load; any other stored base url is unsupported and rejected explicitly rather
# than silently dropped (which would redirect the profile to the app-eu
# default). The trailing ``/api/v2`` and optional slash mirror
# :func:`mammoth_cli.context.endpoint.resolve_base_url`.
_CANONICAL_BASE_URL_RE = re.compile(
    r"^https://(?P<prefix>[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)\.mammoth\.io/api/v2/?$"
)


def _server_prefix_from_legacy_base_url(profile_name: str, base_url: str) -> str:
    """Migrate a legacy stored ``base_url`` to its server prefix, or reject it.

    Args:
        profile_name: The profile whose record carried the legacy base url.
        base_url: The stored legacy base url.

    Returns:
        The server prefix extracted from a canonical Mammoth url.

    Raises:
        CliError: ``unsupported_profile_base_url`` when ``base_url`` is not a
            canonical Mammoth endpoint and therefore cannot be represented by a
            server prefix.
    """
    match = _CANONICAL_BASE_URL_RE.match(base_url)
    if match is not None:
        return match.group("prefix")
    raise CliError(
        code="unsupported_profile_base_url",
        message=(
            f"Profile '{profile_name}' has an unsupported legacy base_url "
            f"'{base_url}'. The CLI now configures endpoints by server prefix only."
        ),
        exit_status=EXIT_USAGE,
        hint=(
            f"Edit {profiles_path()}: remove the profile's base_url and set a "
            "one-label server_prefix (for example server_prefix = 'app-eu')."
        ),
    )


@dataclass(frozen=True)
class ProfileRecord:
    """One non-secret profile record.

    Attributes:
        name: The profile name.
        workspace_id: The Mammoth workspace id.
        server_prefix: A one-label server prefix, or None (default ``app-eu``).
        project_id: The active project id, or None.
    """

    name: str
    workspace_id: int
    server_prefix: str | None = None
    project_id: int | None = None


def validate_profile_name(name: str) -> None:
    """Validate a profile name against the reviewed naming rule.

    Args:
        name: The candidate profile name.

    Raises:
        CliError: ``invalid_profile_name`` when the name does not match
            ``[A-Za-z0-9][A-Za-z0-9._-]{0,63}``.
    """
    if not PROFILE_NAME_RE.match(name):
        raise CliError(
            code="invalid_profile_name",
            message=f"'{name}' is not a valid profile name.",
            exit_status=EXIT_USAGE,
            hint="Use letters, digits, '.', '_' or '-'; start with a letter or digit.",
        )


def config_dir() -> Path:
    """Return the platform-native configuration directory for the CLI."""
    return Path(platformdirs.user_config_dir("mammoth-cli", "Mammoth"))


def profiles_path() -> Path:
    """Return the path to the non-secret profiles file."""
    return config_dir() / PROFILES_FILENAME


def _ensure_config_dir() -> Path:
    directory = config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        os.chmod(directory, stat.S_IRWXU)
    return directory


def _load_document() -> TOMLDocument:
    path = profiles_path()
    if not path.exists():
        return tomlkit.document()
    return tomlkit.parse(path.read_text(encoding="utf-8"))


def _write_document(document: TOMLDocument) -> None:
    directory = _ensure_config_dir()
    fd, tmp_name = tempfile.mkstemp(dir=str(directory), prefix=".profiles-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(tomlkit.dumps(document))
        if os.name == "posix":
            os.chmod(tmp_name, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_name, profiles_path())
    except BaseException:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def _profiles_table(document: TOMLDocument) -> Any:
    return document.get("profiles")


def load_profiles() -> dict[str, ProfileRecord]:
    """Load every stored profile.

    Returns:
        A mapping of profile name to :class:`ProfileRecord`.
    """
    document = _load_document()
    table = _profiles_table(document)
    if not table:
        return {}
    result: dict[str, ProfileRecord] = {}
    for name, value in table.items():
        server_prefix = value.get("server_prefix")
        legacy_base_url = value.get("base_url")
        if legacy_base_url is not None and server_prefix is None:
            # Migrate a legacy base_url to its server prefix, or reject it. This
            # must not be silently ignored: dropping it would redirect the
            # profile to the app-eu default endpoint.
            server_prefix = _server_prefix_from_legacy_base_url(str(name), str(legacy_base_url))
        result[name] = ProfileRecord(
            name=str(name),
            workspace_id=int(value["workspace_id"]),
            server_prefix=server_prefix,
            project_id=value.get("project_id"),
        )
    return result


def list_profiles() -> list[ProfileRecord]:
    """Return every stored profile, sorted by name."""
    return sorted(load_profiles().values(), key=lambda record: record.name)


def get_profile(name: str) -> ProfileRecord | None:
    """Return one stored profile, or None if it does not exist.

    Args:
        name: The profile name.
    """
    return load_profiles().get(name)


def save_profile(record: ProfileRecord) -> None:
    """Create or replace one profile's non-secret record.

    Args:
        record: The complete profile record to store. Replaces any existing
            record with the same name.

    Raises:
        CliError: ``invalid_profile_name`` for a malformed name.
    """
    validate_profile_name(record.name)
    document = _load_document()
    table = document.get("profiles")
    if table is None:
        table = tomlkit.table()
        document["profiles"] = table
    entry = tomlkit.table()
    entry["workspace_id"] = record.workspace_id
    if record.server_prefix is not None:
        entry["server_prefix"] = record.server_prefix
    if record.project_id is not None:
        entry["project_id"] = record.project_id
    table[record.name] = entry
    _write_document(document)


def delete_profile(name: str) -> bool:
    """Delete one profile's non-secret record.

    If the deleted profile was selected, ``default`` becomes selected when it
    still exists; otherwise the selection is cleared. Deleting a profile that
    does not exist is an idempotent no-op.

    Args:
        name: The profile name.

    Returns:
        True if a record was removed, False if none existed.
    """
    document = _load_document()
    table = document.get("profiles")
    removed = False
    if table is not None and name in table:
        del table[name]
        removed = True
    settings_table = document.get("settings")
    if settings_table is not None and name in settings_table:
        del settings_table[name]
    selected = document.get("selected")
    if selected == name:
        if table is not None and DEFAULT_PROFILE_NAME in table:
            document["selected"] = DEFAULT_PROFILE_NAME
        elif "selected" in document:
            del document["selected"]
    _write_document(document)
    return removed


def get_selected() -> str:
    """Return the currently selected profile name (default ``"default"``)."""
    document = _load_document()
    selected = document.get("selected")
    return str(selected) if selected else DEFAULT_PROFILE_NAME


def set_selected(name: str) -> None:
    """Set the selected profile pointer.

    Args:
        name: The profile name to select.

    Raises:
        CliError: ``invalid_profile_name`` for a malformed name.
    """
    validate_profile_name(name)
    document = _load_document()
    document["selected"] = name
    _write_document(document)


def get_setting(name: str, key: str) -> str | None:
    """Return one profile-scoped setting value, or None if unset.

    Args:
        name: The profile name.
        key: The setting key (for example ``"output"`` or ``"timeout"``).
    """
    document = _load_document()
    settings_table = document.get("settings")
    if settings_table is None or name not in settings_table:
        return None
    value = settings_table[name].get(key)
    return str(value) if value is not None else None


def list_settings(name: str) -> dict[str, str]:
    """Return every setting stored for one profile.

    Args:
        name: The profile name.
    """
    document = _load_document()
    settings_table = document.get("settings")
    if settings_table is None or name not in settings_table:
        return {}
    return {str(key): str(value) for key, value in settings_table[name].items()}


def set_setting(name: str, key: str, value: str) -> None:
    """Set one profile-scoped setting value.

    Args:
        name: The profile name.
        key: The setting key.
        value: The value to store (always a string).

    Raises:
        CliError: ``invalid_profile_name`` for a malformed name.
    """
    validate_profile_name(name)
    document = _load_document()
    settings_table = document.get("settings")
    if settings_table is None:
        settings_table = tomlkit.table()
        document["settings"] = settings_table
    profile_settings = settings_table.get(name)
    if profile_settings is None:
        profile_settings = tomlkit.table()
        settings_table[name] = profile_settings
    profile_settings[key] = value
    _write_document(document)
