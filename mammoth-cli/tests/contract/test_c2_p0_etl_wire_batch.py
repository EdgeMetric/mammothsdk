"""Independent P0 ETL handler-to-HTTP wire and confirmation controls.

These tests use the real CLI handlers, SDK service, and recording transport.
They are offline contract evidence only; they do not exercise release access.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import dataset as dataset_cmd
from mammoth_cli.commands import file as file_cmd
from mammoth_cli.commands import view as view_cmd
from mammoth_cli.commands import view_ops
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation

PROJECT = 3
DATASET = 731
VIEW = 278


def _inv(command_id: str, args: list[str], input_file: str | None = None, **kw: Any) -> Invocation:
    return Invocation(
        command_id,
        output="json",
        project=PROJECT,
        no_input=True,
        extra_args=args,
        input_file=input_file,
        **kw,
    )


@contextmanager
def _bind(monkeypatch: pytest.MonkeyPatch, module: Any, service: Any):
    @contextmanager
    def context(_invocation: Invocation):
        yield service, type("Auth", (), {"workspace_id": 4})()

    monkeypatch.setattr(module, "open_service", context)
    yield


def _path(api: Any) -> str:
    return api.last().path.removeprefix("/api/v2")


def test_p0_upload_view_create_and_task_add_wires(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    source = tmp_path / "orders.csv"
    source.write_text("id,value\n1,2\n", encoding="utf-8")
    with _bind(monkeypatch, file_cmd, service):
        file_cmd.file_upload(_inv("file.upload", [str(source)]))
    assert api.last().method == "POST"
    assert api.last().path.endswith(f"/workspaces/4/projects/{PROJECT}/files")

    with _bind(monkeypatch, view_ops, service):
        view_ops.view_create(_inv("view.create", [str(DATASET)]))
    assert api.last().method == "POST"
    assert _path(api) == f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews"

    task_input = tmp_path / "task.json"
    task_input.write_text(
        json.dumps({"task_spec": {"MATH": {"expression": "value"}}, "dataset_id": DATASET})
    )
    with _bind(monkeypatch, view_cmd, service):
        view_cmd.view_task_add(_inv("view.task.add", [str(VIEW)], str(task_input)))
    # The add is followed by an unconditional read-back (list_tasks, __full
    # fields) that catches a task whose step errored at run time without
    # flipping has_error; that GET is the last request, the POST the one before.
    add_request, readback_request = api.requests[-2], api.requests[-1]
    assert add_request.method == "POST"
    assert add_request.path.removeprefix("/api/v2") == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/tasks"
    )
    assert add_request.json_body == {
        "DATAVIEW_ID": VIEW,
        "MATH": {"expression": "value"},
    }
    assert readback_request.method == "GET"
    assert readback_request.path.removeprefix("/api/v2") == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/tasks"
    )


def test_p0_export_wire_and_delete_confirmation_controls(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    api.default(200, {"trigger_id": 71})
    export_input = tmp_path / "export.json"
    export_input.write_text(
        json.dumps(
            {
                "export_spec": {
                    "DATAVIEW_ID": VIEW,
                    "handler_type": "internal_dataset",
                    "trigger_type": "pipeline",
                    "target_properties": {"dataset_name": "owned"},
                    "additional_properties": {},
                    "run_immediately": True,
                },
                "dataset_id": DATASET,
            }
        )
    )
    with _bind(monkeypatch, view_cmd, service):
        with pytest.raises(CliError) as exc:
            view_cmd.view_export_create(_inv("view.export.create", [str(VIEW)], str(export_input)))
    assert exc.value.code == "confirmation_required"
    assert not api.requests

    with _bind(monkeypatch, view_cmd, service):
        view_cmd.view_export_create(
            _inv("view.export.create", [str(VIEW)], str(export_input), yes=True)
        )
    assert api.last().method == "POST"
    assert _path(api) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/exports"
    )
    assert api.last().json_body["DATAVIEW_ID"] == VIEW
    assert api.last().json_body["handler_type"] == "internal_dataset"

    with _bind(monkeypatch, view_ops, service):
        with pytest.raises(CliError) as exc:
            view_ops.view_delete(_inv("view.delete", [str(VIEW)]))
    assert exc.value.code == "confirmation_required"

    with _bind(monkeypatch, view_ops, service):
        view_ops.view_delete(
            _inv("view.delete", [str(VIEW), str(DATASET)], yes=True, input_file=None)
        )
    assert api.last().method == "DELETE"
    assert _path(api) == f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}"

    with _bind(monkeypatch, dataset_cmd, service):
        dataset_cmd.dataset_delete(_inv("dataset.delete", [str(DATASET)], yes=True))
    assert api.last().method == "DELETE"
    assert _path(api) == f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}"

    # A wrong parent is a literal wire mismatch, not an authorized fallback.
    wrong_parent = tmp_path / "wrong-parent.json"
    wrong_parent.write_text(json.dumps({"dataset_id": 999}), encoding="utf-8")
    with _bind(monkeypatch, view_ops, service):
        view_ops.view_delete(_inv("view.delete", [str(VIEW)], str(wrong_parent), yes=True))
    assert _path(api) == f"/workspaces/4/projects/{PROJECT}/datasets/999/dataviews/{VIEW}"
