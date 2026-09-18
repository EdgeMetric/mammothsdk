"""Independent C2/S4 lifecycle wire and recovery controls.

The expected requests in this module are hand-authored from the public SDK
adapter behavior.  They deliberately do not import the CLI command-contract
resolver or derive the expected request from CLI metadata.  A passing case
therefore proves the SDK method/path/query/body contract independently of the
CLI's admission and field-binding implementation.

This is an offline oracle only: it uses a recording SDK client and never calls
the Mammoth service.  The route ledger records which routes still lack this
kind of proof.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pytest
from mammoth.api.batches import BatchesAPI
from mammoth.api.jobs import JobsAPI
from mammoth.api.parameters import ParametersAPI
from mammoth.api.snippets import SnippetsAPI
from mammoth.api.workflows import WorkflowsAPI

from mammoth_cli.commands import job as job_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.strict import validate_input_fields
from mammoth_cli.services.command_contract import resolve_command_contract


class _RecordingClient:
    """Minimal public-client seam that records exact SDK request arguments."""

    workspace_id = 17
    project_id = None

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((method, path, kwargs))
        return {"ok": True}

    def _request_list(self, method: str, path: str, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append((method, path, kwargs))
        return [{"ok": True}]


class _InterruptingService:
    """Service seam that proves a polling interrupt does not trigger replay."""

    def __init__(self) -> None:
        self.calls = 0

    def call(self, _sdk_symbol: str, /, **_kwargs: Any) -> Any:
        self.calls += 1
        raise KeyboardInterrupt


@contextmanager
def _service_context(service: _InterruptingService):
    yield service, type("Auth", (), {"workspace_id": 17})()


def test_batch_wire_oracles_cover_query_body_and_distinct_lifecycle_paths() -> None:
    client = _RecordingClient()
    api = BatchesAPI(client)  # type: ignore[arg-type]

    api.list(731, project_id=41, limit=13, offset=5)
    assert client.calls[-1] == (
        "GET",
        "/workspaces/17/projects/41/datasets/731/batches",
        {"params": {"limit": 13, "offset": 5}},
    )

    api.create(
        731,
        732,
        {"S4_SOURCE": "S4_DEST"},
        project_id=41,
        new_ds_params={"name": "S4_DATASET"},
        is_validation_required=True,
        change_map={"S4_OLD": "S4_NEW"},
        delete_source_ds=False,
    )
    assert client.calls[-1] == (
        "POST",
        "/workspaces/17/projects/41/datasets/731/batches",
        {
            "json": {
                "source_id": 732,
                "mapping": [{"source_c_name": "S4_SOURCE", "destination_c_name": "S4_DEST"}],
                "delete_source_ds": False,
                "new_ds_details": {"name": "S4_DATASET"},
                "validate_only": True,
                "change_map": {"S4_OLD": "S4_NEW"},
            }
        },
    )

    api.update(731, [{"op": "replace", "value": {"S4_BATCH": [733]}}], project_id=41)
    assert client.calls[-1] == (
        "PATCH",
        "/workspaces/17/projects/41/datasets/731/batches",
        {"json": {"patch": [{"op": "replace", "value": {"S4_BATCH": [733]}}]}},
    )

    api.bulk_delete(731, ids=[733, 734], project_id=41)
    assert client.calls[-1] == (
        "DELETE",
        "/workspaces/17/projects/41/datasets/731/batches",
        {"params": {"ids": "733,734"}},
    )


def test_job_wire_oracles_cover_single_and_collection_queries() -> None:
    client = _RecordingClient()
    api = JobsAPI(client)  # type: ignore[arg-type]

    api.get_job(811)
    assert client.calls[-1] == (
        "GET",
        "/jobs/811",
        {"headers": {"x-workspace-id": "17"}},
    )

    api.get_jobs([811, 812])
    assert client.calls[-1] == (
        "GET",
        "/jobs",
        {"params": {"job_ids": "811,812"}, "headers": {"x-workspace-id": "17"}},
    )


def test_job_wait_interrupt_is_inspectable_and_never_replayed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _InterruptingService()
    monkeypatch.setattr(job_cmd, "open_service", lambda _invocation: _service_context(service))

    with pytest.raises(CliError) as excinfo:
        job_cmd.job_wait(Invocation(command_id="job.wait", extra_args=["811"]))

    assert excinfo.value.code == "interrupted"
    assert excinfo.value.details == {
        "interrupted": True,
        "job_id": 811,
        "job_handle": 811,
        "operation_state": "running",
        "phase": "polling",
    }
    assert service.calls == 1
    assert excinfo.value.recovery_commands == [
        "mammoth job get 811 --output json --no-input",
        "mammoth job wait 811 --output json --no-input",
    ]


def test_s4_every_route_has_closed_shared_admission() -> None:
    """Every discovered lifecycle/job route rejects fields without a destination."""
    route_ids = {
        str(record["command_id"])
        for record in load_commands()
        if str(record["command_id"]).split(".", 1)[0]
        in {"batch", "job", "parameter", "snippet", "workflow"}
        or str(record["command_id"]).startswith(
            ("view.checkpoint.", "view.draft.", "view.pipeline.", "view.task.", "view.version.")
        )
    }
    # Keep this invariant derived from the manifest: additive routes such as
    # batch.create-spec must be covered without a stale hard-coded total.
    assert "batch.create-spec" in route_ids
    for command_id in route_ids:
        contract = resolve_command_contract(command_id)
        assert contract is not None
        assert contract.extensibility == "closed", command_id
        with pytest.raises(CliError) as error:
            validate_input_fields(command_id, {"__s4_dropped_field__": "sentinel"})
        assert error.value.code == "unknown_input_field"


def test_parameter_wire_oracles_cover_workspace_body_and_query_bindings() -> None:
    client = _RecordingClient()
    api = ParametersAPI(client)  # type: ignore[arg-type]

    api.create(
        "S4_PARAMETER",
        "NUMERIC",
        17,
        description="S4_DESCRIPTION",
        group_id=19,
        scope="project",
        project_id=41,
    )
    assert client.calls[-1] == (
        "POST",
        "/workspaces/17/parameters",
        {
            "json": {
                "name": "S4_PARAMETER",
                "param_type": "NUMERIC",
                "value": 17,
                "scope": "project",
                "description": "S4_DESCRIPTION",
                "group_id": 19,
                "project_id": 41,
            }
        },
    )

    api.group_create("S4_GROUP", color="#123456", project_id=41)
    assert client.calls[-1] == (
        "POST",
        "/workspaces/17/parameters/groups",
        {"params": {"project_id": 41}, "json": {"name": "S4_GROUP", "color": "#123456"}},
    )

    api.group_update(19, name="S4_GROUP_RENAMED", color="#654321", project_id=41)
    assert client.calls[-1] == (
        "PATCH",
        "/workspaces/17/parameters/groups/19",
        {
            "params": {"project_id": 41},
            "json": {"name": "S4_GROUP_RENAMED", "color": "#654321"},
        },
    )

    api.rerun_all_stale(41)
    assert client.calls[-1] == (
        "POST",
        "/workspaces/17/parameters/rerun-all-stale",
        {"params": {"project_id": 41}},
    )


def test_snippet_wire_oracles_cover_body_and_dependency_paths() -> None:
    client = _RecordingClient()
    api = SnippetsAPI(client)  # type: ignore[arg-type]

    api.create(
        "S4_SNIPPET",
        "S4_CODE",
        "sql",
        description="S4_DESCRIPTION",
        group_id=19,
        scope="project",
        project_id=41,
    )
    assert client.calls[-1] == (
        "POST",
        "/workspaces/17/snippets",
        {
            "json": {
                "name": "S4_SNIPPET",
                "code": "S4_CODE",
                "language": "sql",
                "scope": "project",
                "description": "S4_DESCRIPTION",
                "group_id": 19,
                "project_id": 41,
            }
        },
    )

    api.dependencies(901)
    assert client.calls[-1] == (
        "GET",
        "/workspaces/17/snippets/901/dependencies",
        {},
    )

    api.update(901, code="S4_UPDATED", language="expression", group_id=22)
    assert client.calls[-1] == (
        "PATCH",
        "/workspaces/17/snippets/901",
        {"json": {"code": "S4_UPDATED", "language": "expression", "group_id": 22}},
    )


def test_workflow_wire_oracles_cover_project_parent_and_block_adapters() -> None:
    client = _RecordingClient()
    api = WorkflowsAPI(client)  # type: ignore[arg-type]

    api.list(project_id=41)
    assert client.calls[-1] == ("GET", "/workspaces/17/projects/41/workflows", {})

    api.create(
        "S4_WORKFLOW",
        shape="pipeline",
        purpose="S4_PURPOSE",
        seed_datasource_id=77,
        project_id=41,
    )
    assert client.calls[-1] == (
        "POST",
        "/workspaces/17/projects/41/workflows",
        {
            "json": {
                "name": "S4_WORKFLOW",
                "shape": "pipeline",
                "purpose": "S4_PURPOSE",
                "seed_datasource_id": 77,
            }
        },
    )

    api.from_template(88, "S4_FROM_TEMPLATE", project_id=41)
    assert client.calls[-1] == (
        "POST",
        "/workspaces/17/projects/41/workflows/from-template",
        {"json": {"template_id": 88, "workflow_name": "S4_FROM_TEMPLATE"}},
    )

    api.block_auth(91, 92, {"credential_ref": "S4_SECRET_REF"}, project_id=41)
    assert client.calls[-1] == (
        "PATCH",
        "/workspaces/17/projects/41/workflows/91/blocks/92/auth",
        {"json": {"auth_data": {"credential_ref": "S4_SECRET_REF"}}},
    )

    api.canvas(91, {"node": "S4_NODE"}, project_id=41)
    assert client.calls[-1] == (
        "PATCH",
        "/workspaces/17/projects/41/workflows/91/canvas",
        {"json": {"canvas_state": {"node": "S4_NODE"}}},
    )
