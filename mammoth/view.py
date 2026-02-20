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
    view.branch_out(dest_dataset_id=42)
"""

from __future__ import annotations

import datetime
import random
import string
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
from mammoth.condition import CompoundCondition, Condition, NotCondition

_list = list  # Alias to avoid shadowing by method name

# Keys that control export behavior vs. target_properties
_EXPORT_CONTROL_KEYS = frozenset(
    {
        "trigger_type",
        "additional_properties",
        "condition",
        "run_immediately",
        "validate_only",
        "end_of_pipeline",
    }
)


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

        # Attach export helper
        self.export = ViewExport(self)

    def _build_column_maps(self, data: dict[str, Any]) -> None:
        """Extract column name mappings from dataview metadata."""
        self.columns = {}
        self.display_names = []
        self.column_types = {}
        self._internal_names = []

        columns_list = data.get("metadata", [])
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
        from mammoth.exceptions import MammothColumnError

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

        Args:
            task_spec: Task specification dict.

        Returns:
            API response dict.
        """
        result = self._client.pipeline.add_task(self.id, task_spec, self.dataset_id)
        self._client.pipeline.wait_for_pipeline(self.id, self.dataset_id)
        self.refresh()
        return result

    # ── Data Access ─────────────────────────────────────────────

    def data(
        self,
        limit: int = 400,
        offset: int = 1,
        columns: list[str] | None = None,
        condition: Condition | CompoundCondition | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Fetch data from the dataview.

        Args:
            limit: Number of rows to fetch (default 400).
            offset: One-indexed starting row (default 1).
            columns: List of display names to fetch (default all).
            condition: Condition object for filtering.
            sort: Sort specification string.

        Returns:
            Dict with data rows, columns, and pagination info.
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

        Returns:
            self (for chaining).
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

    # ── Pipeline Management ─────────────────────────────────────

    def list_tasks(self) -> list[dict[str, Any]]:
        """List all pipeline tasks on this dataview.

        Returns:
            List of task dicts.
        """
        result = self._client.pipeline.list_tasks(self.id, self.dataset_id)
        return result.get("tasks", result if isinstance(result, list) else [])

    def delete_task(self, task_id: int) -> dict[str, Any]:
        """Delete a pipeline task.

        Args:
            task_id: ID of the task to remove.

        Returns:
            Deletion confirmation dict.
        """
        result = self._client.pipeline.delete_task(self.id, task_id, self.dataset_id)
        self._client.pipeline.wait_for_pipeline(self.id, self.dataset_id)
        self.refresh()
        return result

    def preview_task(self, task_spec: dict[str, Any]) -> dict[str, Any]:
        """Preview a task without applying it.

        Args:
            task_spec: Task specification dict.

        Returns:
            Preview data dict.
        """
        return self._client.pipeline.preview_task(self.id, task_spec, self.dataset_id)

    def get_column_mapping(self) -> dict[str, str]:
        """Return a mapping of display names to internal column names.

        Returns:
            Dict mapping display names to internal names.
        """
        return dict(self.columns)

    def branch_out(
        self,
        dest_dataset_id: int,
        column_mapping: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Branch out (export) this view to another dataset.

        Args:
            dest_dataset_id: Target dataset ID.
            column_mapping: Column mapping dict (optional).
            **kwargs: Additional export options.

        Returns:
            Export result dict.
        """
        return self.export.to_dataset(dest_dataset_id, column_mapping, **kwargs)

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
        self, handler_type: str, target_properties: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Internal helper to create an export."""
        from mammoth.models.exports import AddExportSpec, HandlerType, TriggerType

        spec = AddExportSpec(
            DATAVIEW_ID=self._view.id,
            handler_type=HandlerType(handler_type),
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
    ) -> dict[str, Any]:
        """Export to PostgreSQL database.

        Args:
            host: Database host.
            port: Database port.
            database: Database name.
            table: Target table name.
            username: Database username.
            password: Database password.

        Returns:
            Export result dict.
        """
        return self._create_export(
            "POSTGRES",
            {
                "host": host,
                "port": port,
                "database": database,
                "table": table,
                "username": username,
                "password": password,
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
    ) -> dict[str, Any]:
        """Export to MySQL database.

        Args:
            host: Database host.
            port: Database port.
            database: Database name.
            table: Target table name.
            username: Database username.
            password: Database password.

        Returns:
            Export result dict.
        """
        return self._create_export(
            "MYSQL",
            {
                "host": host,
                "port": port,
                "database": database,
                "table": table,
                "username": username,
                "password": password,
            },
            **kwargs,
        )

    def to_s3(
        self,
        file_name: str | None = None,
        file_type: str = "csv",
        include_hidden: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Export to S3.

        Args:
            file_name: Output filename (auto-generated if not provided).
            file_type: File format (default "csv").
            include_hidden: Include hidden columns (default False).

        Returns:
            Export result dict with download URL.
        """
        if file_name is None:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"view_{self._view.id}_export_{ts}.{file_type}"

        return self._create_export(
            "S3",
            {
                "file": file_name,
                "file_type": file_type,
                "include_hidden": include_hidden,
                "is_format_set": True,
                "use_format": True,
            },
            **kwargs,
        )

    def to_dataset(
        self,
        dest_dataset_id: int,
        column_mapping: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Export to another Mammoth dataset (branch out).

        Args:
            dest_dataset_id: Target dataset ID.
            column_mapping: Column mapping dict (optional).

        Returns:
            Export result dict.
        """
        target: dict[str, Any] = {"dataset_name": str(dest_dataset_id)}
        if column_mapping:
            target["COLUMN_MAPPING"] = column_mapping
        return self._create_export("INTERNAL_DATASET", target, **kwargs)

    def to_csv(self, output_path: str | None = None, timeout: int = 300) -> Path:
        """Download dataview data as CSV file.

        Args:
            output_path: Path for the output file.
            timeout: Timeout in seconds (default 300).

        Returns:
            Path to the downloaded CSV file.
        """
        return self._client.exports.to_csv(
            dataview_id=self._view.id,
            output_path=output_path,
            timeout=timeout,
            dataset_id=self._view.dataset_id,
        )

    def to_ftp(
        self,
        host: str,
        path: str,
        username: str,
        password: str,
        port: int = 21,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Export to FTP server.

        Args:
            host: FTP host.
            path: Remote file path.
            username: FTP username.
            password: FTP password.
            port: FTP port (default 21).

        Returns:
            Export result dict.
        """
        return self._create_export(
            "FTP",
            {
                "host": host,
                "port": port,
                "path": path,
                "username": username,
                "password": password,
            },
            **kwargs,
        )

    def to_sftp(
        self,
        host: str,
        path: str,
        username: str,
        password: str,
        port: int = 22,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Export to SFTP server.

        Args:
            host: SFTP host.
            path: Remote file path.
            username: SFTP username.
            password: SFTP password.
            port: SFTP port (default 22).

        Returns:
            Export result dict.
        """
        return self._create_export(
            "SFTP",
            {
                "host": host,
                "port": port,
                "path": path,
                "username": username,
                "password": password,
            },
            **kwargs,
        )

    def to_email(self, recipients: list[str], **kwargs: Any) -> dict[str, Any]:
        """Export via email.

        Args:
            recipients: List of email addresses.

        Returns:
            Export result dict.
        """
        return self._create_export("EMAIL", {"recipients": recipients}, **kwargs)

    def to_bigquery(self, **kwargs: Any) -> dict[str, Any]:
        """Export to Google BigQuery.

        Args:
            **kwargs: BigQuery connection and table configuration.

        Returns:
            Export result dict.
        """
        target = {k: v for k, v in kwargs.items() if k not in _EXPORT_CONTROL_KEYS}
        return self._create_export("BIGQUERY", target, **kwargs)

    def to_redshift(self, **kwargs: Any) -> dict[str, Any]:
        """Export to Amazon Redshift.

        Args:
            **kwargs: Redshift connection and table configuration.

        Returns:
            Export result dict.
        """
        target = {k: v for k, v in kwargs.items() if k not in _EXPORT_CONTROL_KEYS}
        return self._create_export("REDSHIFT", target, **kwargs)

    def to_elasticsearch(self, **kwargs: Any) -> dict[str, Any]:
        """Export to Elasticsearch.

        Args:
            **kwargs: Elasticsearch connection and index configuration.

        Returns:
            Export result dict.
        """
        target = {k: v for k, v in kwargs.items() if k not in _EXPORT_CONTROL_KEYS}
        return self._create_export("ELASTICSEARCH", target, **kwargs)

    def publish_to_db(self, **kwargs: Any) -> dict[str, Any]:
        """Publish dataview to database.

        Args:
            **kwargs: Database connection and table configuration.

        Returns:
            Export result dict.
        """
        target = {k: v for k, v in kwargs.items() if k not in _EXPORT_CONTROL_KEYS}
        return self._create_export("PUBLISHDB", target, **kwargs)

    def list(self) -> _list[dict[str, Any]]:
        """List all exports for this dataview.

        Returns:
            List of export dicts.
        """
        result = self._client.exports.list(dataview_id=self._view.id)
        if hasattr(result, "exports"):
            return result.exports
        return result.get("exports", []) if isinstance(result, dict) else []

    def delete(self, export_id: int) -> dict[str, Any]:
        """Delete an export.

        Args:
            export_id: ID of the export to delete.

        Returns:
            Deletion confirmation dict.
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
