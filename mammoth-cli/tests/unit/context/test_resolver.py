"""Authentication and project-context resolution precedence."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.resolver import ExplicitLogin, resolve_auth, resolve_project
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation


def _invocation(**overrides: object) -> Invocation:
    fields: dict[str, object] = {"command_id": "auth.status"}
    fields.update(overrides)
    return Invocation(**fields)  # type: ignore[arg-type]


def test_resolve_auth_raises_when_nothing_available(isolated_cli_config: Path) -> None:
    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation(), env={})
    assert excinfo.value.code == "not_authenticated"
    assert excinfo.value.exit_status == 4


def test_resolve_auth_uses_profile_credentials(isolated_cli_config: Path) -> None:
    profiles.save_profile(
        profiles.ProfileRecord(name="default", workspace_id=4, server_prefix="release")
    )
    credentials.store_credentials("default", "profile-key", "profile-secret", storage="file")
    resolved = resolve_auth(_invocation(), env={})
    assert resolved.api_key == "profile-key"
    assert resolved.workspace_id == 4
    assert resolved.base_url == "https://release.mammoth.io/api/v2"


def test_resolve_auth_env_overrides_profile(isolated_cli_config: Path) -> None:
    profiles.save_profile(
        profiles.ProfileRecord(name="default", workspace_id=4, server_prefix="release")
    )
    credentials.store_credentials("default", "profile-key", "profile-secret", storage="file")
    env = {
        "MAMMOTH_API_KEY": "env-key",
        "MAMMOTH_API_SECRET": "env-secret",
        "MAMMOTH_WORKSPACE_ID": "9",
    }
    resolved = resolve_auth(_invocation(), env=env)
    assert resolved.api_key == "env-key"
    assert resolved.workspace_id == 9
    assert resolved.base_url == "https://app-eu.mammoth.io/api/v2"


def test_resolve_auth_explicit_login_overrides_everything(isolated_cli_config: Path) -> None:
    env = {
        "MAMMOTH_API_KEY": "env-key",
        "MAMMOTH_API_SECRET": "env-secret",
        "MAMMOTH_WORKSPACE_ID": "9",
    }
    explicit = ExplicitLogin(api_key="explicit-key", api_secret="explicit-secret", workspace_id=1)
    resolved = resolve_auth(_invocation(), env=env, explicit_login=explicit)
    assert resolved.api_key == "explicit-key"
    assert resolved.workspace_id == 1


def test_resolve_auth_invocation_base_url_wins(isolated_cli_config: Path) -> None:
    explicit = ExplicitLogin(api_key="k", api_secret="s", workspace_id=1, server_prefix="release")
    resolved = resolve_auth(
        _invocation(base_url="https://override.example.com/api/v2"), env={}, explicit_login=explicit
    )
    assert resolved.base_url == "https://override.example.com/api/v2"


def test_resolve_auth_invalid_env_workspace_id(isolated_cli_config: Path) -> None:
    env = {
        "MAMMOTH_API_KEY": "env-key",
        "MAMMOTH_API_SECRET": "env-secret",
        "MAMMOTH_WORKSPACE_ID": "not-a-number",
    }
    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation(), env=env)
    assert excinfo.value.code == "invalid_workspace_id"


def test_resolve_project_prefers_flag() -> None:
    record = profiles.ProfileRecord(name="default", workspace_id=1, project_id=7)
    assert resolve_project(_invocation(project=42), record) == 42


def test_resolve_project_falls_back_to_profile() -> None:
    record = profiles.ProfileRecord(name="default", workspace_id=1, project_id=7)
    assert resolve_project(_invocation(), record) == 7


def test_resolve_project_none_when_nothing_set() -> None:
    assert resolve_project(_invocation(), None) is None
