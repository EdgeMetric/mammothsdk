"""Construct the production service for one resolved authentication context.

Commands call :func:`build_service` instead of constructing
:class:`~mammoth_cli.services.sdk_service.SdkMammothService` directly. Tests
monkeypatch this single seam to substitute
:class:`~mammoth_cli.services.testing.FakeMammothService` so no network is
touched.
"""

from __future__ import annotations

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.services.protocol import MammothService
from mammoth_cli.services.sdk_service import SdkMammothService


def build_service(
    auth: ResolvedAuth,
    *,
    timeout: float | None = None,
    job_timeout: float | None = None,
    pipeline_timeout: float | None = None,
    project_id: int | None = None,
    progress: bool = False,
) -> MammothService:
    """Build the production SDK-backed service for ``auth``.

    Args:
        auth: Resolved credentials, workspace id, and base url.
        timeout: Optional per-request timeout override, in seconds.
        job_timeout: Optional job-wait timeout override, in seconds.
        pipeline_timeout: Optional pipeline-readiness timeout override, in
            seconds.
        project_id: Active project id to bind on the client for SDK methods
            that read project context implicitly.
        progress: Whether the service shows a stderr spinner during calls.

    Returns:
        A :class:`MammothService` implementation backed by ``MammothClient``.
    """
    return SdkMammothService(
        auth,
        timeout=timeout,
        job_timeout=job_timeout,
        pipeline_timeout=pipeline_timeout,
        project_id=project_id,
        progress=progress,
    )
