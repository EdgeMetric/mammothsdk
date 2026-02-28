"""Text operation mixins: text_transform, replace, bulk_replace, split, substring."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.models.pipeline import (
    BulkReplaceMapping,
    SplitColumnSpec,
    SubstringDirection,
    TextCase,
)

if TYPE_CHECKING:
    from mammoth.condition import CompoundCondition, Condition, NotCondition


class TextOpsMixin:
    """Mixin for text transformation operations on a View."""

    def text_transform(
        self,
        columns: list[str],
        case: TextCase | None = None,
        trim: bool = False,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Apply text case change or trim (TEXT_TRANSFORM task).

        Args:
            columns: List of display names to transform.
            case: Case transformation (e.g. ``TextCase.UPPER``). Optional if
                ``trim=True``.
            trim: Whether to trim leading/trailing whitespace (default False).
            condition: Only transform rows matching this condition.

        Returns:
            API response dict.

        Examples::

            view.text_transform(["Name"], case=TextCase.UPPER)
            view.text_transform(["City", "State"], case=TextCase.TITLE)
            view.text_transform(["Notes"], trim=True)
            view.text_transform(
                ["Name"], case=TextCase.LOWER,
                condition=Condition("Region", Operator.EQ, "West"),
            )
        """
        tt_spec: dict[str, Any] = {
            "SOURCE": self._resolve_columns(columns),
            "TRIM": trim,
        }
        if case is not None:
            tt_spec["CASE"] = case

        spec: dict[str, Any] = {"TEXT_TRANSFORM": tt_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def replace_values(
        self,
        columns: list[str],
        find: str,
        replace: str,
        match_case: bool = False,
        match_words: bool = False,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Find and replace values in one or more columns (REPLACE task).

        Args:
            columns: List of display names to search in.
            find: Text to find.
            replace: Replacement text.
            match_case: Case-sensitive matching (default False).
            match_words: Match whole words only (default False).
            condition: Only replace in rows matching this condition.

        Returns:
            API response dict.

        Examples::

            view.replace_values(["City"], find="NYC", replace="New York")
            view.replace_values(
                ["Name"], find="Jr", replace="Junior",
                match_case=True, match_words=True,
            )
        """
        replace_spec: dict[str, Any] = {
            "SOURCE": self._resolve_columns(columns),
            "VALUE_PAIR": [{"SEARCH_VALUE": find, "REPLACE_VALUE": replace}],
            "MATCH_CASE": match_case,
            "MATCH_WORDS": match_words,
        }

        spec: dict[str, Any] = {"REPLACE": replace_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def bulk_replace(
        self,
        columns: list[str],
        mapping: list[BulkReplaceMapping | dict[str, Any]],
        match_case: bool = True,
        match_words: bool = False,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Bulk find-and-replace across one or more columns (REPLACE with MAPPING).

        Each mapping entry maps multiple search values to a single replacement.

        Args:
            columns: Display names of columns to search in.
            mapping: List of :class:`BulkReplaceMapping` objects or dicts
                with matching keys (``search``, ``replace``)::

                    [BulkReplaceMapping(search=["val1", "val2"], replace="replacement")]
                    [{"search": ["val1", "val2"], "replace": "replacement"}]

            match_case: Case-sensitive matching (default True).
            match_words: Whole-word matching (default False).
            condition: Condition to apply.

        Returns:
            API response dict.

        Example::

            view.bulk_replace(
                columns=["Item"],
                mapping=[
                    BulkReplaceMapping(search=["6 inch CAKE", "8 inch CAKE"], replace="CAKE"),
                ],
            )
        """
        resolved_mapping = [BulkReplaceMapping(**m) if isinstance(m, dict) else m for m in mapping]
        mapping_specs = [
            {"SEARCH_VALUE": m.search, "REPLACE_VALUE": m.replace} for m in resolved_mapping
        ]

        replace_spec: dict[str, Any] = {
            "SOURCE": self._resolve_columns(columns),
            "MAPPING": mapping_specs,
            "MATCH_CASE": match_case,
            "MATCH_WORDS": match_words,
        }

        spec: dict[str, Any] = {"REPLACE": replace_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)

    def split_column(
        self,
        column: str,
        delimiter: str,
        new_columns: list[SplitColumnSpec | dict[str, Any]],
    ) -> dict[str, Any]:
        """Split a column into multiple columns by delimiter (SPLIT task).

        Each new column receives the Nth segment after splitting. If a row
        has fewer segments than columns, the extra columns are empty.

        Args:
            column: Display name of column to split.
            delimiter: Delimiter string (e.g. ``" "``, ``","``).
            new_columns: List of :class:`SplitColumnSpec` objects or dicts
                with matching keys (``name``, ``type``)::

                    [SplitColumnSpec("First"), SplitColumnSpec("Last")]
                    [{"name": "First"}, {"name": "Last"}]

        Returns:
            API response dict.

        Example::

            from mammoth import SplitColumnSpec

            view.split_column(
                "Full Name", " ",
                [SplitColumnSpec("First Name"), SplitColumnSpec("Last Name")],
            )
        """
        resolved_cols = [
            SplitColumnSpec(**nc) if isinstance(nc, dict) else nc for nc in new_columns
        ]
        as_columns = [self._build_as_column(nc.name, nc.type) for nc in resolved_cols]

        return self._add_task(
            {
                "SPLIT": {
                    "SOURCE": self._resolve_column(column),
                    "DELIMITER": delimiter,
                    "AS": as_columns,
                },
            }
        )

    def substring(
        self,
        column: str,
        direction: SubstringDirection | None = None,
        num_char: int | None = None,
        char_position: int | None = None,
        regex_pattern: str | None = None,
        regex_invert: bool = False,
        new_column: str | None = None,
        existing_column: str | None = None,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Extract a substring from a column (SUBSTRING task).

        Two modes of extraction:

        **Position-based** — use ``direction`` with either ``num_char`` or
        ``char_position``:

        - ``START`` + ``num_char``: first N characters.
        - ``END`` + ``num_char``: last N characters.
        - ``LEFT`` + ``char_position``: characters before position N.
        - ``RIGHT`` + ``char_position``: characters from position N onward.

        **Regex-based** — use ``regex_pattern`` (and optionally
        ``regex_invert``) instead of direction.

        Args:
            column: Source column display name.
            direction: Extraction direction (see above).
            num_char: Number of characters (use with ``START`` / ``END``).
            char_position: Character position (use with ``LEFT`` / ``RIGHT``).
            regex_pattern: Regex pattern string for extraction (alternative to
                direction). Pass the raw pattern, not a dict.
            regex_invert: If True, return the part that does *not* match the
                regex (default False).
            new_column: Name for a new result column.
            existing_column: Display name of existing column to overwrite.
            condition: Only apply to rows matching this condition.

        Returns:
            API response dict.

        Examples::

            from mammoth import SubstringDirection

            # First 3 characters
            view.substring("Code", direction=SubstringDirection.START,
                           num_char=3, new_column="Prefix")

            # Last 4 characters
            view.substring("Phone", direction=SubstringDirection.END,
                           num_char=4, new_column="Last4")

            # Characters before position 5
            view.substring("SKU", direction=SubstringDirection.LEFT,
                           char_position=5, new_column="Category")

            # Regex extraction
            view.substring("Email", regex_pattern=r"@(.+)",
                           new_column="Domain")
        """
        sub_spec: dict[str, Any] = {
            "SOURCE": self._resolve_column(column),
        }
        if regex_pattern is not None:
            sub_spec["REGEX"] = {"EXPRESSION": regex_pattern, "INVERT": regex_invert}
        if direction is not None:
            sub_spec["DIRECTION"] = direction
        if num_char is not None:
            sub_spec["NUM_CHAR"] = num_char
        if char_position is not None:
            sub_spec["CHAR_POSITION"] = char_position

        if new_column:
            sub_spec["AS"] = self._build_as_column(new_column, "TEXT")
        elif existing_column:
            sub_spec["DESTINATION"] = self._resolve_column(existing_column)

        spec: dict[str, Any] = {"SUBSTRING": sub_spec}
        if condition:
            spec["CONDITION"] = self._build_condition(condition)

        return self._add_task(spec)
