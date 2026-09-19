"""``MAMMOTH_*`` session defaults stand in for the repeated global flags."""

from __future__ import annotations

import json

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.output.render import render
from mammoth_cli.runtime.invocation import Invocation


def test_env_defaults_fill_omitted_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_PROFILE", "release")
    monkeypatch.setenv("MAMMOTH_PROJECT", "43")
    monkeypatch.setenv("MAMMOTH_OUTPUT", "json")
    monkeypatch.setenv("MAMMOTH_NO_INPUT", "1")
    inv = Invocation(command_id="project.list", output="auto")
    assert (inv.profile, inv.project, inv.output, inv.no_input) == ("release", 43, "json", True)


def test_flags_win_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_PROFILE", "release")
    monkeypatch.setenv("MAMMOTH_PROJECT", "43")
    monkeypatch.setenv("MAMMOTH_OUTPUT", "yaml")
    inv = Invocation(command_id="project.list", output="json", profile="app", project=7)
    assert (inv.profile, inv.project, inv.output) == ("app", 7, "json")


def test_env_project_must_be_a_positive_integer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_PROJECT", "abc")
    with pytest.raises(CliError) as excinfo:
        Invocation(command_id="project.list", output="json")
    assert excinfo.value.code == "invalid_project_id"


def test_unknown_env_output_falls_back_to_auto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_OUTPUT", "xml")
    inv = Invocation(command_id="project.list", output="auto")
    assert inv.output in {"json", "table"}


def test_json_is_compact_when_piped_and_pretty_on_a_tty(tmp_path, monkeypatch) -> None:
    import io

    envelope = {"schema_version": 1, "data": {"a": [1, 2]}, "meta": {"command": "x"}}
    piped = io.StringIO()
    render(envelope, output="json", stream=piped)
    assert piped.getvalue() == '{"data":{"a":[1,2]},"meta":{"command":"x"},"schema_version":1}\n'

    class Tty(io.StringIO):
        def isatty(self) -> bool:
            return True

    terminal = Tty()
    render(envelope, output="json", stream=terminal)
    assert terminal.getvalue().startswith("{\n  ")
    assert json.loads(terminal.getvalue()) == json.loads(piped.getvalue())

    monkeypatch.setenv("MAMMOTH_JSON_PRETTY", "1")
    forced = io.StringIO()
    render(envelope, output="json", stream=forced)
    assert forced.getvalue().startswith("{\n  ")


def test_profile_settings_fill_unset_options(isolated_cli_config, monkeypatch) -> None:
    from mammoth_cli.context import profiles
    from mammoth_cli.testing import login_default_profile

    login_default_profile()
    profiles.set_setting("default", "output", "yaml")
    profiles.set_setting("default", "job_timeout", "900")
    inv = Invocation(command_id="project.list", output="auto")
    assert (inv.output, inv.job_timeout) == ("yaml", 900.0)
    # Flag and environment still outrank the saved setting.
    monkeypatch.setenv("MAMMOTH_OUTPUT", "json")
    inv = Invocation(command_id="project.list", output="auto", job_timeout=5)
    assert (inv.output, inv.job_timeout) == ("json", 5)


def test_mutations_get_a_longer_default_job_budget() -> None:
    from mammoth_cli.runtime.session import DEFAULT_MUTATION_JOB_TIMEOUT, default_job_timeout

    assert default_job_timeout("view.transform.filter") == DEFAULT_MUTATION_JOB_TIMEOUT
    assert default_job_timeout("file.upload") == DEFAULT_MUTATION_JOB_TIMEOUT
    assert default_job_timeout("project.list") is None
