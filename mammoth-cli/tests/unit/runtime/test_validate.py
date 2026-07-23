"""Unit tests for central id/global-option validation (R8).

:mod:`mammoth_cli.runtime.validate` is the new central check for the values
Click/Typer parsing never constrains: resource ids (workspace/project/job/view)
must be positive integers, ``--color`` must be a recognized policy, and the
timeout family must be positive numbers.
"""

from __future__ import annotations

import pytest

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.validate import validate_invocation, validate_positional_ids


def _invocation(**overrides: object) -> Invocation:
    return Invocation(command_id="project.list", **overrides)  # type: ignore[arg-type]


# --- global options ---------------------------------------------------------


def test_default_invocation_passes() -> None:
    validate_invocation(_invocation())


def test_zero_project_option_is_rejected() -> None:
    with pytest.raises(CliError) as excinfo:
        validate_invocation(_invocation(project=0))
    assert excinfo.value.code == "invalid_option_value"
    assert excinfo.value.exit_status == EXIT_USAGE


def test_negative_project_option_is_rejected() -> None:
    with pytest.raises(CliError):
        validate_invocation(_invocation(project=-3))


def test_positive_project_option_passes() -> None:
    validate_invocation(_invocation(project=42))


def test_unrecognized_color_is_rejected() -> None:
    with pytest.raises(CliError) as excinfo:
        validate_invocation(_invocation(color="pink"))
    assert excinfo.value.code == "invalid_option_value"


@pytest.mark.parametrize("color", ["auto", "always", "never"])
def test_recognized_color_passes(color: str) -> None:
    validate_invocation(_invocation(color=color))


@pytest.mark.parametrize("field", ["timeout", "job_timeout", "pipeline_timeout"])
def test_negative_timeout_is_rejected(field: str) -> None:
    with pytest.raises(CliError) as excinfo:
        validate_invocation(_invocation(**{field: -1.0}))
    assert excinfo.value.code == "invalid_option_value"


@pytest.mark.parametrize("field", ["timeout", "job_timeout", "pipeline_timeout"])
def test_zero_timeout_is_rejected(field: str) -> None:
    with pytest.raises(CliError):
        validate_invocation(_invocation(**{field: 0.0}))


@pytest.mark.parametrize("field", ["timeout", "job_timeout", "pipeline_timeout"])
def test_positive_timeout_passes(field: str) -> None:
    validate_invocation(_invocation(**{field: 30.0}))


# --- positional resource ids -------------------------------------------------


def test_zero_view_id_is_rejected() -> None:
    with pytest.raises(CliError) as excinfo:
        validate_positional_ids("view.get", ["0"])
    assert excinfo.value.code == "invalid_option_value"
    assert excinfo.value.exit_status == EXIT_USAGE


def test_negative_job_id_is_rejected() -> None:
    with pytest.raises(CliError):
        validate_positional_ids("job.get", ["-5"])


def test_positive_view_id_passes() -> None:
    validate_positional_ids("view.get", ["5"])


def test_non_numeric_id_token_is_rejected() -> None:
    with pytest.raises(CliError):
        validate_positional_ids("view.get", ["abc"])


def test_str_typed_positional_is_not_checked_as_an_id() -> None:
    """'project create' positional is a name (str); never treated as a numeric id."""
    validate_positional_ids("project.create", ["Sales"])


def test_no_positional_tokens_is_a_noop() -> None:
    validate_positional_ids("project.delete", [])
