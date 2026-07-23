"""Authentication and project-context resolution precedence."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.resolver import (
    ENV_API_KEY,
    ENV_API_SECRET,
    ENV_WORKSPACE_ID,
    ExplicitLogin,
    resolve_auth,
    resolve_project,
)
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
        ENV_API_KEY: "env-key",
        ENV_API_SECRET: "env-secret",
        ENV_WORKSPACE_ID: "9",
    }
    resolved = resolve_auth(_invocation(), env=env)
    assert resolved.api_key == "env-key"
    assert resolved.workspace_id == 9
    assert resolved.base_url == "https://app-eu.mammoth.io/api/v2"


def test_resolve_auth_explicit_login_overrides_everything(isolated_cli_config: Path) -> None:
    env = {
        ENV_API_KEY: "env-key",
        ENV_API_SECRET: "env-secret",
        ENV_WORKSPACE_ID: "9",
    }
    explicit = ExplicitLogin(api_key="explicit-key", api_secret="explicit-secret", workspace_id=1)
    resolved = resolve_auth(_invocation(), env=env, explicit_login=explicit)
    assert resolved.api_key == "explicit-key"
    assert resolved.workspace_id == 1


def test_resolve_auth_invalid_env_workspace_id(isolated_cli_config: Path) -> None:
    env = {
        ENV_API_KEY: "env-key",
        ENV_API_SECRET: "env-secret",
        ENV_WORKSPACE_ID: "not-a-number",
    }
    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation(), env=env)
    assert excinfo.value.code == "invalid_workspace_id"


@pytest.mark.parametrize("raw_workspace", ["0", "-1", "-999"])
def test_resolve_auth_non_positive_env_workspace_id_rejected(
    isolated_cli_config: Path, raw_workspace: str
) -> None:
    """A non-positive MAMMOTH_WORKSPACE_ID is rejected, not silently accepted."""
    env = {
        ENV_API_KEY: "env-key",
        ENV_API_SECRET: "env-secret",
        ENV_WORKSPACE_ID: raw_workspace,
    }
    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation(), env=env)
    assert excinfo.value.code == "invalid_workspace_id"
    assert excinfo.value.exit_status == 2


# Every strict-subset of the three environment credential variables. Each must
# be rejected as incomplete rather than falling back to a saved profile.
_PARTIAL_ENV_COMBINATIONS = [
    {ENV_API_KEY: "env-key"},
    {ENV_API_SECRET: "env-secret"},
    {ENV_WORKSPACE_ID: "9"},
    {ENV_API_KEY: "env-key", ENV_API_SECRET: "env-secret"},
    {ENV_API_KEY: "env-key", ENV_WORKSPACE_ID: "9"},
    {ENV_API_SECRET: "env-secret", ENV_WORKSPACE_ID: "9"},
]


@pytest.mark.parametrize("partial_env", _PARTIAL_ENV_COMBINATIONS)
def test_resolve_auth_partial_env_does_not_fall_back_to_profile(
    isolated_cli_config: Path, partial_env: dict[str, str]
) -> None:
    """A partial env credential set must fail, never use the saved profile.

    A valid ``default`` profile exists here; if partial env auth silently fell
    back to it, the CLI could operate in a different workspace than the partial
    environment implied. The contract is to reject with a stable code and to
    name exactly which variables are missing.
    """
    profiles.save_profile(
        profiles.ProfileRecord(name="default", workspace_id=4, server_prefix="release")
    )
    credentials.store_credentials("default", "profile-key", "profile-secret", storage="file")

    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation(), env=partial_env)

    error = excinfo.value
    assert error.code == "incomplete_environment_auth"
    # It must NOT have fallen back to the profile credentials.
    assert "profile-key" not in str(error)
    # It names every absent variable and no present one.
    missing = set(error.details["missing"])
    all_vars = {ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID}
    assert missing == all_vars - set(partial_env)


def test_resolve_auth_complete_env_still_works(isolated_cli_config: Path) -> None:
    """The all-three case is unaffected by the partial-set guard."""
    env = {ENV_API_KEY: "k", ENV_API_SECRET: "s", ENV_WORKSPACE_ID: "9"}
    resolved = resolve_auth(_invocation(), env=env)
    assert resolved.api_key == "k"
    assert resolved.workspace_id == 9


# Every combination where at least one credential variable is SET-but-empty.
# Presence is by "the variable exists", not by truthiness, so an explicitly
# empty value is a deliberate (broken) env-auth attempt, never a profile
# fallback.
_EMPTY_ENV_COMBINATIONS = [
    {ENV_API_KEY: ""},
    {ENV_API_SECRET: ""},
    {ENV_WORKSPACE_ID: ""},
    {ENV_API_KEY: "", ENV_API_SECRET: "", ENV_WORKSPACE_ID: ""},
    {ENV_API_KEY: "", ENV_API_SECRET: "s", ENV_WORKSPACE_ID: "9"},
    {ENV_API_KEY: "k", ENV_API_SECRET: "", ENV_WORKSPACE_ID: "9"},
    {ENV_API_KEY: "k", ENV_API_SECRET: "s", ENV_WORKSPACE_ID: ""},
]


@pytest.mark.parametrize("empty_env", _EMPTY_ENV_COMBINATIONS)
def test_resolve_auth_explicitly_empty_env_var_does_not_fall_back(
    isolated_cli_config: Path, empty_env: dict[str, str]
) -> None:
    """A SET-but-empty credential variable is rejected, not a profile fallback.

    ``MAMMOTH_API_KEY=""`` is a deliberate attempt to use environment auth; it
    must raise rather than silently operate under a saved profile's workspace.
    """
    profiles.save_profile(
        profiles.ProfileRecord(name="default", workspace_id=4, server_prefix="release")
    )
    credentials.store_credentials("default", "profile-key", "profile-secret", storage="file")

    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation(), env=empty_env)

    error = excinfo.value
    assert error.code == "incomplete_environment_auth"
    assert "profile-key" not in str(error)
    # Every set-but-empty (and absent) variable is reported missing.
    missing = set(error.details["missing"])
    all_vars = {ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID}
    expected = {name for name in all_vars if not empty_env.get(name)}
    assert missing == expected


def test_resolve_auth_rejects_non_positive_profile_workspace(isolated_cli_config: Path) -> None:
    """A saved profile with a non-positive workspace id is rejected centrally."""
    profiles.save_profile(
        profiles.ProfileRecord(name="default", workspace_id=0, server_prefix="release")
    )
    credentials.store_credentials("default", "k", "s", storage="file")
    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation(), env={})
    assert excinfo.value.code == "invalid_workspace_id"


def test_resolve_auth_rejects_non_positive_explicit_workspace(isolated_cli_config: Path) -> None:
    """An explicit login with a non-positive workspace id is rejected centrally."""
    explicit = ExplicitLogin(api_key="k", api_secret="s", workspace_id=-1)
    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation(), env={}, explicit_login=explicit)
    assert excinfo.value.code == "invalid_workspace_id"


def test_resolve_project_prefers_flag() -> None:
    record = profiles.ProfileRecord(name="default", workspace_id=1, project_id=7)
    assert resolve_project(_invocation(project=42), record) == 42


def test_resolve_project_falls_back_to_profile() -> None:
    record = profiles.ProfileRecord(name="default", workspace_id=1, project_id=7)
    assert resolve_project(_invocation(), record) == 7


def test_resolve_project_none_when_nothing_set() -> None:
    assert resolve_project(_invocation(), None) is None
