"""What a data-changing transform would change, counted by a read (no write).

``--dry-run`` of a transform uses these to say, before anything is approved or
written, how many rows or cells the step would touch. A count of zero means the
step would leave a no-op in the pipeline, and the dry run fails with ``no_op``
instead of reporting a change that will not happen.

Every ``measure_*`` takes the :class:`ImpactRead` of one view and the transform's
bound SDK arguments, and returns a :class:`Measured`. Counts that are only an
upper bound say so in their key (``rows_matching``, ``blank_cells``); a zero is
exact either way, because a bound of zero means nothing can change.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from mammoth_cli.errors.envelope import CODE_NO_OP, EXIT_USAGE, CliError
from mammoth_cli.services import read_queries
from mammoth_cli.services.conditions import compile_condition

#: Duplicate groups read back, largest first; more than this is reported as a floor.
MAX_DUPLICATE_GROUPS = 1000
_COUNT_KEY = "agg_0"
_COUNT = [{"function": "COUNT", "as_name": "rows"}]
_REMOVE = "REMOVE"


@dataclass(frozen=True)
class Measured:
    """One transform's predicted impact.

    Attributes:
        changes: Rows or cells the step would change; 0 makes the dry run a no-op.
        report: The ``predicted_impact`` block of the dry-run report.
        no_op_message: What the ``no_op`` error says when ``changes`` is 0.
    """

    changes: int
    report: dict[str, Any]
    no_op_message: str


@dataclass(frozen=True)
class ImpactRead:
    """The view a dry run reads: where it is, its column metadata, the input document."""

    service: Any
    dataset_id: int
    view_id: int
    project_id: int | None
    info: Mapping[str, Any]
    document: Mapping[str, Any] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return int(self.info.get("row_count") or 0)

    def columns(self) -> list[dict[str, Any]]:
        return [c for c in self.info.get("metadata") or [] if isinstance(c, dict)]

    def display_to_internal(self) -> dict[str, str]:
        return {
            str(c["display_name"]): str(c["internal_name"])
            for c in self.columns()
            if c.get("display_name") and c.get("internal_name")
        }

    def column_types(self) -> dict[str, str]:
        return {
            str(c["display_name"]): str(c.get("type") or "")
            for c in self.columns()
            if c.get("display_name")
        }

    def aggregate(self, **fields: Any) -> list[dict[str, Any]]:
        """Rows of one read-only aggregate against this view."""
        result = self.service.call(
            read_queries.AGGREGATE_SYMBOL,
            dataset_id=self.dataset_id,
            dataview_id=self.view_id,
            project_id=self.project_id,
            **fields,
        )
        return [row for row in (result or {}).get("data") or [] if isinstance(row, dict)]

    def count(self, condition: Any = None) -> int:
        """Rows matching ``condition`` (a compiled condition; all rows without one)."""
        built = (
            condition.build(self.display_to_internal() or None, self.column_types() or None)
            if condition is not None
            else None
        )
        rows = self.aggregate(aggregations=_COUNT, condition=built)
        if not rows:
            raise _unmeasurable("the count query returned no row")
        return int(rows[0].get(_COUNT_KEY) or 0)


def no_op_error(message: str, *, view_id: int) -> CliError:
    """The dry-run failure for a step that would change nothing."""
    return CliError(
        code=CODE_NO_OP,
        message=message,
        exit_status=EXIT_USAGE,
        hint="Nothing was changed and nothing needs to be; tell the user there is no work.",
        details={"view_id": view_id},
    )


def _unmeasurable(reason: str) -> CliError:
    """The impact could not be counted; a real write goes ahead, a dry run says so."""
    return CliError(
        code="invalid_arguments",
        message=f"Could not count the impact: {reason}.",
        exit_status=EXIT_USAGE,
    )


def _rows_report(removed: int, row_count: int, exact: bool = True) -> dict[str, Any]:
    return {
        "rows_removed": removed,
        "row_count": row_count,
        "rows_after": row_count - removed,
        "exact": exact,
    }


# --- discard-duplicates ----------------------------------------------------


def measure_duplicates(read: ImpactRead, kwargs: Mapping[str, Any]) -> Measured:
    """Exact duplicate rows a discard-duplicates would remove, honouring ``ignore_columns``.

    Groups the view by every compared column and reads the largest groups back,
    so no row data leaves the backend.
    """
    ignored = [str(name) for name in kwargs.get("ignore_columns") or []]
    columns = [
        internal for name, internal in read.display_to_internal().items() if name not in ignored
    ]
    if not columns:
        raise _unmeasurable("the view has no columns to compare")
    rows = read.aggregate(
        aggregations=_COUNT,
        group_by=columns,
        sort=[[_COUNT_KEY, "DESC"]],
        limit=MAX_DUPLICATE_GROUPS,
    )
    if not rows and read.row_count:
        raise _unmeasurable("the duplicate query returned no groups for a view with rows")
    counts = [int(row.get(_COUNT_KEY) or 0) for row in rows]
    removed = sum(count - 1 for count in counts if count > 1)
    exact = not (len(counts) >= MAX_DUPLICATE_GROUPS and counts[-1] > 1)
    scope = f", ignoring {', '.join(ignored)}" if ignored else ""
    total = read.row_count
    return Measured(
        removed,
        _rows_report(removed, total, exact),
        f"View {read.view_id} has no exact duplicate rows ({total} of {total} checked{scope}); "
        "nothing to change.",
    )


# --- filter ----------------------------------------------------------------


def measure_filter(read: ImpactRead, kwargs: Mapping[str, Any]) -> Measured:
    """Rows a filter would remove: the non-matching rows for SHOW, the matching ones for REMOVE."""
    total = read.row_count
    reads = read_queries.ReadContext(
        read.service,
        read.dataset_id,
        read.view_id,
        read.project_id,
        read.display_to_internal(),
        read.column_types(),
    )
    spec = read_queries.resolve_text_date_conditions(reads, read.document["condition"])
    matching = read.count(compile_condition(spec))
    removes = str(read.document.get("filter_type") or "SHOW").upper() == _REMOVE
    removed = matching if removes else total - matching
    message = (
        f"No row of view {read.view_id} matches the condition (0 of {total}), so removing "
        "matching rows changes nothing; nothing to change."
        if removes
        else f"Every row of view {read.view_id} matches the condition ({total} of {total}), "
        "so the filter keeps all of them; nothing to change."
    )
    return Measured(removed, _rows_report(removed, total), message)


# --- fill-missing ----------------------------------------------------------


def measure_fill_missing(read: ImpactRead, kwargs: Mapping[str, Any]) -> Measured:
    """Blank cells in the column: the most a fill can change (leading blanks may stay)."""
    column = str(kwargs["column"])
    blanks = read.count(compile_condition({"column": column, "operator": "IS_EMPTY"}))
    return Measured(
        blanks,
        {"blank_cells": blanks, "row_count": read.row_count, "exact": False},
        f"Column {column} of view {read.view_id} has no blank values (0 of {read.row_count} "
        "rows); nothing to fill, nothing to change.",
    )


# --- replace / bulk-replace --------------------------------------------------


def _any_contains(columns: Sequence[str], values: Sequence[str], match_case: bool) -> Any:
    operator = "CONTAINS" if match_case else "ICONTAINS"
    return compile_condition(
        {
            "or": [
                {"column": column, "operator": operator, "value": value}
                for column in columns
                for value in values
            ]
        }
    )


def _measure_replace(
    read: ImpactRead, kwargs: Mapping[str, Any], values: Sequence[str], match_case: bool
) -> Measured:
    columns = [str(c) for c in kwargs["columns"]]
    condition = _any_contains(columns, values, match_case)
    scope = kwargs.get("condition")
    if isinstance(scope, Mapping):
        scope = compile_condition(scope)
    matching = read.count(condition & scope if scope is not None else condition)
    shown = ", ".join(repr(v) for v in values[:5])
    return Measured(
        matching,
        {"rows_matching": matching, "row_count": read.row_count, "exact": False},
        f"No row of view {read.view_id} holds {shown} in {', '.join(columns)} "
        f"(0 of {read.row_count} rows); nothing to replace, nothing to change.",
    )


def measure_replace(read: ImpactRead, kwargs: Mapping[str, Any]) -> Measured:
    """Rows that contain the text to find (the most a replace can change)."""
    return _measure_replace(
        read, kwargs, [str(kwargs["find"])], bool(kwargs.get("match_case", False))
    )


def measure_bulk_replace(read: ImpactRead, kwargs: Mapping[str, Any]) -> Measured:
    """Rows that contain any search value of the mapping (the most a bulk replace can change)."""
    # The SDK objects are built later, in the service; here entries are still mappings.
    entries = [e if isinstance(e, Mapping) else vars(e) for e in kwargs["mapping"]]
    values = [str(v) for entry in entries for v in entry.get("search") or []]
    return _measure_replace(read, kwargs, values, bool(kwargs.get("match_case", True)))


Measure = Callable[[ImpactRead, Mapping[str, Any]], Measured]
