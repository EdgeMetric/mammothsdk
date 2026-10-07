"""One-call transform ops: ``view transform update-column`` and ``first-name``.

Rashmi's report #5: an agent spent about six minutes on a draft-mode transform
of two steps, most of it on discovery calls and on the draft submit. Each op is
one command: it adds the step, submits a draft that held nothing else, and
waits on its own task's run, not on the pipeline reading ready.

Real-code: the genuine CLI, service and SDK client, with only the HTTP socket
faked. The fake server below keeps the draft and task state a real one keeps:
a staged task does not run until the draft is submitted, and the pipeline reads
``ready`` from then on, before the task's own run is over.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.commands import view_ops

ServiceFactory = Callable[..., Any]
DATASET, VIEW, TASK = 55, 3062, 7158


class _Server:
    """A view's pipeline: draft mode, its tasks, and the run of the one task added."""

    def __init__(
        self, draft: str | None, polls_until_done: int = 3, final_status: str = "DONE"
    ) -> None:
        self.draft = draft
        self.polls_until_done = polls_until_done
        self.final_status = final_status
        self.task_added = False
        self.submitted = False
        self.reads_after_submit = 0

    def mount(self, api: Any) -> None:
        api.on("GET", r"/pipeline$", handler=self._pipeline)
        api.on("GET", r"/pipeline/tasks$", handler=self._task_list)
        api.on("POST", r"/pipeline/tasks$", handler=self._add_task)
        api.on("POST", r"/draft-mode$", handler=self._draft_mode)
        api.on("GET", rf"/datasets/{DATASET}/dataviews/{VIEW}$", handler=self._view)
        api.on(
            "GET",
            rf"/resources/dataview/{VIEW}$",
            body={"resource": {"object_id": VIEW, "dataset": {"id": DATASET, "name": "ds"}}},
        )
        api.on("GET", r"/data$", body={"data": []})

    def _pipeline(self, _request: Any) -> tuple[int, Any]:
        body: dict[str, Any] = {"state": "ready", "execution_state": "idle"}
        if self.draft is not None:
            body["draft"] = self.draft
        return 200, body

    def _task_list(self, _request: Any) -> tuple[int, Any]:
        tasks: list[dict[str, Any]] = [{"id": 1, "transform_status": "DONE"}]
        if self.task_added:
            if self.submitted:
                self.reads_after_submit += 1
            done = self.reads_after_submit > self.polls_until_done
            status = self.final_status if done else ("QUEUED" if self.submitted else None)
            tasks.append({"id": TASK, "transform_status": status})
        return 200, {"tasks": tasks}

    def _add_task(self, _request: Any) -> tuple[int, Any]:
        self.task_added = True
        if self.draft is not None:
            self.draft = "dirty"
        return 202, {"status": "processing", "task_id": TASK}

    def _draft_mode(self, request: Any) -> tuple[int, Any]:
        operation = request.json_body["draft_operation"]
        if operation == "submit":
            self.submitted = True
        elif operation == "exit":
            self.draft = None
        return 200, {}

    def _view(self, _request: Any) -> tuple[int, Any]:
        columns = [
            {"display_name": "Cost", "internal_name": "col_a", "type": "NUMERIC"},
            {"display_name": "Name", "internal_name": "col_b", "type": "TEXT"},
        ]
        return 200, {"id": VIEW, "row_count": 50, "metadata": columns}


def _run(
    monkeypatch: pytest.MonkeyPatch,
    real_service: ServiceFactory,
    server: _Server,
    command: str,
    document: dict[str, Any],
) -> tuple[int, dict[str, Any], Any]:
    """Invoke ``view transform COMMAND`` once; return the exit code, the envelope, the wire."""
    from mammoth_cli.services import factory
    from mammoth_cli.testing import make_runner

    monkeypatch.setattr(view_ops, "_RUN_RETRY_S", 0)
    service, api = real_service(project_id=180)
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )
    server.mount(api)
    result = make_runner().invoke(
        [
            "view",
            "transform",
            command,
            str(VIEW),
            "--project",
            "180",
            "--input",
            json.dumps({"dataset_id": DATASET, **document}),
            "--yes",
            "--output",
            "json",
            "--no-input",
        ]
    )
    return result.exit_code, json.loads(result.output), api


def _task_bodies(api: Any) -> list[dict[str, Any]]:
    return [r.json_body for r in api.requests if r.method == "POST" and r.path.endswith("/tasks")]


def _draft_operations(api: Any) -> list[str]:
    return [r.json_body["draft_operation"] for r in api.requests if r.path.endswith("/draft-mode")]


def test_update_column_in_draft_mode_submits_and_waits_for_its_own_task(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    server = _Server(draft="clean")

    code, envelope, api = _run(
        monkeypatch,
        real_service,
        server,
        "update-column",
        {"column": "Cost", "expression": "Cost + 5"},
    )

    data = envelope["data"]
    assert code == 0, envelope
    [spec] = _task_bodies(api)
    assert spec["MATH"]["DESTINATION"] == "col_a"
    assert _draft_operations(api)[:1] == ["submit"]
    assert data["status"] == "done" and data["draft_applied"] is True
    assert data["run"] == {"task_id": TASK, "transform_status": "DONE"}
    assert server.reads_after_submit > server.polls_until_done
    assert "pipeline_error" not in data


def test_update_column_leaves_a_draft_that_held_other_steps_staged(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    """Submitting would run steps the caller never named."""
    server = _Server(draft="dirty")

    code, envelope, api = _run(
        monkeypatch,
        real_service,
        server,
        "update-column",
        {"column": "Cost", "expression": "Cost + 5"},
    )

    data = envelope["data"]
    assert code == 0, envelope
    assert data["status"] == "staged"
    assert "submit" not in _draft_operations(api)
    assert "run" not in data
    assert not server.submitted


def test_update_column_outside_draft_mode_waits_for_its_own_task(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    server = _Server(draft=None)
    server.submitted = True  # auto-run: the task runs as soon as it is added

    code, envelope, api = _run(
        monkeypatch,
        real_service,
        server,
        "update-column",
        {"column": "Cost", "expression": "Cost + 5"},
    )

    assert code == 0, envelope
    assert envelope["data"]["run"] == {"task_id": TASK, "transform_status": "DONE"}
    assert _draft_operations(api) == []


def test_update_column_whose_task_errors_is_not_reported_done_and_verified(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    server = _Server(draft="clean", final_status="ERROR")

    code, envelope, _api = _run(
        monkeypatch,
        real_service,
        server,
        "update-column",
        {"column": "Cost", "expression": "Cost + 5"},
    )

    data = envelope["data"]
    assert data["pipeline_error"]["execution_state"] == "runtime_error"
    assert data["pipeline_error"]["task_id"] == TASK
    assert data["verify"]["verified"] is False


def test_first_name_extracts_the_first_word_in_one_draft_call(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    server = _Server(draft="clean")

    code, envelope, api = _run(
        monkeypatch,
        real_service,
        server,
        "first-name",
        {"column": "Name", "new_column": "First name"},
    )

    data = envelope["data"]
    assert code == 0, envelope
    [spec] = _task_bodies(api)
    assert spec["SUBSTRING"]["REGEX"]["EXPRESSION"] == r"^\S+"
    assert spec["SUBSTRING"]["SOURCE"] == "col_b"
    assert _draft_operations(api)[:1] == ["submit"]
    assert data["run"] == {"task_id": TASK, "transform_status": "DONE"}


def test_first_name_needs_exactly_one_destination(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    server = _Server(draft="clean")

    code, envelope, api = _run(monkeypatch, real_service, server, "first-name", {"column": "Name"})

    assert code != 0
    assert "new_column or existing_column" in json.dumps(envelope)
    assert _task_bodies(api) == []
