"""``key_overlap``: the pure match-rate arithmetic behind ``view transform join --dry-run``."""

from __future__ import annotations

from mammoth_cli.commands.view import key_overlap


def test_key_overlap_weights_rows_and_treats_blank_keys_as_unmatched() -> None:
    out = key_overlap({"a": 6, "b": 2, None: 1, "": 1}, {"a": 1})
    assert out["match_rate"] == 0.6
    assert out["unmatched_rows"] == 4
    assert out["unmatched_keys"] == ["b", "None", ""]


def test_key_overlap_of_an_empty_view_has_no_rate() -> None:
    assert key_overlap({}, {"a": 1})["match_rate"] is None
