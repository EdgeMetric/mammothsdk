"""Independent lifecycle tests for server draft state and bounded cleanup."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mammoth.api._pagination import collect_offset_pages
from mammoth.api.datasets import DatasetsAPI
from mammoth.api.pipeline import PipelineAPI
from mammoth.exceptions import (
    MammothAPIError,
    MammothDeletionVerificationError,
    MammothJobTimeoutError,
    MammothPaginationError,
)
from mammoth.models.pipeline import DraftCommand
from mammoth.view import View


def _view_with_pipeline(pipeline: object) -> View:
    client = SimpleNamespace(
        pipeline=pipeline,
        workspace_id=1,
        project_id=2,
        dataviews=SimpleNamespace(get=MagicMock(return_value={"id": 9})),
    )
    view = View(client, {"id": 9, "properties": {"columns": []}}, 3)
    view.refresh = lambda: view  # type: ignore[assignment]
    return view


def test_fresh_view_reads_server_draft_state_before_submitting() -> None:
    """A new process must not replay SUBMIT after a committed draft."""
    pipeline = MagicMock()
    pipeline.reconcile_draft_submission.return_value = {
        "is_draft": True,
        "mode": "clean",
        "pipeline_state": "ready",
        "pipeline": {"state": "ready", "draft_mode": "clean"},
        "outcome": "succeeded",
    }
    view = _view_with_pipeline(pipeline)

    result = view.submit_draft()

    pipeline.draft_mode.assert_called_once_with(9, DraftCommand.EXIT, 3)
    pipeline.wait_for_pipeline.assert_not_called()
    assert result["state"] == "ready"


def test_timeout_reconciles_terminal_pipeline_without_replaying_submit() -> None:
    pipeline = MagicMock()
    pipeline.reconcile_draft_submission.side_effect = [
        {
            "is_draft": True,
            "mode": "dirty",
            "pipeline_state": "ready",
            "pipeline": {"state": "ready", "draft_mode": "clean"},
            "outcome": "pending",
        },
        {
            "is_draft": True,
            "mode": "clean",
            "pipeline_state": "ready",
            "pipeline": {"state": "ready", "draft_mode": "clean"},
            "outcome": "succeeded",
        },
    ]
    from mammoth.exceptions import MammothJobTimeoutError

    pipeline.wait_for_pipeline.side_effect = MammothJobTimeoutError(77, 1)
    view = _view_with_pipeline(pipeline)

    result = view.submit_draft()

    assert result["state"] == "ready"
    assert [call.args[1] for call in pipeline.draft_mode.call_args_list] == [
        DraftCommand.SUBMIT,
        DraftCommand.EXIT,
    ]


def test_nested_terminal_readback_continues_lost_submit_without_duplicate() -> None:
    """A lost SUBMIT response may only be completed by EXIT after readback."""
    api = PipelineAPI(None)  # type: ignore[arg-type]
    api.get_pipeline = MagicMock(
        side_effect=[
            {"state": "ready", "draft": "dirty"},
            {"pipeline": {"state": "ready", "draft": "clean"}},
        ]
    )  # type: ignore[method-assign]
    mutations: list[DraftCommand] = []
    api.draft_mode = MagicMock(side_effect=lambda _id, command, _parent: mutations.append(command))  # type: ignore[method-assign]
    api.wait_for_pipeline = MagicMock(side_effect=MammothJobTimeoutError(9, 1))  # type: ignore[method-assign]
    view = _view_with_pipeline(api)

    result = view.submit_draft()

    assert result["pipeline"]["state"] == "ready"
    assert mutations == [DraftCommand.SUBMIT, DraftCommand.EXIT]
    assert api.get_pipeline.call_count == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"pipeline": {"draft": "dirty"}},
        {"pipeline": {"state": {"value": "ready"}, "draft": "dirty"}},
    ],
)
def test_unknown_draft_readback_blocks_submit_without_mutation(
    payload: dict[str, object],
) -> None:
    api = PipelineAPI(None)  # type: ignore[arg-type]
    api.get_pipeline = MagicMock(return_value=payload)  # type: ignore[method-assign]
    mutations: list[DraftCommand] = []
    api.draft_mode = MagicMock(side_effect=lambda _id, command, _parent: mutations.append(command))  # type: ignore[method-assign]
    view = _view_with_pipeline(api)

    result = view.submit_draft()

    assert result["outcome"] == "unknown"
    assert result["operation_state"] == "outcome_unknown"
    assert result["mutation_blocked"] is True
    assert mutations == []
    assert api.get_pipeline.call_count == 1


def test_pagination_rejects_empty_continuation_and_repeated_pages() -> None:
    pages = iter(
        [
            {"datasets": [{"id": 1}], "next": "/datasets?offset=1"},
            {"datasets": [], "next": "/datasets?offset=2"},
        ]
    )
    with pytest.raises(MammothPaginationError, match="empty page"):
        collect_offset_pages(lambda _offset: next(pages), item_key="datasets", limit=1)

    repeated = iter(
        [
            {"datasets": [{"id": 1}], "next": "/datasets?offset=1"},
            {"datasets": [{"id": 1}], "next": "/datasets?offset=2"},
        ]
    )
    with pytest.raises(MammothPaginationError, match="repeated"):
        collect_offset_pages(lambda _offset: next(repeated), item_key="datasets", limit=1)


def test_dataset_delete_verifies_absence_and_blocks_known_dependents() -> None:
    client = SimpleNamespace(workspace_id=1, project_id=2, job_timeout=1)
    api = DatasetsAPI(client)
    api.delete = MagicMock(return_value={"status": "accepted"})  # type: ignore[method-assign]
    api.get = MagicMock(
        side_effect=MammothAPIError("gone", status_code=404, response_body={})
    )  # type: ignore[method-assign]
    client._wait_if_job = MagicMock(side_effect=lambda response: response)

    result = api.delete_and_verify(8)

    assert result["verified"] is True
    api.delete.assert_called_once_with(8, workspace_id=None, project_id=None)
    with pytest.raises(MammothDeletionVerificationError):
        api.delete_and_verify(8, dependencies=["view:9"])
