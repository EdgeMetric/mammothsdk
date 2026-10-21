"""BatchesAPI: the wire request for each call, held to the pinned OpenAPI spec.

Spec operations: GetBatches, GetBatch, CreateBatch (``BatchesPostRequest``), UpdateBatches
(``BatchesPatchRequest``), DeleteBatch, DeleteBatches.
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401
from ._spec import schema, spec

B = "/workspaces/1/projects/25654/datasets/77/batches"
SPEC_B = "/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/batches"


def _last(server: RecordingServer) -> dict[str, Any]:
    return server.requests[-1]


# --- list / get / delete -----------------------------------------------------------------


async def test_list_sends_no_query_by_default(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers[f"GET {B}"] = {"batches": [], "next": ""}
    assert await client.batches.list(77) == {"batches": [], "next": ""}
    assert server.requests == [{"method": "GET", "path": B, "query": {}, "body": None}]


async def test_list_sends_paging_and_honours_an_explicit_project(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.batches.list(77, project_id=9, limit=5, offset=10)
    assert _last(server)["path"] == "/workspaces/1/projects/9/datasets/77/batches"
    assert _last(server)["query"] == {"limit": "5", "offset": "10"}
    declared = {
        p["name"] for p in spec()["paths"][SPEC_B]["get"]["parameters"] if p["in"] == "query"
    }
    assert set(_last(server)["query"]) <= declared


async def test_list_without_any_project_fails_before_a_request(server: RecordingServer) -> None:
    c = MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    c.project_id = None  # type: ignore[assignment]
    with pytest.raises(ValueError, match="project_id must be set"):
        await c.batches.list(77)
    assert server.requests == []


async def test_get_and_delete_one_batch(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.batches.get(77, 5)
    await client.batches.delete(77, 5)
    assert [(r["method"], r["path"]) for r in server.requests] == [
        ("GET", f"{B}/5"),
        ("DELETE", f"{B}/5"),
    ]


async def test_bulk_delete_with_a_list_a_string_or_nothing(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.batches.bulk_delete(77, ids=[1, 2, 3])
    await client.batches.bulk_delete(77, ids="4,5")
    await client.batches.bulk_delete(77)
    assert [r["query"] for r in server.requests] == [{"ids": "1,2,3"}, {"ids": "4,5"}, {}]
    assert all(r["method"] == "DELETE" and r["path"] == B for r in server.requests)


# --- create (dict shortcut) -----------------------------------------------------------------


async def test_create_expands_a_dict_mapping_to_column_name_mappings(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.batches.create(77, 12, {"Amount": "amount", "Day": "day"})
    assert _last(server) == {
        "method": "POST",
        "path": B,
        "query": {},
        "body": {
            "source_id": 12,
            "mapping": [
                {
                    "source_c_name": "Amount",
                    "destination_c_name": "amount",
                    "expected_destination_c_type": "TEXT",
                },
                {
                    "source_c_name": "Day",
                    "destination_c_name": "day",
                    "expected_destination_c_type": "TEXT",
                },
            ],
            "delete_source_ds": False,
        },
    }
    item_schema = schema("ColumnNameMapping")
    assert set(_last(server)["body"]["mapping"][0]) == set(item_schema["required"])


async def test_create_sends_optional_fields_under_the_spec_names(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.batches.create(
        77,
        12,
        {"A": "a"},
        new_ds_params={"name": "Combined"},
        is_validation_required=False,
        delete_source_ds=True,
        expected_destination_c_type="NUMERIC",
    )
    body = _last(server)["body"]
    assert body["new_ds_details"] == {"name": "Combined"}
    assert body["validate_only"] is False  # False is a value, not "unset"
    assert body["delete_source_ds"] is True
    assert body["mapping"][0]["expected_destination_c_type"] == "NUMERIC"
    assert set(body) <= set(schema("BatchesPostRequest")["properties"])


async def test_create_only_sends_properties_the_spec_defines(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    """``change_map`` is not a BatchesPostRequest property: it warns and is not sent."""
    with pytest.warns(DeprecationWarning, match="change_map"):
        await client.batches.create(77, 12, {"A": "a"}, change_map={"x": 1})
    assert set(_last(server)["body"]) <= set(schema("BatchesPostRequest")["properties"])


async def test_create_passes_prebuilt_mapping_items_through(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    items = [
        {
            "source_c_id": "column_a",
            "destination_c_id": "column_b",
            "expected_destination_c_type": "DATE",
        },
        {"source_c_id": "column_c", "expected_destination_c_type": "TEXT", "action": "add_column"},
    ]
    await client.batches.create(77, 12, items)
    assert _last(server)["body"]["mapping"] == items


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"source_id": 0, "mapping": {"a": "b"}}, "source_id` must be a positive integer, got 0"),
        ({"source_id": 1, "mapping": {}}, "non-empty dict"),
        ({"source_id": 1, "mapping": []}, "non-empty dict"),
        (
            {"source_id": 1, "mapping": {"a": "b"}, "expected_destination_c_type": "BOOL"},
            "must be TEXT, NUMERIC or DATE, got 'BOOL'",
        ),
        (
            {"source_id": 1, "mapping": [{"source_c_id": "x"}]},
            "needs `expected_destination_c_type`",
        ),
    ],
)
async def test_create_rejects_bad_arguments_before_any_request(
    kwargs: dict[str, Any],
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await client.batches.create(77, **kwargs)
    assert server.requests == []


def test_spec_requires_a_destination_type_on_every_mapping_item() -> None:
    assert "expected_destination_c_type" in schema("ColumnNameMapping")["required"]
    assert "expected_destination_c_type" in schema("ColumnIdMapping")["required"]
    assert schema("ColumnNameMapping")["properties"]["expected_destination_c_type"]["enum"] == [
        "TEXT",
        "NUMERIC",
        "DATE",
    ]


# --- create_spec (typed release body) ------------------------------------------------------


async def test_create_spec_from_a_source_dataset_sends_only_what_was_set(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    body = {
        "source_id": 12,
        "mapping": [
            {"source_c_id": "c1", "destination_c_id": "c2", "expected_destination_c_type": "TEXT"}
        ],
        "new_ds_details": {"name": "Batch Dataset"},
    }
    await client.batches.create_spec(77, body)
    assert _last(server) == {"method": "POST", "path": B, "query": {}, "body": body}


async def test_create_spec_from_an_uploaded_file(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    # The second CreateBatch example of the spec.
    example = schema("BatchesPostRequest")["examples"][1]
    assert example == {"file_id": 94}
    await client.batches.create_spec(77, example, project_id=9)
    assert _last(server)["path"] == "/workspaces/1/projects/9/datasets/77/batches"
    assert _last(server)["body"] == {"file_id": 94}


async def test_create_spec_accepts_the_spec_source_example(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    example = schema("BatchesPostRequest")["examples"][0]
    await client.batches.create_spec(77, example)
    assert _last(server)["body"] == example


@pytest.mark.parametrize(
    ("dataset_id", "project_id", "body", "message"),
    [
        (0, None, {"file_id": 1}, "`dataset_id` must be a positive integer, got 0"),
        (True, None, {"file_id": 1}, "`dataset_id` must be a positive integer"),
        (7, 0, {"file_id": 1}, "`project_id` must be a positive integer, got 0"),
        (7, None, {"bogus": 1}, "Invalid release batch spec"),
        (7, None, {}, "Either `source_id` or `file_id` is required"),
        (
            7,
            None,
            {"source_id": 1, "file_id": 2},
            "`source_id` and `file_id` are mutually exclusive",
        ),
        (7, None, {"source_id": 0, "mapping": []}, "`source_id` must be a positive integer, got 0"),
        (7, None, {"file_id": 0}, "`file_id` must be a positive integer, got 0"),
        (7, None, {"source_id": 1}, "`mapping` must be a non-empty release mapping array"),
        (
            7,
            None,
            {
                "file_id": 4,
                "mapping": [{"source_c_id": "a", "expected_destination_c_type": "TEXT"}],
            },
            "`mapping` must be omitted when `file_id` is provided",
        ),
    ],
)
async def test_create_spec_rejects_invalid_requests_before_any_request(
    dataset_id: Any,
    project_id: Any,
    body: dict[str, Any],
    message: str,
    server: RecordingServer,
    client: MammothClient,  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await client.batches.create_spec(dataset_id, body, project_id=project_id)
    assert server.requests == []


# --- update ---------------------------------------------------------------------------------


async def test_update_wraps_the_operation_and_defaults_the_path(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    example = schema("BatchesPatchRequest")["examples"][0]["patch"]
    await client.batches.update(77, {"op": example["op"], "value": example["value"]})
    assert _last(server) == {
        "method": "PATCH",
        "path": B,
        "query": {},
        "body": {"patch": example},
    }


async def test_update_accepts_a_one_item_list_and_a_remove_op(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    await client.batches.update(77, [{"op": "remove", "value": {"suspend": [3]}}])
    assert _last(server)["body"] == {
        "patch": {"path": "batches", "op": "remove", "value": {"suspend": [3]}}
    }
    assert "remove" in schema("datasets_schema_OpValues")["enum"]


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        ({}, "must be a patch operation"),
        ([], "must be a patch operation"),
        ([{"op": "replace"}, {"op": "replace"}], "one patch operation per call; got 2"),
        ({"op": "add", "value": {}}, "op='replace' or op='remove', got 'add'"),
        ({"value": {}}, "op='replace' or op='remove', got None"),
    ],
)
async def test_update_rejects_bad_patches_before_any_request(
    patch: Any, message: str, server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match=message):
        await client.batches.update(77, patch)
    assert server.requests == []
