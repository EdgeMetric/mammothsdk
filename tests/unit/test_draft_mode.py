"""Unit tests for draft mode functionality."""

from __future__ import annotations

from unittest.mock import call

import pytest

from mammoth.client import MammothClient
from mammoth.models.pipeline import DraftCommand
from mammoth.view import View

from .conftest import SAMPLE_DATASET_ID, SAMPLE_VIEW_DATA


class TestEnterDraftMode:
    def test_calls_api_and_sets_flag(self, mock_client: MammothClient) -> None:
        view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        assert view.is_draft_mode is False

        result = view.enter_draft_mode()

        mock_client.pipeline.draft_mode.assert_called_once_with(
            view.id, DraftCommand.ENTER, SAMPLE_DATASET_ID
        )
        assert view.is_draft_mode is True
        assert result == {"state": "ok"}


class TestSubmitDraft:
    def test_submit_wait_refresh_exit(self, mock_client: MammothClient) -> None:
        view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        view._draft_mode = True

        # Mock refresh to avoid real API call
        view.refresh = lambda: view  # type: ignore[assignment]

        result = view.submit_draft()

        calls = mock_client.pipeline.draft_mode.call_args_list
        assert calls[0] == call(view.id, DraftCommand.SUBMIT, SAMPLE_DATASET_ID)
        assert calls[1] == call(view.id, DraftCommand.EXIT, SAMPLE_DATASET_ID)

        mock_client.pipeline.wait_for_pipeline.assert_called_once_with(view.id, SAMPLE_DATASET_ID)
        assert view.is_draft_mode is False
        assert result == {"state": "ready"}


class TestDiscardDraft:
    def test_discard_exit_refresh(self, mock_client: MammothClient) -> None:
        view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        view._draft_mode = True

        view.refresh = lambda: view  # type: ignore[assignment]

        result = view.discard_draft()

        calls = mock_client.pipeline.draft_mode.call_args_list
        assert calls[0] == call(view.id, DraftCommand.DISCARD, SAMPLE_DATASET_ID)
        assert calls[1] == call(view.id, DraftCommand.EXIT, SAMPLE_DATASET_ID)

        assert view.is_draft_mode is False
        assert result == {"state": "ok"}


class TestAddTaskDraftAware:
    def test_skips_wait_and_refresh_in_draft_mode(self, mock_client: MammothClient) -> None:
        view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        view._draft_mode = True

        view.refresh = lambda: view  # type: ignore[assignment]

        result = view._add_task({"TASK_TYPE": "TEST"})

        mock_client.pipeline.add_task.assert_called_once_with(
            view.id, {"TASK_TYPE": "TEST"}, SAMPLE_DATASET_ID
        )
        mock_client.pipeline.wait_for_pipeline.assert_not_called()
        assert result == {"id": 999}

    def test_waits_and_refreshes_in_auto_run(self, mock_client: MammothClient) -> None:
        view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        assert view._draft_mode is False

        view.refresh = lambda: view  # type: ignore[assignment]

        result = view._add_task({"TASK_TYPE": "TEST"})

        mock_client.pipeline.add_task.assert_called_once()
        mock_client.pipeline.wait_for_pipeline.assert_called_once_with(view.id, SAMPLE_DATASET_ID)
        assert result == {"id": 999}


class TestDraftContextManager:
    def test_success_enters_and_submits(self, mock_client: MammothClient) -> None:
        view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        view.refresh = lambda: view  # type: ignore[assignment]

        with view.draft() as v:
            assert v is view
            assert view.is_draft_mode is True

        # After clean exit: enter → submit → exit
        calls = mock_client.pipeline.draft_mode.call_args_list
        assert calls[0] == call(view.id, DraftCommand.ENTER, SAMPLE_DATASET_ID)
        assert calls[1] == call(view.id, DraftCommand.SUBMIT, SAMPLE_DATASET_ID)
        assert calls[2] == call(view.id, DraftCommand.EXIT, SAMPLE_DATASET_ID)
        assert view.is_draft_mode is False

    def test_exception_enters_and_discards(self, mock_client: MammothClient) -> None:
        view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        view.refresh = lambda: view  # type: ignore[assignment]

        with pytest.raises(ValueError, match="boom"), view.draft():
            assert view.is_draft_mode is True
            raise ValueError("boom")

        # After exception: enter → discard → exit
        calls = mock_client.pipeline.draft_mode.call_args_list
        assert calls[0] == call(view.id, DraftCommand.ENTER, SAMPLE_DATASET_ID)
        assert calls[1] == call(view.id, DraftCommand.DISCARD, SAMPLE_DATASET_ID)
        assert calls[2] == call(view.id, DraftCommand.EXIT, SAMPLE_DATASET_ID)
        assert view.is_draft_mode is False


class TestIsDraftModeProperty:
    def test_reflects_state(self, mock_client: MammothClient) -> None:
        view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        assert view.is_draft_mode is False

        view._draft_mode = True
        assert view.is_draft_mode is True

        view._draft_mode = False
        assert view.is_draft_mode is False


class TestSetAutoRun:
    def test_enable_clears_draft_flag(self, mock_client: MammothClient) -> None:
        view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        view._draft_mode = True

        result = view.set_auto_run(True)

        mock_client.pipeline.edit_pipeline.assert_called_once_with(
            view.id,
            [{"op": "command", "path": "auto_run", "value": True}],
            SAMPLE_DATASET_ID,
        )
        assert view.is_draft_mode is False
        assert result == {"state": "ready"}

    def test_disable_sets_draft_flag(self, mock_client: MammothClient) -> None:
        view = View(mock_client, SAMPLE_VIEW_DATA, SAMPLE_DATASET_ID)
        assert view._draft_mode is False

        result = view.set_auto_run(False)

        mock_client.pipeline.edit_pipeline.assert_called_once_with(
            view.id,
            [{"op": "command", "path": "auto_run", "value": False}],
            SAMPLE_DATASET_ID,
        )
        assert view.is_draft_mode is True
        assert result == {"state": "ready"}
