"""What a data-changing transform would change, counted by a read (no write).

``--dry-run`` of a transform uses these to say, before anything is approved or
written, how many rows or cells the step would touch. A count of zero means the
step would leave a no-op in the pipeline, and the dry run fails with ``no_op``
instead of reporting a change that will not happen.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from mammoth_cli.errors.envelope import CODE_NO_OP, EXIT_USAGE, CliError
from mammoth_cli.services.read_queries import AGGREGATE_SYMBOL

#: Duplicate groups read back, largest first; more than this is reported as a floor.
MAX_DUPLICATE_GROUPS = 1000
_COUNT_KEY = "agg_0"


def duplicate_rows_removed(
    service: Any,
    *,
    dataset_id: int,
    view_id: int,
    project_id: int | None,
    columns: Sequence[str],
) -> tuple[int, bool]:
    """Rows a discard-duplicates over ``columns`` (internal names) would remove.

    Groups the view by every compared column and reads the largest groups back,
    so no row data leaves the backend. Returns ``(rows_removed, exact)``;
    ``exact`` is False when more groups than :data:`MAX_DUPLICATE_GROUPS` repeat.
    """
    result = service.call(
        AGGREGATE_SYMBOL,
        dataset_id=dataset_id,
        dataview_id=view_id,
        project_id=project_id,
        aggregations=[{"function": "COUNT", "as_name": "rows"}],
        group_by=list(columns),
        sort=[[_COUNT_KEY, "DESC"]],
        limit=MAX_DUPLICATE_GROUPS,
    )
    rows = [row for row in (result or {}).get("data") or [] if isinstance(row, dict)]
    counts = [int(row.get(_COUNT_KEY) or 0) for row in rows]
    removed = sum(count - 1 for count in counts if count > 1)
    truncated = len(counts) >= MAX_DUPLICATE_GROUPS and counts[-1] > 1
    return removed, not truncated


def no_op_error(message: str, *, view_id: int, hint: str | None = None) -> CliError:
    """The dry-run failure for a step that would change nothing."""
    return CliError(
        code=CODE_NO_OP,
        message=message,
        exit_status=EXIT_USAGE,
        hint=hint or "Nothing was changed and nothing needs to be; tell the user there is no work.",
        details={"view_id": view_id},
    )
