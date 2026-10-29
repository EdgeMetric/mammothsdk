"""``mammoth run`` steps: a named line's result feeds later lines (#310).

``name`` keeps a line's envelope as ``steps.<name>``; ``args``, ``input`` and ``flags``
read it through ``{{...}}`` references; ``when`` skips a line; ``for_each`` runs a line
once per item. Nothing evaluates code: these are JSON expressions only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.app import app
from mammoth_cli.context import resolver
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_BASE = ["--output", "json", "--project", "9"]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    fake = FakeMammothService()
    fake.responses[_DATASET_GET] = {"dataset": {"id": 7, "name": "sales"}}
    monkeypatch.setattr(service_factory, "build_service", lambda *_a, **_k: fake)
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_a, **_k: 4)
    return fake


def _run(tmp_path: Path, *lines: Any, extra: tuple[str, ...] = ()) -> tuple[int, list[Any]]:
    path = tmp_path / "steps.jsonl"
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
    result = make_runner()._runner.invoke(app, ["run", str(path), *_BASE, *extra])
    return result.exit_code, [json.loads(text) for text in result.stdout.splitlines() if text]


def _dataset_ids(service: FakeMammothService) -> list[Any]:
    return [
        kwargs.get("dataset_id") for symbol, kwargs in service.call_log if symbol == _DATASET_GET
    ]


def test_a_reference_reads_an_earlier_named_line(
    service: FakeMammothService, tmp_path: Path
) -> None:
    code, lines = _run(
        tmp_path,
        {"cmd": "dataset get", "args": [7], "name": "first"},
        {"cmd": "dataset get", "args": ["{{steps.first.data.dataset.id}}"]},
    )
    assert code == 0, lines
    assert [line["exit"] for line in lines[:2]] == [0, 0]
    assert _dataset_ids(service) == [7, 7]


def test_when_false_skips_the_line(service: FakeMammothService, tmp_path: Path) -> None:
    code, lines = _run(
        tmp_path,
        {"cmd": "dataset get", "args": [7], "name": "first"},
        {
            "cmd": "dataset get",
            "args": [7],
            "when": {"eq": ["{{steps.first.data.dataset.name}}", "x"]},
        },
        {
            "cmd": "dataset get",
            "args": [7],
            "when": {"eq": ["{{steps.first.data.dataset.name}}", "sales"]},
        },
    )
    assert code == 0, lines
    assert lines[1]["skipped"] is True and lines[1]["exit"] == 0
    assert "skipped" not in lines[2]
    assert len(_dataset_ids(service)) == 2
    assert lines[-1]["data"]["ok"] == 3


def test_for_each_runs_once_per_item(service: FakeMammothService, tmp_path: Path) -> None:
    code, lines = _run(
        tmp_path,
        {"cmd": "dataset get", "args": [7], "name": "first"},
        {
            "cmd": "dataset get",
            "args": ["{{item}}"],
            "for_each": ["{{steps.first.data.dataset.id}}", 7],
            "name": "each",
            "when": {"present": "{{steps.first.data.dataset.id}}"},
        },
    )
    assert code == 0, lines
    each = [line for line in lines if line.get("line") == 2]
    assert [line["item"] for line in each] == [0, 1]
    assert _dataset_ids(service) == [7, 7, 7]


def test_for_each_needs_a_list(service: FakeMammothService, tmp_path: Path) -> None:
    code, lines = _run(
        tmp_path,
        {"cmd": "dataset get", "args": [7], "name": "first"},
        {"cmd": "dataset get", "args": ["{{item}}"], "for_each": "{{steps.first.data.dataset.id}}"},
    )
    assert code == 2
    assert lines[1]["error"]["code"] == "invalid_run_line"


def test_an_unresolved_reference_fails_the_line(
    service: FakeMammothService, tmp_path: Path
) -> None:
    code, lines = _run(tmp_path, {"cmd": "dataset get", "args": ["{{steps.nope.data.id}}"]})
    assert code == 2
    error = lines[0]["error"]
    assert error["code"] == "unresolved_reference"
    assert error["details"]["reference"] == "steps.nope.data.id"
    assert _dataset_ids(service) == []


def test_dry_run_plans_a_line_that_waits_on_a_preview(
    service: FakeMammothService, tmp_path: Path
) -> None:
    code, lines = _run(
        tmp_path,
        {"cmd": "dataset delete", "args": [7], "flags": {"yes": True}, "name": "first"},
        {"cmd": "dataset get", "args": ["{{steps.first.data.made_by_a_write}}"], "name": "later"},
        {"cmd": "dataset get", "args": ["{{steps.later.data.id}}"]},
        extra=("--dry-run",),
    )
    assert code == 0, lines
    assert lines[1]["data"]["planned"] is True
    assert lines[1]["data"]["waits_on"] == "steps.first.data.made_by_a_write"
    assert lines[2]["data"]["planned"] is True


def test_dry_run_fails_what_a_preview_could_never_resolve(
    service: FakeMammothService, tmp_path: Path
) -> None:
    code, lines = _run(
        tmp_path,
        {"cmd": "dataset delete", "args": [7], "flags": {"yes": True}, "name": "first"},
        {"cmd": "dataset get", "args": ["{{steps.typo.data.id}}"]},
        {"cmd": "dataset get", "args": [7], "when": {"exec": "x"}},
        {"cmd": "dataset get", "args": [7], "when": "steps.first.data.ok"},
        {"cmd": "dataset get", "args": ["{{inputs.nope}}"]},
        extra=("--dry-run", "--continue"),
    )
    assert code == 2
    assert [line["exit"] for line in lines[1:5]] == [2, 2, 2, 2]
    assert all(line["error"]["code"] == "unresolved_reference" for line in lines[1:5])


def test_a_name_is_used_once(service: FakeMammothService, tmp_path: Path) -> None:
    code, lines = _run(
        tmp_path,
        {"cmd": "dataset get", "args": [7], "name": "a"},
        {"cmd": "dataset get", "args": [7], "name": "a"},
    )
    assert code == 2
    assert lines[1]["error"]["code"] == "invalid_run_line"
    assert "already named" in lines[1]["error"]["message"]


def test_a_malformed_condition_fails_the_line(service: FakeMammothService, tmp_path: Path) -> None:
    code, lines = _run(tmp_path, {"cmd": "dataset get", "args": [7], "when": {"exec": "x"}})
    assert code == 2
    assert lines[0]["error"]["code"] == "unresolved_reference"


def test_a_dollar_key_in_a_line_is_data(service: FakeMammothService, tmp_path: Path) -> None:
    code, lines = _run(
        tmp_path,
        {"cmd": "dataset get", "args": [7], "input": {"$schema": "x", "$ref": "#/y"}},
    )
    assert lines[0]["error"]["code"] != "unresolved_reference", lines


def test_a_bare_string_when_is_refused(service: FakeMammothService, tmp_path: Path) -> None:
    code, lines = _run(
        tmp_path,
        {"cmd": "dataset get", "args": [7], "name": "first"},
        {"cmd": "dataset get", "args": [7], "when": "steps.first.data.ok"},
    )
    assert code == 2
    assert "always true" in lines[1]["error"]["message"]


def test_an_empty_for_each_prints_an_envelope(service: FakeMammothService, tmp_path: Path) -> None:
    code, lines = _run(
        tmp_path,
        {"cmd": "dataset get", "args": ["{{item}}"], "for_each": [], "name": "none"},
    )
    assert code == 0, lines
    assert lines[0]["skipped"] is True and lines[0]["data"] == []


def test_for_each_goes_on_past_a_failed_item_with_continue(
    service: FakeMammothService, tmp_path: Path
) -> None:
    items = [7, "bad", 7]
    line = {"cmd": "dataset get", "args": ["{{item}}"], "for_each": items}
    stopped_code, stopped = _run(tmp_path, line)
    kept_code, kept = _run(tmp_path, line, extra=("--continue",))
    assert stopped_code != 0 and kept_code != 0
    assert [entry.get("item") for entry in stopped if "item" in entry] == [0, 1]
    assert [entry.get("item") for entry in kept if "item" in entry] == [0, 1, 2]
