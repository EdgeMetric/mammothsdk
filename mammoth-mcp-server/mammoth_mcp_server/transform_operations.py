"""Pydantic v2 input models for workflow_agent tools.

One model per tool. Tool names are module-level constants so the ToolSpec,
the handler dispatch, and tests all reference the same string.

The column-type enum is reused from mm-pysdk (``mammoth.models.pipeline``) so
the agent's contract and the backend builders share one source of truth — the
JSON schema then advertises exactly the backend-valid types (TEXT/NUMERIC/DATE).
"""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from mammoth.models.exports import HandlerType
from mammoth.models.pipeline import (
    AggregateFunction,
    ColumnType,
    DateComponent,
    DateDiffUnit,
    FillDirection,
    JoinType,
    JsonType,
    Operator,
    SmallLargeFunction,
    SortDirection,
    SubstringDirection,
    TextCase,
    WindowFunction,
    WindowRange,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

GET_COLUMNS_TOOL_NAME = "get_columns"
GET_COLUMN_PROFILE_TOOL_NAME = "get_column_profile"
GET_DATA_QUALITY_TOOL_NAME = "get_data_quality"
GET_SAMPLE_ROWS_TOOL_NAME = "get_sample_rows"
GET_PIPELINE_TOOL_NAME = "get_pipeline"
ADD_STEP_TOOL_NAME = "add_step"
RUN_PIPELINE_TOOL_NAME = "run_pipeline"
DISCARD_DRAFT_TOOL_NAME = "discard_draft"
EXPORT_TO_TARGET_TOOL_NAME = "export_to_target"
GENERATE_DASHBOARD_TOOL_NAME = "generate_dashboard"

# Default/maximum sample-row page size. The default mirrors the backend's
# ROW_CONSIDERED_FOR_LLM heuristic (a handful of rows is enough to read intent);
# the cap keeps the heavy DuckDB read and the LLM context bounded.
_SAMPLE_ROWS_DEFAULT = 20
_SAMPLE_ROWS_MAX = 200

# Shared across every op that can target an existing column instead of a new one
# (overwrite-in-place). One source of truth so the contract reads identically.
_OVERWRITE_EXISTING_COLUMN_DESCRIPTION = (
    "Display name of an existing column to overwrite. " "Provide this OR new_column (exactly one)."
)


class GetColumnsInput(BaseModel):
    """Input for ``get_columns`` — read a View's column metadata.

    ``view_id`` is the numeric id of the View (dataview) to inspect; the
    handler returns its display↔internal name map and column types.
    """

    model_config = ConfigDict(extra="forbid")

    view_id: int = Field(ge=1, description="Numeric id of the View to inspect.")


class GetColumnProfileInput(BaseModel):
    """Input for ``get_column_profile`` — read a View's stored column stats.

    ``view_id`` is the numeric id of the View to profile; the handler returns
    per-column row counts, distinct counts, and uniqueness from stored
    statistics (a cheap read — no full-table scan).
    """

    model_config = ConfigDict(extra="forbid")

    view_id: int = Field(ge=1, description="Numeric id of the View to profile.")


class GetDataQualityInput(BaseModel):
    """Input for ``get_data_quality`` — read a View's stored quality report.

    ``view_id`` is the numeric id of the View. The handler reads the report the
    Data Quality panel already generated; it never generates one, so the call is
    a single stored-row read regardless of how large the View is.
    """

    model_config = ConfigDict(extra="forbid")

    view_id: int = Field(ge=1, description="Numeric id of the View to report on.")


class GetPipelineInput(BaseModel):
    """Input for ``get_pipeline`` — read a View's existing transform steps.

    ``view_id`` is the numeric id of the View whose pipeline to enumerate; the
    handler returns its ordered steps (op type, sequence, status, label).
    """

    model_config = ConfigDict(extra="forbid")

    view_id: int = Field(ge=1, description="Numeric id of the View whose pipeline to read.")


class GetSampleRowsInput(BaseModel):
    """Input for ``get_sample_rows`` — read a small page of a View's data.

    ``view_id`` selects the View; ``limit`` caps how many rows are returned
    (display-formatted). This runs a real query, so keep ``limit`` small —
    a handful of rows is enough to read example values and confirm intent.
    """

    model_config = ConfigDict(extra="forbid")

    view_id: int = Field(ge=1, description="Numeric id of the View to sample.")
    limit: int = Field(
        default=_SAMPLE_ROWS_DEFAULT,
        ge=1,
        le=_SAMPLE_ROWS_MAX,
        description="Maximum number of rows to return (display-formatted).",
    )


class ConvertColumnSpec(BaseModel):
    """One column type conversion within an ``add_step`` convert step."""

    model_config = ConfigDict(extra="forbid")

    column: str = Field(
        min_length=1,
        description="Display name (or internal name) of the column to convert.",
    )
    to_type: ColumnType = Field(
        description="Target column type. Only TEXT, NUMERIC, or DATE are valid."
    )
    date_format: str | None = Field(
        default=None,
        description=(
            "Source date format as a Python strptime template, required only "
            "when parsing text into DATE — e.g. '%Y-%m-%d' for 2024-03-11, "
            "'%m/%d/%Y' for 03/11/2024. Use strptime codes (%Y %m %d %H %M %S), "
            "NOT letter patterns like YYYY-MM-DD. Omit for TEXT/NUMERIC."
        ),
    )


class ConvertOperation(BaseModel):
    """The ``convert`` operation: change one or more columns' types in place."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["convert"] = "convert"
    conversions: list[ConvertColumnSpec] = Field(
        min_length=1,
        description="One or more column type conversions applied in a single step.",
    )


class TextTransformOperation(BaseModel):
    """The ``text_transform`` operation: change case and/or trim whitespace.

    At least one of ``case``/``trim`` must be set (a no-op transform is rejected).
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["text_transform"] = "text_transform"
    columns: list[str] = Field(
        min_length=1,
        description="Display (or internal) names of the columns to transform.",
    )
    case: TextCase | None = Field(
        default=None,
        description="Case conversion: UPPER, LOWER, or TITLE. Omit to leave case as-is.",
    )
    trim: bool = Field(
        default=False, description="Strip leading/trailing whitespace from each value."
    )

    @model_validator(mode="after")
    def _require_an_effect(self) -> TextTransformOperation:
        if self.case is None and not self.trim:
            raise ValueError("text_transform requires `case` and/or `trim` to have an effect.")
        return self


class DiscardDuplicatesOperation(BaseModel):
    """The ``discard_duplicates`` operation: drop duplicate rows (dedupe)."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["discard_duplicates"] = "discard_duplicates"
    ignore_columns: list[str] = Field(
        default_factory=list,
        description=(
            "Columns to EXCLUDE when comparing rows for duplicates. Empty (default) "
            "compares all columns — two rows are duplicates only if every column matches."
        ),
    )


class ReplaceOperation(BaseModel):
    """The ``replace`` operation: find-and-replace text within columns."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["replace"] = "replace"
    columns: list[str] = Field(
        min_length=1,
        description="Display (or internal) names of the columns to search.",
    )
    find: str = Field(min_length=1, description="The substring to search for.")
    replace: str = Field(description="The replacement text (empty string deletes the match).")
    match_case: bool = Field(default=False, description="Case-sensitive search when True.")
    match_words: bool = Field(default=False, description="Match whole words only when True.")


class FillNullOperation(BaseModel):
    """The ``fill_null`` operation: write a constant into empty cells of a column."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["fill_null"] = "fill_null"
    column: str = Field(
        min_length=1, description="Display (or internal) name of the column to fill."
    )
    value: str | int | float = Field(
        description="The constant written into every empty cell of the column."
    )


class MathOperation(BaseModel):
    """The ``math`` operation: compute a new column from an arithmetic expression."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["math"] = "math"
    expression: str = Field(
        min_length=1,
        description=(
            "Arithmetic expression over column display names, e.g. "
            "'Price * Quantity' or '(Sales + Tax) * 1.1'. Supports + - * / , "
            "parentheses, and numeric literals."
        ),
    )
    new_column: str = Field(
        min_length=1, description="Name of the new column holding the computed result."
    )
    column_type: ColumnType = Field(
        default=ColumnType.NUMERIC,
        description="Type of the computed column (usually NUMERIC).",
    )


class CombineOperation(BaseModel):
    """The ``combine`` operation: concatenate columns into a new column."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["combine"] = "combine"
    columns: list[str] = Field(
        min_length=2,
        description="Display names of the columns to concatenate, in order.",
    )
    new_column: str = Field(
        min_length=1, description="Name of the new column holding the joined text."
    )
    separator: str = Field(
        default=" ", description="Text inserted between each source column's value."
    )
    column_type: ColumnType = Field(
        default=ColumnType.TEXT, description="Type of the new column (usually TEXT)."
    )


class AddColumnOperation(BaseModel):
    """The ``add_column`` operation: append a new empty column."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["add_column"] = "add_column"
    name: str = Field(min_length=1, description="Display name of the new column.")
    column_type: ColumnType = Field(default=ColumnType.TEXT, description="Type of the new column.")


class CopyColumnSpec(BaseModel):
    """One column duplication within a ``copy`` operation."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, description="Display name of the column to duplicate.")
    new_name: str | None = Field(
        default=None,
        description="Name for the copy; defaults to '<source> Copy' when omitted.",
    )
    column_type: ColumnType = Field(
        default=ColumnType.TEXT, description="Type of the copied column."
    )
    condition: ConditionInput | None = Field(
        default=None,
        description="When set, only rows matching this condition are copied; other "
        "rows get an empty cell in the new column.",
    )


class CopyOperation(BaseModel):
    """The ``copy`` operation: duplicate one or more columns."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["copy"] = "copy"
    copies: list[CopyColumnSpec] = Field(
        min_length=1, description="One or more column copies to create."
    )


# --- Conditions: a row predicate the agent can express in natural-language terms
# --- and which row-scoped operations (select/set/copy) forward to the pysdk
# --- ``build_condition`` pure builder. A condition is a discriminated tree:
# --- a leaf comparison, an AND/OR group, or a negation — mirroring the ``op``
# --- discriminator pattern so malformed trees are rejected at validation time.

# Comparison value shape is operator-dependent. These sets drive one validator
# (no per-operator branching): value-free operators take no value, list/range
# operators take a list, everything else takes a single scalar.
_NULL_OPERATORS = frozenset(
    {
        Operator.IS_EMPTY,
        Operator.IS_NOT_EMPTY,
        Operator.IS_MAXVAL,
        Operator.IS_NOT_MAXVAL,
        Operator.IS_MINVAL,
        Operator.IS_NOT_MINVAL,
    }
)
_LIST_OPERATORS = frozenset({Operator.IN_LIST, Operator.NOT_IN_LIST})
_RANGE_OPERATORS = frozenset({Operator.IN_RANGE})

# A comparison value: a scalar for most operators, a list for IN_LIST/IN_RANGE,
# or absent for value-free operators (IS_EMPTY/IS_MAXVAL/…). Mammoth column
# types are TEXT/NUMERIC/DATE, so there is no boolean value.
ConditionValue = str | int | float | list[str | int | float] | None


class ComparisonCondition(BaseModel):
    """A single ``column operator value`` predicate, e.g. ``Sales >= 1000``.

    The operator's value shape is validated: value-free operators (IS_EMPTY,
    IS_MAXVAL, …) take no ``value``; IN_LIST/NOT_IN_LIST take a non-empty list;
    IN_RANGE takes exactly two bounds; all others take a single scalar.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["compare"] = "compare"
    column: str = Field(min_length=1, description="Display name of the column to test.")
    operator: Operator = Field(
        description="Comparison operator — e.g. EQ, NE, GT, LT, GTE, LTE, CONTAINS, "
        "ICONTAINS, STARTS_WITH, IN_LIST, IN_RANGE, IS_EMPTY.",
    )
    value: ConditionValue = Field(
        default=None,
        description="Value to compare against: a single scalar for most operators, "
        "a list for IN_LIST/NOT_IN_LIST, exactly two bounds for IN_RANGE, and "
        "omitted for value-free operators (IS_EMPTY/IS_NOT_EMPTY/IS_MAXVAL/…).",
    )
    case_sensitive: bool | None = Field(
        default=None,
        description="Text matching case: True=case-sensitive, False=case-insensitive, "
        "omit to use the backend default.",
    )

    @model_validator(mode="after")
    def _check_value_shape(self) -> ComparisonCondition:
        if self.operator in _NULL_OPERATORS:
            if self.value is not None:
                raise ValueError(f"operator {self.operator.value} takes no value")
        elif self.operator in _RANGE_OPERATORS:
            if not isinstance(self.value, list) or len(self.value) != 2:
                raise ValueError("IN_RANGE requires a list of exactly two bounds")
        elif self.operator in _LIST_OPERATORS:
            if not isinstance(self.value, list) or not self.value:
                raise ValueError(f"operator {self.operator.value} requires a non-empty list value")
        elif self.value is None or isinstance(self.value, list):
            raise ValueError(f"operator {self.operator.value} requires a single scalar value")
        return self


class GroupCondition(BaseModel):
    """An AND/OR combination of two or more nested conditions."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["group"] = "group"
    logic: Literal["and", "or"] = Field(
        description="Combine the nested conditions with `and` (all must hold) or "
        "`or` (any may hold).",
    )
    conditions: list[ConditionInput] = Field(
        min_length=2, description="The two or more conditions to combine."
    )


class NegateCondition(BaseModel):
    """The logical NOT of a nested condition."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["not"] = "not"
    condition: ConditionInput = Field(description="The condition to negate.")


# Discriminated condition tree: a leaf comparison, an AND/OR group, or a
# negation. The recursive members reference this alias by forward name, resolved
# by the ``model_rebuild()`` calls below (standard Pydantic-v2 self-reference).
ConditionInput = Annotated[
    ComparisonCondition | GroupCondition | NegateCondition,
    Field(discriminator="kind"),
]

GroupCondition.model_rebuild()
NegateCondition.model_rebuild()
# CopyColumnSpec is declared above this alias (a Tier-A model), so its optional
# condition field is a forward reference resolved here.
CopyColumnSpec.model_rebuild()


class SelectRowsOperation(BaseModel):
    """The ``select`` operation: keep or drop rows by a condition (row filter)."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["select"] = "select"
    condition: ConditionInput = Field(
        description="The row filter — each row is tested against this condition."
    )
    keep_matching: bool = Field(
        default=True,
        description="True keeps the rows that match the condition; False drops them.",
    )


class SetValueSpec(BaseModel):
    """One value within a ``set`` operation, optionally scoped to a condition.

    With a ``condition``, only rows matching it receive this value (the backend
    applies the values in order). Without one, the value applies to every row
    (the last unconditional value wins — use it as the default/else branch).
    """

    model_config = ConfigDict(extra="forbid")

    value: str | int | float = Field(description="The literal value to write.")
    condition: ConditionInput | None = Field(
        default=None,
        description="When set, only rows matching this condition receive this value.",
    )


class SetValuesOperation(BaseModel):
    """The ``set`` operation: write fixed values into a column, by condition.

    Targets exactly one of a brand-new column (``new_column``, created with
    ``column_type``) or an existing column (``existing_column``). Each value may
    carry its own ``condition`` (a per-row rule, e.g. "High" where Sales ≥ 10000,
    else "Low"); an optional top-level ``condition`` scopes the whole step.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["set"] = "set"
    values: list[SetValueSpec] = Field(
        min_length=1,
        description="The values to write, applied in order; earlier conditional "
        "values take precedence.",
    )
    new_column: str | None = Field(
        default=None,
        description="Display name of a new column to create and fill. Provide this "
        "OR existing_column (exactly one).",
    )
    existing_column: str | None = Field(
        default=None,
        description="Display name of an existing column to overwrite. Provide this "
        "OR new_column (exactly one).",
    )
    column_type: ColumnType = Field(
        default=ColumnType.TEXT,
        description="Type of the new column (used only with new_column).",
    )
    condition: ConditionInput | None = Field(
        default=None,
        description="Optional condition scoping the whole step to matching rows.",
    )

    @model_validator(mode="after")
    def _exactly_one_target(self) -> SetValuesOperation:
        if bool(self.new_column) == bool(self.existing_column):
            raise ValueError("set requires exactly one of new_column or existing_column.")
        return self


# --- Multi-view operations (JOIN / LOOKUP). Unlike every operation above, these
# --- reference a SECOND ("foreign") View by id and pull columns from it, so the
# --- handler resolves a second column context and gates it behind a read check.
# --- All column references are display names: left/source on the target View,
# --- right/key/value on the foreign View.
class JoinKeyInput(BaseModel):
    """One key pair the join matches on (``left`` on the target, ``right`` on the
    foreign View). Both are display names; matched key columns must share a type."""

    model_config = ConfigDict(extra="forbid")

    left: str = Field(min_length=1, description="Target-View column to match on.")
    right: str = Field(min_length=1, description="Foreign-View column to match on.")


class JoinSelectInput(BaseModel):
    """One foreign-View column to bring into the target View, optionally renamed."""

    model_config = ConfigDict(extra="forbid")

    column: str = Field(min_length=1, description="Foreign-View column to bring in.")
    alias: str | None = Field(
        default=None,
        description="Optional display name for the brought-in column (defaults to "
        "the source column's name).",
    )


class JoinOperation(BaseModel):
    """The ``join`` operation: merge a foreign View into the target by key columns.

    Reads the foreign View (``foreign_view_id``) and joins it onto the current
    View on the ``on`` key pairs. ``select`` lists the foreign columns to bring in
    (required — name them explicitly); ``column_prefix`` disambiguates brought-in
    names.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["join"] = "join"
    foreign_view_id: int = Field(ge=1, description="Numeric id of the foreign View to join in.")
    join_type: JoinType = Field(
        default=JoinType.INNER,
        description="INNER (only matching rows), LEFT (all target rows), RIGHT (all "
        "foreign rows), or OUTER (all rows from both).",
    )
    on: list[JoinKeyInput] = Field(min_length=1, description="The key pairs to match rows on.")
    select: list[JoinSelectInput] = Field(
        min_length=1,
        description="The foreign columns to bring into this View (list them "
        "explicitly — there is no implicit 'all').",
    )
    column_prefix: str | None = Field(
        default=None,
        description="Optional prefix applied to brought-in foreign column names.",
    )


class LookupOperation(BaseModel):
    """The ``lookup`` operation: enrich the target with one value from a foreign View.

    For each target row, matches ``source`` (target column) against the foreign
    View's ``key`` column and writes that row's ``value`` column into either a new
    column (``new_column``) or an existing one (``existing_column``) — exactly one.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["lookup"] = "lookup"
    foreign_view_id: int = Field(
        ge=1, description="Numeric id of the foreign View to look values up in."
    )
    source: str = Field(
        min_length=1, description="Target-View column matched against the foreign key."
    )
    key: str = Field(min_length=1, description="Foreign-View column to match the source against.")
    value: str = Field(min_length=1, description="Foreign-View column whose value is brought in.")
    new_column: str | None = Field(
        default=None,
        description="Display name of a new column to write the looked-up value into. "
        "Provide this OR existing_column (exactly one).",
    )
    existing_column: str | None = Field(
        default=None,
        description="Display name of an existing column to overwrite. Provide this "
        "OR new_column (exactly one).",
    )

    @model_validator(mode="after")
    def _exactly_one_target(self) -> LookupOperation:
        if bool(self.new_column) == bool(self.existing_column):
            raise ValueError("lookup requires exactly one of new_column or existing_column.")
        return self


class GenAiOperation(BaseModel):
    """The ``gen_ai`` operation: generate a new column with generative AI.

    The AI reads up to 20 ``context_columns`` and writes ``new_column`` per the
    ``prompt`` (e.g. "classify the review text as Positive, Negative, or
    Neutral"). Use it for enrichment/derivation no structured op can express —
    free-text classification, extraction, summarization. For a SQL-expressible
    transform prefer ``sql``; for plain arithmetic/text rules prefer the
    dedicated ops.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["gen_ai"] = "gen_ai"
    prompt: str = Field(
        min_length=1,
        description="Plain-English instruction describing the new column's values.",
    )
    context_columns: list[str] = Field(
        min_length=1,
        max_length=20,
        description="Display names of up to 20 columns the AI reads as input context.",
    )
    new_column: str = Field(
        default="AI Result",
        min_length=1,
        description="Display name of the generated column.",
    )


class SqlOperation(BaseModel):
    """The ``sql`` operation: transform via an AI-generated, validated SQL query.

    The universal escape hatch — use it when no structured operation can express
    the transformation faithfully (e.g. normalizing a column that mixes several
    date formats into one DATE, multi-column derivations, or conditional logic a
    single op can't represent). Describe the goal in plain English (``intent``);
    Mammoth's AI writes and self-validates the SQL against the View's columns and
    sample values. NEVER hand-write SQL — state the intent. Prefer a dedicated op
    when one fits exactly, and reach for ``sql`` rather than applying a lossy op.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["sql"] = "sql"
    intent: str = Field(
        min_length=1,
        description="Plain-English description of the transformation, e.g. 'parse "
        "the order date column — values appear as 2024-01-15, 15-Jan-2024, and "
        "1/15/2024 — into a single DATE column'.",
    )


# ---------------------------------------------------------------------------
# Tier 2 operations
# ---------------------------------------------------------------------------


class DeleteOperation(BaseModel):
    """The ``delete`` operation: permanently remove one or more columns."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["delete"] = "delete"
    columns: list[str] = Field(
        min_length=1,
        description="Display (or internal) names of the columns to delete.",
    )


class OrderBySpec(BaseModel):
    """One sort criterion for operations that accept an ``order_by`` list."""

    model_config = ConfigDict(extra="forbid")

    column: str = Field(min_length=1, description="Display name of the column to sort on.")
    direction: SortDirection = Field(
        default=SortDirection.ASC,
        description="Sort direction: ASC (smallest first) or DESC (largest first).",
    )


class LimitOperation(BaseModel):
    """The ``limit`` operation: keep only the top (or bottom) N rows.

    Without ``order_by`` the backend keeps whichever N rows happen to be stored
    first/last; supply ``order_by`` to make the selection deterministic.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["limit"] = "limit"
    n: int = Field(ge=1, description="Number of rows to keep.")
    bottom: bool = Field(
        default=False,
        description="Keep the last N rows when True; keep the first N when False (default).",
    )
    order_by: list[OrderBySpec] = Field(
        default_factory=list,
        description="Optional sort to apply before limiting — omit for storage order.",
    )


class SubstringOperation(BaseModel):
    """The ``substring`` operation: extract a portion of a text column.

    Exactly one extraction mode must be specified:
    - ``regex_pattern``: extract via a regular-expression match.
    - ``direction`` + ``num_char``: take N characters from the START or END.
    - ``direction`` + ``char_position``: take characters LEFT or RIGHT of a position.

    Result goes into a new column (``new_column``) or overwrites an existing one
    (``existing_column``) — supply exactly one.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["substring"] = "substring"
    column: str = Field(
        min_length=1,
        description="Display (or internal) name of the source text column.",
    )
    new_column: str | None = Field(
        default=None,
        description="Name of the new column to create with the extracted text. "
        "Provide this OR existing_column (exactly one).",
    )
    existing_column: str | None = Field(
        default=None,
        description=_OVERWRITE_EXISTING_COLUMN_DESCRIPTION,
    )
    direction: SubstringDirection | None = Field(
        default=None,
        description=(
            "Extraction direction: START/END (N chars from start/end) or "
            "LEFT/RIGHT (chars before/after a position). Required with "
            "num_char or char_position."
        ),
    )
    num_char: int | None = Field(
        default=None,
        ge=1,
        description="Number of characters to extract from the START or END.",
    )
    char_position: int | None = Field(
        default=None,
        ge=1,
        description="Character position used with LEFT (before) or RIGHT (after).",
    )
    regex_pattern: str | None = Field(
        default=None,
        min_length=1,
        description="Regular-expression pattern — matched text becomes the output.",
    )
    regex_invert: bool = Field(
        default=False,
        description="When True, keep the part of the text that does NOT match the regex.",
    )
    condition: ConditionInput | None = Field(
        default=None,
        description="Optional condition scoping the extraction to matching rows.",
    )

    @model_validator(mode="after")
    def _exactly_one_target(self) -> SubstringOperation:
        if bool(self.new_column) == bool(self.existing_column):
            raise ValueError("substring requires exactly one of new_column or existing_column.")
        return self


class SplitColumnNewCol(BaseModel):
    """One new column produced by a ``split`` operation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, description="Display name of the new split column.")
    column_type: ColumnType = Field(
        default=ColumnType.TEXT,
        description="Type of the new column (usually TEXT).",
    )


class SplitOperation(BaseModel):
    """The ``split`` operation: split a text column on a delimiter into new columns.

    Each item in ``new_columns`` receives one segment; surplus segments are
    discarded and missing segments get an empty cell.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["split"] = "split"
    column: str = Field(
        min_length=1, description="Display (or internal) name of the column to split."
    )
    delimiter: str = Field(
        min_length=1,
        description="The separator string to split on (e.g. ' ', ',', ' - ').",
    )
    new_columns: list[SplitColumnNewCol] = Field(
        min_length=2,
        description="The new columns to produce, in split-segment order (at least 2).",
    )


class BulkReplaceMappingInput(BaseModel):
    """One mapping entry for the ``bulk_replace`` operation.

    ``search`` is a list so many source spellings collapse to one canonical value.
    """

    model_config = ConfigDict(extra="forbid")

    search: list[str] = Field(
        min_length=1, description="List of source values to replace (non-empty)."
    )
    replace: str = Field(description="The single canonical replacement string.")


class BulkReplaceOperation(BaseModel):
    """The ``bulk_replace`` operation: apply many find→replace pairs in one step.

    Unlike ``replace`` (a single pair), ``bulk_replace`` is for standardising a
    categorical column — e.g. mapping many product-name variants to one canonical
    form. The entire mapping is applied atomically.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["bulk_replace"] = "bulk_replace"
    columns: list[str] = Field(
        min_length=1,
        description="Display (or internal) names of the columns to apply the mapping to.",
    )
    mapping: list[BulkReplaceMappingInput] = Field(
        min_length=1,
        description="The replace mapping: each entry lists the source spellings and "
        "the canonical replacement.",
    )
    match_case: bool = Field(
        default=True,
        description="Case-sensitive matching when True (default). Set False for case-insensitive.",
    )
    match_words: bool = Field(
        default=False,
        description="Match whole words only when True.",
    )
    condition: ConditionInput | None = Field(
        default=None,
        description="Optional condition scoping the operation to matching rows.",
    )


class FillOperation(BaseModel):
    """The ``fill`` operation: propagate non-null values to fill adjacent nulls.

    Direction FIRST_VALUE propagates downward (next non-null fills following
    nulls); LAST_VALUE propagates upward. Optionally scoped by ``partition_by``
    (fill within groups) and ordered by ``order_by`` for deterministic direction.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["fill"] = "fill"
    column: str = Field(
        min_length=1, description="Display (or internal) name of the column to fill."
    )
    direction: FillDirection = Field(
        description="FIRST_VALUE propagates downward; LAST_VALUE propagates upward.",
    )
    partition_by: str | None = Field(
        default=None,
        description="Optional column to group by before filling (fills within each group).",
    )
    order_by: list[OrderBySpec] = Field(
        default_factory=list,
        description="Optional sort defining the fill direction within each partition.",
    )


class ExtractDateOperation(BaseModel):
    """The ``extract_date`` operation: extract one component from a DATE column.

    Supported components: year, month, day, hour, minute, second, week, quarter,
    day_of_week, day_of_year, weekday_text, month_text, year_month, year_week,
    year_quarter, month_day, hour_minute, hour_minute_second, year_month_day,
    year_month_day_as_date, month_day_year_hour_minute_second, date_only.

    Result goes into a new column (``new_column``) or overwrites an existing one
    (``existing_column``) — supply exactly one.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["extract_date"] = "extract_date"
    column: str = Field(
        min_length=1,
        description="Display (or internal) name of the source DATE column.",
    )
    component: DateComponent = Field(
        description="The date component to extract (e.g. DateComponent.YEAR for year).",
    )
    new_column: str | None = Field(
        default=None,
        description="Name of the new column to create. "
        "Provide this OR existing_column (exactly one).",
    )
    existing_column: str | None = Field(
        default=None,
        description=_OVERWRITE_EXISTING_COLUMN_DESCRIPTION,
    )

    @model_validator(mode="after")
    def _exactly_one_target(self) -> ExtractDateOperation:
        if bool(self.new_column) == bool(self.existing_column):
            raise ValueError("extract_date requires exactly one of new_column or existing_column.")
        return self


class DateDiffOperation(BaseModel):
    """The ``date_diff`` operation: compute the signed difference between two dates.

    Result is a NUMERIC column counting ``unit`` periods from ``start`` to ``end``
    (positive when end is after start). Targets exactly one of ``new_column``
    (created) or ``existing_column`` (overwritten).
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["date_diff"] = "date_diff"
    start: str = Field(
        min_length=1,
        description="Display name of the earlier (subtrahend) date column.",
    )
    end: str = Field(min_length=1, description="Display name of the later (minuend) date column.")
    unit: DateDiffUnit = Field(
        description="Unit to express the difference in: YEAR, MONTH, DAY, HOUR, MINUTE, "
        "SECOND, WEEK, or QUARTER.",
    )
    new_column: str | None = Field(
        default=None,
        description="Name of the new NUMERIC column to create. "
        "Provide this OR existing_column (exactly one).",
    )
    existing_column: str | None = Field(
        default=None,
        description=_OVERWRITE_EXISTING_COLUMN_DESCRIPTION,
    )

    @model_validator(mode="after")
    def _exactly_one_target(self) -> DateDiffOperation:
        if bool(self.new_column) == bool(self.existing_column):
            raise ValueError("date_diff requires exactly one of new_column or existing_column.")
        return self


class DateDeltaInput(BaseModel):
    """The amount to add (or subtract, using negative values) in each unit.

    Unspecified units default to zero. At least one non-zero unit is required.
    """

    model_config = ConfigDict(extra="forbid")

    years: int = Field(default=0, description="Number of years to add (negative to subtract).")
    months: int = Field(default=0, description="Number of months to add.")
    weeks: int = Field(default=0, description="Number of weeks to add.")
    days: int = Field(default=0, description="Number of days to add.")
    hours: int = Field(default=0, description="Number of hours to add.")
    minutes: int = Field(default=0, description="Number of minutes to add.")
    seconds: int = Field(default=0, description="Number of seconds to add.")

    @model_validator(mode="after")
    def _at_least_one_unit(self) -> DateDeltaInput:
        if not any(
            [
                self.years,
                self.months,
                self.weeks,
                self.days,
                self.hours,
                self.minutes,
                self.seconds,
            ]
        ):
            raise ValueError("increment_date delta must have at least one non-zero unit.")
        return self


class IncrementDateOperation(BaseModel):
    """The ``increment_date`` operation: shift a date column by a fixed delta.

    Adds the ``delta`` to each value of ``column``. Negative values subtract.
    Result goes into a new DATE column (``new_column``) or overwrites an existing
    one (``existing_column``) — supply exactly one. An optional ``condition``
    scopes the shift to matching rows.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["increment_date"] = "increment_date"
    column: str = Field(
        min_length=1,
        description="Display (or internal) name of the DATE column to shift.",
    )
    delta: DateDeltaInput = Field(
        description="The amount to add in each calendar unit (years/months/weeks/days/…)."
    )
    new_column: str | None = Field(
        default=None,
        description="Name of the new DATE column to create. "
        "Provide this OR existing_column (exactly one).",
    )
    existing_column: str | None = Field(
        default=None,
        description=_OVERWRITE_EXISTING_COLUMN_DESCRIPTION,
    )
    condition: ConditionInput | None = Field(
        default=None,
        description="Optional condition scoping the shift to matching rows.",
    )

    @model_validator(mode="after")
    def _exactly_one_target(self) -> IncrementDateOperation:
        if bool(self.new_column) == bool(self.existing_column):
            raise ValueError(
                "increment_date requires exactly one of new_column or existing_column."
            )
        return self


class SmallLargeOperation(BaseModel):
    """The ``small_large`` operation: pick the Nth smallest/largest value per row.

    Across the given value sources — the ``columns`` plus any numeric
    ``constants`` — writes each row's ``index``-th smallest (function SMALL) or
    largest (function LARGE) value. ``index`` is 1-based: 1 is the most extreme.
    Result goes into a new column (``new_column``) or overwrites an existing one
    (``existing_column``) — supply exactly one.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["small_large"] = "small_large"
    function: SmallLargeFunction = Field(
        description="SMALL = the Nth smallest value, LARGE = the Nth largest value.",
    )
    columns: list[str] = Field(
        min_length=1,
        description="Display names of the value-source columns to rank (at least one).",
    )
    index: int = Field(
        default=1,
        ge=1,
        description="1-based rank to pick across the value sources (1 = most extreme).",
    )
    constants: list[float] = Field(
        default_factory=list,
        description="Optional numeric constants to include among the value sources "
        "(e.g. a floor of 0 so the result never goes below zero).",
    )
    new_column: str | None = Field(
        default=None,
        description="Name of the new NUMERIC column to create. "
        "Provide this OR existing_column (exactly one).",
    )
    existing_column: str | None = Field(
        default=None,
        description=_OVERWRITE_EXISTING_COLUMN_DESCRIPTION,
    )

    @model_validator(mode="after")
    def _exactly_one_target(self) -> SmallLargeOperation:
        if bool(self.new_column) == bool(self.existing_column):
            raise ValueError("small_large requires exactly one of new_column or existing_column.")
        return self


class JsonExtractionInput(BaseModel):
    """One key extraction within a ``json_extract`` operation."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, description="The JSON key (field name) to extract.")
    as_name: str | None = Field(
        default=None,
        description="Display name for the extracted column; defaults to the key name.",
    )
    column_type: ColumnType = Field(
        default=ColumnType.TEXT,
        description="Type of the extracted column: TEXT or NUMERIC.",
    )


class JsonExtractOperation(BaseModel):
    """The ``json_extract`` operation: expand a JSON column into new columns (or rows).

    For a JSON-object column (``json_type=OBJECT``), each key becomes a new column.
    For a JSON-array column (``json_type=LIST``), each element becomes a new row.
    Use ``extractions`` to specify which keys to extract and their output names;
    omit it (use ``keys``) for a quick unnamed extraction.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["json_extract"] = "json_extract"
    column: str = Field(
        min_length=1,
        description="Display (or internal) name of the JSON source column.",
    )
    json_type: JsonType = Field(
        default=JsonType.OBJECT,
        description="OBJECT to expand keys into columns; LIST to expand items into rows.",
    )
    extractions: list[JsonExtractionInput] | None = Field(
        default=None,
        description="Explicit key-to-column mapping. Use this for named, typed output. "
        "Provide this OR keys (not both; omit both to let the backend infer).",
    )
    keys: list[str] | None = Field(
        default=None,
        description="Simple list of JSON keys to extract (all become TEXT columns). "
        "Provide this OR extractions.",
    )
    keep_source: bool = Field(
        default=False,
        description="Keep the original JSON source column after extraction.",
    )

    @model_validator(mode="after")
    def _not_both_keys_and_extractions(self) -> JsonExtractOperation:
        if self.extractions is not None and self.keys is not None:
            raise ValueError("json_extract accepts extractions OR keys, not both.")
        return self


# ---------------------------------------------------------------------------
# Tier 3 shape-changing operations
# ---------------------------------------------------------------------------


class AggregationSpecInput(BaseModel):
    """One aggregation within a ``group_aggregate`` operation."""

    model_config = ConfigDict(extra="forbid")

    column: str = Field(min_length=1, description="Display name of the column to aggregate.")
    function: AggregateFunction = Field(
        description="Aggregation function: SUM, AVG, MIN, MAX, COUNT, COUNT_DISTINCT, "
        "STDDEV, VARIANCE, MEDIAN, FIRST, LAST, CONCAT.",
    )
    as_name: str | None = Field(
        default=None,
        description="Output column name; defaults to '<FUNCTION>_<column>' when omitted.",
    )
    delimiter: str | None = Field(
        default=None,
        description="Delimiter used by the CONCAT function; ignored for other functions.",
    )


class GroupAggregateOperation(BaseModel):
    """The ``group_aggregate`` operation: collapse rows by grouping and aggregating.

    SHAPE-CHANGING — replaces the dataset with the grouped result (one row per
    unique combination of ``group_by`` columns). Apply after all row-level
    cleaning steps. Uses the backend PIVOT task.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["group_aggregate"] = "group_aggregate"
    group_by: list[str] = Field(
        min_length=1,
        description="Display names of the columns to group by (the new row keys).",
    )
    aggregations: list[AggregationSpecInput] = Field(
        min_length=1,
        description="The aggregation(s) to compute per group.",
    )
    condition: ConditionInput | None = Field(
        default=None,
        description="Optional condition to filter rows before aggregating.",
    )


class WindowOperation(BaseModel):
    """The ``window`` operation: compute a window function over partitions.

    ADDITIVE — adds a new column without changing the row count. Use for
    running totals, ranks, lag/lead comparisons, and partition-level aggregates.
    Supply ``partition_by`` to compute within groups and ``order_by`` to define
    row order within each partition.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["window"] = "window"
    function: WindowFunction = Field(
        description="Window function: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, SUM, "
        "AVG, MIN, MAX, COUNT, FIRST_VALUE, LAST_VALUE, STDDEV, VARIANCE, "
        "PERCENT_RANK, NTILE.",
    )
    column: str | None = Field(
        default=None,
        description="Source column for value-bearing functions (SUM/AVG/MIN/MAX/LAG/LEAD/…). "
        "Omit for row-numbering functions (ROW_NUMBER/RANK/DENSE_RANK).",
    )
    new_column: str | None = Field(
        default=None,
        description="Name of the new column to create. "
        "Provide this OR existing_column (exactly one).",
    )
    existing_column: str | None = Field(
        default=None,
        description=_OVERWRITE_EXISTING_COLUMN_DESCRIPTION,
    )
    column_type: ColumnType = Field(
        default=ColumnType.NUMERIC,
        description="Type of the result column (usually NUMERIC).",
    )
    partition_by: list[str] = Field(
        default_factory=list,
        description="Columns to partition by (window resets per group). "
        "Omit for a single global window.",
    )
    order_by: list[OrderBySpec] = Field(
        default_factory=list,
        description="Columns defining the within-partition row order (required for "
        "rank/lag/lead functions; ignored by partition-level aggregates).",
    )
    range_type: WindowRange = Field(
        default=WindowRange.UNBOUNDED,
        description="UNBOUNDED includes all rows in the partition; RUNNING accumulates "
        "up to the current row (running total / running rank).",
    )

    @model_validator(mode="after")
    def _exactly_one_target(self) -> WindowOperation:
        if bool(self.new_column) == bool(self.existing_column):
            raise ValueError("window requires exactly one of new_column or existing_column.")
        return self


class UnnestOperation(BaseModel):
    """The ``unnest`` operation: unpivot selected columns into Label/Value rows.

    SHAPE-CHANGING — fan-out: one column per selected source column becomes a
    row, multiplying row count. Each source column contributes a row with its
    display name in the ``label_column`` and its cell value in the
    ``value_column``. The source columns are dropped and all other columns are
    repeated per new row.
    """

    model_config = ConfigDict(extra="forbid")

    op: Literal["unnest"] = "unnest"
    columns: list[str] = Field(
        min_length=2,
        description="Display names of the columns to unpivot (at least 2).",
    )
    label_column: str = Field(
        default="Label",
        min_length=1,
        description="Name of the output column that holds the source column's display name.",
    )
    value_column: str = Field(
        default="Value",
        min_length=1,
        description="Name of the output column that holds the source column's cell value.",
    )


# Discriminated union of transform operations: the model selects an operation by
# its ``op`` discriminator, and the handler routes it to the matching pysdk pure
# builder (handlers._OPERATION_BUILDERS). Adding an operation = a new member here
# + one registry entry — no new tool, no handler branching.
TransformOperation = Annotated[
    ConvertOperation
    | TextTransformOperation
    | DiscardDuplicatesOperation
    | ReplaceOperation
    | FillNullOperation
    | MathOperation
    | CombineOperation
    | AddColumnOperation
    | CopyOperation
    | SelectRowsOperation
    | SetValuesOperation
    | JoinOperation
    | LookupOperation
    | GenAiOperation
    | SqlOperation
    | DeleteOperation
    | LimitOperation
    | SubstringOperation
    | SplitOperation
    | BulkReplaceOperation
    | FillOperation
    | ExtractDateOperation
    | DateDiffOperation
    | IncrementDateOperation
    | SmallLargeOperation
    | JsonExtractOperation
    | GroupAggregateOperation
    | WindowOperation
    | UnnestOperation,
    Field(discriminator="op"),
]


class AddStepInput(BaseModel):
    """Input for ``add_step`` — add one transform step to a View's draft.

    The step is added to the View's *draft* pipeline (entering draft mode on the
    first step), where it is staged and statically projected but NOT run. The
    pipeline executes only when ``run_pipeline`` submits the draft. Always
    ``get_columns`` first so the operation references real column names.
    """

    model_config = ConfigDict(extra="forbid")

    view_id: int = Field(ge=1, description="Numeric id of the View to transform.")
    operation: TransformOperation = Field(
        description="The transform operation to add to the View's draft."
    )

    @field_validator("operation", mode="before")
    @classmethod
    def _parse_stringified_operation(cls, v: object) -> object:
        """Anthropic tool-use serializes a deeply-nested object parameter as a
        JSON string rather than an object, so ``operation`` arrives as e.g.
        ``'{"op": "join", ...}'``. Parse it back to a dict before the
        discriminated union validates; leave a non-JSON string for the union to
        reject with a clear error.
        """
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v


class RunPipelineInput(BaseModel):
    """Input for ``run_pipeline`` — submit a View's draft for execution.

    Submits every step added since the draft began and fires the pipeline run in
    the background (the agent does not wait for it to finish).
    """

    model_config = ConfigDict(extra="forbid")

    view_id: int = Field(ge=1, description="Numeric id of the View whose draft to run.")


class DiscardDraftInput(BaseModel):
    """Input for ``discard_draft`` — throw away a View's pending draft steps.

    Restores the View to its last submitted state; use this to abandon a plan
    before it is run.
    """

    model_config = ConfigDict(extra="forbid")

    view_id: int = Field(ge=1, description="Numeric id of the View whose draft to discard.")


class ExportToTargetInput(BaseModel):
    """Input for ``export_to_target`` — send a View's data to an external target.

    ``handler_type`` selects the destination (a database, cloud store, file
    transfer, email, BI tool, …). ``target_properties`` carries that handler's
    connection/destination config as a flat dict — its keys are handler-specific
    and validated against the destination's contract by the pysdk builder, which
    raises an actionable error for a missing/unknown key (surfaced as a typed
    FAILED result, never a silent mis-send). Credentials passed here are split
    into the encrypted trigger store backend-side.
    """

    model_config = ConfigDict(extra="forbid")

    view_id: int = Field(ge=1, description="Numeric id of the View to export from.")
    handler_type: HandlerType = Field(
        description="Destination handler, e.g. mysql/postgres/s3/email/sftp/bigquery."
    )
    target_properties: dict[str, Any] = Field(
        description=(
            "Handler-specific destination config (host/port/database/table/… for "
            "databases, emails for email, domain/directory/file for ftp, …). "
            "Credentials go here and are encrypted backend-side."
        )
    )
    run_immediately: bool = Field(
        True, description="Run the export as soon as it is added (default True)."
    )
    end_of_pipeline: bool = Field(
        True, description="Export after all transforms have run (default True)."
    )

    @field_validator("target_properties", mode="before")
    @classmethod
    def _parse_stringified_target(cls, v: object) -> object:
        """Anthropic tool-use serializes a nested object parameter as a JSON
        string rather than an object, so ``target_properties`` can arrive as e.g.
        ``'{"host": "...", ...}'``. Parse it back to a dict before validation;
        leave a non-JSON string for the dict-type check to reject clearly.
        """
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v


class GenerateDashboardInput(BaseModel):
    """Input for ``generate_dashboard`` — build an AI dashboard from a View.

    ``intent`` is a plain-English description of the dashboard to build; the
    backend's AI turns it into charts over the View's data. Validation of the
    intent (length) and source happens in the pysdk dashboard-spec builder, whose
    actionable error is surfaced as a typed FAILED result.
    """

    model_config = ConfigDict(extra="forbid")

    view_id: int = Field(ge=1, description="Numeric id of the View the dashboard draws from.")
    intent: str = Field(description="Plain-English description of the dashboard to build.")
    enable_filters: bool = Field(True, description="Generate interactive filters (default True).")
    enable_pages: bool = Field(
        False, description="Generate multiple dashboard pages (default False)."
    )
