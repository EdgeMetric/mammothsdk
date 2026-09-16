"""Independent offline wires for uncovered task/draft/math Core routes."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view, view_ops
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation

PROJECT = 41
DATASET = 731
VIEW = 278
TASK = 41


def _inv(
    command: str,
    args: list[str],
    path: str,
    *,
    yes: bool = False,
    confirm: str | None = None,
) -> Invocation:
    return Invocation(
        command,
        output="json",
        project=PROJECT,
        no_input=True,
        extra_args=args,
        input_file=path,
        yes=yes,
        confirm=confirm,
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


def _write(tmp_path: Path, name: str, payload: dict[str, Any]) -> str:
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_task_draft_routes_match_pinned_openapi() -> None:
    spec = json.loads(
        (Path(__file__).parents[2] / "spec" / "openapi" / "openapi.json").read_text(
            encoding="utf-8"
        )
    )
    prefix = "/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
    view_prefix = f"{prefix}/dataviews/{{dataview_id}}"
    expected = {
        "ExecutePipelineDraftCommand": ("POST", f"{view_prefix}/draft-mode"),
        "DeleteTask": ("DELETE", f"{view_prefix}/pipeline/tasks/{{task_id}}"),
        "GetTaskPreview": ("POST", f"{view_prefix}/pipeline/task_preview"),
        "EditTask": ("PATCH", f"{view_prefix}/pipeline/tasks/{{task_id}}"),
    }
    actual = {
        operation.get("operationId"): (method.upper(), path)
        for path, methods in spec["paths"].items()
        for method, operation in methods.items()
        if isinstance(operation, dict) and operation.get("operationId") in expected
    }
    assert actual == expected


def test_task_draft_and_math_routes_have_literal_wires(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Exercise routes not covered by the existing pipeline-read batch."""
    service, api = real_service(project_id=PROJECT)
    api.default(200, {})

    def invoke(
        module: Any,
        command: str,
        args: list[str],
        payload: dict[str, Any],
        **flags: Any,
    ) -> None:
        with _bind(monkeypatch, module, service):
            handler = getattr(module, command.replace(".", "_").replace("-", "_"))
            handler(
                _inv(command, args, _write(tmp_path, command.replace(".", "-"), payload), **flags)
            )

    invoke(
        view,
        "view.draft.command",
        [str(VIEW)],
        {"dataset_id": DATASET, "command": "discard"},
        yes=True,
        confirm=str(VIEW),
    )
    assert (api.last().method, _path(api), api.last().json_body) == (
        "POST",
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/draft-mode",
        {"draft_operation": "discard"},
    )
    invoke(view, "view.task.delete", [str(VIEW), str(TASK)], {"dataset_id": DATASET}, yes=True)
    assert (_path(api), api.last().method) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/tasks/{TASK}",
        "DELETE",
    )

    invoke(
        view,
        "view.task.preview",
        [str(VIEW)],
        {
            "dataset_id": DATASET,
            "task_spec": {"task_type": "MATH", "params": {"expression": "amount * 2"}},
        },
    )
    assert (_path(api), api.last().method, api.last().json_body) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/task_preview",
        "POST",
        {"task_type": "MATH", "params": {"expression": "amount * 2"}},
    )

    invoke(
        view,
        "view.task.update",
        [str(VIEW), str(TASK)],
        {
            "dataset_id": DATASET,
            "task_spec": {"task_type": "MATH", "params": {"expression": "amount * 2"}},
        },
    )
    assert (_path(api), api.last().method, api.last().json_body) == (
        f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/dataviews/{VIEW}/pipeline/tasks/{TASK}",
        "PATCH",
        {"task_type": "MATH", "params": {"expression": "amount * 2"}},
    )

    # A successful math transform requires a server-backed display-name map;
    # the offline default has no metadata, so assert the safe failure path
    # instead of fabricating a column schema or payload oracle.
    before = len(api.requests)
    with _bind(monkeypatch, view_ops, service):
        with pytest.raises(CliError, match="Column reference"):
            view_ops.view_transform_math(
                _inv(
                    "view.transform.math",
                    [str(VIEW)],
                    _write(
                        tmp_path,
                        "math-invalid",
                        {"dataset_id": DATASET, "expression": "unknown * 2"},
                    ),
                )
            )
    assert len(api.requests) > before
    assert any("/dataviews/278" in request.path for request in api.requests[before:])
    assert not any(
        request.method == "POST" and "/pipeline/tasks" in request.path
        for request in api.requests[before:]
    )


def test_destructive_task_and_draft_routes_do_not_request_without_confirmation(
    real_service: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, api = real_service(project_id=PROJECT)
    payload = _write(tmp_path, "blocked", {"dataset_id": DATASET, "command": "discard"})
    with _bind(monkeypatch, view, service):
        with pytest.raises(CliError, match="explicit confirmation"):
            view.view_draft_command(_inv("view.draft.command", [str(VIEW)], payload))
        with pytest.raises(CliError, match="confirmation"):
            view.view_task_delete(
                _inv(
                    "view.task.delete",
                    [str(VIEW), str(TASK)],
                    _write(tmp_path, "blocked-task", {"dataset_id": DATASET}),
                )
            )
    assert api.requests == []
