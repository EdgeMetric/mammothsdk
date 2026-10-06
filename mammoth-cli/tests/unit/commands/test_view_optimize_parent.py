"""A DATASET_ID that is not the view's parent is refused with the real one named."""

from __future__ import annotations

import pytest

from mammoth_cli.commands.view import _check_parent_matches
from mammoth_cli.errors.envelope import CliError


def test_a_dataset_that_is_not_the_views_parent_is_refused() -> None:
    with pytest.raises(CliError) as refused:
        _check_parent_matches(5224, given=5214, real=5199)
    assert refused.value.message == "view 5224 belongs to dataset 5199, not 5214"
    assert refused.value.details["dataset_id"] == 5199


def test_the_views_own_dataset_passes() -> None:
    _check_parent_matches(5224, given=5199, real=5199)
