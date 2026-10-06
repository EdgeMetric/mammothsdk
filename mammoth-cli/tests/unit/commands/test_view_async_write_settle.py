"""An async view write (task delete, task update, pipeline rerun) is read back
only after the job its response names has finished: before that, the view
still shows the old row count, and the write would be "verified" on it."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.commands import view


class _FakeService:
    """The view shows 11 rows until the delete's follow-on job is waited for."""

    def __init__(self) -> None:
        self.job_waited = False

    def wait_if_job(self, write_result: Any) -> Any:
        self.job_waited = True
        return write_result

    def call(self, symbol: str, **kwargs: Any) -> Any:
        return {"row_count": 20 if self.job_waited else 11}


def test_a_task_delete_is_read_back_after_its_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(view, "wait_for_pipeline_to_settle", lambda *args: None)
    service = _FakeService()
    response = {"status": "processing", "type_of_modification": "discard_rule", "future_id": 9}

    data = view._settle_async_view_write(service, 4, 7, 1, response, {"rows_before": 11})

    assert data["row_check"] == {"rows_before": 11, "rows_after": 20}
