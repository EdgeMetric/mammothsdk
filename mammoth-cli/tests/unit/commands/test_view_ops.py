"""Unit tests for the ``view`` draft, transform, and view-CRUD handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import view_ops as view_ops_cmd
from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.invocation import Invocation, ResourceRef
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_CREATE = "mammoth.client.ViewsResource.create"
_GET = "mammoth.client.ViewsResource.get"
_DELETE = "mammoth.client.ViewsResource.delete"


@pytest.fixture(autouse=True)
def _env_auth(isolated_cli_config: Path) -> None:
    """Authenticate every test with a saved default profile."""
    login_default_profile()


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _parent(view_id: int) -> ResourceRef:
    """Exact parent context: non-read view commands refuse project-wide discovery."""
    return ResourceRef(dataset_id=122, view_id=view_id)


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


class _RichView:
    """Stand-in for the SDK ``View``: a record plus a discovered parent."""

    def __init__(self) -> None:
        self.raw = {"id": 7, "name": "View 1", "metadata": [{"display_name": "amount"}]}
        self.dataset_id = 63

    def get_data(self) -> None:  # pragma: no cover - method presence only
        raise AssertionError


def test_get_via_discovery_returns_the_dataview_record(
    fake_service: FakeMammothService,
) -> None:
    # Without an exact parent the SDK hands back a rich View object; the
    # envelope must carry its dataview record (and the discovered parent),
    # not "<unserializable View>".
    fake_service.responses[_GET] = _RichView()
    data, _ = view_ops_cmd.view_get(_inv("view.get", extra_args=["7"]))
    assert data == {
        "id": 7,
        "name": "View 1",
        "metadata": [{"display_name": "amount"}],
        "dataset_id": 63,
    }


def test_create_returns_the_dataview_record(fake_service: FakeMammothService) -> None:
    # ``ViewsResource.create`` also hands back a rich View; the envelope must
    # carry the new view's record so callers can read its id.
    fake_service.responses[_CREATE] = _RichView()
    data, _ = view_ops_cmd.view_create(_inv("view.create", extra_args=["63"]))
    assert data == {
        "id": 7,
        "name": "View 1",
        "metadata": [{"display_name": "amount"}],
        "dataset_id": 63,
    }


def test_delete_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_delete(_inv("view.delete", extra_args=["7"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.call_log == []


def test_delete_refuses_parent_discovery(fake_service: FakeMammothService) -> None:
    # A destructive call never falls back to the project-wide parent probe:
    # with no exact parent it fails closed before any SDK call.
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_delete(_inv("view.delete", extra_args=["7"], yes=True))
    assert excinfo.value.code == "resource_identity_required"
    assert fake_service.call_log == []


def test_delete_forwards_exact_parent_positional(fake_service: FakeMammothService) -> None:
    view_ops_cmd.view_delete(_inv("view.delete", extra_args=["7", "122"], yes=True))
    assert fake_service.call_log == [(_DELETE, {"view_id": 7, "dataset_id": 122})]


def test_delete_forwards_exact_parent_input(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"dataset_id": 122})
    view_ops_cmd.view_delete(_inv("view.delete", extra_args=["7"], input_file=doc, yes=True))
    assert fake_service.call_log == [(_DELETE, {"view_id": 7, "dataset_id": 122})]


def test_delete_uses_typed_resource_parent_without_probe(
    fake_service: FakeMammothService,
) -> None:
    view_ops_cmd.view_delete(
        _inv(
            "view.delete",
            extra_args=["7"],
            resource_ref=ResourceRef(workspace_id=4, project_id=180, dataset_id=122, view_id=7),
            yes=True,
        )
    )
    assert fake_service.call_log == [(_DELETE, {"view_id": 7, "dataset_id": 122})]


def test_get_rejects_conflicting_explicit_parent_identities(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"dataset_id": 122})
    with pytest.raises(CliError) as raised:
        view_ops_cmd.view_get(
            _inv(
                "view.get",
                extra_args=["7"],
                input_file=doc,
                resource_ref=ResourceRef(dataset_id=123, view_id=7),
            )
        )

    assert raised.value.code == "ambiguous_resource_identity"
    assert fake_service.call_log == []


def test_transform_uses_exact_resource_parent_in_parallel_project_scope(
    fake_service: FakeMammothService,
) -> None:
    view_ops_cmd.view_transform_discard_duplicates(
        _inv(
            "view.transform.add-column",
            extra_args=["7"],
            resource_ref=ResourceRef(project_id=180, dataset_id=122, view_id=7),
            project=180,
            positionals={"view_id": "7"},
        )
    )
    assert fake_service.view_call_log == [(7, "discard_duplicates", {"dataset_id": 122})]


def test_resource_reference_rejects_selected_profile_project_mismatch(
    fake_service: FakeMammothService,
) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4, project_id=181))
    with pytest.raises(CliError) as raised:
        view_ops_cmd.view_get(
            _inv(
                "view.get",
                extra_args=["7"],
                resource_ref=ResourceRef(project_id=180, dataset_id=122, view_id=7),
            )
        )

    assert raised.value.code == "invalid_resource_context"
    assert "effective project scope" in raised.value.message
    assert fake_service.call_log == []


# --- view draft * (``service.call_view`` seam) -----------------------------


def test_draft_enter_calls_view(fake_service: FakeMammothService) -> None:
    view_ops_cmd.view_draft_enter(
        _inv("view.draft.enter", extra_args=["3"], resource_ref=_parent(3))
    )
    assert fake_service.view_call_log == [(3, "enter_draft_mode", {"dataset_id": 122})]


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
    view_ops_cmd.view_draft_submit(
        _inv("view.draft.submit", extra_args=["3"], resource_ref=_parent(3))
    )
    assert fake_service.view_call_log == [(3, "submit_draft", {"dataset_id": 122})]


def test_draft_discard_blocked_without_confirmation(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_draft_discard(_inv("view.draft.discard", extra_args=["3"], output="json"))
    assert excinfo.value.code == "confirmation_required"
    assert fake_service.view_call_log == []


def test_draft_discard_proceeds_with_yes(fake_service: FakeMammothService) -> None:
    view_ops_cmd.view_draft_discard(
        _inv("view.draft.discard", extra_args=["3"], resource_ref=_parent(3), yes=True)
    )
    assert fake_service.view_call_log == [(3, "discard_draft", {"dataset_id": 122})]


def test_draft_auto_run_requires_enabled(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_draft_auto_run(_inv("view.draft.auto-run", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_draft_auto_run_forwards_enabled(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"enabled": True})
    view_ops_cmd.view_draft_auto_run(
        _inv("view.draft.auto-run", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [(3, "set_auto_run", {"dataset_id": 122, "enabled": True})]


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
        _inv("view.transform.add-column", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "add_column", {"dataset_id": 122, "name": "Col", "column_type": "NUMERIC"})
    ]


def test_transform_add_sql_requires_query(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_add_sql(_inv("view.transform.add-sql", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_add_sql_forwards_query(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"query": "SELECT 1"})
    view_ops_cmd.view_transform_add_sql(
        _inv("view.transform.add-sql", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [(3, "add_sql", {"dataset_id": 122, "query": "SELECT 1"})]


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
    view_ops_cmd.view_transform_ai(
        _inv("view.transform.ai", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "gen_ai",
            {
                "dataset_id": 122,
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
            "mapping": [{"search": ["x"], "replace": "y"}],
            "match_case": True,
            "condition": {"column": "a", "operator": "EQ", "value": 1},
        },
    )
    view_ops_cmd.view_transform_bulk_replace(
        _inv(
            "view.transform.bulk-replace", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert fake_service.view_call_log == [
        (
            3,
            "bulk_replace",
            {
                "dataset_id": 122,
                "columns": ["a"],
                "mapping": [{"search": ["x"], "replace": "y"}],
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
        _inv(
            "view.transform.combine-columns",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=doc,
        )
    )
    assert fake_service.view_call_log == [
        (3, "combine_columns", {"dataset_id": 122, "sources": ["a", "b"], "separator": "-"})
    ]


def test_transform_convert_type_requires_conversions(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_convert_type(
            _inv("view.transform.convert-type", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_convert_type_forwards(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"conversions": [{"column": "a", "to": "NUMERIC"}]})
    view_ops_cmd.view_transform_convert_type(
        _inv(
            "view.transform.convert-type", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert fake_service.view_call_log == [
        (3, "convert_type", {"dataset_id": 122, "conversions": [{"column": "a", "to": "NUMERIC"}]})
    ]


_DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_TYPED_METADATA = {
    "metadata": [
        {"display_name": "a", "internal_name": "column_1", "type": "NUMERIC"},
        {"display_name": "b", "internal_name": "column_2", "type": "TEXT"},
    ]
}


def test_transform_convert_type_skips_a_column_that_already_has_the_type(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # Converting NUMERIC -> NUMERIC puts the pipeline in ref_error on release.
    fake_service.responses[_DATAVIEW_GET] = _TYPED_METADATA
    doc = _write(
        tmp_path,
        {"conversions": [{"column": "a", "to": "NUMERIC"}, {"column": "b", "to": "NUMERIC"}]},
    )
    data, _ = view_ops_cmd.view_transform_convert_type(
        _inv(
            "view.transform.convert-type", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert fake_service.view_call_log == [
        (3, "convert_type", {"dataset_id": 122, "conversions": [{"column": "b", "to": "NUMERIC"}]})
    ]
    assert data["skipped"] == [{"column": "a", "type": "NUMERIC"}]


def test_transform_convert_type_adds_no_task_when_every_column_has_the_type(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[_DATAVIEW_GET] = _TYPED_METADATA
    doc = _write(tmp_path, {"conversions": [{"column": "a", "to": "NUMERIC"}]})
    data, _ = view_ops_cmd.view_transform_convert_type(
        _inv(
            "view.transform.convert-type", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert fake_service.view_call_log == []
    assert data["status"] == "no_change"
    assert data["skipped"] == [{"column": "a", "type": "NUMERIC"}]


def test_transform_copy_columns_requires_copies(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_copy_columns(
            _inv("view.transform.copy-columns", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_copy_columns_forwards(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"copies": [{"source": "a", "as_name": "a2"}]})
    view_ops_cmd.view_transform_copy_columns(
        _inv(
            "view.transform.copy-columns", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert fake_service.view_call_log == [
        (3, "copy_columns", {"dataset_id": 122, "copies": [{"source": "a", "as_name": "a2"}]})
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
        _inv("view.transform.crosstab", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "crosstab",
            {
                "dataset_id": 122,
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
    doc = _write(tmp_path, {"component": "DAY", "start": "a", "end": "b", "new_column": "diff"})
    view_ops_cmd.view_transform_date_diff(
        _inv("view.transform.date-diff", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "date_diff",
            {"dataset_id": 122, "component": "DAY", "start": "a", "end": "b", "new_column": "diff"},
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
        _inv(
            "view.transform.delete-columns",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=doc,
        )
    )
    assert fake_service.view_call_log == [
        (3, "delete_columns", {"dataset_id": 122, "columns": ["a", "b"]})
    ]


def test_transform_discard_duplicates_no_input(fake_service: FakeMammothService) -> None:
    view_ops_cmd.view_transform_discard_duplicates(
        _inv("view.transform.discard-duplicates", extra_args=["3"], resource_ref=_parent(3))
    )
    assert fake_service.view_call_log == [(3, "discard_duplicates", {"dataset_id": 122})]


def test_transform_discard_duplicates_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"ignore_columns": ["a"]})
    view_ops_cmd.view_transform_discard_duplicates(
        _inv(
            "view.transform.discard-duplicates",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=doc,
        )
    )
    assert fake_service.view_call_log == [
        (3, "discard_duplicates", {"dataset_id": 122, "ignore_columns": ["a"]})
    ]


def test_transform_extract_date_requires_component(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_extract_date(
            _inv("view.transform.extract-date", extra_args=["3"], input_file=None)
        )
    assert excinfo.value.code == "missing_field"


def test_transform_extract_date_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"column": "a", "component": "year", "new_column": "yr"})
    view_ops_cmd.view_transform_extract_date(
        _inv(
            "view.transform.extract-date", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert fake_service.view_call_log == [
        (
            3,
            "extract_date",
            {"dataset_id": 122, "column": "a", "component": "year", "new_column": "yr"},
        )
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
    doc = _write(tmp_path, {"column": "a", "direction": "LAST_VALUE", "partition_by": "b"})
    view_ops_cmd.view_transform_fill_missing(
        _inv(
            "view.transform.fill-missing", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert fake_service.view_call_log == [
        (
            3,
            "fill_missing",
            {"dataset_id": 122, "column": "a", "direction": "LAST_VALUE", "partition_by": "b"},
        )
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
            "filter_type": "REMOVE",
        },
    )
    view_ops_cmd.view_transform_filter(
        _inv("view.transform.filter", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "filter_rows",
            {
                "dataset_id": 122,
                "condition": {"column": "a", "operator": "EQ", "value": 1},
                "filter_type": "REMOVE",
            },
        )
    ]


def test_transform_generate_sql_requires_intent(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_generate_sql(
            _inv("view.transform.generate-sql", extra_args=["3"])
        )
    assert excinfo.value.code == "missing_field"


def test_transform_generate_sql_says_the_view_is_unchanged(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # The route returns a validated query and adds no task (release).
    query = 'SELECT "city", COUNT(*) AS n FROM "View 1" GROUP BY "city"'
    fake_service.view_responses[(3, "generate_sql")] = query
    doc = _write(tmp_path, {"intent": "Count rows per city"})
    data, _ = view_ops_cmd.view_transform_generate_sql(
        _inv(
            "view.transform.generate-sql", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert data["sql"] == query
    assert data["applied"] is False
    assert data["apply"].startswith("mammoth view transform add-sql 3 --input '")
    applied = json.loads(data["apply"].split("--input ", 1)[1].strip("'"))
    assert applied == {"dataset_id": 122, "query": query}


def test_transform_generate_sql_forwards(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"intent": "Top customers"})
    view_ops_cmd.view_transform_generate_sql(
        _inv(
            "view.transform.generate-sql", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert fake_service.view_call_log == [
        (3, "generate_sql", {"dataset_id": 122, "intent": "Top customers"})
    ]


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
        _inv(
            "view.transform.increment-date",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=doc,
        )
    )
    assert fake_service.view_call_log == [
        (
            3,
            "increment_date",
            {"dataset_id": 122, "column": "a", "delta": {"days": 1}, "new_column": "a2"},
        )
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
    view_ops_cmd.view_transform_join(
        _inv("view.transform.join", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "join",
            {
                "dataset_id": 122,
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
        _inv(
            "view.transform.json-extract", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert fake_service.view_call_log == [
        (3, "json_extract", {"dataset_id": 122, "column": "a", "keys": ["k1"], "keep_source": True})
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
        _inv("view.transform.limit-rows", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "limit_rows", {"dataset_id": 122, "n": 10, "bottom": True})
    ]


@pytest.mark.parametrize(
    "command_id,handler,field",
    [
        ("view.transform.rename-columns", "view_transform_rename_columns", "renames"),
        ("view.transform.sort", "view_transform_sort", "order_by"),
    ],
)
def test_display_setting_transforms_require_field(
    fake_service: FakeMammothService, command_id: str, handler: str, field: str
) -> None:
    with pytest.raises(CliError) as excinfo:
        getattr(view_ops_cmd, handler)(_inv(command_id, extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_rename_columns_forwards(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"renames": {"cust_id": "Customer ID"}})
    view_ops_cmd.view_transform_rename_columns(
        _inv(
            "view.transform.rename-columns",
            extra_args=["3"],
            resource_ref=_parent(3),
            input_file=doc,
        )
    )
    assert fake_service.view_call_log == [
        (3, "rename_columns", {"dataset_id": 122, "renames": {"cust_id": "Customer ID"}})
    ]


def test_transform_sort_forwards(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"order_by": [["Revenue", "DESC"]]})
    view_ops_cmd.view_transform_sort(
        _inv("view.transform.sort", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "sort_rows", {"dataset_id": 122, "order_by": [["Revenue", "DESC"]]})
    ]


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
        _inv("view.transform.lookup", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "lookup",
            {
                "dataset_id": 122,
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
    view_ops_cmd.view_transform_math(
        _inv("view.transform.math", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "math", {"dataset_id": 122, "expression": "a + b", "new_column": "sum"})
    ]


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
        _inv("view.transform.pivot", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "pivot",
            {
                "dataset_id": 122,
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
        _inv("view.transform.replace", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "replace_values",
            {"dataset_id": 122, "columns": ["a"], "find": "x", "replace": "y", "match_words": True},
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
        _inv("view.transform.set-values", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "set_values",
            {
                "dataset_id": 122,
                "values": [{"value": "x"}],
                "new_column": "nc",
                "column_type": "TEXT",
            },
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
        _inv(
            "view.transform.small-large", extra_args=["3"], resource_ref=_parent(3), input_file=doc
        )
    )
    assert fake_service.view_call_log == [
        (3, "small_large", {"dataset_id": 122, "function": "SMALL", "columns": ["a"], "index": 2})
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
        _inv("view.transform.split", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (
            3,
            "split_column",
            {
                "dataset_id": 122,
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
    doc = _write(tmp_path, {"column": "a", "num_char": 3, "direction": "START"})
    view_ops_cmd.view_transform_substring(
        _inv("view.transform.substring", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "substring", {"dataset_id": 122, "column": "a", "num_char": 3, "direction": "START"})
    ]


def test_transform_substring_rejects_left_with_numchar(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"column": "a", "num_char": 3, "direction": "LEFT"})
    invocation = _inv("view.transform.substring", extra_args=["3"], input_file=doc)
    assert invocation.load_input() == {
        "column": "a",
        "num_char": 3,
        "direction": "LEFT",
        "view_id": "3",
    }
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_substring(invocation)
    assert excinfo.value.code == "invalid_argument"
    assert fake_service.view_call_log == []


def test_transform_text_requires_columns(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_text(_inv("view.transform.text", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_text_forwards_optional(fake_service: FakeMammothService, tmp_path: Path) -> None:
    doc = _write(tmp_path, {"columns": ["a"], "case": "UPPER", "trim": True})
    view_ops_cmd.view_transform_text(
        _inv("view.transform.text", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "text_transform", {"dataset_id": 122, "columns": ["a"], "case": "UPPER", "trim": True})
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
        _inv("view.transform.unnest", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "unnest", {"dataset_id": 122, "columns": ["a"], "label_column": "L"})
    ]


def test_transform_window_requires_function(fake_service: FakeMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_window(_inv("view.transform.window", extra_args=["3"]))
    assert excinfo.value.code == "missing_field"


def test_transform_window_forwards_optional(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = _write(tmp_path, {"function": "RANK", "partition_by": ["a"], "column": "b"})
    view_ops_cmd.view_transform_window(
        _inv("view.transform.window", extra_args=["3"], resource_ref=_parent(3), input_file=doc)
    )
    assert fake_service.view_call_log == [
        (3, "window", {"dataset_id": 122, "function": "RANK", "partition_by": ["a"], "column": "b"})
    ]


@pytest.mark.parametrize(
    ("handler", "command_id", "payload"),
    [
        (
            "view_transform_filter",
            "view.transform.filter",
            {"condition": {"column": "a", "operator": "LT", "value": 0}, "filter_type": "REMOVE"},
        ),
        (
            "view_transform_math",
            "view.transform.math",
            {"expression": "ABS(a)", "existing_column": "a"},
        ),
        (
            "view_transform_join",
            "view.transform.join",
            {
                "foreign_view": 9,
                "join_type": "OUTER",
                "on": [{"left": "a", "right": "a"}],
                "select": [{"column": "b"}],
            },
        ),
        ("view_draft_enter", "view.draft.enter", None),
    ],
)
def test_non_read_view_ops_refuse_parent_discovery(
    fake_service: FakeMammothService,
    tmp_path: Path,
    handler: str,
    command_id: str,
    payload: dict[str, Any] | None,
) -> None:
    # Without an exact parent the SDK would browse every folder and probe
    # every dataset in the project; on large projects that path 500s or
    # misses the view and used to surface as an opaque api_error. Fail
    # closed before any SDK call and hand back the read that supplies it.
    overrides: dict[str, Any] = {"extra_args": ["308772"], "project": 4301}
    if payload is not None:
        overrides["input_file"] = _write(tmp_path, payload)
    with pytest.raises(CliError) as excinfo:
        getattr(view_ops_cmd, handler)(_inv(command_id, **overrides))
    assert excinfo.value.code == "missing_argument"
    assert excinfo.value.recovery_commands == ["mammoth view get 308772 --project 4301"]
    assert fake_service.view_call_log == []
    assert fake_service.call_log == []


_DV_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_BRIEF = (
    "id,ds_id,name,status,row_count,column_count,metadata,pipeline_status,"
    "is_pipeline_running,is_dataview_data_in_sync,data_updated_at,updated_at,display_properties"
)


def test_get_with_exact_parent_asks_the_server_for_the_brief_projection(
    fake_service: FakeMammothService,
) -> None:
    # The standard dataview record is ~5x the brief one (dependencies_info,
    # display trees); the GET route projects server-side.
    view_ops_cmd.view_get(_inv("view.get", extra_args=["7", "63"]))
    assert fake_service.call_log == [
        (_DV_GET, {"dataset_id": 63, "dataview_id": 7, "fields": _BRIEF})
    ]


def test_get_fields_input_overrides_the_projection(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    doc = tmp_path / "in.json"
    doc.write_text('{"fields": "__full"}', encoding="utf-8")
    view_ops_cmd.view_get(_inv("view.get", extra_args=["7", "63"], input_file=str(doc)))
    assert fake_service.call_log[-1][1]["fields"] == "__full"


def test_get_via_discovery_trims_to_the_brief_shape(fake_service: FakeMammothService) -> None:
    rich = _RichView()
    rich.raw = {
        "id": 7,
        "ds_id": 63,
        "name": "View 1",
        "status": "ready",
        "row_count": 3,
        "metadata": [{"display_name": "amount"}],
        "dependencies_info": {"dependees": {"7": {"DISPLAY_PROPERTIES": {}}}},
        "display_properties": {"COLUMN_ORDER": {}},
    }
    fake_service.responses[_GET] = rich
    data, _ = view_ops_cmd.view_get(_inv("view.get", extra_args=["7"]))
    assert "dependencies_info" not in data and "display_properties" not in data
    assert data["row_count"] == 3 and data["dataset_id"] == 63 and data["ds_id"] == 63


_RENAMED = {
    "id": 7,
    "metadata": [
        {"display_name": "cust_ref", "internal_name": "column_2"},
        {"display_name": "qty", "internal_name": "column_5"},
    ],
    "display_properties": {"COLUMN_NAMES": {"column_2": "Customer Ref"}},
}


def test_exact_get_shows_renamed_columns_and_drops_display_properties(
    fake_service: FakeMammothService,
) -> None:
    fake_service.responses[_DV_GET] = dict(_RENAMED)
    data, _ = view_ops_cmd.view_get(_inv("view.get", extra_args=["7", "63"]))
    assert [c["display_name"] for c in data["metadata"]] == ["Customer Ref", "qty"]
    assert "display_properties" not in data


def test_discovery_get_shows_renamed_columns(fake_service: FakeMammothService) -> None:
    rich = _RichView()
    rich.raw = dict(_RENAMED)
    fake_service.responses[_GET] = rich
    data, _ = view_ops_cmd.view_get(_inv("view.get", extra_args=["7"]))
    assert [c["display_name"] for c in data["metadata"]] == ["Customer Ref", "qty"]


def test_discovery_get_with_fields_keeps_the_full_record(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # The discovery route has no projection: ``fields`` must not reach the
    # SDK (it raised "unexpected keyword argument 'fields'") and the full
    # record comes back.
    rich = _RichView()
    rich.raw = dict(_RENAMED)
    fake_service.responses[_GET] = rich
    doc = _write(tmp_path, {"fields": "__full"})
    data, _ = view_ops_cmd.view_get(_inv("view.get", extra_args=["7"], input_file=doc))
    assert fake_service.call_log == [(_GET, {"view_id": 7})]
    assert data["display_properties"] == _RENAMED["display_properties"]
    assert data["metadata"][0]["display_name"] == "Customer Ref"


# --- reference errors after a pipeline mutation ---------------------------


def _programme_reference_error(fake_service: FakeMammothService, view_id: int) -> None:
    fake_service.view_responses[(view_id, "bulk_replace")] = {
        "has_error": True,
        "status": "done",
        "type_of_modification": "add_rule",
    }
    fake_service.responses[view_ops_cmd._PIPELINE_SYMBOL] = {"state": "ref_error"}
    fake_service.responses[view_ops_cmd._PIPELINE_ITEMS_SYMBOL] = {
        "items": [
            {"id": 91, "item_type": "task", "sequence": 1, "status": "executed"},
            {
                "id": 107,
                "item_type": "task",
                "sequence": 2,
                "status": "added",
                "reference_errors": {
                    "type": "referror",
                    "reference_errors": [
                        {
                            "column": {
                                "display_name": "amount",
                                "internal_name": "column_4",
                                "type": "NUMERIC",
                            },
                            "reason": "type mismatch",
                            "error_code": 7003,
                        }
                    ],
                },
            },
        ]
    }


def test_transform_with_reference_errors_fails_with_the_repair_command(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    _programme_reference_error(fake_service, 132)
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_bulk_replace(
            _inv(
                "view.transform.bulk-replace",
                extra_args=["132"],
                resource_ref=_parent(132),
                positionals={"view_id": "132"},
                input_file=_write(
                    tmp_path,
                    {"columns": ["amount"], "mapping": [{"search": ["$"], "replace": ""}]},
                ),
            )
        )
    error = excinfo.value
    assert error.code == view_ops_cmd.CODE_PIPELINE_REFERENCE_ERROR
    assert error.exit_status == 1
    assert error.details["pipeline_state"] == "ref_error"
    assert error.details["task_ids"] == [107]
    assert error.details["reference_errors"] == [
        {
            "column": "amount",
            "internal_name": "column_4",
            "type": "NUMERIC",
            "reason": "type mismatch",
            "error_code": 7003,
        }
    ]
    assert error.recovery_commands == [
        "mammoth view task delete 132 107 --yes --input '{\"dataset_id\": 122}'"
    ]
    assert "amount" in error.message and "TEXT" in (error.hint or "")
    # The follow-up reads carry the exact parent so they never fall into discovery.
    assert (
        view_ops_cmd._PIPELINE_ITEMS_SYMBOL,
        {"dataview_id": 132, "dataset_id": 122, "fields": "__full"},
    ) in fake_service.call_log


def test_transform_without_has_error_is_untouched(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.view_responses[(132, "bulk_replace")] = {"has_error": False, "status": "done"}
    data, _meta = view_ops_cmd.view_transform_bulk_replace(
        _inv(
            "view.transform.bulk-replace",
            extra_args=["132"],
            resource_ref=_parent(132),
            positionals={"view_id": "132"},
            input_file=_write(
                tmp_path, {"columns": ["amount"], "mapping": [{"search": ["$"], "replace": ""}]}
            ),
        )
    )
    assert data == {"has_error": False, "status": "done"}
    assert view_ops_cmd._PIPELINE_SYMBOL not in fake_service.calls


def test_reference_error_survives_a_failed_follow_up_read(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    _programme_reference_error(fake_service, 132)
    fake_service.responses[view_ops_cmd._PIPELINE_ITEMS_SYMBOL] = CliError(
        code="api_error", message="boom", exit_status=1
    )
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_bulk_replace(
            _inv(
                "view.transform.bulk-replace",
                extra_args=["132"],
                resource_ref=_parent(132),
                positionals={"view_id": "132"},
                input_file=_write(
                    tmp_path,
                    {"columns": ["amount"], "mapping": [{"search": ["$"], "replace": ""}]},
                ),
            )
        )
    error = excinfo.value
    assert error.code == view_ops_cmd.CODE_PIPELINE_REFERENCE_ERROR
    assert error.details["task_ids"] == []
    assert error.recovery_commands == [
        'mammoth view pipeline items 132 --input \'{"fields": "__full"}\''
    ]


def test_sdk_raised_reference_error_is_enriched_the_same_way(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    _programme_reference_error(fake_service, 132)
    fake_service.view_responses[(132, "bulk_replace")] = CliError(
        code="api_error",
        message="Mammoth could not complete the operation.",
        exit_status=1,
        details={"dataview_id": 132, "response": {"has_error": True, "status": "done"}},
    )
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_bulk_replace(
            _inv(
                "view.transform.bulk-replace",
                extra_args=["132"],
                resource_ref=_parent(132),
                positionals={"view_id": "132"},
                input_file=_write(
                    tmp_path, {"columns": ["amount"], "mapping": [{"search": ["$"], "replace": ""}]}
                ),
            )
        )
    assert excinfo.value.code == view_ops_cmd.CODE_PIPELINE_REFERENCE_ERROR
    assert excinfo.value.recovery_commands == [
        "mammoth view task delete 132 107 --yes --input '{\"dataset_id\": 122}'"
    ]


# -- expected_task_count precondition --------------------------------------


def _filter_doc(tmp_path: Path, expected: object) -> str:
    return _write(
        tmp_path,
        {
            "expected_task_count": expected,
            "filter_type": "REMOVE",
            "condition": {"column": "Status", "operator": "EQ", "value": "x"},
        },
    )


def test_expected_task_count_mismatch_refuses_the_write(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[view_ops_cmd._TASK_LIST_SYMBOL] = {"tasks": [{"id": 1}, {"id": 2}]}
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_filter(
            _inv(
                "view.transform.filter",
                extra_args=["132"],
                resource_ref=_parent(132),
                positionals={"view_id": "132"},
                input_file=_filter_doc(tmp_path, 1),
            )
        )
    error = excinfo.value
    assert error.code == view_ops_cmd.CODE_PIPELINE_CHANGED
    assert error.details["expected_task_count"] == 1
    assert error.details["actual_task_count"] == 2
    assert error.details["task_ids"] == [1, 2]
    assert error.recovery_commands == ["mammoth view task list 132"]
    # The precondition read carried the exact parent, and no write followed.
    assert fake_service.call_log == [
        (view_ops_cmd._TASK_LIST_SYMBOL, {"dataview_id": 132, "dataset_id": 122})
    ]
    assert fake_service.view_call_log == []


def test_expected_task_count_match_lets_the_write_through_without_the_field(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.responses[view_ops_cmd._TASK_LIST_SYMBOL] = {"tasks": [{"id": 1}, {"id": 2}]}
    fake_service.view_responses[(132, "filter_rows")] = {"has_error": False}
    view_ops_cmd.view_transform_filter(
        _inv(
            "view.transform.filter",
            extra_args=["132"],
            resource_ref=_parent(132),
            positionals={"view_id": "132"},
            input_file=_filter_doc(tmp_path, 2),
        )
    )
    view_id, method, kwargs = fake_service.view_call_log[0]
    assert (view_id, method) == (132, "filter_rows")
    assert "expected_task_count" not in kwargs


def test_expected_task_count_must_be_a_non_negative_integer(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as excinfo:
        view_ops_cmd.view_transform_filter(
            _inv(
                "view.transform.filter",
                extra_args=["132"],
                resource_ref=_parent(132),
                positionals={"view_id": "132"},
                input_file=_filter_doc(tmp_path, -1),
            )
        )
    assert excinfo.value.code == "invalid_resource_context"
    assert fake_service.call_log == []
