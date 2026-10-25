"""``mammoth run``: references to skipped lines and operator objects (#318, second review)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.app import app
from mammoth_cli.commands import run as run_cmd
from mammoth_cli.context import resolver
from mammoth_cli.runtime import bindings
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_BASE = ["--output", "json", "--project", "9"]
_SKIPPED = {"cmd": "dataset get", "args": [7], "name": "a", "when": {"eq": [1, 2]}}
_READS_IT = {"cmd": "dataset get", "args": ["{{steps.a.data.dataset.id}}"]}


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture(autouse=True)
def _service(monkeypatch: pytest.MonkeyPatch) -> None:
    def build(*_a: Any, **_k: Any) -> FakeMammothService:
        service = FakeMammothService()
        service.responses[_DATASET_GET] = {"dataset": {"id": 7, "name": "sales"}}
        return service

    monkeypatch.setattr(service_factory, "build_service", build)
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_a, **_k: 4)


def _run(tmp_path: Path, *argv: str) -> tuple[int, list[dict[str, Any]]]:
    path = tmp_path / "commands.jsonl"
    path.write_text("\n".join(json.dumps(line) for line in (_SKIPPED, _READS_IT)) + "\n")
    result = make_runner()._runner.invoke(app, ["run", str(path), *argv, *_BASE])
    return result.exit_code, [json.loads(t) for t in result.stdout.split("\n") if t.strip()]


def test_a_real_run_fails_on_a_reference_to_a_skipped_line(tmp_path: Path) -> None:
    code, lines = _run(tmp_path)
    assert lines[0]["skipped"] is True
    assert code == 2 and lines[1]["error"]["code"] == "unresolved_reference"


def test_a_dry_run_fails_on_it_too_and_does_not_plan_it(tmp_path: Path) -> None:
    code, lines = _run(tmp_path, "--dry-run")
    assert code == 2, lines
    assert lines[1]["error"]["code"] == "unresolved_reference"


def test_a_skipped_step_is_not_a_preview() -> None:
    steps = {"a": {"skipped": True, "data": None, "exit": 0}, "b": {"data": {}, "exit": 0}}
    assert run_cmd._reads_a_preview("steps.b.data.x", steps) is True
    assert run_cmd._reads_a_preview("steps.a.data.x", steps) is False
    assert run_cmd._reads_a_preview("steps.zzz.data.x", steps) is False


def test_a_condition_on_a_planned_write_waits_but_one_on_a_real_read_does_not() -> None:
    steps = {
        "w": {"data": {"would_call": {"sdk_symbol": "X"}}, "exit": 0},
        "r": {"data": {"dataset": {"id": 1}}, "exit": 0},
        "s": {"skipped": True, "data": None, "exit": 0},
    }
    assert run_cmd._waits_on_preview({"present": "{{steps.w.data.id}}"}, steps) is True
    assert run_cmd._waits_on_preview({"present": "{{steps.r.data.id}}"}, steps) is False
    assert run_cmd._waits_on_preview({"present": "{{steps.s.data.id}}"}, steps) is False


@pytest.mark.parametrize("operator", ["$first", "$keys", "$default", "$without"])
def test_an_operator_beside_other_keys_is_an_error(operator: str) -> None:
    with pytest.raises(bindings.BindingError, match="only key"):
        bindings.resolve({operator: [1], "extra": 1}, {})


def test_other_dollar_keys_stay_data() -> None:
    assert bindings.resolve({"$schema": "x", "a": 1}, {}) == {"$schema": "x", "a": 1}
    assert bindings.resolve({"$first": [4, 5]}, {}) == 4
