"""``project ensure`` readback ids must resolve against the shape the command returns."""

from __future__ import annotations

from typing import Any

from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.state import _resolve_source


def test_project_ensure_readback_id_resolves_from_the_ensure_result() -> None:
    # `project ensure` returns {project, project_id, created, duplicates}: no top-level `id`.
    result: dict[str, Any] = {
        "project": {"id": 25654, "name": "Prod Errors Monitor"},
        "project_id": 25654,
        "created": False,
        "duplicates": [],
    }
    readback = (command_by_id("project.ensure") or {})["readback"]
    invocation = Invocation(command_id="project.ensure", output="json", profile="default")

    resolved = {
        name: _resolve_source(source, result, invocation)
        for name, source in readback["ids"].items()
    }

    assert resolved == {"project_id": 25654}
