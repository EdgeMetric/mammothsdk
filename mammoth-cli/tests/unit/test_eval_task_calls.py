"""The offline call-count eval for the task layer (#309): recipes take fewer calls."""

from __future__ import annotations

import sys
from pathlib import Path

CLI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CLI_ROOT / "scripts"))

import eval_task_calls as evaluation  # noqa: E402


def test_every_task_is_one_call_with_its_recipe() -> None:
    rows = evaluation.tasks()
    assert len(rows) >= 20
    assert {row.recipe for row in rows} == {1}
    assert all(row.recipe_preview == (2 if row.writes else 1) for row in rows)


def test_a_recipe_never_takes_more_calls_than_the_steps_it_replaces() -> None:
    for row in evaluation.tasks():
        assert row.recipe_preview <= row.manual, row
        assert row.manual <= row.manual_lookups, row
        # Each line of the one call is a command the prose steps name, so it is a step saved.
        assert row.lines <= row.manual + 1, row


def test_the_tasks_take_fewer_calls_in_total() -> None:
    rows = evaluation.tasks()
    assert sum(row.recipe_preview for row in rows) < sum(row.manual for row in rows)
    assert sum(1 for row in rows if row.recipe_preview < row.manual) >= len(rows) // 2


def test_the_committed_table_is_current() -> None:
    assert evaluation.main(["--check"]) == 0
    assert evaluation.DOC.read_text(encoding="utf-8") == evaluation.render(evaluation.tasks())
