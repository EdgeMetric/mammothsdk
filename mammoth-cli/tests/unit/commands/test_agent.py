"""Unit tests for the ``agent`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import agent as agent_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_CHAT = "mammoth.api.agents.AgentsAPI.chat"
_SESSION_DELETE = "mammoth.api.agents.AgentsAPI.session_delete"
_SESSION_LIST = "mammoth.api.agents.AgentsAPI.session_list"
_SESSION_MESSAGES = "mammoth.api.agents.AgentsAPI.session_messages"
_SESSION_SET_VISIBILITY = "mammoth.api.agents.AgentsAPI.session_set_visibility"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# --- agent chat --------------------------------------------------------------


def test_chat_requires_message(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"scope": {"type": "workspace"}})
    with pytest.raises(CliError) as excinfo:
        agent_cmd.agent_chat(_inv("agent.chat", input_file=doc))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_chat_requires_scope(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"message": "hello"})
    with pytest.raises(CliError) as excinfo:
        agent_cmd.agent_chat(_inv("agent.chat", input_file=doc))
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_chat_passes_required_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"message": "hello", "scope": {"type": "workspace"}})
    agent_cmd.agent_chat(_inv("agent.chat", input_file=doc))
    assert fake_service.call_log == [
        (_CHAT, {"message": "hello", "scope": {"type": "workspace"}, "wait": 120})
    ]


def test_chat_forwards_optional_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        {
            "message": "hello",
            "scope": {"type": "workspace"},
            "agent_key": "insights",
            "session_id": "s-1",
            "client_context": {"page": "home"},
            "selection": {"rows": [1, 2]},
        },
    )
    agent_cmd.agent_chat(_inv("agent.chat", input_file=doc))
    assert fake_service.call_log == [
        (
            _CHAT,
            {
                "message": "hello",
                "scope": {"type": "workspace"},
                "agent_key": "insights",
                "session_id": "s-1",
                "client_context": {"page": "home"},
                "selection": {"rows": [1, 2]},
                "wait": 120,
            },
        )
    ]


def test_chat_forwards_the_intelligence_level(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path, {"message": "hi", "scope": {"type": "workspace"}, "intelligence": "expert"}
    )
    agent_cmd.agent_chat(_inv("agent.chat", input_file=doc))
    assert fake_service.call_log[0][1]["intelligence"] == "expert"


def test_chat_reports_active_project_in_meta(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"message": "hello", "scope": {"type": "workspace"}})
    _, meta = agent_cmd.agent_chat(_inv("agent.chat", project=180, input_file=doc))
    assert meta == {"profile": None, "workspace_id": 4, "project_id": 180}


# --- agent session delete -----------------------------------------------------


def test_session_delete_requires_session_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        agent_cmd.agent_session_delete(_inv("agent.session.delete", yes=True))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_session_delete_blocked_without_confirmation(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        agent_cmd.agent_session_delete(
            _inv("agent.session.delete", extra_args=["s-1"], output="json")
        )
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_session_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    agent_cmd.agent_session_delete(_inv("agent.session.delete", extra_args=["s-1"], yes=True))
    assert fake_service.call_log == [(_SESSION_DELETE, {"session_id": "s-1"})]


# --- agent session list --------------------------------------------------------


def test_session_list_with_no_input(fake_service: FakeMammothService) -> None:
    agent_cmd.agent_session_list(_inv("agent.session.list"))
    assert fake_service.call_log == [(_SESSION_LIST, {})]


def test_session_list_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {"agent_key": "insights", "limit": 10, "offset": 5, "include_shared": True},
    )
    agent_cmd.agent_session_list(_inv("agent.session.list", input_file=doc))
    assert fake_service.call_log == [
        (
            _SESSION_LIST,
            {"agent_key": "insights", "limit": 10, "offset": 5, "include_shared": True},
        )
    ]


def test_session_list_never_forwards_workspace_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"workspace_id": 999, "limit": 10})
    with pytest.raises(CliError) as excinfo:
        agent_cmd.agent_session_list(_inv("agent.session.list", input_file=doc))
    assert excinfo.value.code == "unknown_input_field"


# --- agent session messages -----------------------------------------------------


def test_session_messages_requires_session_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        agent_cmd.agent_session_messages(_inv("agent.session.messages"))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_session_messages_uses_positional_session_id(
    fake_service: FakeMammothService,
) -> None:
    agent_cmd.agent_session_messages(_inv("agent.session.messages", extra_args=["s-1"]))
    assert fake_service.call_log == [(_SESSION_MESSAGES, {"session_id": "s-1"})]


# --- agent session set-visibility -----------------------------------------------


def test_session_set_visibility_requires_session_id(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"visibility": "shared"})
    with pytest.raises(CliError) as excinfo:
        agent_cmd.agent_session_set_visibility(_inv("agent.session.set-visibility", input_file=doc))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_session_set_visibility_requires_visibility_field(
    fake_service: FakeMammothService,
) -> None:
    with pytest.raises(CliError) as excinfo:
        agent_cmd.agent_session_set_visibility(
            _inv("agent.session.set-visibility", extra_args=["s-1"])
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_session_set_visibility_proceeds(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"visibility": "shared"})
    agent_cmd.agent_session_set_visibility(
        _inv("agent.session.set-visibility", extra_args=["s-1"], input_file=doc)
    )
    assert fake_service.call_log == [
        (_SESSION_SET_VISIBILITY, {"session_id": "s-1", "visibility": "shared"})
    ]


# --- agent run stop -------------------------------------------------------------------------


def test_run_stop_names_the_run_and_session_when_the_server_refuses_the_run_id(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses["mammoth.api.agents.AgentsAPI.run_stop"] = CliError(
        code="api_error", message="Mammoth returned an API error."
    )
    with pytest.raises(CliError) as excinfo:
        agent_cmd.agent_run_stop(_inv("agent.run.stop", session="sess-1", extra_args=["run-9"]))
    assert "run-9" in excinfo.value.message
    assert "sess-1" in excinfo.value.message
    assert "agent run status --session" in (excinfo.value.hint or "")


@pytest.mark.parametrize("verb", ["pause", "resume", "stop", "extend", "retry"])
def test_run_command_example_shows_the_session_flag(verb: str) -> None:
    from mammoth_cli.manifest.loader import command_by_id

    record = command_by_id(f"agent.run.{verb}")
    assert record is not None
    assert f"mammoth agent run {verb} resource-123 --session session-123" in (
        record["agent_example"]
    )
