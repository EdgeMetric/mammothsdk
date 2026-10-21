"""``mammoth run`` after review: real-tree refusals, Ctrl-C, line splitting, flags, exits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.app import app
from mammoth_cli.commands import run as run_cmd
from mammoth_cli.context import profiles, resolver
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


def _invoke(*argv: str, stdin: str | None = None) -> tuple[int, list[dict[str, Any]]]:
    result = make_runner()._runner.invoke(app, ["run", *argv, *_BASE], input=stdin)
    lines = [json.loads(text) for text in result.stdout.split("\n") if text.strip()]
    return result.exit_code, lines


# --- 1. refusals follow the command that runs, not the spelling of the line -------------


@pytest.mark.parametrize(
    "line",
    [
        {"cmd": "auth", "args": ["logout"], "flags": {"yes": True}},
        {"cmd": "auth", "args": ["login"]},
        {"cmd": "auth logout", "flags": {"yes": True}},
        {"cmd": "auth login"},
        {"cmd": "run inner"},
        {"cmd": "run", "args": ["inner.jsonl"]},
        {"cmd": "run"},
        {"cmd": "  auth   logout "},
    ],
    ids=[
        "auth+logout-arg",
        "auth+login-arg",
        "auth logout",
        "auth login",
        "run inner",
        "run+arg",
        "run",
        "spaced",
    ],
)
def test_refusals_are_checked_on_the_command_that_would_run(
    built: list[FakeMammothService], tmp_path: Path, line: dict[str, Any]
) -> None:
    code, lines = _invoke(str(_write(tmp_path, line)))
    assert code == 2
    assert lines[0]["error"]["code"] == "run_command_refused", lines[0]
    assert not built
    # Nothing ran: the saved login is still there.
    assert profiles.get_profile("default") is not None


def test_a_refused_line_does_not_stop_continue_from_running_the_rest(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    path = _write(
        tmp_path,
        {"cmd": "auth", "args": ["logout"], "flags": {"yes": True}},
        {"cmd": "dataset get", "args": [7]},
    )
    code, lines = _invoke(str(path), "--continue")
    assert code == 2
    assert [line["exit"] for line in lines[:-1]] == [2, 0]
    assert profiles.get_profile("default") is not None


# --- 2. Ctrl-C ends the whole run -------------------------------------------------------


def test_ctrl_c_stops_a_continue_run_and_skips_the_rest(
    built: list[FakeMammothService], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    deleted: list[Any] = []

    def _interrupt(_log: Any) -> Any:
        raise KeyboardInterrupt

    real_build = service_factory.build_service

    def _build(auth: Any, **kwargs: Any) -> FakeMammothService:
        service = real_build(auth, **kwargs)
        service.responses[_DATASET_GET] = _interrupt
        service.responses[_DATASET_DELETE] = lambda log: deleted.append(log) or {}
        return service

    monkeypatch.setattr(service_factory, "build_service", _build)
    path = _write(
        tmp_path,
        {"cmd": "dataset get", "args": [7]},
        {"cmd": "dataset delete", "args": [7], "flags": {"yes": True}},
        {"cmd": "dataset delete", "args": [8], "flags": {"yes": True}},
    )
    code, lines = _invoke(str(path), "--continue")
    assert code == 130
    assert [line["line"] for line in lines[:-1]] == [1]
    assert lines[0]["exit"] == 130
    data = lines[-1]["data"]
    assert (data["skipped"], data["stopped_at"], data["exit"]) == (2, 1, 130)
    assert deleted == []


# --- 3. only "\n" ends a line; a BOM is accepted -----------------------------------------


def test_raw_unicode_line_separators_inside_a_string_do_not_split_the_line(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    odd = "a b c\u0085d\x1ce\x1df\x1eg"
    path = tmp_path / "commands.jsonl"
    first = json.dumps({"cmd": "dataset get", "args": [7], "id": odd}, ensure_ascii=False)
    second = json.dumps({"cmd": "dataset get", "args": [7], "id": "two"})
    assert " " in first
    path.write_text(first + "\n" + second + "\n", encoding="utf-8")
    code, lines = _invoke(str(path))
    assert code == 0
    assert [(line["line"], line["id"]) for line in lines[:-1]] == [(1, odd), (2, "two")]


def test_a_crlf_file_runs_and_line_numbers_count_blank_lines(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    path = tmp_path / "commands.jsonl"
    row = json.dumps({"cmd": "dataset get", "args": [7]})
    path.write_bytes((row + "\r\n\r\n" + row + "\r\n").encode())
    code, lines = _invoke(str(path))
    assert code == 0
    assert [line["line"] for line in lines[:-1]] == [1, 3]


def test_a_utf8_bom_on_the_first_line_is_accepted(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    path = tmp_path / "commands.jsonl"
    row = json.dumps({"cmd": "dataset get", "args": [7]})
    path.write_bytes(b"\xef\xbb\xbf" + (row + "\n" + row + "\n").encode())
    code, lines = _invoke(str(path))
    assert code == 0 and [line["exit"] for line in lines[:-1]] == [0, 0]
    code, lines = _invoke("-", stdin="﻿" + row + "\n")
    assert code == 0 and lines[0]["line"] == 1 and lines[0]["exit"] == 0


# --- 4. FILE defaults to stdin; --continue works in any position -------------------------


def test_continue_before_the_file_is_the_flag_not_the_file(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    row = json.dumps({"cmd": "dataset get", "args": [7]})
    bad = json.dumps({"cmd": "nosuch thing"})
    stdin = "\n".join([bad, row]) + "\n"
    code, lines = _invoke("--continue", stdin=stdin)
    assert code == 2
    assert [line["exit"] for line in lines[:-1]] == [2, 0]
    assert lines[-1]["data"]["continue"] is True
    path = _write(tmp_path, bad, row)
    for argv in (["--continue", str(path)], [str(path), "--continue"]):
        code, lines = _invoke(*argv)
        assert [line["exit"] for line in lines[:-1]] == [2, 0], argv
        assert lines[-1]["data"]["continue"] is True


def test_file_defaults_to_stdin_without_continue(
    built: list[FakeMammothService],
) -> None:
    code, lines = _invoke(stdin=json.dumps({"cmd": "dataset get", "args": [7]}) + "\n")
    assert code == 0 and lines[0]["exit"] == 0
    assert lines[-1]["data"]["continue"] is False


# --- 7. exit statuses ---------------------------------------------------------------------


class _Root:
    def __init__(self, behaviour: Any) -> None:
        self.behaviour = behaviour

    def main(self, **_: Any) -> Any:
        return self.behaviour()

    def render_usage_error(self, *_: Any) -> None:
        return None


def _exit_with(code: object) -> Any:
    def behave() -> None:
        raise SystemExit(code)

    return behave


@pytest.mark.parametrize(
    "behaviour, expected",
    [
        (_exit_with(None), 0),
        (_exit_with(0), 0),
        (_exit_with(3), 3),
        (_exit_with("a message"), 1),
        (lambda: None, 0),
    ],
    ids=["sys.exit()", "sys.exit(0)", "sys.exit(3)", "sys.exit(msg)", "returns"],
)
def test_a_clean_exit_with_no_envelope_is_not_a_failure(
    monkeypatch: pytest.MonkeyPatch, behaviour: Any, expected: int
) -> None:
    monkeypatch.setattr(run_cmd, "_click_root", lambda: _Root(behaviour))
    status, envelope = run_cmd.execute_line(["version"], "version")
    assert status == expected
    if expected == 0:
        assert "error" not in envelope


# --- 8. negative numbers are values ------------------------------------------------------


def test_negative_numbers_are_arguments_not_flags(
    built: list[FakeMammothService], tmp_path: Path
) -> None:
    for token in (-5, "-5", "-0.25", "-1e3"):
        spec = run_cmd.parse_line(
            1, json.dumps({"cmd": "calc", "args": [token]}), {}, lambda _c: frozenset()
        )
        assert spec.argv[:2] == ["calc", str(token)]
    for token in ("-x", "--5", "-"):
        with pytest.raises(Exception, match="looks like a flag"):
            run_cmd.parse_line(
                1, json.dumps({"cmd": "calc", "args": [token]}), {}, lambda _c: frozenset()
            )
    code, lines = _invoke(str(_write(tmp_path, {"cmd": "calc", "args": ["-5"]})))
    assert lines[0].get("error", {}).get("code") not in {"invalid_run_line", "unknown_option"}


# --- 9. the credential memo is dropped after a line that can change who you are ----------


def test_the_credential_memo_is_cleared_after_an_auth_config_or_context_line(
    built: list[FakeMammothService], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved: list[str | None] = []
    real = resolver._resolve_auth

    def counting(invocation: Any, explicit_login: Any = None) -> Any:
        resolved.append(invocation.command_id)
        return real(invocation, explicit_login)

    monkeypatch.setattr(resolver, "_resolve_auth", counting)
    path = _write(
        tmp_path,
        {"cmd": "dataset get", "args": [7]},
        {"cmd": "dataset get", "args": [7]},
        {"cmd": "config list"},
        {"cmd": "dataset get", "args": [7]},
    )
    code, lines = _invoke(str(path))
    assert code == 0, lines
    datasets = [command for command in resolved if command == "dataset.get"]
    # Once for the first two lines together, once again after `config list`.
    assert len(datasets) == 2, resolved
