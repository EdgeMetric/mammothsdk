"""Whole-view column profile: pure computation over backend aggregate results.

``view data profile`` asks the backend for whole-column aggregates (never a
page of rows) and hands the answers to these functions. Nothing here talks to
the network, so every rule is testable on plain values:

* per-column summary (nulls, distinct, min/max, top values);
* spelling-variant groups that know legal forms (Ltd = Limited, Inc =
  Incorporated, ...) and emit a ready ``bulk-replace`` mapping;
* target-vs-column association from a contingency table (Cramer's V, rate by
  value, blank-vs-filled rate).
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

#: Distinct values above which a column's values are not listed or grouped.
MAX_LISTED_DISTINCT = 5000
#: Longest target (distinct classes) association is computed for.
MAX_TARGET_CLASSES = 20
#: A value needs this many rows (or this share of all rows) to be a "signal".
MIN_SIGNAL_ROWS = 30
MIN_SIGNAL_SHARE = 0.005
TOP_SIGNALS = 3

BLANK = "(blank)"

_LEGAL_FORMS: dict[str, str] = {
    "limited": "ltd",
    "ltd": "ltd",
    "incorporated": "inc",
    "inc": "inc",
    "corporation": "corp",
    "corp": "corp",
    "company": "co",
    "co": "co",
    "plc": "plc",
    "llc": "llc",
    "llp": "llp",
    "lp": "lp",
    "gmbh": "gmbh",
    "pvt": "pvt",
    "private": "pvt",
    "pty": "pty",
    "proprietary": "pty",
    "sarl": "sarl",
    "srl": "srl",
    "bv": "bv",
    "nv": "nv",
}
#: Dropped by :func:`loose_key` only: every legal form, the Spanish/Portuguese
#: ``SA`` and the connector ``DE`` (``SIGMA-ALDRICH DE ARGENTINA``).
_LOOSE_DROP = frozenset({*_LEGAL_FORMS.values(), "sa", "de"})
_DOTTED_INITIALS = re.compile(r"(?<=\b\w)\.(?=\w\b)")
_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)


def is_blank(value: Any) -> bool:
    """A NULL or a text with nothing but whitespace."""
    return value is None or (isinstance(value, str) and not value.strip())


def spelling_key(text: str) -> str:
    """Grouping key: case, punctuation, ``&``/and and legal-form spellings folded.

    ``Acme Ltd.``, ``ACME Limited`` and ``Acme  L.T.D`` share a key; ``Acme``
    (no legal form) and ``Acme Holdings`` do not -- this is normalisation, not
    fuzzy matching.
    """
    lowered = text.casefold().replace("&", " and ")
    dotted = _DOTTED_INITIALS.sub("", lowered)
    tokens = [token for token in _NON_WORD.split(dotted) if token]
    return " ".join(_LEGAL_FORMS.get(token, token) for token in tokens)


def loose_key(text: str) -> str:
    """:func:`spelling_key` without legal forms and connector words.

    ``TECNOLAB``, ``TECNOLAB S.A.`` and ``SIGMA-ALDRICH DE ARGENTINA SRL`` /
    ``SIGMA-ALDRICH ARGENTINA S.A.`` share a key; ``Acme`` and ``Acme Holdings``
    still do not. Too loose to merge on its own: it only proposes.
    """
    tokens = spelling_key(text).split()
    kept = [token for token in tokens if token not in _LOOSE_DROP]
    return " ".join(kept or tokens)


def variant_groups(counts: Mapping[str, int]) -> list[dict[str, Any]]:
    """Groups of distinct spellings that share :func:`spelling_key`, most rows first.

    Each group names the spelling to keep (the most frequent, ties broken by
    the shorter then alphabetical spelling) and every variant with its count.
    """
    return _grouped(counts, spelling_key, lambda spellings: len(spellings) >= 2)


def likely_groups(counts: Mapping[str, int]) -> list[dict[str, Any]]:
    """Groups that differ only by a legal form or a connector word (:func:`loose_key`).

    Only groups the sure :func:`variant_groups` do not already make on their own:
    their spellings span two or more :func:`spelling_key` s. A person confirms
    these before they are merged (``SRL`` and ``SA`` can be two companies).
    """
    return _grouped(
        counts, loose_key, lambda spellings: len({spelling_key(t) for t in spellings}) >= 2
    )


def _grouped(
    counts: Mapping[str, int],
    key: Callable[[str], str],
    is_group: Callable[[list[str]], bool],
) -> list[dict[str, Any]]:
    by_key: dict[str, list[str]] = defaultdict(list)
    for value in counts:
        if isinstance(value, str) and not is_blank(value):
            by_key[key(value)].append(value)
    groups: list[dict[str, Any]] = []
    for spellings in by_key.values():
        if not is_group(spellings):
            continue
        keep = min(spellings, key=lambda text: (-counts[text], len(text), text))
        groups.append(
            {
                "keep": keep,
                "rows": sum(counts[text] for text in spellings),
                "variants": [
                    {"value": text, "count": counts[text]}
                    for text in sorted(spellings, key=lambda text: (-counts[text], text))
                ],
            }
        )
    return sorted(groups, key=lambda group: (-group["rows"], group["keep"]))


def bulk_replace_input(column: str, groups: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The ``view transform bulk-replace`` ``--input`` that merges every group."""
    return {
        "columns": [column],
        "mapping": [
            {
                "search": [v["value"] for v in group["variants"] if v["value"] != group["keep"]],
                "replace": group["keep"],
            }
            for group in groups
        ],
        "match_case": True,
        "match_words": False,
    }


def value_counts(rows: Iterable[Mapping[str, Any]], key: str, count_key: str) -> dict[Any, int]:
    """``{value: rows}`` from grouped result rows; a NULL group keeps the key ``None``."""
    counts: dict[Any, int] = defaultdict(int)
    for row in rows:
        counts[row.get(key)] += int(row.get(count_key) or 0)
    return dict(counts)


def summarize_column(counts: Mapping[Any, int], total_rows: int, top: int) -> dict[str, Any]:
    """Blank count and share plus the ``top`` most frequent values of a full value table."""
    blank = sum(count for value, count in counts.items() if is_blank(value))
    ranked = sorted(
        ((value, count) for value, count in counts.items() if not is_blank(value)),
        key=lambda item: (-item[1], str(item[0])),
    )
    return {
        "nulls": blank,
        "null_share": _share(blank, total_rows),
        "top_values": [
            {"value": value, "count": count, "share": _share(count, total_rows)}
            for value, count in ranked[:top]
        ],
    }


def _share(part: int, whole: int) -> float:
    return round(part / whole, 4) if whole else 0.0


def choose_positive(class_totals: Mapping[Any, int]) -> Any:
    """The target class rates are reported for: the minority class of a binary target."""
    return min(class_totals, key=lambda value: (class_totals[value], str(value)))


def association(
    cells: Iterable[tuple[Any, Any, int]], positive: Any, total_rows: int
) -> dict[str, Any] | None:
    """Target-vs-column association from ``(column value, target class, rows)`` cells.

    Returns Cramer's V (0 = unrelated, 1 = the column decides the target),
    the blank-vs-filled target rate, and the values whose rate differs most
    from the overall rate among values with enough rows to trust. ``None``
    when the table has fewer than two values or classes.
    """
    table: dict[Any, dict[Any, int]] = defaultdict(lambda: defaultdict(int))
    for value, target, rows in cells:
        table[BLANK if is_blank(value) else value][target] += int(rows)
    classes = sorted({target for row in table.values() for target in row}, key=str)
    if len(table) < 2 or len(classes) < 2:
        return None
    n = sum(sum(row.values()) for row in table.values())
    base = sum(row.get(positive, 0) for row in table.values()) / n if n else 0.0
    return {
        "cramers_v": round(_cramers_v(table, classes, n), 4),
        "blank_vs_filled": _blank_vs_filled(table, positive),
        "signals": _signals(table, positive, base, total_rows),
    }


def _cramers_v(table: Mapping[Any, Mapping[Any, int]], classes: list[Any], n: int) -> float:
    class_totals = {c: sum(row.get(c, 0) for row in table.values()) for c in classes}
    chi2 = 0.0
    for row in table.values():
        row_total = sum(row.values())
        for target in classes:
            expected = row_total * class_totals[target] / n
            if expected:
                chi2 += (row.get(target, 0) - expected) ** 2 / expected
    dof = min(len(table) - 1, len(classes) - 1)
    return math.sqrt(chi2 / (n * dof)) if n and dof else 0.0


def _blank_vs_filled(
    table: Mapping[Any, Mapping[Any, int]], positive: Any
) -> dict[str, Any] | None:
    blank = table.get(BLANK)
    if not blank:
        return None
    filled = [row for value, row in table.items() if value != BLANK]
    blank_rows = sum(blank.values())
    filled_rows = sum(sum(row.values()) for row in filled)
    return {
        "blank_rows": blank_rows,
        "blank_rate": _share(blank.get(positive, 0), blank_rows),
        "filled_rows": filled_rows,
        "filled_rate": _share(sum(row.get(positive, 0) for row in filled), filled_rows),
    }


def _signals(
    table: Mapping[Any, Mapping[Any, int]], positive: Any, base: float, total_rows: int
) -> list[dict[str, Any]]:
    floor = max(MIN_SIGNAL_ROWS, MIN_SIGNAL_SHARE * total_rows)
    found: list[dict[str, Any]] = []
    for value, row in table.items():
        rows = sum(row.values())
        if rows < floor:
            continue
        rate = row.get(positive, 0) / rows
        found.append(
            {
                "value": value,
                "rows": rows,
                "rate": round(rate, 4),
                "lift": round(rate / base, 2) if base else None,
            }
        )
    found.sort(key=lambda item: (-abs(item["rate"] - base) * item["rows"], str(item["value"])))
    return found[:TOP_SIGNALS]


def rank_associations(items: Sequence[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Columns ordered by Cramer's V, strongest first, capped at ``limit``."""
    return sorted(items, key=lambda item: -item["cramers_v"])[:limit]


def standardized_difference(
    positive: Mapping[str, float | None], rest: Mapping[str, float | None]
) -> float | None:
    """Cohen's d of a NUMERIC column between two groups from ``{n, mean, stddev}`` each.

    Positive when the column runs higher in the positive class. ``None`` when a
    group is too small or the pooled spread is zero, so nothing is invented.
    """
    n1, n0 = positive.get("n"), rest.get("n")
    m1, m0 = positive.get("mean"), rest.get("mean")
    s1, s0 = positive.get("stddev"), rest.get("stddev")
    if n1 is None or n0 is None or m1 is None or m0 is None or s1 is None or s0 is None:
        return None
    if n1 < 2 or n0 < 2:
        return None
    pooled = math.sqrt(((n1 - 1) * s1**2 + (n0 - 1) * s0**2) / (n1 + n0 - 2))
    return round((m1 - m0) / pooled, 4) if pooled else None
