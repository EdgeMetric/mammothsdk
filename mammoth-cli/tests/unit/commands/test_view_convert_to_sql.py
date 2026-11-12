"""``view task convert-plan``, ``convert-generate`` and ``convert``: rules to one SQL rule."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands.view import convert_to_sql as convert_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_PREFIX = "mammoth.api.pipeline.PipelineAPI"
_TASK_LIST = f"{_PREFIX}.list_tasks"
_PLAN = f"{_PREFIX}.plan_sql_conversion"
_CONVERT = f"{_PREFIX}.convert_to_sql"
_PREVIEW = f"{_PREFIX}.preview_task"
_GENERATE = "mammoth.api.ai.AIAPI.generate_sql"
_DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"

#: Rules 1 to 4 have task ids 11 to 14.
_TASKS = {"tasks": [{"id": 10 + n, "sequence": n} for n in range(1, 5)]}
_QUERY = 'SELECT a FROM "view:7" WHERE a > 1'


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def service(fake_service: FakeMammothService) -> FakeMammothService:
    fake_service.responses[_TASK_LIST] = _TASKS
    return fake_service


def _inv(command_id: str, payload: dict[str, Any], tmp_path: Path, **overrides: Any) -> Invocation:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"dataset_id": 9, **payload}), encoding="utf-8")
    return Invocation(
        command_id=command_id,
        extra_args=["7"],
        input_file=str(doc),
        **overrides,  # type: ignore[arg-type]
    )


def _calls(service: FakeMammothService, symbol: str) -> list[dict[str, Any]]:
    return [kwargs for name, kwargs in service.call_log if name == symbol]


def test_plan_shows_groups_and_cuts_in_rule_numbers(
    service: FakeMammothService, tmp_path: Path
) -> None:
    service.responses[_PLAN] = {
        "groups": [{"task_ids": [11, 12, 13], "first_sequence": 1, "last_sequence": 3}],
        "cuts": [{"sequence": 4, "task_id": 14, "reason": "rule_type_not_supported"}],
    }

    data, _ = convert_cmd.view_task_convert_plan(
        _inv("view.task.convert-plan", {"rules": "1-4"}, tmp_path)
    )

    assert data["groups"] == [
        {"rules": [1, 2, 3], "first_rule": 1, "last_rule": 3, "task_ids": [11, 12, 13]}
    ]
    assert data["cuts"][0]["rule"] == 4
    assert data["cuts"][0]["reason"] == "rule_type_not_supported"
    assert "join, lookup" in data["cuts"][0]["why"]
    assert data["changed"] is False
    assert _calls(service, _PLAN) == [
        {"dataview_id": 7, "dataset_id": 9, "task_ids": [11, 12, 13, 14]}
    ]
    assert _calls(service, _CONVERT) == []


def test_plan_without_rules_plans_the_whole_pipeline(
    service: FakeMammothService, tmp_path: Path
) -> None:
    service.responses[_PLAN] = {"groups": [], "cuts": []}

    convert_cmd.view_task_convert_plan(_inv("view.task.convert-plan", {}, tmp_path))

    assert _calls(service, _PLAN) == [{"dataview_id": 7, "dataset_id": 9}]


def test_plan_refuses_a_rule_that_does_not_exist(
    service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as excinfo:
        convert_cmd.view_task_convert_plan(
            _inv("view.task.convert-plan", {"rules": [3, 9]}, tmp_path)
        )

    assert "no rule 9" in excinfo.value.message
    assert _calls(service, _PLAN) == []


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1-3", [1, 2, 3]), ("1,3,5-6", [1, 3, 5, 6]), ([2, "4-5"], [2, 4, 5]), (3, [3])],
)
def test_rules_are_read_from_ranges_and_lists(value: Any, expected: list[int]) -> None:
    assert convert_cmd.parse_rules(value) == expected


@pytest.mark.parametrize("value", ["a", "5-2", 0, [True]])
def test_a_bad_rule_number_is_refused(value: Any) -> None:
    with pytest.raises(CliError):
        convert_cmd.parse_rules(value)


def test_plan_on_a_server_without_the_route_says_so(
    service: FakeMammothService, tmp_path: Path
) -> None:
    service.responses[_PLAN] = CliError(code="resource_not_found", message="not found")

    with pytest.raises(CliError) as excinfo:
        convert_cmd.view_task_convert_plan(_inv("view.task.convert-plan", {}, tmp_path))

    assert "does not support convert-to-sql yet" in excinfo.value.message


def _generate_group_input() -> dict[str, Any]:
    return {"groups": [{"rules": "1-3", "text": "Keep rows where a is above 1."}]}


def test_generate_passes_task_ids_and_changes_nothing(
    service: FakeMammothService, tmp_path: Path
) -> None:
    service.responses[_GENERATE] = {"response": {"result": _QUERY}}
    service.responses[_PREVIEW] = {"rows": [[2]]}
    service.responses[_DATAVIEW_GET] = {"name": "Sales"}

    data, _ = convert_cmd.view_task_convert_generate(
        _inv("view.task.convert-generate", _generate_group_input(), tmp_path)
    )

    assert _calls(service, _GENERATE) == [
        {
            "intent": "Keep rows where a is above 1.",
            "sequence_number": 1,
            "dataset_id": 9,
            "dataview_id": 7,
            "task_ids": [11, 12, 13],
        }
    ]
    assert _calls(service, _PREVIEW)[0]["task_spec"] == {
        "DATAVIEW_ID": 7,
        "SEQUENCE_NUMBER": 1,
        "SQL": {"USER_QUERY": _QUERY, "INTENT": "Keep rows where a is above 1."},
    }
    assert _calls(service, _CONVERT) == []
    assert data["changed"] is False
    assert data["groups"][0]["sql"] == _QUERY
    assert data["groups"][0]["preview"] == {"rows": [[2]]}


def test_generate_returns_a_convert_command_with_the_previewed_query(
    service: FakeMammothService, tmp_path: Path
) -> None:
    service.responses[_GENERATE] = {"response": {"result": _QUERY}}
    service.responses[_PREVIEW] = {"rows": []}
    service.responses[_DATAVIEW_GET] = {"name": "Sales"}

    data, _ = convert_cmd.view_task_convert_generate(
        _inv("view.task.convert-generate", _generate_group_input(), tmp_path)
    )

    command = data["convert"]
    assert command.startswith("mammoth view task convert 7 --input ")
    body = json.loads(command.split("--input ", 1)[1].strip("'"))
    assert body["groups"] == [
        {"task_ids": [11, 12, 13], "text": "Keep rows where a is above 1.", "query": _QUERY}
    ]


def test_generate_refuses_a_blank_text_before_any_request(
    service: FakeMammothService, tmp_path: Path
) -> None:
    payload = {"groups": [{"rules": "1-3", "text": "   "}]}

    with pytest.raises(CliError) as excinfo:
        convert_cmd.view_task_convert_generate(
            _inv("view.task.convert-generate", payload, tmp_path)
        )

    assert excinfo.value.code == "missing_field"
    assert service.call_log == []


def _convert_input(**group: Any) -> dict[str, Any]:
    return {
        "groups": [
            {"rules": "1-3", "text": "Keep rows where a is above 1.", "query": _QUERY, **group},
            {"task_ids": [14, 13], "text": "Second.", "query": "SELECT 1"},
        ]
    }


def test_convert_sends_one_request_with_all_groups(
    service: FakeMammothService, tmp_path: Path
) -> None:
    service.responses[_CONVERT] = {"status": "done"}

    data, _ = convert_cmd.view_task_convert(
        _inv("view.task.convert", _convert_input(), tmp_path, yes=True)
    )

    assert data == {"status": "done"}
    assert _calls(service, _CONVERT) == [
        {
            "dataview_id": 7,
            "dataset_id": 9,
            "groups": [
                {
                    "task_ids": [11, 12, 13],
                    "SQL": {"USER_QUERY": _QUERY, "INTENT": "Keep rows where a is above 1."},
                },
                {"task_ids": [14, 13], "SQL": {"USER_QUERY": "SELECT 1", "INTENT": "Second."}},
            ],
        }
    ]


@pytest.mark.parametrize("blank", ["", "   ", None])
def test_convert_refuses_a_blank_text_before_any_request(
    service: FakeMammothService, tmp_path: Path, blank: str | None
) -> None:
    with pytest.raises(CliError) as excinfo:
        convert_cmd.view_task_convert(
            _inv("view.task.convert", _convert_input(text=blank), tmp_path, yes=True)
        )

    assert excinfo.value.code == "missing_field"
    assert "Group 1" in excinfo.value.message
    assert service.call_log == []


def test_convert_refuses_a_blank_query_before_any_request(
    service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError):
        convert_cmd.view_task_convert(
            _inv("view.task.convert", _convert_input(query=" "), tmp_path, yes=True)
        )

    assert service.call_log == []


def test_convert_asks_for_approval_and_sends_nothing_without_it(
    service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as excinfo:
        convert_cmd.view_task_convert(
            _inv("view.task.convert", _convert_input(), tmp_path, output="json")
        )

    assert excinfo.value.code == "confirmation_required"
    assert _calls(service, _CONVERT) == []


def test_convert_on_a_server_without_the_route_says_so_and_does_not_fall_back(
    service: FakeMammothService, tmp_path: Path
) -> None:
    service.responses[_CONVERT] = CliError(code="resource_not_found", message="not found")

    with pytest.raises(CliError) as excinfo:
        convert_cmd.view_task_convert(
            _inv("view.task.convert", _convert_input(), tmp_path, yes=True)
        )

    assert excinfo.value.message == "This server does not support convert-to-sql yet."
    assert "Do not delete the rules one by one" in (excinfo.value.hint or "")
    assert [name for name, _ in service.call_log if name.endswith("delete_task")] == []


def test_convert_names_a_refusal_in_plain_words(
    service: FakeMammothService, tmp_path: Path
) -> None:
    service.responses[_CONVERT] = CliError(
        code="api_error", message="raw", details={"backend_code": "4DTVW043", "status_code": 400}
    )

    with pytest.raises(CliError) as excinfo:
        convert_cmd.view_task_convert(
            _inv("view.task.convert", _convert_input(), tmp_path, yes=True)
        )

    assert "checkpoint, data check or export sits between the rules" in excinfo.value.message
    assert excinfo.value.details["backend_code"] == "4DTVW043"


def test_convert_is_classed_like_task_delete() -> None:
    convert = command_by_id("view.task.convert")
    delete = command_by_id("view.task.delete")

    assert convert is not None and delete is not None
    for key in ("mutation_class", "edits_target", "confirmation"):
        assert convert[key] == delete[key]
    for plan in ("view.task.convert-plan", "view.task.convert-generate"):
        record = command_by_id(plan)
        assert record is not None and record["mutation_class"] == "read"
