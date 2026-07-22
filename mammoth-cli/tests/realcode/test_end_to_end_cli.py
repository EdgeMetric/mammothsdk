"""Full-stack real-code test: CLI argv in, HTTP request + envelope out.

This is the widest real-code path in the suite. It drives the actual Typer app
with real argv, through the real command handler, the real
:class:`~mammoth_cli.services.sdk_service.SdkMammothService`, the real
``MammothClient`` and its sub-clients — with only the HTTP socket faked. The
sole seam replaced is the service factory, and only so the genuine service it
builds has the fake transport mounted on its client; every layer of business
logic runs for real.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.context.resolver import ENV_API_KEY, ENV_API_SECRET, ENV_WORKSPACE_ID
from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]

_ENV = {ENV_API_KEY: "k", ENV_API_SECRET: "s", ENV_WORKSPACE_ID: "4"}


def _bind_real_service(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, **kwargs: Any
) -> Any:
    """Point the CLI's service factory at a real service with a fake transport.

    Returns the :class:`FakeApi` mounted on the built service's client so the
    test can assert the exact HTTP request the real stack emitted.
    """
    service, api = real_service(**kwargs)
    monkeypatch.setattr(factory, "build_service", lambda *a, **k: service)
    return api


def test_project_list_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    """`mammoth project list` reaches the API and renders a real envelope."""
    api = _bind_real_service(monkeypatch, real_service)
    api.on("GET", r"/projects", 200, {"projects": [{"id": 7, "name": "Demo"}]})

    result = make_runner().invoke(["project", "list", "--output", "json", "--no-input"], env=_ENV)

    assert result.exit_code == 0, result.output
    assert any(r.path.endswith("/projects") for r in api.requests)
    envelope = json.loads(result.output)
    assert envelope["data"]["projects"] == [{"id": 7, "name": "Demo"}]


def test_generated_dashboard_path_query_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Any
) -> None:
    api = _bind_real_service(monkeypatch, real_service)
    api.on("GET", r"/dashboards/17/rls/values$", body={"values": ["west"]})
    doc = tmp_path / "rls.json"
    doc.write_text(json.dumps({"column": "region", "search": "west"}), encoding="utf-8")

    result = make_runner().invoke(
        [
            "dashboard",
            "rls",
            "value",
            "list",
            "17",
            "--input",
            str(doc),
            "--output",
            "json",
            "--no-input",
        ],
        env=_ENV,
    )

    assert result.exit_code == 0, result.output
    request = api.last()
    assert request.path.endswith("/dashboards/17/rls/values")
    assert request.query == {"column": ["region"], "search": ["west"]}


def test_dashboard_list_nullable_project_query_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    api = _bind_real_service(monkeypatch, real_service, project_id=42)
    api.on("GET", r"/dashboards$", body={"dashboards": []})

    result = make_runner().invoke(
        ["dashboard", "list", "--project", "42", "--output", "json", "--no-input"],
        env=_ENV,
    )

    assert result.exit_code == 0, result.output
    assert api.last().query == {"project_id": ["42"]}


def test_generated_dashboard_body_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Any
) -> None:
    api = _bind_real_service(monkeypatch, real_service)
    api.on("POST", r"/dashboards/v3/contexts$", body={"id": "ctx-1"})
    doc = tmp_path / "context.json"
    body = {"params": {"name": "Revenue", "type": "analyst"}}
    doc.write_text(json.dumps({"body": body}), encoding="utf-8")

    result = make_runner().invoke(
        [
            "dashboard",
            "context",
            "create",
            "--input",
            str(doc),
            "--output",
            "json",
            "--no-input",
        ],
        env=_ENV,
    )

    assert result.exit_code == 0, result.output
    assert api.last().json_body == body


def test_generated_dashboard_delete_requires_confirmation_and_routes(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    api = _bind_real_service(monkeypatch, real_service)
    api.on("DELETE", r"/dashboards/v3/contexts/abc$", body={})
    argv = [
        "dashboard",
        "context",
        "delete",
        "abc",
        "--output",
        "json",
        "--no-input",
    ]
    refused = make_runner().invoke(argv, env=_ENV)
    assert refused.exit_code != 0
    assert not api.requests

    accepted = make_runner().invoke([*argv, "--yes"], env=_ENV)
    assert accepted.exit_code == 0, accepted.output
    assert api.last().path.endswith("/dashboards/v3/contexts/abc")


def test_view_transform_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Any
) -> None:
    """`view transform bulk-replace` runs argv -> coercion -> real payload."""
    api = _bind_real_service(monkeypatch, real_service, project_id=180)
    api.on(
        "GET",
        r"/browse",
        body={"resources": [{"id": 180, "children": [{"type": "datasource", "id": 55}]}]},
    )
    api.on(
        "GET",
        r"/datasets/55/dataviews/1039$",
        body={
            "id": 1039,
            "metadata": [{"display_name": "Item", "internal_name": "col_item", "type": "TEXT"}],
        },
    )
    api.on("POST", r"/pipeline/tasks", body={})
    api.on("GET", r"/pipeline$", body={"state": "ready"})

    doc = tmp_path / "in.json"
    doc.write_text(
        json.dumps({"columns": ["Item"], "mapping": [{"search": ["a"], "replace": "b"}]}),
        encoding="utf-8",
    )
    result = make_runner().invoke(
        [
            "view",
            "transform",
            "bulk-replace",
            "1039",
            "--project",
            "180",
            "--input",
            str(doc),
            "--output",
            "json",
            "--no-input",
        ],
        env=_ENV,
    )

    assert result.exit_code == 0, result.output
    posts = [r for r in api.requests if r.method == "POST" and r.path.endswith("/tasks")]
    assert len(posts) == 1
    replace = posts[0].json_body["REPLACE"]
    assert replace["SOURCE"] == ["col_item"]
    assert replace["MAPPING"] == [{"SEARCH_VALUE": ["a"], "REPLACE_VALUE": "b"}]
