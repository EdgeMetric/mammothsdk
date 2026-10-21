"""Public Dataset / Dataview / Page models, parsed against the pinned prod OpenAPI spec.

Payloads below use the property names and types of the spec schemas (``DsInfo``,
``DatasetsList``, ``DataviewInfo``, ``DataviewInfoList``, ``DataviewActiveUsers``,
``DatasetPatchRequest``, ``DataviewPatch``, ``DataviewData``), not the SDK's own field lists.
Where the SDK model rejects a payload the server really sends, the test is an
``xfail(strict=True)`` that records the drift.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from mammoth.models.datasets import (
    DatasetCreateSpec,
    DatasetDataResponse,
    DatasetPatchRequest,
    DatasetSchema,
    DatasetsList,
)
from mammoth.models.dataviews import (
    ActiveUsersList,
    DataviewCreateRequest,
    DataviewDataRequest,
    DataviewDataResponse,
    DataviewPatchRequest,
    DataviewSchema,
    DataviewsList,
)
from mammoth.models.pagination import Page

from ._spec import schema

# --- real-shaped payloads (property names/types from the spec's DsInfo / DataviewInfo) ----------


def _ds_info(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": 9423,
        "name": "Orders 2026",
        "created_at": "2026-09-03T08:59:55.872656",
        "created_by": "Asha Rao",  # DsInfo.created_by is a string in the spec
        "updated_at": "2026-09-04T08:59:02.483757",
        "status": "processing",
        "status_info": {"processing": "ingesting"},
        "data_schema": [{"c_id": "column_ab12cd34ef", "c_name": "amount", "c_type": "numeric"}],
        "stats": {"row_count": 8362, "column_count": 3, "batch_count": 1, "size": 4353},
        "batch_ids": [5946],
    }
    return base | over


def _dv_info(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": 4,
        "name": "Orders view",
        "ds_id": 9423,
        "status": "ready",
        "row_count": 120,
        "column_count": 3,
        "created_at": "2026-09-03T08:59:55",
    }
    return base | over


def test_spec_dataset_list_items_are_dsinfo_with_string_created_by() -> None:
    # Guards the fixtures above against drifting from the pinned spec.
    props = schema("DsInfo")["properties"]
    assert {"id", "name", "status", "created_by"} <= set(props)
    assert props["created_by"]["oneOf"][0]["type"] == "string"
    assert "ds_id" in schema("DataviewInfo")["properties"]
    assert "active_users" in schema("DataviewActiveUsers")["properties"]


class TestDatasetModels:
    def test_dataset_parses_core_fields_and_timestamps(self) -> None:
        ds = DatasetSchema.model_validate(_ds_info(created_by=None))
        assert (ds.id, ds.name, ds.status) == (9423, "Orders 2026", "processing")
        assert ds.created_at == datetime(2026, 9, 3, 8, 59, 55, 872656)
        # Unmodelled spec fields are kept, not dropped.
        assert ds.model_dump()["batch_ids"] == [5946]

    def test_dataset_requires_id_and_name(self) -> None:
        with pytest.raises(ValidationError) as exc:
            DatasetSchema.model_validate({"status": "ready"})
        assert {e["loc"] for e in exc.value.errors()} == {("id",), ("name",)}

    def test_dataset_id_must_be_integer(self) -> None:
        with pytest.raises(ValidationError, match="id"):
            DatasetSchema.model_validate(_ds_info(id="not-a-number"))

    def test_dataset_list_parses_items_and_pagination(self) -> None:
        body = {"datasets": [_ds_info(created_by=None), _ds_info(id=2, created_by=None)]}
        parsed = DatasetsList.model_validate(body | {"total": 2, "limit": 50, "offset": 0})
        assert [d.id for d in parsed.datasets] == [9423, 2]
        assert (parsed.total, parsed.limit, parsed.offset) == (2, 50, 0)

    def test_dataset_list_requires_the_datasets_key(self) -> None:
        with pytest.raises(ValidationError, match="datasets"):
            DatasetsList.model_validate({"total": 0})

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: DatasetSchema.created_by is int|None but spec DsInfo.created_by is a string",
    )
    def test_dataset_accepts_spec_string_created_by(self) -> None:
        assert DatasetSchema.model_validate(_ds_info()).created_by == "Asha Rao"

    def test_create_spec_requires_source_type_and_config(self) -> None:
        with pytest.raises(ValidationError) as exc:
            DatasetCreateSpec.model_validate({"name": "x"})
        assert {e["loc"] for e in exc.value.errors()} == {("source_type",), ("source_config",)}

    def test_data_response_requires_rows_list(self) -> None:
        ok = DatasetDataResponse.model_validate({"data": [{"a": 1}], "total_rows": 1})
        assert ok.data == [{"a": 1}] and ok.total_rows == 1
        with pytest.raises(ValidationError, match="data"):
            DatasetDataResponse.model_validate({"data": "rows"})

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: DatasetPatchRequest.patch is a required list; spec DatasetPatchRequest "
        "takes a single `patch` operation or a `patches` list (both optional)",
    )
    def test_spec_patch_request_examples_parse(self) -> None:
        # The spec documents ``{"patch": {op, path, value}}`` (a single operation).
        example = schema("DatasetPatchRequest")["examples"][0]
        assert example == {"patch": {"op": "replace", "path": "name", "value": "test"}}
        req = DatasetPatchRequest.model_validate(example)
        assert req.patch[0].op == "replace" and req.patch[0].value == "test"

    def test_patch_request_requires_patch(self) -> None:
        with pytest.raises(ValidationError, match="patch"):
            DatasetPatchRequest.model_validate({})


class TestDataviewModels:
    def test_defaults_match_the_spec_dataview_data_body(self) -> None:
        props = schema("DataviewData")["properties"]
        req = DataviewDataRequest()
        assert req.offset == props["offset"]["default"] == 1
        assert req.limit == props["limit"]["default"] == 400

    def test_create_request_requires_name_and_keeps_clone_source(self) -> None:
        assert DataviewCreateRequest(name="V", clone_config_from=3).clone_config_from == 3
        with pytest.raises(ValidationError, match="name"):
            DataviewCreateRequest.model_validate({})

    def test_data_response_parses_rows_and_sequence(self) -> None:
        r = DataviewDataResponse.model_validate({"data": [{"c": 1}], "sequence": 2, "limit": 5})
        assert (r.data, r.sequence, r.limit) == ([{"c": 1}], 2, 5)

    def test_spec_patch_examples_parse(self) -> None:
        examples = schema("DataviewPatch")["examples"]
        parsed = [DataviewPatchRequest.model_validate(e) for e in examples]
        assert [(p.patch[0].op, p.patch[0].path) for p in parsed] == [
            ("replace", "name"),
            ("command", ""),
        ]
        assert parsed[1].patch[0].value == "reset"

    def test_patch_op_requires_op_and_path(self) -> None:
        with pytest.raises(ValidationError) as exc:
            DataviewPatchRequest.model_validate({"patch": [{"value": 1}]})
        assert {e["loc"][-1] for e in exc.value.errors()} == {"op", "path"}

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: DataviewSchema requires dataset_id but spec DataviewInfo names it ds_id",
    )
    def test_dataview_accepts_spec_dataview_info(self) -> None:
        assert DataviewSchema.model_validate(_dv_info()).dataset_id == 9423

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: DataviewsList cannot parse spec DataviewInfoList (items use ds_id)",
    )
    def test_dataview_list_accepts_spec_dataview_info_list(self) -> None:
        body = {"dataviews": [_dv_info()], "offset": 0, "limit": 50, "next": "u"}
        assert DataviewsList.model_validate(body).dataviews[0].id == 4

    def test_dataview_requires_dataset_id_when_given_sdk_shape(self) -> None:
        with pytest.raises(ValidationError, match="dataset_id"):
            DataviewSchema.model_validate({"id": 1, "name": "v"})

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: ActiveUsersList expects 'users'; spec DataviewActiveUsers uses 'active_users'",
    )
    def test_active_users_accepts_spec_shape(self) -> None:
        body = {"active_users": [{"id": 7, "email": "a@example.com", "first_name": "A"}]}
        assert len(ActiveUsersList.model_validate(body).users) == 1


class TestPage:
    def test_empty_page_has_no_next(self) -> None:
        p: Page[int] = Page()
        assert (p.items, p.offset, p.next_offset, p.has_more) == ([], 0, None, False)

    def test_full_page_continues_at_offset_plus_count(self) -> None:
        p = Page[str](items=["a", "b"], offset=10, limit=2)
        assert p.next_offset == 12 and p.has_more is True

    def test_total_reached_ends_pagination(self) -> None:
        assert Page[int](items=[1, 2], offset=0, limit=2, total=2).next_offset is None
        assert Page[int](items=[1, 2], offset=0, limit=2, total=3).next_offset == 2

    def test_short_page_is_the_last(self) -> None:
        assert Page[int](items=[1], offset=4, limit=50).next_offset is None

    def test_unknown_total_and_limit_assume_more(self) -> None:
        assert Page[int](items=[1, 2, 3], offset=3).next_offset == 6

    def test_items_are_validated_against_the_type_parameter(self) -> None:
        assert Page[int].model_validate({"items": ["1", 2]}).items == [1, 2]
        with pytest.raises(ValidationError, match="items"):
            Page[int].model_validate({"items": ["x"]})
