"""``dispatch`` runs a command and returns its outcome; it never prints or exits."""

from __future__ import annotations

from typing import Any

import pytest
import typer
from mammoth.exceptions import MammothJobTimeoutError

from mammoth_cli.errors.envelope import EXIT_API, EXIT_AUTH, CliError
from mammoth_cli.runtime.dispatch import (
    INTERCEPTORS,
    STREAMED_META,
    Next,
    Outcome,
    Request,
    dispatch,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.mapping import map_sdk_exception


def _request(producer: Any, command_id: str = "project.list", **kwargs: Any) -> Request:
    return Request(command_id, "json", producer, **kwargs)


def test_success_is_returned_not_printed(capsys: pytest.CaptureFixture[str]) -> None:
    outcome = dispatch(_request(lambda: ({"id": 1}, {"project_id": 7})))
    assert outcome.ok
    assert outcome.data == {"id": 1}
    assert outcome.meta == {"project_id": 7}
    assert outcome.exit_status == 0
    assert capsys.readouterr() == ("", "")


def test_a_cli_error_is_an_outcome_not_an_exit() -> None:
    def refused() -> tuple[Any, dict[str, Any]]:
        raise CliError(code="not_found", message="No project 9.", exit_status=EXIT_API)

    outcome = dispatch(_request(refused))
    assert not outcome.ok
    assert outcome.error is not None and outcome.error.code == "not_found"
    assert outcome.exit_status == EXIT_API
    assert outcome.cause is None


def test_an_unexpected_exception_keeps_its_cause() -> None:
    boom = TypeError("cannot serialise")

    def broken() -> tuple[Any, dict[str, Any]]:
        raise boom

    outcome = dispatch(_request(broken))
    assert outcome.error is not None and outcome.error.code == "internal_error"
    assert outcome.cause is boom


def test_an_abort_is_a_clean_cancel() -> None:
    def aborted() -> tuple[Any, dict[str, Any]]:
        raise typer.Abort()

    outcome = dispatch(_request(aborted))
    assert outcome.error is not None and outcome.error.code == "aborted"


def test_an_input_rejection_carries_the_input_contract() -> None:
    def rejected() -> tuple[Any, dict[str, Any]]:
        raise CliError(code="unknown_input_field", message="No field 'x'.", exit_status=2)

    outcome = dispatch(_request(rejected, command_id="project.create"))
    assert outcome.error is not None
    assert "input_contract" in outcome.error.details


def test_an_invalid_output_mode_refuses_before_the_handler() -> None:
    def must_not_run() -> tuple[Any, dict[str, Any]]:
        raise AssertionError("handler ran")

    outcome = dispatch(Request("project.list", "xml", must_not_run))
    assert outcome.error is not None and outcome.error.code == "invalid_output_mode"


def test_a_failed_read_back_sets_the_exit_status() -> None:
    outcome = dispatch(_request(lambda: ({"verify": {"outcome": "failed"}}, {})))
    assert outcome.ok and outcome.exit_status == EXIT_API


def test_a_failed_doctor_report_exits_as_auth() -> None:
    outcome = dispatch(_request(lambda: ({"ok": False}, {}), command_id="doctor"))
    assert outcome.ok and outcome.exit_status == EXIT_AUTH


def test_a_streamed_result_names_its_own_exit_status() -> None:
    outcome = dispatch(_request(lambda: (None, {STREAMED_META: True, "exit_status": 3})))
    assert outcome.streamed and outcome.exit_status == 3
    assert outcome.meta == {}


def test_return_running_hands_back_the_handle() -> None:
    invocation = Invocation(command_id="view.data.aggregate", output="json", return_running=True)

    def timed_out() -> tuple[Any, dict[str, Any]]:
        raise map_sdk_exception(MammothJobTimeoutError(27102, 20))

    outcome = dispatch(
        _request(timed_out, command_id="view.data.aggregate", invocation=invocation, profile="p")
    )
    assert outcome.ok and outcome.running
    assert outcome.data["status"] == "running"
    assert outcome.meta["profile"] == "p"


def test_interceptors_run_outermost_first_around_the_handler() -> None:
    seen: list[str] = []

    def named(name: str) -> Any:
        def interceptor(request: Request, call_next: Next) -> Outcome:
            seen.append(f"{name}>")
            outcome = call_next(request)
            seen.append(f"<{name}")
            return outcome

        return interceptor

    def handler() -> tuple[Any, dict[str, Any]]:
        seen.append("handler")
        return {}, {}

    dispatch(_request(handler), interceptors=(named("a"), named("b")))
    assert seen == ["a>", "b>", "handler", "<b", "<a"]


def test_an_interceptor_refuses_by_raising() -> None:
    def refuse(request: Request, call_next: Next) -> Outcome:
        raise CliError(code="refused", message="No.", exit_status=2)

    outcome = dispatch(_request(lambda: ({}, {})), interceptors=(refuse, *INTERCEPTORS))
    assert outcome.error is not None and outcome.error.code == "refused"
