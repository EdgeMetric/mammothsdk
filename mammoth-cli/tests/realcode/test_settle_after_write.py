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


# --- a write is never done + verified while its read-back says otherwise -----------


def _convert_type(
    monkeypatch: Any,
    real_service: ServiceFactory,
    api_routes: Callable[[Any], None],
    execution_state: str = "ready",
) -> dict[str, Any]:
    import json

    from mammoth_cli.services import factory
    from mammoth_cli.testing import make_runner

    service, api = real_service(project_id=180)
    # A fresh service per build, as in production: each command closes its own.
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    view = {
        "id": VIEW,
        "name": "Fundraising",
        "row_count": 50,
        "metadata": [{"display_name": "Gift", "internal_name": "col_b", "type": "TEXT"}],
    }
    api.on("GET", rf"/datasets/{DATASET}/dataviews/{VIEW}$", body=view)
    api.on("POST", r"/pipeline/tasks", body={})
    api.on("GET", r"/pipeline$", body={"state": "ready", "execution_state": execution_state})
    api_routes(api)
    result = make_runner().invoke(
        [
            "view",
            "transform",
            "convert-type",
            str(VIEW),
            "--project",
            "180",
            "--input",
            json.dumps(
                {"dataset_id": DATASET, "conversions": [{"column": "Gift", "to": "NUMERIC"}]}
            ),
            "--yes",
            "--output",
            "json",
            "--no-input",
        ]
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.output)["data"]


def test_a_failed_readback_is_not_reported_verified(
    monkeypatch: Any, real_service: ServiceFactory
) -> None:
    """The read-back raced the pipeline: its job failed with the reason in ``reason``."""
    reason = "no data for pipeline step 1 of dataview 3062 yet; the step is 'added'"

    def routes(api: Any) -> None:
        api.on("GET", r"/data$", body={"job_id": 5})
        api.on(
            "GET",
            r"/jobs/5$",
            body={"id": 5, "status": "failure", "response": {"reason": reason}},
        )

    data = _convert_type(monkeypatch, real_service, routes)

    assert data["state"]["kind"] == "unreadable"
    assert reason in data["state"]["reason"]
    assert data["verify"]["verified"] is False
    assert "read-back" in data["verify"]["reason"]


def test_a_pipeline_that_errored_after_the_write_is_not_verified(
    monkeypatch: Any, real_service: ServiceFactory
) -> None:
    """A write with no row check still waits for the pipeline and reads its own error."""

    def routes(api: Any) -> None:
        api.on("GET", r"/data$", body={"data": []})

    data = _convert_type(monkeypatch, real_service, routes, execution_state="runtime_error")

    assert data["pipeline_error"]["execution_state"] == "runtime_error"
    assert data["verify"]["verified"] is False
