"""Independent C2/S3 controls for view transformation adapters.

The expected method names and field destinations in this module are authored
outside the command-contract resolver.  A route therefore cannot pass by
regenerating its expected kwargs from the same signature/introspection code it
is meant to exercise.  The fake service is the wire seam for this offline
slice: it records the exact public View method and kwargs and performs no
mutation or network call.
"""

# The authored wire table keeps every route's destination legible on one row;
# the values are test data, not implementation logic.
# ruff: noqa: E501

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view_ops
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.strict import validate_input_fields
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.command_contract import resolve_command_contract
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_CONDITION = {"column": "S3_REGION", "operator": "EQ", "value": "S3_WEST"}


# Hand-authored expected adapter wires. Values are deliberately distinctive so
# a field dropped by a handler cannot be hidden by a default or another field.
TRANSFORM_CASES: tuple[tuple[str, str, str, dict[str, Any]], ...] = (
    (
        "view.transform.add-column",
        "view_transform_add_column",
        "add_column",
        {"name": "S3_NAME", "column_type": "NUMERIC"},
    ),
    ("view.transform.add-sql", "view_transform_add_sql", "add_sql", {"query": "S3_QUERY"}),
    (
        "view.transform.ai",
        "view_transform_ai",
        "gen_ai",
        {
            "prompt": "S3_PROMPT",
            "context_columns": ["S3_CONTEXT"],
            "new_column": "S3_AI",
            "assistant_data": ["S3_ASSISTANT"],
            "context_columns_derivation": True,
        },
    ),
    (
        "view.transform.bulk-replace",
        "view_transform_bulk_replace",
        "bulk_replace",
        {
            "columns": ["S3_STATUS"],
            "mapping": [{"search": ["S3_OLD"], "replace": "S3_NEW"}],
            "match_case": False,
            "match_words": True,
            "condition": _CONDITION,
        },
    ),
    (
        "view.transform.combine-columns",
        "view_transform_combine_columns",
        "combine_columns",
        {
            "sources": ["S3_A", "S3_B"],
            "new_column": "S3_COMBINED",
            "column_type": "TEXT",
            "existing_column": "S3_EXISTING",
            "separator": "S3_SEPARATOR",
            "condition": _CONDITION,
        },
    ),
    (
        "view.transform.convert-type",
        "view_transform_convert_type",
        "convert_type",
        {"conversions": [{"column": "S3_AMOUNT", "to": "NUMERIC", "format": "S3_FORMAT"}]},
    ),
    (
        "view.transform.copy-columns",
        "view_transform_copy_columns",
        "copy_columns",
        {
            "copies": [
                {
                    "source": "S3_SOURCE",
                    "as_name": "S3_COPY",
                    "type": "TEXT",
                    "destination": "S3_DEST",
                }
            ]
        },
    ),
    (
        "view.transform.crosstab",
        "view_transform_crosstab",
        "crosstab",
        {
            "rows": ["S3_ROW"],
            "pivot_column": "S3_PIVOT",
            "select": {"column": "S3_VALUE", "function": "SUM"},
            "dataset_name": "S3_DATASET",
            "save_as_mode": "APPEND_TO_DS",
            "target_ds_id": 731,
            "condition": _CONDITION,
            "timeout": 37,
        },
    ),
    (
        "view.transform.date-diff",
        "view_transform_date_diff",
        "date_diff",
        {
            "component": "DAY",
            "start": "S3_START",
            "end": "S3_END",
            "new_column": "S3_DIFF",
            "existing_column": "S3_DIFF_EXISTING",
        },
    ),
    (
        "view.transform.delete-columns",
        "view_transform_delete_columns",
        "delete_columns",
        {"columns": ["S3_DELETE_A", "S3_DELETE_B"]},
    ),
    (
        "view.transform.discard-duplicates",
        "view_transform_discard_duplicates",
        "discard_duplicates",
        {"ignore_columns": ["S3_UNIQUE"]},
    ),
    (
        "view.transform.extract-date",
        "view_transform_extract_date",
        "extract_date",
        {
            "column": "S3_DATE",
            "component": "year",
            "new_column": "S3_YEAR",
            "existing_column": "S3_YEAR_EXISTING",
        },
    ),
    (
        "view.transform.fill-missing",
        "view_transform_fill_missing",
        "fill_missing",
        {
            "column": "S3_VALUE",
            "direction": "FIRST_VALUE",
            "partition_by": "S3_GROUP",
            "order_by": [["S3_ORDER", "DESC"]],
        },
    ),
    (
        "view.transform.filter",
        "view_transform_filter",
        "filter_rows",
        {"condition": _CONDITION, "filter_type": "REMOVE", "prompt": "S3_PROMPT"},
    ),
    (
        "view.transform.generate-sql",
        "view_transform_generate_sql",
        "generate_sql",
        {"intent": "S3_INTENT"},
    ),
    (
        "view.transform.increment-date",
        "view_transform_increment_date",
        "increment_date",
        {
            "column": "S3_DATE",
            "delta": {"days": 7},
            "new_column": "S3_INCREMENTED",
            "existing_column": "S3_INCREMENTED_EXISTING",
            "condition": _CONDITION,
        },
    ),
    (
        "view.transform.join",
        "view_transform_join",
        "join",
        {
            "foreign_view": 902,
            "join_type": "LEFT",
            "on": [{"left": "S3_LEFT", "right": "S3_RIGHT"}],
            "select": [{"column": "S3_FOREIGN", "alias": "S3_ALIAS"}],
            "column_prefix": "S3_PREFIX",
            "foreign_dataset_id": 903,
        },
    ),
    (
        "view.transform.json-extract",
        "view_transform_json_extract",
        "json_extract",
        {
            "column": "S3_JSON",
            "json_type": "OBJECT",
            "keys": ["S3_KEY"],
            "extractions": [{"key": "S3_KEY", "as_name": "S3_EXTRACTED", "type": "TEXT"}],
            "keep_source": True,
            "op_type": "JSON_OBJECT_TO_COLUMNS",
        },
    ),
    (
        "view.transform.limit-rows",
        "view_transform_limit_rows",
        "limit_rows",
        {"n": 17, "bottom": True, "order_by": [["S3_ORDER", "ASC"]]},
    ),
    (
        "view.transform.lookup",
        "view_transform_lookup",
        "lookup",
        {
            "source": "S3_SOURCE",
            "lookup_view_id": 904,
            "key": "S3_KEY",
            "value": "S3_VALUE",
            "new_column": "S3_LOOKUP",
            "new_column_type": "NUMERIC",
            "existing_column": "S3_LOOKUP_EXISTING",
            "lookup_dataset_id": 905,
        },
    ),
    (
        "view.transform.math",
        "view_transform_math",
        "math",
        {
            "expression": "S3_AMOUNT * 2",
            "new_column": "S3_TOTAL",
            "column_type": "NUMERIC",
            "existing_column": "S3_TOTAL_EXISTING",
            "condition": _CONDITION,
        },
    ),
    (
        "view.transform.pivot",
        "view_transform_pivot",
        "pivot",
        {
            "group_by": ["S3_GROUP"],
            "aggregations": [{"column": "S3_AMOUNT", "function": "SUM", "as_name": "S3_TOTAL"}],
            "condition": _CONDITION,
        },
    ),
    (
        "view.transform.replace",
        "view_transform_replace",
        "replace_values",
        {
            "columns": ["S3_TEXT"],
            "find": "S3_FIND",
            "replace": "S3_REPLACE",
            "match_case": True,
            "match_words": True,
            "condition": _CONDITION,
        },
    ),
    (
        "view.transform.set-values",
        "view_transform_set_values",
        "set_values",
        {
            "values": [{"value": "S3_VALUE", "condition": _CONDITION}],
            "new_column": "S3_SET",
            "column_type": "TEXT",
            "existing_column": "S3_SET_EXISTING",
            "condition": _CONDITION,
        },
    ),
    (
        "view.transform.small-large",
        "view_transform_small_large",
        "small_large",
        {
            "function": "LARGE",
            "columns": ["S3_AMOUNT"],
            "index": 2,
            "constants": [7.5],
            "new_column": "S3_EXTREME",
            "existing_column": "S3_EXTREME_EXISTING",
        },
    ),
    (
        "view.transform.split",
        "view_transform_split",
        "split_column",
        {
            "column": "S3_NAME",
            "delimiter": "S3_DELIM",
            "new_columns": [{"name": "S3_FIRST", "type": "TEXT"}],
        },
    ),
    (
        "view.transform.substring",
        "view_transform_substring",
        "substring",
        {
            "column": "S3_TEXT",
            "direction": "START",
            "num_char": 4,
            "regex_pattern": "S3_REGEX",
            "regex_invert": True,
            "new_column": "S3_SUB",
            "existing_column": "S3_SUB_EXISTING",
            "condition": _CONDITION,
        },
    ),
    (
        "view.transform.text",
        "view_transform_text",
        "text_transform",
        {"columns": ["S3_TEXT"], "case": "UPPER", "trim": True, "condition": _CONDITION},
    ),
    (
        "view.transform.unnest",
        "view_transform_unnest",
        "unnest",
        {
            "columns": ["S3_LIST"],
            "label_column": "S3_LABEL",
            "value_column": "S3_VALUE",
            "value_type": "TEXT",
        },
    ),
    (
        "view.transform.window",
        "view_transform_window",
        "window",
        {
            "function": "SUM",
            "column": "S3_AMOUNT",
            "new_column": "S3_RUNNING",
            "column_type": "NUMERIC",
            "existing_column": "S3_RUNNING_EXISTING",
            "partition_by": ["S3_GROUP"],
            "order_by": [["S3_ORDER", "ASC"]],
            "range_type": "RUNNING",
        },
    ),
)


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    login_default_profile()


@pytest.fixture
def isolated_cli_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir",
        lambda *_args, **_kwargs: str(tmp_path),
    )


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeMammothService:
    service = FakeMammothService()
    monkeypatch.setattr(service_factory, "build_service", lambda *_args, **_kwargs: service)
    return service


def _write(tmp_path: Path, payload: dict[str, Any]) -> str:
    path = tmp_path / "s3-transform.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def test_substring_left_char_position_is_forwarded(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """LEFT/RIGHT directions use character position, not ``num_char``."""
    payload = {"column": "S3_TEXT", "direction": "LEFT", "char_position": 2}
    view_ops.view_transform_substring(
        _inv("view.transform.substring", extra_args=["501"], input_file=_write(tmp_path, payload))
    )
    assert fake_service.view_call_log == [(501, "substring", payload)]


def test_substring_regex_without_direction_is_forwarded(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """Regex extraction remains independent of directional arguments."""
    payload = {"column": "S3_TEXT", "regex_pattern": "S3_REGEX", "regex_invert": True}
    view_ops.view_transform_substring(
        _inv("view.transform.substring", extra_args=["501"], input_file=_write(tmp_path, payload))
    )
    assert fake_service.view_call_log == [(501, "substring", payload)]


def test_transform_inventory_is_explicit_and_complete() -> None:
    expected = {item[0] for item in TRANSFORM_CASES}
    assert len(expected) == 30
    for command_id, handler_name, _method, _payload in TRANSFORM_CASES:
        record = command_by_id(command_id)
        assert record is not None
        assert record["sdk_symbol"]
        assert getattr(view_ops, handler_name)
        contract = resolve_command_contract(command_id)
        assert contract is not None
        # S3's shared owner closes these contracts; this assertion prevents a
        # permissive/open contract from being mistaken for migration evidence.
        assert contract.extensibility == "closed"
        assert contract.input_schema is not None


@pytest.mark.parametrize("command_id,handler_name,method,payload", TRANSFORM_CASES)
def test_transform_wire_destination_is_exact(
    command_id: str,
    handler_name: str,
    method: str,
    payload: dict[str, Any],
    fake_service: FakeMammothService,
    tmp_path: Path,
) -> None:
    handler: Callable[[Invocation], Any] = getattr(view_ops, handler_name)
    handler(_inv(command_id, extra_args=["501"], input_file=_write(tmp_path, payload)))
    assert fake_service.view_call_log == [(501, method, payload)]


@pytest.mark.parametrize("command_id,handler_name,method,payload", TRANSFORM_CASES)
def test_transform_dropped_field_is_rejected_before_dispatch(
    command_id: str,
    handler_name: str,
    method: str,
    payload: dict[str, Any],
    fake_service: FakeMammothService,
    tmp_path: Path,
) -> None:
    del method
    altered = dict(payload)
    altered["S3_DROPPED_FIELD"] = "must-not-be-forwarded"
    handler: Callable[[Invocation], Any] = getattr(view_ops, handler_name)
    with pytest.raises(CliError) as error:
        handler(_inv(command_id, extra_args=["501"], input_file=_write(tmp_path, altered)))
    assert error.value.code == "unknown_input_field"
    assert fake_service.view_call_log == []


def test_s3_every_route_has_closed_shared_admission() -> None:
    """The 63-route S3 surface cannot silently accept a dropped field."""
    route_ids = {
        str(record["command_id"])
        for record in load_commands()
        if str(record["command_id"]).startswith("view.")
        and not str(record["command_id"]).startswith("view.export.")
        and not str(record["command_id"]).startswith(
            ("view.checkpoint.", "view.draft.", "view.pipeline.", "view.task.", "view.version.")
        )
    }
    assert len(route_ids) == 63
    for command_id in route_ids:
        contract = resolve_command_contract(command_id)
        assert contract is not None
        assert contract.extensibility == "closed", command_id
        with pytest.raises(CliError) as error:
            validate_input_fields(command_id, {"__s3_dropped_field__": "sentinel"})
        assert error.value.code == "unknown_input_field"
