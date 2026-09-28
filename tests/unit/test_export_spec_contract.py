"""What the add-export route takes, held to the route as it stands.

Two properties the route defaults for itself were required here, and the one
rule the route states about `sequence` was not stated here at all.
"""

import pytest
from pydantic import ValidationError

from mammoth.models.exports import AddExportSpec, HandlerType, TriggerType


def _spec(**overrides: object) -> AddExportSpec:
    fields: dict[str, object] = {
        "DATAVIEW_ID": 11,
        "handler_type": HandlerType.INTERNAL_DATASET,
        "trigger_type": TriggerType.PIPELINE,
        "run_immediately": True,
    }
    return AddExportSpec(**(fields | overrides))  # type: ignore[arg-type]


def test_an_export_that_names_no_properties_is_accepted() -> None:
    # The route defaults both to an empty object; a destination that needs
    # none — an internal dataset, say — sends neither.
    spec = _spec()

    assert spec.target_properties == {}
    assert spec.additional_properties == {}


def test_an_export_partway_down_the_pipeline_must_say_where() -> None:
    with pytest.raises(ValidationError, match="[Ss]equence"):
        _spec(end_of_pipeline=False)


def test_a_sequence_before_the_start_of_the_pipeline_is_refused() -> None:
    with pytest.raises(ValidationError, match="[Ss]equence"):
        _spec(end_of_pipeline=False, sequence=-1)


def test_an_export_before_the_first_step_is_accepted() -> None:
    assert _spec(end_of_pipeline=False, sequence=0).sequence == 0


def test_an_export_at_the_end_needs_no_sequence() -> None:
    assert _spec().sequence is None
