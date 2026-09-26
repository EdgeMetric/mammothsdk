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
from urllib.parse import parse_qs, urlparse

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

    The project dataset listing always succeeds and reports a single
    dataset, so resolution proceeds to the dataview lookup. The dataview
    lookup then returns a configurable status code + body, which is exactly
    the response whose classification is under test.
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

        # Project dataset listing — the first call resolution makes. Return
        # one dataset so the dataview scan has a target.
        if path.endswith("/datasets"):
            body: dict[str, Any] = {
                "datasets": [{"id": DATASET_ID, "name": "ds"}],
                "limit": 100,
                "offset": 0,
                "next": None,
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


def test_successful_resolution_is_cached_across_calls() -> None:
    """The expensive browse-based scan runs once; repeats hit the cache.

    A dataview belongs to one dataset for its lifetime, so a second resolution
    of the same dataview must not scan again.
    """
    transport = _FakeTransport(200, {"id": DATAVIEW_ID})
    client = _client_with_transport(transport)
    try:
        first = client.pipeline.find_dataset_for_dataview(DATAVIEW_ID)
        calls_after_first = transport.dataview_calls
        second = client.pipeline.find_dataset_for_dataview(DATAVIEW_ID)
        assert first == second == DATASET_ID
        # The first resolution scanned; the second added ZERO dataview calls
        # because it was served from the per-client cache.
        assert calls_after_first >= 1
        assert transport.dataview_calls == calls_after_first
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


def test_wrong_parent_403_is_disambiguated_by_collection_membership() -> None:
    """A tenant's wrong-parent 403 must not hide a view in the next dataset."""

    class TwoDatasetTransport(requests.adapters.HTTPAdapter):
        def send(  # type: ignore[override]
            self, request: requests.PreparedRequest, **kwargs: Any
        ) -> requests.models.Response:
            path = urlparse(request.url or "").path
            if path.endswith("/datasets"):
                body = {
                    "datasets": [{"id": 500, "name": "a"}, {"id": 501, "name": "b"}],
                    "limit": 100,
                    "offset": 0,
                    "next": None,
                }
                return _make_response(200, body, request)
            if path.endswith("/datasets/500/dataviews/1039"):
                return _make_response(403, {"detail": "forbidden"}, request)
            if path.endswith("/datasets/500/dataviews"):
                return _make_response(
                    200,
                    {
                        "dataviews": [{"id": 22}],
                        "limit": 1000,
                        "next": "https://example.test/dataviews?offset=1000",
                    },
                    request,
                )
            if path.endswith("/datasets/501/dataviews/1039"):
                return _make_response(200, {"id": DATAVIEW_ID}, request)
            raise AssertionError(f"Unexpected request: {path}")

    client = _client_with_transport(TwoDatasetTransport())
    try:
        assert client.pipeline.find_dataset_for_dataview(DATAVIEW_ID) == 501
    finally:
        client.close()


def test_a_dataset_beyond_the_first_page_is_still_discovered() -> None:
    """A project with more than one page of datasets must not be truncated.

    Regression (PR25 item A): resolution used to enumerate candidate
    datasets via a single, unpaginated workspace/folder browse call (a
    default page size of 100, with the server's ``next`` continuation never
    followed). A project holding more than 100 datasets silently lost every
    dataset past the first page -- and a freshly created dataset, which
    sorts onto the *last* page, was exactly the one most likely to be
    dropped. That made ``view get VIEW_ID`` (no dataset id) on a fresh, idle
    view deterministically resource_not_found, even though the view plainly
    existed and a scoped ``view get VIEW_ID DATASET_ID`` worked. Enumeration
    must fully paginate ``dataset.list`` instead.
    """
    first_page_ids = list(range(1, 101))

    class PagedDatasetsTransport(requests.adapters.HTTPAdapter):
        def send(  # type: ignore[override]
            self, request: requests.PreparedRequest, **kwargs: Any
        ) -> requests.models.Response:
            path = urlparse(request.url or "").path
            if path.endswith("/datasets"):
                offset = int(parse_qs(urlparse(request.url or "").query).get("offset", ["0"])[0])
                if offset == 0:
                    body = {
                        "datasets": [{"id": i, "name": f"ds{i}"} for i in first_page_ids],
                        "limit": 100,
                        "offset": 0,
                        "next": "https://example.test/datasets?offset=100",
                    }
                else:
                    body = {
                        "datasets": [{"id": DATASET_ID, "name": "target"}],
                        "limit": 100,
                        "offset": 100,
                        "next": None,
                    }
                return _make_response(200, body, request)
            if "/dataviews/" in path:
                dataset_id = int(path.split("/datasets/")[1].split("/")[0])
                if dataset_id == DATASET_ID:
                    return _make_response(200, {"id": DATAVIEW_ID}, request)
                return _make_response(404, {"detail": "not found"}, request)
            raise AssertionError(f"Unexpected request: {path}")

    client = _client_with_transport(PagedDatasetsTransport())
    try:
        assert client.pipeline.find_dataset_for_dataview(DATAVIEW_ID) == DATASET_ID
    finally:
        client.close()
