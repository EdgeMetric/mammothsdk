"""``ensure_deleted`` reads a deleted id back as gone, by the one shared table of codes."""

from __future__ import annotations

from typing import Any

import pytest
from mammoth.exceptions import MammothAPIError

from mammoth_cli.errors.envelope import EXIT_API, EXIT_AUTH, EXIT_NOT_FOUND, CliError
from mammoth_cli.services import delete_check
from mammoth_cli.services.delete_check import GONE_BACKEND_CODES, ensure_deleted
from mammoth_cli.services.mapping import map_sdk_exception
from mammoth_cli.services.testing import FakeMammothService

_GET = "x.get"


def _delete(service: FakeMammothService, noun: str = "automation") -> None:
    ensure_deleted(
        service,
        noun=noun,
        resource_id=7,
        read_symbol=_GET,
        read_kwargs={"id": 7},
        responses=(),
    )


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(delete_check.time, "sleep", lambda _s: None)


def test_the_table_covers_automation_and_dashboard_codes() -> None:
    assert GONE_BACKEND_CODES["4AUTO005"][0] == "automation"
    assert GONE_BACKEND_CODES["4DASH001"][0] == "dashboard"
    assert GONE_BACKEND_CODES["4DSET001"][0] == "dataset"


@pytest.mark.parametrize("backend_code", sorted(GONE_BACKEND_CODES))
def test_a_gone_backend_code_reads_back_as_deleted(backend_code: str) -> None:
    service = FakeMammothService()
    service.responses[_GET] = CliError(
        code="api_error",
        message="x",
        exit_status=EXIT_API,
        details={"backend_code": backend_code},
    )
    _delete(service)


def test_a_403_on_a_deleted_dashboard_reads_back_as_deleted() -> None:
    service = FakeMammothService()
    service.responses[_GET] = CliError(
        code="authorization_required",
        message="denied",
        exit_status=EXIT_AUTH,
        details={"status_code": 403},
    )
    _delete(service, noun="dashboard")


def test_a_403_on_another_resource_is_still_an_error() -> None:
    service = FakeMammothService()
    service.responses[_GET] = CliError(
        code="authorization_required",
        message="denied",
        exit_status=EXIT_AUTH,
        details={"status_code": 403},
    )
    with pytest.raises(CliError) as excinfo:
        _delete(service, noun="automation")
    assert excinfo.value.code == "authorization_required"


def test_a_not_found_error_maps_to_the_same_code_the_read_back_accepts() -> None:
    error = map_sdk_exception(
        _api_error({"error_code": "4AUTO005", "message": "No automation found"})
    )
    assert error.code == "resource_not_found" and error.exit_status == EXIT_NOT_FOUND
    service = FakeMammothService()
    service.responses[_GET] = error
    _delete(service)


@pytest.mark.parametrize(
    "record",
    [
        {"id": 7, "status": "trashed"},
        {"id": 7, "is_trashed": True},
        {"automation": {"id": 7, "deleted": True}},
        {},
    ],
)
def test_a_trashed_or_empty_read_counts_as_deleted(record: dict[str, Any]) -> None:
    service = FakeMammothService()
    service.responses[_GET] = record
    _delete(service)


def test_a_live_record_after_the_delete_is_an_error() -> None:
    service = FakeMammothService()
    service.responses[_GET] = {"id": 7, "status": "active"}
    with pytest.raises(CliError) as excinfo:
        _delete(service)
    assert excinfo.value.code == "delete_not_applied"


def _api_error(body: dict[str, Any]) -> Any:
    return MammothAPIError(
        "Bad Request",
        status_code=400,
        method="GET",
        operation_state="failed",
        response_body=body,
    )
