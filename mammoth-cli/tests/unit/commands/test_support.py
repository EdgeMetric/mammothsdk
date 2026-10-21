"""Unit tests for the ``support`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import support as support_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_CONNECTOR_LIST = "mammoth.api.support.SupportAPI.connector_list"
_CONNECTOR_CREATE = "mammoth.api.support.SupportAPI.connector_create"
_CONNECTOR_UPDATE = "mammoth.api.support.SupportAPI.connector_update"
_CONNECTOR_DELETE = "mammoth.api.support.SupportAPI.connector_delete"
_CONNECTOR_PROFILE_LIST = "mammoth.api.support.SupportAPI.connector_profile_list"
_CONNECTOR_PROFILE_CREATE = "mammoth.api.support.SupportAPI.connector_profile_create"
_CONNECTOR_PROFILE_UPDATE = "mammoth.api.support.SupportAPI.connector_profile_update"
_CONNECTOR_PROFILE_DELETE = "mammoth.api.support.SupportAPI.connector_profile_delete"
_CONNECTOR_PROFILE_ADD_CONNECTOR = "mammoth.api.support.SupportAPI.connector_profile_add_connector"
_FEATURE_LIST = "mammoth.api.support.SupportAPI.feature_list"
_FEATURE_CREATE = "mammoth.api.support.SupportAPI.feature_create"
_FEATURE_UPDATE = "mammoth.api.support.SupportAPI.feature_update"
_FEATURE_DELETE = "mammoth.api.support.SupportAPI.feature_delete"
_FEATURE_PROFILE_LIST = "mammoth.api.support.SupportAPI.feature_profile_list"
_FEATURE_PROFILE_CREATE = "mammoth.api.support.SupportAPI.feature_profile_create"
_FEATURE_PROFILE_UPDATE = "mammoth.api.support.SupportAPI.feature_profile_update"
_FEATURE_PROFILE_DELETE = "mammoth.api.support.SupportAPI.feature_profile_delete"
_FEATURE_PROFILE_ADD_FEATURE = "mammoth.api.support.SupportAPI.feature_profile_add_feature"
_OWNERSHIP_TRANSFER = "mammoth.api.support.SupportAPI.ownership_transfer"
_PLAN_LIST = "mammoth.api.support.SupportAPI.plan_list"
_PLAN_SELF_SERVE_LIST = "mammoth.api.support.SupportAPI.plan_self_serve_list"
_PLAN_CHARGEBEE_LIST = "mammoth.api.support.SupportAPI.plan_chargebee_list"
_PLAN_GET = "mammoth.api.support.SupportAPI.plan_get"
_PLAN_CREATE = "mammoth.api.support.SupportAPI.plan_create"
_PLAN_UPDATE = "mammoth.api.support.SupportAPI.plan_update"
_PLAN_DELETE = "mammoth.api.support.SupportAPI.plan_delete"
_PLAN_UPDATE_STORAGE_TIERS = "mammoth.api.support.SupportAPI.plan_update_storage_tiers"
_PLAN_ARCHIVE = "mammoth.api.support.SupportAPI.plan_archive"
_SUBSCRIPTION_GET = "mammoth.api.support.SupportAPI.subscription_get"
_SUBSCRIPTION_CREATE = "mammoth.api.support.SupportAPI.subscription_create"
_SUBSCRIPTION_UPDATE = "mammoth.api.support.SupportAPI.subscription_update"
_USER_LIST_ALL = "mammoth.api.support.SupportAPI.user_list_all"
_USER_REGISTER = "mammoth.api.support.SupportAPI.user_register"
_USER_UPDATE = "mammoth.api.support.SupportAPI.user_update"
_WORKSPACE_LIST = "mammoth.api.support.SupportAPI.workspace_list"
_WORKSPACE_GET = "mammoth.api.support.SupportAPI.workspace_get"
_WORKSPACE_CREATE = "mammoth.api.support.SupportAPI.workspace_create"
_WORKSPACE_UPDATE = "mammoth.api.support.SupportAPI.workspace_update"
_WORKSPACE_DELETE = "mammoth.api.support.SupportAPI.workspace_delete"
_WORKSPACE_SUSPEND_ACCESS = "mammoth.api.support.SupportAPI.workspace_suspend_access"
_WORKSPACE_RESTORE_ACCESS = "mammoth.api.support.SupportAPI.workspace_restore_access"
_WORKSPACE_USER_LIST = "mammoth.api.support.SupportAPI.workspace_user_list"
_WORKSPACE_USER_ADD = "mammoth.api.support.SupportAPI.workspace_user_add"
_WORKSPACE_USER_REMOVE = "mammoth.api.support.SupportAPI.workspace_user_remove"
_WORKSPACE_USER_TRANSFER = "mammoth.api.support.SupportAPI.workspace_user_transfer"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, data: object) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(data), encoding="utf-8")
    return str(doc)


# --- connector.list --------------------------------------------------------------


def test_connector_list_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_connector_list(_inv("support.connector.list", output="json"))
    assert fake_service.call_log == [(_CONNECTOR_LIST, {})]


# --- connector.create --------------------------------------------------------------


def test_connector_create_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_create(_inv("support.connector.create", yes=True))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_connector_create_blocked_without_confirmation(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_create(
            _inv("support.connector.create", extra_args=["Slack"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_create_uses_positional_name(fake_service: FakeMammothService) -> None:
    support_cmd.support_connector_create(
        _inv("support.connector.create", extra_args=["Slack"], yes=True, confirm="Slack")
    )
    assert fake_service.call_log == [(_CONNECTOR_CREATE, {"name": "Slack"})]


def test_connector_create_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"name": "Slack", "description": "chat", "enabled": False})
    support_cmd.support_connector_create(
        _inv("support.connector.create", input_file=doc, yes=True, confirm="Slack")
    )
    assert fake_service.call_log == [
        (_CONNECTOR_CREATE, {"name": "Slack", "description": "chat", "enabled": False})
    ]


# --- connector.update --------------------------------------------------------------


def test_connector_update_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_update(_inv("support.connector.update", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_connector_update_blocked_without_confirmation(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_update(
            _inv("support.connector.update", extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_update_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"name": "New", "price_per_month": 5.0})
    data, _meta = support_cmd.support_connector_update(
        _inv("support.connector.update", extra_args=["7"], input_file=doc, yes=True, confirm="7")
    )
    assert fake_service.call_log == [
        (_CONNECTOR_UPDATE, {"connector_id": 7, "name": "New", "price_per_month": 5.0})
    ]
    assert isinstance(data, dict)
    assert data["warnings"] == [support_cmd.CONNECTOR_PRICE_REMOVED]


def test_connector_update_without_the_removed_price_has_no_warning(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"name": "New"})
    data, _meta = support_cmd.support_connector_update(
        _inv("support.connector.update", extra_args=["7"], input_file=doc, yes=True, confirm="7")
    )
    assert not (isinstance(data, dict) and "warnings" in data)


def test_connector_create_warns_that_the_removed_price_has_no_effect(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"name": "Slack", "price_per_month": 3})
    data, _meta = support_cmd.support_connector_create(
        _inv("support.connector.create", input_file=doc, yes=True, confirm="Slack")
    )
    assert isinstance(data, dict)
    assert data["warnings"] == [support_cmd.CONNECTOR_PRICE_REMOVED]


# --- connector.delete --------------------------------------------------------------


def test_connector_delete_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_delete(_inv("support.connector.delete", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_connector_delete_blocked_without_confirmation(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_delete(
            _inv("support.connector.delete", extra_args=["7"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_delete_mismatch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_delete(
            _inv("support.connector.delete", extra_args=["7"], yes=True, confirm="8")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_connector_delete_proceeds_with_matching_target(
    fake_service: FakeMammothService,
) -> None:
    support_cmd.support_connector_delete(
        _inv("support.connector.delete", extra_args=["7"], yes=True, confirm="7")
    )
    assert fake_service.call_log == [(_CONNECTOR_DELETE, {"connector_id": 7})]


# --- connector-profile.list --------------------------------------------------------


def test_connector_profile_list_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_connector_profile_list(
        _inv("support.connector-profile.list", output="json")
    )
    assert fake_service.call_log == [(_CONNECTOR_PROFILE_LIST, {})]


# --- connector-profile.create --------------------------------------------------------


def test_connector_profile_create_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_create(
            _inv("support.connector-profile.create", yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_connector_profile_create_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_create(
            _inv("support.connector-profile.create", extra_args=["Basic"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_profile_create_forwards_connectors(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"name": "Basic", "connectors": [{"connector_id": 1}]})
    support_cmd.support_connector_profile_create(
        _inv("support.connector-profile.create", input_file=doc, yes=True, confirm="Basic")
    )
    assert fake_service.call_log == [
        (_CONNECTOR_PROFILE_CREATE, {"name": "Basic", "connectors": [{"connector_id": 1}]})
    ]


# --- connector-profile.update --------------------------------------------------------


def test_connector_profile_update_requires_positional(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_update(
            _inv("support.connector-profile.update", yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_connector_profile_update_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_update(
            _inv("support.connector-profile.update", extra_args=["3"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_profile_update_forwards_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"name": "Renamed"})
    support_cmd.support_connector_profile_update(
        _inv(
            "support.connector-profile.update",
            extra_args=["3"],
            input_file=doc,
            yes=True,
            confirm="3",
        )
    )
    assert fake_service.call_log == [
        (_CONNECTOR_PROFILE_UPDATE, {"profile_id": 3, "name": "Renamed"})
    ]


# --- connector-profile.delete --------------------------------------------------------


def test_connector_profile_delete_requires_positional(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_delete(
            _inv("support.connector-profile.delete", yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_connector_profile_delete_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_delete(
            _inv("support.connector-profile.delete", extra_args=["3"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_profile_delete_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_connector_profile_delete(
        _inv("support.connector-profile.delete", extra_args=["3"], yes=True, confirm="3")
    )
    assert fake_service.call_log == [(_CONNECTOR_PROFILE_DELETE, {"profile_id": 3})]


# --- connector-profile.add-connector --------------------------------------------------


def test_connector_profile_add_connector_requires_positional(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_add_connector(
            _inv("support.connector-profile.add-connector", yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_connector_profile_add_connector_requires_connector_id(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_add_connector(
            _inv(
                "support.connector-profile.add-connector",
                extra_args=["3"],
                yes=True,
                confirm="3",
            )
        )
    assert excinfo.value.code == "missing_argument"


def test_connector_profile_add_connector_blocked(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_add_connector(
            _inv(
                "support.connector-profile.add-connector",
                extra_args=["3", "9"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_profile_add_connector_forwards_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"price_per_month": 2.5, "enabled": False})
    support_cmd.support_connector_profile_add_connector(
        _inv(
            "support.connector-profile.add-connector",
            extra_args=["3", "9"],
            input_file=doc,
            yes=True,
            confirm="3",
        )
    )
    assert fake_service.call_log == [
        (
            _CONNECTOR_PROFILE_ADD_CONNECTOR,
            {"profile_id": 3, "connector_id": 9, "price_per_month": 2.5, "enabled": False},
        )
    ]


# --- feature.list --------------------------------------------------------------------


def test_feature_list_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_feature_list(_inv("support.feature.list", output="json"))
    assert fake_service.call_log == [(_FEATURE_LIST, {})]


# --- feature.create --------------------------------------------------------------------


def test_feature_create_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_create(_inv("support.feature.create", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_feature_create_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_create(
            _inv("support.feature.create", extra_args=["Beta"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_feature_create_forwards_values(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"name": "Beta", "values": ["a", "b"]})
    support_cmd.support_feature_create(
        _inv("support.feature.create", input_file=doc, yes=True, confirm="Beta")
    )
    assert fake_service.call_log == [(_FEATURE_CREATE, {"name": "Beta", "values": ["a", "b"]})]


# --- feature.update --------------------------------------------------------------------


def test_feature_update_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_update(_inv("support.feature.update", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_feature_update_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_update(
            _inv("support.feature.update", extra_args=["5"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_feature_update_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"enabled": False})
    support_cmd.support_feature_update(
        _inv("support.feature.update", extra_args=["5"], input_file=doc, yes=True, confirm="5")
    )
    assert fake_service.call_log == [(_FEATURE_UPDATE, {"feature_id": 5, "enabled": False})]


# --- feature.delete --------------------------------------------------------------------


def test_feature_delete_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_delete(_inv("support.feature.delete", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_feature_delete_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_delete(
            _inv("support.feature.delete", extra_args=["5"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_feature_delete_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_feature_delete(
        _inv("support.feature.delete", extra_args=["5"], yes=True, confirm="5")
    )
    assert fake_service.call_log == [(_FEATURE_DELETE, {"feature_id": 5})]


# --- feature-profile.list --------------------------------------------------------------


def test_feature_profile_list_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_feature_profile_list(_inv("support.feature-profile.list", output="json"))
    assert fake_service.call_log == [(_FEATURE_PROFILE_LIST, {})]


# --- feature-profile.create --------------------------------------------------------------


def test_feature_profile_create_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_create(_inv("support.feature-profile.create", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_feature_profile_create_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_create(
            _inv("support.feature-profile.create", extra_args=["Gold"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_feature_profile_create_forwards_features(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"name": "Gold", "features": [{"feature_id": 1}]})
    support_cmd.support_feature_profile_create(
        _inv("support.feature-profile.create", input_file=doc, yes=True, confirm="Gold")
    )
    assert fake_service.call_log == [
        (_FEATURE_PROFILE_CREATE, {"name": "Gold", "features": [{"feature_id": 1}]})
    ]


# --- feature-profile.update --------------------------------------------------------------


def test_feature_profile_update_requires_positional(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_update(_inv("support.feature-profile.update", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_feature_profile_update_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_update(
            _inv("support.feature-profile.update", extra_args=["2"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_feature_profile_update_forwards_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"description": "updated"})
    support_cmd.support_feature_profile_update(
        _inv(
            "support.feature-profile.update",
            extra_args=["2"],
            input_file=doc,
            yes=True,
            confirm="2",
        )
    )
    assert fake_service.call_log == [
        (_FEATURE_PROFILE_UPDATE, {"profile_id": 2, "description": "updated"})
    ]


# --- feature-profile.delete --------------------------------------------------------------


def test_feature_profile_delete_requires_positional(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_delete(_inv("support.feature-profile.delete", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_feature_profile_delete_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_delete(
            _inv("support.feature-profile.delete", extra_args=["2"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_feature_profile_delete_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_feature_profile_delete(
        _inv("support.feature-profile.delete", extra_args=["2"], yes=True, confirm="2")
    )
    assert fake_service.call_log == [(_FEATURE_PROFILE_DELETE, {"profile_id": 2})]


# --- feature-profile.add-feature --------------------------------------------------------


def test_feature_profile_add_feature_requires_positional(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_add_feature(
            _inv("support.feature-profile.add-feature", yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_feature_profile_add_feature_requires_feature_id(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_add_feature(
            _inv(
                "support.feature-profile.add-feature",
                extra_args=["2"],
                yes=True,
                confirm="2",
            )
        )
    assert excinfo.value.code == "missing_argument"


def test_feature_profile_add_feature_blocked(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_add_feature(
            _inv(
                "support.feature-profile.add-feature",
                extra_args=["2", "8"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_feature_profile_add_feature_forwards_value(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"value": "on"})
    support_cmd.support_feature_profile_add_feature(
        _inv(
            "support.feature-profile.add-feature",
            extra_args=["2", "8"],
            input_file=doc,
            yes=True,
            confirm="2",
        )
    )
    assert fake_service.call_log == [
        (_FEATURE_PROFILE_ADD_FEATURE, {"profile_id": 2, "feature_id": 8, "value": "on"})
    ]


# --- ownership.transfer -----------------------------------------------------------------


def test_ownership_transfer_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_ownership_transfer(_inv("support.ownership.transfer", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_ownership_transfer_requires_user_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_ownership_transfer(
            _inv(
                "support.ownership.transfer",
                extra_args=["9"],
                yes=True,
                confirm="9",
            )
        )
    assert excinfo.value.code == "missing_argument"


def test_ownership_transfer_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_ownership_transfer(
            _inv(
                "support.ownership.transfer",
                extra_args=["9", "3"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_ownership_transfer_forwards_roles(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"new_role": "workspace_owner", "remove_role": "member"})
    support_cmd.support_ownership_transfer(
        _inv(
            "support.ownership.transfer",
            extra_args=["9", "3"],
            input_file=doc,
            yes=True,
            confirm="9",
        )
    )
    assert fake_service.call_log == [
        (
            _OWNERSHIP_TRANSFER,
            {
                "workspace_id": 9,
                "user_id": 3,
                "new_role": "workspace_owner",
                "remove_role": "member",
            },
        )
    ]


# --- plan.list / self-serve-list / chargebee-list --------------------------------------


def test_plan_list_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_plan_list(_inv("support.plan.list", output="json"))
    assert fake_service.call_log == [(_PLAN_LIST, {})]


def test_plan_self_serve_list_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_plan_self_serve_list(_inv("support.plan.self-serve-list", output="json"))
    assert fake_service.call_log == [(_PLAN_SELF_SERVE_LIST, {})]


def test_plan_chargebee_list_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_plan_chargebee_list(_inv("support.plan.chargebee-list", output="json"))
    assert fake_service.call_log == [(_PLAN_CHARGEBEE_LIST, {})]


def test_plan_chargebee_list_forwards_resource(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"resource": "addons"})
    support_cmd.support_plan_chargebee_list(_inv("support.plan.chargebee-list", input_file=doc))
    assert fake_service.call_log == [(_PLAN_CHARGEBEE_LIST, {"resource": "addons"})]


# --- plan.get ----------------------------------------------------------------------------


def test_plan_get_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_get(_inv("support.plan.get", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_plan_get_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_plan_get(_inv("support.plan.get", extra_args=["6"], output="json"))
    assert fake_service.call_log == [(_PLAN_GET, {"plan_id": 6})]


# --- plan.create -------------------------------------------------------------------------


def test_plan_create_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_create(_inv("support.plan.create", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_plan_create_requires_monthly_price(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_create(
            _inv("support.plan.create", extra_args=["Pro"], yes=True, confirm="Pro")
        )
    assert excinfo.value.code == "missing_field"


def test_plan_create_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"monthly_price": 49.0, "is_self_serve": True})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_create(
            _inv("support.plan.create", extra_args=["Pro"], input_file=doc, output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_plan_create_forwards_optional(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        {
            "monthly_price": 49.0,
            "is_self_serve": True,
            "display_name": "Pro Plan",
            "tiers": [{"gb": 10, "price_per_gb": 1.0}],
        },
    )
    support_cmd.support_plan_create(
        _inv(
            "support.plan.create",
            extra_args=["Pro"],
            input_file=doc,
            yes=True,
            confirm="Pro",
        )
    )
    assert fake_service.call_log == [
        (
            _PLAN_CREATE,
            {
                "name": "Pro",
                "monthly_price": 49.0,
                "is_self_serve": True,
                "display_name": "Pro Plan",
                "tiers": [{"gb": 10, "price_per_gb": 1.0}],
            },
        )
    ]


# --- plan.update -------------------------------------------------------------------------


def test_plan_update_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_update(_inv("support.plan.update", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_plan_update_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_update(
            _inv("support.plan.update", extra_args=["6"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_plan_update_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"name": "Renamed", "monthly_price": 59.0})
    support_cmd.support_plan_update(
        _inv("support.plan.update", extra_args=["6"], input_file=doc, yes=True, confirm="6")
    )
    assert fake_service.call_log == [
        (_PLAN_UPDATE, {"plan_id": 6, "name": "Renamed", "monthly_price": 59.0})
    ]


# --- plan.delete -------------------------------------------------------------------------


def test_plan_delete_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_delete(_inv("support.plan.delete", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_plan_delete_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_delete(
            _inv("support.plan.delete", extra_args=["6"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_plan_delete_mismatch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_delete(
            _inv("support.plan.delete", extra_args=["6"], yes=True, confirm="7")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_plan_delete_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_plan_delete(
        _inv("support.plan.delete", extra_args=["6"], yes=True, confirm="6")
    )
    assert fake_service.call_log == [(_PLAN_DELETE, {"plan_id": 6})]


# --- plan.update-storage-tiers -------------------------------------------------------------


def test_plan_update_storage_tiers_requires_positional(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_update_storage_tiers(
            _inv("support.plan.update-storage-tiers", yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_plan_update_storage_tiers_requires_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_update_storage_tiers(
            _inv(
                "support.plan.update-storage-tiers",
                extra_args=["6"],
                yes=True,
                confirm="6",
            )
        )
    assert excinfo.value.code == "missing_field"


def test_plan_update_storage_tiers_blocked(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"storage_tiers": [{"gb": 5, "price_per_gb": 0.5}]})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_update_storage_tiers(
            _inv(
                "support.plan.update-storage-tiers",
                extra_args=["6"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_plan_update_storage_tiers_proceeds(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"storage_tiers": [{"gb": 5, "price_per_gb": 0.5}]})
    support_cmd.support_plan_update_storage_tiers(
        _inv(
            "support.plan.update-storage-tiers",
            extra_args=["6"],
            input_file=doc,
            yes=True,
            confirm="6",
        )
    )
    assert fake_service.call_log == [
        (
            _PLAN_UPDATE_STORAGE_TIERS,
            {"plan_id": 6, "storage_tiers": [{"gb": 5, "price_per_gb": 0.5}]},
        )
    ]


# --- plan.archive ------------------------------------------------------------------------


def test_plan_archive_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_archive(_inv("support.plan.archive", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_plan_archive_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_archive(
            _inv("support.plan.archive", extra_args=["6"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_plan_archive_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_plan_archive(
        _inv("support.plan.archive", extra_args=["6"], yes=True, confirm="6")
    )
    assert fake_service.call_log == [(_PLAN_ARCHIVE, {"plan_id": 6})]


# --- subscription.get ----------------------------------------------------------------------


def test_subscription_get_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_subscription_get(_inv("support.subscription.get", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_subscription_get_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_subscription_get(
        _inv("support.subscription.get", extra_args=["9"], output="json")
    )
    assert fake_service.call_log == [(_SUBSCRIPTION_GET, {"workspace_id": 9})]


def test_subscription_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"fields": "plan_id,status"})
    support_cmd.support_subscription_get(
        _inv("support.subscription.get", extra_args=["9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (_SUBSCRIPTION_GET, {"workspace_id": 9, "fields": "plan_id,status"})
    ]


# --- subscription.create -------------------------------------------------------------------


def test_subscription_create_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_subscription_create(_inv("support.subscription.create", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_subscription_create_requires_plan_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_subscription_create(
            _inv(
                "support.subscription.create",
                extra_args=["9"],
                yes=True,
                confirm="9",
            )
        )
    assert excinfo.value.code == "missing_argument"


def test_subscription_create_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_subscription_create(
            _inv(
                "support.subscription.create",
                extra_args=["9", "cb-plan-1"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_subscription_create_forwards_customer_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {
            "first_name": "Ann",
            "last_name": "Lee",
            "email": "ann@x.com",
            "company_name": "Acme",
        },
    )
    support_cmd.support_subscription_create(
        _inv(
            "support.subscription.create",
            extra_args=["9", "cb-plan-1"],
            input_file=doc,
            yes=True,
            confirm="9",
        )
    )
    assert fake_service.call_log == [
        (
            _SUBSCRIPTION_CREATE,
            {
                "workspace_id": 9,
                "plan_id": "cb-plan-1",
                "first_name": "Ann",
                "last_name": "Lee",
                "email": "ann@x.com",
                "company_name": "Acme",
            },
        )
    ]


# --- subscription.update -------------------------------------------------------------------


def test_subscription_update_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_subscription_update(_inv("support.subscription.update", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_subscription_update_requires_field(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_subscription_update(
            _inv(
                "support.subscription.update",
                extra_args=["9"],
                yes=True,
                confirm="9",
            )
        )
    assert excinfo.value.code == "missing_argument"


def test_subscription_update_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_subscription_update(
            _inv(
                "support.subscription.update",
                extra_args=["9", "sub-1"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_subscription_update_proceeds(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {})
    support_cmd.support_subscription_update(
        _inv(
            "support.subscription.update",
            extra_args=["9", "sub-1"],
            input_file=doc,
            yes=True,
            confirm="9",
        )
    )
    assert fake_service.call_log == [
        (_SUBSCRIPTION_UPDATE, {"workspace_id": 9, "subscription_id": "sub-1"})
    ]


# --- user.list-all -------------------------------------------------------------------------


def test_user_list_all_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_user_list_all(_inv("support.user.list-all", output="json"))
    assert fake_service.call_log == [(_USER_LIST_ALL, {})]


def test_user_list_all_forwards_pagination(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"limit": 10, "offset": 5, "sort": "(email:asc)"})
    support_cmd.support_user_list_all(_inv("support.user.list-all", input_file=doc))
    assert fake_service.call_log == [
        (_USER_LIST_ALL, {"limit": 10, "offset": 5, "sort": "(email:asc)"})
    ]


# --- user.register -------------------------------------------------------------------------


def test_user_register_requires_email(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_user_register(_inv("support.user.register", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_user_register_requires_fields(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_user_register(
            _inv(
                "support.user.register",
                extra_args=["ann@x.com"],
                yes=True,
                confirm="ann@x.com",
            )
        )
    assert excinfo.value.code == "missing_field"


def test_user_register_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"first_name": "Ann", "last_name": "Lee", "verified": True})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_user_register(
            _inv(
                "support.user.register",
                extra_args=["ann@x.com"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_user_register_forwards_is_registration(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {"first_name": "Ann", "last_name": "Lee", "verified": True, "is_registration": True},
    )
    support_cmd.support_user_register(
        _inv(
            "support.user.register",
            extra_args=["ann@x.com"],
            input_file=doc,
            yes=True,
            confirm="ann@x.com",
        )
    )
    assert fake_service.call_log == [
        (
            _USER_REGISTER,
            {
                "email": "ann@x.com",
                "first_name": "Ann",
                "last_name": "Lee",
                "verified": True,
                "is_registration": True,
            },
        )
    ]


# --- user.update -------------------------------------------------------------------------


def test_user_update_requires_email(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_user_update(_inv("support.user.update", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_user_update_requires_verified(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_user_update(
            _inv(
                "support.user.update",
                extra_args=["ann@x.com"],
                yes=True,
                confirm="ann@x.com",
            )
        )
    assert excinfo.value.code == "missing_field"


def test_user_update_mismatch(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"verified": True})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_user_update(
            _inv(
                "support.user.update",
                extra_args=["ann@x.com"],
                input_file=doc,
                yes=True,
                confirm="wrong@x.com",
            )
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_user_update_proceeds(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"verified": True})
    support_cmd.support_user_update(
        _inv(
            "support.user.update",
            extra_args=["ann@x.com"],
            input_file=doc,
            yes=True,
            confirm="ann@x.com",
        )
    )
    assert fake_service.call_log == [(_USER_UPDATE, {"email": "ann@x.com", "verified": True})]


# --- workspace.list -------------------------------------------------------------------------


def test_workspace_list_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_workspace_list(_inv("support.workspace.list", output="json"))
    assert fake_service.call_log == [(_WORKSPACE_LIST, {})]


# --- workspace.get -------------------------------------------------------------------------


def test_workspace_get_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_get(_inv("support.workspace.get", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_workspace_get_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_workspace_get(
        _inv("support.workspace.get", extra_args=["9"], output="json")
    )
    assert fake_service.call_log == [(_WORKSPACE_GET, {"workspace_id": 9})]


def test_workspace_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"fields": "name,plan_id"})
    support_cmd.support_workspace_get(
        _inv("support.workspace.get", extra_args=["9"], input_file=doc)
    )
    assert fake_service.call_log == [
        (_WORKSPACE_GET, {"workspace_id": 9, "fields": "name,plan_id"})
    ]


# --- workspace.create -------------------------------------------------------------------------


def test_workspace_create_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_create(_inv("support.workspace.create", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_workspace_create_requires_fields(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_create(
            _inv(
                "support.workspace.create",
                extra_args=["Acme"],
                yes=True,
                confirm="Acme",
            )
        )
    assert excinfo.value.code == "missing_field"


def test_workspace_create_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"user_email": "owner@acme.com", "payment_frequency": "monthly"})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_create(
            _inv(
                "support.workspace.create",
                extra_args=["Acme"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_create_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {
            "user_email": "owner@acme.com",
            "payment_frequency": "monthly",
            "plan_id": 3,
            "is_registration": True,
        },
    )
    support_cmd.support_workspace_create(
        _inv(
            "support.workspace.create",
            extra_args=["Acme"],
            input_file=doc,
            yes=True,
            confirm="Acme",
        )
    )
    assert fake_service.call_log == [
        (
            _WORKSPACE_CREATE,
            {
                "name": "Acme",
                "user_email": "owner@acme.com",
                "payment_frequency": "monthly",
                "plan_id": 3,
                "is_registration": True,
            },
        )
    ]


# --- workspace.update -------------------------------------------------------------------------


def test_workspace_update_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_update(_inv("support.workspace.update", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_workspace_update_requires_fields(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_update(
            _inv(
                "support.workspace.update",
                extra_args=["9"],
                yes=True,
                confirm="9",
            )
        )
    assert excinfo.value.code == "missing_field"


def test_workspace_update_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"name": "Acme Renamed", "payment_frequency": "yearly", "plan_id": 4})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_update(
            _inv(
                "support.workspace.update",
                extra_args=["9"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_update_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {
            "name": "Acme Renamed",
            "payment_frequency": "yearly",
            "plan_id": 4,
            "plan_update": {"monthly_price": 99.0},
        },
    )
    support_cmd.support_workspace_update(
        _inv(
            "support.workspace.update",
            extra_args=["9"],
            input_file=doc,
            yes=True,
            confirm="9",
        )
    )
    assert fake_service.call_log == [
        (
            _WORKSPACE_UPDATE,
            {
                "workspace_id": 9,
                "name": "Acme Renamed",
                "payment_frequency": "yearly",
                "plan_id": 4,
                "plan_update": {"monthly_price": 99.0},
            },
        )
    ]


# --- workspace.delete -------------------------------------------------------------------------


def test_workspace_delete_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_delete(_inv("support.workspace.delete", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_workspace_delete_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_delete(
            _inv("support.workspace.delete", extra_args=["9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_delete_mismatch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_delete(
            _inv("support.workspace.delete", extra_args=["9"], yes=True, confirm="99")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_workspace_delete_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_workspace_delete(
        _inv("support.workspace.delete", extra_args=["9"], yes=True, confirm="9")
    )
    assert fake_service.call_log == [(_WORKSPACE_DELETE, {"workspace_id": 9})]


# --- workspace.suspend-access -------------------------------------------------------------------


def test_workspace_suspend_access_requires_positional(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_suspend_access(
            _inv("support.workspace.suspend-access", yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_workspace_suspend_access_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_suspend_access(
            _inv("support.workspace.suspend-access", extra_args=["9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_suspend_access_forwards_reason(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"reason": "Non-payment"})
    support_cmd.support_workspace_suspend_access(
        _inv(
            "support.workspace.suspend-access",
            extra_args=["9"],
            input_file=doc,
            yes=True,
            confirm="9",
        )
    )
    assert fake_service.call_log == [
        (_WORKSPACE_SUSPEND_ACCESS, {"workspace_id": 9, "reason": "Non-payment"})
    ]


# --- workspace.restore-access -------------------------------------------------------------------


def test_workspace_restore_access_requires_positional(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_restore_access(
            _inv("support.workspace.restore-access", yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_workspace_restore_access_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_restore_access(
            _inv("support.workspace.restore-access", extra_args=["9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_restore_access_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_workspace_restore_access(
        _inv("support.workspace.restore-access", extra_args=["9"], yes=True, confirm="9")
    )
    assert fake_service.call_log == [(_WORKSPACE_RESTORE_ACCESS, {"workspace_id": 9})]


# --- workspace.user.list -------------------------------------------------------------------------


def test_workspace_user_list_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_list(_inv("support.workspace.user.list", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_workspace_user_list_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    """Item 11: a read (GET) is never high_impact/confirm_target."""
    support_cmd.support_workspace_user_list(
        _inv("support.workspace.user.list", extra_args=["9"], output="json")
    )
    assert fake_service.call_log == [(_WORKSPACE_USER_LIST, {"workspace_id": 9})]


def test_workspace_user_list_forwards_pagination(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"limit": 20, "offset": 0, "sort": "(email:asc)"})
    support_cmd.support_workspace_user_list(
        _inv(
            "support.workspace.user.list",
            extra_args=["9"],
            input_file=doc,
        )
    )
    assert fake_service.call_log == [
        (
            _WORKSPACE_USER_LIST,
            {"workspace_id": 9, "limit": 20, "offset": 0, "sort": "(email:asc)"},
        )
    ]


# --- workspace.user.add -------------------------------------------------------------------------


def test_workspace_user_add_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_add(_inv("support.workspace.user.add", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_workspace_user_add_requires_fields(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_add(
            _inv(
                "support.workspace.user.add",
                extra_args=["9"],
                yes=True,
                confirm="9",
            )
        )
    assert excinfo.value.code == "missing_field"


def test_workspace_user_add_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"email": "u@x.com", "role": "workspace_member"})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_add(
            _inv(
                "support.workspace.user.add",
                extra_args=["9"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_user_add_forwards_names(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {
            "email": "u@x.com",
            "role": "workspace_member",
            "first_name": "Uma",
            "last_name": "X",
        },
    )
    support_cmd.support_workspace_user_add(
        _inv(
            "support.workspace.user.add",
            extra_args=["9"],
            input_file=doc,
            yes=True,
            confirm="9",
        )
    )
    assert fake_service.call_log == [
        (
            _WORKSPACE_USER_ADD,
            {
                "workspace_id": 9,
                "email": "u@x.com",
                "role": "workspace_member",
                "first_name": "Uma",
                "last_name": "X",
            },
        )
    ]


# --- workspace.user.remove -------------------------------------------------------------


def test_workspace_user_remove_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_remove(_inv("support.workspace.user.remove", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_workspace_user_remove_requires_user_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_remove(
            _inv(
                "support.workspace.user.remove",
                extra_args=["9"],
                yes=True,
                confirm="9",
            )
        )
    assert excinfo.value.code == "missing_argument"


def test_workspace_user_remove_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_remove(
            _inv(
                "support.workspace.user.remove",
                extra_args=["9", "2"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_user_remove_proceeds(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {})
    support_cmd.support_workspace_user_remove(
        _inv(
            "support.workspace.user.remove",
            extra_args=["9", "2"],
            input_file=doc,
            yes=True,
            confirm="9",
        )
    )
    assert fake_service.call_log == [(_WORKSPACE_USER_REMOVE, {"workspace_id": 9, "user_id": 2})]


# --- workspace.user.transfer -----------------------------------------------------------


def test_workspace_user_transfer_requires_positional(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_transfer(
            _inv("support.workspace.user.transfer", yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_workspace_user_transfer_requires_fields(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_transfer(
            _inv(
                "support.workspace.user.transfer",
                extra_args=["9"],
                yes=True,
                confirm="9",
            )
        )
    assert excinfo.value.code == "missing_argument"


def test_workspace_user_transfer_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"role": "workspace_admin"})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_transfer(
            _inv(
                "support.workspace.user.transfer",
                extra_args=["9", "2"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_user_transfer_forwards_remove_role(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"role": "workspace_admin", "remove_role": "workspace_member"})
    support_cmd.support_workspace_user_transfer(
        _inv(
            "support.workspace.user.transfer",
            extra_args=["9", "2"],
            input_file=doc,
            yes=True,
            confirm="9",
        )
    )
    assert fake_service.call_log == [
        (
            _WORKSPACE_USER_TRANSFER,
            {
                "workspace_id": 9,
                "user_id": 2,
                "role": "workspace_admin",
                "remove_role": "workspace_member",
            },
        )
    ]


# --- plan.unarchive / plan.storage-option.* (platform admin) -----------------------------

_SUPPORT = "mammoth.api.support.SupportAPI."


def test_plan_unarchive_blocked_without_confirm(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_unarchive(_inv("support.plan.unarchive", extra_args=["6"]))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_plan_unarchive_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_plan_unarchive(
        _inv("support.plan.unarchive", extra_args=["6"], yes=True, confirm="6")
    )
    assert fake_service.call_log == [(_SUPPORT + "plan_unarchive", {"plan_id": 6})]


def test_storage_option_list_needs_no_confirmation(fake_service: FakeMammothService) -> None:
    support_cmd.support_plan_storage_option_list(
        _inv("support.plan.storage-option.list", extra_args=["6"])
    )
    assert fake_service.call_log == [(_SUPPORT + "plan_storage_option_list", {"plan_id": 6})]


def test_storage_option_create_requires_prices(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"storage_gb": 100})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_storage_option_create(
            _inv(
                "support.plan.storage-option.create",
                extra_args=["6"],
                input_file=doc,
                yes=True,
                confirm="6",
            )
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_storage_option_create_proceeds(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"storage_gb": 100, "monthly_price": 20.0, "annual_price": 200.0})
    support_cmd.support_plan_storage_option_create(
        _inv(
            "support.plan.storage-option.create",
            extra_args=["6"],
            input_file=doc,
            yes=True,
            confirm="6",
        )
    )
    assert fake_service.call_log == [
        (
            _SUPPORT + "plan_storage_option_create",
            {"plan_id": 6, "storage_gb": 100, "monthly_price": 20.0, "annual_price": 200.0},
        )
    ]


def test_storage_option_update_confirms_the_option(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"monthly_price": 25.0})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_storage_option_update(
            _inv(
                "support.plan.storage-option.update",
                extra_args=["6", "9"],
                input_file=doc,
                yes=True,
                confirm="6",
            )
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    support_cmd.support_plan_storage_option_update(
        _inv(
            "support.plan.storage-option.update",
            extra_args=["6", "9"],
            input_file=doc,
            yes=True,
            confirm="9",
        )
    )
    assert fake_service.call_log == [
        (
            _SUPPORT + "plan_storage_option_update",
            {"plan_id": 6, "option_id": 9, "monthly_price": 25.0},
        )
    ]


def test_storage_option_archive_requires_option_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_storage_option_archive(
            _inv("support.plan.storage-option.archive", extra_args=["6"], yes=True, confirm="6")
        )
    assert excinfo.value.code == "missing_argument"


def test_storage_option_archive_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_plan_storage_option_archive(
        _inv("support.plan.storage-option.archive", extra_args=["6", "9"], yes=True, confirm="9")
    )
    assert fake_service.call_log == [
        (_SUPPORT + "plan_storage_option_archive", {"plan_id": 6, "option_id": 9})
    ]


# --- template.* (curated catalog, platform admin) ----------------------------------------


@pytest.mark.parametrize(
    ("handler", "command_id", "method"),
    [
        (
            support_cmd.support_template_data_preview,
            "support.template.data-preview",
            "data_preview",
        ),
        (support_cmd.support_template_canvas, "support.template.canvas", "canvas"),
    ],
)
def test_template_reads_take_the_slug(
    fake_service: FakeMammothService, handler: object, command_id: str, method: str
) -> None:
    handler(_inv(command_id, extra_args=["sales"]))  # type: ignore[operator]
    assert fake_service.call_log == [(_SUPPORT + f"template_{method}", {"slug": "sales"})]


@pytest.mark.parametrize(
    ("handler", "command_id", "method"),
    [
        (support_cmd.support_template_publish, "support.template.publish", "publish"),
        (support_cmd.support_template_unpublish, "support.template.unpublish", "unpublish"),
        (support_cmd.support_template_retire, "support.template.retire", "retire"),
        (
            support_cmd.support_template_thumbnail_clear,
            "support.template.thumbnail.clear",
            "thumbnail_clear",
        ),
        (support_cmd.support_template_discard, "support.template.discard", "discard"),
    ],
)
def test_template_writes_confirm_the_slug(
    fake_service: FakeMammothService, handler: object, command_id: str, method: str
) -> None:
    with pytest.raises(CliError) as excinfo:
        handler(_inv(command_id, extra_args=["sales"], yes=True))  # type: ignore[operator]
    assert excinfo.value.code in {"confirmation_required", "confirmation_target_mismatch"}
    assert fake_service.call_log == []
    handler(_inv(command_id, extra_args=["sales"], yes=True, confirm="sales"))  # type: ignore[operator]
    assert fake_service.call_log == [(_SUPPORT + f"template_{method}", {"slug": "sales"})]


def test_template_list_audit_snapshots_take_nothing(fake_service: FakeMammothService) -> None:
    support_cmd.support_template_list(_inv("support.template.list"))
    support_cmd.support_template_audit(_inv("support.template.audit"))
    support_cmd.support_template_snapshots(_inv("support.template.snapshots"))
    assert fake_service.call_log == [
        (_SUPPORT + "template_list", {}),
        (_SUPPORT + "template_audit", {}),
        (_SUPPORT + "template_snapshots", {}),
    ]


def test_template_edit_requires_changes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_template_edit(
            _inv("support.template.edit", extra_args=["sales"], yes=True, confirm="sales")
        )
    assert excinfo.value.code == "missing_field"


def test_template_edit_forwards_changes(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"changes": {"title": "Sales", "function": None}})
    support_cmd.support_template_edit(
        _inv(
            "support.template.edit", extra_args=["sales"], input_file=doc, yes=True, confirm="sales"
        )
    )
    assert fake_service.call_log == [
        (
            _SUPPORT + "template_edit",
            {"slug": "sales", "changes": {"title": "Sales", "function": None}},
        )
    ]


def test_template_inspect_is_a_read(fake_service: FakeMammothService) -> None:
    support_cmd.support_template_inspect(_inv("support.template.inspect", extra_args=["t.zip"]))
    assert fake_service.call_log == [(_SUPPORT + "template_inspect", {"file": "t.zip"})]


def test_template_import_requires_yes(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_template_import(
            _inv("support.template.import", extra_args=["t.zip"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_template_import_forwards_dataset(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"dataset": "Orders"})
    support_cmd.support_template_import(
        _inv("support.template.import", extra_args=["t.zip"], input_file=doc, yes=True)
    )
    assert fake_service.call_log == [
        (_SUPPORT + "template_import", {"file": "t.zip", "dataset": "Orders"})
    ]


def test_template_thumbnail_set_takes_slug_and_file(fake_service: FakeMammothService) -> None:
    support_cmd.support_template_thumbnail_set(
        _inv(
            "support.template.thumbnail.set",
            extra_args=["sales", "card.png"],
            yes=True,
            confirm="sales",
        )
    )
    assert fake_service.call_log == [
        (_SUPPORT + "template_thumbnail_set", {"slug": "sales", "file": "card.png"})
    ]


def test_template_export_returns_the_written_path(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"output_path": "out.zip", "with_data": True})
    fake_service.responses[_SUPPORT + "template_export"] = Path("out.zip")
    data, _ = support_cmd.support_template_export(
        _inv("support.template.export", extra_args=["sales"], input_file=doc)
    )
    assert data == {"output_path": "out.zip"}
    assert fake_service.call_log == [
        (
            _SUPPORT + "template_export",
            {"slug": "sales", "output_path": "out.zip", "with_data": True},
        )
    ]


def test_template_export_dashboard_requires_slug(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_template_export_dashboard(
            _inv("support.template.export-dashboard", extra_args=["42"])
        )
    assert excinfo.value.code == "missing_field"


def test_template_export_dashboard_forwards_slug(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"slug": "my-board", "with_data": False})
    support_cmd.support_template_export_dashboard(
        _inv("support.template.export-dashboard", extra_args=["42"], input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _SUPPORT + "template_export_dashboard",
            {"dashboard_id": 42, "slug": "my-board", "with_data": False},
        )
    ]


# --- admin console: billing actions, deals, partners, identities, archive ------------------
#
# Each row is (command id, positional args, input document, SDK method, expected kwargs).
# The handler name is the command id with dots and dashes turned into underscores.

_ADMIN_READS = [
    (
        "support.connector.bucket-impact",
        ["4"],
        {"bucket": "100GB"},
        "connector_bucket_impact",
        {"connector_id": 4, "bucket": "100GB"},
    ),
    ("support.entitlement.registry", [], {}, "entitlement_registry", {}),
    ("support.plan.catalog", [], {}, "plan_catalog", {}),
    ("support.deal.list", [], {}, "deal_list", {}),
    ("support.deal.get", ["5"], {}, "deal_get", {"deal_id": 5}),
    ("support.deal.activity", ["5"], {}, "deal_activity", {"deal_id": 5}),
    ("support.deal.preview-entitlement", ["5"], {}, "deal_preview_entitlement", {"deal_id": 5}),
    (
        "support.identity.list",
        [],
        {"limit": 10, "search": "ann"},
        "identity_list",
        {"limit": 10, "search": "ann"},
    ),
    ("support.identity.get", ["6"], {}, "identity_get", {"user_id": 6}),
    ("support.partner.list", [], {}, "partner_list", {}),
    ("support.partner.get", ["7"], {}, "partner_get", {"partner_id": 7}),
    ("support.partner.activity", ["7"], {}, "partner_activity", {"partner_id": 7}),
    ("support.partner.billing", ["7"], {}, "partner_billing", {"partner_id": 7}),
    ("support.partner.invoices", ["7"], {}, "partner_invoices", {"partner_id": 7}),
    ("support.partner.client.list", ["7"], {}, "partner_client_list", {"partner_id": 7}),
    ("support.triage", [], {}, "triage", {}),
    ("support.usage-tiles", [], {}, "usage_tiles", {}),
    ("support.workspace.activity", ["9"], {}, "workspace_activity", {"workspace_id": 9}),
    ("support.workspace.entitlement", ["9"], {}, "workspace_entitlement", {"workspace_id": 9}),
    ("support.workspace.deal-seed", ["9"], {}, "workspace_deal_seed", {"workspace_id": 9}),
    ("support.workspace.archive-info", ["9"], {}, "workspace_archive_info", {"workspace_id": 9}),
]

# (command id, positional args, input document, SDK method, expected kwargs, confirm target)
_ADMIN_WRITES = [
    (
        "support.billing.start-trial",
        ["9"],
        {"days": 14},
        "billing_start_trial",
        {"workspace_id": 9, "days": 14},
        "9",
    ),
    ("support.billing.end-trial", ["9"], {}, "billing_end_trial", {"workspace_id": 9}, "9"),
    ("support.billing.retry-payment", ["9"], {}, "billing_retry_payment", {"workspace_id": 9}, "9"),
    (
        "support.billing.refund",
        ["9"],
        {"amount": 500},
        "billing_refund",
        {"workspace_id": 9, "amount": 500},
        "9",
    ),
    (
        "support.billing.change-plan",
        ["9", "3"],
        {"when": "period_end", "storage_gb": 50},
        "billing_change_plan",
        {"workspace_id": 9, "new_plan_id": 3, "when": "period_end", "storage_gb": 50},
        "9",
    ),
    (
        "support.billing.cancel-subscription",
        ["9"],
        {"when": "now"},
        "billing_cancel_subscription",
        {"workspace_id": 9, "when": "now"},
        "9",
    ),
    (
        "support.deal.update",
        ["5"],
        {"notes": "hi"},
        "deal_update",
        {"deal_id": 5, "notes": "hi"},
        "5",
    ),
    (
        "support.deal.opt-in",
        ["5"],
        {"keys": ["a"]},
        "deal_opt_in",
        {"deal_id": 5, "keys": ["a"]},
        "5",
    ),
    (
        "support.deal.move-to-partner",
        ["5", "7"],
        {"price": 900, "billing_interval": "monthly"},
        "deal_move_to_partner",
        {"deal_id": 5, "partner_id": 7, "price": 900, "billing_interval": "monthly"},
        "5",
    ),
    (
        "support.deal.cancel-move-to-partner",
        ["5"],
        {},
        "deal_cancel_move_to_partner",
        {"deal_id": 5},
        "5",
    ),
    (
        "support.partner.update",
        ["7"],
        {"notes": ""},
        "partner_update",
        {"partner_id": 7, "notes": ""},
        "7",
    ),
    (
        "support.partner.charge-invoices",
        ["7"],
        {},
        "partner_charge_invoices",
        {"partner_id": 7},
        "7",
    ),
    (
        "support.partner.send-payment-link",
        ["7"],
        {},
        "partner_send_payment_link",
        {"partner_id": 7},
        "7",
    ),
    (
        "support.partner.client.delete",
        ["7", "9"],
        {},
        "partner_client_delete",
        {"partner_id": 7, "workspace_id": 9},
        "9",
    ),
    (
        "support.partner.client.detach",
        ["7", "9"],
        {"price": 900, "contact_email": "a@b.co"},
        "partner_client_detach",
        {"partner_id": 7, "workspace_id": 9, "price": 900, "contact_email": "a@b.co"},
        "9",
    ),
    (
        "support.partner.client.cancel-detach",
        ["7", "9"],
        {},
        "partner_client_cancel_detach",
        {"partner_id": 7, "workspace_id": 9},
        "9",
    ),
    (
        "support.workspace.chargebee-cancelled",
        ["9"],
        {},
        "workspace_chargebee_cancelled",
        {"workspace_id": 9},
        "9",
    ),
    (
        "support.workspace.archive",
        ["9"],
        {"storage_class": "GLACIER_IR", "confirm_name": "Acme", "cancel_billing": True},
        "workspace_archive",
        {
            "workspace_id": 9,
            "storage_class": "GLACIER_IR",
            "confirm_name": "Acme",
            "cancel_billing": True,
        },
        "9",
    ),
    (
        "support.workspace.restore-archive",
        ["9"],
        {},
        "workspace_restore_archive",
        {"workspace_id": 9},
        "9",
    ),
    (
        "support.workspace.invite.cancel",
        ["9", "4"],
        {},
        "workspace_invite_cancel",
        {"workspace_id": 9, "invite_id": 4},
        "9",
    ),
    (
        "support.workspace.invite.resend",
        ["9", "4"],
        {},
        "workspace_invite_resend",
        {"workspace_id": 9, "invite_id": 4},
        "9",
    ),
]


def _handler(command_id: str) -> Any:
    return getattr(support_cmd, command_id.replace(".", "_").replace("-", "_"))


@pytest.mark.parametrize(("cid", "args", "doc", "method", "kwargs"), _ADMIN_READS)
def test_admin_read_runs_without_confirmation(
    fake_service: FakeMammothService,
    tmp_path: Path,
    cid: str,
    args: list[str],
    doc: dict[str, object],
    method: str,
    kwargs: dict[str, object],
) -> None:
    extra = {"input_file": _write(tmp_path, doc)} if doc else {}
    _handler(cid)(_inv(cid, extra_args=args, output="json", **extra))
    assert fake_service.call_log == [(_SUPPORT + method, kwargs)]


@pytest.mark.parametrize(("cid", "args", "doc", "method", "kwargs", "target"), _ADMIN_WRITES)
def test_admin_write_needs_the_confirm_target(
    fake_service: FakeMammothService,
    tmp_path: Path,
    cid: str,
    args: list[str],
    doc: dict[str, object],
    method: str,
    kwargs: dict[str, object],
    target: str,
) -> None:
    extra = {"input_file": _write(tmp_path, doc)} if doc else {}
    handler = _handler(cid)
    with pytest.raises(CliError) as blocked:
        handler(_inv(cid, extra_args=args, output="json", **extra))
    assert blocked.value.code == "confirmation_required"
    with pytest.raises(CliError) as wrong:
        handler(_inv(cid, extra_args=args, yes=True, confirm="not-the-target", **extra))
    assert wrong.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []
    handler(_inv(cid, extra_args=args, yes=True, confirm=target, **extra))
    assert fake_service.call_log == [(_SUPPORT + method, kwargs)]


@pytest.mark.parametrize(
    "cid",
    sorted({row[0] for row in _ADMIN_READS + _ADMIN_WRITES if row[1]}),
)
def test_admin_command_with_ids_needs_them(fake_service: FakeMammothService, cid: str) -> None:
    with pytest.raises(CliError) as excinfo:
        _handler(cid)(_inv(cid, yes=True, confirm="1"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_admin_id_must_be_an_integer(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_deal_get(_inv("support.deal.get", extra_args=["abc"]))
    assert excinfo.value.code == "invalid_argument"


def test_cancel_subscription_requires_when(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_billing_cancel_subscription(
            _inv("support.billing.cancel-subscription", extra_args=["9"], yes=True, confirm="9")
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_move_to_partner_requires_price_and_interval(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"price": 1})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_deal_move_to_partner(
            _inv(
                "support.deal.move-to-partner",
                extra_args=["5", "7"],
                input_file=doc,
                yes=True,
                confirm="5",
            )
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_archive_requires_the_typed_workspace_name(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"storage_class": "DEEP_ARCHIVE"})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_archive(
            _inv(
                "support.workspace.archive",
                extra_args=["9"],
                input_file=doc,
                yes=True,
                confirm="9",
            )
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_an_input_id_cannot_replace_the_positional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"workspace_id": 1})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_billing_end_trial(
            _inv(
                "support.billing.end-trial",
                extra_args=["9"],
                input_file=doc,
                yes=True,
                confirm="9",
            )
        )
    assert excinfo.value.code == "unknown_input_field"
    assert fake_service.call_log == []


def test_deal_create_on_an_existing_workspace(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"base_plan_id": 3, "price": 1200.0})
    support_cmd.support_deal_create(
        _inv("support.deal.create", extra_args=["42"], input_file=doc, yes=True, confirm="42")
    )
    assert fake_service.call_log == [
        (_SUPPORT + "deal_create", {"base_plan_id": 3, "price": 1200.0, "workspace_id": 42})
    ]


def test_deal_create_on_a_new_workspace_confirms_its_name(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    created = {"name": "Acme", "user_email": "a@acme.co"}
    doc = _write(tmp_path, {"base_plan_id": 3, "workspace_create": created})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_deal_create(
            _inv("support.deal.create", input_file=doc, yes=True, confirm="3")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    support_cmd.support_deal_create(
        _inv("support.deal.create", input_file=doc, yes=True, confirm="Acme")
    )
    assert fake_service.call_log == [
        (_SUPPORT + "deal_create", {"base_plan_id": 3, "workspace_create": created})
    ]


def test_deal_create_requires_a_base_plan(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"price": 1.0})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_deal_create(
            _inv("support.deal.create", extra_args=["42"], input_file=doc, yes=True, confirm="42")
        )
    assert excinfo.value.code == "missing_field"


def test_partner_create_takes_the_name_from_a_positional_or_the_field(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    support_cmd.support_partner_create(
        _inv("support.partner.create", extra_args=["Acme"], yes=True, confirm="Acme")
    )
    doc = _write(tmp_path, {"name": "Beta", "contact_email": "b@beta.co"})
    support_cmd.support_partner_create(
        _inv("support.partner.create", input_file=doc, yes=True, confirm="Beta")
    )
    assert fake_service.call_log == [
        (_SUPPORT + "partner_create", {"name": "Acme"}),
        (_SUPPORT + "partner_create", {"name": "Beta", "contact_email": "b@beta.co"}),
    ]


def test_partner_create_needs_a_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_partner_create(_inv("support.partner.create", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_search_takes_text_from_a_positional_or_the_field(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    support_cmd.support_search(_inv("support.search", extra_args=["acme"]))
    support_cmd.support_search(_inv("support.search", input_file=_write(tmp_path, {"q": "ws-42"})))
    support_cmd.support_search(_inv("support.search"))
    assert fake_service.call_log == [
        (_SUPPORT + "search", {"q": "acme"}),
        (_SUPPORT + "search", {"q": "ws-42"}),
        (_SUPPORT + "search", {}),
    ]


# --- review fixes: confirm targets, refund, dry run, validation ------------------------------

_CLIENT_COMMANDS = [
    ("support.partner.client.delete", {}),
    ("support.partner.client.detach", {"price": 900, "contact_email": "a@b.co"}),
    ("support.partner.client.cancel-detach", {}),
]


@pytest.mark.parametrize(("cid", "doc"), _CLIENT_COMMANDS)
def test_client_commands_refuse_the_partner_id_as_the_confirm_target(
    fake_service: FakeMammothService, tmp_path: Path, cid: str, doc: dict[str, object]
) -> None:
    """The change lands on the workspace (second positional), so that is what is typed."""
    extra = {"input_file": _write(tmp_path, doc)} if doc else {}
    with pytest.raises(CliError) as excinfo:
        _handler(cid)(_inv(cid, extra_args=["7", "9"], yes=True, confirm="7", **extra))
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def _refund(tmp_path: Path, doc: dict[str, object], **overrides: object) -> None:
    support_cmd.support_billing_refund(
        _inv(
            "support.billing.refund",
            extra_args=["9"],
            input_file=_write(tmp_path, doc),
            **overrides,
        )
    )


@pytest.mark.parametrize(
    "doc",
    [
        {},
        {"amount": 500, "full": True},
        {"amount": 0},
        {"amount": -5},
        {"amount": 2.5},
        {"amount": "abc"},
        {"amount": True},
    ],
)
def test_refund_needs_exactly_one_valid_amount(
    fake_service: FakeMammothService, tmp_path: Path, doc: dict[str, object]
) -> None:
    with pytest.raises(CliError) as excinfo:
        _refund(tmp_path, doc, yes=True, confirm="9")
    assert excinfo.value.code in {"invalid_argument", "invalid_input_field_type"}
    assert excinfo.value.exit_status == 2
    assert fake_service.call_log == []


def test_refund_full_is_explicit_and_the_confirmation_says_so(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as blocked:
        _refund(tmp_path, {"full": True}, output="json")
    assert "FULL" in blocked.value.message
    assert fake_service.call_log == []
    _refund(tmp_path, {"full": True}, yes=True, confirm="9")
    assert fake_service.call_log == [
        (_SUPPORT + "billing_refund", {"workspace_id": 9, "full": True})
    ]


def test_refund_partial_confirmation_names_the_amount(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as blocked:
        _refund(tmp_path, {"amount": 750}, output="json")
    assert "750" in blocked.value.message


@pytest.mark.parametrize("cid", [row[0] for row in _ADMIN_WRITES + _ADMIN_READS if row[1]])
def test_workspace_id_zero_is_refused_at_the_cli(
    fake_service: FakeMammothService, cid: str
) -> None:
    args = ["0"] + ["1"] * (
        len(next(r for r in _ADMIN_WRITES + _ADMIN_READS if r[0] == cid)[1]) - 1
    )
    with pytest.raises(CliError) as excinfo:
        _handler(cid)(_inv(cid, extra_args=args, yes=True, confirm="0"))
    assert excinfo.value.code in {"invalid_argument", "missing_field"}
    assert fake_service.call_log == []


def test_archive_forwards_the_typed_name_verbatim(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """The name is checked by the server (case sensitive); the CLI never edits it."""
    doc = _write(tmp_path, {"storage_class": "GLACIER_IR", "confirm_name": "acme"})
    support_cmd.support_workspace_archive(
        _inv("support.workspace.archive", extra_args=["9"], input_file=doc, yes=True, confirm="9")
    )
    assert fake_service.call_log[0][1]["confirm_name"] == "acme"


def test_deal_create_without_a_workspace_is_a_usage_error(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"base_plan_id": 3, "price": 10, "billing_interval": "monthly"})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_deal_create(
            _inv("support.deal.create", input_file=doc, yes=True, confirm="3")
        )
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_deal_update_to_cancelled_has_its_own_confirmation_text(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"status": "cancelled"})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_deal_update(
            _inv("support.deal.update", extra_args=["5"], input_file=doc, output="json")
        )
    assert "CANCEL deal 5" in excinfo.value.message


@pytest.mark.parametrize(
    ("when", "phrase"), [("now", "refunds the unused time"), ("period_end", "period end")]
)
def test_move_to_partner_confirmation_says_what_now_does(
    fake_service: FakeMammothService, tmp_path: Path, when: str, phrase: str
) -> None:
    doc = _write(tmp_path, {"price": 9, "billing_interval": "monthly", "when": when})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_deal_move_to_partner(
            _inv(
                "support.deal.move-to-partner", extra_args=["5", "7"], input_file=doc, output="json"
            )
        )
    assert phrase in excinfo.value.message


def test_start_trial_confirmation_says_it_replaces_billing(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_billing_start_trial(
            _inv("support.billing.start-trial", extra_args=["9"], output="json")
        )
    assert "REPLACES" in excinfo.value.message
    assert "Stripe" in excinfo.value.message


def _dry_run(args: list[str], doc: str | None = None) -> Any:
    argv = ["support", *args, "--dry-run", "--output", "json", "--no-input"]
    if doc:
        argv += ["--input", doc]
    return make_runner().invoke(argv)


@pytest.mark.parametrize(
    ("args", "doc"),
    [
        (["billing", "refund", "9"], '{"full": true}'),
        (["partner", "client", "delete", "7", "9"], None),
    ],
)
def test_dry_run_of_an_irreversible_command_sends_nothing_and_says_so(
    fake_service: FakeMammothService, args: list[str], doc: str | None
) -> None:
    result = _dry_run(args, doc)
    assert result.exit_code == 0, result.output
    record = json.loads(result.output)["data"]
    assert record["irreversible"] is True
    assert record["ran"] is False
    assert [c for c in fake_service.call_log if not c[0].endswith("_get")] == []


def test_dry_run_of_archive_sends_nothing(fake_service: FakeMammothService) -> None:
    doc = '{"storage_class": "GLACIER_IR", "confirm_name": "Acme"}'
    result = _dry_run(["workspace", "archive", "9"], doc)
    assert result.exit_code == 0, result.output
    record = json.loads(result.output)["data"]
    assert record["ran"] is False
    assert record["irreversible"] is False
    assert record["mutation_class"] == "high_impact"
    assert fake_service.call_log == []
