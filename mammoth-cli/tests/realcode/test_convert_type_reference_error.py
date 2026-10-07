"""``view transform convert-type`` that breaks a step the backend validates later.

Koyal view 38745: the add answered without ``has_error``, the backend then found that a step
reads ``customer_id`` as a number (``type_mismatch`` 7003) and the new task stayed ``added``.
Real-code: the genuine CLI, service and SDK client, with only the HTTP socket faked.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.commands import view_ops
from tests.realcode.test_one_call_transform_ops import TASK, VIEW, _Server, _run

ServiceFactory = Callable[..., Any]
BROKEN_STEP = 5


class _NeverRuns(_Server):
    """The new task is stored but never runs; one older step carries the reference error."""

    def mount(self, api: Any) -> None:
        super().mount(api)
        api.on("GET", r"/pipeline/items$", handler=self._items)

    def _task_list(self, _request: Any) -> tuple[int, Any]:
        tasks: list[dict[str, Any]] = [{"id": 1, "transform_status": "DONE"}]
        if self.task_added:
            tasks.append({"id": TASK, "transform_status": "added"})
        return 200, {"tasks": tasks}

    def _items(self, _request: Any) -> tuple[int, Any]:
        broken = {
            "id": BROKEN_STEP,
            "reference_errors": {
                "reference_errors": [
                    {
                        "column": {"display_name": "Cost", "type": "NUMERIC"},
                        "reason": "type_mismatch",
                        "error_code": 7003,
                    }
                ]
            },
        }
        return 200, {"items": [{"id": 1}, broken], "total": 2}


def test_convert_type_whose_task_never_runs_names_the_broken_step(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    monkeypatch.setattr(view_ops, "_RUN_ATTEMPTS", 2)
    code, envelope, _api = _run(
        monkeypatch,
        real_service,
        _NeverRuns(draft=None),
        "convert-type",
        {"conversions": [{"column": "Cost", "to": "TEXT"}]},
    )

    error = envelope["error"]
    assert code != 0, envelope
    assert error["code"] == "pipeline_reference_error"
    assert error["details"]["reference_errors"][0]["column"] == "Cost"
    assert error["details"]["task_ids"] == [BROKEN_STEP]
    assert f"mammoth view task delete {VIEW} {BROKEN_STEP} --yes" in error["recovery_commands"][0]


def test_convert_type_whose_task_never_runs_and_pipeline_is_clean_is_still_unfinished(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    class _Clean(_NeverRuns):
        def _items(self, _request: Any) -> tuple[int, Any]:
            return 200, {"items": [{"id": 1}], "total": 1}

    monkeypatch.setattr(view_ops, "_RUN_ATTEMPTS", 2)
    code, envelope, _api = _run(
        monkeypatch,
        real_service,
        _Clean(draft=None),
        "convert-type",
        {"conversions": [{"column": "Cost", "to": "TEXT"}]},
    )

    assert code == 0, envelope
    assert envelope["data"]["pipeline_error"]["execution_state"] == view_ops.UNFINISHED_STATE
