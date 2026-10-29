"""A refused task write keeps the keys the SDK named when the CLI rebuilds the message."""

from __future__ import annotations

from mammoth.api.pipeline import _task_params_rejection
from mammoth.exceptions import MammothAPIError

from mammoth_cli.services.mapping import map_sdk_exception


def test_the_cli_message_names_the_rejected_task_keys() -> None:
    refusal = MammothAPIError(
        "API request failed: Validation error",
        status_code=400,
        response_body={
            "message": "Validation error",
            "details": {
                "extra": [{"key": "patches.0", "message": "value must be of type AddTaskSpec"}]
            },
        },
    )
    rebuilt = _task_params_rejection(refusal, {"SQL": {}, "BOGUS_KEY": 1})

    error = map_sdk_exception(rebuilt)

    assert "keys sent beyond those: ['BOGUS_KEY', 'SQL']" in error.message
    assert error.details["rejected_task_keys"] == ["BOGUS_KEY", "SQL"]
