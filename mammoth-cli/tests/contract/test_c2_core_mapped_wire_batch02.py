"""Independent offline wire checks for ten ETL-critical Core read routes."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import dataset, project, trash, view
from mammoth_cli.runtime.invocation import Invocation

PROJECT = 3
DATASET = 731
VIEW = 278


def _inv(command: str, args: list[str], input_file: str | None = None) -> Invocation:
    return Invocation(
        command,
        output="json",
        project=PROJECT,
        no_input=True,
        extra_args=args,
        input_file=input_file,
    )


@contextmanager
def _bind(monkeypatch: pytest.MonkeyPatch, module: Any, service: Any):
    @contextmanager
    def opened(_invocation: Invocation):
        yield service, type("Auth", (), {"workspace_id": 4})()

    monkeypatch.setattr(module, "open_service", opened)
    yield


def _path(api: Any) -> str:
    return api.last().path.removeprefix("/api/v2")


def test_batch02_operations_match_pinned_openapi() -> None:
    """Keep the literal transport checks anchored to the pinned contract."""
    spec = json.loads(
        (Path(__file__).parents[2] / "spec" / "openapi" / "openapi.json").read_text(
            encoding="utf-8"
        )
    )
    prefix = "/workspaces/{workspace_id}/projects/{project_id}"
    expected = {
        "GetDatasetData": ("GET", f"{prefix}/datasets/{{dataset_id}}/data"),
        "ListDataviews": ("GET", f"{prefix}/datasets/{{dataset_id}}/dataviews"),
        "GetFileSettings": ("GET", f"{prefix}/datasets/{{dataset_id}}/file_settings"),
        "GetProjectCheckpoints": ("GET", f"{prefix}/checkpoints"),
        "GetProjectDataChecks": ("GET", f"{prefix}/data-checks"),
        "GetPendingChanges": ("GET", f"{prefix}/pending-changes"),
        "GetResourceStatus": ("GET", f"{prefix}/resource-status"),
        "GetResourceDependencies": ("GET", f"{prefix}/resource-dependencies"),
        "ListTrash": ("GET", f"{prefix}/trash"),
        "GetDataviewPreview": (
            "GET",
            f"{prefix}/datasets/{{dataset_id}}/dataviews/{{dataview_id}}/preview",
        ),
    }
    actual = {}
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            if isinstance(operation, dict) and operation.get("operationId") in expected:
                actual[operation["operationId"]] = (method.upper(), path)
    assert actual == expected


def test_core_read_batch02_matches_literal_release_wire(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    api.default(200, {"items": [], "next": ""})

    def run(
        module: Any,
        command: str,
        args: list[str],
        payload: dict[str, Any] | None = None,
    ) -> None:
        input_file = None
        if payload is not None:
            input_file = str(tmp_path / f"{command.replace('.', '-')}.json")
            Path(input_file).write_text(json.dumps(payload), encoding="utf-8")
        with _bind(monkeypatch, module, service):
            handler_names = {
                "dataset.file-settings.get": "dataset_file_settings",
                "project.data-check.list": "project_data_check_list",
                "view.preview": "view_preview",
            }
            default_name = command.replace(".", "_").replace("-", "_")
            handler = getattr(module, handler_names.get(command, default_name))
            handler(_inv(command, args, input_file))

    # REL-196 dataset data.
    run(dataset, "dataset.data", [str(DATASET)], {"timeout": 17, "poll_interval": 2})
    # timeout/poll_interval are local job-wait controls, not HTTP query fields.
    assert (_path(api), api.last().method, api.last().query) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/data",
        "GET",
        {},
    )

    # REL-197 dataview list.
    run(view, "view.list", [str(DATASET)], {"limit": 13, "sort": "-created_at"})
    assert (_path(api), api.last().method, api.last().query) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews",
        "GET",
        {"limit": ["13"], "sort": ["-created_at"]},
    )

    # REL-219 dataset file settings.
    run(dataset, "dataset.file-settings.get", [str(DATASET)])
    assert (_path(api), api.last().method) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/file_settings",
        "GET",
    )

    project_cases = [
        (
            "project.checkpoint.list",
            "project_checkpoint_list",
            {"fields": "__full", "dataview_id": VIEW, "status": "ready"},
            f"/workspaces/4/projects/{PROJECT}/checkpoints",
            {"fields": ["__full"], "dataview_id": [str(VIEW)], "status": ["ready"]},
        ),
        (
            "project.data-check.list",
            "project_data_check_list",
            {"fields": "__full", "dataview_id": VIEW, "sequence": 4},
            f"/workspaces/4/projects/{PROJECT}/data-checks",
            {"fields": ["__full"], "dataview_id": [str(VIEW)], "sequence": ["4"]},
        ),
        (
            "project.pending-changes",
            "project_pending_changes",
            None,
            f"/workspaces/4/projects/{PROJECT}/pending-changes",
            {},
        ),
        (
            "project.resource-status",
            "project_resource_status",
            None,
            f"/workspaces/4/projects/{PROJECT}/resource-status",
            {},
        ),
    ]
    for command, handler_name, payload, expected_path, expected_query in project_cases:
        run(project, command, [str(PROJECT)], payload)
        assert (_path(api), api.last().method, api.last().query) == (
            expected_path,
            "GET",
            expected_query,
        )

    run(
        project,
        "project.resource-dependencies",
        [str(PROJECT)],
        {"resource_ids": ["dataset-731", "view-278"], "is_recursive": True},
    )
    assert (_path(api), api.last().method, api.last().query) == (
        f"/workspaces/4/projects/{PROJECT}/resource-dependencies",
        "GET",
        {"resource_ids": ["dataset-731,view-278"], "is_recursive": ["True"]},
    )

    # REL-234 project trash list.
    run(trash, "trash.list", [], {"type": "dataview", "limit": 7, "q": "owned"})
    assert (_path(api), api.last().method, api.last().query) == (
        f"/workspaces/4/projects/{PROJECT}/trash",
        "GET",
        {"type": ["dataview"], "limit": ["7"], "q": ["owned"]},
    )

    # REL-199 view preview.  Supplying dataset_id avoids implicit parent
    # discovery; the preceding metadata request is intentionally harmless.
    run(view, "view.preview", [str(VIEW)], {"dataset_id": DATASET, "rows": 9, "cols": 4})
    assert (_path(api), api.last().method, api.last().query) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/preview",
        "GET",
        {"rows": ["9"], "cols": ["4"]},
    )
