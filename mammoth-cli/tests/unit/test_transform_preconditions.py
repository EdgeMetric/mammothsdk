"""Every transform's schema preconditions name the read to run before it."""

from __future__ import annotations

import json

import pytest

from mammoth_cli.testing import make_runner

TRANSFORMS = (
    "add-column convert-type copy-columns discard-duplicates extract-date fill-missing filter "
    "increment-date join limit-rows lookup math set-values small-large split substring text "
    "unnest window"
).split()


@pytest.mark.parametrize("name", TRANSFORMS)
def test_schema_get_preconditions_start_with_an_observe_first_read(name: str) -> None:
    result = make_runner().invoke(["schema", "get", f"view.transform.{name}", "--output", "json"])
    assert result.exit_code == 0, result.output
    text = json.dumps(json.loads(result.output))
    assert "Observe first:" in text
