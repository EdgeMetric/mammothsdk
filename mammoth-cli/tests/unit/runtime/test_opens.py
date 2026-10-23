"""``meta.opens``: the objects a write made or changed."""

from __future__ import annotations

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
