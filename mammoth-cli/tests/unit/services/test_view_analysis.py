"""``view analyze`` id parsing."""

from __future__ import annotations

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.view_analysis import view_ids


def test_a_dashboard_trace_of_16_views_fits_one_call() -> None:
    """mammothsdk#381 item 9: 16 views needed two calls at a cap of 12."""
    raw = ",".join(str(view_id) for view_id in range(308580, 308596))
    assert view_ids(raw) == list(range(308580, 308596))


def test_a_pasted_list_past_the_cap_is_still_refused() -> None:
    with pytest.raises(CliError) as caught:
        view_ids(",".join(str(view_id) for view_id in range(1, 52)))
    assert caught.value.code == "too_many_ids"
