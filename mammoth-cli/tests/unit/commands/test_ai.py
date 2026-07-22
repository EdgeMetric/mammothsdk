"""Unit tests for the ``ai`` command handlers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mammoth_cli.commands import ai as ai_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_CONDITION_GENERATE = "mammoth.api.ai.AIAPI.condition_generate"
_EXPRESSION_GENERATE = "mammoth.api.ai.AIAPI.expression_generate"
_SQL_GENERATE = "mammoth.api.ai.AIAPI.generate_sql"
_SUGGESTION_LIST = "mammoth.api.ai.AIAPI.get_suggestions"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write_input(tmp_path: Path, payload: dict[str, object]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# ── ai.condition.generate ────────────────────────────────────────────────────


def test_condition_generate_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_condition_generate(_inv("ai.condition.generate", extra_args=["12"]))
    assert excinfo.value.code == "project_required"


def test_condition_generate_requires_dataset_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_condition_generate(_inv("ai.condition.generate", project=180))
    assert excinfo.value.code == "missing_argument"


def test_condition_generate_invalid_dataset_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_condition_generate(
            _inv("ai.condition.generate", project=180, extra_args=["abc"])
        )
    assert excinfo.value.code == "invalid_argument"


def test_condition_generate_requires_intent(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_condition_generate(
            _inv("ai.condition.generate", project=180, extra_args=["12"])
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_condition_generate_minimal_call(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write_input(tmp_path, {"intent": "rows over 10"})
    ai_cmd.ai_condition_generate(
        _inv("ai.condition.generate", project=180, extra_args=["12"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (
            _CONDITION_GENERATE,
            {"intent": "rows over 10", "dataset_id": 12, "project_id": 180},
        )
    ]


def test_condition_generate_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write_input(
        tmp_path, {"intent": "rows over 10", "dataview_id": 99, "sequence_number": 3}
    )
    ai_cmd.ai_condition_generate(
        _inv("ai.condition.generate", project=180, extra_args=["12"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (
            _CONDITION_GENERATE,
            {
                "intent": "rows over 10",
                "dataset_id": 12,
                "project_id": 180,
                "dataview_id": 99,
                "sequence_number": 3,
            },
        )
    ]


def test_condition_generate_returns_response_and_meta(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_CONDITION_GENERATE] = {"condition": {"op": "gt"}}
    input_file = _write_input(tmp_path, {"intent": "rows over 10"})
    data, meta = ai_cmd.ai_condition_generate(
        _inv("ai.condition.generate", project=180, extra_args=["12"], input_file=input_file)
    )
    assert data == {"condition": {"op": "gt"}}
    assert meta == {"profile": None, "workspace_id": 4, "project_id": 180}


# ── ai.expression.generate ───────────────────────────────────────────────────


def test_expression_generate_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_expression_generate(_inv("ai.expression.generate", extra_args=["12"]))
    assert excinfo.value.code == "project_required"


def test_expression_generate_requires_dataset_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_expression_generate(_inv("ai.expression.generate", project=180))
    assert excinfo.value.code == "missing_argument"


def test_expression_generate_requires_intent(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_expression_generate(
            _inv("ai.expression.generate", project=180, extra_args=["12"])
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_expression_generate_requires_mode(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write_input(tmp_path, {"intent": "total sales"})
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_expression_generate(
            _inv("ai.expression.generate", project=180, extra_args=["12"], input_file=input_file)
        )
    assert excinfo.value.code == "missing_field"
    assert fake_service.call_log == []


def test_expression_generate_minimal_call(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write_input(tmp_path, {"intent": "total sales", "mode": "metric"})
    ai_cmd.ai_expression_generate(
        _inv("ai.expression.generate", project=180, extra_args=["12"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (
            _EXPRESSION_GENERATE,
            {
                "intent": "total sales",
                "mode": "metric",
                "dataset_id": 12,
                "project_id": 180,
            },
        )
    ]


def test_expression_generate_forwards_optional_fields(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "intent": "total sales",
            "mode": "math",
            "dataview_id": 55,
            "sequence_number": 1,
        },
    )
    ai_cmd.ai_expression_generate(
        _inv("ai.expression.generate", project=180, extra_args=["12"], input_file=input_file)
    )
    assert fake_service.call_log == [
        (
            _EXPRESSION_GENERATE,
            {
                "intent": "total sales",
                "mode": "math",
                "dataset_id": 12,
                "project_id": 180,
                "dataview_id": 55,
                "sequence_number": 1,
            },
        )
    ]


# ── ai.sql.generate ──────────────────────────────────────────────────────────


def test_sql_generate_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_sql_generate(_inv("ai.sql.generate", extra_args=["total sales by region"]))
    assert excinfo.value.code == "project_required"
    assert fake_service.call_log == []


def test_sql_generate_requires_intent(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_sql_generate(_inv("ai.sql.generate", project=180))
    assert excinfo.value.code == "missing_argument"
    assert fake_service.call_log == []


def test_sql_generate_uses_positional_intent(fake_service: FakeMammothService) -> None:
    ai_cmd.ai_sql_generate(
        _inv("ai.sql.generate", project=180, extra_args=["total sales by region"])
    )
    assert fake_service.call_log == [(_SQL_GENERATE, {"intent": "total sales by region"})]


def test_sql_generate_uses_intent_input_field(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write_input(tmp_path, {"intent": "total sales by region"})
    ai_cmd.ai_sql_generate(_inv("ai.sql.generate", project=180, input_file=input_file))
    assert fake_service.call_log == [(_SQL_GENERATE, {"intent": "total sales by region"})]


def test_sql_generate_forwards_sequence_number(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    input_file = _write_input(tmp_path, {"sequence_number": 2})
    ai_cmd.ai_sql_generate(
        _inv(
            "ai.sql.generate",
            project=180,
            extra_args=["total sales by region"],
            input_file=input_file,
        )
    )
    assert fake_service.call_log == [
        (_SQL_GENERATE, {"intent": "total sales by region", "sequence_number": 2})
    ]


def test_sql_generate_returns_response_and_meta(fake_service: FakeMammothService) -> None:
    fake_service.responses[_SQL_GENERATE] = {"sql": "SELECT 1"}
    data, meta = ai_cmd.ai_sql_generate(
        _inv("ai.sql.generate", project=180, extra_args=["total sales by region"])
    )
    assert data == {"sql": "SELECT 1"}
    assert meta == {"profile": None, "workspace_id": 4, "project_id": 180}


# ── ai.suggestion.list ───────────────────────────────────────────────────────


def test_suggestion_list_requires_project(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        ai_cmd.ai_suggestion_list(_inv("ai.suggestion.list"))
    assert excinfo.value.code == "project_required"
    assert fake_service.call_log == []


def test_suggestion_list_calls_with_no_kwargs(fake_service: FakeMammothService) -> None:
    ai_cmd.ai_suggestion_list(_inv("ai.suggestion.list", project=180))
    assert fake_service.call_log == [(_SUGGESTION_LIST, {})]


def test_suggestion_list_returns_response_and_meta(fake_service: FakeMammothService) -> None:
    fake_service.responses[_SUGGESTION_LIST] = {"suggestions": []}
    data, meta = ai_cmd.ai_suggestion_list(_inv("ai.suggestion.list", project=180))
    assert data == {"suggestions": []}
    assert meta == {"profile": None, "workspace_id": 4, "project_id": 180}
