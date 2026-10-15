"""One command run opens one service per credential set, not one per handler and read-back."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.runtime import session
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.shared import shared_services


class _Service:
    def __init__(self) -> None:
        self.closed = False
        self.bound: list[tuple[float | None, float | None]] = []

    def bind_timeouts(self, *, job_timeout: float | None, pipeline_timeout: float | None) -> None:
        self.bound.append((job_timeout, pipeline_timeout))

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def built(monkeypatch: pytest.MonkeyPatch) -> list[_Service]:
    services: list[_Service] = []
    auth = ResolvedAuth(
        api_key=None, api_secret=None, workspace_id=4, base_url="https://x.test", api_token="t"
    )

    def build(_auth: Any, **_kwargs: Any) -> _Service:
        services.append(_Service())
        return services[-1]

    monkeypatch.setattr(session, "resolve_auth", lambda _inv: auth)
    monkeypatch.setattr(session, "resolved_project", lambda _inv: 3633)
    monkeypatch.setattr(session.factory, "build_service", build)
    return services


def _inv(command_id: str = "view.transform.filter", **overrides: Any) -> Invocation:
    return Invocation(command_id=command_id, output="json", profile="default", **overrides)


def test_without_a_scope_every_open_builds_and_closes_its_own(built: list[_Service]) -> None:
    for _ in range(3):
        with session.open_service(_inv()):
            pass
    assert len(built) == 3
    assert all(service.closed for service in built)


def test_inside_a_scope_the_write_and_its_read_backs_share_one_service(
    built: list[_Service],
) -> None:
    with shared_services():
        with session.open_service(_inv()) as (first, _):
            pass
        assert not built[0].closed  # still warm for the verify and state reads
        with session.open_service(_inv("view.data.get")) as (second, _):
            pass
        with session.open_service(_inv("view.get")) as (third, _):
            pass
    assert len(built) == 1
    assert first is second is third
    assert built[0].closed


def test_a_shared_service_takes_the_next_opener_s_job_wait(built: list[_Service]) -> None:
    with shared_services():
        with session.open_service(_inv(job_timeout=300)):
            pass
        with session.open_service(_inv("view.data.get", job_timeout=45)):
            pass
        with session.open_service(_inv("view.data.get")):
            pass
    # Built with the first opener's wait; each later opener rebinds its own (None: the default).
    assert built[0].bound == [(45, None), (None, None)]


def test_a_dry_run_gate_is_never_shared_with_a_real_run(built: list[_Service]) -> None:
    with shared_services():
        with session.open_service(_inv(dry_run=True)):
            pass
        with session.open_service(_inv()):
            pass
    assert len(built) == 2


def test_the_scope_closes_its_services_when_the_command_fails(built: list[_Service]) -> None:
    with pytest.raises(RuntimeError), shared_services():
        with session.open_service(_inv()):
            pass
        raise RuntimeError("boom")
    assert built[0].closed
