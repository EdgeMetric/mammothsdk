"""SDK-foundation contract tests (Phase 2).

Red until the public SDK gains a deterministic session close, context-manager
support, and server-backed draft state that survives process boundaries.
"""

from __future__ import annotations

import inspect

import pytest


def test_client_has_public_close_and_context_manager() -> None:
    from mammoth.client import MammothClient

    assert hasattr(MammothClient, "close"), "MammothClient needs a public close()"
    assert hasattr(MammothClient, "__enter__") and hasattr(
        MammothClient, "__exit__"
    ), "MammothClient must support the context-manager protocol"


def test_public_dataview_to_dataset_resolver_exists() -> None:
    from mammoth.api.pipeline import PipelineAPI
    from mammoth.client import MammothClient

    # A public typed resolver on both the client and the pipeline sub-client,
    # so public view conveniences never reach a private cross-subclient helper.
    assert callable(getattr(MammothClient, "find_dataset_for_dataview", None))
    assert callable(getattr(PipelineAPI, "find_dataset_for_dataview", None))


def test_draft_state_survives_process_boundaries() -> None:
    from mammoth.api import pipeline

    api = pipeline.PipelineAPI
    # A server-backed draft status read must exist so separate CLI processes
    # observe the same draft state.
    getter = getattr(api, "get_draft_status", None)
    assert getter is not None and callable(
        getter
    ), "PipelineAPI needs a public server-backed draft status reader"
    sig = inspect.signature(getter)
    assert "dataview_id" in sig.parameters


def test_typed_pagination_page_is_public() -> None:
    try:
        from mammoth.models.pagination import Page  # type: ignore
    except ModuleNotFoundError:
        pytest.fail("a public typed pagination Page model must exist")
    assert hasattr(Page, "items") or "items" in getattr(Page, "model_fields", {})
