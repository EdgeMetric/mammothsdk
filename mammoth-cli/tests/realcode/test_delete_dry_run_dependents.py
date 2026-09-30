"""A delete's dry run lists what depends on the resource, or says it could not look."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]

_GRAPH = {"55": {"dependencies": [], "dependents": [{"id": "77", "type": "view"}]}}


def _dry_run(monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, deps: Any) -> Any:
    service, api = real_service(project_id=180)
    monkeypatch.setattr(factory, "build_service", lambda *a, **k: service)
    api.on("GET", r"/datasets/55$", body={"dataset": {"id": 55, "name": "orders"}})
    api.on("GET", r"/resource-dependencies", **deps)
    result = make_runner().invoke(
        ["dataset", "delete", "55", "--project", "180", "--dry-run", "--output", "json"]
    )
    assert result.exit_code == 0, result.output
    assert not [r for r in api.requests if r.method == "DELETE"]
    return json.loads(result.output)["data"], api


def test_dataset_delete_dry_run_lists_dependents(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    data, api = _dry_run(monkeypatch, real_service, {"body": _GRAPH})
    assert data["targets"][0]["name"] == "orders"
    assert data["dependents"]["checked"] is True
    assert data["dependents"]["dependencies"] == _GRAPH
    lookup = [r for r in api.requests if "resource-dependencies" in r.path][0]
    assert lookup.query["resource_ids"] == ["55"]


def test_a_failed_dependents_lookup_is_reported_not_omitted(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    data, _ = _dry_run(monkeypatch, real_service, {"status": 500, "body": {"message": "boom"}})
    assert data["dependents"]["checked"] is False
    assert data["dependents"]["error"]
