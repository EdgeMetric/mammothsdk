"""Contract tests for typed ``View.export`` destination routes."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from mammoth.models.exports import (
    ExportStatus,
    HandlerType,
    ItemExportInfo,
    PipelineExportsPaginated,
)
from mammoth.view import ViewExport

from mammoth_cli.commands import view as view_cmd
from mammoth_cli.commands.view import _SPECIAL_EXPORT_COMMON_FIELDS, _SPECIAL_EXPORTS
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import POLICY_NONE
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.verify import with_verify
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import login_default_profile

_DATAVIEW_LIST = "mammoth.api.dataviews.DataviewsAPI.list"
_EXPORTS_LIST = "mammoth.api.exports.ExportsAPI.list"
_WAIT_FOR_PIPELINE = "mammoth.api.pipeline.PipelineAPI.wait_for_pipeline"
_DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
_PIPELINE_GET = "mammoth.api.pipeline.PipelineAPI.get_pipeline"


def _dataset_schema(*display_names: str) -> dict[str, object]:
    # The real ``GET .../datasets/{id}`` shape (probed on a live server): the
    # dataset is nested under "dataset", and each schema column names itself
    # with ``c_name`` next to its internal ``c_id``.
    return {
        "dataset": {
            "data_schema": [
                {"c_id": f"column_{i}", "c_name": name, "c_type": "text"}
                for i, name in enumerate(display_names, start=1)
            ]
        }
    }


def _exports_page(*items: ItemExportInfo) -> PipelineExportsPaginated:
    return PipelineExportsPaginated(limit=50, offset=0, next="", exports=list(items))


def _internal_dataset_export(
    export_id: int, target_ds_id: object, *, status: ExportStatus | None = None
) -> ItemExportInfo:
    return ItemExportInfo(
        id=export_id,
        handler_type=HandlerType.INTERNAL_DATASET,
        target_properties={"TARGET_DS_ID": target_ds_id},
        status=status,
    )


def _inv(command_id: str, **overrides: object) -> Invocation:
    return Invocation(command_id=command_id, **overrides)  # type: ignore[arg-type]


def _doc(tmp_path: Path, payload: dict[str, object]) -> str:
    path = tmp_path / "input.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


@pytest.fixture(autouse=True)
def _auth(isolated_cli_config: Path) -> None:
    login_default_profile()


def test_dataset_route_uses_view_export_and_exact_parent(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=180,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, {"dataset_name": "snapshot", "timeout": 30}),
            yes=True,
        )
    )
    assert fake_service.view_call_log == [
        (7, "to_dataset", {"dataset_id": 9, "dataset_name": "snapshot", "timeout": 30})
    ]


def test_dataset_route_names_the_written_dataset_and_its_project(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.view_responses[(7, "to_dataset")] = 114
    data, _meta = view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=58,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, {"dataset_name": "feed", "target_project_id": 57}),
            yes=True,
        )
    )
    assert fake_service.view_call_log == [
        (7, "to_dataset", {"dataset_id": 9, "dataset_name": "feed", "target_project_id": 57})
    ]
    assert data == {
        "dataset_id": 114,
        "project_id": 57,
        "source_view_id": 7,
        "refreshes_on_pipeline_run": True,
        "next": "mammoth view list 114 --project 57",
        "row_check": {"rows_before": None, "rows_after": None},
    }


def test_dataset_route_reports_rows_after_for_a_new_dataset(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.view_responses[(7, "to_dataset")] = 114
    fake_service.responses[_DATAVIEW_LIST] = {"dataviews": [{"id": 500, "row_count": 42}]}
    data, _meta = view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=180,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, {"dataset_name": "snapshot"}),
            yes=True,
        )
    )
    assert data["row_check"] == {"rows_before": None, "rows_after": 42}
    assert data["refreshes_on_pipeline_run"] is True
    assert (_DATAVIEW_LIST, {"dataset_id": 114, "project_id": 180}) in fake_service.call_log


def test_dataset_route_reports_settled_row_counts_for_append_into_existing_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """Regression for eval W2 (2026-09-26): ``rows_after`` used to come from a
    read taken immediately after the write, before the target view's row
    count had recomputed -- stale by construction, so it was omitted rather
    than reported wrong. ``wait_for_pipeline_to_settle`` now resolves that
    same race instead of sidestepping it, so both counts are reported: one
    read before the write (``rows_before``), and one read after waiting for
    the target's pipeline to settle (``rows_after``).
    """
    fake_service.view_responses[(7, "to_dataset")] = 9
    fake_service.responses[_DATAVIEW_LIST] = {"dataviews": [{"id": 500, "row_count": 60}]}
    fake_service.responses[_DATASET_GET] = _dataset_schema()
    data, _meta = view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=180,
            extra_args=["7", "3"],
            input_file=_doc(
                tmp_path,
                {"dataset_name": "orders", "target_ds_id": 9, "save_as_mode": "APPEND_TO_DS"},
            ),
            yes=True,
        )
    )
    assert data["row_check"] == {
        "rows_before": 60,
        "rows_after": 60,
        "expected_row_increase": True,
    }
    assert data["refreshes_on_pipeline_run"] is True
    # One read ahead of the write (rows_before), one to discover the view id
    # to wait on, and one settled re-read after the wait (rows_after).
    assert fake_service.call_log.count((_DATAVIEW_LIST, {"dataset_id": 9, "project_id": 180})) == 3
    assert (
        _WAIT_FOR_PIPELINE,
        {"dataview_id": 500, "dataset_id": 9, "timeout": 60.0},
    ) in fake_service.call_log
    assert (
        _EXPORTS_LIST,
        {"dataview_id": 7, "dataset_id": 3, "handler_type": HandlerType.INTERNAL_DATASET},
    ) in fake_service.call_log


def test_dataset_route_marks_an_append_that_adds_no_rows_as_unverified(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """An APPEND_TO_DS that leaves the target's row count unchanged is not a
    successful append; ``row_check`` carries ``expected_row_increase`` so
    :mod:`mammoth_cli.runtime.verify` marks it unverified instead of trusting
    a flat row count.
    """
    fake_service.view_responses[(7, "to_dataset")] = 9
    fake_service.responses[_DATAVIEW_LIST] = {"dataviews": [{"id": 500, "row_count": 60}]}
    fake_service.responses[_DATASET_GET] = _dataset_schema()
    data, _meta = view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=180,
            extra_args=["7", "3"],
            input_file=_doc(
                tmp_path,
                {"dataset_name": "orders", "target_ds_id": 9, "save_as_mode": "APPEND_TO_DS"},
            ),
            yes=True,
        )
    )
    verified = with_verify(data)["verify"]
    assert verified["verified"] is False
    assert verified["needs_user"] is None
    assert verified["reason"] == "the append did not add rows"


def test_dataset_route_rejects_append_when_source_has_unmapped_columns(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """An APPEND_TO_DS whose source view has a column the target dataset's
    schema does not, with no ``column_mapping`` entry for it, is refused
    before any write -- an append that silently drops or mismatches a
    column is worse than an early, explicit refusal.
    """
    fake_service.responses[_DATASET_GET] = _dataset_schema("Region")
    fake_service.view_responses[(7, "columns")] = {"Region": "column_1", "Amount": "column_2"}
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.dataset",
                project=180,
                extra_args=["7", "3"],
                input_file=_doc(
                    tmp_path,
                    {"dataset_name": "orders", "target_ds_id": 9, "save_as_mode": "APPEND_TO_DS"},
                ),
                yes=True,
            )
        )
    assert excinfo.value.code == "append_schema_mismatch"
    assert "Amount" in excinfo.value.message
    assert excinfo.value.details == {"source_only": ["Amount"], "target_only": []}
    assert "to_dataset" not in [call[1] for call in fake_service.view_call_log]


def test_dataset_route_matches_the_target_datasets_own_schema_not_its_views(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """Regression: the target VIEW can carry a rename task that disagrees
    with the target DATASET's own schema (evidence: a target view renamed
    'Cust ID' -> 'cust_id' while the dataset's data_schema still said
    'Cust ID'). The backend's own append-schema match
    (match_existing_target_schema) compares against the dataset's schema,
    not any view's live columns -- so this check must too, or a real
    mismatch (source 'cust_id' vs. dataset schema 'Cust ID') would pass
    when it should be refused.
    """
    fake_service.responses[_DATASET_GET] = _dataset_schema("Cust ID")
    fake_service.view_responses[(7, "columns")] = {"cust_id": "column_1"}
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.dataset",
                project=180,
                extra_args=["7", "3"],
                input_file=_doc(
                    tmp_path,
                    {"dataset_name": "orders", "target_ds_id": 9, "save_as_mode": "APPEND_TO_DS"},
                ),
                yes=True,
            )
        )
    assert excinfo.value.code == "append_schema_mismatch"
    assert excinfo.value.details["source_only"] == ["cust_id"]
    assert (_DATASET_GET, {"dataset_id": 9}) in fake_service.call_log
    # Only the source view's own columns are consulted -- never a target
    # VIEW's, which is exactly the mismatch this regression covers.
    assert fake_service.view_call_log == [(7, "columns", {"dataset_id": 3})]


def test_dataset_route_source_columns_are_display_names_not_internal(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """``call_view(view_id, "columns", ...)`` returns ``View.columns``: a
    display-name -> internal-name mapping (mammoth/view.py). The mismatch
    check must compare display names -- what the backend's own schema match
    uses -- never the internal ids in the dict's values.
    """
    fake_service.view_responses[(7, "to_dataset")] = 9
    fake_service.responses[_DATASET_GET] = _dataset_schema("Region")
    fake_service.view_responses[(7, "columns")] = {"Region": "some_internal_id_999"}
    data, _meta = view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=180,
            extra_args=["7", "3"],
            input_file=_doc(
                tmp_path,
                {"dataset_name": "orders", "target_ds_id": 9, "save_as_mode": "APPEND_TO_DS"},
            ),
            yes=True,
        )
    )
    # "Region" (the display name) matched the target schema; the internal id
    # "some_internal_id_999" was never treated as a column name to compare.
    assert data["dataset_id"] == 9


def test_dataset_route_raises_when_source_columns_are_unreadable(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """An unreadable/malformed source-view column read must never be treated
    as "no columns" (which would silently pass the check and let the write
    through) -- fail loud instead.
    """
    fake_service.view_responses[(7, "columns")] = "not a dict"
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.dataset",
                project=180,
                extra_args=["7", "3"],
                input_file=_doc(
                    tmp_path,
                    {"dataset_name": "orders", "target_ds_id": 9, "save_as_mode": "APPEND_TO_DS"},
                ),
                yes=True,
            )
        )
    assert excinfo.value.code == "append_schema_unreadable"
    assert excinfo.value.details["side"] == "source"
    assert "to_dataset" not in [call[1] for call in fake_service.view_call_log]


def test_dataset_route_raises_when_target_schema_is_unreadable(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.view_responses[(7, "columns")] = {"Region": "column_1"}
    fake_service.responses[_DATASET_GET] = {"dataset": {"data_schema": "not a list"}}
    with pytest.raises(CliError) as excinfo:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.dataset",
                project=180,
                extra_args=["7", "3"],
                input_file=_doc(
                    tmp_path,
                    {"dataset_name": "orders", "target_ds_id": 9, "save_as_mode": "APPEND_TO_DS"},
                ),
                yes=True,
            )
        )
    assert excinfo.value.code == "append_schema_unreadable"
    assert excinfo.value.details["side"] == "target"
    assert "to_dataset" not in [call[1] for call in fake_service.view_call_log]


def test_dataset_route_allows_append_when_column_mapping_covers_the_difference(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.view_responses[(7, "to_dataset")] = 9
    fake_service.responses[_DATASET_GET] = _dataset_schema("Region", "Amount")
    fake_service.view_responses[(7, "columns")] = {"Region": "column_1", "Amt": "column_2"}
    data, _meta = view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=180,
            extra_args=["7", "3"],
            input_file=_doc(
                tmp_path,
                {
                    "dataset_name": "orders",
                    "target_ds_id": 9,
                    "save_as_mode": "APPEND_TO_DS",
                    "column_mapping": {"Amt": "Amount"},
                },
            ),
            yes=True,
        )
    )
    assert data["dataset_id"] == 9
    assert "warnings" not in data.get("row_check", {})


def test_dataset_route_warns_when_target_has_columns_the_source_lacks(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    fake_service.view_responses[(7, "to_dataset")] = 9
    fake_service.responses[_DATAVIEW_LIST] = {"dataviews": [{"id": 500, "row_count": 60}]}
    fake_service.responses[_DATASET_GET] = _dataset_schema("Region", "Notes")
    fake_service.view_responses[(7, "columns")] = {"Region": "column_1"}
    data, _meta = view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=180,
            extra_args=["7", "3"],
            input_file=_doc(
                tmp_path,
                {"dataset_name": "orders", "target_ds_id": 9, "save_as_mode": "APPEND_TO_DS"},
            ),
            yes=True,
        )
    )
    assert data["row_check"]["warnings"] == [
        "target dataset has column(s) the source view does not (kept as-is): Notes"
    ]
    verified = with_verify(data)["verify"]
    assert "target dataset has column(s)" in verified["warnings"][0]


def test_dataset_route_rejects_a_second_export_into_the_same_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """Regression for eval W2 (2026-09-26): a repeat ``view export dataset``
    into a target this view already exports into must fail loud instead of
    creating a second persistent trigger -- each is a separate writer, so
    ``REPLACE_IN_DS``/``APPEND_TO_DS`` only ever replaces/appends its OWN
    trigger's rows, and the target's row count balloons on every rerun.
    """
    fake_service.responses[_EXPORTS_LIST] = _exports_page(_internal_dataset_export(42, 1545))
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.dataset",
                project=180,
                extra_args=["1758", "1544"],
                input_file=_doc(
                    tmp_path,
                    {
                        "dataset_name": "YouTube CPM benchmark",
                        "target_ds_id": 1545,
                        "save_as_mode": "REPLACE_IN_DS",
                    },
                ),
                yes=True,
            )
        )
    assert error.value.code == "export_already_exists"
    assert "view 1758" in error.value.message.lower()
    assert "dataset 1545" in error.value.message.lower()
    assert "export 42" in error.value.message.lower()
    assert "re-runs on every pipeline run" in error.value.message
    assert "replace_in_ds" in error.value.message.lower()
    assert error.value.recovery_commands == ["mammoth view pipeline rerun 1758"]
    assert fake_service.view_call_log == []


def test_dataset_route_export_guard_matches_target_ds_id_as_int(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """The existing export's ``TARGET_DS_ID`` can come back as a string on
    the wire; the comparison must not silently miss that match (mirrors the
    int/str fix already applied to the SDK's own write-confirmation poll).
    """
    fake_service.responses[_EXPORTS_LIST] = _exports_page(_internal_dataset_export(42, "1545"))
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.dataset",
                project=180,
                extra_args=["1758", "1544"],
                input_file=_doc(tmp_path, {"dataset_name": "feed", "target_ds_id": 1545}),
                yes=True,
            )
        )
    assert error.value.code == "export_already_exists"
    assert fake_service.view_call_log == []


def test_dataset_route_export_guard_ignores_a_soft_deleted_export(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """mvc-service soft-deletes a trigger (status -> ExportStatus.DELETED)
    rather than removing its row, and the exports-list endpoint does not
    filter on status (api/api/dataview/actions/actions.py:887,
    apiv2/apiv2/dataview_pipeline/exports/controller.py:151). A deleted
    export into the target must not count as an existing writer -- or a
    once-deleted export would block every later export into that target
    forever.
    """
    fake_service.responses[_EXPORTS_LIST] = _exports_page(
        _internal_dataset_export(42, 1545, status=ExportStatus.DELETED)
    )
    fake_service.view_responses[(1758, "to_dataset")] = 1545
    view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=180,
            extra_args=["1758", "1544"],
            input_file=_doc(
                tmp_path,
                {
                    "dataset_name": "YouTube CPM benchmark",
                    "target_ds_id": 1545,
                    "save_as_mode": "REPLACE_IN_DS",
                },
            ),
            yes=True,
        )
    )
    assert fake_service.view_call_log == [
        (
            1758,
            "to_dataset",
            {
                "dataset_id": 1544,
                "dataset_name": "YouTube CPM benchmark",
                "target_ds_id": 1545,
                "save_as_mode": "REPLACE_IN_DS",
            },
        )
    ]


def test_dataset_route_allows_first_export_into_an_existing_target(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """No existing export from this view into the target -> the write
    proceeds normally (an unrelated export, or none at all, must not block
    it)."""
    fake_service.responses[_EXPORTS_LIST] = _exports_page(_internal_dataset_export(7, 9001))
    fake_service.view_responses[(7, "to_dataset")] = 9
    view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=180,
            extra_args=["7", "3"],
            input_file=_doc(tmp_path, {"dataset_name": "orders", "target_ds_id": 9}),
            yes=True,
        )
    )
    assert fake_service.view_call_log == [
        (7, "to_dataset", {"dataset_id": 3, "dataset_name": "orders", "target_ds_id": 9})
    ]


def test_dataset_route_rejects_target_ds_id_equal_to_own_dataset(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.dataset",
                project=180,
                extra_args=["7", "9"],
                input_file=_doc(tmp_path, {"dataset_name": "snapshot", "target_ds_id": 9}),
                yes=True,
            )
        )
    assert error.value.code == "invalid_arguments"
    assert error.value.hint is not None
    assert "own dataset" in error.value.hint
    assert fake_service.view_call_log == []


def test_dataset_route_inlines_the_target_view_instead_of_a_relist_hint(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    # A dataset export (create or append) never changes the target dataset's
    # view id; when it can be resolved here, the response carries it instead
    # of sending the agent back through a separate 'view list' call.
    fake_service.view_responses[(7, "to_dataset")] = 114
    fake_service.responses["mammoth.api.dataviews.DataviewsAPI.list"] = {
        "dataviews": [{"id": 220, "name": "Store sales combined"}]
    }
    data, _meta = view_cmd.view_export_specialized(
        _inv(
            "view.export.dataset",
            project=58,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, {"dataset_name": "feed", "target_ds_id": 114}),
            yes=True,
        )
    )
    assert data == {
        "dataset_id": 114,
        "project_id": 58,
        "source_view_id": 7,
        "refreshes_on_pipeline_run": True,
        "view_id": 220,
        "view_name": "Store sales combined",
        "row_check": {"rows_before": None, "rows_after": None},
    }
    assert "next" not in data
    assert (
        "mammoth.api.dataviews.DataviewsAPI.list",
        {"dataset_id": 114, "project_id": 58},
    ) in fake_service.call_log


@pytest.mark.parametrize("file_type", ["csv", "json", "parquet"])
def test_managed_s3_omitted_filename_reaches_sdk_default(
    fake_service: FakeMammothService, tmp_path: Path, file_type: str
) -> None:
    view_cmd.view_export_specialized(
        _inv(
            "view.export.managed-s3",
            project=180,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, {"file_type": file_type}),
            yes=True,
        )
    )
    assert fake_service.view_call_log == [(7, "to_s3", {"dataset_id": 9, "file_type": file_type})]


def test_postgres_route_requires_confirmation_and_forwards_secret(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    payload = {
        "host": "db.example",
        "port": 5432,
        "database": "analytics",
        "table": "sales",
        "username": "agent",
        "password": "secret",
    }
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.postgres",
                project=180,
                extra_args=["7"],
                input_file=_doc(tmp_path, payload),
            )
        )
    assert error.value.code == "confirmation_required"
    assert fake_service.view_call_log == []

    view_cmd.view_export_specialized(
        _inv(
            "view.export.postgres",
            project=180,
            extra_args=["7", "9"],
            input_file=_doc(tmp_path, payload),
            yes=True,
        )
    )
    assert fake_service.view_call_log == [(7, "to_postgres", {"dataset_id": 9, **payload})]


def test_specialized_route_rejects_unknown_fields_before_service(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.email",
                project=180,
                extra_args=["7"],
                input_file=_doc(tmp_path, {"emails": ["a@example.com"], "recipients": []}),
                yes=True,
            )
        )
    assert error.value.code == "unknown_input_field"
    assert fake_service.view_call_log == []


def test_destination_specific_field_cannot_leak_through_kwargs(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    payload = {
        "host": "db.example",
        "port": 5432,
        "database": "analytics",
        "table": "sales",
        "username": "agent",
        "password": "secret",
        "subject": "email-only option",
    }
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.postgres",
                project=180,
                extra_args=["7", "9"],
                input_file=_doc(tmp_path, payload),
                yes=True,
            )
        )
    assert error.value.code == "unknown_input_field"
    assert error.value.details["unknown"] == ["subject"]
    assert fake_service.view_call_log == []


def test_secret_destination_requires_required_secret_field(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.azure-blob",
                project=180,
                extra_args=["7"],
                input_file=_doc(
                    tmp_path,
                    {
                        "storage_account_name": "acct",
                        "tenant_id": "tenant",
                        "client_id": "client",
                        "container_name": "exports",
                    },
                ),
                yes=True,
            )
        )
    assert error.value.code == "missing_field"
    assert fake_service.view_call_log == []


# ---------------------------------------------------------------------------
# DEFECT 1 parity: runtime confirmation gate vs. manifest `confirmation`
# ---------------------------------------------------------------------------
#
# The in-app agent product decides whether to show a confirmation card from
# the MANIFEST's `confirmation` field alone -- it never runs the CLI to find
# out. A runtime gate the manifest does not declare (or a manifest promise
# the runtime does not honor) is therefore invisible to that product. This
# sweeps every typed `view.export.*` destination and asserts the two agree,
# so a future destination cannot silently drift the same way
# `view.export.dataset` did (manifest: confirmation=none; runtime: always
# demanded --yes).

# One plausible value per required field name used across `_SPECIAL_EXPORTS`,
# just enough to satisfy `_require_field` and reach the confirmation gate.
_FIELD_FAKES: dict[str, object] = {
    "dataset_name": "snapshot",
    "storage_account_name": "acct",
    "tenant_id": "tenant",
    "client_id": "client",
    "client_secret": "secret",
    "container_name": "exports",
    "selected_profile": {"name": "dataset", "value": [["proj", "dataset"]]},
    "selected_identity": {"identity_config": {}, "host": "sa@example.iam.gserviceaccount.com"},
    "table": "sales",
    "host": "db.example",
    "username": "agent",
    "password": "secret",
    "index": "logs",
    "emails": ["a@example.com"],
    "domain": "example.com",
    "directory": "/exports",
    "file": "out.csv",
    "port": 5432,
    "database": "analytics",
    "user_id": "user-1",
    "dataset": "reports",
    "base_url": "https://api.example.com",
    "endpoint_path": "/ingest",
    "site_url": "https://tenant.sharepoint.com/sites/team",
    "server_url": "https://tableau.example.com",
    "token_name": "token",
    "token_secret": "token-secret",
}


def _payload_for(required: tuple[str, ...]) -> dict[str, object]:
    return {name: _FIELD_FAKES[name] for name in required}


@pytest.mark.parametrize("command_id", sorted(view_cmd._SPECIAL_EXPORTS))
def test_export_route_confirmation_matches_manifest(
    command_id: str, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    record = command_by_id(command_id)
    assert record is not None, command_id
    _method, required, _secrets = view_cmd._SPECIAL_EXPORTS[command_id]
    payload = _payload_for(required)

    try:
        view_cmd.view_export_specialized(
            _inv(
                command_id,
                project=180,
                extra_args=["7", "9"],
                input_file=_doc(tmp_path, payload),
            )
        )
    except CliError as error:
        runtime_requires_confirmation = error.code == "confirmation_required"
    else:
        runtime_requires_confirmation = False

    manifest_requires_confirmation = record["confirmation"] != POLICY_NONE
    assert runtime_requires_confirmation == manifest_requires_confirmation, (
        f"{command_id}: manifest confirmation={record['confirmation']!r} but the runtime "
        f"{'did' if runtime_requires_confirmation else 'did not'} demand --yes without it"
    )


def test_csv_export_route_confirmation_matches_manifest(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """`view.export.csv` never calls `enforce_confirmation`; assert that
    matches its manifest entry (`confirmation: none`) rather than assuming it."""
    record = command_by_id("view.export.csv")
    assert record is not None
    assert record["confirmation"] == POLICY_NONE

    try:
        view_cmd.view_export_csv(
            _inv(
                "view.export.csv",
                extra_args=["7"],
                input_file=_doc(tmp_path, {"output_path": str(tmp_path / "out.csv")}),
            )
        )
    except CliError as error:
        assert error.code != "confirmation_required"


def test_common_trigger_field_rejected_when_route_has_no_kwargs_sink(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """PR25 item A follow-up (T2-F-006 c37): ``view.export.dataset`` (SDK
    ``ViewExport.to_dataset``) has a closed signature -- no ``**kwargs`` -- so
    it cannot actually accept any of the six common trigger controls. Passing
    one used to pass the unknown-field check (they were unioned in for every
    route) and then crash the SDK call itself with an opaque "unexpected
    keyword argument" TypeError, surfaced as invalid_arguments instead of a
    clear unknown_input_field naming the actual problem field.
    """
    with pytest.raises(CliError) as error:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.dataset",
                project=180,
                extra_args=["7", "9"],
                input_file=_doc(tmp_path, {"dataset_name": "snapshot", "end_of_pipeline": True}),
                yes=True,
            )
        )
    assert error.value.code == "unknown_input_field"
    assert error.value.details["unknown"] == ["end_of_pipeline"]
    assert fake_service.view_call_log == []


def test_every_special_export_field_the_cli_would_forward_is_accepted_by_its_sdk_method() -> None:
    """Guard against a repeat of the ``to_dataset``/``end_of_pipeline`` drift.

    For every typed export route, whatever the CLI's own field-allow-list
    computation would let through must be forwardable to that route's SDK
    method without raising a TypeError for an unexpected keyword: either the
    field is an explicit named parameter, or the method has a ``**kwargs``
    sink to carry it.
    """
    for command_id, (method, required, _secrets) in _SPECIAL_EXPORTS.items():
        signature = inspect.signature(getattr(ViewExport, method))
        explicit_fields = {
            name
            for name, parameter in signature.parameters.items()
            if name != "self" and parameter.kind is not inspect.Parameter.VAR_KEYWORD
        }
        accepts_var_keyword = any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )
        common_fields = _SPECIAL_EXPORT_COMMON_FIELDS if accepts_var_keyword else frozenset()
        allowed = explicit_fields | common_fields
        for field in required:
            assert field in explicit_fields, (
                f"{command_id}: required field {field!r} is not an explicit "
                f"parameter of {method!r}"
            )
        if not accepts_var_keyword:
            unforwardable = common_fields - explicit_fields
            assert not unforwardable, (
                f"{command_id}: {method!r} has no **kwargs sink, so the common "
                f"trigger fields {sorted(unforwardable)} would crash the call"
            )
        assert allowed  # every route accepts at least its own explicit fields


def test_dataset_route_refuses_a_view_in_draft_mode_instead_of_waiting_on_it(
    fake_service: FakeMammothService, tmp_path: Path
) -> None:
    """With auto-run off, a view holds new pipeline changes in a draft, so an
    export added there never runs and the SDK waited out its whole timeout
    (~6 min) before a generic error; the agent then gave up (eval T1-O-11)."""
    fake_service.responses[_PIPELINE_GET] = {"draft_mode": "clean", "auto_run": False}

    with pytest.raises(CliError) as caught:
        view_cmd.view_export_specialized(
            _inv(
                "view.export.dataset",
                project=180,
                extra_args=["7", "9"],
                input_file=_doc(tmp_path, {"dataset_name": "orders_copy"}),
                yes=True,
            )
        )

    assert caught.value.code == "view_in_draft"
    assert "mammoth view draft auto-run 7" in (caught.value.hint or "")
    assert fake_service.view_call_log == []
