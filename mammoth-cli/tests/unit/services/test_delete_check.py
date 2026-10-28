"""The shared table of gone codes and the 403 rule, on plain data (no service, no fakes)."""

from __future__ import annotations

from typing import Any

import pytest
from mammoth.exceptions import MammothAPIError

from mammoth_cli.errors.envelope import EXIT_API, EXIT_AUTH, EXIT_NOT_FOUND, CliError
from mammoth_cli.services.delete_check import GONE_BACKEND_CODES, _is_gone, _still_there
from mammoth_cli.services.mapping import map_sdk_exception


def _forbidden() -> CliError:
    return CliError(
        code="authorization_required",
        message="denied",
        exit_status=EXIT_AUTH,
        details={"status_code": 403},
    )


def test_the_table_covers_automation_and_dashboard_codes() -> None:
    assert GONE_BACKEND_CODES["4AUTO005"][0] == "automation"
    assert GONE_BACKEND_CODES["4DASH001"][0] == "dashboard"
    assert GONE_BACKEND_CODES["4DSET001"][0] == "dataset"


@pytest.mark.parametrize("backend_code", sorted(GONE_BACKEND_CODES))
def test_a_gone_backend_code_reads_back_as_deleted(backend_code: str) -> None:
    error = CliError(
        code="api_error", message="x", exit_status=EXIT_API, details={"backend_code": backend_code}
    )
    assert _is_gone(error)


def test_a_403_is_gone_only_when_the_caller_vouches_for_it() -> None:
    assert _is_gone(_forbidden(), forbidden_means_gone=True)
    assert not _is_gone(_forbidden())
    assert not _is_gone(_forbidden(), forbidden_means_gone=False)


def test_the_generic_permission_code_follows_the_same_rule() -> None:
    error = CliError(
        code="permission_denied",
        message="no",
        exit_status=EXIT_AUTH,
        details={"backend_code": "4PERM002"},
    )
    assert _is_gone(error, forbidden_means_gone=True)
    assert not _is_gone(error)


def test_a_not_found_error_maps_to_the_same_code_the_read_back_accepts() -> None:
    error = map_sdk_exception(
        MammothAPIError(
            "Bad Request",
            status_code=400,
            method="GET",
            operation_state="failed",
            response_body={"error_code": "4AUTO005", "message": "No automation found"},
        )
    )
    assert error.code == "resource_not_found" and error.exit_status == EXIT_NOT_FOUND
    assert _is_gone(error)


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
    assert not _still_there(record, 7)


def test_a_live_record_is_still_there() -> None:
    assert _still_there({"id": 7, "status": "active"}, 7)
