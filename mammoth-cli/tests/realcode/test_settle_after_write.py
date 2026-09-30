"""After a write the CLI waits for the pipeline and never reads a stale count as final.

Real-code: the real service and client, with only the HTTP socket faked.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mammoth_cli.commands.view import wait_for_view_row_count
from mammoth_cli.runtime.verify import with_verify

ServiceFactory = Callable[..., Any]
DATASET, VIEW = 55, 3062


def test_a_followon_job_that_failed_is_reported_with_its_reason(
    real_service: ServiceFactory,
) -> None:
    service, api = real_service(project_id=180)
    reason = "no data for pipeline step 1 of dataview 3062 yet; the step is 'added'"
    api.on(
        "GET",
        r"/jobs/91$",
        body={"id": 91, "status": "failure", "response": {"reason": reason}},
    )
    api.on("GET", r"/pipeline$", body={"state": "ready", "execution_state": "ready"})
    api.on("GET", rf"/datasets/{DATASET}/dataviews/{VIEW}$", body={"id": VIEW, "row_count": 50})

    rows, error = wait_for_view_row_count(
        service, DATASET, VIEW, 180, write_result={"future_id": 91}
    )

    assert error is not None and reason in error["wait_error"]
    assert rows == 50


def test_a_pipeline_still_running_after_the_wait_is_not_finished(
    real_service: ServiceFactory,
) -> None:
    """The wait's own failure is reported, not swallowed, so verify says so."""
    service, api = real_service(project_id=180)
    api.on("GET", r"/pipeline$", body={"state": "running", "execution_state": "running"})
    api.on("GET", rf"/datasets/{DATASET}/dataviews/{VIEW}$", body={"id": VIEW, "row_count": 50})

    rows, error = wait_for_view_row_count(service, DATASET, VIEW, 180, settle_timeout=0.2)

    assert error is not None and error["execution_state"] == "unfinished"
    verified = with_verify(
        {
            "status": "done",
            "row_check": {"rows_before": 50, "rows_after": rows},
            "pipeline_error": error,
        }
    )["verify"]
    assert verified["verified"] is False
    assert verified["reason"].startswith("not finished")


def test_a_row_reducing_write_that_removed_nothing_is_flagged_unchanged() -> None:
    check = {"rows_before": 50, "rows_after": 50, "expected_row_decrease": True}
    verify = with_verify({"status": "done", "row_check": check})["verify"]
    assert verify["changed"] is False
    assert verify["reason"] == "no rows removed (50 -> 50)"


def test_a_row_reducing_write_with_an_unread_before_count_is_flagged() -> None:
    check = {"rows_before": None, "rows_after": 50, "expected_row_decrease": True}
    verify = with_verify({"status": "done", "row_check": check})["verify"]
    assert verify["verified"] is False
    assert "before" in verify["reason"]
