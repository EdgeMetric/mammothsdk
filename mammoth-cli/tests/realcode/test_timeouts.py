"""Real-code tests that the timeout options reach the SDK client.

Finding #8 was that ``--job-timeout`` and ``--pipeline-timeout`` were parsed
but never consumed: the SDK service ignored them, so job and pipeline waits
always used the client defaults. The service now forwards them to the client
(which reads ``job_timeout`` / ``pipeline_timeout`` when waiting), and the
session wires the invocation values into the factory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.runtime import session
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services import factory
from mammoth_cli.services.sdk_service import SdkMammothService
from mammoth_cli.testing import login_default_profile

_AUTH = ResolvedAuth(
    api_key="k", api_secret="s", workspace_id=4, base_url="https://fake.mammoth.test/api/v2"
)


def test_service_forwards_timeouts_to_the_real_client() -> None:
    """The SDK client is built with the job/pipeline timeouts the service got."""
    service = SdkMammothService(_AUTH, timeout=5, job_timeout=11, pipeline_timeout=22)
    try:
        assert service._client.timeout == 5
        assert service._client.job_timeout == 11
        assert service._client.pipeline_timeout == 22
    finally:
        service.close()


def test_service_defaults_leave_client_defaults_intact() -> None:
    """Omitting the timeouts leaves the SDK client's own defaults in place."""
    default = SdkMammothService(_AUTH)
    try:
        assert default._client.job_timeout > 0
        assert default._client.pipeline_timeout > 0
    finally:
        default.close()


def test_open_service_wires_invocation_timeouts(
    isolated_cli_config: Path, monkeypatch: Any
) -> None:
    """open_service passes the invocation's timeout family into the factory."""
    captured: dict[str, Any] = {}

    class _Probe:
        def close(self) -> None:
            pass

    def _fake_build_service(auth: ResolvedAuth, **kwargs: Any) -> _Probe:
        captured.update(kwargs)
        return _Probe()

    monkeypatch.setattr(factory, "build_service", _fake_build_service)
    login_default_profile()

    invocation = Invocation(
        command_id="project.list", timeout=5, job_timeout=11, pipeline_timeout=22
    )
    with session.open_service(invocation):
        pass

    assert captured["timeout"] == 5
    assert captured["job_timeout"] == 11
    assert captured["pipeline_timeout"] == 22
