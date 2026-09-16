"""Offline REL-308 CLI-to-HTTP controls for resource data-sync PATCH."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import project as project_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation

PROJECT = 7


def _invocation(input_file: str, **kwargs: Any) -> Invocation:
    return Invocation(
        "project.resource-dependencies.update",
        output="json",
        project=PROJECT,
        no_input=True,
        extra_args=[str(PROJECT)],
        input_file=input_file,
        **kwargs,
    )


@contextmanager
def _bind(monkeypatch: pytest.MonkeyPatch, service: Any):
    @contextmanager
    def context(_invocation: Invocation):
        yield service, type("Auth", (), {"workspace_id": 4})()

    monkeypatch.setattr(project_cmd, "open_service", context)
    yield


def test_rel308_approved_cli_emits_exact_patch_wire(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    payload = {
        "patches": [
            {
                "op": "replace",
                "path": "data_sync",
                "value": {
                    "context_type": "dataview",
                    "context_id": 42,
                    "data_pass_through": None,
                    "run_pending_update": True,
                },
            }
        ]
    }
    source = tmp_path / "patch.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    with _bind(monkeypatch, service):
        project_cmd.project_resource_dependencies_update(
            _invocation(str(source), yes=True, confirm=str(PROJECT))
        )
    request = api.last()
    assert request.method == "PATCH"
    assert request.path.removeprefix("/api/v2") == (
        f"/workspaces/4/projects/{PROJECT}/resource-dependencies"
    )
    assert request.json_body == payload


def test_rel308_confirmation_blocks_request(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    source = tmp_path / "patch.json"
    source.write_text(
        json.dumps(
            {
                "patches": [
                    {
                        "op": "replace",
                        "path": "data_sync",
                        "value": {"context_type": "task", "context_id": 9},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with _bind(monkeypatch, service):
        with pytest.raises(CliError) as error:
            project_cmd.project_resource_dependencies_update(_invocation(str(source)))
    assert error.value.code == "confirmation_required"
    assert api.requests == []
