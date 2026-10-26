"""``meta.opens`` and the undo built from it (#311)."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import journal, opens
from mammoth_cli.runtime.dispatch import Outcome, Request
from mammoth_cli.runtime.invocation import Invocation


def _opens(command_id: str, result: dict[str, object], *args: str) -> list[tuple[str, int, bool]]:
    invocation = Invocation(command_id=command_id, output="json", project=9, extra_args=list(args))
    return opens._targets(invocation, command_by_id(command_id) or {}, result)


def test_variants_open_every_view_they_made() -> None:
    result = {"view_ids": [31, 32, 33], "variants": []}
    assert _opens("view.variants.create", result, "5") == [
        ("view", 31, True),
        ("view", 32, True),
        ("view", 33, True),
    ]


def test_the_undo_of_variants_trashes_every_one_of_them() -> None:
    made = [{"kind": "view", "id": n, "created": True} for n in (31, 32, 33)]
    request = Request(
        "view.variants.create",
        "json",
        lambda: ({}, {}),
        invocation=Invocation(command_id="view.variants.create", output="json", project=9),
        profile="p",
    )
    lines, reason = journal.compensation(
        request, Outcome(data={}, meta={"opens": made}), journal._Before()
    )
    assert reason is None
    assert [line["args"] for line in lines] == [[33], [32], [31]]


def test_a_live_chart_made_before_is_not_created_again() -> None:
    assert _opens("dashboard.live-chart.create", {"dashboard_id": 70}) == [("dashboard", 70, False)]


def test_a_new_live_chart_is_created() -> None:
    result = {"dashboard_id": 71, "job_id": 4}
    assert _opens("dashboard.live-chart.create", result) == [("dashboard", 71, True)]


def test_the_undo_of_a_repeated_live_chart_trashes_nothing() -> None:
    request = Request(
        "dashboard.live-chart.create",
        "json",
        lambda: ({}, {}),
        invocation=Invocation(command_id="dashboard.live-chart.create", output="json"),
        profile="p",
    )
    existing = [{"kind": "dashboard", "id": 70, "created": False}]
    lines, reason = journal.compensation(
        request, Outcome(data={}, meta={"opens": existing}), journal._Before()
    )
    assert lines == [] and reason is not None


def _as_result(
    monkeypatch: pytest.MonkeyPatch, command_id: str, data: Any, document: dict[str, Any]
) -> dict[str, Any]:
    invocation = Invocation(command_id=command_id, output="json", project=9)
    monkeypatch.setattr(Invocation, "load_input", lambda _self: document)
    return opens._as_result(invocation, data)


def test_the_job_id_of_an_upload_that_did_not_wait_names_no_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The bare id is a job, not a dataset: undo must never trash a dataset with that number.
    document = {"files": ["a.csv"], "wait_for_completion": False}
    assert _as_result(monkeypatch, "file.upload", 987654, document) == {}
    assert (
        _as_result(monkeypatch, "file.upload-folder", 987654, {"wait_for_completion": False}) == {}
    )


def test_a_folder_upload_that_waited_names_the_datasets_it_made(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _as_result(monkeypatch, "file.upload-folder", [12, 13], {}) == {"dataset_ids": [12, 13]}
