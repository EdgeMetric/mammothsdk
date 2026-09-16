"""Small, defensive helpers for offset-paginated API responses.

The API commonly returns a ``next`` URL even when the page is empty or when a
proxy accidentally repeats the same page.  Never treat that hint as proof of
progress: callers must bound pages and prove both cursor and record progress.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import parse_qs, urlparse

from mammoth.exceptions import MammothPaginationError, MammothValidationError


def next_offset_from_hint(hint: object, current: int) -> int | None:
    """Extract a strictly advancing offset from a server ``next`` hint."""
    if not hint:
        return None
    parsed = urlparse(str(hint))
    values = parse_qs(parsed.query).get("offset")
    if not values:
        return None
    try:
        candidate = int(values[-1])
    except (TypeError, ValueError) as exc:
        raise MammothPaginationError(
            "The API returned a non-numeric pagination offset.",
            {"offset": values[-1], "current_offset": current},
        ) from exc
    if candidate <= current:
        raise MammothPaginationError(
            "The API returned a non-advancing pagination offset.",
            {"offset": candidate, "current_offset": current},
        )
    return candidate


def collect_offset_pages(
    fetch: Callable[[int], Mapping[str, Any]],
    *,
    item_key: str,
    limit: int,
    max_pages: int = 1000,
) -> dict[str, Any]:
    """Collect pages while requiring bounded, observable progress.

    ``fetch`` receives the offset to request.  If a page has records but no
    explicit offset in its ``next`` URL, the next offset is derived from the
    current offset and page length (the documented offset contract).  A page
    fingerprint is tracked as well, so a repeated full page cannot loop even
    when the backend emits a malformed continuation URL.
    """
    if limit <= 0:
        raise MammothValidationError("`limit` must be > 0")
    if max_pages <= 0:
        raise MammothValidationError("`max_pages` must be > 0")

    offset = 0
    pages = 0
    seen_offsets: set[int] = set()
    seen_fingerprints: set[str] = set()
    records: list[Any] = []
    first: dict[str, Any] | None = None

    while True:
        if pages >= max_pages:
            raise MammothPaginationError(
                "Pagination exceeded the configured page bound.",
                {"max_pages": max_pages, "offset": offset, "records": len(records)},
            )
        if offset in seen_offsets:
            raise MammothPaginationError(
                "Pagination did not advance its offset.", {"offset": offset}
            )
        seen_offsets.add(offset)
        page = dict(fetch(offset))
        if first is None:
            first = page
        page_records = page.get(item_key, [])
        if not isinstance(page_records, list):
            raise MammothPaginationError(
                "The API returned a non-list page collection.", {"item_key": item_key}
            )
        if not page_records:
            if page.get("next"):
                raise MammothPaginationError(
                    "The API returned an empty page with a continuation hint.",
                    {"offset": offset, "next": page.get("next")},
                )
            break

        fingerprint = json.dumps(page_records, sort_keys=True, default=str, separators=(",", ":"))
        if fingerprint in seen_fingerprints:
            raise MammothPaginationError(
                "The API repeated a pagination page.", {"offset": offset}
            )
        seen_fingerprints.add(fingerprint)
        records.extend(page_records)
        pages += 1

        hint_offset = next_offset_from_hint(page.get("next"), offset)
        if hint_offset is None:
            if not page.get("next"):
                break
            hint_offset = offset + len(page_records)
            if hint_offset <= offset:
                raise MammothPaginationError(
                    "The API continuation did not make progress.", {"offset": offset}
                )
        offset = hint_offset

    result = dict(first or {})
    result[item_key] = records
    result["offset"] = 0
    result["limit"] = limit
    result["pages"] = pages
    result["next"] = None
    if "total" in result and result["total"] is None:
        result["total"] = len(records)
    return result
