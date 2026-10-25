"""``meta.opens``: the objects a write made or changed."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import opens
from mammoth_cli.runtime.invocation import Invocation


def test_an_upload_opens_every_dataset_it_made() -> None:
    invocation = Invocation(command_id="file.upload", output="json", project=9)
    record = command_by_id("file.upload") or {}
    result = {"dataset_id": 5, "dataset_ids": [5, 6], "status": "ready"}
    assert opens._targets(invocation, record, result) == [
        ("dataset", 5, True),
        ("dataset", 6, True),
    ]


def _with_input(monkeypatch: pytest.MonkeyPatch, document: dict[str, Any]) -> None:
    monkeypatch.setattr(Invocation, "bound_input", lambda _self: document)


def test_an_append_changes_its_target_and_does_not_make_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _with_input(monkeypatch, {"append_to_ds_id": 49})
    invocation = Invocation(command_id="file.upload", output="json", project=9)
    record = command_by_id("file.upload") or {}
    result = {"dataset_id": 49, "dataset_ids": [49], "appended_to": 49}
    assert opens._targets(invocation, record, result) == [("dataset", 49, False)]


def test_an_export_into_an_existing_dataset_does_not_make_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _with_input(monkeypatch, {"target_ds_id": 12, "save_as_mode": "APPEND_TO_DS"})
    invocation = Invocation(
        command_id="view.export.dataset", output="json", project=9, extra_args=["3"]
    )
    record = command_by_id("view.export.dataset") or {}
    targets = opens._targets(invocation, record, {"dataset_id": 12, "view_id": 3})
    assert all(created is False for _kind, _id, created in targets)
