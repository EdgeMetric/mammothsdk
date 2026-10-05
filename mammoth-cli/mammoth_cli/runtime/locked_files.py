"""Password-protected files, stated wherever one appears in a result.

A file record carries ``password_protected: true``, but the flag alone does not
say what to do. :func:`with_locked_files` adds a ``locked_files`` entry per such
file that says the file's password unlocks it and names the command that takes
the password. It runs on every result and never makes a request.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

#: Nesting to search: a result, a listing inside it, a record in the listing.
_MAX_DEPTH = 3
#: Where a file record keeps the flag: a file listing, a browse search record.
_INFO_KEYS = ("additional_info", "additional_data")
_BROWSE_FILE_TYPE = "file_object"


def with_locked_files(data: Any) -> Any:
    """Return ``data`` with a ``locked_files`` list, or unchanged when no file is locked."""
    # A file listing comes back as an SDK model; it is read as the output prints it.
    plain = data.model_dump(mode="python") if hasattr(data, "model_dump") else data
    if not isinstance(plain, dict):
        return data
    locked = [_entry(record) for record in _locked_records(plain, 0)]
    if not locked:
        return data
    return {**plain, "locked_files": locked}


def _locked_records(value: Any, depth: int) -> Iterator[dict[str, Any]]:
    if depth > _MAX_DEPTH:
        return
    if isinstance(value, dict):
        if _is_locked(value) and _file_id(value) is not None:
            yield value
        for child in value.values():
            yield from _locked_records(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from _locked_records(child, depth + 1)


def _is_locked(record: dict[str, Any]) -> bool:
    return any(
        isinstance(info := record.get(key), dict) and info.get("password_protected") is True
        for key in _INFO_KEYS
    )


def _file_id(record: dict[str, Any]) -> int | None:
    """A file record names itself ``id``; a browse record names the file ``object_id``."""
    key = "object_id" if record.get("resource_type") == _BROWSE_FILE_TYPE else "id"
    value = record.get(key)
    return value if isinstance(value, int) else None


def _entry(record: dict[str, Any]) -> dict[str, Any]:
    file_id = _file_id(record)
    return {
        "file_id": file_id,
        "name": record.get("name"),
        "detail": "This file is password-protected; its data cannot be read until it is unlocked.",
        "fix": (
            "Ask the user for the file's password, not for an unlocked copy, then run "
            f"mammoth file set-password {file_id} with the password in --input."
        ),
    }
