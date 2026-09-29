"""The volatile query's display properties: a real SORT before the LIMIT."""

from __future__ import annotations

import pytest

from mammoth.api.dataviews import _build_query_display_properties
from mammoth.exceptions import MammothValidationError


def test_sort_is_sent_as_upper_case_pairs_alongside_the_limit() -> None:
    display = _build_query_display_properties(5, [["agg_0", "desc"], ["group_0", "ASC"]])
    assert display == {"LIMIT": 5, "SORT": [["agg_0", "DESC"], ["group_0", "ASC"]]}


def test_no_limit_and_no_sort_sends_nothing() -> None:
    assert _build_query_display_properties(None, None) == {}


def test_a_limit_alone_is_unchanged() -> None:
    assert _build_query_display_properties(10, None) == {"LIMIT": 10}


@pytest.mark.parametrize(
    "sort",
    [
        [["agg_0", "sideways"]],
        [["agg_0"]],
        [["a", "ASC"], ["b", "ASC"], ["c", "ASC"], ["d", "ASC"]],
    ],
)
def test_a_sort_the_backend_would_reject_fails_before_the_request(sort: list[list[str]]) -> None:
    with pytest.raises(MammothValidationError):
        _build_query_display_properties(3, sort)
