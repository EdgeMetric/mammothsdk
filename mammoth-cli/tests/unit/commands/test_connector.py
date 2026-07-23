"""Unit tests for the ``connector`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import connector as connector_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_ACTIVE = "mammoth.api.connectors.ConnectorsAPI.active_connectors"
_AI_CHAT = "mammoth.api.connector_ai.ConnectorAIAPI.chat"
_AI_HISTORY = "mammoth.api.connector_ai.ConnectorAIAPI.history"
_AI_SESSION_LIST = "mammoth.api.connector_ai.ConnectorAIAPI.session_list"
_AI_SESSION_MESSAGES = "mammoth.api.connector_ai.ConnectorAIAPI.session_messages"
_AI_SUBMIT_COLUMN_SELECTION = "mammoth.api.connector_ai.ConnectorAIAPI.submit_column_selection"
_AI_SUBMIT_CREDENTIALS = "mammoth.api.connector_ai.ConnectorAIAPI.submit_credentials"
_CONNECTION_CREATE = "mammoth.api.connectors.ConnectorsAPI.create_connection"
_CONNECTION_DELETE = "mammoth.api.connectors.ConnectorsAPI.delete_connection"
_CONNECTION_GET = "mammoth.api.connectors.ConnectorsAPI.get_connection"
_CONNECTION_LIST = "mammoth.api.connectors.ConnectorsAPI.list_connections"
_CONNECTION_UPDATE = "mammoth.api.connectors.ConnectorsAPI.update_connection"
_DS_CONFIG_CREATE = "mammoth.api.connectors.ConnectorsAPI.create_ds_config"
_DS_CONFIG_DELETE = "mammoth.api.connectors.ConnectorsAPI.delete_ds_config"
_DS_CONFIG_DELETE_ALL = "mammoth.api.connectors.ConnectorsAPI.ds_config_delete_all"
_DS_CONFIG_GET = "mammoth.api.connectors.ConnectorsAPI.get_ds_config"
_DS_CONFIG_LIST = "mammoth.api.connectors.ConnectorsAPI.list_ds_configs"
_DS_CONFIG_UPDATE = "mammoth.api.connectors.ConnectorsAPI.update_ds_config"
_GET = "mammoth.api.connectors.ConnectorsAPI.get"
_LIST = "mammoth.api.connectors.ConnectorsAPI.list"
_QUERY_GENERATE = "mammoth.api.ai.AIAPI.query_gen"
_QUERY_STATUS = "mammoth.api.ai.AIAPI.status"


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


# --- active ------------------------------------------------------------------


def test_active_dispatches(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_active(_inv("connector.active"))
    assert fake_service.call_log == [(_ACTIVE, {})]


# --- get -----------------------------------------------------------------------


def test_get_requires_connector_key(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_get(_inv("connector.get"))
    assert excinfo.value.code == "missing_argument"


def test_get_uses_positional_connector_key(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_get(_inv("connector.get", extra_args=["postgres"]))
    assert fake_service.call_log == [(_GET, {"connector_key": "postgres"})]


# --- list ------------------------------------------------------------------------


def test_list_dispatches(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_list(_inv("connector.list"))
    assert fake_service.call_log == [(_LIST, {})]


# --- ai chat ---------------------------------------------------------------------


def test_ai_chat_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ai_chat(_inv("connector.ai.chat"))
    assert excinfo.value.code == "project_required"


def test_ai_chat_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ai_chat(_inv("connector.ai.chat", project=180))
    assert excinfo.value.code == "missing_field"


def test_ai_chat_dispatches(fake_service: FakeMammothService, tmp_path: Path) -> None:
    body = {"messages": [{"role": "user", "content": "connect postgres"}]}
    doc = _write(tmp_path, {"body": body})
    connector_cmd.connector_ai_chat(_inv("connector.ai.chat", project=180, input_file=doc))
    assert fake_service.call_log == [(_AI_CHAT, {"body": body, "project_id": 180})]


# --- ai history --------------------------------------------------------------------


def test_ai_history_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ai_history(_inv("connector.ai.history", extra_args=["conn1"]))
    assert excinfo.value.code == "project_required"


def test_ai_history_requires_connection_key(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ai_history(_inv("connector.ai.history", project=180))
    assert excinfo.value.code == "missing_argument"


def test_ai_history_dispatches(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_ai_history(
        _inv("connector.ai.history", project=180, extra_args=["conn1"])
    )
    assert fake_service.call_log == [(_AI_HISTORY, {"connection_key": "conn1", "project_id": 180})]


# --- ai session list -----------------------------------------------------------------


def test_ai_session_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ai_session_list(_inv("connector.ai.session.list"))
    assert excinfo.value.code == "project_required"


def test_ai_session_list_dispatches(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_ai_session_list(_inv("connector.ai.session.list", project=180))
    assert fake_service.call_log == [(_AI_SESSION_LIST, {"project_id": 180})]


# --- ai session messages -------------------------------------------------------------


def test_ai_session_messages_requires_session_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ai_session_messages(
            _inv("connector.ai.session.messages", project=180)
        )
    assert excinfo.value.code == "missing_argument"


def test_ai_session_messages_invalid_session_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ai_session_messages(
            _inv("connector.ai.session.messages", project=180, extra_args=["nope"])
        )
    assert excinfo.value.code == "invalid_argument"


def test_ai_session_messages_dispatches(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_ai_session_messages(
        _inv("connector.ai.session.messages", project=180, extra_args=["9"])
    )
    assert fake_service.call_log == [(_AI_SESSION_MESSAGES, {"session_id": 9, "project_id": 180})]


# --- ai submit-column-selection --------------------------------------------------------


def test_ai_submit_column_selection_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ai_submit_column_selection(
            _inv("connector.ai.submit-column-selection", project=180)
        )
    assert excinfo.value.code == "missing_field"


def test_ai_submit_column_selection_dispatches(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    body = {"selected_columns": ["a", "b"], "session_id": "s1"}
    doc = _write(tmp_path, {"body": body})
    connector_cmd.connector_ai_submit_column_selection(
        _inv("connector.ai.submit-column-selection", project=180, input_file=doc)
    )
    assert fake_service.call_log == [
        (_AI_SUBMIT_COLUMN_SELECTION, {"body": body, "project_id": 180})
    ]


# --- ai submit-credentials --------------------------------------------------------------


def test_ai_submit_credentials_requires_body(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ai_submit_credentials(
            _inv("connector.ai.submit-credentials", project=180)
        )
    assert excinfo.value.code == "missing_field"


def test_ai_submit_credentials_dispatches(fake_service: FakeMammothService, tmp_path: Path) -> None:
    body = {"credentials": {"username": "u", "password": "p"}, "session_id": "s1"}
    doc = _write(tmp_path, {"body": body})
    connector_cmd.connector_ai_submit_credentials(
        _inv("connector.ai.submit-credentials", project=180, input_file=doc)
    )
    assert fake_service.call_log == [
        (
            _AI_SUBMIT_CREDENTIALS,
            {"body": body, "project_id": 180},
        )
    ]


# --- connection create -------------------------------------------------------------------


def test_connection_create_requires_connector_key(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_create(
            _inv("connector.connection.create", project=180, yes=True)
        )
    assert excinfo.value.code == "missing_argument"


def test_connection_create_requires_config(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_create(
            _inv(
                "connector.connection.create",
                project=180,
                extra_args=["postgres"],
                yes=True,
            )
        )
    assert excinfo.value.code == "missing_field"


def test_connection_create_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"config": {"hostname": "db", "password": "s3cret"}})
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_create(
            _inv(
                "connector.connection.create",
                project=180,
                extra_args=["postgres"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connection_create_never_reads_config_from_positional(
    fake_service: FakeMammothService,
) -> None:
    """Even with a second positional present, config must come from --input."""
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_create(
            _inv(
                "connector.connection.create",
                project=180,
                extra_args=["postgres", "hostname=db;password=s3cret"],
                yes=True,
            )
        )
    assert excinfo.value.code == "missing_field"


def test_connection_create_dispatches_with_yes(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"config": {"hostname": "db", "password": "s3cret"}})
    connector_cmd.connector_connection_create(
        _inv(
            "connector.connection.create",
            project=180,
            extra_args=["postgres"],
            input_file=doc,
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (
            _CONNECTION_CREATE,
            {
                "connector_key": "postgres",
                "config": {"hostname": "db", "password": "s3cret"},
                "project_id": 180,
            },
        )
    ]


# --- connection delete -------------------------------------------------------------------


def test_connection_delete_requires_connection_key(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_delete(
            _inv("connector.connection.delete", project=180, extra_args=["postgres"], yes=True)
        )
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_connection_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_delete(
            _inv(
                "connector.connection.delete",
                project=180,
                extra_args=["postgres", "conn1"],
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connection_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_connection_delete(
        _inv(
            "connector.connection.delete",
            project=180,
            extra_args=["postgres", "conn1"],
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (
            _CONNECTION_DELETE,
            {"connector_key": "postgres", "connection_key": "conn1", "project_id": 180},
        )
    ]


# --- connection get -------------------------------------------------------------------


def test_connection_get_requires_both_keys(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_get(
            _inv("connector.connection.get", project=180, extra_args=["postgres"])
        )
    assert excinfo.value.code == "missing_argument"


def test_connection_get_dispatches(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_connection_get(
        _inv("connector.connection.get", project=180, extra_args=["postgres", "conn1"])
    )
    assert fake_service.call_log == [
        (
            _CONNECTION_GET,
            {"connector_key": "postgres", "connection_key": "conn1", "project_id": 180},
        )
    ]


# --- connection list -------------------------------------------------------------------


def test_connection_list_requires_connector_key(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_list(_inv("connector.connection.list", project=180))
    assert excinfo.value.code == "missing_argument"


def test_connection_list_dispatches(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_connection_list(
        _inv("connector.connection.list", project=180, extra_args=["postgres"])
    )
    assert fake_service.call_log == [
        (_CONNECTION_LIST, {"connector_key": "postgres", "project_id": 180})
    ]


# --- connection update -------------------------------------------------------------------


def test_connection_update_requires_credentials(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_update(
            _inv(
                "connector.connection.update",
                project=180,
                extra_args=["postgres", "conn1"],
                yes=True,
            )
        )
    assert excinfo.value.code == "missing_field"


def test_connection_update_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"credentials": {"password": "new-s3cret"}})
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_update(
            _inv(
                "connector.connection.update",
                project=180,
                extra_args=["postgres", "conn1"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_connection_update_never_reads_credentials_from_positional(
    fake_service: FakeMammothService,
) -> None:
    """Even with a third positional present, credentials must come from --input."""
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_connection_update(
            _inv(
                "connector.connection.update",
                project=180,
                extra_args=["postgres", "conn1", "password=new-s3cret"],
                yes=True,
            )
        )
    assert excinfo.value.code == "missing_field"


def test_connection_update_dispatches_with_yes(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"credentials": {"password": "new-s3cret"}})
    connector_cmd.connector_connection_update(
        _inv(
            "connector.connection.update",
            project=180,
            extra_args=["postgres", "conn1"],
            input_file=doc,
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (
            _CONNECTION_UPDATE,
            {
                "connector_key": "postgres",
                "connection_key": "conn1",
                "credentials": {"password": "new-s3cret"},
                "project_id": 180,
            },
        )
    ]


# --- ds-config create -------------------------------------------------------------------


def test_ds_config_create_requires_connection_key(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ds_config_create(
            _inv(
                "connector.ds-config.create",
                project=180,
                extra_args=["postgres"],
                yes=True,
            )
        )
    assert excinfo.value.code == "missing_argument"


def test_ds_config_create_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ds_config_create(
            _inv(
                "connector.ds-config.create",
                project=180,
                extra_args=["postgres", "conn1"],
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_ds_config_create_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"query": "select 1", "table": "t1", "data_sample": True})
    connector_cmd.connector_ds_config_create(
        _inv(
            "connector.ds-config.create",
            project=180,
            extra_args=["postgres", "conn1"],
            input_file=doc,
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (
            _DS_CONFIG_CREATE,
            {
                "connector_key": "postgres",
                "connection_key": "conn1",
                "project_id": 180,
                "query": "select 1",
                "table": "t1",
                "data_sample": True,
            },
        )
    ]


# --- ds-config delete -------------------------------------------------------------------


def test_ds_config_delete_requires_ds_config_key(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ds_config_delete(
            _inv(
                "connector.ds-config.delete",
                project=180,
                extra_args=["postgres", "conn1"],
                yes=True,
            )
        )
    assert excinfo.value.code == "missing_argument"


def test_ds_config_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ds_config_delete(
            _inv(
                "connector.ds-config.delete",
                project=180,
                extra_args=["postgres", "conn1", "ds1"],
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_ds_config_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_ds_config_delete(
        _inv(
            "connector.ds-config.delete",
            project=180,
            extra_args=["postgres", "conn1", "ds1"],
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (
            _DS_CONFIG_DELETE,
            {
                "connector_key": "postgres",
                "connection_key": "conn1",
                "ds_config_key": "ds1",
                "project_id": 180,
            },
        )
    ]


# --- ds-config delete-all -------------------------------------------------------------------


def test_ds_config_delete_all_requires_config_ids(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ds_config_delete_all(
            _inv(
                "connector.ds-config.delete-all",
                project=180,
                extra_args=["postgres", "conn1"],
                yes=True,
            )
        )
    assert excinfo.value.code == "missing_field"


def test_ds_config_delete_all_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"config_ids": ["ds1", "ds2"]})
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ds_config_delete_all(
            _inv(
                "connector.ds-config.delete-all",
                project=180,
                extra_args=["postgres", "conn1"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_ds_config_delete_all_proceeds_with_yes(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"config_ids": ["ds1", "ds2"]})
    connector_cmd.connector_ds_config_delete_all(
        _inv(
            "connector.ds-config.delete-all",
            project=180,
            extra_args=["postgres", "conn1"],
            input_file=doc,
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (
            _DS_CONFIG_DELETE_ALL,
            {
                "connector_key": "postgres",
                "connection_key": "conn1",
                "config_ids": ["ds1", "ds2"],
                "project_id": 180,
            },
        )
    ]


# --- ds-config get -------------------------------------------------------------------


def test_ds_config_get_requires_ds_config_key(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ds_config_get(
            _inv("connector.ds-config.get", project=180, extra_args=["postgres", "conn1"])
        )
    assert excinfo.value.code == "missing_argument"


def test_ds_config_get_dispatches(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_ds_config_get(
        _inv(
            "connector.ds-config.get",
            project=180,
            extra_args=["postgres", "conn1", "ds1"],
        )
    )
    assert fake_service.call_log == [
        (
            _DS_CONFIG_GET,
            {
                "connector_key": "postgres",
                "connection_key": "conn1",
                "ds_config_key": "ds1",
                "project_id": 180,
            },
        )
    ]


# --- ds-config list -------------------------------------------------------------------


def test_ds_config_list_requires_connection_key(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ds_config_list(
            _inv("connector.ds-config.list", project=180, extra_args=["postgres"])
        )
    assert excinfo.value.code == "missing_argument"


def test_ds_config_list_dispatches(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_ds_config_list(
        _inv("connector.ds-config.list", project=180, extra_args=["postgres", "conn1"])
    )
    assert fake_service.call_log == [
        (
            _DS_CONFIG_LIST,
            {"connector_key": "postgres", "connection_key": "conn1", "project_id": 180},
        )
    ]


# --- ds-config update -------------------------------------------------------------------


def test_ds_config_update_requires_patch(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ds_config_update(
            _inv(
                "connector.ds-config.update",
                project=180,
                extra_args=["postgres", "conn1", "ds1"],
                yes=True,
            )
        )
    assert excinfo.value.code == "missing_field"


def test_ds_config_update_blocked_without_confirmation(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"patch": [{"op": "replace", "path": "query", "value": "select 2"}]})
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_ds_config_update(
            _inv(
                "connector.ds-config.update",
                project=180,
                extra_args=["postgres", "conn1", "ds1"],
                input_file=doc,
                output="json",
            )
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_ds_config_update_dispatches_with_yes(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"patch": [{"op": "replace", "path": "query", "value": "select 2"}]})
    connector_cmd.connector_ds_config_update(
        _inv(
            "connector.ds-config.update",
            project=180,
            extra_args=["postgres", "conn1", "ds1"],
            input_file=doc,
            yes=True,
        )
    )
    assert fake_service.call_log == [
        (
            _DS_CONFIG_UPDATE,
            {
                "connector_key": "postgres",
                "connection_key": "conn1",
                "ds_config_key": "ds1",
                "patch": [{"op": "replace", "path": "query", "value": "select 2"}],
                "project_id": 180,
            },
        )
    ]


# --- query generate -------------------------------------------------------------------


def test_query_generate_requires_prompt(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_query_generate(
            _inv("connector.query.generate", project=180, extra_args=["postgres", "conn1"])
        )
    assert excinfo.value.code == "missing_field"


def test_query_generate_dispatches(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"prompt": "top customers by revenue"})
    connector_cmd.connector_query_generate(
        _inv(
            "connector.query.generate",
            project=180,
            extra_args=["postgres", "conn1"],
            input_file=doc,
        )
    )
    assert fake_service.call_log == [
        (
            _QUERY_GENERATE,
            {
                "connector_key": "postgres",
                "connection_key": "conn1",
                "prompt": "top customers by revenue",
                "project_id": 180,
            },
        )
    ]


# --- query status -------------------------------------------------------------------


def test_query_status_requires_connection_key(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        connector_cmd.connector_query_status(
            _inv("connector.query.status", project=180, extra_args=["postgres"])
        )
    assert excinfo.value.code == "missing_argument"


def test_query_status_dispatches(fake_service: FakeMammothService) -> None:
    connector_cmd.connector_query_status(
        _inv("connector.query.status", project=180, extra_args=["postgres", "conn1"])
    )
    assert fake_service.call_log == [
        (_QUERY_STATUS, {"connector_key": "postgres", "connection_key": "conn1", "project_id": 180})
    ]
