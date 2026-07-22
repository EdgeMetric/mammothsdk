"""Unit tests for the local doctor and completion commands."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.commands import completion as completion_cmd
from mammoth_cli.commands import doctor as doctor_cmd
from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_doctor_reports_no_credentials_when_unauthenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ENV_API_KEY, raising=False)
    monkeypatch.delenv(ENV_API_SECRET, raising=False)
    monkeypatch.delenv(ENV_WORKSPACE_ID, raising=False)
    data, _meta = doctor_cmd.doctor(_inv("doctor"))
    assert data["ok"] is False
    names = {c["name"]: c["ok"] for c in data["checks"]}
    assert names["credentials"] is False
    assert names["connection"] is False
    assert "cli_version" in data


def test_doctor_connection_ok_with_fake_service(
    fake_service: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_API_KEY, "k")
    monkeypatch.setenv(ENV_API_SECRET, "s")
    monkeypatch.setenv(ENV_WORKSPACE_ID, "4")
    data, _meta = doctor_cmd.doctor(_inv("doctor"))
    names = {c["name"]: c["ok"] for c in data["checks"]}
    assert names["endpoint"] is True
    assert names["connection"] is True


def test_completion_show_bash() -> None:
    data, _meta = completion_cmd.completion_show(_inv("completion.show", extra_args=["bash"]))
    assert data["shell"] == "bash"
    assert "_MAMMOTH_COMPLETE=bash_source mammoth" in data["script"]


def test_completion_show_unsupported_shell_is_usage_error() -> None:
    with pytest.raises(CliError) as excinfo:
        completion_cmd.completion_show(_inv("completion.show", extra_args=["tcsh"]))
    assert excinfo.value.code == "unsupported_shell"


def test_completion_install_writes_snippet_idempotently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    first, _ = completion_cmd.completion_install(_inv("completion.install", extra_args=["bash"]))
    assert first["added"] is True
    assert Path(first["path"]).read_text(encoding="utf-8").count("_MAMMOTH_COMPLETE") == 1
    second, _ = completion_cmd.completion_install(_inv("completion.install", extra_args=["bash"]))
    assert second["added"] is False
    assert Path(second["path"]).read_text(encoding="utf-8").count("_MAMMOTH_COMPLETE") == 1
