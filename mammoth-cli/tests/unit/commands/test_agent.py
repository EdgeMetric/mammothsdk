"""Unit tests for the ``agent`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import agent as agent_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_CHAT = "mammoth.api.agents.AgentsAPI.chat"
_SESSION_DELETE = "mammoth.api.agents.AgentsAPI.session_delete"
_SESSION_LIST = "mammoth.api.agents.AgentsAPI.session_list"
_SESSION_MESSAGES = "mammoth.api.agents.AgentsAPI.session_messages"
_SESSION_SET_VISIBILITY = "mammoth.api.agents.AgentsAPI.session_set_visibility"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


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
        (_CHAT, {"message": "hello", "scope": {"type": "workspace"}})
    ]


def test_chat_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
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
            },
        )
    ]


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
    agent_cmd.agent_session_list(_inv("agent.session.list", input_file=doc))
    assert fake_service.call_log == [(_SESSION_LIST, {"limit": 10})]


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
        agent_cmd.agent_session_set_visibility(
            _inv("agent.session.set-visibility", input_file=doc)
        )
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


def test_session_set_visibility_proceeds(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"visibility": "shared"})
    agent_cmd.agent_session_set_visibility(
        _inv("agent.session.set-visibility", extra_args=["s-1"], input_file=doc)
    )
    assert fake_service.call_log == [
        (_SESSION_SET_VISIBILITY, {"session_id": "s-1", "visibility": "shared"})
    ]
