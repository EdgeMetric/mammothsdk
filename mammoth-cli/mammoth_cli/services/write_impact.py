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

import re
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from mammoth_cli.errors.envelope import CODE_EMPTIES_VIEW, CODE_NO_OP, EXIT_USAGE, CliError
from mammoth_cli.services import data_profile as dp
from mammoth_cli.services import read_queries
from mammoth_cli.services.conditions import compile_condition

#: Duplicate groups read back, largest first; more than this is reported as a floor.
MAX_DUPLICATE_GROUPS = 1000
_COUNT_KEY = "agg_0"
_GROUP_KEY = "group_0"
_COUNT = [{"function": "COUNT", "as_name": "rows"}]
_REMOVE = "REMOVE"


@dataclass(frozen=True)
class Measured:
    """One transform's predicted impact.

    Attributes:
        changes: Rows or cells the step would change; 0 makes the dry run a no-op.
        report: The ``predicted_impact`` block of the dry-run report.
        no_op_message: What the ``no_op`` error says when ``changes`` is 0.
        empties_message: What the ``empties_view`` error says when a keep filter
            matches no row; ``None`` for every other step.
    """

    changes: int
    report: dict[str, Any]
    no_op_message: str
    empties_message: str | None = None


@dataclass(frozen=True)
class ImpactRead:
    """The view a dry run reads: where it is, its column metadata, the input document."""

    service: Any
    dataset_id: int
    view_id: int
    project_id: int | None
    info: Mapping[str, Any]
    document: Mapping[str, Any] = field(default_factory=dict)
    dry_run: bool = False

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
        return _rows(self._query(**fields))

    def _query(self, **fields: Any) -> dict[str, Any]:
        result = self.service.call(
            read_queries.AGGREGATE_SYMBOL,
            dataset_id=self.dataset_id,
            dataview_id=self.view_id,
            project_id=self.project_id,
            **fields,
        )
        return result if isinstance(result, dict) else {}

    def count(self, condition: Any = None) -> int:
        """Rows matching ``condition`` (a compiled condition; all rows without one)."""
        built = (
            condition.build(self.display_to_internal() or None, self.column_types() or None)
            if condition is not None
            else None
        )
        result = self._query(aggregations=_COUNT, condition=built)
        rows = _rows(result)
        if rows:
            return int(rows[0].get(_COUNT_KEY) or 0)
        # An answered count no row matches comes back with no row, not a row of 0.
        if result.get("STATUS") == "READY":
            return 0
        raise _unmeasurable("the count query returned no row")


def _rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [row for row in result.get("data") or [] if isinstance(row, dict)]


#: Said wherever a step is refused or skipped for changing no row today.
STANDING_HINT = "To keep it as a standing rule for future data, add --standing to stage it anyway."
#: What a staged zero-change step tells the caller.
STANDING_NOTE = "Staged as a standing rule: it changes no row today and will apply to future rows."


def no_op_error(message: str, *, view_id: int) -> CliError:
    """The dry-run failure for a step that would change nothing."""
    return CliError(
        code=CODE_NO_OP,
        message=message,
        exit_status=EXIT_USAGE,
        hint="Nothing was changed and nothing needs to be; tell the user there is no work. "
        + STANDING_HINT,
        details={"view_id": view_id},
    )


def empties_view_error(message: str, *, view_id: int) -> CliError:
    """The dry-run failure for a keep filter that matches no row."""
    return CliError(
        code=CODE_EMPTIES_VIEW,
        message=message,
        exit_status=EXIT_USAGE,
        hint="Nothing was changed. Tell the user no row matches and name the values the "
        "column holds, then ask which they meant. Only if the user then asks for the empty "
        "filter anyway, run the command again with --allow-empty.",
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
    report = _rows_report(removed, total)
    held = _values_when_nothing_matches(read, spec) if matching == 0 else None
    if held is not None:
        report["no_row_matches"] = held
    message = (
        f"No row of view {read.view_id} matches the condition (0 of {total}), so removing "
        f"matching rows changes nothing; nothing to change.{_holds_note(held)}"
        if removes
        else f"Every row of view {read.view_id} matches the condition ({total} of {total}), "
        "so the filter keeps all of them; nothing to change."
    )
    empties = (
        f"No row of view {read.view_id} matches the condition (0 of {total}), so keeping "
        f"only matching rows would leave the view empty.{_holds_note(held)}"
        if matching == 0 and total and not removes
        else None
    )
    return Measured(removed, report, message, empties)


#: Distinct values named when a one-column condition matches no row.
_HELD_VALUES_CAP = 20


def _values_when_nothing_matches(read: ImpactRead, spec: Any) -> dict[str, Any] | None:
    """The values a one-column condition's column holds, when no row matched it.

    "Keep only North" on East/West data matches nothing; saying so without the
    values there leaves the agent guessing what the user meant (FB-03).
    """
    column = spec.get("column") if isinstance(spec, dict) else None
    internal = read.display_to_internal().get(str(column)) if column else None
    if internal is None:
        return None
    rows = read.aggregate(
        aggregations=_COUNT,
        group_by=[internal],
        sort=[[_COUNT_KEY, "DESC"]],
        limit=_HELD_VALUES_CAP,
    )
    values = {str(row.get(_GROUP_KEY)): int(row.get(_COUNT_KEY) or 0) for row in rows}
    return {"column": str(column), "values": values} if values else None


def _holds_note(held: dict[str, Any] | None) -> str:
    if held is None:
        return ""
    listed = ", ".join(f"{value} ({count})" for value, count in held["values"].items())
    return f" {held['column']} holds: {listed}."


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


def _variants_left(
    read: ImpactRead, columns: Sequence[str], rewrite: Callable[[str], str]
) -> dict[str, Any]:
    """Per TEXT column, the spelling-variant groups still there once ``rewrite`` is applied.

    Reads the column's value table (what the profile reads), applies the step to
    it in memory and groups what is left, so a merge that fixed 343 of 347
    groups says so before it is approved. Never blocks the dry run.
    """
    left: dict[str, Any] = {}
    internal, types = read.display_to_internal(), read.column_types()
    for column in columns:
        if types.get(column) != "TEXT" or column not in internal:
            continue
        try:
            rows = read.aggregate(
                aggregations=_COUNT,
                group_by=[internal[column]],
                limit=dp.MAX_LISTED_DISTINCT + 2,
            )
        except Exception as exc:  # noqa: BLE001 -- the dry run must still report its count
            left[column] = {"checked": False, "reason": str(exc)[:120]}
            continue
        if len(rows) > dp.MAX_LISTED_DISTINCT + 1:
            left[column] = {"checked": False, "reason": "too many distinct values to compare"}
            continue
        counts: dict[str, int] = defaultdict(int)
        for row in rows:
            if isinstance(row.get("group_0"), str):
                counts[rewrite(row["group_0"])] += int(row.get(_COUNT_KEY) or 0)
        groups, likely = dp.variant_groups(counts), dp.likely_groups(counts)
        if groups or likely:
            left[column] = {
                "groups_left": len(groups),
                "likely_groups_left": len(likely),
                "examples": [[v["value"] for v in g["variants"]] for g in (groups + likely)[:3]],
            }
    return left


def _rewriter(
    pairs: Sequence[tuple[str, str]], match_case: bool, whole: bool
) -> Callable[[str], str]:
    """The text change a replace makes to one value (substring, or whole cell)."""
    flags = 0 if match_case else re.IGNORECASE

    def rewrite(value: str) -> str:
        for search, replace in pairs:
            pattern = re.escape(search)
            value = re.sub(
                f"^{pattern}$" if whole else pattern, lambda _m, r=replace: r, value, flags=flags
            )
        return value

    return rewrite


def _measure_replace(
    read: ImpactRead,
    kwargs: Mapping[str, Any],
    pairs: Sequence[tuple[str, str]],
    options: tuple[bool, bool] = (False, False),
) -> Measured:
    match_case, whole = options
    values = [search for search, _replace in pairs]
    columns = [str(c) for c in kwargs["columns"]]
    condition = _any_contains(columns, values, match_case)
    scope = kwargs.get("condition")
    if isinstance(scope, Mapping):
        scope = compile_condition(scope)
    matching = read.count(condition & scope if scope is not None else condition)
    shown = ", ".join(repr(v) for v in values[:5])
    report: dict[str, Any] = {
        "rows_matching": matching,
        "row_count": read.row_count,
        "exact": False,
    }
    if read.dry_run and matching and scope is None:
        left = _variants_left(read, columns, _rewriter(pairs, match_case, whole))
        report["variants_left"] = left or "none: no spelling-variant group remains in these columns"
    return Measured(
        matching,
        report,
        f"No row of view {read.view_id} holds {shown} in {', '.join(columns)} "
        f"(0 of {read.row_count} rows); nothing to replace, nothing to change.",
    )


def measure_replace(read: ImpactRead, kwargs: Mapping[str, Any]) -> Measured:
    """Rows that contain the text to find (the most a replace can change)."""
    pairs = [(str(kwargs["find"]), str(kwargs.get("replace", "")))]
    return _measure_replace(read, kwargs, pairs, (bool(kwargs.get("match_case", False)), False))


def measure_bulk_replace(read: ImpactRead, kwargs: Mapping[str, Any]) -> Measured:
    """Rows that contain any search value of the mapping (the most a bulk replace can change)."""
    # The SDK objects are built later, in the service; here entries are still mappings.
    entries = [e if isinstance(e, Mapping) else vars(e) for e in kwargs["mapping"]]
    pairs = [
        (str(v), str(entry.get("replace", "")))
        for entry in entries
        for v in entry.get("search") or []
    ]
    options = (bool(kwargs.get("match_case", True)), bool(kwargs.get("match_words", False)))
    return _measure_replace(read, kwargs, pairs, options)


Measure = Callable[[ImpactRead, Mapping[str, Any]], Measured]
