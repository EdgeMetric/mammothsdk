"""One paging block for every paged read: 0-based offset, explicit next and previous.

The API routes disagree: the dataview data route counts rows from 1, the export and
pipeline routes skip from 0 and echo a drifting ``offset`` with an empty ``next``.
The CLI surface is 0-based everywhere (``offset`` is the number of rows to skip) and
reports the same block, computed from what was asked and what came back, so pages
neither overlap nor leave gaps.
"""

from __future__ import annotations

import json
import shlex
from typing import Any


def paging_block(
    *,
    command: str,
    project: int | None,
    offset: int,
    limit: int,
    returned: int,
    total: int | None = None,
) -> dict[str, Any]:
    """The ``paging`` block for one page.

    Args:
        command: The command words up to the ids, e.g. ``"mammoth view data get 7"``.
        project: Project id to repeat in the continuation commands, if any.
        offset: Rows skipped before this page (0-based).
        limit: Page size that was asked for.
        returned: Rows this page holds.
        total: Row count of the whole listing when the route reports it. With none,
            a page of ``limit`` rows is taken to have a successor.

    Returns:
        ``offset``, ``limit``, ``count``, ``total`` (when known) and ``next_offset``,
        ``next_command``, ``previous_offset``, ``previous_command``; each of the last
        four is null when there is no such page.
    """
    if total is not None:
        more = offset + returned < total
    else:
        more = limit > 0 and returned >= limit
    more = more and returned > 0
    next_offset = offset + returned if more else None
    previous_offset = max(0, offset - limit) if offset > 0 and limit > 0 else None
    block: dict[str, Any] = {"offset": offset, "limit": limit, "count": returned}
    if total is not None:
        block["total"] = total
    block["next_offset"] = next_offset
    block["next_command"] = (
        _command(command, project, next_offset, limit) if next_offset is not None else None
    )
    block["previous_offset"] = previous_offset
    block["previous_command"] = (
        _command(command, project, previous_offset, limit) if previous_offset is not None else None
    )
    return block


def _command(command: str, project: int | None, offset: int, limit: int) -> str:
    payload = json.dumps({"offset": offset, "limit": limit})
    suffix = f" --project {project}" if project is not None else ""
    return f"{command} --input {shlex.quote(payload)}{suffix}"
