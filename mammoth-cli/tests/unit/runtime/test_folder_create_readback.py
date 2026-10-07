"""``folder create`` readback ids must resolve against the shape the command returns."""

from __future__ import annotations

from typing import Any

from mammoth.models.folders import FolderSchema
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.state import _resolve_source


def test_folder_create_readback_id_resolves_from_the_flat_folder_result() -> None:
    # `folder create` returns the SDK FolderSchema dump itself, with no `folder` wrapper.
    result: dict[str, Any] = FolderSchema(id=4321, name="RS-12", resource_id="res-abc").model_dump(
        mode="json"
    )
    readback = (command_by_id("folder.create") or {})["readback"]
    invocation = Invocation(command_id="folder.create", output="json", profile="default")

    resolved = {
        name: _resolve_source(source, result, invocation)
        for name, source in readback["ids"].items()
    }

    assert resolved == {"folder_id": 4321}
