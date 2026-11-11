"""The Workflows API: list runnable workflows, start a run, read its status and result.

The SDK calls run against a real loopback HTTP server that records every request; the callback
signature check is pure and runs against a fixed clock.
"""

from __future__ import annotations

import hashlib
import hmac

import pytest

import mammoth
from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError, MammothValidationError
from mammoth.workflow_callbacks import callback_problem, sign_callback, verify_callback

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

WF = "/workspaces/1/projects/25654/workflows"
RUN = "3f2b8c1e-6a4d-4e9b-9a51-0c7d2e5f8a10"


async def test_list_runnable_reads_the_runnable_route(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    listed = [{"workflow_id": 42, "name": "Weekly", "running": False, "last_run": None}]
    server.answers[f"GET {WF}/runnable"] = listed
    assert await client.workflows.list_runnable() == listed
    assert server.requests[-1]["path"] == f"{WF}/runnable"


async def test_start_run_posts_an_empty_body_without_a_callback(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    started = {"run_id": RUN, "already_running": False, "callback_secret": None}
    server.answers[f"POST {WF}/42/start"] = (202, started)
    assert await client.workflows.start_run(42) == started
    assert server.requests[-1] == {
        "method": "POST",
        "path": f"{WF}/42/start",
        "query": {},
        "body": {},
    }


async def test_start_run_sends_the_callback_url_and_honours_the_project(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.workflows.start_run(42, callback_url="https://hooks.example.com/r", project_id=7)
    assert server.requests[-1]["path"] == "/workspaces/1/projects/7/workflows/42/start"
    assert server.requests[-1]["body"] == {"callback_url": "https://hooks.example.com/r"}


async def test_start_run_surfaces_the_rate_limit(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"POST {WF}/42/start"] = (429, {"detail": "Too many starts"})
    with pytest.raises(MammothAPIError) as caught:
        await client.workflows.start_run(42)
    assert caught.value.status_code == 429


async def test_run_status_and_result_read_the_run_routes(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {WF}/42/runs/{RUN}"] = {"run_id": RUN, "status": "running"}
    server.answers[f"GET {WF}/42/runs/{RUN}/result"] = {"run_id": RUN, "outputs": []}
    assert (await client.workflows.run_status(42, RUN))["status"] == "running"
    assert (await client.workflows.run_result(42, RUN))["outputs"] == []
    assert [r["path"] for r in server.requests] == [
        f"{WF}/42/runs/{RUN}",
        f"{WF}/42/runs/{RUN}/result",
    ]


@pytest.mark.parametrize(
    ("method", "args", "kwargs"),
    [
        ("list_runnable", (), {"project_id": 0}),
        ("start_run", (0,), {}),
        ("start_run", (42,), {"callback_url": "  "}),
        ("run_status", (42, ""), {}),
        ("run_status", (42, "a/b"), {}),
        ("run_status", (0, RUN), {}),
        ("run_result", (42, " "), {}),
        ("run_result", (42, RUN), {"project_id": -3}),
    ],
)
async def test_bad_ids_are_refused_before_any_request(
    server: RecordingServer,  # noqa: F811
    client: MammothClient,  # noqa: F811
    method: str,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(MammothValidationError):
        await getattr(client.workflows, method)(*args, **kwargs)
    assert server.requests == []


# --- verify_callback ------------------------------------------------------------------------

SECRET = "9c1e" * 16
BODY = b'{"event":"workflow_run.finished","run_id":"r1","status":"success"}'
NOW = 1_731_230_000


def _header(timestamp: int = NOW, body: bytes = BODY, secret: str = SECRET) -> str:
    """The header as the backend builds it (callback.signature): HMAC of "<t>.<body>"."""
    mac = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256)
    return f"t={timestamp},v1={mac.hexdigest()}"


def test_sign_callback_matches_the_backend_format() -> None:
    assert sign_callback(SECRET, NOW, BODY) == _header()
    assert sign_callback(SECRET, NOW, BODY.decode()) == _header()


def test_a_valid_signature_verifies() -> None:
    assert verify_callback(SECRET, _header(), BODY, now=NOW) is True
    assert verify_callback(SECRET, _header(), BODY.decode(), now=NOW + 300) is True
    assert verify_callback(SECRET, " " + _header().replace(",", " , "), BODY, now=NOW) is True


def test_any_matching_v1_is_accepted() -> None:
    header = f"t={NOW},v1={'0' * 64},{_header().split(',')[1]}"
    assert verify_callback(SECRET, header, BODY, now=NOW) is True


@pytest.mark.parametrize(
    ("header", "body", "secret", "now", "why"),
    [
        (_header(), BODY + b" ", SECRET, NOW, "does not match"),
        (_header(), BODY, "other", NOW, "does not match"),
        (_header(), BODY, SECRET, NOW + 301, "seconds from now"),
        (_header(), BODY, SECRET, NOW - 301, "seconds from now"),
        (_header().split(",")[1], BODY, SECRET, NOW, "no t="),
        (f"t=abc,{_header().split(',')[1]}", BODY, SECRET, NOW, "no t="),
        (f"t={NOW}", BODY, SECRET, NOW, "no v1"),
        ("", BODY, SECRET, NOW, "no t="),
        (_header(), BODY, "", NOW, "secret is empty"),
    ],
)
def test_a_bad_signature_is_refused_and_says_why(
    header: str, body: bytes, secret: str, now: int, why: str
) -> None:
    assert verify_callback(secret, header, body, now=now) is False
    assert why in (callback_problem(secret, header, body, now=now) or "")


def test_tolerance_none_skips_the_age_check_but_not_the_signature() -> None:
    assert verify_callback(SECRET, _header(), BODY, tolerance=None, now=NOW + 10**6)
    assert not verify_callback(SECRET, _header(), BODY + b"x", tolerance=None, now=NOW)


def test_verify_callback_is_exported_from_the_package() -> None:
    assert mammoth.verify_callback is verify_callback
    assert "verify_callback" in mammoth.__all__
