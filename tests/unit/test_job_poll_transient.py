"""One 502 on a job poll is polled again, not reported as the job's outcome (issue #368)."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError


def _client() -> MammothClient:
    return MammothClient("key", "secret", workspace_id=1)


async def test_a_transient_poll_failure_is_polled_again(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    answers: list[Any] = [
        MammothAPIError("bad gateway", status_code=502),
        {"job": {"id": 7, "status": "success"}},
    ]

    async def get_job(job_id: int, timeout: float | None = None) -> Any:
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(client.jobs, "get_job", get_job)
    job = await client.jobs.wait_for_job(7, timeout=30, poll_interval=0.01)
    assert job["status"] == "success"


async def test_a_refused_poll_still_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()

    async def get_job(job_id: int, timeout: float | None = None) -> Any:
        raise MammothAPIError("forbidden", status_code=403)

    monkeypatch.setattr(client.jobs, "get_job", get_job)
    with pytest.raises(MammothAPIError) as raised:
        await client.jobs.wait_for_job(7, timeout=30, poll_interval=0.01)
    assert raised.value.job_handle == 7


async def test_a_poll_that_keeps_failing_raises_at_the_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()

    async def get_job(job_id: int, timeout: float | None = None) -> Any:
        raise MammothAPIError("bad gateway", status_code=502)

    monkeypatch.setattr(client.jobs, "get_job", get_job)
    with pytest.raises(MammothAPIError) as raised:
        await client.jobs.wait_for_job(7, timeout=0.3, poll_interval=0.01)
    assert raised.value.operation_state == "outcome_unknown"
