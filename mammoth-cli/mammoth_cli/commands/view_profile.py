"""``view data profile``: what is in this view, over ALL its rows.

Read-only. Every number comes from a backend aggregate over the whole view
(a job per question, never a page of rows pulled here): one pivot per batch
of columns for distinct counts and min/max, one grouped count per column for
nulls, top values and spelling variants, and -- with a ``target`` -- one
grouped count of (column, target) per column for the association ranking.
The arithmetic on those answers lives in :mod:`mammoth_cli.services.data_profile`.
"""

from __future__ import annotations

import json
import shlex
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from mammoth_cli.commands.view import (
    _column_profile,
    _meta,
    _require_int_positional_at,
    _resolve_dataset_id,
)
from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENTS, EXIT_USAGE, CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services import data_profile as dp
from mammoth_cli.services.conditions import compile_condition

HandlerResult = tuple[Any, dict[str, Any]]

_AGGREGATE = "mammoth.api.dataviews.DataviewsAPI.aggregate"
_TOTALS_BATCH = 40
_WORKERS = 6
_DEFAULT_TOP = 5
_DEFAULT_DETAIL_LIMIT = 50
_ASSOCIATION_LIMIT = 20
_BUCKET_ABOVE_DISTINCT = 200
_MAX_VARIANT_GROUPS = 25
_RANGE_TYPES = frozenset({"NUMERIC", "DATE"})
_COUNT = {"function": "COUNT", "as_name": "n"}


@dataclass
class _Scope:
    """Everything one profile run needs to ask the backend about a view."""

    service: Any
    dataset_id: int
    view_id: int
    project_id: int
    internal: dict[str, str]  # display name -> internal name
    types: dict[str, str]  # display name -> type

    def rows(self, **fields: Any) -> list[dict[str, Any]]:
        """Run one aggregate job and return its result rows."""
        result = self.service.call(
            _AGGREGATE,
            dataset_id=self.dataset_id,
            dataview_id=self.view_id,
            project_id=self.project_id,
            **fields,
        )
        rows = result.get("data") if isinstance(result, dict) else None
        return [row for row in rows or [] if isinstance(row, dict)]

    def blank_count(self, column: str) -> int:
        """Rows where ``column`` is empty (NULL or blank), as one filtered count."""
        condition = compile_condition({"column": column, "operator": "IS_EMPTY"})
        built = condition.build(self.internal, self.types)
        rows = self.rows(aggregations=[_COUNT], condition=built)
        return int(rows[0].get("agg_0") or 0) if rows else 0


def view_data_profile(invocation: Invocation) -> HandlerResult:
    """Profile a view's columns over all its rows; ``target`` ranks columns against an outcome."""
    project_id = require_project(invocation)
    view_id = _require_int_positional_at(invocation, 0, "view id")
    document = invocation.load_input() or {}
    with open_service(invocation) as (service, auth):
        dataset_id = _resolve_dataset_id(service, invocation, view_id, document, 1)
        to_display, types = _column_profile(service, dataset_id, view_id, project_id)
        scope = _Scope(
            service, dataset_id, view_id, project_id, {v: k for k, v in to_display.items()}, types
        )
        workers = 1 if getattr(service, "_progress", False) else _WORKERS
        profile = build_profile(scope, document, workers)
    return profile, _meta(invocation, auth.workspace_id, project_id)


def build_profile(scope: _Scope, document: dict[str, Any], workers: int) -> dict[str, Any]:
    """Run the backend questions and assemble the result."""
    names = _selected_columns(scope, document)
    target = document.get("target")
    if target is not None and target not in scope.types:
        raise _usage(f"target column {target!r} is not in the view", sorted(scope.types))
    profiled = list(dict.fromkeys([*names, *([target] if target else [])]))
    total_rows, facts = _column_facts(scope, profiled)
    tables = _value_tables(scope, facts, total_rows, workers)
    top = int(document.get("top", _DEFAULT_TOP))
    details = {name: _detail(name, scope, facts[name], tables, total_rows, top) for name in names}
    result: dict[str, Any] = {
        "view_id": scope.view_id,
        "dataset_id": scope.dataset_id,
        "row_count": total_rows,
        "summary": _summary(details, total_rows),
        **_paged_columns(details, int(document.get("limit", _DEFAULT_DETAIL_LIMIT))),
        "spelling_variants": _variant_report(scope, names, tables),
    }
    if target:
        result["target"] = _target_report(
            scope, str(target), names, facts, tables, total_rows, workers
        )
    return result


def _usage(message: str, choices: list[str]) -> CliError:
    return CliError(
        code=CODE_INVALID_ARGUMENTS,
        message=message,
        exit_status=EXIT_USAGE,
        hint="Columns: " + ", ".join(choices[:20]) + (" ..." if len(choices) > 20 else ""),
    )


def _selected_columns(scope: _Scope, document: dict[str, Any]) -> list[str]:
    requested = document.get("columns")
    if requested is None:
        return list(scope.types)
    missing = [name for name in requested if name not in scope.types]
    if missing:
        raise _usage(f"columns not in the view: {missing}", sorted(scope.types))
    return list(dict.fromkeys(requested))


def _map_all[T](workers: int, fn: Callable[..., T], items: list[Any]) -> list[T]:
    """Apply ``fn`` to each item, concurrently; results keep the item order."""
    if workers <= 1 or len(items) <= 1:
        return [fn(item) for item in items]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(fn, items))


# -- pass 1: distinct count and min/max of every column, a few pivots in all ----------


def _column_facts(scope: _Scope, names: list[str]) -> tuple[int, dict[str, dict[str, Any]]]:
    facts: dict[str, dict[str, Any]] = {}
    total_rows = 0
    for start in range(0, len(names), _TOTALS_BATCH):
        batch = names[start : start + _TOTALS_BATCH]
        aggregations, slots = _totals_request(scope, batch)
        rows = scope.rows(aggregations=aggregations)
        row = rows[0] if rows else {}
        total_rows = int(row.get("agg_0") or 0)
        for (name, stat), key in slots.items():
            facts.setdefault(name, {})[stat] = row.get(key)
    return total_rows, facts


def _totals_request(
    scope: _Scope, batch: list[str]
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], str]]:
    aggregations: list[dict[str, Any]] = [_COUNT]
    slots: dict[tuple[str, str], str] = {}
    for name in batch:
        stats = ["distinct"] + (["min", "max"] if scope.types.get(name) in _RANGE_TYPES else [])
        for stat in stats:
            function = "DISTINCT_COUNT" if stat == "distinct" else stat.upper()
            slots[(name, stat)] = f"agg_{len(aggregations)}"
            aggregations.append(
                {
                    "function": function,
                    "column": scope.internal[name],
                    "as_name": f"{stat}_{len(slots)}",
                }
            )
    return aggregations, slots


# -- pass 2: one grouped count per column -> its whole value table -----------------------


def _value_tables(
    scope: _Scope, facts: dict[str, dict[str, Any]], total_rows: int, workers: int
) -> dict[str, dict[Any, int] | None]:
    """``{column: {value: rows}}``; ``None`` when the column has too many values to list."""
    names = [n for n, f in facts.items() if _needs_table(f, total_rows)]

    def table(name: str) -> dict[Any, int] | None:
        rows = scope.rows(
            aggregations=[_COUNT],
            group_by=[scope.internal[name]],
            limit=dp.MAX_LISTED_DISTINCT + 2,
        )
        if len(rows) > dp.MAX_LISTED_DISTINCT + 1:
            return None
        return dp.value_counts(rows, "group_0", "agg_0")

    return dict(zip(names, _map_all(workers, table, names), strict=True))


def _needs_table(fact: dict[str, Any], total_rows: int) -> bool:
    distinct = int(fact.get("distinct") or 0)
    return 0 < distinct <= dp.MAX_LISTED_DISTINCT and distinct != total_rows


# -- per-column detail and summary -----------------------------------------------------


def _detail(
    name: str,
    scope: _Scope,
    fact: dict[str, Any],
    tables: dict[str, dict[Any, int] | None],
    total_rows: int,
    top: int,
) -> dict[str, Any]:
    distinct = int(fact.get("distinct") or 0)
    detail: dict[str, Any] = {"column": name, "type": scope.types.get(name), "distinct": distinct}
    if "min" in fact:
        detail.update(min=fact["min"], max=fact["max"])
    table = tables.get(name)
    if table is not None:
        summary = dp.summarize_column(table, total_rows, top)
        detail.update(nulls=summary["nulls"], top=_top_text(summary["top_values"]))
    elif distinct == 0:
        detail.update(nulls=total_rows)
    elif distinct == total_rows:
        detail.update(nulls=0, note="every value is different")
    else:
        detail.update(nulls=scope.blank_count(name), note=f"{distinct} distinct values, not listed")
    return detail


def _top_text(values: list[dict[str, Any]]) -> list[str]:
    return [f"{item['value']} ({item['count']})" for item in values]


def _summary(details: dict[str, dict[str, Any]], total_rows: int) -> dict[str, Any]:
    rows = list(details.values())
    return {
        "columns": len(rows),
        "constant": [d["column"] for d in rows if d["distinct"] == 1 and not d.get("nulls")],
        "all_blank": [d["column"] for d in rows if d["distinct"] == 0],
        "mostly_blank": [
            {"column": d["column"], "nulls": d["nulls"]}
            for d in rows
            if d["distinct"] > 0 and d.get("nulls", 0) * 2 >= total_rows
        ],
    }


def _paged_columns(details: dict[str, dict[str, Any]], limit: int) -> dict[str, Any]:
    shown = list(details.values())[:limit]
    paged: dict[str, Any] = {"columns_detail": shown}
    if len(details) > len(shown):
        paged["columns_omitted"] = len(details) - len(shown)
        paged["columns_note"] = "Pass input 'columns' (names) or a larger 'limit' to see the rest."
    return paged


# -- spelling variants ---------------------------------------------------------------------


def _variant_report(
    scope: _Scope, names: list[str], tables: dict[str, dict[Any, int] | None]
) -> list[dict[str, Any]]:
    """Per TEXT column, spellings of one value (Ltd/Limited, case, punctuation) and the fix."""
    report: list[dict[str, Any]] = []
    for name in names:
        table = tables.get(name)
        if table is None or scope.types.get(name) != "TEXT":
            continue
        groups = dp.variant_groups({k: v for k, v in table.items() if isinstance(k, str)})
        if not groups:
            continue
        shown = groups[:_MAX_VARIANT_GROUPS]
        body = {**dp.bulk_replace_input(name, shown), "dataset_id": scope.dataset_id}
        report.append(
            {
                "column": name,
                "groups_total": len(groups),
                "groups": shown,
                "bulk_replace": body,
                "command": (
                    f"mammoth view transform bulk-replace {scope.view_id} "
                    f"--input {shlex.quote(json.dumps(body))}"
                ),
            }
        )
    return report


# -- target vs column ----------------------------------------------------------------------


def _target_report(
    scope: _Scope,
    target: str,
    names: list[str],
    facts: dict[str, dict[str, Any]],
    tables: dict[str, dict[Any, int] | None],
    total_rows: int,
    workers: int,
) -> dict[str, Any]:
    classes = _target_classes(target, tables, facts)
    positive = dp.choose_positive(classes)
    labeled = sum(classes.values())
    predictors = [n for n in names if n != target and int(facts[n].get("distinct") or 0) > 1]
    skipped: list[dict[str, Any]] = []

    def one(name: str) -> dict[str, Any] | None:
        group = _predictor_group(scope, name, facts[name])
        if group is None:
            skipped.append({"column": name, "reason": f"{facts[name]['distinct']} distinct values"})
            return None
        rows = scope.rows(
            aggregations=[_COUNT], group_by=[group, scope.internal[target]], limit=None
        )
        cells = [(r.get("group_0"), r.get("group_1"), r.get("agg_0") or 0) for r in rows]
        found = dp.association([c for c in cells if not dp.is_blank(c[1])], positive, labeled)
        return {"column": name, **found} if found else None

    ranked = dp.rank_associations(
        [item for item in _map_all(workers, one, predictors) if item], _ASSOCIATION_LIMIT
    )
    return {
        "column": target,
        "rows_with_target": labeled,
        "rows_without_target": total_rows - labeled,
        "classes": [
            {"value": value, "rows": rows, "share": round(rows / labeled, 4)}
            for value, rows in sorted(classes.items(), key=lambda item: -item[1])
        ],
        "positive": positive,
        "positive_rate": round(classes[positive] / labeled, 4),
        "positive_rule": "the rarest class of the target",
        "association": ranked,
        "skipped": skipped,
        "method": (
            "cramers_v: 0 = the column says nothing about the target, 1 = it decides it; it "
            "rises with the number of distinct values, so compare columns of similar cardinality "
            "and read 'signals' (rate = share of that value's rows in the positive class)"
        ),
    }


def _target_classes(
    target: str,
    tables: dict[str, dict[Any, int] | None],
    facts: dict[str, dict[str, Any]],
) -> dict[Any, int]:
    table = tables.get(target)
    classes = {k: v for k, v in (table or {}).items() if not dp.is_blank(k)}
    if not 2 <= len(classes) <= dp.MAX_TARGET_CLASSES:
        raise CliError(
            code=CODE_INVALID_ARGUMENTS,
            message=(
                f"target {target!r} has {facts[target].get('distinct')} distinct values; "
                f"a target needs between 2 and {dp.MAX_TARGET_CLASSES}."
            ),
            exit_status=EXIT_USAGE,
        )
    return classes


def _predictor_group(scope: _Scope, name: str, fact: dict[str, Any]) -> Any:
    """The group-by entry for a predictor: itself, bucketed when a wide NUMERIC, else None."""
    distinct = int(fact.get("distinct") or 0)
    if distinct <= _BUCKET_ABOVE_DISTINCT:
        return scope.internal[name]
    if scope.types.get(name) == "NUMERIC":
        return {"column": scope.internal[name], "resolution": "AUTO"}
    return None
