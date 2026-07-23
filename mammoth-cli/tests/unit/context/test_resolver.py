"""Authentication and project-context resolution precedence.

Authentication requires a login: credentials resolve from an explicit login
(handed in by ``auth login``) or from a saved profile. There is no environment
credential path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.context import credentials, profiles
from mammoth_cli.context.resolver import (
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


def test_resolve_auth_raises_when_no_profile(isolated_cli_config: Path) -> None:
    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation())
    assert excinfo.value.code == "not_authenticated"
    assert excinfo.value.exit_status == 4


def test_resolve_auth_uses_profile_credentials(isolated_cli_config: Path) -> None:
    profiles.save_profile(
        profiles.ProfileRecord(name="default", workspace_id=4, server_prefix="release")
    )
    credentials.store_credentials("default", "profile-key", "profile-secret", storage="file")
    resolved = resolve_auth(_invocation())
    assert resolved.api_key == "profile-key"
    assert resolved.workspace_id == 4
    assert resolved.base_url == "https://release.mammoth.io/api/v2"


def test_resolve_auth_explicit_login_overrides_profile(isolated_cli_config: Path) -> None:
    profiles.save_profile(
        profiles.ProfileRecord(name="default", workspace_id=4, server_prefix="release")
    )
    credentials.store_credentials("default", "profile-key", "profile-secret", storage="file")
    explicit = ExplicitLogin(api_key="explicit-key", api_secret="explicit-secret", workspace_id=1)
    resolved = resolve_auth(_invocation(), explicit_login=explicit)
    assert resolved.api_key == "explicit-key"
    assert resolved.workspace_id == 1


def test_resolve_auth_uses_named_profile(isolated_cli_config: Path) -> None:
    """``--profile`` selects which saved profile authenticates."""
    profiles.save_profile(profiles.ProfileRecord(name="staging", workspace_id=7))
    credentials.store_credentials("staging", "k", "s", storage="file")
    resolved = resolve_auth(_invocation(profile="staging"))
    assert resolved.workspace_id == 7


def test_resolve_auth_profile_without_credentials_is_not_authenticated(
    isolated_cli_config: Path,
) -> None:
    """A profile record with no stored credentials cannot authenticate."""
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4))
    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation())
    assert excinfo.value.code == "not_authenticated"


def test_resolve_auth_rejects_non_positive_profile_workspace(isolated_cli_config: Path) -> None:
    """A saved profile with a non-positive workspace id is rejected centrally."""
    profiles.save_profile(
        profiles.ProfileRecord(name="default", workspace_id=0, server_prefix="release")
    )
    credentials.store_credentials("default", "k", "s", storage="file")
    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation())
    assert excinfo.value.code == "invalid_workspace_id"


def test_resolve_auth_rejects_non_positive_explicit_workspace(isolated_cli_config: Path) -> None:
    """An explicit login with a non-positive workspace id is rejected centrally."""
    explicit = ExplicitLogin(api_key="k", api_secret="s", workspace_id=-1)
    with pytest.raises(CliError) as excinfo:
        resolve_auth(_invocation(), explicit_login=explicit)
    assert excinfo.value.code == "invalid_workspace_id"


def test_resolve_project_prefers_flag() -> None:
    record = profiles.ProfileRecord(name="default", workspace_id=1, project_id=7)
    assert resolve_project(_invocation(project=42), record) == 42


def test_resolve_project_falls_back_to_profile() -> None:
    record = profiles.ProfileRecord(name="default", workspace_id=1, project_id=7)
    assert resolve_project(_invocation(), record) == 7


def test_resolve_project_none_when_nothing_set() -> None:
    assert resolve_project(_invocation(), None) is None
