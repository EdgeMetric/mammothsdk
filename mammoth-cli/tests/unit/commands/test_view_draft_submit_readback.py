"""A draft submit is read back once the view's data has been refreshed.

The submit returns with the pipeline already ``ready``/``idle``, but the steps
run a moment later: a row count read at once is the old one, reported as
verified (FB-22: "20 rows before and after" for a draft that left 18).
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.commands import view, view_ops

_OLD = {"row_count": 20, "data_updated_at": "2026-01-01T10:00:00"}
_NEW = {"row_count": 18, "data_updated_at": "2026-01-01T10:00:03"}
_PENDING = {"has_pending_changes": True}


class _Service:
    """Answers each view read with the next programmed record, then repeats the last."""

    def __init__(self, infos: list[dict[str, Any]], draft: dict[str, Any] = _PENDING) -> None:
        self.infos = list(infos)
        self.draft = draft
        self.view_reads = 0

    def call(self, symbol: str, **kwargs: Any) -> Any:
        if symbol.endswith("get_draft_status"):
            return self.draft
        self.view_reads += 1
        return self.infos.pop(0) if len(self.infos) > 1 else self.infos[0]


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(view.time, "sleep", lambda _s: None)


def test_the_read_back_waits_for_the_refreshed_row_count() -> None:
    service = _Service([_OLD, _OLD, _OLD, _NEW])
    before = view_ops._draft_before_submit(service, 4, 7, 1)

    data = view_ops._draft_submit_row_check(service, 4, 7, 1, before, {"draft_mode": "clean"})

    assert data["row_check"] == {"rows_before": 20, "rows_after": 18}
    assert "pipeline_error" not in data


def test_data_that_never_refreshes_is_reported_as_unfinished() -> None:
    service = _Service([_OLD])
    before = view_ops._draft_before_submit(service, 4, 7, 1)

    data = view_ops._draft_submit_row_check(service, 4, 7, 1, before, {"draft_mode": "clean"})

    assert data["row_check"] == {"rows_before": 20, "rows_after": None}
    assert data["pipeline_error"]["execution_state"] == view.UNFINISHED_STATE


def test_a_draft_with_nothing_pending_is_read_at_once() -> None:
    service = _Service([_OLD], draft={"has_pending_changes": False})
    before = view_ops._draft_before_submit(service, 4, 7, 1)

    data = view_ops._draft_submit_row_check(service, 4, 7, 1, before, {"draft_mode": "clean"})

    assert data["row_check"] == {"rows_before": 20, "rows_after": 20}
    assert service.view_reads == 2
