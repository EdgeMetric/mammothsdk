"""
Rich View domain object for working with Mammoth dataviews.

The View object is the central interface for data transformations.
Get one via client.views.get(view_id):

    view = client.views.get(1039)
    print(view.display_names)     # ["Sales", "Region", ...]
    print(view.columns)           # {"Sales": "column_1", ...}

    # Transformations
    view.filter_rows(Condition("Sales", Operator.GTE, 1000))
    view.set_values(new_column="Label", column_type="TEXT", values=[...])
    view.math(expression=[...], new_column="Total")

    # Exports
    view.export.to_csv("output.csv")
    view.export.to_postgres(host="...", database="...", table="...")
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path


class View:
    """Rich domain object for a Mammoth dataview.

    Provides access to dataview metadata, data, pipeline tasks,
    and 25+ transformation methods. Created via client.views.get().

    Attributes:
        id: Dataview ID.
        dataset_id: Parent dataset ID.
        columns: Dict mapping display names to internal names (e.g. {"Sales": "column_1"}).
        display_names: List of column display names.
        column_types: Dict mapping display names to types (e.g. {"Sales": "numeric"}).
        raw: Raw API response dict.
        export: ViewExport helper for export operations.
    """

    def __init__(self, client, dataview_data: dict, dataset_id: int):
        self._client = client
        self.raw = dataview_data
        self.id = dataview_data.get("id")
        self.dataset_id = dataset_id
        self.name = dataview_data.get("name", "")

        # Build column mappings from metadata
        self._build_column_maps(dataview_data)

        # Attach export helper
        self.export = ViewExport(self)

    def _build_column_maps(self, data: dict) -> None:
        """Extract column name mappings from dataview metadata."""
        self.columns: Dict[str, str] = {}
        self.display_names: List[str] = []
        self.column_types: Dict[str, str] = {}
        self._internal_names: List[str] = []

        properties = data.get("properties", {})
        columns_list = properties.get("columns", [])

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
        # Check if it's already an internal name
        if display_name in self._internal_names:
            return display_name
        from .exceptions import MammothColumnError
        raise MammothColumnError(display_name, self.display_names)

    def _resolve_columns(self, names: List[str]) -> List[str]:
        """Resolve multiple display names to internal names."""
        return [self._resolve_column(n) for n in names]

    def _next_internal_name(self) -> str:
        """Compute the next available internal column name (column_{n+1})."""
        max_num = 0
        for name in self._internal_names:
            if name.startswith("column_"):
                try:
                    num = int(name.split("_", 1)[1])
                    max_num = max(max_num, num)
                except (ValueError, IndexError):
                    pass
        return f"column_{max_num + 1}"

    def _build_as_column(self, name: str, column_type: str = "TEXT", internal_name: Optional[str] = None) -> dict:
        """Build an AS (new column) spec."""
        return {
            "COLUMN": name,
            "TYPE": column_type.upper(),
            "INTERNAL_NAME": internal_name or self._next_internal_name(),
        }

    def _build_condition(self, condition) -> Optional[dict]:
        """Build condition dict from Condition object or raw dict."""
        if condition is None:
            return None
        if isinstance(condition, dict):
            return condition
        # Condition or CompoundCondition with .build()
        return condition.build(self.columns)

    def _add_task(self, task_spec: dict) -> dict:
        """Add a task to the pipeline and refresh metadata.

        Args:
            task_spec: Task specification dict.

        Returns:
            API response dict.
        """
        result = self._client.pipeline.add_task(self.id, task_spec, self.dataset_id)
        self.refresh()
        return result

    # ── Data Access ─────────────────────────────────────────────

    def data(
        self,
        limit: int = 400,
        offset: int = 1,
        columns: Optional[List[str]] = None,
        condition: Optional[Any] = None,
        sort: Optional[str] = None,
    ) -> dict:
        """Fetch data from the dataview.

        Args:
            limit: Number of rows to fetch (default 400).
            offset: One-indexed starting row (default 1).
            columns: List of display names to fetch (default all).
            condition: Condition object or raw dict for filtering.
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

    def refresh(self) -> "View":
        """Re-fetch metadata from the API and update local state.

        Returns:
            self (for chaining).
        """
        ws = self._client.workspace_id
        proj = getattr(self._client, 'project_id', None)
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

    def list_tasks(self) -> list:
        """List all pipeline tasks on this dataview.

        Returns:
            List of task dicts.
        """
        result = self._client.pipeline.list_tasks(self.id, self.dataset_id)
        return result.get("tasks", result if isinstance(result, list) else [])

    def delete_task(self, task_id: int) -> dict:
        """Delete a pipeline task.

        Args:
            task_id: ID of the task to remove.

        Returns:
            Deletion confirmation dict.
        """
        result = self._client.pipeline.delete_task(self.id, task_id, self.dataset_id)
        self.refresh()
        return result

    def preview_task(self, task_spec: dict) -> dict:
        """Preview a task without applying it.

        Args:
            task_spec: Task specification dict.

        Returns:
            Preview data dict.
        """
        return self._client.pipeline.preview_task(self.id, task_spec, self.dataset_id)

    # ── Transformation Methods ──────────────────────────────────

    def set_values(
        self,
        values: List[dict],
        new_column: Optional[str] = None,
        column_type: str = "TEXT",
        existing_column: Optional[str] = None,
        condition: Optional[Any] = None,
    ) -> dict:
        """Label and insert values into a new or existing column (SET task).

        Args:
            values: List of value specs. Each dict has "value" and optional "condition":
                    [{"value": "High", "condition": Condition(...)}, {"value": "Low"}]
            new_column: Name for a new column (mutually exclusive with existing_column).
            column_type: Type for new column: "TEXT", "NUMERIC", or "DATE" (default "TEXT").
            existing_column: Display name of existing column to update.
            condition: Global condition applied to the whole task.

        Returns:
            API response dict.

        Examples:
            # New column with conditional values
            view.set_values(
                new_column="Risk Level", column_type="TEXT",
                values=[
                    {"value": "High", "condition": Condition("Sales", Operator.GTE, 10000)},
                    {"value": "Low"},
                ],
            )

            # Update existing column
            view.set_values(existing_column="Status", values=[{"value": "Active"}])
        """
        set_items = []
        for v in values:
            item = {"VALUE": v["value"], "TYPE": "FIXED"}
            if "condition" in v and v["condition"] is not None:
                item["CONDITION"] = self._build_condition(v["condition"])
            set_items.append(item)

        spec: dict = {"SET": set_items}

        if new_column:
            spec["SET"] = [{**item} for item in set_items]
            # For new columns, embed the AS spec in each set item or at task level
            internal = self._next_internal_name()
            for item in spec["SET"]:
                item.setdefault("AS", self._build_as_column(new_column, column_type, internal))
        elif existing_column:
            dest = self._resolve_column(existing_column)
            for item in spec["SET"]:
                item["DESTINATION"] = dest

        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def filter_rows(self, condition: Any) -> dict:
        """Filter rows by condition (SELECT task).

        Args:
            condition: Condition or CompoundCondition object, or raw condition dict.

        Returns:
            API response dict.

        Example:
            view.filter_rows(Condition("Sales", Operator.GTE, 1000))
            view.filter_rows(cond1 & cond2)
        """
        spec: dict = {"SELECT": "*"}
        spec["CONDITION"] = self._build_condition(condition)
        return self._add_task(spec)

    def math(
        self,
        expression: list,
        new_column: Optional[str] = None,
        column_type: str = "NUMERIC",
        existing_column: Optional[str] = None,
        condition: Optional[Any] = None,
    ) -> dict:
        """Apply arithmetic operations (MATH task).

        Args:
            expression: List of expression parts:
                        [{"TYPE": "COLUMN", "VALUE": "Sales"},
                         {"TYPE": "OPERATOR", "VALUE": "*"},
                         {"TYPE": "NUMBER", "VALUE": 1.1}]
            new_column: Name for result column (creates new).
            column_type: Type for new column (default "NUMERIC").
            existing_column: Existing column to overwrite.
            condition: Condition to apply.

        Returns:
            API response dict.

        Example:
            view.math(
                expression=[
                    {"TYPE": "COLUMN", "VALUE": "Price"},
                    {"TYPE": "OPERATOR", "VALUE": "*"},
                    {"TYPE": "COLUMN", "VALUE": "Quantity"},
                ],
                new_column="Total",
            )
        """
        # Resolve column references in expression
        resolved_expr = []
        for part in expression:
            p = dict(part)
            if p.get("TYPE") == "COLUMN" and p.get("VALUE") in self.columns:
                p["VALUE"] = self.columns[p["VALUE"]]
            resolved_expr.append(p)

        math_spec: dict = {"EXPRESSION": resolved_expr}

        if new_column:
            math_spec["AS"] = self._build_as_column(new_column, column_type)
        elif existing_column:
            math_spec["DESTINATION"] = self._resolve_column(existing_column)

        spec: dict = {"MATH": math_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def sql(self, query: Optional[str] = None, intent: Optional[str] = None) -> dict:
        """Execute raw SQL or natural language intent (SQL task).

        Args:
            query: Raw SQL query string.
            intent: Natural language description (converted to SQL by Mammoth).

        Returns:
            API response dict.

        Examples:
            view.sql(query="SELECT * FROM table WHERE amount > 100")
            view.sql(intent="show total sales by region")
        """
        sql_spec: dict = {}
        if query:
            sql_spec["QUERY"] = query
        if intent:
            sql_spec["INTENT"] = intent

        return self._add_task({"SQL": sql_spec})

    def copy_columns(self, copies: List[dict]) -> dict:
        """Duplicate columns (COPY task).

        Args:
            copies: List of copy specs:
                    [{"source": "Sales", "as": "Sales Copy", "type": "NUMERIC"}]

        Returns:
            API response dict.
        """
        copy_items = []
        for c in copies:
            internal = self._next_internal_name()
            copy_items.append({
                "SOURCE": self._resolve_column(c["source"]),
                "AS": self._build_as_column(c.get("as", f"{c['source']} Copy"), c.get("type", "TEXT"), internal),
            })

        return self._add_task({"COPY": copy_items})

    def delete_columns(self, columns: List[str]) -> dict:
        """Remove columns (DELETE task).

        Args:
            columns: List of display names to delete.

        Returns:
            API response dict.
        """
        return self._add_task({"DELETE": self._resolve_columns(columns)})

    def add_column(self, name: str, column_type: str = "TEXT") -> dict:
        """Add an empty column (ADD_COLUMN task).

        Args:
            name: Display name for the new column.
            column_type: Column type: "TEXT", "NUMERIC", or "DATE" (default "TEXT").

        Returns:
            API response dict.
        """
        return self._add_task({
            "ADD_COLUMN": [{
                "COLUMN": name,
                "TYPE": column_type.upper(),
                "INTERNAL_NAME": self._next_internal_name(),
            }],
        })

    def combine_columns(
        self,
        sources: List[str],
        new_column: Optional[str] = None,
        column_type: str = "TEXT",
        existing_column: Optional[str] = None,
        separator: str = " ",
        condition: Optional[Any] = None,
    ) -> dict:
        """Concatenate columns (COMBINE task).

        Args:
            sources: List of display names to combine.
            new_column: Name for result column.
            column_type: Type for new column (default "TEXT").
            existing_column: Existing column to overwrite.
            separator: Separator between values (default space).
            condition: Condition to apply.

        Returns:
            API response dict.
        """
        source_specs = []
        for s in sources:
            source_specs.append({"SOURCE": self._resolve_column(s), "SEPARATOR": separator})

        combine_spec: dict = {"SOURCE": source_specs}

        if new_column:
            combine_spec["AS"] = self._build_as_column(new_column, column_type)
        elif existing_column:
            combine_spec["DESTINATION"] = self._resolve_column(existing_column)

        spec: dict = {"COMBINE": combine_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def replace_values(
        self,
        columns: List[str],
        find: str,
        replace: str,
        match_case: bool = False,
        match_words: bool = False,
        condition: Optional[Any] = None,
    ) -> dict:
        """Find and replace values (REPLACE task).

        Args:
            columns: List of display names to search in.
            find: Text to find.
            replace: Replacement text.
            match_case: Case-sensitive matching (default False).
            match_words: Match whole words only (default False).
            condition: Condition to apply.

        Returns:
            API response dict.
        """
        replace_spec: dict = {
            "SOURCE": self._resolve_columns(columns),
            "VALUE_PAIR": [{"FIND": find, "REPLACE": replace}],
            "MATCH_CASE": match_case,
            "MATCH_WORDS": match_words,
        }

        spec: dict = {"REPLACE": replace_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def convert_type(self, conversions: List[dict]) -> dict:
        """Convert column types (CONVERT task).

        Args:
            conversions: List of conversion specs:
                         [{"column": "Sales", "to": "NUMERIC"}]

        Returns:
            API response dict.
        """
        convert_items = []
        for c in conversions:
            convert_items.append({
                "SOURCE": self._resolve_column(c["column"]),
                "TYPE": c["to"].upper(),
            })

        return self._add_task({"CONVERT": convert_items})

    def text_transform(
        self,
        columns: List[str],
        case: Optional[str] = None,
        trim: bool = False,
        condition: Optional[Any] = None,
    ) -> dict:
        """Apply text case change or trim (TEXT_TRANSFORM task).

        Args:
            columns: List of display names to transform.
            case: Case transformation: "UPPER", "LOWER", or "TITLE" (optional).
            trim: Whether to trim whitespace (default False).
            condition: Condition to apply.

        Returns:
            API response dict.
        """
        tt_spec: dict = {
            "SOURCE": self._resolve_columns(columns),
            "TRIM": trim,
        }
        if case:
            tt_spec["CASE"] = case.upper()

        spec: dict = {"TEXT_TRANSFORM": tt_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def split_column(
        self,
        column: str,
        delimiter: str,
        new_columns: List[dict],
    ) -> dict:
        """Split a column by delimiter (SPLIT task).

        Args:
            column: Display name of column to split.
            delimiter: Delimiter string.
            new_columns: List of new column specs:
                         [{"name": "First", "type": "TEXT"}, {"name": "Last", "type": "TEXT"}]

        Returns:
            API response dict.
        """
        as_columns = []
        for nc in new_columns:
            as_columns.append(self._build_as_column(nc["name"], nc.get("type", "TEXT")))

        return self._add_task({
            "SPLIT": {
                "SOURCE": self._resolve_column(column),
                "DELIMITER": delimiter,
                "AS": as_columns,
            },
        })

    def join(
        self,
        foreign_view_id: int,
        join_type: str,
        on: List[dict],
        select: List[dict],
        column_prefix: Optional[str] = None,
    ) -> dict:
        """Join with another dataview (JOIN task).

        Args:
            foreign_view_id: ID of the dataview to join with.
            join_type: Join type: "INNER", "LEFT", "RIGHT", or "OUTER".
            on: Join keys: [{"source": "Customer ID", "foreign": "ID"}].
            select: Columns to bring in: [{"column": "Name", "as": "Customer Name"}].
            column_prefix: Prefix for joined columns (optional).

        Returns:
            API response dict.

        Example:
            view.join(
                foreign_view_id=2050, join_type="LEFT",
                on=[{"source": "Customer ID", "foreign": "ID"}],
                select=[{"column": "Name", "as": "Customer Name"}],
            )
        """
        import uuid
        join_spec: dict = {
            "JOIN_ID": str(uuid.uuid4())[:8],
            "DATAVIEW_ID": foreign_view_id,
            "TYPE": join_type.upper(),
            "ON": [{"SOURCE": self._resolve_column(j["source"]), "FOREIGN": j["foreign"]} for j in on],
            "SELECT": [{"SOURCE": j["column"], "AS": j.get("as", j["column"])} for j in select],
        }
        if column_prefix:
            join_spec["COLUMN_PREFIX"] = column_prefix

        return self._add_task({"JOIN": join_spec})

    def pivot(
        self,
        group_by: List[str],
        aggregations: List[dict],
        condition: Optional[Any] = None,
    ) -> dict:
        """Group / aggregate / pivot (PIVOT task).

        Args:
            group_by: List of display names to group by.
            aggregations: List of aggregation specs:
                          [{"column": "Sales", "function": "SUM", "as": "Total Sales"}]
            condition: Condition to apply.

        Returns:
            API response dict.

        Example:
            view.pivot(
                group_by=["Region"],
                aggregations=[{"column": "Sales", "function": "SUM", "as": "Total Sales"}],
            )
        """
        group_specs = [{"SOURCE": self._resolve_column(g)} for g in group_by]
        select_specs = []
        for agg in aggregations:
            select_specs.append({
                "SOURCE": self._resolve_column(agg["column"]),
                "FUNCTION": agg["function"].upper(),
                "AS": agg.get("as", f"{agg['function']}_{agg['column']}"),
            })

        pivot_spec: dict = {"GROUP_BY": group_specs, "SELECT": select_specs}
        if condition:
            pivot_spec["CONDITION"] = self._build_condition(condition)

        return self._add_task({"PIVOT": pivot_spec})

    def window(
        self,
        function: str,
        column: Optional[str] = None,
        new_column: Optional[str] = None,
        column_type: str = "NUMERIC",
        existing_column: Optional[str] = None,
        partition_by: Optional[List[str]] = None,
        order_by: Optional[List[List[str]]] = None,
        range_type: str = "UNBOUNDED",
    ) -> dict:
        """Apply window function (WINDOW task).

        Args:
            function: Window function name (e.g. "ROW_NUMBER", "SUM", "LAG").
            column: Source column for aggregate window functions.
            new_column: Name for result column.
            column_type: Type for new column (default "NUMERIC").
            existing_column: Existing column to overwrite.
            partition_by: List of display names to partition by.
            order_by: Sort spec: [["column_name", "ASC"]] or [["column_name", "DESC"]].
            range_type: Window range (default "UNBOUNDED").

        Returns:
            API response dict.

        Example:
            view.window(
                function="ROW_NUMBER",
                new_column="Row #",
                partition_by=["Region"],
                order_by=[["Sales", "DESC"]],
            )
        """
        evaluate: dict = {"FUNCTION": function.upper()}
        if column:
            evaluate["SOURCE"] = self._resolve_column(column)

        window_spec: dict = {"EVALUATE": evaluate, "RANGE": range_type}

        if new_column:
            window_spec["AS"] = self._build_as_column(new_column, column_type)
        elif existing_column:
            window_spec["DESTINATION"] = self._resolve_column(existing_column)

        if partition_by:
            window_spec["GROUP_BY"] = [{"SOURCE": self._resolve_column(p)} for p in partition_by]

        if order_by:
            resolved_order = []
            for ob in order_by:
                col = self._resolve_column(ob[0]) if ob[0] in self.columns else ob[0]
                direction = ob[1] if len(ob) > 1 else "ASC"
                resolved_order.append([col, direction])
            window_spec["ORDER_BY"] = resolved_order

        return self._add_task({"WINDOW": window_spec})

    def extract_date(
        self,
        column: str,
        component: str,
        new_column: Optional[str] = None,
        existing_column: Optional[str] = None,
    ) -> dict:
        """Extract date parts (EXTRACT_DATE task).

        Args:
            column: Source date column display name.
            component: Date component: "YEAR", "MONTH", "DAY", "HOUR", etc.
            new_column: Name for result column.
            existing_column: Existing column to overwrite.

        Returns:
            API response dict.

        Example:
            view.extract_date("Order Date", "YEAR", new_column="Order Year")
        """
        ed_spec: dict = {
            "SOURCE": self._resolve_column(column),
            "COMPONENT": component.upper(),
        }

        if new_column:
            ed_spec["AS"] = self._build_as_column(new_column, "NUMERIC")
        elif existing_column:
            ed_spec["DESTINATION"] = self._resolve_column(existing_column)

        return self._add_task({"EXTRACT_DATE": ed_spec})

    def date_diff(
        self,
        component: str,
        start: str,
        end: str,
        new_column: Optional[str] = None,
        existing_column: Optional[str] = None,
    ) -> dict:
        """Calculate date difference (DATE_DIFF task).

        Args:
            component: Unit of difference: "YEAR", "MONTH", "DAY", etc.
            start: Start date column display name.
            end: End date column display name.
            new_column: Name for result column.
            existing_column: Existing column to overwrite.

        Returns:
            API response dict.

        Example:
            view.date_diff("DAY", start="Start Date", end="End Date", new_column="Duration")
        """
        dd_spec: dict = {
            "COMPONENT": component.upper(),
            "MINUEND": {"SOURCE": self._resolve_column(end)},
            "SUBTRAHEND": {"SOURCE": self._resolve_column(start)},
        }

        if new_column:
            dd_spec["AS"] = self._build_as_column(new_column, "NUMERIC")
        elif existing_column:
            dd_spec["DESTINATION"] = self._resolve_column(existing_column)

        return self._add_task({"DATE_DIFF": dd_spec})

    def increment_date(
        self,
        column: str,
        delta: dict,
        new_column: Optional[str] = None,
        existing_column: Optional[str] = None,
        condition: Optional[Any] = None,
    ) -> dict:
        """Add or subtract from a date column (INCREMENT_DATE task).

        Args:
            column: Source date column display name.
            delta: Delta spec: {"DAYS": 30} or {"MONTHS": -1, "YEARS": 2}.
            new_column: Name for result column.
            existing_column: Existing column to overwrite.
            condition: Condition to apply.

        Returns:
            API response dict.
        """
        id_spec: dict = {
            "SOURCE": self._resolve_column(column),
            "DELTA": delta,
        }

        if new_column:
            id_spec["AS"] = self._build_as_column(new_column, "DATE")
        elif existing_column:
            id_spec["DESTINATION"] = self._resolve_column(existing_column)

        spec: dict = {"INCREMENT_DATE": id_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def fill_missing(
        self,
        column: str,
        direction: str,
        partition_by: Optional[str] = None,
        order_by: Optional[List[List[str]]] = None,
    ) -> dict:
        """Fill missing values forward or backward (FILL task).

        Args:
            column: Display name of column to fill.
            direction: Fill direction: "FIRST_VALUE" (forward) or "LAST_VALUE" (backward).
            partition_by: Column to partition by (optional).
            order_by: Sort order for fill direction (optional).

        Returns:
            API response dict.
        """
        fill_spec: dict = {
            "COLUMN": self._resolve_column(column),
            "WITH": direction.upper(),
        }
        if partition_by:
            fill_spec["PARTITION_BY"] = self._resolve_column(partition_by)
        if order_by:
            resolved = []
            for ob in order_by:
                col = self._resolve_column(ob[0]) if ob[0] in self.columns else ob[0]
                direction_val = ob[1] if len(ob) > 1 else "ASC"
                resolved.append([col, direction_val])
            fill_spec["ORDER_BY"] = resolved

        return self._add_task({"FILL": fill_spec})

    def limit_rows(
        self,
        n: int,
        bottom: bool = False,
        order_by: Optional[List[List[str]]] = None,
    ) -> dict:
        """Keep top or bottom N rows (LIMIT task).

        Args:
            n: Number of rows to keep.
            bottom: If True, keep bottom N instead of top N (default False).
            order_by: Sort order before limiting (optional).

        Returns:
            API response dict.
        """
        spec: dict = {"LIMIT": {"LIMIT": n, "BOTTOM": bottom}}
        if order_by:
            resolved = []
            for ob in order_by:
                col = self._resolve_column(ob[0]) if ob[0] in self.columns else ob[0]
                direction = ob[1] if len(ob) > 1 else "ASC"
                resolved.append([col, direction])
            spec["ORDER_BY"] = resolved

        return self._add_task(spec)

    def lookup(
        self,
        source: str,
        lookup_view_id: int,
        key: str,
        value: str,
        new_column: Optional[str] = None,
        existing_column: Optional[str] = None,
    ) -> dict:
        """Lookup values from another dataview (LOOKUP task).

        Args:
            source: Source column display name (the key in this view).
            lookup_view_id: ID of the dataview to look up from.
            key: Key column name in the lookup view.
            value: Value column name in the lookup view.
            new_column: Name for result column.
            existing_column: Existing column to overwrite.

        Returns:
            API response dict.
        """
        lookup_spec: dict = {
            "SOURCE": self._resolve_column(source),
            "TABLE": str(lookup_view_id),
            "KEY": key,
            "VALUE": value,
        }

        if new_column:
            lookup_spec["AS"] = self._build_as_column(new_column, "TEXT")
        elif existing_column:
            lookup_spec["DESTINATION"] = self._resolve_column(existing_column)

        return self._add_task({"LOOKUP": lookup_spec})

    def substring(
        self,
        column: str,
        regex: Optional[dict] = None,
        direction: Optional[str] = None,
        num_char: Optional[int] = None,
        new_column: Optional[str] = None,
        existing_column: Optional[str] = None,
        condition: Optional[Any] = None,
    ) -> dict:
        """Extract text from a column (SUBSTRING task).

        Args:
            column: Source column display name.
            regex: Regex extraction spec: {"PATTERN": "...", "GROUP": 0}.
            direction: "LEFT" or "RIGHT" for character-based extraction.
            num_char: Number of characters to extract.
            new_column: Name for result column.
            existing_column: Existing column to overwrite.
            condition: Condition to apply.

        Returns:
            API response dict.
        """
        sub_spec: dict = {"SOURCE": self._resolve_column(column)}
        if regex:
            sub_spec["REGEX"] = regex
        if direction:
            sub_spec["DIRECTION"] = direction.upper()
        if num_char is not None:
            sub_spec["NUM_CHAR"] = num_char

        if new_column:
            sub_spec["AS"] = self._build_as_column(new_column, "TEXT")
        elif existing_column:
            sub_spec["DESTINATION"] = self._resolve_column(existing_column)

        spec: dict = {"SUBSTRING": sub_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def unnest(
        self,
        columns: List[str],
        label_column: str = "Label",
        value_column: str = "Value",
    ) -> dict:
        """Unpivot columns to rows (UNNEST task).

        Args:
            columns: Display names of columns to unnest.
            label_column: Name for the label column (default "Label").
            value_column: Name for the value column (default "Value").

        Returns:
            API response dict.
        """
        col_specs = [{"SOURCE": self._resolve_column(c)} for c in columns]
        label_internal = self._next_internal_name()
        value_internal = f"column_{int(label_internal.split('_')[1]) + 1}"

        return self._add_task({
            "UNNEST": {
                "COLUMNS": col_specs,
                "LABEL": {"COLUMN": label_column, "INTERNAL_NAME": label_internal, "TYPE": "TEXT"},
                "VALUE": {"COLUMN": value_column, "INTERNAL_NAME": value_internal, "TYPE": "TEXT"},
            },
        })

    def json_extract(
        self,
        column: str,
        json_type: str = "object",
        extractions: Optional[List[dict]] = None,
        keep_source: bool = False,
    ) -> dict:
        """Extract data from JSON column (JSON_HANDLE task).

        Args:
            column: Source JSON column display name.
            json_type: JSON type: "object" or "list".
            extractions: List of extraction specs:
                         [{"key": "name", "as": "Name", "type": "TEXT"}]
            keep_source: Keep the original JSON column (default False).

        Returns:
            API response dict.
        """
        extract_specs = []
        for e in (extractions or []):
            extract_specs.append({
                "KEY": e["key"],
                "AS": self._build_as_column(e.get("as", e["key"]), e.get("type", "TEXT")),
            })

        return self._add_task({
            "JSON_HANDLE": {
                "SOURCE": self._resolve_column(column),
                "TYPE": json_type,
                "JSON_EXTRACT": extract_specs,
                "JSON_KEEP_SOURCE": keep_source,
            },
        })

    def gen_ai(
        self,
        prompt: str,
        context_columns: List[str],
        new_column: str = "AI Result",
        assistant_data: Optional[List[str]] = None,
    ) -> dict:
        """AI-powered transformation (GEN_AI task).

        Args:
            prompt: Natural language prompt for the AI.
            context_columns: Display names of columns to use as context.
            new_column: Name for the AI output column (default "AI Result").
            assistant_data: Additional assistant context strings.

        Returns:
            API response dict.

        Example:
            view.gen_ai(
                prompt="Classify the sentiment of the review",
                context_columns=["Review Text"],
                new_column="Sentiment",
            )
        """
        return self._add_task({
            "GEN_AI": {
                "AS": self._build_as_column(new_column, "TEXT"),
                "ASSISTANT_DATA": assistant_data or [],
                "QUERY": prompt,
                "CONTEXT_COLUMNS": self._resolve_columns(context_columns),
            },
        })

    def crosstab(
        self,
        rows: List[str],
        pivot_column: str,
        select: dict,
    ) -> dict:
        """Crosstab / pivot table (CROSSTAB task).

        Args:
            rows: List of display names for row grouping.
            pivot_column: Display name of column whose values become columns.
            select: Aggregation spec: {"column": "Sales", "function": "SUM"}.

        Returns:
            API response dict.
        """
        return self._add_task({
            "CROSSTAB": {
                "ROWS": [{"SOURCE": self._resolve_column(r)} for r in rows],
                "COLUMNS": [{"SOURCE": self._resolve_column(pivot_column)}],
                "SELECT": {
                    "SOURCE": self._resolve_column(select["column"]),
                    "FUNCTION": select["function"].upper(),
                },
            },
        })

    def __repr__(self) -> str:
        return f"View(id={self.id}, name={self.name!r}, columns={len(self.display_names)})"


class ViewExport:
    """Export operations for a View. Access via view.export.

    Examples:
        view.export.to_csv("output.csv")
        view.export.to_postgres(host="...", database="...", table="...")
        view.export.list()
    """

    def __init__(self, view: View):
        self._view = view
        self._client = view._client

    def _create_export(self, handler_type: str, target_properties: dict, **kwargs) -> dict:
        """Internal helper to create an export."""
        from .models.exports import AddExportSpec, HandlerType, TriggerType
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
        **kwargs,
    ) -> dict:
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
        return self._create_export("POSTGRES", {
            "host": host, "port": port, "database": database,
            "table": table, "username": username, "password": password,
        }, **kwargs)

    def to_mysql(
        self,
        host: str,
        port: int,
        database: str,
        table: str,
        username: str,
        password: str,
        **kwargs,
    ) -> dict:
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
        return self._create_export("MYSQL", {
            "host": host, "port": port, "database": database,
            "table": table, "username": username, "password": password,
        }, **kwargs)

    def to_s3(
        self,
        file_name: Optional[str] = None,
        file_type: str = "csv",
        include_hidden: bool = False,
        **kwargs,
    ) -> dict:
        """Export to S3.

        Args:
            file_name: Output filename (auto-generated if not provided).
            file_type: File format: "csv", "json", etc. (default "csv").
            include_hidden: Include hidden columns (default False).

        Returns:
            Export result dict with download URL.
        """
        if file_name is None:
            import datetime
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"view_{self._view.id}_export_{ts}.{file_type}"

        return self._create_export("S3", {
            "file": file_name, "file_type": file_type,
            "include_hidden": include_hidden, "is_format_set": True, "use_format": True,
        }, **kwargs)

    def to_dataset(
        self,
        dest_dataset_id: int,
        column_mapping: Optional[dict] = None,
        **kwargs,
    ) -> dict:
        """Export to another Mammoth dataset (branch out).

        Args:
            dest_dataset_id: Target dataset ID.
            column_mapping: Column mapping dict (optional).

        Returns:
            Export result dict.
        """
        target = {"dataset_name": str(dest_dataset_id)}
        if column_mapping:
            target["COLUMN_MAPPING"] = column_mapping
        return self._create_export("INTERNAL_DATASET", target, **kwargs)

    def to_csv(self, output_path: Optional[str] = None, timeout: int = 300) -> Path:
        """Download dataview data as CSV file.

        Args:
            output_path: Path for the output file. Auto-generated if not provided.
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

    def to_ftp(self, host: str, path: str, username: str, password: str, port: int = 21, **kwargs) -> dict:
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
        return self._create_export("FTP", {
            "host": host, "port": port, "path": path,
            "username": username, "password": password,
        }, **kwargs)

    def to_sftp(self, host: str, path: str, username: str, password: str, port: int = 22, **kwargs) -> dict:
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
        return self._create_export("SFTP", {
            "host": host, "port": port, "path": path,
            "username": username, "password": password,
        }, **kwargs)

    def to_email(self, recipients: List[str], **kwargs) -> dict:
        """Export via email.

        Args:
            recipients: List of email addresses.

        Returns:
            Export result dict.
        """
        return self._create_export("EMAIL", {"recipients": recipients}, **kwargs)

    def to_bigquery(self, **kwargs) -> dict:
        """Export to Google BigQuery.

        Args:
            **kwargs: BigQuery connection and table configuration.

        Returns:
            Export result dict.
        """
        target = {k: v for k, v in kwargs.items() if k not in
                  ("trigger_type", "additional_properties", "condition",
                   "run_immediately", "validate_only", "end_of_pipeline")}
        return self._create_export("BIGQUERY", target, **kwargs)

    def to_redshift(self, **kwargs) -> dict:
        """Export to Amazon Redshift.

        Args:
            **kwargs: Redshift connection and table configuration.

        Returns:
            Export result dict.
        """
        target = {k: v for k, v in kwargs.items() if k not in
                  ("trigger_type", "additional_properties", "condition",
                   "run_immediately", "validate_only", "end_of_pipeline")}
        return self._create_export("REDSHIFT", target, **kwargs)

    def to_elasticsearch(self, **kwargs) -> dict:
        """Export to Elasticsearch.

        Args:
            **kwargs: Elasticsearch connection and index configuration.

        Returns:
            Export result dict.
        """
        target = {k: v for k, v in kwargs.items() if k not in
                  ("trigger_type", "additional_properties", "condition",
                   "run_immediately", "validate_only", "end_of_pipeline")}
        return self._create_export("ELASTICSEARCH", target, **kwargs)

    def publish_to_db(self, **kwargs) -> dict:
        """Publish dataview to database.

        Args:
            **kwargs: Database connection and table configuration.

        Returns:
            Export result dict.
        """
        target = {k: v for k, v in kwargs.items() if k not in
                  ("trigger_type", "additional_properties", "condition",
                   "run_immediately", "validate_only", "end_of_pipeline")}
        return self._create_export("PUBLISHDB", target, **kwargs)

    def list(self) -> list:
        """List all exports for this dataview.

        Returns:
            List of export dicts.
        """
        result = self._client.exports.list(dataview_id=self._view.id)
        if hasattr(result, 'exports'):
            return result.exports
        return result.get("exports", []) if isinstance(result, dict) else []

    def delete(self, export_id: int) -> dict:
        """Delete an export.

        Args:
            export_id: ID of the export to delete.

        Returns:
            Deletion confirmation dict.
        """
        ws = self._client.workspace_id
        proj = getattr(self._client, 'project_id', None)
        if proj is None:
            raise ValueError("project_id must be set on the client using client.set_project_id()")

        return self._client._request(
            "DELETE",
            f"/workspaces/{ws}/projects/{proj}/datasets/{self._view.dataset_id}"
            f"/dataviews/{self._view.id}/pipeline/exports/{export_id}",
        )
