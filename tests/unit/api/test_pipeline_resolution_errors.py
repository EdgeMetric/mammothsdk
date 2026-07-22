"""Dataview-resolution error-classification tests for PipelineAPI.

These tests exercise the *real* resolution code path
(``PipelineAPI.find_dataset_for_dataview`` →
``_find_dataset_for_dataview``) end to end. No business function is mocked:
only the HTTP boundary is faked by mounting a custom ``requests`` transport
adapter on the genuine ``client.session``.

Regression under test: a transient/authorization failure (401/403/429/5xx)
raised while scanning datasets for a dataview must propagate with its correct
classification, instead of being swallowed and misreported as the generic
``ValueError("... not found in any dataset ...")``. A genuine 404 must still
be treated as a real miss.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

import pytest
import requests

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError, MammothAuthError

WORKSPACE_ID = 11
PROJECT_ID = 10
DATASET_ID = 500
DATAVIEW_ID = 1039


def _make_response(
    status_code: int, body: dict[str, Any], request: requests.PreparedRequest
) -> requests.models.Response:
    """Build a real ``requests.Response`` with a JSON body and status code.

    Args:
        status_code: HTTP status code to report.
        body: JSON-serialisable response body.
        request: The prepared request this response answers.

    Returns:
        A populated ``requests.models.Response`` instance.
    """
    response = requests.models.Response()
    response.status_code = status_code
    response._content = json.dumps(body).encode("utf-8")
    response.encoding = "utf-8"
    response.headers["Content-Type"] = "application/json"
    response.url = request.url or ""
    response.request = request
    return response


class _FakeTransport(requests.adapters.HTTPAdapter):
    """A ``requests`` transport adapter that fakes only the HTTP layer.

    The workspace-browse call always succeeds and reports a single project
    holding a single dataset, so resolution proceeds to the dataview lookup.
    The dataview lookup then returns a configurable status code + body, which
    is exactly the response whose classification is under test.
    """

    def __init__(self, dataview_status: int, dataview_body: dict[str, Any]) -> None:
        super().__init__()
        self._dataview_status = dataview_status
        self._dataview_body = dataview_body
        self.dataview_calls = 0

    def send(  # type: ignore[override]
        self, request: requests.PreparedRequest, **kwargs: Any
    ) -> requests.models.Response:
        path = urlparse(request.url or "").path

        # Workspace browse — the first call resolution makes. Return one
        # project with one dataset child so the dataview scan has a target.
        if path.endswith("/browse"):
            body: dict[str, Any] = {
                "resources": [
                    {
                        "id": PROJECT_ID,
                        "children": [{"id": DATASET_ID, "type": "datasource"}],
                    }
                ]
            }
            return _make_response(200, body, request)

        # Dataview lookup — the response under test.
        if "/dataviews/" in path:
            self.dataview_calls += 1
            return _make_response(self._dataview_status, self._dataview_body, request)

        return _make_response(200, {}, request)


def _client_with_transport(transport: _FakeTransport) -> MammothClient:
    """Build a genuine client and mount the fake transport on its session.

    Args:
        transport: The fake HTTP transport adapter to mount.

    Returns:
        A ready-to-use ``MammothClient`` with project context set.
    """
    client = MammothClient(
        api_key="test-key",
        api_secret="test-secret",
        workspace_id=WORKSPACE_ID,
    )
    client.set_project_id(PROJECT_ID)
    client.session.mount("https://", transport)
    client.session.mount("http://", transport)
    return client


@pytest.mark.parametrize("status_code", [403, 500, 429])
def test_non_404_during_resolution_propagates_as_api_error(status_code: int) -> None:
    """A 403/429/5xx during the dataview scan must raise MammothAPIError.

    It must NOT be swallowed into the generic "not found in any dataset"
    ValueError.
    """
    transport = _FakeTransport(status_code, {"detail": "boom"})
    client = _client_with_transport(transport)
    try:
        with pytest.raises(MammothAPIError) as excinfo:
            client.pipeline.find_dataset_for_dataview(DATAVIEW_ID)
        assert excinfo.value.status_code == status_code
        assert not isinstance(excinfo.value, ValueError)
    finally:
        client.close()


def test_401_during_resolution_propagates_as_auth_error() -> None:
    """A 401 during the dataview scan must raise MammothAuthError (401)."""
    transport = _FakeTransport(401, {"detail": "bad creds"})
    client = _client_with_transport(transport)
    try:
        with pytest.raises(MammothAuthError) as excinfo:
            client.pipeline.find_dataset_for_dataview(DATAVIEW_ID)
        assert excinfo.value.status_code == 401
    finally:
        client.close()


def test_genuine_404_still_yields_not_found() -> None:
    """A real 404 (dataview absent) must keep the not-found ValueError path."""
    transport = _FakeTransport(404, {"detail": "Not found"})
    client = _client_with_transport(transport)
    try:
        with pytest.raises(ValueError) as excinfo:
            client.pipeline.find_dataset_for_dataview(DATAVIEW_ID)
        assert "not found in any dataset" in str(excinfo.value)
        # The dataset was actually scanned before concluding "not found".
        assert transport.dataview_calls == 1
    finally:
        client.close()
