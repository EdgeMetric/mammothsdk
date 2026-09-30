"""``view data profile``: what is in this view, over ALL its rows.

Read-only. Per-column nulls, distinct counts and min/max come from the stats
the backend already stored for the view (``view ai profile`` action ``stats``,
see :mod:`mammoth_cli.services.stored_stats`) when they are current -- their
row count equals the view's now -- and from a few multi-column pivots
otherwise. Only what is not stored is queried: value tables for TEXT columns
(spelling variants, top values) and the target comparison (two multi-column
pivots for the NUMERIC columns, one grouped count per categorical column).
The result says which figures came from which. The arithmetic lives in
:mod:`mammoth_cli.services.data_profile`.
"""

from __future__ import annotations

import json
import shlex
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
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
from mammoth_cli.services import stored_stats
from mammoth_cli.services.conditions import compile_condition

HandlerResult = tuple[Any, dict[str, Any]]

_AGGREGATE = "mammoth.api.dataviews.DataviewsAPI.aggregate"
_STORED_STATS = "mammoth.api.ai.AIAPI.generate_profile"
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
    jobs: list[str] = field(default_factory=list)

    def rows(self, **fields: Any) -> list[dict[str, Any]]:
        """Run one aggregate job and return its result rows."""
        self.jobs.append("aggregate")
        result = self.service.call(
            _AGGREGATE,
            dataset_id=self.dataset_id,
            dataview_id=self.view_id,
            project_id=self.project_id,
            **fields,
        )
        rows = result.get("data") if isinstance(result, dict) else None
        return [row for row in rows or [] if isinstance(row, dict)]


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
    """Read the stored stats, query the rest, and assemble the result."""
    names = _selected_columns(scope, document)
    target = document.get("target")
    if target is not None and target not in scope.types:
        raise _usage(f"target column {target!r} is not in the view", sorted(scope.types))
    profiled = list(dict.fromkeys([*names, *([target] if target else [])]))
    live_rows = _live_rows(scope)
    facts, sources = _facts(scope, profiled, live_rows)
    wanted = _table_columns(scope, facts, names, target, "columns" in document)
    tables = _value_tables(scope, wanted, workers)
    top = int(document.get("top", _DEFAULT_TOP))
    details = {
        name: _detail(name, scope, facts[name], tables, live_rows, top, sources["stored_columns"])
        for name in names
    }
    variants, variants_checked, variants_skipped = _variant_report(scope, names, tables)
    result: dict[str, Any] = {
        "view_id": scope.view_id,
        "dataset_id": scope.dataset_id,
        "row_count": live_rows,
        "summary": _summary(details, live_rows),
        **_paged_columns(details, int(document.get("limit", _DEFAULT_DETAIL_LIMIT))),
        "spelling_variants": variants,
        "spelling_variants_checked": variants_checked,
        "spelling_variants_skipped": variants_skipped,
    }
    if target:
        result["target"] = _target_report(
            scope, str(target), names, facts, tables, live_rows, workers
        )
    result["sources"] = _sources_block(scope, sources, live_rows)
    return result


def _live_rows(scope: _Scope) -> int:
    rows = scope.rows(aggregations=[_COUNT])
    return int(rows[0].get("agg_0") or 0) if rows else 0


def _facts(
    scope: _Scope, names: list[str], live_rows: int
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Per-column facts: stored stats while current, a fresh pivot for the rest."""
    stored, info = _read_stored(scope, live_rows)
    usable = {n: f for n, f in stored.items() if n in names} if info.get("current") else {}
    facts = dict(usable)
    missing = [n for n in names if n not in facts]
    if missing:
        facts.update(_column_facts(scope, missing)[1])
    return facts, {**info, "stored_columns": set(usable), "queried_columns": missing}


def _read_stored(scope: _Scope, live_rows: int) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """The backend's stored stats and whether they match the view as it is now."""
    try:
        payload = scope.service.call(
            _STORED_STATS,
            dataview_id=scope.view_id,
            dataset_id=scope.dataset_id,
            action="stats",
        )
    except CliError as error:
        return {}, {"current": False, "reason": f"stored stats unavailable: {error.message}"}
    facts, stored_rows = stored_stats.stored_facts(payload, scope.internal)
    return facts, {"stored_rows": stored_rows, **stored_stats.currency(stored_rows, live_rows)}


def _sources_block(scope: _Scope, sources: dict[str, Any], live_rows: int) -> dict[str, Any]:
    stored = sorted(sources["stored_columns"])
    return {
        "stored_stats": {
            "columns": len(stored),
            "used": bool(stored),
            "live_rows": live_rows,
            **{
                k: v
                for k, v in sources.items()
                if k in ("stored_rows", "current", "reason", "note")
            },
            "as_of": "not recorded by the backend",
        },
        "queried": {
            "columns_without_stored_stats": len(sources["queried_columns"]),
            "backend_jobs": len(scope.jobs),
        },
        "how_to_read": (
            "Each column's 'from' says 'stored' (backend stats) or 'query' (aggregate run now). "
            "top values, spelling variants and the target comparison are always queried; "
            "stored 'sample' values are a few values, not the most frequent."
        ),
    }


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


# -- value tables: one grouped count per column that needs its values -------------------------


def _table_columns(
    scope: _Scope,
    facts: dict[str, dict[str, Any]],
    names: list[str],
    target: Any,
    explicit: bool,
) -> list[str]:
    """Columns whose values must be listed: target, named columns, TEXT with variants."""
    wanted: list[str] = []
    for name, fact in facts.items():
        distinct = int(fact.get("distinct") or 0)
        if not 2 <= distinct <= dp.MAX_LISTED_DISTINCT and name != target:
            continue
        if name == target or (name in names and (explicit or scope.types.get(name) == "TEXT")):
            wanted.append(name)
    return wanted


def _value_tables(
    scope: _Scope, names: list[str], workers: int
) -> dict[str, dict[Any, int] | None]:
    """``{column: {value: rows}}``; ``None`` when the column has too many values to list."""

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


# -- per-column detail and summary -----------------------------------------------------


def _detail(
    name: str,
    scope: _Scope,
    fact: dict[str, Any],
    tables: dict[str, dict[Any, int] | None],
    total_rows: int,
    top: int,
    stored: set[str],
) -> dict[str, Any]:
    distinct = int(fact.get("distinct") or 0)
    detail: dict[str, Any] = {"column": name, "type": scope.types.get(name), "distinct": distinct}
    detail["from"] = "stored" if name in stored else "query"
    if "min" in fact:
        detail.update(min=fact["min"], max=fact["max"])
    table = tables.get(name)
    if table is not None:
        summary = dp.summarize_column(table, total_rows, top)
        detail.update(nulls=summary["nulls"], top=_top_text(summary["top_values"]))
        detail["nulls_from"] = detail["top_from"] = "query"
    else:
        detail.update(nulls=_nulls(scope, name, fact, distinct, total_rows))
        if fact.get("sample"):
            detail["sample"] = [str(v) for v in fact["sample"][:top]]
        if distinct and distinct == total_rows:
            detail["note"] = "every value is different"
        elif table is None and name in tables:
            detail["note"] = f"{distinct} distinct values, not listed"
    return detail


def _nulls(
    scope: _Scope, name: str, fact: dict[str, Any], distinct: int, total_rows: int
) -> int | None:
    """Blank count from the stats; ``None`` (not guessed) when only a per-column job could tell."""
    if "nulls" in fact:
        return int(fact["nulls"])
    if distinct == 0:
        return total_rows
    return 0 if distinct == total_rows else None


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
            if d["distinct"] > 0 and (d.get("nulls") or 0) * 2 >= total_rows
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
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, str]]]:
    """Per TEXT column, spellings of one value (Ltd/Limited, case, punctuation) and the fix.

    ``likely_groups`` are names that differ only by a legal form or a connector
    (``TECNOLAB`` / ``TECNOLAB S.A.``): proposed, never merged without a yes.
    Also returns the columns that were checked and ``{column, reason}`` for each
    that was not, so an empty report never reads as "no variants" for a column
    whose values were never compared.
    """
    report: list[dict[str, Any]] = []
    checked: list[str] = []
    skipped: list[dict[str, str]] = []
    for name in names:
        reason = _variant_skip_reason(scope, name, tables)
        if reason:
            skipped.append({"column": name, "reason": reason})
            continue
        checked.append(name)
        texts = {k: v for k, v in (tables[name] or {}).items() if isinstance(k, str)}
        groups, likely = dp.variant_groups(texts), dp.likely_groups(texts)
        if not groups and not likely:
            continue
        entry: dict[str, Any] = {"column": name, **_merge_fix(scope, name, groups)}
        if likely:
            entry["likely_groups"] = {"note": _LIKELY_NOTE, **_merge_fix(scope, name, likely)}
        report.append(entry)
    return report, checked, skipped


def _variant_skip_reason(
    scope: _Scope, name: str, tables: dict[str, dict[Any, int] | None]
) -> str | None:
    """Why ``name``'s spellings were not compared, or ``None`` when they were."""
    column_type = scope.types.get(name)
    if column_type != "TEXT":
        return f"type is {column_type}, not TEXT"
    if name not in tables:
        return "values not listed (fewer than 2 distinct values, or too many to list)"
    if tables[name] is None:
        return f"more than {dp.MAX_LISTED_DISTINCT} distinct values, too many to compare"
    return None


_LIKELY_NOTE = (
    "Same name apart from a legal form or a connector word; confirm with the user "
    "before merging (SRL and SA can be two companies)."
)


def _merge_fix(scope: _Scope, column: str, groups: list[dict[str, Any]]) -> dict[str, Any]:
    """The groups shown and the bulk-replace that merges them."""
    shown = groups[:_MAX_VARIANT_GROUPS]
    fix: dict[str, Any] = {"groups_total": len(groups), "groups": shown}
    if not shown:
        return fix
    body = {**dp.bulk_replace_input(column, shown), "dataset_id": scope.dataset_id}
    command = (
        f"mammoth view transform bulk-replace {scope.view_id} "
        f"--input {shlex.quote(json.dumps(body))}"
    )
    return {**fix, "bulk_replace": body, "command": command}


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
    numeric = [n for n in predictors if scope.types.get(n) == "NUMERIC"]
    others = [n for n in predictors if n not in numeric]
    skipped: list[dict[str, Any]] = []
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
        "association": {
            "categorical": _categorical(
                scope, target, others, facts, (positive, labeled), workers, skipped
            ),
            "numeric": _numeric_effects(scope, target, positive, numeric, workers),
        },
        "skipped": skipped,
        "method": (
            "categorical: cramers_v (0 = the column says nothing about the target, 1 = it decides "
            "it; rises with distinct values, so compare columns of similar cardinality) and "
            "'signals' (rate = share of that value's rows in the positive class), one grouped "
            "count per column. numeric: standardized_difference (Cohen's d, positive = higher "
            "in the positive class) from two multi-column pivots (mean, stddev per class); blank "
            "rates are not compared for numeric columns."
        ),
    }


def _categorical(
    scope: _Scope,
    target: str,
    names: list[str],
    facts: dict[str, dict[str, Any]],
    class_info: tuple[Any, int],
    workers: int,
    skipped: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    positive, labeled = class_info

    def one(name: str) -> dict[str, Any] | None:
        group = _predictor_group(scope, name, facts[name])
        if group is None:
            skipped.append({"column": name, "reason": f"{facts[name]['distinct']} distinct values"})
            return None
        rows = scope.rows(aggregations=[_COUNT], group_by=[group, scope.internal[target]])
        cells = [(r.get("group_0"), r.get("group_1"), r.get("agg_0") or 0) for r in rows]
        found = dp.association([c for c in cells if not dp.is_blank(c[1])], positive, labeled)
        return {"column": name, **found} if found else None

    found = [item for item in _map_all(workers, one, names) if item]
    return dp.rank_associations(found, _ASSOCIATION_LIMIT)


def _numeric_effects(
    scope: _Scope, target: str, positive: Any, names: list[str], workers: int
) -> list[dict[str, Any]]:
    """Mean and spread of every NUMERIC column in the positive class vs the rest."""
    batches = [names[i : i + _TOTALS_BATCH] for i in range(0, len(names), _TOTALS_BATCH)]
    results: list[dict[str, Any]] = []
    for batch in batches:
        groups = {
            "positive": _group_moments(scope, target, positive, "EQ", batch),
            "rest": _group_moments(scope, target, positive, "NE", batch),
        }
        for name in batch:
            d = dp.standardized_difference(groups["positive"][name], groups["rest"][name])
            if d is not None:
                results.append(
                    {
                        "column": name,
                        "standardized_difference": d,
                        "mean_positive": groups["positive"][name]["mean"],
                        "mean_rest": groups["rest"][name]["mean"],
                    }
                )
    results.sort(key=lambda item: -abs(item["standardized_difference"]))
    return results[:_ASSOCIATION_LIMIT]


def _group_moments(
    scope: _Scope, target: str, positive: Any, operator: str, names: list[str]
) -> dict[str, dict[str, float | None]]:
    """``{column: {n, mean, stddev}}`` over the rows where the target is / is not ``positive``."""
    aggregations: list[dict[str, Any]] = [_COUNT]
    for name in names:
        column = scope.internal[name]
        aggregations.append({"function": "AVG", "column": column, "as_name": "m"})
        aggregations.append({"function": "STDDEV", "column": column, "as_name": "s"})
    condition = compile_condition({"column": target, "operator": operator, "value": positive})
    rows = scope.rows(
        aggregations=aggregations, condition=condition.build(scope.internal, scope.types)
    )
    row = rows[0] if rows else {}
    n = row.get("agg_0")
    return {
        name: {"n": n, "mean": row.get(f"agg_{1 + 2 * i}"), "stddev": row.get(f"agg_{2 + 2 * i}")}
        for i, name in enumerate(names)
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
    """The group-by entry for a categorical predictor, or None when it has too many values."""
    if int(fact.get("distinct") or 0) <= _BUCKET_ABOVE_DISTINCT:
        return scope.internal[name]
    return None
