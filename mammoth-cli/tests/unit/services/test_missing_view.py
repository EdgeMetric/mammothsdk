"""A missing view says whether it is in the trash (mammothsdk#381 item 10)."""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import CODE_RESOURCE_NOT_FOUND, EXIT_NOT_FOUND, CliError
from mammoth_cli.services.missing_view import TRASH_LIST_SYMBOL, explain_missing_view

_NOT_FOUND = CliError(
    code=CODE_RESOURCE_NOT_FOUND,
    message="The requested Mammoth resource does not exist.",
    exit_status=EXIT_NOT_FOUND,
)
_TRASHED = {
    "id": 151091,
    "type": "dataview",
    "name": "F - Deposits",
    "dataset_id": 144863,
    "trashed_at": "2026-10-30T09:12:00",
    "trashed_by": {"id": 13, "name": "Ana"},
    "days_until_purge": 26,
}


def _trash(*items: dict[str, Any]) -> Any:
    calls: list[dict[str, Any]] = []

    def call(symbol: str, **kwargs: Any) -> Any:
        assert symbol == TRASH_LIST_SYMBOL
        calls.append(kwargs)
        return {"items": list(items)}

    call.calls = calls  # type: ignore[attr-defined]
    return call


def test_a_trashed_view_says_when_and_how_to_restore_it() -> None:
    call = _trash({"id": 9, "type": "dataview"}, _TRASHED)
    error = explain_missing_view(call, 4270, 151091, _NOT_FOUND)
    assert error.message == (
        "View 151091 (F - Deposits) is in project 4270's trash: trashed 2026-10-30 by Ana; "
        "it is deleted for good in 26 days."
    )
    assert error.recovery_commands == ["mammoth view restore 151091 144863 --project 4270"]
    assert error.details["in_trash"] is True
    assert call.calls == [{"project_id": 4270, "type": "dataview", "limit": 100, "offset": 0}]


def test_a_view_in_neither_place_says_it_is_gone_for_good() -> None:
    error = explain_missing_view(_trash(), 4270, 151091, _NOT_FOUND)
    assert "nor in its trash: it was deleted for good" in error.message
    assert error.details["in_trash"] is False


def test_an_unreadable_trash_keeps_the_original_error() -> None:
    def call(symbol: str, **kwargs: Any) -> Any:
        raise CliError(code="permission_denied", message="no", exit_status=1)

    assert explain_missing_view(call, 4270, 151091, _NOT_FOUND) is _NOT_FOUND


def test_other_errors_are_not_touched() -> None:
    other = CliError(code="invalid_argument", message="bad", exit_status=2)
    assert explain_missing_view(_trash(_TRASHED), 4270, 151091, other) is other
