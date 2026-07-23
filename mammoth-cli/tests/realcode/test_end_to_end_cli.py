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

from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]


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

    result = make_runner().invoke(["project", "list", "--output", "json", "--no-input"])

    assert result.exit_code == 0, result.output
    assert any(r.path.endswith("/projects") for r in api.requests)
    envelope = json.loads(result.output)
    assert envelope["data"]["projects"] == [{"id": 7, "name": "Demo"}]


def test_generated_dashboard_path_query_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Any
) -> None:
    api = _bind_real_service(monkeypatch, real_service)
    api.on(
        "GET",
        r"/dashboards/17/rls/values$",
        body={"column": "region", "total": 1, "values": ["west"]},
    )
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
    )

    assert result.exit_code == 0, result.output
    assert api.last().query == {"project_id": ["42"]}


def test_generated_dashboard_body_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Any
) -> None:
    api = _bind_real_service(monkeypatch, real_service)
    api.on("POST", r"/dashboards/v3/contexts$", body={"context": {"id": "ctx-1"}})
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
    )

    assert result.exit_code == 0, result.output
    assert api.last().json_body == body


def test_generated_dashboard_async_result_waits_for_job(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, tmp_path: Any
) -> None:
    from mammoth.api.jobs import JobsAPI

    observed_timeouts: list[int | None] = []
    real_wait = JobsAPI.wait_for_job

    def recording_wait(
        self: JobsAPI, job_id: int, timeout: int | None = None, poll_interval: int = 2
    ) -> dict[str, Any]:
        observed_timeouts.append(timeout)
        return real_wait(self, job_id, timeout, poll_interval)

    monkeypatch.setattr(JobsAPI, "wait_for_job", recording_wait)
    service, api = real_service()

    def build_with_cli_timeouts(*_args: Any, **kwargs: Any) -> Any:
        service._client.job_timeout = kwargs["job_timeout"]
        return service

    monkeypatch.setattr(factory, "build_service", build_with_cli_timeouts)
    api.on("POST", r"/dashboards/v3/generate$", status=202, body={"job_id": 91})
    api.on(
        "GET",
        r"/jobs/91$",
        body={"id": 91, "status": "success", "response": {"dashboard_id": 73}},
    )
    doc = tmp_path / "generate.json"
    doc.write_text(
        json.dumps({"body": {"params": {"dataview_id": 1, "intent": "Revenue by quarter"}}}),
        encoding="utf-8",
    )

    result = make_runner().invoke(
        [
            "dashboard",
            "v3",
            "generate",
            "--input",
            str(doc),
            "--output",
            "json",
            "--no-input",
            "--job-timeout",
            "7",
        ],
    )

    assert result.exit_code == 0, result.output
    assert [request.method for request in api.requests] == ["POST", "GET"]
    assert observed_timeouts == [7]
    assert json.loads(result.output)["data"] == {"dashboard_id": 73}


def test_generated_dashboard_delete_requires_confirmation_and_routes(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    api = _bind_real_service(monkeypatch, real_service)
    api.on("DELETE", r"/dashboards/v3/contexts/abc$", body={"ok": True})
    argv = [
        "dashboard",
        "context",
        "delete",
        "abc",
        "--output",
        "json",
        "--no-input",
    ]
    refused = make_runner().invoke(argv)
    assert refused.exit_code != 0
    assert not api.requests

    accepted = make_runner().invoke([*argv, "--yes"])
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
    )

    assert result.exit_code == 0, result.output
    posts = [r for r in api.requests if r.method == "POST" and r.path.endswith("/tasks")]
    assert len(posts) == 1
    replace = posts[0].json_body["REPLACE"]
    assert replace["SOURCE"] == ["col_item"]
    assert replace["MAPPING"] == [{"SEARCH_VALUE": ["a"], "REPLACE_VALUE": "b"}]


def test_data_app_user_remove_email_positional_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    """`data-app user remove <id> <email>` routes the email through the real stack.

    Review finding #1: the handler requires the email as a *second positional*,
    but the command contract exposed only one positional. A second positional
    was rejected as ``unexpected_argument`` and ``--input`` produced
    ``missing_argument`` -- so the command could not be invoked at all. This
    drives real argv parsing through to the emitted HTTP request and asserts the
    DELETE carries the email as a query parameter.
    """
    api = _bind_real_service(monkeypatch, real_service)
    api.on("DELETE", r"/data-apps/123/users$", 200, {"removed": True})

    result = make_runner().invoke(
        ["data-app", "user", "remove", "123", "user@example.com", "--yes", "--output", "json"],
    )

    assert result.exit_code == 0, result.output
    removals = [r for r in api.requests if r.method == "DELETE" and "/users" in r.path]
    assert len(removals) == 1
    assert removals[0].path.endswith("/data-apps/123/users")
    assert removals[0].query.get("email") == ["user@example.com"]


def test_data_app_user_remove_rejects_email_via_input(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    """The email is a required positional, not an ``--input`` field.

    With the email missing from the positionals, strict validation must fail
    before any HTTP call -- and it must not be silently satisfied by an
    ``--input`` document (the old, unusable invocation shape).
    """
    api = _bind_real_service(monkeypatch, real_service)

    result = make_runner().invoke(
        [
            "data-app",
            "user",
            "remove",
            "123",
            "--yes",
            "--input",
            '{"email": "user@example.com"}',
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 2, result.output
    assert '"code": "missing_argument"' in result.output
    assert not any(r.method == "DELETE" for r in api.requests), "no HTTP before validation"


def test_folder_get_forwards_fields_input_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    """`folder get` must forward the advertised ``fields`` --input field.

    Review finding #5 (handler/schema drift): ``fields`` was advertised as an
    accepted input field but the handler never forwarded it, so it was silently
    ignored. This drives the real stack and asserts the value reaches the HTTP
    query string.
    """
    api = _bind_real_service(monkeypatch, real_service)
    api.on("GET", r"/folders/88$", 200, {"folder": {"id": 88, "name": "Reports"}})

    result = make_runner().invoke(
        [
            "folder",
            "get",
            "88",
            "--project",
            "180",
            "--input",
            '{"fields": "__full"}',
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    gets = [r for r in api.requests if r.method == "GET" and r.path.endswith("/folders/88")]
    assert len(gets) == 1
    assert gets[0].query.get("fields") == ["__full"], "the advertised `fields` must be forwarded"


def test_folder_delete_positional_id_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    """`folder delete <id>` is invokable and wraps the id into ``folder_ids``.

    Review finding #5 (systematic audit): the id positional was unregistered, so
    the command was uninvokable (surplus positional rejected) while ``folder_ids``
    was advertised as an ignored ``--input`` field. Drives the real stack and
    asserts the DELETE carries the single id.
    """
    api = _bind_real_service(monkeypatch, real_service, project_id=180)
    api.on("DELETE", r"/projects/180/folders$", 200, {"job": {"id": 1}})

    result = make_runner().invoke(
        ["folder", "delete", "7", "--project", "180", "--yes", "--output", "json"],
    )

    assert result.exit_code == 0, result.output
    deletes = [r for r in api.requests if r.method == "DELETE" and r.path.endswith("/folders")]
    assert len(deletes) == 1
    assert deletes[0].query.get("ids") == ["7"]


def test_ai_condition_generate_positional_dataset_full_stack(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    """`ai condition generate <dataset_id>` routes the id and the intent input.

    Review finding #5 (systematic audit): ``dataset_id`` was advertised as an
    ``--input`` field but read only positionally from an unregistered positional,
    making the command uninvokable. Now the id is positional and ``intent`` stays
    an ``--input`` field.
    """
    api = _bind_real_service(monkeypatch, real_service, project_id=180)
    api.on("POST", r"/projects/180/sql_generation/condition$", 200, {"condition": {}})

    result = make_runner().invoke(
        [
            "ai",
            "condition",
            "generate",
            "5",
            "--project",
            "180",
            "--input",
            '{"intent": "rows where status is active"}',
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    posts = [r for r in api.requests if r.method == "POST" and "sql_generation/condition" in r.path]
    assert len(posts) == 1
    assert posts[0].query.get("dataset_id") == ["5"]
    assert posts[0].json_body == {"params": {"intent": "rows where status is active"}}
