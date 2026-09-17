"""Independent SDK recovery/fault tests for the M4 lifecycle contract."""

from __future__ import annotations

import errno
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests

from mammoth.api.exports import ExportsAPI
from mammoth.api.jobs import JobsAPI
from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError, MammothJobTimeoutError, safe_response_body


class _Response:
    def __init__(
        self,
        status_code: int = 200,
        body: dict[str, object] | None = None,
        chunks: list[bytes] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._body = body or {}
        self._chunks = chunks or []
        self.headers = headers or {}
        self.content = b"{}"
        self.closed = False

    def json(self) -> dict[str, object]:
        return self._body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def iter_content(self, chunk_size: int = 8192):  # noqa: ARG002
        yield from self._chunks

    def close(self) -> None:
        self.closed = True


def _client() -> MammothClient:
    with patch("mammoth.client.requests.Session"):
        client = MammothClient("key", "secret", workspace_id=7)
    return client


def test_safe_body_preserves_business_fields_and_redacts_credentials() -> None:
    body = {
        "token_count": 12,
        "secret_sauce": "recipe",
        "credential_status": "verified",
        "credentials": {"username": "analyst", "password": "hidden"},
        "nested": {"api_secret": "hidden-too", "value": "kept"},
    }

    safe = safe_response_body(body)

    assert safe["token_count"] == 12
    assert safe["secret_sauce"] == "recipe"
    assert safe["credential_status"] == "verified"
    assert safe["credentials"] == "<redacted>"
    assert safe["nested"] == {"api_secret": "<redacted>", "value": "kept"}


@pytest.mark.parametrize("status_code", [403, 409, 429, 503])
def test_http_errors_preserve_safe_recovery_metadata(status_code: int) -> None:
    client = _client()
    response = _Response(
        status_code,
        {"detail": "blocked", "api_secret": "must-not-leak", "job_id": 91},
        headers={"X-Request-ID": "req-91", "Retry-After": "8"},
    )
    client.session.request = MagicMock(return_value=response)

    with pytest.raises(MammothAPIError) as raised:
        client._request("POST", "/datasets", json={"name": "new"})

    error = raised.value
    assert error.status_code == status_code
    assert error.method == "POST"
    assert error.request_id == "req-91"
    assert error.retry_after == "8"
    assert error.job_handle == 91
    assert error.response_body["api_secret"] == "<redacted>"
    assert "must-not-leak" not in str(error)
    assert client.session.request.call_count == 1


def test_read_timeout_is_safe_and_does_not_replay() -> None:
    client = _client()
    client.session.request = MagicMock(side_effect=requests.exceptions.ReadTimeout("secret-value"))

    with pytest.raises(MammothAPIError) as raised:
        client._request("GET", "/datasets/1")

    error = raised.value
    assert error.method == "GET"
    assert error.operation_state == "not_started"
    assert error.phase == "request"
    assert "secret-value" not in str(error)
    assert client.session.request.call_count == 1


def test_lost_write_response_is_outcome_unknown_without_duplicate() -> None:
    client = _client()
    client.session.request = MagicMock(side_effect=requests.exceptions.ReadTimeout())

    with pytest.raises(MammothAPIError) as raised:
        client._request("POST", "/datasets", json={"name": "once"})

    assert raised.value.operation_state == "outcome_unknown"
    assert client.session.request.call_count == 1


def test_job_timeout_retains_last_observed_handle_and_phase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = SimpleNamespace(job_timeout=1)
    jobs = JobsAPI(client)  # type: ignore[arg-type]
    jobs.get_job = MagicMock(return_value={"job": {"id": 44, "status": "processing"}})
    clock = iter([0.0, 0.0, 0.0, 2.0])
    monkeypatch.setattr("mammoth.api.jobs.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("mammoth.api.jobs.time.sleep", lambda _seconds: None)

    with pytest.raises(MammothJobTimeoutError) as raised:
        jobs.wait_for_job(44, timeout=1)

    error = raised.value
    assert error.job_handle == 44
    assert error.operation_state == "running"
    assert error.phase == "polling"
    assert error.details["observed_job"]["status"] == "processing"


def test_job_wait_uses_monotonic_budget_for_request_and_sleep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = SimpleNamespace(job_timeout=1)
    jobs = JobsAPI(client)  # type: ignore[arg-type]
    jobs.get_job = MagicMock(return_value={"job": {"id": 44, "status": "processing"}})
    clock = iter([100.0, 100.0, 100.25, 101.0])
    sleeps: list[float] = []
    monkeypatch.setattr("mammoth.api.jobs.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("mammoth.api.jobs.time.sleep", sleeps.append)

    with pytest.raises(MammothJobTimeoutError):
        jobs.wait_for_job(44, timeout=1, poll_interval=30)

    assert jobs.get_job.call_args.kwargs["timeout"] == 1
    assert sleeps == [0.75]


def test_job_observation_timeout_reaches_transport() -> None:
    client = _client()
    response = _Response(body={"job": {"id": 44, "status": "processing"}})
    client.session.request = MagicMock(return_value=response)

    client.jobs.get_job(44, timeout=0.5)

    assert client.session.request.call_args.kwargs["timeout"] == 0.5


def test_job_observation_rejects_nonpositive_timeout() -> None:
    jobs = JobsAPI(SimpleNamespace(workspace_id=7))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must be positive"):
        jobs.get_job(44, timeout=0)


@pytest.mark.parametrize(
    ("response", "expected_pending_id"),
    [
        ({"jobs": []}, 101),
        ({"jobs": [{"id": 101, "status": "success"}]}, 102),
    ],
)
def test_wait_for_jobs_does_not_treat_empty_or_partial_results_as_completion(
    monkeypatch: pytest.MonkeyPatch, response: dict[str, object], expected_pending_id: int
) -> None:
    client = SimpleNamespace(job_timeout=1)
    jobs = JobsAPI(client)  # type: ignore[arg-type]
    jobs.get_jobs = MagicMock(return_value=response)
    clock = iter([0.0, 0.0, 0.0, 2.0])
    monkeypatch.setattr("mammoth.api.jobs.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("mammoth.api.jobs.time.sleep", lambda _seconds: None)

    with pytest.raises(MammothJobTimeoutError) as raised:
        jobs.wait_for_jobs([101, 102], timeout=1)

    assert raised.value.job_handle == expected_pending_id
    assert jobs.get_jobs.call_count == 1


def test_wait_for_jobs_returns_every_requested_success_in_request_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = SimpleNamespace(job_timeout=1)
    jobs = JobsAPI(client)  # type: ignore[arg-type]
    jobs.get_jobs = MagicMock(
        return_value={
            "jobs": [
                {"id": 102, "status": "success"},
                {"id": 101, "status": "success"},
            ]
        }
    )
    monkeypatch.setattr("mammoth.api.jobs.time.monotonic", lambda: 0.0)

    result = jobs.wait_for_jobs([101, 102], timeout=1)

    assert [job["id"] for job in result["jobs"]] == [101, 102]


@pytest.mark.parametrize(
    "response, protocol_error",
    [
        (
            {"jobs": [{"id": 101, "status": "success"}, {"id": 101, "status": "success"}]},
            "duplicate_job_id",
        ),
        ({"jobs": [{"id": 999, "status": "success"}]}, "unexpected_job_id"),
    ],
)
def test_wait_for_jobs_rejects_duplicate_or_unrequested_server_records(
    response: dict[str, object], protocol_error: str
) -> None:
    client = SimpleNamespace(job_timeout=1)
    jobs = JobsAPI(client)  # type: ignore[arg-type]
    jobs.get_jobs = MagicMock(return_value=response)

    with pytest.raises(MammothAPIError) as raised:
        jobs.wait_for_jobs([101, 102], timeout=1)

    assert raised.value.details["protocol_error"] == protocol_error


def _export_api(session: MagicMock) -> ExportsAPI:
    client = SimpleNamespace(session=session, timeout=5)
    return ExportsAPI(client)  # type: ignore[arg-type]


def test_download_publishes_atomically_and_replaces_complete_file(tmp_path: Path) -> None:
    destination = tmp_path / "result.csv"
    destination.write_bytes(b"old")
    response = _Response(chunks=[b"new", b" content"])
    session = MagicMock()
    session.get.return_value = response

    result = _export_api(session)._download_file("https://download.invalid/file", destination)

    assert result == destination
    assert destination.read_bytes() == b"new content"
    assert list(tmp_path.glob("*.part")) == []
    assert response.closed


def test_partial_download_preserves_destination_and_cleans_temp(tmp_path: Path) -> None:
    destination = tmp_path / "result.csv"
    destination.write_bytes(b"old")

    class BrokenResponse(_Response):
        def iter_content(self, chunk_size: int = 8192):  # noqa: ARG002
            yield b"partial"
            raise requests.exceptions.ConnectionError("broken stream")

    response = BrokenResponse()
    session = MagicMock()
    session.get.return_value = response

    with pytest.raises(MammothAPIError) as raised:
        _export_api(session)._download_file("https://download.invalid/file", destination)

    assert raised.value.method == "GET"
    assert destination.read_bytes() == b"old"
    assert list(tmp_path.glob("*.part")) == []


def test_enospc_preserves_destination_and_cleans_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "result.csv"
    destination.write_bytes(b"old")
    response = _Response(chunks=[b"new"])
    session = MagicMock()
    session.get.return_value = response

    def full_disk(_fd: int) -> None:
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr("mammoth.api.exports.os.fsync", full_disk)
    with pytest.raises(MammothAPIError) as raised:
        _export_api(session)._download_file("https://download.invalid/file", destination)

    assert raised.value.details["errno"] == errno.ENOSPC
    assert destination.read_bytes() == b"old"
    assert list(tmp_path.glob("*.part")) == []


def test_interrupted_download_preserves_destination_and_remote_job_handle(tmp_path: Path) -> None:
    destination = tmp_path / "result.csv"
    destination.write_bytes(b"old")

    class InterruptedResponse(_Response):
        def iter_content(self, chunk_size: int = 8192):  # noqa: ARG002
            yield b"partial"
            raise KeyboardInterrupt

    session = MagicMock()
    session.get.return_value = InterruptedResponse()
    with pytest.raises(MammothAPIError) as raised:
        _export_api(session)._download_file(
            "https://download.invalid/file", destination, job_handle=919
        )

    assert raised.value.details["interrupted"] is True
    assert raised.value.job_handle == 919
    assert raised.value.details["job_handle"] == 919
    assert raised.value.operation_state == "succeeded"
    assert raised.value.details["remote_export_state"] == "succeeded"
    assert raised.value.details["local_artifact_state"] == "interrupted"
    assert "do not recreate" in raised.value.details["recovery_hint"]
    assert destination.read_bytes() == b"old"
    assert list(tmp_path.glob("*.part")) == []


def test_symlink_destination_is_refused_without_touching_target(tmp_path: Path) -> None:
    target = tmp_path / "target.csv"
    target.write_bytes(b"old")
    destination = tmp_path / "result.csv"
    destination.symlink_to(target)
    session = MagicMock()

    with pytest.raises(MammothAPIError) as raised:
        _export_api(session)._download_file("https://download.invalid/file", destination)

    assert raised.value.details["errno"] == errno.ELOOP
    assert target.read_bytes() == b"old"
    assert destination.is_symlink()
    assert session.get.call_count == 0


def test_local_save_failure_marks_remote_export_succeeded_when_handle_known(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "result.csv"
    session = MagicMock()
    session.get.return_value = _Response(chunks=[b"new"])

    def full_disk(_fd: int) -> None:
        raise OSError(errno.ENOSPC, "full")

    monkeypatch.setattr("mammoth.api.exports.os.fsync", full_disk)

    with pytest.raises(MammothAPIError) as raised:
        _export_api(session)._download_file(
            "https://download.invalid/file", destination, job_handle=919
        )

    assert raised.value.operation_state == "succeeded"
    assert raised.value.details["remote_export_state"] == "succeeded"
    assert raised.value.details["local_artifact_state"] == "failed"
