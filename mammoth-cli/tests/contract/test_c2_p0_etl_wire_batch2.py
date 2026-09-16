"""Independent wire checks for the next ten mapped ETL routes.

These invoke real CLI handlers against the recording transport.  They are
offline route evidence only; no release service is contacted.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation

PROJECT = 3
DATASET = 731
VIEW = 278
TASK = 41
EXPORT = 19


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
def _bind(monkeypatch: pytest.MonkeyPatch, service: Any):
    @contextmanager
    def open_service(_invocation: Invocation):
        yield service, type("Auth", (), {"workspace_id": 4})()

    monkeypatch.setattr(view, "open_service", open_service)
    yield


def _path(api: Any) -> str:
    return api.last().path.removeprefix("/api/v2")


def test_next_ten_etl_routes_have_literal_wire_contracts(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    api.default(200, {"limit": 50, "offset": 0, "next": "", "exports": []})

    def run(
        command: str,
        args: list[str],
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        input_file = None
        if payload is not None:
            input_file = str(tmp_path / f"{command.replace('.', '-')}.json")
            Path(input_file).write_text(json.dumps(payload), encoding="utf-8")
        with _bind(monkeypatch, service):
            getattr(view, command.replace(".", "_"))(_inv(command, args, input_file, **kwargs))

    # REL-206, REL-213, REL-459, REL-460, REL-215, REL-301.
    run("view.pipeline.get", [str(VIEW)], {"dataset_id": DATASET})
    assert (api.last().method, _path(api)) == (
        "GET",
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline",
    )

    run(
        "view.pipeline.items",
        [str(VIEW)],
        {
            "dataset_id": DATASET,
            "fields": "__full",
            "limit": 23,
            "offset": 4,
            "status": "success",
        },
    )
    assert api.last().query == {
        "fields": ["__full"],
        "limit": ["23"],
        "offset": ["4"],
        "status": ["success"],
    }

    run("view.pipeline.rerun", [str(VIEW)], {"dataset_id": DATASET, "from_sequence": 3})
    assert (api.last().method, _path(api), api.last().json_body) == (
        "POST",
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/rerun",
        {"from_sequence": 3},
    )

    spec = {
        "task_spec": {"DATAVIEW_ID": VIEW, "MATH": {"expression": "value"}},
        "dataset_id": DATASET,
    }
    run("view.task.preview", [str(VIEW)], spec)
    assert (api.last().method, _path(api), api.last().json_body) == (
        "POST",
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/task_preview",
        {"DATAVIEW_ID": VIEW, "MATH": {"expression": "value"}},
    )

    run("view.task.get", [str(VIEW), str(TASK)], {"dataset_id": DATASET})
    assert (api.last().method, _path(api)) == (
        "GET",
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/tasks/{TASK}",
    )

    run("view.task.update", [str(VIEW), str(TASK)], spec)
    assert (api.last().method, _path(api), api.last().json_body) == (
        "PATCH",
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/tasks/{TASK}",
        {"DATAVIEW_ID": VIEW, "MATH": {"expression": "value"}},
    )

    run("view.export.get", [str(VIEW), str(EXPORT)], {"dataset_id": DATASET, "fields": "__full"})
    assert api.last().query == {"fields": ["__full"]}
    assert _path(api).endswith(
        f"/datasets/{DATASET}/dataviews/{VIEW}/pipeline/exports/{EXPORT}"
    )

    run(
        "view.export.update",
        [str(VIEW), str(EXPORT)],
        {
            "dataset_id": DATASET,
            "patches": [{"op": "replace", "path": "status", "value": "paused"}],
        },
        yes=True,
    )
    assert (api.last().method, api.last().json_body) == (
        "PATCH",
        {"patches": [{"op": "replace", "path": "status", "value": "paused"}]},
    )

    run("view.export.delete", [str(VIEW), str(EXPORT)], {"dataset_id": DATASET}, yes=True)
    assert (api.last().method, _path(api)) == (
        "DELETE",
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/exports/{EXPORT}",
    )

    with _bind(monkeypatch, service):
        with pytest.raises(CliError) as exc:
            view.view_export_delete(_inv("view.export.delete", [str(VIEW), str(EXPORT)]))
    assert exc.value.code == "confirmation_required"


def test_export_list_explicit_parent_wires_exact_scope(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    api.default(200, {"limit": 50, "offset": 0, "next": "", "exports": []})
    document = tmp_path / "export-list.json"
    document.write_text(json.dumps({"dataset_id": DATASET}), encoding="utf-8")
    with _bind(monkeypatch, service):
        view.view_export_list(_inv("view.export.list", [str(VIEW)], str(document)))
    assert (api.last().method, _path(api)) == (
        "GET",
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/exports",
    )
