"""Settle an ``outcome_unknown`` write of an idempotent command by reading the resource once.

A write whose response was lost (a gateway 5xx after the server committed) is reported as
``outcome_unknown``. For a command that is safe to ask twice about -- trashing a dataset,
discarding a draft -- the answer is one read away: if the change is in place the command
succeeded, whatever the reply said.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mammoth_cli.errors.envelope import CODE_OUTCOME_UNKNOWN, CliError
from mammoth_cli.services.delete_check import _is_gone, _still_there


def trashed_or_gone(record: Any, resource_id: int) -> bool:
    """Whether a read of the resource shows it in the trash (a trashed record is not live)."""
    return not _still_there(record, resource_id)


def settle_unknown_outcome(
    service: Any,
    write: Callable[[], Any],
    *,
    noun: str,
    resource_id: int,
    read_symbol: str,
    read_kwargs: dict[str, Any],
    applied: Callable[[Any], bool],
    done_status: str,
) -> Any:
    """Run ``write``; on ``outcome_unknown`` read the resource once and report what it shows.

    Args:
        service: The open service.
        write: The write call; its result is returned when it succeeds.
        noun: ``dataset`` or ``connector draft``, for the note.
        resource_id: The resource's id.
        read_symbol: The SDK ``get`` that reads it.
        read_kwargs: Its arguments.
        applied: Whether the record the read returns shows the change in place. A read that
            answers "gone" counts as the change in place too (a discarded draft is gone;
            a trashed dataset may read as gone).
        done_status: The ``status`` word of the confirmed result (``trashed``).

    Returns:
        ``write``'s result, or a confirmed result when the read shows the change in place.

    Raises:
        CliError: The original ``outcome_unknown`` error when the read shows the change is
            not in place, or could not be read; any other error from ``write`` unchanged.
    """
    try:
        return write()
    except CliError as error:
        if error.code != CODE_OUTCOME_UNKNOWN:
            raise
        unknown = error
    try:
        record = service.call(read_symbol, **read_kwargs)
    except CliError as read_error:
        if _is_gone(read_error):
            record, in_place = None, True
        else:
            raise unknown from read_error
    else:
        in_place = applied(record)
    if not in_place:
        raise unknown
    return {
        "id": resource_id,
        "status": done_status,
        "confirmed_by_read_back": True,
        "note": (
            f"The write's reply was lost, so the {noun} was read back once: "
            f"it is {done_status}. Nothing was sent twice."
        ),
    }
