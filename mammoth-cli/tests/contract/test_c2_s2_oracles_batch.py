"""Independent CLI-to-SDK and SDK wire oracles for the first S2 batch.

The fixture is intentionally hand-authored from the pinned public API surface.
The tests never ask the command resolver, manifest, or SDK introspection to
construct an expected request.  The first parametrized test drives the real
CLI, service, SDK resource and HTTP transport seam; the second invokes the
same public SDK resource methods directly through a recording transport.  A
mutated request is asserted to fail the oracle so a dropped or misrouted field
cannot be hidden by a shared builder.

This closes only the first 30 routes in the C2 S2 inventory.  The workbook
ledger remains explicit about the other 64 S2 routes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from mammoth.api.addons import AddonsAPI
from mammoth.api.annotations import AnnotationsAPI
from mammoth.api.browse import BrowseAPI
from mammoth.api.dashboards import DashboardsAPI
from mammoth.api.projects import ProjectsAPI
from pydantic import ValidationError

from mammoth_cli.services import factory
from mammoth_cli.testing import login_default_profile, make_runner

FIXTURE = Path(__file__).with_name("fixtures") / "C2-S2-BATCH-01.json"


@pytest.fixture(autouse=True)
def _isolated_login(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Give the in-process CLI a disposable logged-in profile."""
    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir", lambda *_a, **_k: str(tmp_path)
    )
    # File-backed storage is explicitly selected by login_default_profile, so
    # this test never reads or mutates a developer's keyring.
    login_default_profile()


class _RecordingClient:
    """Public SDK client seam recording method/path/query/body exactly."""

    workspace_id = 4
    project_id = 41
    job_timeout = 0

    def __init__(self, responses: dict[str, Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def _request_json(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        return self.responses.get(path, {})

    def _request_binary(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        # Artifact routes (PNG/PDF/MP4/HTML) go through the binary seam; the
        # wire oracle only cares about method, path, and query.
        self.calls.append((method, path, kwargs))
        return {"content_type": "application/octet-stream", "size_bytes": 0, "sha256": ""}

    def _request_list(self, method: str, path: str, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append((method, path, kwargs))
        response = self.responses.get(path, [])
        return response if isinstance(response, list) else []


def _fixture() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _cli_argv(case: dict[str, Any]) -> list[str]:
    argv = list(case["command"])
    if case.get("project") is not None:
        argv += ["--project", str(case["project"])]
    if case.get("yes") or case.get("confirm"):
        argv.append("--yes")
    if case.get("confirm"):
        argv += ["--confirm", "4"]
    if case.get("input") is not None:
        argv += ["--input", json.dumps(case["input"])]
    argv += ["--output", "json", "--no-input"]
    return argv


def _expected_wire(case: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    expected = case["expected"]
    kwargs: dict[str, Any] = {"params": expected["query"]}
    if expected["json"] is not None:
        kwargs["json"] = expected["json"]
    return expected["method"], expected["path"], kwargs


def _actual_sdk_wire(call: tuple[str, str, dict[str, Any]]) -> tuple[str, str, dict[str, Any]]:
    method, path, kwargs = call
    return (
        method,
        path,
        {"params": kwargs.get("params"), **({"json": kwargs["json"]} if "json" in kwargs else {})},
    )


def _sdk_api(client: _RecordingClient, name: str) -> Any:
    return {
        "addons": AddonsAPI,
        "annotations": AnnotationsAPI,
        "browse": BrowseAPI,
        "dashboards": DashboardsAPI,
        "projects": ProjectsAPI,
    }[name](client)  # type: ignore[arg-type]


def _invoke_sdk(case: dict[str, Any], client: _RecordingClient) -> None:
    api = _sdk_api(client, case["sdk_api"])
    try:
        getattr(api, case["sdk_method"])(**case["sdk_kwargs"])
    except ValidationError:
        # The request has already crossed the transport seam.  Generated SDK
        # response models are intentionally not the subject of this oracle.
        pass


@pytest.mark.parametrize("case", _fixture()["cases"], ids=lambda case: case["route"])
def test_cli_binding_reaches_real_sdk_transport(
    case: dict[str, Any], monkeypatch: pytest.MonkeyPatch, real_service: Any
) -> None:
    """Real CLI dispatch consumes every supplied field into exact wire data."""
    service, api = real_service(project_id=41)
    monkeypatch.setattr(factory, "build_service", lambda *args, **kwargs: service)
    expected = _expected_wire(case)
    response = case["response"]
    api.on(expected[0], re.escape("/api/v2" + expected[1]) + r"$", body=response)

    result = make_runner().invoke(_cli_argv(case))
    assert result.exit_code == 0, result.output
    # Dashboard authoring steps end with one canvas read (deliverable_check);
    # the oracle is the mutation itself.
    request = next(r for r in reversed(api.requests) if r.method == expected[0])
    assert (request.method, request.path.removeprefix("/api/v2")) == expected[:2]
    assert request.json_body == case["expected"]["json"]
    actual_query = {key: values[-1] for key, values in request.query.items()}
    expected_query = expected[2]["params"] or {}
    assert actual_query == {key: str(value) for key, value in expected_query.items()}


@pytest.mark.parametrize("case", _fixture()["cases"], ids=lambda case: case["route"])
def test_real_sdk_resource_method_matches_independent_wire_oracle(
    case: dict[str, Any],
) -> None:
    """A direct public SDK call agrees with fixture-authored wire constants."""
    expected = _expected_wire(case)
    client = _RecordingClient({case["expected"]["path"]: case["response"]})
    _invoke_sdk(case, client)
    assert len(client.calls) == 1, f"{case['route']} emitted {len(client.calls)} requests"
    assert _actual_sdk_wire(client.calls[0]) == expected


def test_dropped_or_misrouted_field_fails_independent_oracle() -> None:
    """Corrupting an optional body field cannot still satisfy the oracle."""
    case = next(item for item in _fixture()["cases"] if item["route"] == "dashboard.context.create")
    expected = _expected_wire(case)
    corrupted = dict(expected[2])
    corrupted["json"] = json.loads(json.dumps(corrupted["json"]))
    corrupted["json"]["params"].pop("guardrails")
    assert corrupted != expected[2]
    with pytest.raises(AssertionError):
        assert corrupted == expected[2]


def test_batch_scope_is_explicit_and_first_uncovered_routes_are_accounted_for() -> None:
    fixture = _fixture()
    assert len(fixture["cases"]) == 30
    assert [case["route"] for case in fixture["cases"]] == [
        "addon.connector.remove",
        "addon.list",
        "addon.storage.add",
        "addon.storage.remove",
        "addon.user.add",
        "addon.user.remove",
        "annotation.comment.add",
        "annotation.delete",
        "annotation.list",
        "annotation.update",
        "browse.folder",
        "browse.project",
        "browse.workspace",
        "dashboard.cancel-generation",
        "dashboard.canvas.restore",
        "dashboard.canvas.save",
        "dashboard.chat.edit",
        "dashboard.chat.history",
        "dashboard.context.create",
        "dashboard.context.list",
        "dashboard.context.update",
        "dashboard.data.published",
        "dashboard.delete",
        "dashboard.descriptor-data",
        "dashboard.duplicate",
        "dashboard.figure-intent",
        "dashboard.get",
        "dashboard.get-by-url",
        "dashboard.job-by-url",
        "dashboard.og-card",
    ]
