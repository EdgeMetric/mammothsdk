"""Rich View domain object for working with Mammoth dataviews.

The View object is the central interface for data transformations in the
Mammoth SDK. It wraps a single dataview and exposes 25+ transformation
methods, data access, pipeline management, and export helpers.

Get a View via ``client.views.get(view_id)``::

    from mammoth import MammothClient, Condition, Operator, ColumnType, SetValue

    client = MammothClient(api_key="...", api_secret="...", workspace_id=11)
    client.set_project_id(10)

    view = client.views.get(1039)
    print(view.display_names)     # ["Sales", "Region", ...]
    print(view.columns)           # {"Sales": "column_1", ...}

Transformations are applied in-place and refresh the view metadata::

    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.set_values(
        new_column="Risk",
        column_type=ColumnType.TEXT,
        values=[
            SetValue("High", condition=Condition("Sales", Operator.GTE, 10000)),
            SetValue("Low"),
        ],
    )
    view.math("Price * Quantity", new_column="Total")

Exports are accessed via ``view.export``::

    view.export.to_csv("output.csv")
    view.export.to_postgres(host="db.example.com", port=5432, ...)
    view.branch_out(dataset_name="Sales snapshot")
"""

from __future__ import annotations

import datetime
import random
import string
import time
from pathlib import Path
from typing import Any

from mammoth._mixins import (
    AdvancedOpsMixin,
    AggregateOpsMixin,
    ColumnOpsMixin,
    DateOpsMixin,
    FilterOpsMixin,
    MathOpsMixin,
    RowOpsMixin,
    TextOpsMixin,
)
from mammoth._pure.builders import build_branch_out_params
from mammoth.condition import CompoundCondition, Condition, NotCondition
from mammoth.exceptions import MammothColumnError, MammothExportError, MammothValidationError
from mammoth.models.exports import (
    AddExportSpec,
    BigQueryExportType,
    ExportResult,
    ExportStatus,
    ExportTargetKey,
    HandlerType,
    HttpMethod,
    OdbcType,
    RestAuthType,
    TriggerType,
)
from mammoth.models.jobs import JobResponse
from mammoth.models.pipeline import (
    DraftCommand,
    ExportFileType,
    SaveAsDatasetMode,
)

_list = list  # Alias to avoid shadowing by method name
_K = ExportTargetKey  # short alias for the export target_properties wire keys

# Raised when a new internal-dataset export never exposes its dataset id in time.
ERR_EXPORT_DATASET_UNRESOLVED = (
    "Export for dataset {name!r} completed but its dataset id did not resolve "
    "before the timeout; the materialisation may still be in progress."
)

# Export-method argument validation (raised before any API call).
ERR_EMAIL_NO_RECIPIENTS = "to_email requires at least one recipient in `emails`."
ERR_SFTP_KEY_REQUIRED = (
    "to_sftp with ssh_key_authentication=True requires a non-empty `private_key`."
)
ERR_BIGQUERY_UPSERT_KEYS = (
    "to_bigquery with export_type=UPSERT requires at least one entry in `upsert_keys`."
)
ERR_REST_BATCH_SIZE = "to_rest_api `batch_size` must be between 1 and 10000 (got {value})."
ERR_REST_TIMEOUT = "to_rest_api `timeout_seconds` must be between 5 and 300 (got {value})."

# Inclusive bounds the REST-API handler accepts.
_REST_BATCH_SIZE_MIN = 1
_REST_BATCH_SIZE_MAX = 10000
_REST_TIMEOUT_MIN = 5
_REST_TIMEOUT_MAX = 300


class _DraftContext:
    """Context manager for View.draft().

    Enters draft mode on entry, submits on clean exit, discards on exception.
    """

    def __init__(self, view: View) -> None:
        self._view = view

    def __enter__(self) -> View:
        self._view.enter_draft_mode()
        return self._view

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if exc_type is not None:
            self._view.discard_draft()
        else:
            self._view.submit_draft()


class View(
    ColumnOpsMixin,
    FilterOpsMixin,
    MathOpsMixin,
    TextOpsMixin,
    DateOpsMixin,
    AggregateOpsMixin,
    RowOpsMixin,
    AdvancedOpsMixin,
):
    """Rich domain object for a Mammoth dataview.

    Provides access to dataview metadata, data retrieval, pipeline task
    management, and 25+ transformation methods. Created via
    ``client.views.get()`` — not instantiated directly.

    Attributes:
        id: Dataview ID (int).
        dataset_id: Parent dataset ID (int).
        name: Dataview display name.
        columns: Dict mapping display names to internal names.
        display_names: Ordered list of column display names.
        column_types: Dict mapping display names to types.
        raw: Full raw API response dict.
        export: ViewExport helper for export operations.

    Transformation methods (SET, FILTER, MATH, JOIN, PIVOT, WINDOW, etc.)
    send the task to the pipeline API and automatically refresh metadata.
    Each method returns the API response dict.
    """

    def __init__(self, client: Any, dataview_data: dict[str, Any], dataset_id: int) -> None:
        self._client = client
        self.raw = dataview_data
        self.id: int = dataview_data.get("id", 0)
        self.dataset_id = dataset_id
        self.name: str = dataview_data.get("name", "")

        # Column mappings
        self.columns: dict[str, str] = {}
        self.display_names: list[str] = []
        self.column_types: dict[str, str] = {}
        self._internal_names: list[str] = []

        self._build_column_maps(dataview_data)

        # Draft mode tracking
        self._draft_mode: bool = False

        # Attach export helper
        self.export = ViewExport(self)

    def _build_column_maps(self, data: dict[str, Any]) -> None:
        """Extract column name mappings from dataview metadata.

        Reads column metadata from the last task in ``taskwise_info``, which
        always reflects the final post-pipeline column list including any columns
        added by transforms (math, set_values, add_column, etc.).  Falls back to
        the top-level ``metadata`` field for views that have no pipeline tasks yet.
        """
        self.columns = {}
        self.display_names = []
        self.column_types = {}
        self._internal_names = []

        # taskwise_info keys are task sequence numbers (str in JSON).
        # The entry with the highest sequence holds the final column list.
        columns_list: list[dict[str, Any]] = []
        taskwise_info = data.get("taskwise_info") or {}
        if taskwise_info:
            try:
                last_seq = max(int(k) for k in taskwise_info)
                task_info = taskwise_info.get(last_seq) or taskwise_info.get(str(last_seq)) or {}
                columns_list = task_info.get("metadata") or []
            except ValueError, TypeError:
                pass

        # Fresh view with no tasks yet — taskwise_info is null, fall back to
        # the top-level metadata field which has the original dataset columns.
        if not columns_list:
            columns_list = data.get("metadata") or []
        if not columns_list:
            properties = data.get("properties", {})
            columns_list = properties.get("columns", []) if isinstance(properties, dict) else []

        for col in columns_list:
            display = col.get("display_name") or col.get("name", "")
            internal = col.get("internal_name") or col.get("name", "")
            col_type = col.get("type", "TEXT")

            if display:
                self.columns[display] = internal
                self.display_names.append(display)
                self.column_types[display] = col_type
                self._internal_names.append(internal)

    def _resolve_column(self, display_name: str) -> str:
        """Resolve a display name to internal column name.

        Args:
            display_name: Column display name (e.g. "Sales").

        Returns:
            Internal column name (e.g. "column_1").

        Raises:
            MammothColumnError: If column not found.
        """
        if display_name in self.columns:
            return self.columns[display_name]
        if display_name in self._internal_names:
            return display_name
        raise MammothColumnError(display_name, self.display_names)

    def _resolve_columns(self, names: list[str]) -> list[str]:
        """Resolve multiple display names to internal names."""
        return [self._resolve_column(n) for n in names]

    def _next_internal_name(self) -> str:
        """Generate a unique internal column name."""
        chars = string.ascii_lowercase + string.digits
        return f"column_{''.join(random.choices(chars, k=10))}"

    def _build_as_column(
        self,
        name: str,
        column_type: str = "TEXT",
        internal_name: str | None = None,
    ) -> dict[str, str]:
        """Build an AS (new column) spec."""
        return {
            "COLUMN": name,
            "TYPE": column_type.upper(),
            "INTERNAL_NAME": internal_name or self._next_internal_name(),
        }

    def _build_condition(
        self, condition: Condition | CompoundCondition | NotCondition | dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Build condition dict from Condition object or raw dict."""
        if condition is None:
            return None
        if isinstance(condition, dict):
            return condition
        return condition.build(self.columns, self.column_types)

    def _add_task(self, task_spec: dict[str, Any]) -> dict[str, Any]:
        """Add a task to the pipeline, wait for completion, and refresh metadata.

        In draft mode, skips waiting and metadata refresh — tasks are queued
        and executed when ``submit_draft()`` is called.

        Args:
            task_spec: Task specification dict.

        Returns:
            API response dict.
        """
        result = self._client.pipeline.add_task(self.id, task_spec, self.dataset_id)
        if not self._draft_mode:
            self._client.pipeline.wait_for_pipeline(self.id, self.dataset_id)
            self.refresh()
        return result

    def _run_internal_dataset_export(
        self,
        target_properties: dict[str, Any],
        timeout: int | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> int:
        """Submit an internal-dataset export (crosstab / branch-out) and return the id.

        Both crosstab and branch-out materialise a dataset through the same
        ``internal_dataset`` export handler. *condition* is a typed condition
        object (the wire dict is built here, so callers never deal with the raw
        payload).

        The submit job returns with an empty ``response`` *before* the dataset
        is created (the materialisation is a fire-and-forget downstream action),
        so the new id is resolved from the export trigger once it reaches
        ``EXECUTED``. When writing into a known existing dataset
        (``TARGET_DS_ID`` set) that id is returned directly.

        Returns:
            The id of the dataset the export wrote to (new or existing).

        Raises:
            MammothExportError: If a new dataset's id does not resolve within
                the timeout.
        """
        spec = AddExportSpec(
            DATAVIEW_ID=self.id,
            handler_type=HandlerType.INTERNAL_DATASET,
            trigger_type=TriggerType.PIPELINE,
            target_properties=target_properties,
            additional_properties={},
            condition=self._build_condition(condition) or {},
            run_immediately=True,
            validate_only=False,
            end_of_pipeline=True,
        )
        result = self._client.exports.create(self.id, spec, self.dataset_id)
        if isinstance(result, JobResponse):
            self._client.jobs.wait_for_job(result.job.id, timeout)

        existing_id = target_properties.get("TARGET_DS_ID")
        if existing_id is not None:
            return int(existing_id)
        return self._resolve_exported_dataset_id(target_properties["DS_NAME"], timeout)

    def _resolve_exported_dataset_id(self, dataset_name: str, timeout: int | None = None) -> int:
        """Resolve the id of the dataset a new internal-dataset export created.

        Polls this dataview's ``internal_dataset`` export triggers for the one
        named *dataset_name* (the most recent, by id) until it reaches
        ``EXECUTED`` and exposes ``TARGET_DS_ID``.
        """
        deadline = time.monotonic() + (timeout or getattr(self._client, "job_timeout", 60) or 60)
        poll_interval = 2.0
        while time.monotonic() < deadline:
            page = self._client.exports.list(self.id, handler_type=HandlerType.INTERNAL_DATASET)
            matches = [
                e
                for e in page.exports
                if (e.target_properties or {}).get("DS_NAME") == dataset_name
            ]
            if matches:
                export = max(matches, key=lambda e: e.id or 0)
                target_id = (export.target_properties or {}).get("TARGET_DS_ID")
                if export.status == ExportStatus.EXECUTED and target_id is not None:
                    return int(target_id)
            time.sleep(poll_interval)
        raise MammothExportError(
            ERR_EXPORT_DATASET_UNRESOLVED.format(name=dataset_name),
            {"dataset_name": dataset_name, "timeout": timeout},
        )

    # ── Data Access ─────────────────────────────────────────────

    def data(
        self,
        limit: int = 400,
        offset: int = 1,
        columns: list[str] | None = None,
        condition: Condition | CompoundCondition | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Fetch data rows from the dataview.

        Args:
            limit: Maximum number of rows to return (default 400).
            offset: One-indexed starting row (default 1).
            columns: List of display names to fetch. ``None`` fetches all.
            condition: Filter condition — only matching rows are returned.
            sort: Sort specification string.

        Returns:
            Dict with ``data`` (list of row dicts), ``columns``, and
            pagination info (``total``, ``limit``, ``offset``).

        Examples::

            rows = view.data(limit=10)
            rows = view.data(columns=["Name", "Sales"], limit=50)
            rows = view.data(
                condition=Condition("Sales", Operator.GTE, 1000),
                limit=100,
            )
        """
        resolved_cols = self._resolve_columns(columns) if columns else None
        built_condition = self._build_condition(condition)

        return self._client.dataviews.query_data(
            dataset_id=self.dataset_id,
            dataview_id=self.id,
            limit=limit,
            offset=offset,
            columns=resolved_cols,
            condition=built_condition,
            sort=sort,
        )

    def refresh(self) -> View:
        """Re-fetch metadata from the API and update local state.

        Updates ``columns``, ``display_names``, ``column_types``, and ``raw``
        to reflect any changes (e.g. columns added by pipeline tasks).

        .. note::

            Pipeline-derived columns (from add_column, math, etc.) are
            included only when the server response contains ``taskwise_info``.
            If a column is missing after refresh, call ``view.data(limit=1)``
            to verify the column exists in the output, or re-get the view
            with ``client.views.get(view.id)``.

        Returns:
            self (for chaining).

        Example::

            view.refresh()
            print(view.display_names)  # updated column list
        """
        proj = getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        data = self._client.dataviews.get(
            dataset_id=self.dataset_id,
            dataview_id=self.id,
        )
        self.raw = data
        self.name = data.get("name", "")
        self._build_column_maps(data)
        return self

    def get_metadata(self) -> list[dict[str, Any]]:
        """Return current column metadata as a list of dicts.

        Each dict has keys ``display_name``, ``internal_name``, and ``type``.
        Reflects all columns including those added by pipeline transformations.

        Returns:
            List of column metadata dicts.

        Example::

            meta = view.get_metadata()
            for col in meta:
                print(f"{col['display_name']} ({col['type']})")
        """
        return [
            {
                "display_name": name,
                "internal_name": self.columns[name],
                "type": self.column_types[name],
            }
            for name in self.display_names
        ]

    # ── Pipeline Management ─────────────────────────────────────

    def list_tasks(self) -> list[dict[str, Any]]:
        """List all pipeline tasks on this dataview.

        Returns:
            List of task dicts, each with ``id``, ``sequence``,
            ``task_key``, ``params``, etc.

        Example::

            tasks = view.list_tasks()
            for t in tasks:
                print(f"#{t['sequence']} {t['task_key']}")
        """
        result = self._client.pipeline.list_tasks(self.id, self.dataset_id)
        return result.get("tasks", result if isinstance(result, list) else [])

    def delete_task(self, task_id: int) -> dict[str, Any]:
        """Delete a pipeline task and re-run the pipeline.

        Removes the task, waits for the pipeline to settle, then refreshes
        column metadata.

        Args:
            task_id: ID of the task to remove (from ``list_tasks()``).

        Returns:
            Deletion confirmation dict.

        Example::

            tasks = view.list_tasks()
            view.delete_task(tasks[-1]["id"])  # remove last task
        """
        result = self._client.pipeline.delete_task(self.id, task_id, self.dataset_id)
        self._client.pipeline.wait_for_pipeline(self.id, self.dataset_id)
        self.refresh()
        return result

    def preview_task(self, task_spec: dict[str, Any]) -> dict[str, Any]:
        """Preview the result of a task without applying it to the pipeline.

        Args:
            task_spec: Task specification dict (same format as ``_add_task``
                payloads).

        Returns:
            Preview data dict showing what the data would look like.

        Example::

            preview = view.preview_task({"DELETE": ["column_abc123"]})
        """
        return self._client.pipeline.preview_task(self.id, task_spec, self.dataset_id)

    # ── Draft Mode ───────────────────────────────────────────────

    @property
    def is_draft_mode(self) -> bool:
        """Whether this view is currently in draft mode."""
        return self._draft_mode

    def enter_draft_mode(self) -> dict[str, Any]:
        """Enter draft mode — tasks are queued without pipeline execution.

        If already in draft mode, returns immediately without making an API call.

        Returns:
            Draft mode state dict from the API, or a status dict if already in
            draft mode.
        """
        if self._draft_mode:
            return {"status": "already_in_draft_mode"}

        result = self._client.pipeline.draft_mode(self.id, DraftCommand.ENTER, self.dataset_id)
        self._draft_mode = True
        return result

    def submit_draft(self) -> dict[str, Any]:
        """Submit queued draft tasks, run the pipeline, and exit draft mode.

        Executes all queued tasks, refreshes column metadata, then
        exits draft mode.

        Returns:
            Pipeline state dict after execution.
        """
        self._client.pipeline.draft_mode(self.id, DraftCommand.SUBMIT, self.dataset_id)
        pipeline = self._client.pipeline.wait_for_pipeline(self.id, self.dataset_id)
        self.refresh()
        self._client.pipeline.draft_mode(self.id, DraftCommand.EXIT, self.dataset_id)
        self._draft_mode = False
        return pipeline

    def discard_draft(self) -> dict[str, Any]:
        """Discard queued draft tasks and exit draft mode.

        Reverts all tasks added since ``enter_draft_mode()``, refreshes
        metadata to the pre-draft state.

        Returns:
            Draft mode state dict from the discard call.
        """
        result = self._client.pipeline.draft_mode(self.id, DraftCommand.DISCARD, self.dataset_id)
        self._client.pipeline.draft_mode(self.id, DraftCommand.EXIT, self.dataset_id)
        self.refresh()
        self._draft_mode = False
        return result

    def set_auto_run(self, enabled: bool) -> dict[str, Any]:
        """Toggle auto-run on the pipeline.

        When auto-run is enabled (default), each transformation triggers
        immediate pipeline execution. When disabled, the view enters draft
        mode and tasks are queued.

        Args:
            enabled: ``True`` to enable auto-run, ``False`` to disable.

        Returns:
            Updated pipeline state dict.
        """
        result = self._client.pipeline.edit_pipeline(
            self.id,
            [{"op": "command", "path": "auto_run", "value": enabled}],
            self.dataset_id,
        )
        self._draft_mode = not enabled
        return result

    def draft(self) -> _DraftContext:
        """Context manager for draft mode.

        Enters draft mode on ``__enter__``, submits on clean exit,
        discards on exception::

            with view.draft():
                view.filter_rows(Condition("Sales", Operator.GTE, 1000))
                view.math("Price * 2", new_column="Double")
            # Pipeline runs once for both tasks
        """
        return _DraftContext(self)

    def get_column_mapping(self) -> dict[str, str]:
        """Return a copy of the display-name-to-internal-name mapping.

        Returns:
            Dict mapping display names to internal names (e.g.
            ``{"Sales": "column_abc123", ...}``).

        Example::

            mapping = view.get_column_mapping()
            print(mapping)  # {"Sales": "column_abc123", "Region": "column_xyz"}
        """
        return dict(self.columns)

    def branch_out(
        self,
        dataset_name: str,
        *,
        target_ds_id: int | None = None,
        save_as_mode: SaveAsDatasetMode = SaveAsDatasetMode.REPLACE,
        column_mapping: dict[str, str] | None = None,
        label_ids: list[int] | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
        timeout: int | None = None,
    ) -> int:
        """Branch out — save this view's data as a Mammoth dataset.

        Shortcut for :meth:`ViewExport.to_dataset`. ``target_ds_id`` None
        creates a new dataset named *dataset_name*; an int replaces/appends
        into that existing dataset (per *save_as_mode*).

        Args:
            dataset_name: Name for the new dataset (display name when writing
                into an existing one).
            target_ds_id: Existing dataset to write into; None creates a new one.
            save_as_mode: Replace or append when writing the output dataset.
            column_mapping: Source -> destination column-name map (empty = all).
            label_ids: Folder/label ids for the new dataset.
            condition: Optional row filter applied before copying.
            timeout: Max seconds to wait for the job.

        Returns:
            The id of the dataset written to (new when ``target_ds_id`` is None,
            otherwise ``target_ds_id``).

        Example::

            new_id = view.branch_out(dataset_name="Q1 snapshot")
        """
        return self.export.to_dataset(
            dataset_name,
            target_ds_id=target_ds_id,
            save_as_mode=save_as_mode,
            column_mapping=column_mapping,
            label_ids=label_ids,
            condition=condition,
            timeout=timeout,
        )

    def __repr__(self) -> str:
        return f"View(id={self.id}, name={self.name!r}, " f"columns={len(self.display_names)})"


class ViewExport:
    """Export operations for a View. Access via view.export.

    Examples::

        view.export.to_csv("output.csv")
        view.export.to_postgres(host="...", database="...", table="...")
        view.export.list()
    """

    def __init__(self, view: View) -> None:
        self._view = view
        self._client = view._client

    def _create_export(
        self, handler_type: HandlerType, target_properties: dict[str, Any], **kwargs: Any
    ) -> ExportResult:
        """Internal helper to create an export."""
        spec = AddExportSpec(
            DATAVIEW_ID=self._view.id,
            handler_type=handler_type,
            trigger_type=kwargs.get("trigger_type", TriggerType.PIPELINE),
            target_properties=target_properties,
            additional_properties=kwargs.get("additional_properties", {}),
            condition=kwargs.get("condition", {}),
            run_immediately=kwargs.get("run_immediately", True),
            validate_only=kwargs.get("validate_only", False),
            end_of_pipeline=kwargs.get("end_of_pipeline", True),
        )
        return self._client.exports.create(
            dataview_id=self._view.id,
            export_spec=spec,
            dataset_id=self._view.dataset_id,
        )

    def to_postgres(
        self,
        host: str,
        port: int,
        database: str,
        table: str,
        username: str,
        password: str,
        **kwargs: Any,
    ) -> ExportResult:
        """Export to a PostgreSQL database.

        Requires a pre-configured PostgreSQL instance accessible from
        the Mammoth platform.

        Args:
            host: Database host.
            port: Database port.
            database: Database name.
            table: Target table name.
            username: Database username.
            password: Database password.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, etc.).

        Returns:
            Export result dict.

        Example::

            view.export.to_postgres(
                host="db.example.com", port=5432,
                database="analytics", table="sales_export",
                username="user", password="pass",
            )
        """
        return self._create_export(
            HandlerType.POSTGRES,
            {
                _K.HOST: host,
                _K.PORT: port,
                _K.DATABASE: database,
                _K.TABLE: table,
                _K.USERNAME: username,
                _K.PASSWORD: password,
            },
            **kwargs,
        )

    def to_mysql(
        self,
        host: str,
        port: int,
        database: str,
        table: str,
        username: str,
        password: str,
        **kwargs: Any,
    ) -> ExportResult:
        """Export to MySQL database.

        Args:
            host: Database host.
            port: Database port.
            database: Database name.
            table: Target table name.
            username: Database username.
            password: Database password.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            Export result dict.
        """
        return self._create_export(
            HandlerType.MYSQL,
            {
                _K.HOST: host,
                _K.PORT: port,
                _K.DATABASE: database,
                _K.TABLE: table,
                _K.USERNAME: username,
                _K.PASSWORD: password,
            },
            **kwargs,
        )

    def to_s3(
        self,
        file_name: str | None = None,
        file_type: ExportFileType = ExportFileType.CSV,
        include_hidden: bool = False,
        **kwargs: Any,
    ) -> ExportResult:
        """Export to S3 (Mammoth-managed bucket).

        Args:
            file_name: Output filename. Auto-generated with timestamp if
                not provided.
            file_type: File format (default ``ExportFileType.CSV``).
                Supported formats: CSV, JSON, PARQUET.
            include_hidden: Include hidden columns (default False).
            **kwargs: Additional export options.

        Returns:
            Export result dict with download URL.

        Example::

            result = view.export.to_s3(file_name="report.csv")
            view.export.to_s3(file_type=ExportFileType.PARQUET)
        """
        if file_name is None:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"view_{self._view.id}_export_{ts}.{file_type}"

        return self._create_export(
            HandlerType.S3,
            {
                _K.FILE: file_name,
                _K.FILE_TYPE: file_type.value,
                _K.INCLUDE_HIDDEN: include_hidden,
                _K.IS_FORMAT_SET: True,
                _K.USE_FORMAT: True,
            },
            **kwargs,
        )

    def to_dataset(
        self,
        dataset_name: str,
        *,
        target_ds_id: int | None = None,
        save_as_mode: SaveAsDatasetMode = SaveAsDatasetMode.REPLACE,
        column_mapping: dict[str, str] | None = None,
        label_ids: list[int] | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
        timeout: int | None = None,
    ) -> int:
        """Save this view's data as an internal Mammoth dataset (branch out).

        Runs through the ``internal_dataset`` export handler and blocks until
        the dataset is materialised.

        Args:
            dataset_name: Name for the new dataset (display name when writing
                into an existing one).
            target_ds_id: Existing dataset to write into; None creates a new one.
            save_as_mode: Replace or append when writing the output dataset.
            column_mapping: Source -> destination column-name map (empty = all).
            label_ids: Folder/label ids for the new dataset.
            condition: Optional row filter applied before copying.
            timeout: Max seconds to wait for the job.

        Returns:
            The id of the dataset written to (new when ``target_ds_id`` is None,
            otherwise ``target_ds_id``).

        Example::

            new_id = view.export.to_dataset("Sales snapshot")
        """
        target_properties = build_branch_out_params(
            dataset_name,
            target_ds_id=target_ds_id,
            save_as_mode=save_as_mode,
            column_mapping=column_mapping,
            label_ids=label_ids,
        )
        return self._view._run_internal_dataset_export(target_properties, timeout, condition)

    def to_csv(self, output_path: str | None = None, timeout: int = 300) -> Path:
        """Download dataview data as a local CSV file.

        Args:
            output_path: Local path for the output file. Auto-generated
                if not provided.
            timeout: Timeout in seconds (default 300).

        Returns:
            :class:`~pathlib.Path` to the downloaded CSV file.

        Example::

            path = view.export.to_csv("output.csv")
            print(f"Downloaded to {path}")
        """
        return self._client.exports.to_csv(
            dataview_id=self._view.id,
            output_path=output_path,
            timeout=timeout,
            dataset_id=self._view.dataset_id,
        )

    def to_ftp(
        self,
        domain: str,
        directory: str,
        file: str,
        username: str,
        password: str,
        port: int = 21,
        **kwargs: Any,
    ) -> ExportResult:
        """Export to an FTP server.

        Args:
            domain: FTP server hostname.
            directory: Remote directory to write into.
            file: Remote filename to write.
            username: FTP username.
            password: FTP password.
            port: FTP port (default 21).
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.

        Example::

            view.export.to_ftp(
                domain="ftp.example.com", directory="/exports",
                file="sales.csv", username="user", password="pass",
            )
        """
        return self._create_export(
            HandlerType.FTP,
            {
                _K.DOMAIN: domain,
                _K.PORT: port,
                _K.DIRECTORY: directory,
                _K.FILE: file,
                _K.USERNAME: username,
                _K.PASSWORD: password,
            },
            **kwargs,
        )

    def to_sftp(
        self,
        host: str,
        username: str,
        password: str = "",
        directory: str = "",
        file_name: str = "",
        port: int = 22,
        randomize_file_name: bool = False,
        ssh_key_authentication: bool = False,
        private_key: str = "",
        passphrase: str = "",
        **kwargs: Any,
    ) -> ExportResult:
        """Export to an SFTP server.

        Supports both password and private-key authentication. For key auth,
        set *ssh_key_authentication* and provide *private_key* (PEM string)
        plus an optional *passphrase*.

        Args:
            host: SFTP server hostname.
            username: SFTP username.
            password: SFTP password (omit when using key auth).
            directory: Remote directory; defaults server-side to the user home.
            file_name: Output filename; defaults server-side to
                ``{dataset}_{view}.csv``.
            port: SFTP port (default 22).
            randomize_file_name: Append a random suffix to the filename.
            ssh_key_authentication: Authenticate with a private key.
            private_key: PEM-format private key string (key auth).
            passphrase: Passphrase protecting *private_key*, if any.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.

        Raises:
            MammothValidationError: If key authentication is requested without a
                ``private_key``.
        """
        if ssh_key_authentication and not private_key:
            raise MammothValidationError(ERR_SFTP_KEY_REQUIRED)
        target: dict[str, Any] = {
            _K.HOST: host,
            _K.PORT: port,
            _K.USERNAME: username,
            _K.DIRECTORY: directory,
            _K.FILE_NAME: file_name,
            _K.RANDOMIZE_FILE_NAME: randomize_file_name,
            _K.SSH_KEY_AUTHENTICATION: ssh_key_authentication,
        }
        if ssh_key_authentication:
            target[_K.PRIVATE_KEY] = private_key
            target[_K.PASSPHRASE] = passphrase
        else:
            target[_K.PASSWORD] = password
        return self._create_export(HandlerType.SFTP, target, **kwargs)

    def to_email(
        self,
        emails: list[str],
        subject: str = "",
        message: str = "",
        resource: str = "",
        **kwargs: Any,
    ) -> ExportResult:
        """Export by emailing a download link to recipients.

        Args:
            emails: Recipient email addresses.
            subject: Email subject (defaults server-side).
            message: Body message appended to the email.
            resource: Display name of the exported resource in the email.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.

        Example::

            view.export.to_email(emails=["analyst@example.com"], subject="Q1")

        Raises:
            MammothValidationError: If *emails* is empty.
        """
        if not emails:
            raise MammothValidationError(ERR_EMAIL_NO_RECIPIENTS)
        target: dict[str, Any] = {_K.EMAILS: emails}
        if subject:
            target[_K.SUBJECT] = subject
        if message:
            target[_K.MESSAGE] = message
        if resource:
            target[_K.RESOURCE] = resource
        return self._create_export(HandlerType.EMAIL, target, **kwargs)

    def to_mssql(
        self,
        host: str,
        port: int,
        database: str,
        table: str,
        username: str,
        password: str,
        **kwargs: Any,
    ) -> ExportResult:
        """Export to a Microsoft SQL Server database.

        Args:
            host: Database host.
            port: Database port (SQL Server default is 1433).
            database: Database name.
            table: Target table name.
            username: Database username.
            password: Database password.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.
        """
        return self._create_export(
            HandlerType.MSSQL,
            {
                _K.HOST: host,
                _K.PORT: port,
                _K.DATABASE: database,
                _K.TABLE: table,
                _K.USERNAME: username,
                _K.PASSWORD: password,
            },
            **kwargs,
        )

    def to_redshift(
        self,
        host: str,
        port: int,
        database: str,
        table: str,
        username: str,
        password: str,
        **kwargs: Any,
    ) -> ExportResult:
        """Export to an Amazon Redshift cluster.

        Data is staged through a Mammoth-managed S3 bucket and then
        ``COPY``-ed into the target table.

        Args:
            host: Cluster endpoint host.
            port: Cluster port (Redshift default is 5439).
            database: Database name.
            table: Target table name.
            username: Database username.
            password: Database password.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.
        """
        return self._create_export(
            HandlerType.REDSHIFT,
            {
                _K.HOST: host,
                _K.PORT: port,
                _K.DATABASE: database,
                _K.TABLE: table,
                _K.USERNAME: username,
                _K.PASSWORD: password,
            },
            **kwargs,
        )

    def to_bigquery(
        self,
        selected_profile: dict[str, Any],
        selected_identity: dict[str, Any],
        table: str,
        export_type: BigQueryExportType = BigQueryExportType.REPLACE,
        upsert_keys: list[dict[str, Any]] | None = None,
        partition: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ExportResult:
        """Export to Google BigQuery.

        Uses an existing Mammoth BigQuery integration; *selected_profile*
        and *selected_identity* are obtained from that integration rather
        than passed as raw credentials here.

        Args:
            selected_profile: Project/dataset selection, shaped as
                ``{"name": "<dataset>", "value": [[project_id, dataset_id]]}``.
            selected_identity: Service-account identity config, shaped as
                ``{"identity_config": {...}, "host": "<sa-email>"}``.
            table: Destination table name.
            export_type: Write mode (REPLACE, COMBINE, or UPSERT).
            upsert_keys: Required when *export_type* is UPSERT — a list of
                ``{"column": {"display_name": "<col>"}}`` dicts.
            partition: Optional partitioning spec. For datetime partitioning,
                ``{"FIELD": str, "GRANULARITY": "DAY"|"MONTH"|"YEAR"}``; for
                integer-range partitioning, ``{"FIELD": str, "START": int,
                "END": int, "INTERVAL": int}``.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.

        Raises:
            MammothValidationError: If *export_type* is UPSERT but no
                *upsert_keys* are given.
        """
        if export_type is BigQueryExportType.UPSERT and not upsert_keys:
            raise MammothValidationError(ERR_BIGQUERY_UPSERT_KEYS)
        target: dict[str, Any] = {
            _K.SELECTED_PROFILE: selected_profile,
            _K.SELECTED_IDENTITY: selected_identity,
            _K.TABLE: table,
            _K.EXPORT_TYPE: export_type.value,
        }
        if upsert_keys is not None:
            target[_K.UPSERT_KEYS] = upsert_keys
        if partition is not None:
            target[_K.PARTITION] = partition
        return self._create_export(HandlerType.BIGQUERY, target, **kwargs)

    def to_elasticsearch(
        self,
        host: str,
        username: str,
        password: str,
        index: str,
        port: int = 9243,
        connection: str = "https",
        chunksize: int = 200,
        **kwargs: Any,
    ) -> ExportResult:
        """Export to an Elasticsearch index.

        Args:
            host: Elasticsearch host.
            username: Auth username.
            password: Auth password.
            index: Destination index name.
            port: Port (default 9243).
            connection: Protocol, ``"http"`` or ``"https"`` (default).
            chunksize: Bulk-insert batch size (default 200).
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.
        """
        return self._create_export(
            HandlerType.ELASTICSEARCH,
            {
                _K.HOST: host,
                _K.PORT: port,
                _K.USERNAME: username,
                _K.PASSWORD: password,
                _K.INDEX: index,
                _K.CONNECTION: connection,
                _K.CHUNKSIZE: chunksize,
            },
            **kwargs,
        )

    def to_azure_blob(
        self,
        storage_account_name: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        container_name: str,
        folder_path: str = "",
        file_name: str = "",
        **kwargs: Any,
    ) -> ExportResult:
        """Export to Azure Blob Storage.

        Args:
            storage_account_name: Azure storage account name.
            tenant_id: Azure AD tenant id.
            client_id: App registration client id.
            client_secret: App registration client secret.
            container_name: Target blob container.
            folder_path: Optional subfolder within the container.
            file_name: Optional output filename (no slashes).
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.
        """
        target: dict[str, Any] = {
            _K.STORAGE_ACCOUNT_NAME: storage_account_name,
            _K.TENANT_ID: tenant_id,
            _K.CLIENT_ID: client_id,
            _K.CLIENT_SECRET: client_secret,
            _K.CONTAINER_NAME: container_name,
        }
        if folder_path:
            target[_K.FOLDER_PATH] = folder_path
        if file_name:
            target[_K.FILE_NAME] = file_name
        return self._create_export(HandlerType.AZURE_BLOB, target, **kwargs)

    def to_sharepoint(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        site_url: str,
        document_library: str = "Documents",
        folder_path: str = "",
        file_name: str = "",
        **kwargs: Any,
    ) -> ExportResult:
        """Export to a SharePoint document library.

        Args:
            tenant_id: Azure AD tenant id.
            client_id: App registration client id.
            client_secret: App registration client secret.
            site_url: Full or partial SharePoint site URL.
            document_library: Target library (default ``"Documents"``).
            folder_path: Optional subfolder path within the library.
            file_name: Optional output filename.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.
        """
        target: dict[str, Any] = {
            _K.TENANT_ID: tenant_id,
            _K.CLIENT_ID: client_id,
            _K.CLIENT_SECRET: client_secret,
            _K.SITE_URL: site_url,
            _K.DOCUMENT_LIBRARY: document_library,
        }
        if folder_path:
            target[_K.FOLDER_PATH] = folder_path
        if file_name:
            target[_K.FILE_NAME] = file_name
        return self._create_export(HandlerType.SHAREPOINT, target, **kwargs)

    def to_onedrive(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        user_id: str,
        folder_path: str = "",
        file_name: str = "",
        **kwargs: Any,
    ) -> ExportResult:
        """Export to a user's OneDrive.

        Args:
            tenant_id: Azure AD tenant id.
            client_id: App registration client id.
            client_secret: App registration client secret.
            user_id: Azure AD user object id or UPN whose drive is targeted.
            folder_path: Optional subfolder path.
            file_name: Optional output filename.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.
        """
        target: dict[str, Any] = {
            _K.TENANT_ID: tenant_id,
            _K.CLIENT_ID: client_id,
            _K.CLIENT_SECRET: client_secret,
            _K.USER_ID: user_id,
        }
        if folder_path:
            target[_K.FOLDER_PATH] = folder_path
        if file_name:
            target[_K.FILE_NAME] = file_name
        return self._create_export(HandlerType.ONEDRIVE, target, **kwargs)

    def to_tableau(
        self,
        server_url: str,
        token_name: str,
        token_secret: str,
        site_name: str = "",
        project_name: str = "Default",
        datasource_name: str = "mammoth_export",
        ca_bundle_path: str = "",
        **kwargs: Any,
    ) -> ExportResult:
        """Publish this view as a Tableau Server datasource.

        Authenticates with a Tableau Personal Access Token (PAT).

        Args:
            server_url: Tableau Server base URL.
            token_name: PAT name.
            token_secret: PAT secret.
            site_name: Tableau site; empty string targets the default site.
            project_name: Destination project (default ``"Default"``).
            datasource_name: Published datasource name
                (default ``"mammoth_export"``).
            ca_bundle_path: Optional CA bundle path for self-signed TLS.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.
        """
        target: dict[str, Any] = {
            _K.SERVER_URL: server_url,
            _K.TOKEN_NAME: token_name,
            _K.TOKEN_SECRET: token_secret,
            _K.SITE_NAME: site_name,
            _K.PROJECT_NAME: project_name,
            _K.DATASOURCE_NAME: datasource_name,
        }
        if ca_bundle_path:
            target[_K.CA_BUNDLE_PATH] = ca_bundle_path
        return self._create_export(HandlerType.TABLEAU_SERVER, target, **kwargs)

    def to_powerbi(
        self,
        username: str,
        password: str,
        client_id: str,
        dataset: str,
        table: str,
        **kwargs: Any,
    ) -> ExportResult:
        """Push this view into a Power BI dataset table.

        Args:
            username: Power BI account username.
            password: Power BI account password.
            client_id: Azure AD application (client) id.
            dataset: Target Power BI dataset name.
            table: Target table within the dataset.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.
        """
        return self._create_export(
            HandlerType.POWERBI,
            {
                _K.USERNAME: username,
                _K.PASSWORD: password,
                # Backend reads the camelCase key (powerbi.py:82,140).
                _K.CLIENT_ID_CAMEL: client_id,
                _K.DATASET: dataset,
                _K.TABLE: table,
            },
            **kwargs,
        )

    def to_rest_api(
        self,
        base_url: str,
        endpoint_path: str,
        auth_type: RestAuthType = RestAuthType.NONE,
        http_method: HttpMethod = HttpMethod.POST,
        wrap_path: str = "records",
        batch_size: int = 1000,
        timeout_seconds: int = 30,
        ssl_verify: bool = True,
        auth: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        extra_body_fields: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ExportResult:
        """Export rows to a generic REST API endpoint.

        Rows are batched and POSTed (or PUT/PATCHed) to
        ``base_url + endpoint_path``.

        Args:
            base_url: API base URL (http/https).
            endpoint_path: Path appended to *base_url*, e.g. ``"/v1/records"``.
            auth_type: Authentication scheme (:class:`RestAuthType`); defaults to
                ``RestAuthType.NONE``.
            http_method: Request verb (:class:`HttpMethod`); defaults to
                ``HttpMethod.POST``.
            wrap_path: Dot-path under which records are nested in the body
                (default ``"records"``).
            batch_size: Records per request (default 1000, 1-10000).
            timeout_seconds: Per-request timeout, 5-300s (default 30).
            ssl_verify: Verify TLS certificates (default True).
            auth: Auth-type-specific secrets, merged flat into the request.
                ``api_key``: ``{"key_name", "key_value", "key_location"}``.
                ``bearer``: ``{"token"}``. ``basic``: ``{"username", "password"}``.
                ``oauth2_authorization_code``: ``{"token_url", "client_id",
                "client_secret", "refresh_token", ...}``.
            headers: Static headers sent on every request.
            query_params: URL query params appended to every request.
            extra_body_fields: Static fields merged alongside records in body.
            **kwargs: Additional export options (``trigger_type``,
                ``run_immediately``, ``validate_only``,
                ``end_of_pipeline``, ``additional_properties``,
                ``condition``).

        Returns:
            The created export trigger record or its tracking job.

        Raises:
            MammothValidationError: If *batch_size* or *timeout_seconds* is
                outside the accepted range.
        """
        if not _REST_BATCH_SIZE_MIN <= batch_size <= _REST_BATCH_SIZE_MAX:
            raise MammothValidationError(ERR_REST_BATCH_SIZE.format(value=batch_size))
        if not _REST_TIMEOUT_MIN <= timeout_seconds <= _REST_TIMEOUT_MAX:
            raise MammothValidationError(ERR_REST_TIMEOUT.format(value=timeout_seconds))
        target: dict[str, Any] = {
            _K.BASE_URL: base_url,
            _K.ENDPOINT_PATH: endpoint_path,
            _K.AUTH_TYPE: auth_type.value,
            _K.HTTP_METHOD: http_method.value,
            _K.WRAP_PATH: wrap_path,
            _K.BATCH_SIZE: batch_size,
            _K.TIMEOUT_SECONDS: timeout_seconds,
            _K.SSL_VERIFY: ssl_verify,
        }
        if auth:
            target.update(auth)
        if headers is not None:
            target[_K.DEFAULT_HEADERS] = headers
        if query_params is not None:
            target[_K.QUERY_PARAMS] = query_params
        if extra_body_fields is not None:
            target[_K.EXTRA_BODY_FIELDS] = extra_body_fields
        return self._create_export(HandlerType.GENERIC_REST_API_EXPORT, target, **kwargs)

    def publish_to_db(self, table: str, odbc_type: OdbcType = OdbcType.POSTGRES) -> dict[str, Any]:
        """Publish this view to a Mammoth-managed database for dashboards.

        Unlike the other export helpers, publish-to-db uses
        Mammoth-managed connection credentials (configured once per
        workspace) — you only name the target *table* and connection type.
        It posts to the dedicated ``publish-to-db`` endpoint, not the
        pipeline-exports endpoint.

        Args:
            table: Destination table name.
            odbc_type: Managed connection type (postgres or bigquery).

        Returns:
            Dict with the tracking ``job_id`` for the publish job.

        Example::

            view.export.publish_to_db(table="sales_dashboard")
        """
        ws = self._client.workspace_id
        proj = getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        return self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/datasets/{self._view.dataset_id}"
            f"/dataviews/{self._view.id}/publish-to-db",
            json={_K.ODBC_TYPE: odbc_type.value, "target_properties": {_K.TABLE: table}},
        )

    def list(self) -> _list[dict[str, Any]]:
        """List all exports configured for this dataview.

        Returns:
            List of export dicts, each with ``id``, ``handler_type``,
            ``target_properties``, etc.

        Example::

            exports = view.export.list()
            for exp in exports:
                print(f"{exp['id']}: {exp['handler_type']}")
        """
        result = self._client.exports.list(dataview_id=self._view.id)
        if hasattr(result, "exports"):
            return result.exports
        return result.get("exports", []) if isinstance(result, dict) else []

    def delete(self, export_id: int) -> dict[str, Any]:
        """Delete an export configuration.

        Args:
            export_id: ID of the export to delete (from ``list()``).

        Returns:
            Deletion confirmation dict.

        Example::

            exports = view.export.list()
            view.export.delete(exports[0]["id"])
        """
        ws = self._client.workspace_id
        proj = getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        return self._client._request_json(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{self._view.dataset_id}"
            f"/dataviews/{self._view.id}/pipeline/exports/{export_id}",
        )
