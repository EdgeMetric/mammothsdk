"""The ``file_exists`` recovery command re-runs the command the way the user ran it."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.local_files import refuse_existing_file


def _refusal(tmp_path: Path, **fields: object) -> CliError:
    existing = tmp_path / "out.csv"
    existing.write_text("keep me", encoding="utf-8")
    invocation = Invocation(command_id="view.export.csv", extra_args=["7"], **fields)  # type: ignore[arg-type]
    with pytest.raises(CliError) as excinfo:
        refuse_existing_file(invocation, existing)
    assert excinfo.value.code == "file_exists"
    return excinfo.value


def test_recovery_command_keeps_project_and_profile(tmp_path: Path) -> None:
    error = _refusal(tmp_path, project=3633, profile="staging")
    assert error.recovery_commands == [
        "mammoth view export csv 7 --project 3633 --profile staging --overwrite"
    ]


def test_recovery_command_keeps_the_input_file_with_the_scope(tmp_path: Path) -> None:
    error = _refusal(tmp_path, project=12, input_file="req.json")
    assert error.recovery_commands == [
        "mammoth view export csv 7 --project 12 --input req.json --overwrite"
    ]


def test_recovery_command_quotes_an_unusual_profile_name(tmp_path: Path) -> None:
    error = _refusal(tmp_path, profile="my team")
    assert error.recovery_commands == ["mammoth view export csv 7 --profile 'my team' --overwrite"]


def test_recovery_command_without_scope_flags_is_unchanged(tmp_path: Path) -> None:
    error = _refusal(tmp_path)
    assert error.recovery_commands == ["mammoth view export csv 7 --overwrite"]


def test_a_defaulted_profile_is_not_pinned_into_the_command(tmp_path: Path) -> None:
    error = _refusal(tmp_path, profile="work", profile_is_default=True)
    assert error.recovery_commands == ["mammoth view export csv 7 --overwrite"]


def test_a_directory_target_is_a_usage_error_even_with_overwrite(tmp_path: Path) -> None:
    invocation = Invocation(command_id="view.export.csv", extra_args=["7"], overwrite=True)
    with pytest.raises(CliError) as excinfo:
        refuse_existing_file(invocation, tmp_path)
    assert excinfo.value.code == "invalid_argument"
    assert excinfo.value.exit_status == 2
    assert "is a directory" in excinfo.value.message
    assert "output_path" in (excinfo.value.hint or "")
