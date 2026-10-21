"""``mammoth run``: JSON Lines, many commands, one process.

The lines go through the same command path as a single command, so these tests pin what is
specific to ``run``: one service and one credential load for all lines, the stop and
``--continue`` modes, the per-line confirmation, ``--dry-run`` reaching every line, and the
line-level errors.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import run as run_cmd
from mammoth_cli.context import credentials, resolver
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile, make_runner

_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_DATASET_DELETE = "mammoth.api.datasets.DatasetsAPI.delete"
_BASE = ["--output", "json", "--project", "9"]


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def built(monkeypatch: pytest.MonkeyPatch) -> list[FakeMammothService]:
    """Count the services the run builds; every build is a fresh fake."""
    services: list[FakeMammothService] = []

    def _build(auth: Any, **_kwargs: Any) -> FakeMammothService:
        service = FakeMammothService()
        service.responses[_DATASET_GET] = {"dataset": {"id": 7, "name": "sales"}}
        services.append(service)
        return service

    monkeypatch.setattr(service_factory, "build_service", _build)
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_a, **_k: 4)
    return services


def _write(tmp_path: Path, *lines: Any) -> Path:
    path = tmp_path / "commands.jsonl"
    path.write_text(
        "\n".join(line if isinstance(line, str) else json.dumps(line) for line in lines) + "\n",
        encoding="utf-8",
    )
    return path


def _run(
    path: Path | str, *extra: str, stdin: str | None = None
) -> tuple[int, list[dict[str, Any]]]:
    result = make_runner()._runner.invoke(
        __import__("mammoth_cli.app", fromlist=["app"]).app,
        ["run", str(path), *_BASE, *extra],
        input=stdin,
    )
    lines = [json.loads(text) for text in result.stdout.splitlines() if text.strip()]
    return result.exit_code, lines


def test_lines_share_one_service_and_one_credential_load(
    built: list[FakeMammothService], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loads: list[str] = []
    real = credentials.load_credential
    monkeypatch.setattr(
        credentials, "load_credential", lambda name, *a, **k: (loads.append(name), real(name))[1]
    )
    path = _write(
        tmp_path,
        {"cmd": "dataset get", "args": [7]},
        {"cmd": "dataset get", "args": ["7"], "id": "again"},
        {"cmd": "dataset get", "args": [7]},
    )
    code, lines = _run(path)
    assert code == 0
    assert len(built) == 1, "every line reuses the one service (one client, one pool)"
    assert len(loads) == 1, "credentials are read once for the whole run"
    assert [line.get("line") for line in lines[:3]] == [1, 2, 3]
    assert lines[1]["id"] == "again"
    assert all(line["exit"] == 0 and line["cmd"] == "dataset get" for line in lines[:3])
    assert lines[0]["meta"]["command"] == "dataset get"
    summary = lines[-1]
    assert "line" not in summary
    assert summary["data"]["ok"] == 3 and summary["data"]["failed"] == 0


def test_stops_at_the_first_failed_line_with_its_exit_status(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    path = _write(
        tmp_path,
        {"cmd": "dataset get", "args": [7]},
        {"cmd": "nosuch thing"},
        {"cmd": "dataset get", "args": [7]},
    )
    code, lines = _run(path)
    assert code == 2
    assert [line.get("line") for line in lines[:-1]] == [1, 2]
    assert lines[1]["exit"] == 2 and "error" in lines[1]
    data = lines[-1]["data"]
    assert (data["ok"], data["failed"], data["skipped"], data["stopped_at"]) == (1, 1, 1, 2)
    assert len(built) == 1


def test_continue_runs_every_line_and_exits_with_the_first_failure(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    path = _write(
        tmp_path,
        {"cmd": "nosuch thing"},
        {"cmd": "dataset get", "args": [7]},
        "{not json",
        {"cmd": "dataset get", "args": [7]},
    )
    code, lines = _run(path, "--continue")
    assert code == 2
    assert [line.get("line") for line in lines[:-1]] == [1, 2, 3, 4]
    assert [line["exit"] for line in lines[:-1]] == [2, 0, 2, 0]
    data = lines[-1]["data"]
    assert (data["ok"], data["failed"], data["skipped"]) == (2, 2, 0)
    assert data["failed_lines"] == [1, 3] and data["continue"] is True


def test_a_mutating_line_needs_its_own_confirmation(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    path = _write(
        tmp_path,
        {"cmd": "dataset delete", "args": [7]},
        {"cmd": "dataset get", "args": [7]},
    )
    code, lines = _run(path, "--continue")
    assert code == 2
    assert lines[0]["error"]["code"] == "confirmation_required"
    assert lines[1]["exit"] == 0
    assert not any(sym == _DATASET_DELETE for sym, _ in built[0].call_log), "nothing was deleted"


def test_run_has_no_global_yes_or_confirm(built: list[FakeMammothService], tmp_path: Path) -> None:
    path = _write(tmp_path, {"cmd": "dataset delete", "args": [7]})
    for flag in (["--yes"], ["--confirm", str(path)]):
        result = make_runner().invoke(["run", str(path), *_BASE, *flag])
        assert result.exit_code == 2
        assert "run_global_flag_refused" in result.output + result.stderr
    assert not built, "refused before any line ran"


def test_dry_run_reaches_every_line_and_sends_nothing(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    path = _write(
        tmp_path,
        {"cmd": "dataset delete", "args": [7], "flags": {"yes": True}},
        {"cmd": "dataset delete", "args": [7], "flags": {"yes": True, "dry-run": False}},
    )
    code, lines = _run(path, "--dry-run")
    assert code == 0, lines
    assert all(line["data"]["dry_run"] is True for line in lines[:2])
    assert lines[-1]["data"]["dry_run"] is True
    assert not any(sym == _DATASET_DELETE for service in built for sym, _ in service.call_log)


def test_a_line_that_confirms_runs_and_per_line_flags_apply(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    path = _write(
        tmp_path,
        {"cmd": "dataset delete", "args": [7], "flags": {"yes": True, "project": 12}},
    )
    code, lines = _run(path)
    assert any(sym == _DATASET_DELETE for sym, _ in built[0].call_log), lines
    deleted = [kwargs for sym, kwargs in built[0].call_log if sym == _DATASET_DELETE]
    assert deleted[0]["project_id"] == 12, "the line's own project outranks run's"
    assert code in (0, 1)


def test_a_malformed_line_is_a_line_level_usage_error(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    path = _write(tmp_path, {"cmd": "dataset get", "args": [7]}, "{not json", {"cmd": "x"})
    code, lines = _run(path)
    assert code == 2
    bad = lines[1]
    assert bad["line"] == 2 and bad["exit"] == 2
    assert bad["error"]["code"] == "invalid_run_line"
    assert lines[-1]["data"]["stopped_at"] == 2 and lines[-1]["data"]["skipped"] == 1


@pytest.mark.parametrize(
    "line",
    [
        [1, 2],
        {"args": [1]},
        {"cmd": "dataset get", "extra": 1},
        {"cmd": "dataset get", "args": "7"},
        {"cmd": "dataset get", "args": [True]},
        {"cmd": "dataset get", "args": ["--help"]},
        {"cmd": "dataset get", "input": [1]},
        {"cmd": "dataset get", "flags": []},
        {"cmd": "dataset get", "flags": {"nosuch": 1}},
        {"cmd": "dataset get", "flags": {"output": "table"}},
        {"cmd": "dataset get", "flags": {"input": "x.json"}},
        {"cmd": "dataset get", "flags": {"yes": "yes"}},
        {"cmd": "dataset get", "flags": {"project": True}},
        {"cmd": "--help"},
        {"cmd": "dataset get", "id": [1]},
        '{"cmd": "dataset get", "cmd": "dataset list"}',
    ],
)
def test_bad_lines_are_rejected_before_anything_runs(
    built: list[FakeMammothService], tmp_path: Path, line: Any
) -> None:
    code, lines = _run(_write(tmp_path, line))
    assert code == 2
    assert lines[0]["error"]["code"] == "invalid_run_line", lines[0]
    assert built == [] or not built[0].call_log


@pytest.mark.parametrize("cmd", ["run", "auth login", "auth logout"])
def test_nested_run_and_stdin_commands_are_refused(
    built: list[FakeMammothService], tmp_path: Path, cmd: str
) -> None:
    code, lines = _run(_write(tmp_path, {"cmd": cmd}))
    assert code == 2
    assert lines[0]["error"]["code"] == "run_command_refused"
    assert not built


def test_a_command_flag_may_be_listed_in_args(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    spec = run_cmd.parse_line(
        1,
        json.dumps({"cmd": "schema get", "args": ["dataset.get", "--full"]}),
        {},
        lambda _c: {"--full"},
    )
    assert spec.argv[:3] == ["schema", "get", "dataset.get"] and "--full" in spec.argv


def test_argv_carries_inherited_flags_input_and_the_owned_flags() -> None:
    spec = run_cmd.parse_line(
        4,
        json.dumps(
            {
                "cmd": "view  task list",
                "args": [290],
                "input": {"limit": 5},
                "flags": {"project": 3, "job_timeout": 30, "yes": True, "standing": False},
            }
        ),
        {"--profile": "--profile=jup", "--standing": "--standing"},
        lambda _c: frozenset(),
    )
    assert spec.cmd == "view task list"
    assert spec.argv[:4] == ["view", "task", "list", "290"]
    assert "--project=3" in spec.argv and "--job-timeout=30" in spec.argv and "--yes" in spec.argv
    assert "--profile=jup" in spec.argv
    assert "--standing" not in spec.argv, "a line may switch an inherited flag off"
    assert '--input={"limit": 5}' in spec.argv
    assert spec.argv[-4:] == ["--output", "json", "--no-input", "--no-progress"]


def test_run_reads_stdin_and_an_empty_input_is_an_error(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    code, lines = _run("-", stdin=json.dumps({"cmd": "dataset get", "args": [7]}) + "\n\n")
    assert code == 0 and lines[0]["line"] == 1
    empty = make_runner()._runner.invoke(
        __import__("mammoth_cli.app", fromlist=["app"]).app,
        ["run", "-", *_BASE],
        input="\n  \n",
    )
    assert empty.exit_code == 2
    assert "run_input_empty" in empty.output + empty.stderr


def test_a_missing_file_is_a_usage_error(tmp_path: Path) -> None:
    result = make_runner().invoke(["run", str(tmp_path / "nope.jsonl"), *_BASE])
    assert result.exit_code == 2
    assert "input_not_found" in result.output + result.stderr
