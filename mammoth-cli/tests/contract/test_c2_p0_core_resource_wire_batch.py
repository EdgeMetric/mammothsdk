"""Recording-transport wire checks for ten Core ETL resource routes."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pytest

from mammoth_cli.commands import dataset, file, folder, project
from mammoth_cli.runtime.invocation import Invocation

PROJECT = 3
DATASET = 731
FILE = 91
FOLDER = 17


def _inv(command: str, args: list[str], **kwargs: Any) -> Invocation:
    return Invocation(
        command, output="json", project=PROJECT, no_input=True, extra_args=args, **kwargs
    )


@contextmanager
def _bind(monkeypatch: pytest.MonkeyPatch, module: Any, service: Any):
    @contextmanager
    def opened(_invocation: Invocation):
        yield service, type("Auth", (), {"workspace_id": 4})()

    monkeypatch.setattr(module, "open_service", opened)
    yield


#: Commands whose handler issues a trailing read after its own request; the
#: command's own wire call is that many requests back from the last one.
#: dataset.get also reads the dataview count for its "hint" (T1-I-13).
_TRAILING_READS = {"dataset.get": 1}


def _own_request(api: Any, command: str) -> Any:
    return api.requests[-1 - _TRAILING_READS.get(command, 0)]


def _path(api: Any, command: str) -> str:
    return _own_request(api, command).path.removeprefix("/api/v2")


def test_core_resource_reads_and_lifecycle_wire(
    real_service: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, api = real_service(project_id=PROJECT)
    api.default(200, {"projects": [{"id": PROJECT, "name": "owned"}]})
    api.on("GET", rf"/files/{FILE}$", body={"file": {}})
    api.on("GET", r"/files$", body={"files": [], "next": ""})
    api.on("GET", rf"/folders/{FOLDER}$", body={"folder": {}})
    # The folder is named by its resource id (1000 + its own id); the CLI lists the project once.
    api.on(
        "GET",
        r"/folders$",
        body={"folders": [{"id": FOLDER, "resource_id": 1000 + FOLDER}], "next": ""},
    )
    cases = [
        (
            project,
            "project.get",
            [str(PROJECT)],
            "/workspaces/4/projects",
            "GET",
        ),
        (project, "project.list", [], "/workspaces/4/projects", "GET"),
        (
            dataset,
            "dataset.get",
            [str(DATASET)],
            f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}",
            "GET",
        ),
        (dataset, "dataset.list", [], f"/workspaces/4/projects/{PROJECT}/datasets", "GET"),
        (
            dataset,
            "dataset.trash",
            [str(DATASET)],
            f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/trash",
            "POST",
        ),
        (
            dataset,
            "dataset.restore",
            [str(DATASET)],
            f"/workspaces/4/projects/{PROJECT}/datasets/{DATASET}/restore",
            "POST",
        ),
        (
            file,
            "file.get",
            [str(FILE)],
            f"/workspaces/4/projects/{PROJECT}/files/{FILE}",
            "GET",
        ),
        (file, "file.list", [], f"/workspaces/4/projects/{PROJECT}/files", "GET"),
        (
            folder,
            "folder.get",
            [str(1000 + FOLDER)],
            f"/workspaces/4/projects/{PROJECT}/folders/{FOLDER}",
            "GET",
        ),
        (folder, "folder.list", [], f"/workspaces/4/projects/{PROJECT}/folders", "GET"),
    ]
    for module, command, args, expected, method in cases:
        with _bind(monkeypatch, module, service):
            getattr(module, command.replace(".", "_"))(_inv(command, args))
        assert (_own_request(api, command).method, _path(api, command)) == (
            method,
            expected,
        ), command
