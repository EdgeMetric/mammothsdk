"""A 404 after a view -> dataset answer was read from disk drops it and retries once."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from mammoth.exceptions import MammothAPIError

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.sdk_service import SdkMammothService

AUTH = ResolvedAuth(
    api_key="key",
    api_secret="secret",
    workspace_id=4,
    base_url="https://unused.invalid/api/v2",
)


READ = "mammoth.api.dataviews.DataviewsAPI.get"
WRITE = "mammoth.api.pipeline.PipelineAPI.add_task"
POST_READ = "mammoth.api.activity_logs.ActivityLogsAPI.export"  # read-class, but a POST


class _Pipeline:
    def __init__(self, stored: set[int]) -> None:
        self.stored = stored
        self.forgotten: list[int] = []

    def stored_dataview_resolutions(self) -> frozenset[int]:
        return frozenset(self.stored)

    def forget_dataview_dataset(self, dataview_id: int) -> None:
        self.forgotten.append(dataview_id)
        self.stored.discard(dataview_id)


@pytest.fixture
def service() -> Iterator[SdkMammothService]:
    instance = SdkMammothService(AUTH)
    try:
        yield instance
    finally:
        instance.close()


def _wire(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch, outcomes: list[Any]
) -> list[int]:
    attempts: list[int] = []

    async def method(**_: Any) -> str:
        attempts.append(1)
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return str(outcome)

    monkeypatch.setattr(service, "_prepare_call", lambda symbol, kwargs: (method, kwargs))
    return attempts


def test_404_after_a_stored_answer_retries_once(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    pipeline = _Pipeline({290})
    service._client.__dict__["pipeline"] = pipeline
    attempts = _wire(service, monkeypatch, [MammothAPIError("gone", status_code=404), "ok"])
    assert service.call(READ) == "ok"
    assert len(attempts) == 2
    assert pipeline.forgotten == [290]


def test_404_without_a_stored_answer_is_not_retried(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    pipeline = _Pipeline(set())
    service._client.__dict__["pipeline"] = pipeline
    attempts = _wire(service, monkeypatch, [MammothAPIError("gone", status_code=404), "ok"])
    with pytest.raises(CliError) as excinfo:
        service.call(READ)
    assert excinfo.value.exit_status == 5
    assert len(attempts) == 1


def test_second_404_surfaces_after_one_retry(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    pipeline = _Pipeline({290})
    service._client.__dict__["pipeline"] = pipeline
    attempts = _wire(
        service,
        monkeypatch,
        [MammothAPIError("gone", status_code=404), MammothAPIError("gone", status_code=404)],
    )
    with pytest.raises(CliError) as excinfo:
        service.call(READ)
    assert excinfo.value.exit_status == 5
    assert len(attempts) == 2


def test_other_errors_are_not_retried(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    pipeline = _Pipeline({290})
    service._client.__dict__["pipeline"] = pipeline
    attempts = _wire(service, monkeypatch, [MammothAPIError("boom", status_code=500), "ok"])
    with pytest.raises(CliError):
        service.call(READ)
    assert len(attempts) == 1
    assert pipeline.forgotten == []


def test_a_write_is_never_replayed_after_a_404(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """add_task may have run before a later step 404ed: sending it again could add two."""
    pipeline = _Pipeline({290})
    service._client.__dict__["pipeline"] = pipeline
    attempts = _wire(service, monkeypatch, [MammothAPIError("gone", status_code=404), "ok"])
    with pytest.raises(CliError) as excinfo:
        service.call(WRITE)
    assert excinfo.value.exit_status == 5
    assert len(attempts) == 1
    # The stale entry is still dropped, so the next command asks the server.
    assert pipeline.forgotten == [290]


def test_an_older_sdk_without_the_store_just_raises_the_404(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """mammoth-io 0.8.46 has no stored_dataview_resolutions(): no AttributeError, no retry."""

    class OldPipeline:
        pass

    service._client.__dict__["pipeline"] = OldPipeline()
    attempts = _wire(service, monkeypatch, [MammothAPIError("gone", status_code=404), "ok"])
    with pytest.raises(CliError) as excinfo:
        service.call(READ)
    assert excinfo.value.exit_status == 5
    assert len(attempts) == 1


def test_a_read_class_post_is_never_replayed_after_a_404(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    """activity export is read-class but POSTs and may start a job: not sent twice."""
    pipeline = _Pipeline({290})
    service._client.__dict__["pipeline"] = pipeline
    attempts = _wire(service, monkeypatch, [MammothAPIError("gone", status_code=404), "ok"])
    with pytest.raises(CliError):
        service.call(POST_READ)
    assert len(attempts) == 1
    assert pipeline.forgotten == [290]


@pytest.mark.parametrize(
    "symbol, expected",
    [
        ("mammoth.client.ViewsResource.get", True),
        ("mammoth.api.pipeline.PipelineAPI.list_tasks", True),
        ("mammoth.api.dataviews.DataviewsAPI.get", True),
        (POST_READ, False),
        ("mammoth.api.dataviews.DataviewsAPI.query_data", False),
        ("mammoth.api.pipeline.PipelineAPI.add_task", False),
        ("mammoth.api.nowhere.Made.up", False),
    ],
)
def test_only_get_reads_are_replayable(symbol: str, expected: bool) -> None:
    from mammoth_cli.runtime import dryrun

    assert dryrun.is_get_symbol(symbol) is expected
