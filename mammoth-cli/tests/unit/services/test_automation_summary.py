"""``automation list`` summary per automation (ILG friction 11-03, #7)."""

from __future__ import annotations

from typing import Any

from mammoth_cli.services.automation_summary import summary


def _scheduled(details: dict[str, Any], **record: Any) -> dict[str, Any]:
    condition = {"condition_type": "at_specific_time", "details": details}
    return {
        "status": "active",
        "conditions": [condition],
        "tasks": [
            {
                "task_type": "run_data_retrieval",
                "details": [
                    {"ds_details": {"ds_id": 42}, "last_run": "2026-10-27T07:00:03"},
                    {"ds_details": {"ds_id": 43}, "last_run": "2026-10-27T07:01:10"},
                ],
                "recurrence_details": [{"next_occurrence": "2026-11-03T07:00:00"}],
            }
        ],
        **record,
    }


def test_a_weekly_refresh_reads_as_its_weekday_time_next_run_and_datasets() -> None:
    weekly = {
        "frequency": "weekly",
        "interval": 1,
        "by_week_day": ["tu"],
        "start_at": "2026-09-01T07:00:00",
    }
    assert summary(_scheduled(weekly)) == {
        "runs": "weekly on Tue at 07:00",
        "next_run": "2026-11-03T07:00:00",
        "datasets": 2,
        "last_run": "2026-10-27T07:01:10",
    }


def test_a_suspended_automation_has_no_next_run() -> None:
    daily = {"frequency": "daily", "interval": 1, "start_at": "2026-09-01T02:30:00"}
    result = summary(_scheduled(daily, status="suspended"))
    assert result["runs"] == "daily at 02:30"
    assert result["next_run"] is None


def test_month_end_folder_drop_workflow_and_failure() -> None:
    month_end = summary(
        _scheduled({"frequency": "monthly", "by_month_day": [-1], "start_at": "2026-09-01T08:00"})
    )
    assert month_end["runs"] == "monthly on the last day at 08:00"
    folder = summary(
        {
            "status": "active",
            "conditions": [{"condition_type": "new_data_addition_in_folder", "details": {}}],
            "tasks": [
                {
                    "task_type": "run_workflow",
                    "details": [
                        {
                            "workflow_id": 2254,
                            "last_run_result": {"failure_reason": {"failure_reason": "bad total"}},
                        }
                    ],
                }
            ],
        }
    )
    assert folder["runs"] == "when a file lands in its folder"
    assert (folder["workflows"], folder["datasets"]) == (1, 0)
    assert folder["last_failure"] == "bad total"
