"""``View.build_only``: build and validate a transform, send nothing.

Real client and View; the HTTP boundary is a recording transport adapter.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
import requests

from mammoth.client import MammothClient
from mammoth.view import View

_DATA = {
    "id": 7,
    "name": "tips",
    "metadata": [
        {"display_name": "tip", "internal_name": "column_1", "type": "NUMERIC"},
        {"display_name": "bill", "internal_name": "column_2", "type": "NUMERIC"},
    ],
}


class _Recorder(requests.adapters.HTTPAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[str] = []

    def send(  # type: ignore[override]
        self, request: requests.PreparedRequest, **kwargs: Any
    ) -> requests.models.Response:
        self.requests.append(f"{request.method} {request.url}")
        response = requests.models.Response()
        response.status_code = 200
        response._content = json.dumps({}).encode()
        response.headers["Content-Type"] = "application/json"
        response.url = request.url or ""
        response.request = request
        return response


@pytest.fixture
def view_and_wire() -> tuple[View, _Recorder]:
    client = MammothClient(api_key="k", api_secret="s", workspace_id=1)
    client.set_project_id(2)
    wire = _Recorder()
    client.session.mount("https://", wire)
    client.session.mount("http://", wire)
    return View(client, _DATA, 9), wire


def test_build_only_returns_the_built_task_and_sends_nothing(
    view_and_wire: tuple[View, _Recorder],
) -> None:
    view, wire = view_and_wire
    with view.build_only():
        result = view.math('"tip" * 2', new_column="out")
    assert result["status"] == "validated"
    assert "MATH" in json.dumps(result["task_spec"])
    assert wire.requests == []


def test_build_only_still_rejects_what_a_real_run_rejects(
    view_and_wire: tuple[View, _Recorder],
) -> None:
    view, wire = view_and_wire
    with view.build_only(), pytest.raises(ValueError, match="Unrecognized token"):
        view.math('"nope" * 2', new_column="out")
    assert wire.requests == []


def test_an_inner_block_leaves_the_outer_one_in_force(
    view_and_wire: tuple[View, _Recorder],
) -> None:
    view, wire = view_and_wire
    with view.build_only():
        with view.build_only():
            pass
        assert view.math('"tip" * 2', new_column="out")["status"] == "validated"
    assert wire.requests == []
