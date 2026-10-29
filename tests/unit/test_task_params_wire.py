"""``add_task``, ``update_task`` and ``preview_task`` against a real local HTTP server.

A task read from ``list_tasks`` carries the keys the server wrote (``EXECUTION_TIMESTAMP``,
``TASK_NAMESPACE``); an older server counts each as a second transform param and refuses
the write. Each of the three writes must drop them from the body the server receives, and
keep every other key. A refusal rebuilt with the keys sent must keep every attribute the
request layer set on the original error.
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth.api.pipeline import _task_params_rejection
from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError, MammothAuthError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

PIPELINE = "/workspaces/1/projects/25654/datasets/500/dataviews/42/pipeline"
READ_BACK: dict[str, Any] = {
    "FILTER": {"CONDITION": {}},
    "TASK_KEY": "filter",
    "EXECUTION_TIMESTAMP": "20261028091500",
    "TASK_NAMESPACE": "abcde",
}


def _body(server: RecordingServer) -> Any:
    return server.requests[-1]["body"]


def _assert_server_keys_dropped(sent: dict[str, Any]) -> None:
    assert "EXECUTION_TIMESTAMP" not in sent
    assert "TASK_NAMESPACE" not in sent
    assert sent["FILTER"] == {"CONDITION": {}}
    assert sent["TASK_KEY"] == "filter"


async def test_add_task_sends_a_read_back_task_without_the_server_written_keys(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.pipeline.add_task(dataview_id=42, task_spec=READ_BACK, dataset_id=500)

    assert server.requests[-1]["method"] == "POST"
    assert server.requests[-1]["path"] == f"{PIPELINE}/tasks"
    sent = _body(server)
    _assert_server_keys_dropped(sent)
    assert sent["DATAVIEW_ID"] == 42


async def test_update_task_sends_an_edited_sql_read_back_with_its_task_key(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    """A `view task get` copy of a SQL task, with the query edited, goes back whole (#353)."""
    read_back = {
        "SQL": {"QUERY": "SELECT 1 AS a"},
        "TASK_KEY": "sql",
        "EXECUTION_TIMESTAMP": "20261028091500",
        "TASK_NAMESPACE": "abcde",
    }
    read_back["SQL"]["QUERY"] = "SELECT 2 AS a"

    await client.pipeline.update_task(
        dataview_id=42, task_id=7, task_spec=read_back, dataset_id=500
    )

    (patch,) = _body(server)["patches"]
    sent = patch["value"]
    assert "EXECUTION_TIMESTAMP" not in sent
    assert "TASK_NAMESPACE" not in sent
    assert sent["TASK_KEY"] == "sql"
    assert sent["SQL"] == {"QUERY": "SELECT 2 AS a"}


async def test_add_task_drops_the_keys_from_every_spec_of_a_list(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.pipeline.add_task(dataview_id=42, task_spec=[READ_BACK, READ_BACK], dataset_id=500)

    assert len(_body(server)) == 2
    for sent in _body(server):
        _assert_server_keys_dropped(sent)


async def test_update_task_sends_a_read_back_task_without_the_server_written_keys(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.pipeline.update_task(
        dataview_id=42, task_id=7, task_spec=READ_BACK, dataset_id=500
    )

    assert server.requests[-1]["method"] == "PATCH"
    assert server.requests[-1]["path"] == f"{PIPELINE}/tasks/7"
    (patch,) = _body(server)["patches"]
    assert patch["op"] == "replace"
    assert patch["path"] == "params"
    _assert_server_keys_dropped(patch["value"])


async def test_update_task_drops_the_keys_from_explicit_params_patches(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    patches = [
        {"op": "replace", "path": "params", "value": READ_BACK},
        {"op": "replace", "path": "summary", "value": "kept"},
    ]
    await client.pipeline.update_task(dataview_id=42, task_id=7, patches=patches, dataset_id=500)

    sent = _body(server)["patches"]
    _assert_server_keys_dropped(sent[0]["value"])
    assert sent[1] == {"op": "replace", "path": "summary", "value": "kept"}


async def test_preview_task_sends_a_read_back_task_without_the_server_written_keys(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.pipeline.preview_task(
        dataview_id=42, task_spec=READ_BACK, dataset_id=500, sample_size=25
    )

    assert server.requests[-1]["method"] == "POST"
    assert server.requests[-1]["path"] == f"{PIPELINE}/task_preview"
    assert server.requests[-1]["query"] == {"sample_size": "25"}
    _assert_server_keys_dropped(_body(server))


async def test_a_type_refusal_from_the_server_names_the_keys_sent(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"PATCH {PIPELINE}/tasks/7"] = (
        400,
        {"detail": "For path params, value must be of type AddTaskSpec"},
    )

    with pytest.raises(MammothAPIError) as raised:
        await client.pipeline.update_task(
            dataview_id=42,
            task_id=7,
            task_spec={"MATH": {}, "EXTRA": 1, "DATAVIEW_ID": 42},
            dataset_id=500,
        )

    error = raised.value
    assert "keys sent beyond those: ['EXTRA', 'MATH']" in str(error)
    assert error.status_code == 400
    assert error.method == "PATCH"
    # The request layer labels a refused PATCH; the CLI reads this to say nothing changed.
    assert error.operation_state is not None


def test_the_rebuilt_refusal_keeps_every_attribute_of_the_original() -> None:
    original = MammothAPIError(
        "value must be of type AddTaskSpec",
        status_code=400,
        response_body={"detail": "value must be of type AddTaskSpec"},
        details={"extra": "kept"},
        method="PATCH",
        request_id="req-1",
        retry_after="3",
        operation_state="outcome_unknown",
        phase="polling",
        job_handle=52618,
        resource_handle=9,
        endpoint="/pipeline/tasks/7",
    )

    rebuilt = _task_params_rejection(original, {"MATH": {}, "EXTRA": 1})

    assert rebuilt is not original
    assert "keys sent beyond those: ['EXTRA', 'MATH']" in rebuilt.message
    assert str(rebuilt) == rebuilt.message
    for name in (
        "status_code",
        "response_body",
        "method",
        "request_id",
        "retry_after",
        "operation_state",
        "phase",
        "job_handle",
        "resource_handle",
        "endpoint",
    ):
        assert getattr(rebuilt, name) == getattr(original, name), name
    assert rebuilt.details == {
        **original.details,
        "rejection_note": rebuilt.details["rejection_note"],
        "rejected_task_keys": ["EXTRA", "MATH"],
    }
    assert "keys sent beyond those: ['EXTRA', 'MATH']" in rebuilt.details["rejection_note"]
    assert rebuilt.details["operation_state"] == "outcome_unknown"
    assert rebuilt.details["job_handle"] == 52618
    # The original is left as it was.
    assert "keys sent" not in original.message
    assert "keys sent" not in str(original)


def test_the_rebuilt_refusal_keeps_the_class_and_its_own_fields() -> None:
    original = MammothAuthError(
        "value must be of type AddTaskSpec", error_code="E1", hint="sign in", method="PATCH"
    )

    rebuilt = _task_params_rejection(original, {"MATH": {}, "EXTRA": 1})

    assert isinstance(rebuilt, MammothAuthError)
    assert rebuilt.error_code == "E1"
    assert rebuilt.hint == "sign in"
    assert rebuilt.status_code == 401


def test_a_refusal_that_is_not_the_type_message_is_returned_as_is() -> None:
    other = MammothAPIError("conflict", status_code=409)

    assert _task_params_rejection(other, {"MATH": {}}) is other


def test_a_refusal_whose_text_is_only_in_the_response_body_names_the_keys() -> None:
    """The server's real 400 says "Validation error"; the type message is in the body."""
    original = MammothAPIError(
        "API request failed: Validation error",
        status_code=400,
        response_body={
            "message": "Validation error",
            "details": {
                "extra": [
                    {
                        "key": "patches.0",
                        "message": "For path ItemTaskPatchPath.PARAMS, value must be of "
                        "type AddTaskSpec",
                    }
                ]
            },
        },
    )

    rebuilt = _task_params_rejection(original, {"SQL": {}, "BOGUS_KEY": 1})

    assert rebuilt is not original
    assert "keys sent beyond those: ['BOGUS_KEY', 'SQL']" in rebuilt.message
    assert rebuilt.details["rejected_task_keys"] == ["BOGUS_KEY", "SQL"]
