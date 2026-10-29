"""A failed job poll after an accepted write is an unknown state, never "not started".

The request layer labels a read's failure ``not_started``. A poll of a job the server
already returned is a read too, but the write behind the job was accepted: reporting it as
not started invites a resubmit that duplicates the write.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError

from ._loopback import RecordingServer


class _RefusingJobsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = json.dumps({"detail": "the jobs route is refusing"})
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def client() -> Iterator[MammothClient]:
    server = HTTPServer(("127.0.0.1", 0), _RefusingJobsHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    server.shutdown()


async def test_a_failed_poll_of_one_job_is_outcome_unknown_with_the_job(
    client: MammothClient,
) -> None:
    with pytest.raises(MammothAPIError) as raised:
        await client.jobs.wait_for_job(52618, timeout=5)

    error = raised.value
    assert error.operation_state == "outcome_unknown"
    assert error.phase == "polling"
    assert error.job_handle == 52618
    assert error.details["job_handle"] == 52618
    assert error.details["operation_state"] == "outcome_unknown"


async def test_a_failed_poll_of_several_jobs_names_all_of_them(client: MammothClient) -> None:
    with pytest.raises(MammothAPIError) as raised:
        await client.jobs.wait_for_jobs([52618, 52619], timeout=5)

    error = raised.value
    assert error.operation_state == "outcome_unknown"
    assert error.job_handle == 52618
    assert error.details["job_handles"] == [52618, 52619]


async def test_a_plain_read_of_a_job_keeps_the_request_layers_own_state(
    client: MammothClient,
) -> None:
    # ``get_job`` is the read itself: only a wait for an accepted job re-labels.
    with pytest.raises(MammothAPIError) as raised:
        await client.jobs.get_job(52618)

    assert raised.value.operation_state != "outcome_unknown"


@pytest.fixture(params=[401, 403])
def refused_client(request: pytest.FixtureRequest) -> Iterator[MammothClient]:
    """A client whose job polls the server answers with a refused sign-in."""
    server = RecordingServer()
    server.answers["GET /jobs/52618"] = (request.param, {"detail": "token expired"})
    server.answers["GET /jobs"] = (request.param, {"detail": "token expired"})
    threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    ).start()
    yield MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    server.shutdown()


async def test_a_refused_sign_in_while_polling_is_still_outcome_unknown_and_says_to_sign_in(
    refused_client: MammothClient,
) -> None:
    # The job was accepted, so its outcome is unknown whatever the poll's status; the next
    # step is a new sign-in and then a read of the job, never a resubmit.
    with pytest.raises(MammothAPIError) as raised:
        await refused_client.jobs.wait_for_job(52618, timeout=5)

    error = raised.value
    assert error.status_code in (401, 403)
    assert error.operation_state == "outcome_unknown"
    assert error.phase == "polling"
    assert error.job_handle == 52618
    note = error.details["next_step"]
    assert "52618" in note
    assert "sign in again" in note
    assert "Do not resubmit" in note


async def test_a_refused_sign_in_while_polling_several_jobs_names_the_first(
    refused_client: MammothClient,
) -> None:
    with pytest.raises(MammothAPIError) as raised:
        await refused_client.jobs.wait_for_jobs([52618, 52619], timeout=5)

    error = raised.value
    assert error.operation_state == "outcome_unknown"
    assert error.details["job_handles"] == [52618, 52619]
    assert "52618" in error.details["next_step"]


async def test_a_non_auth_poll_failure_carries_no_sign_in_step(client: MammothClient) -> None:
    with pytest.raises(MammothAPIError) as raised:
        await client.jobs.wait_for_job(52618, timeout=5)

    assert "next_step" not in raised.value.details
