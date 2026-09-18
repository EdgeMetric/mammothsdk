"""Offline exact-wire checks for high-priority Core delete routes.

The fake transport records requests and is the only oracle used here; no
release or backend endpoint is contacted.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import batch, dashboard, dataset, project
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation

PROJECT, DATASET, BATCH, DASHBOARD, TEMPLATE = 3, 731, 12, 91, 44


def _inv(command: str, args: list[str], input_file: str | None = None, **kwargs: Any) -> Invocation:
    return Invocation(
        command,
        output="json",
        project=PROJECT,
        no_input=True,
        extra_args=args,
        input_file=input_file,
        **kwargs,
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


def test_delete_batch03_routes_match_release_openapi() -> None:
    """Pin operation IDs to the release method/path contract."""
    expected = {
        "DeleteDashboard": ("DELETE", "/dashboards/{dashboard_id}"),
        "DashboardV3DeleteTemplate": ("DELETE", "/dashboards/v3/templates/{template_id}"),
        "DeleteProjects": ("DELETE", "/workspaces/{workspace_id}/projects"),
        "DeleteProject": ("DELETE", "/workspaces/{workspace_id}/projects/{project_id}"),
        "DeleteDatasets": ("DELETE", "/workspaces/{workspace_id}/projects/{project_id}/datasets"),
        "DeleteDataset": (
            "DELETE",
            "/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}",
        ),
        "DeleteBatches": (
            "DELETE",
            "/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/batches",
        ),
        "DeleteBatch": (
            "DELETE",
            "/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/batches/{batch_id}",
        ),
    }
    fixture_path = (
        Path(__file__).parent / "fixtures" / "openapi-release-20260916-delete-routes.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert fixture["schema_version"] == 1
    assert fixture["source"] == {
        "path": "OPENAPI-release-20260916.json",
        "sha256": "b7c5aa651e6820dfee79afa9c10d17332e03c82e20f65ac30105879b8795236c",
    }
    actual = {operation_id: tuple(route) for operation_id, route in fixture["routes"].items()}
    assert actual == expected


def test_delete_batch03_emits_exact_method_path_query_and_no_body(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    api.default(200, {"ok": True})

    def run(
        module: Any,
        command: str,
        args: list[str],
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        input_file = None
        if payload is not None:
            input_file = str(tmp_path / (command.replace(".", "-") + ".json"))
            Path(input_file).write_text(json.dumps(payload), encoding="utf-8")
        with _bind(monkeypatch, module, service):
            getattr(module, command.replace(".", "_").replace("-", "_"))(
                _inv(command, args, input_file, yes=True, **kwargs)
            )

    run(dashboard, "dashboard.delete", [str(DASHBOARD)])
    assert (_path(api), api.last().method, api.last().query, api.last().json_body) == (
        f"/dashboards/{DASHBOARD}",
        "DELETE",
        {},
        None,
    )
    # REL-009: generated Dashboard V3 SDK operation, kept separate from the
    # legacy workspace-template CLI command.
    service._client.dashboards.template_delete(str(TEMPLATE))
    assert (_path(api), api.last().method, api.last().query, api.last().json_body) == (
        f"/dashboards/v3/templates/{TEMPLATE}",
        "DELETE",
        {},
        None,
    )
    run(project, "project.bulk-delete", [], {"project_ids": [17, 18]})
    assert (_path(api), api.last().method, api.last().query, api.last().json_body) == (
        "/workspaces/4/projects",
        "DELETE",
        {"ids": ["17,18"]},
        None,
    )
    run(project, "project.delete", [str(PROJECT)])
    assert (_path(api), api.last().method, api.last().query, api.last().json_body) == (
        f"/workspaces/4/projects/{PROJECT}",
        "DELETE",
        {},
        None,
    )
    # The release route rejects an empty id list (4DSET025), so the CLI
    # requires dataset_ids and sends them as the ids query parameter.
    run(dataset, "dataset.bulk-delete", [], {"dataset_ids": [7, 8]})
    assert (_path(api), api.last().method, api.last().query, api.last().json_body) == (
        f"/workspaces/4/projects/{PROJECT}/datasets",
        "DELETE",
        {"ids": ["7,8"]},
        None,
    )
    run(dataset, "dataset.delete", [str(DATASET)])
    assert (_path(api), api.last().method, api.last().query, api.last().json_body) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}",
        "DELETE",
        {},
        None,
    )
    run(batch, "batch.bulk-delete", [str(DATASET)], {"ids": [5, 6]})
    assert (_path(api), api.last().method, api.last().query, api.last().json_body) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/batches",
        "DELETE",
        {"ids": ["5,6"]},
        None,
    )
    run(batch, "batch.delete", [str(DATASET), str(BATCH)])
    assert (_path(api), api.last().method, api.last().query, api.last().json_body) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/batches/{BATCH}",
        "DELETE",
        {},
        None,
    )


@pytest.mark.parametrize(
    ("module", "command", "args"),
    [
        (dashboard, "dashboard.delete", ["bad"]),
        (project, "project.delete", ["bad"]),
        (dataset, "dataset.delete", ["bad"]),
        (batch, "batch.delete", ["bad", "12"]),
    ],
)
def test_delete_batch03_invalid_target_is_safe(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, module: Any, command: str, args: list[str]
) -> None:
    service, api = real_service(project_id=PROJECT)
    with _bind(monkeypatch, module, service):
        with pytest.raises(CliError):
            getattr(module, command.replace(".", "_").replace("-", "_"))(
                _inv(command, args, yes=True)
            )
    assert api.requests == []
