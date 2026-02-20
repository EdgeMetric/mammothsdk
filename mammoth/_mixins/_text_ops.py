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
            case: Case transformation (optional).
            trim: Whether to trim whitespace (default False).
            condition: Condition to apply.

        Returns:
            API response dict.
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
        mapping: list[BulkReplaceMapping],
        match_case: bool = True,
        match_words: bool = False,
        condition: Condition | CompoundCondition | NotCondition | None = None,
    ) -> dict[str, Any]:
        """Bulk find-and-replace across one or more columns (REPLACE with MAPPING).

        Each mapping entry maps multiple search values to a single replacement.

        Args:
            columns: Display names of columns to search in.
            mapping: List of BulkReplaceMapping objects::

                [BulkReplaceMapping(search=["val1", "val2"], replace="replacement")]

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
        mapping_specs = [{"SEARCH_VALUE": m.search, "REPLACE_VALUE": m.replace} for m in mapping]

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
        new_columns: list[SplitColumnSpec],
    ) -> dict[str, Any]:
        """Split a column by delimiter (SPLIT task).

        Args:
            column: Display name of column to split.
            delimiter: Delimiter string.
            new_columns: List of SplitColumnSpec objects::

                [SplitColumnSpec("First"), SplitColumnSpec("Last")]

        Returns:
            API response dict.
        """
        as_columns = [self._build_as_column(nc.name, nc.type) for nc in new_columns]

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
        """Extract text from a column (SUBSTRING task).

        Args:
            column: Source column display name.
            direction: Extraction direction.
                START/END with num_char (first/last N chars).
                LEFT/RIGHT with char_position (chars before/after position).
            num_char: Number of characters to extract (use with START/END).
            char_position: Character position (use with LEFT/RIGHT).
            regex_pattern: Regex pattern for extraction (alternative to direction).
            regex_invert: Invert regex match (default False).
            new_column: Name for result column.
            existing_column: Existing column to overwrite.
            condition: Condition to apply.

        Returns:
            API response dict.
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
