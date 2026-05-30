"""Advanced operation mixins: join, lookup, json_extract, gen_ai, sql."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth._pure.builders import (
    build_gen_ai_params,
    build_join_params,
    build_json_extract_params,
    build_lookup_params,
    build_sql_params,
)
from mammoth.models.pipeline import (
    JoinKeySpec,
    JoinSelectSpec,
    JoinType,
    JsonExtractionSpec,
    JsonOpType,
    JsonType,
)

if TYPE_CHECKING:
    from mammoth._mixins._host import ViewHost
    from mammoth.view import View
else:
    ViewHost = object


class AdvancedOpsMixin(ViewHost):
    """Mixin for advanced operations on a View: join, lookup, JSON, AI, SQL."""

    def join(
        self,
        foreign_view: int | View,
        join_type: JoinType,
        on: list[JoinKeySpec],
        select: list[str | JoinSelectSpec],
        column_prefix: str | None = None,
    ) -> dict[str, Any]:
        """Join with another dataview (JOIN task).

        Args:
            foreign_view: View object or ID of the dataview to join with.
                When a View object is passed, display names in ``on.right``
                and ``select`` are resolved automatically.
            join_type: Join type.
            on: Join keys as JoinKeySpec objects::

                [JoinKeySpec(left="Customer ID", right="Customer ID")]

            select: Columns to bring in from the foreign view. Simple list of
                display names or JoinSelectSpec objects::

                    ["Category", "Name"]
                    [JoinSelectSpec(column="Category", alias="Cat")]

            column_prefix: Prefix for joined columns (optional).

        Returns:
            API response dict.

        Examples::

            # Join with View object (display names everywhere)
            other = client.views.get(2050)
            view.join(
                foreign_view=other,
                join_type=JoinType.LEFT,
                on=[JoinKeySpec(left="Customer ID", right="Customer ID")],
                select=["Category", "Name"],
            )

            # Join with view ID (internal names for foreign view)
            view.join(
                foreign_view=2050,
                join_type=JoinType.LEFT,
                on=[JoinKeySpec(left="Customer ID", right="column_1")],
                select=[JoinSelectSpec(column="column_7", alias="Category")],
            )
        """
        # Resolve foreign view
        foreign_view_id: int
        foreign_columns: dict[str, str] | None = None

        if isinstance(foreign_view, int):
            foreign_view_id = foreign_view
        else:
            foreign_view_id = foreign_view.id
            foreign_columns = foreign_view.columns

        return self._add_task(
            build_join_params(
                foreign_view_id,
                join_type,
                on,
                select,
                self.columns,
                self._internal_names,
                foreign_columns=foreign_columns,
                column_prefix=column_prefix,
            )
        )

    def lookup(
        self,
        source: str,
        lookup_view_id: int,
        key: str,
        value: str,
        new_column: str | None = None,
        existing_column: str | None = None,
    ) -> dict[str, Any]:
        """VLOOKUP-style value lookup from another dataview (LOOKUP task).

        For each row, matches ``source`` against ``key`` in the lookup view
        and returns the corresponding ``value``.

        Args:
            source: Display name of the key column in *this* view.
            lookup_view_id: ID of the dataview to look up from.
            key: Column name of the key in the lookup view (display name
                or internal name — both are accepted).
            value: Column name of the value in the lookup view (display name
                or internal name — both are accepted).
            new_column: Name for a new result column.
            existing_column: Display name of existing column to overwrite.

        Returns:
            API response dict.

        Example::

            view.lookup(
                source="Product ID",
                lookup_view_id=2055,
                key="column_abc123",
                value="column_xyz789",
                new_column="Product Name",
            )
        """
        return self._add_task(
            build_lookup_params(
                source,
                lookup_view_id,
                key,
                value,
                self.columns,
                self._internal_names,
                new_column=new_column,
                existing_column=existing_column,
                name_gen=self._next_internal_name,
            )
        )

    def json_extract(
        self,
        column: str,
        json_type: JsonType = JsonType.OBJECT,
        keys: list[str] | None = None,
        extractions: list[JsonExtractionSpec] | None = None,
        keep_source: bool = False,
        op_type: JsonOpType | None = None,
    ) -> dict[str, Any]:
        """Extract data from JSON column (JSON_HANDLE task).

        Args:
            column: Source JSON column display name.
            json_type: JSON structure type (default JsonType.OBJECT).
            keys: Simple list of keys to extract (each becomes TEXT column).
                Use for quick extraction without custom types/aliases.
            extractions: Advanced extraction specs as JsonExtractionSpec objects
                (overrides keys)::

                [JsonExtractionSpec(key="name", as_name="Name", type=ColumnType.TEXT)]

            keep_source: Keep the original JSON column (default False).
            op_type: Operation type override.

        Returns:
            API response dict.

        Example::

            # Simple key extraction
            view.json_extract("data", keys=["name", "email", "age"])

            # Advanced with custom types
            view.json_extract(
                "data",
                extractions=[
                    JsonExtractionSpec(key="name", as_name="Name"),
                    JsonExtractionSpec(key="age", as_name="Age", type=ColumnType.NUMERIC),
                ],
            )
        """
        return self._add_task(
            build_json_extract_params(
                column,
                self.columns,
                self._internal_names,
                json_type=json_type,
                keys=keys,
                extractions=extractions,
                keep_source=keep_source,
                op_type=op_type,
                name_gen=self._next_internal_name,
            )
        )

    def gen_ai(
        self,
        prompt: str,
        context_columns: list[str],
        new_column: str = "AI Result",
        assistant_data: list[str] | None = None,
        context_columns_derivation: bool | None = None,
    ) -> dict[str, Any]:
        """AI-powered transformation (GEN_AI task).

        Args:
            prompt: Natural language prompt for the AI.
            context_columns: Display names of columns to use as context.
            new_column: Name for the AI output column (default "AI Result").
            assistant_data: Additional assistant context strings.
            context_columns_derivation: Whether to derive from context columns.

        Returns:
            API response dict.

        Example::

            view.gen_ai(
                prompt="Classify the sentiment of the review",
                context_columns=["Review Text"],
                new_column="Sentiment",
            )
        """
        return self._add_task(
            build_gen_ai_params(
                prompt,
                context_columns,
                self.columns,
                self._internal_names,
                new_column=new_column,
                assistant_data=assistant_data,
                context_columns_derivation=context_columns_derivation,
                name_gen=self._next_internal_name,
            )
        )

    def _next_sequence_number(self) -> int:
        """Return the next pipeline sequence number for this view."""
        tasks = self.list_tasks()
        if not tasks:
            return 1
        return max(t.get("sequence", 0) for t in tasks) + 1

    def generate_sql(self, intent: str) -> str:
        """Generate SQL from natural language using the Mammoth LLM.

        Calls the ``/sql_generation`` endpoint which converts the intent
        into SQL, adds the resulting task to the pipeline, waits for
        completion, and returns the generated query.

        Args:
            intent: Natural language description of the desired query
                (e.g. ``"count employees by department"``).

        Returns:
            The generated SQL query string.

        Example::

            sql = view.generate_sql("show total sales by region")
            print(sql)  # "SELECT region, SUM(sales) FROM ... GROUP BY region"
        """
        ws = self._client.workspace_id
        proj = getattr(self._client, "project_id", None)
        if proj is None:
            raise ValueError("project_id must be set")

        seq = self._next_sequence_number()
        result = self._client._request_json(
            "POST",
            f"/workspaces/{ws}/projects/{proj}/sql_generation",
            params={
                "dataset_id": self.dataset_id,
                "dataview_id": self.id,
            },
            json={"params": {"intent": intent, "sequence_number": seq}},
        )

        job_id = result.get("id")
        if job_id:
            job = self._client.jobs.wait_for_job(job_id)
        else:
            job = result
        self._client.pipeline.wait_for_pipeline(self.id, self.dataset_id)
        self.refresh()

        resp = job.get("response", {})
        inner = resp.get("response", resp)
        return inner.get("result", "")

    def add_sql(self, query: str) -> dict[str, Any]:
        """Add a raw SQL query as a pipeline task (SQL task).

        The query runs against the dataview's underlying data. Column
        references should use internal names (e.g. ``column_abc123``).

        .. note::

            Requires the SQL addon to be enabled on the workspace.

        Args:
            query: SQL query string.

        Returns:
            API response dict.

        Example::

            view.add_sql("SELECT *, column_abc * 2 AS doubled FROM __TABLE__")
        """
        return self._add_task(build_sql_params(query))
