"""``dataset rename`` with ``{"unique": true}`` asks the server for a free name.

Real-code: argv through the real handler, service and SDK client, with only the HTTP
socket faked. The fake server behaves as the real one does: a taken name is refused
unless the request carries ``unique=true``, in which case it applies ``name 2``.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.services import factory
from mammoth_cli.testing import make_runner

ServiceFactory = Callable[..., Any]
_PATH = r"/workspaces/4/projects/180/datasets/55$"


def _rename(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory, document: dict[str, Any]
) -> tuple[Any, Any]:
    service, api = real_service(project_id=180)
    unused = iter([service])
    monkeypatch.setattr(
        factory,
        "build_service",
        lambda *a, **k: next(unused, None) or real_service(api=api, project_id=180)[0],
    )

    def patch(request: Any) -> tuple[int, Any]:
        if request.query.get("unique") == ["true"]:
            return 200, {"name": "Gifts 2"}
        return 409, {"error": "a dataset named 'Gifts' already exists"}

    api.on("PATCH", _PATH, handler=patch)
    result = make_runner().invoke(
        ["dataset", "rename", "55", "--project", "180", "--input", json.dumps(document)]
        + ["--output", "json", "--no-input"]
    )
    return result, api


def test_unique_true_renames_to_the_free_name_the_server_picks(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    result, api = _rename(monkeypatch, real_service, {"name": "Gifts", "unique": True})

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["data"]["name"] == "Gifts 2"
    (request,) = [r for r in api.requests if r.method == "PATCH"]
    assert request.query == {"unique": ["true"]}
    assert request.json_body == {"patch": {"op": "replace", "path": "name", "value": "Gifts"}}


def test_unique_false_does_not_ask_for_a_free_name(
    monkeypatch: pytest.MonkeyPatch, real_service: ServiceFactory
) -> None:
    _, api = _rename(monkeypatch, real_service, {"name": "Gifts", "unique": False})

    (request,) = [r for r in api.requests if r.method == "PATCH"]
    assert request.query == {}
