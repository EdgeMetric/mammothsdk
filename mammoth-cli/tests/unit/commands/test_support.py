"""Unit tests for the ``support`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import support as support_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

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
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, data: object) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(data), encoding="utf-8")
    return str(doc)


# --- connector.list --------------------------------------------------------------


def test_connector_list_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_list(_inv("support.connector.list", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_list_mismatch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_list(
            _inv("support.connector.list", yes=True, confirm="wrong")
        )
    assert excinfo.value.code == "confirmation_target_mismatch"
    assert fake_service.call_log == []


def test_connector_list_proceeds_with_workspace_target(
    fake_service: FakeMammothService,
) -> None:
    support_cmd.support_connector_list(_inv("support.connector.list", yes=True, confirm="4"))
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
    support_cmd.support_connector_update(
        _inv("support.connector.update", extra_args=["7"], input_file=doc, yes=True, confirm="7")
    )
    assert fake_service.call_log == [
        (_CONNECTOR_UPDATE, {"connector_id": 7, "name": "New", "price_per_month": 5.0})
    ]


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


def test_connector_profile_list_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_list(
            _inv("support.connector-profile.list", output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_profile_list_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_connector_profile_list(
        _inv("support.connector-profile.list", yes=True, confirm="4")
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
    assert excinfo.value.code == "missing_field"


def test_connector_profile_add_connector_blocked(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"connector_id": 9})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_connector_profile_add_connector(
            _inv(
                "support.connector-profile.add-connector",
                extra_args=["3"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connector_profile_add_connector_forwards_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"connector_id": 9, "price_per_month": 2.5, "enabled": False})
    support_cmd.support_connector_profile_add_connector(
        _inv(
            "support.connector-profile.add-connector",
            extra_args=["3"],
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


def test_feature_list_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_list(_inv("support.feature.list", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_feature_list_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_feature_list(_inv("support.feature.list", yes=True, confirm="4"))
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


def test_feature_profile_list_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_list(
            _inv("support.feature-profile.list", output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_feature_profile_list_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_feature_profile_list(
        _inv("support.feature-profile.list", yes=True, confirm="4")
    )
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
    assert excinfo.value.code == "missing_field"


def test_feature_profile_add_feature_blocked(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"feature_id": 8})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_feature_profile_add_feature(
            _inv(
                "support.feature-profile.add-feature",
                extra_args=["2"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_feature_profile_add_feature_forwards_value(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"feature_id": 8, "value": "on"})
    support_cmd.support_feature_profile_add_feature(
        _inv(
            "support.feature-profile.add-feature",
            extra_args=["2"],
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
    assert excinfo.value.code == "missing_field"


def test_ownership_transfer_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"user_id": 3})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_ownership_transfer(
            _inv(
                "support.ownership.transfer",
                extra_args=["9"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_ownership_transfer_forwards_roles(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"user_id": 3, "new_role": "workspace_owner", "remove_role": "member"})
    support_cmd.support_ownership_transfer(
        _inv(
            "support.ownership.transfer",
            extra_args=["9"],
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


def test_plan_list_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_list(_inv("support.plan.list", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_plan_list_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_plan_list(_inv("support.plan.list", yes=True, confirm="4"))
    assert fake_service.call_log == [(_PLAN_LIST, {})]


def test_plan_self_serve_list_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_self_serve_list(
            _inv("support.plan.self-serve-list", output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_plan_self_serve_list_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_plan_self_serve_list(
        _inv("support.plan.self-serve-list", yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_PLAN_SELF_SERVE_LIST, {})]


def test_plan_chargebee_list_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_chargebee_list(_inv("support.plan.chargebee-list", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_plan_chargebee_list_forwards_resource(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"resource": "addons"})
    support_cmd.support_plan_chargebee_list(
        _inv("support.plan.chargebee-list", input_file=doc, yes=True, confirm="4")
    )
    assert fake_service.call_log == [(_PLAN_CHARGEBEE_LIST, {"resource": "addons"})]


# --- plan.get ----------------------------------------------------------------------------


def test_plan_get_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_get(_inv("support.plan.get", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_plan_get_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_plan_get(_inv("support.plan.get", extra_args=["6"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_plan_get_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_plan_get(_inv("support.plan.get", extra_args=["6"], yes=True, confirm="6"))
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


def test_subscription_get_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_subscription_get(
            _inv("support.subscription.get", extra_args=["9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_subscription_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"fields": "plan_id,status"})
    support_cmd.support_subscription_get(
        _inv("support.subscription.get", extra_args=["9"], input_file=doc, yes=True, confirm="9")
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
    assert excinfo.value.code == "missing_field"


def test_subscription_create_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"plan_id": "cb-plan-1"})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_subscription_create(
            _inv(
                "support.subscription.create",
                extra_args=["9"],
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
            "plan_id": "cb-plan-1",
            "first_name": "Ann",
            "last_name": "Lee",
            "email": "ann@x.com",
            "company_name": "Acme",
        },
    )
    support_cmd.support_subscription_create(
        _inv(
            "support.subscription.create",
            extra_args=["9"],
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
    assert excinfo.value.code == "missing_field"


def test_subscription_update_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"subscription_id": "sub-1"})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_subscription_update(
            _inv(
                "support.subscription.update",
                extra_args=["9"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_subscription_update_proceeds(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"subscription_id": "sub-1"})
    support_cmd.support_subscription_update(
        _inv(
            "support.subscription.update",
            extra_args=["9"],
            input_file=doc,
            yes=True,
            confirm="9",
        )
    )
    assert fake_service.call_log == [
        (_SUBSCRIPTION_UPDATE, {"workspace_id": 9, "subscription_id": "sub-1"})
    ]


# --- user.list-all -------------------------------------------------------------------------


def test_user_list_all_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_user_list_all(_inv("support.user.list-all", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_user_list_all_forwards_pagination(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"limit": 10, "offset": 5, "sort": "(email:asc)"})
    support_cmd.support_user_list_all(
        _inv("support.user.list-all", input_file=doc, yes=True, confirm="4")
    )
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


def test_workspace_list_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_list(_inv("support.workspace.list", output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_list_proceeds(fake_service: FakeMammothService) -> None:
    support_cmd.support_workspace_list(_inv("support.workspace.list", yes=True, confirm="4"))
    assert fake_service.call_log == [(_WORKSPACE_LIST, {})]


# --- workspace.get -------------------------------------------------------------------------


def test_workspace_get_requires_positional(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_get(_inv("support.workspace.get", yes=True))
    assert excinfo.value.code == "missing_argument"


def test_workspace_get_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_get(
            _inv("support.workspace.get", extra_args=["9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_get_forwards_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"fields": "name,plan_id"})
    support_cmd.support_workspace_get(
        _inv("support.workspace.get", extra_args=["9"], input_file=doc, yes=True, confirm="9")
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


def test_workspace_user_list_blocked(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_list(
            _inv("support.workspace.user.list", extra_args=["9"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_user_list_forwards_pagination(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"limit": 20, "offset": 0, "sort": "(email:asc)"})
    support_cmd.support_workspace_user_list(
        _inv(
            "support.workspace.user.list",
            extra_args=["9"],
            input_file=doc,
            yes=True,
            confirm="9",
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
    assert excinfo.value.code == "missing_field"


def test_workspace_user_remove_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"user_id": 2})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_remove(
            _inv(
                "support.workspace.user.remove",
                extra_args=["9"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_user_remove_proceeds(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"user_id": 2})
    support_cmd.support_workspace_user_remove(
        _inv(
            "support.workspace.user.remove",
            extra_args=["9"],
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
    assert excinfo.value.code == "missing_field"


def test_workspace_user_transfer_blocked(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"user_id": 2, "role": "workspace_admin"})
    with pytest.raises(CliError) as excinfo:
        support_cmd.support_workspace_user_transfer(
            _inv(
                "support.workspace.user.transfer",
                extra_args=["9"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_workspace_user_transfer_forwards_remove_role(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path, {"user_id": 2, "role": "workspace_admin", "remove_role": "workspace_member"}
    )
    support_cmd.support_workspace_user_transfer(
        _inv(
            "support.workspace.user.transfer",
            extra_args=["9"],
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
