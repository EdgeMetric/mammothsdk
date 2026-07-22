"""Unit tests for the ``view`` draft, transform, and view-CRUD handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view_ops as view_ops_cmd
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.testing import FakeMammothService

_CREATE = "mammoth.client.ViewsResource.create"
_GET = "mammoth.client.ViewsResource.get"
_DELETE = "mammoth.client.ViewsResource.delete"


@pytest.fixture(autouse=True)
def _env_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAMMOTH_API_KEY", "k")
    monkeypatch.setenv("MAMMOTH_API_SECRET", "s")
    monkeypatch.setenv("MAMMOTH_WORKSPACE_ID", "4")


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _write(tmp_path: Path, payload: dict[str, Any]) -> str:
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps(payload), encoding="utf-8")
    return str(doc)


# --- view create/get/delete (generic ``service.call`` seam) ---------------


def test_create_requires_dataset_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_create(_inv("view.create"))
    assert excinfo.value.code == "missing_argument"


def test_create_forwards_optional_fields(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"name": "Copy", "clone_from": 9})
    view_ops_cmd.view_create(_inv("view.create", extra_args=["5"], input_file=doc))
    assert fake_service.call_log == [(_CREATE, {"dataset_id": 5, "name": "Copy", "clone_from": 9})]


def test_get_requires_view_id(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_get(_inv("view.get"))
    assert excinfo.value.code == "missing_argument"


def test_get_uses_positional_view_id(fake_service: FakeMammothService) -> None:
    view_ops_cmd.view_get(_inv("view.get", extra_args=["7"]))
    assert fake_service.call_log == [(_GET, {"view_id": 7})]


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_delete(_inv("view.delete", extra_args=["7"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_ops_cmd.view_delete(_inv("view.delete", extra_args=["7"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"view_id": 7})]


# --- view draft * (``service.call_view`` seam) -----------------------------


def test_draft_enter_calls_view(fake_service: FakeMammothService) -> None:
    view_ops_cmd.view_draft_enter(_inv("view.draft.enter", extra_args=["3"]))
    assert fake_service.view_call_log == [(3, "enter_draft_mode", {})]


def test_draft_status_reads_server_backed_pipeline(fake_service: FakeMammothService) -> None:
    """Draft status dispatches to the server-backed pipeline symbol, not the
    process-local View flag."""
    symbol = "mammoth.api.pipeline.PipelineAPI.get_draft_status"
    fake_service.responses[symbol] = {"dataview_id": 3, "is_draft": True}
    data, _ = view_ops_cmd.view_draft_status(_inv("view.draft.status", extra_args=["3"]))
    assert data == {"dataview_id": 3, "is_draft": True}
    assert fake_service.call_log == [(symbol, {"dataview_id": 3})]
    assert fake_service.view_call_log == []


def test_draft_submit_calls_view(fake_service: FakeMammothService) -> None:
    view_ops_cmd.view_draft_submit(_inv("view.draft.submit", extra_args=["3"]))
    assert fake_service.view_call_log == [(3, "submit_draft", {})]


def test_draft_discard_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_draft_discard(_inv("view.draft.discard", extra_args=["3"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.view_call_log == []


def test_draft_discard_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_ops_cmd.view_draft_discard(_inv("view.draft.discard", extra_args=["3"], yes=True))
    assert fake_service.view_call_log == [(3, "discard_draft", {})]


def test_draft_auto_run_requires_enabled(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_draft_auto_run(_inv("view.draft.auto-run", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_draft_auto_run_forwards_enabled(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"enabled": True})
    view_ops_cmd.view_draft_auto_run(_inv("view.draft.auto-run", extra_args=["3"], input_file=doc))
    assert fake_service.view_call_log == [(3, "set_auto_run", {"enabled": True})]


# --- view transform * (``service.call_view`` seam) -------------------------


def test_transform_add_column_requires_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_add_column(_inv("view.transform.add-column", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_add_column_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"name": "Col", "column_type": "NUMERIC"})
    view_ops_cmd.view_transform_add_column(
        _inv("view.transform.add-column", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "add_column", {"name": "Col", "column_type": "NUMERIC"})
    ]


def test_transform_add_sql_requires_query(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_add_sql(_inv("view.transform.add-sql", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_add_sql_forwards_query(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"query": "SELECT 1"})
    view_ops_cmd.view_transform_add_sql(
        _inv("view.transform.add-sql", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [(3, "add_sql", {"query": "SELECT 1"})]


def test_transform_ai_requires_prompt(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_ai(_inv("view.transform.ai", extra_args=["3"], input_file=None))
    assert excinfo.value.code == "missing_field"


def test_transform_ai_forwards_optional(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        {
            "prompt": "Summarize",
            "context_columns": ["a"],
            "new_column": "AI",
            "assistant_data": ["x"],
            "context_columns_derivation": True,
        },
    )
    view_ops_cmd.view_transform_ai(_inv("view.transform.ai", extra_args=["3"], input_file=doc))
    assert fake_service.view_call_log == [
        (
            3,
            "gen_ai",
            {
                "prompt": "Summarize",
                "context_columns": ["a"],
                "new_column": "AI",
                "assistant_data": ["x"],
                "context_columns_derivation": True,
            },
        )
    ]


def test_transform_bulk_replace_requires_columns(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_bulk_replace(
            _inv("view.transform.bulk-replace", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_bulk_replace_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {
            "columns": ["a"],
            "mapping": [{"find": "x", "replace": "y"}],
            "match_case": True,
            "condition": {"column": "a", "operator": "EQ", "value": 1},
        },
    )
    view_ops_cmd.view_transform_bulk_replace(
        _inv("view.transform.bulk-replace", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "bulk_replace",
            {
                "columns": ["a"],
                "mapping": [{"find": "x", "replace": "y"}],
                "match_case": True,
                "condition": {"column": "a", "operator": "EQ", "value": 1},
            },
        )
    ]


def test_transform_combine_columns_requires_sources(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_combine_columns(
            _inv("view.transform.combine-columns", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_combine_columns_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"sources": ["a", "b"], "separator": "-"})
    view_ops_cmd.view_transform_combine_columns(
        _inv("view.transform.combine-columns", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "combine_columns", {"sources": ["a", "b"], "separator": "-"})
    ]


def test_transform_convert_type_requires_conversions(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_convert_type(
            _inv("view.transform.convert-type", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_convert_type_forwards(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"conversions": [{"column": "a", "column_type": "NUMERIC"}]})
    view_ops_cmd.view_transform_convert_type(
        _inv("view.transform.convert-type", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "convert_type", {"conversions": [{"column": "a", "column_type": "NUMERIC"}]})
    ]


def test_transform_copy_columns_requires_copies(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_copy_columns(
            _inv("view.transform.copy-columns", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_copy_columns_forwards(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"copies": [{"source": "a", "new_column": "a2"}]})
    view_ops_cmd.view_transform_copy_columns(
        _inv("view.transform.copy-columns", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "copy_columns", {"copies": [{"source": "a", "new_column": "a2"}]})
    ]


def test_transform_crosstab_requires_dataset_name(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_crosstab(_inv("view.transform.crosstab", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_crosstab_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {
            "rows": ["a"],
            "pivot_column": "b",
            "select": {"column": "c", "function": "SUM"},
            "dataset_name": "Crosstab",
            "timeout": 30,
        },
    )
    view_ops_cmd.view_transform_crosstab(
        _inv("view.transform.crosstab", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "crosstab",
            {
                "rows": ["a"],
                "pivot_column": "b",
                "select": {"column": "c", "function": "SUM"},
                "dataset_name": "Crosstab",
                "timeout": 30,
            },
        )
    ]


def test_transform_date_diff_requires_component(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_date_diff(_inv("view.transform.date-diff", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_date_diff_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"component": "DAYS", "start": "a", "end": "b", "new_column": "diff"})
    view_ops_cmd.view_transform_date_diff(
        _inv("view.transform.date-diff", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "date_diff",
            {"component": "DAYS", "start": "a", "end": "b", "new_column": "diff"},
        )
    ]


def test_transform_delete_columns_requires_columns(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_delete_columns(
            _inv("view.transform.delete-columns", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_delete_columns_forwards(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"columns": ["a", "b"]})
    view_ops_cmd.view_transform_delete_columns(
        _inv("view.transform.delete-columns", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [(3, "delete_columns", {"columns": ["a", "b"]})]


def test_transform_discard_duplicates_no_input(fake_service: FakeMammothService) -> None:
    view_ops_cmd.view_transform_discard_duplicates(
        _inv("view.transform.discard-duplicates", extra_args=["3"])
    )
    assert fake_service.view_call_log == [(3, "discard_duplicates", {})]


def test_transform_discard_duplicates_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"ignore_columns": ["a"]})
    view_ops_cmd.view_transform_discard_duplicates(
        _inv("view.transform.discard-duplicates", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [(3, "discard_duplicates", {"ignore_columns": ["a"]})]


def test_transform_extract_date_requires_component(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_extract_date(
            _inv("view.transform.extract-date", extra_args=["3"], input_file=None)
        )
    assert excinfo.value.code == "missing_field"


def test_transform_extract_date_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"column": "a", "component": "YEAR", "new_column": "yr"})
    view_ops_cmd.view_transform_extract_date(
        _inv("view.transform.extract-date", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "extract_date", {"column": "a", "component": "YEAR", "new_column": "yr"})
    ]


def test_transform_fill_missing_requires_direction(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_fill_missing(
            _inv("view.transform.fill-missing", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_fill_missing_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"column": "a", "direction": "DOWN", "partition_by": "b"})
    view_ops_cmd.view_transform_fill_missing(
        _inv("view.transform.fill-missing", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "fill_missing", {"column": "a", "direction": "DOWN", "partition_by": "b"})
    ]


def test_transform_filter_requires_condition(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_filter(_inv("view.transform.filter", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_filter_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {
            "condition": {"column": "a", "operator": "EQ", "value": 1},
            "filter_type": "HIDE",
        },
    )
    view_ops_cmd.view_transform_filter(
        _inv("view.transform.filter", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "filter_rows",
            {
                "condition": {"column": "a", "operator": "EQ", "value": 1},
                "filter_type": "HIDE",
            },
        )
    ]


def test_transform_generate_sql_requires_intent(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_generate_sql(
            _inv("view.transform.generate-sql", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_generate_sql_forwards(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"intent": "Top customers"})
    view_ops_cmd.view_transform_generate_sql(
        _inv("view.transform.generate-sql", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [(3, "generate_sql", {"intent": "Top customers"})]


def test_transform_increment_date_requires_delta(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_increment_date(
            _inv("view.transform.increment-date", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_increment_date_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"column": "a", "delta": {"days": 1}, "new_column": "a2"})
    view_ops_cmd.view_transform_increment_date(
        _inv("view.transform.increment-date", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "increment_date", {"column": "a", "delta": {"days": 1}, "new_column": "a2"})
    ]


def test_transform_join_requires_on(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_join(_inv("view.transform.join", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_join_forwards_optional(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        {
            "foreign_view": 9,
            "join_type": "LEFT",
            "on": [{"left": "a", "right": "b"}],
            "select": ["a"],
            "column_prefix": "f_",
        },
    )
    view_ops_cmd.view_transform_join(_inv("view.transform.join", extra_args=["3"], input_file=doc))
    assert fake_service.view_call_log == [
        (
            3,
            "join",
            {
                "foreign_view": 9,
                "join_type": "LEFT",
                "on": [{"left": "a", "right": "b"}],
                "select": ["a"],
                "column_prefix": "f_",
            },
        )
    ]


def test_transform_json_extract_requires_column(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_json_extract(
            _inv("view.transform.json-extract", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_json_extract_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"column": "a", "keys": ["k1"], "keep_source": True})
    view_ops_cmd.view_transform_json_extract(
        _inv("view.transform.json-extract", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "json_extract", {"column": "a", "keys": ["k1"], "keep_source": True})
    ]


def test_transform_limit_rows_requires_n(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_limit_rows(_inv("view.transform.limit-rows", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_limit_rows_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"n": 10, "bottom": True})
    view_ops_cmd.view_transform_limit_rows(
        _inv("view.transform.limit-rows", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [(3, "limit_rows", {"n": 10, "bottom": True})]


def test_transform_lookup_requires_value(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_lookup(_inv("view.transform.lookup", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_lookup_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {"source": "a", "lookup_view_id": 9, "key": "k", "value": "v", "new_column": "nc"},
    )
    view_ops_cmd.view_transform_lookup(
        _inv("view.transform.lookup", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "lookup",
            {
                "source": "a",
                "lookup_view_id": 9,
                "key": "k",
                "value": "v",
                "new_column": "nc",
            },
        )
    ]


def test_transform_math_requires_expression(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_math(_inv("view.transform.math", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_math_forwards_optional(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"expression": "a + b", "new_column": "sum"})
    view_ops_cmd.view_transform_math(_inv("view.transform.math", extra_args=["3"], input_file=doc))
    assert fake_service.view_call_log == [(3, "math", {"expression": "a + b", "new_column": "sum"})]


def test_transform_pivot_requires_aggregations(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_pivot(_inv("view.transform.pivot", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_pivot_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(
        tmp_path,
        {
            "group_by": ["a"],
            "aggregations": [{"column": "b", "function": "SUM"}],
            "condition": {"column": "a", "operator": "EQ", "value": 1},
        },
    )
    view_ops_cmd.view_transform_pivot(
        _inv("view.transform.pivot", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "pivot",
            {
                "group_by": ["a"],
                "aggregations": [{"column": "b", "function": "SUM"}],
                "condition": {"column": "a", "operator": "EQ", "value": 1},
            },
        )
    ]


def test_transform_replace_requires_find(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_replace(_inv("view.transform.replace", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_replace_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"columns": ["a"], "find": "x", "replace": "y", "match_words": True})
    view_ops_cmd.view_transform_replace(
        _inv("view.transform.replace", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "replace_values",
            {"columns": ["a"], "find": "x", "replace": "y", "match_words": True},
        )
    ]


def test_transform_set_values_requires_values(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_set_values(_inv("view.transform.set-values", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_set_values_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"values": [{"value": "x"}], "new_column": "nc", "column_type": "TEXT"})
    view_ops_cmd.view_transform_set_values(
        _inv("view.transform.set-values", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "set_values",
            {"values": [{"value": "x"}], "new_column": "nc", "column_type": "TEXT"},
        )
    ]


def test_transform_small_large_requires_columns(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_small_large(
            _inv("view.transform.small-large", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_small_large_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"function": "SMALL", "columns": ["a"], "index": 2})
    view_ops_cmd.view_transform_small_large(
        _inv("view.transform.small-large", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "small_large", {"function": "SMALL", "columns": ["a"], "index": 2})
    ]


def test_transform_split_requires_new_columns(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_split(_inv("view.transform.split", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_split_forwards(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(
        tmp_path,
        {"column": "a", "delimiter": ",", "new_columns": [{"name": "a1"}, {"name": "a2"}]},
    )
    view_ops_cmd.view_transform_split(
        _inv("view.transform.split", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "split_column",
            {
                "column": "a",
                "delimiter": ",",
                "new_columns": [{"name": "a1"}, {"name": "a2"}],
            },
        )
    ]


def test_transform_substring_requires_column(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_substring(_inv("view.transform.substring", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_substring_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"column": "a", "num_char": 3, "direction": "LEFT"})
    view_ops_cmd.view_transform_substring(
        _inv("view.transform.substring", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "substring", {"column": "a", "num_char": 3, "direction": "LEFT"})
    ]


def test_transform_text_requires_columns(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_text(_inv("view.transform.text", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_text_forwards_optional(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"columns": ["a"], "case": "UPPER", "trim": True})
    view_ops_cmd.view_transform_text(_inv("view.transform.text", extra_args=["3"], input_file=doc))
    assert fake_service.view_call_log == [
        (3, "text_transform", {"columns": ["a"], "case": "UPPER", "trim": True})
    ]


def test_transform_unnest_requires_columns(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_unnest(_inv("view.transform.unnest", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_unnest_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"columns": ["a"], "label_column": "L"})
    view_ops_cmd.view_transform_unnest(
        _inv("view.transform.unnest", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [(3, "unnest", {"columns": ["a"], "label_column": "L"})]


def test_transform_window_requires_function(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_window(_inv("view.transform.window", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_window_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"function": "RANK", "partition_by": ["a"], "column": "b"})
    view_ops_cmd.view_transform_window(
        _inv("view.transform.window", extra_args=["3"], input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "window", {"function": "RANK", "partition_by": ["a"], "column": "b"})
    ]
