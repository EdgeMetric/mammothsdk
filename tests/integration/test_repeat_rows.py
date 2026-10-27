"""Integration tests for ``View.repeat_rows``: each asserts the rows the step leaves.

Target: release.mammoth.io (``MM_REL_*`` credentials; skipped without them).
Dataset used: employee.csv, as in ``test_transformations.py``.

Run:
    pytest tests/integration/test_repeat_rows.py -v
"""

from __future__ import annotations

import pytest

from mammoth import (
    ColumnType,
    DateDelta,
    RepeatOrder,
    RepeatSeries,
    View,
)

# The session fixtures open the client's connection pool; tests must share their loop.
pytestmark = pytest.mark.asyncio(loop_scope="session")

_PAGE = 10_000
_HASH_KEY = "hash"


async def _rows(view: View, columns: list[str] | None = None) -> list[dict[str, object]]:
    """Every row of the view, paged (``paging.total`` is unreliable)."""
    rows: list[dict[str, object]] = []
    offset = 1
    while True:
        page = (await view.data(columns=columns, limit=_PAGE, offset=offset))["data"]
        rows.extend(page)
        if len(page) < _PAGE:
            return rows
        offset += _PAGE


async def _values(view: View, column: str) -> list[str]:
    """The values of one column, one per row, as text."""
    return [
        str(value)
        for row in await _rows(view, [column])
        for key, value in row.items()
        if key != _HASH_KEY
    ]


class TestRepeatRows:
    async def test_times_multiplies_the_rows(self, view):
        before = len(await _rows(view))

        await view.repeat_rows(times=3)

        assert len(await _rows(view)) == before * 3

    async def test_values_make_one_copy_per_value_in_a_new_column(self, view):
        before = len(await _rows(view))

        await view.repeat_rows(
            values=["North", "South"], new_column="Zone", new_column_type=ColumnType.TEXT
        )

        zones = await _values(view, "Zone")
        assert len(zones) == before * 2
        assert zones.count("North") == before
        assert zones.count("South") == before

    async def test_keep_original_adds_the_values_to_the_rows_as_they_were(self, view):
        before = await _values(view, "department")

        await view.repeat_rows(
            values=["Marker"],
            existing_column="department",
            keep_original=True,
            order=RepeatOrder.GROUPED,
        )

        after = await _values(view, "department")
        assert len(after) == len(before) * 2
        assert after.count("Marker") == len(before)
        assert sorted(v for v in after if v != "Marker") == sorted(before)

    async def test_number_series_makes_one_copy_per_step(self, view):
        before = len(await _rows(view))

        await view.repeat_rows(series=RepeatSeries(1, 4, step=1), new_column="Step")

        steps = await _values(view, "Step")
        assert len(steps) == before * 4
        assert {float(step) for step in steps} == {1.0, 2.0, 3.0, 4.0}

    async def test_date_series_makes_one_copy_per_month(self, view):
        before = len(await _rows(view))

        await view.repeat_rows(
            series=RepeatSeries("2026-01-01", "2026-03-31", delta=DateDelta(months=1)),
            new_column="Month",
        )

        months = await _values(view, "Month")
        assert len(months) == before * 3
        assert sorted({month[:7] for month in months}) == ["2026-01", "2026-02", "2026-03"]
