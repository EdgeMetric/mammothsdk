"""The gaps of a read-back's wait: short first, growing, capped, and the same total as before."""

from __future__ import annotations

import pytest

from mammoth_cli.services.poll import poll_delays


def test_the_gaps_start_at_a_tenth_of_a_second_and_grow_to_the_cap() -> None:
    gaps = list(poll_delays(total=20, cap=0.5))

    assert gaps[0] == 0.1
    assert gaps[:5] == pytest.approx([0.1, 0.15, 0.225, 0.3375, 0.5])
    assert max(gaps) == 0.5


def test_the_gaps_add_up_to_the_total_the_fixed_sleeps_made() -> None:
    assert sum(poll_delays(total=20, cap=0.5)) == pytest.approx(20)
    assert sum(poll_delays(total=10, cap=2.0)) == pytest.approx(10)
