"""On-demand help docs — progressive disclosure for LLM context."""

from __future__ import annotations

from mammoth_mcp.server import mcp

HELP_TOPICS: dict[str, str] = {
    "overview": """\
# Mammoth Analytics — Key Concepts

## Entities

- **Workspace**: Top-level container that owns billing, members, and projects.
- **Project**: Groups related datasets within a workspace. You must call \
`set_project` before any data operation.
- **Dataset**: One uploaded file (CSV, Excel) or connected data source. \
A dataset always has at least one view.
- **View**: A transformable lens on a dataset's data. Every transformation \
(filter, join, pivot, …) is appended as a **pipeline task**. Views share the \
underlying data but each has its own independent pipeline.
- **Pipeline task**: A single transformation step applied to a view. Tasks \
are ordered and executed sequentially. Use `list_tasks` to see them and \
`delete_task` to undo any step.
- **Column**: Each view has columns with a **display name** (human-readable, \
used in all tool parameters) and an **internal name** (system-generated). \
Column types: TEXT, NUMERIC, DATE, DATETIME.

## Navigation Tools
- `list_projects` → projects in the workspace
- `list_datasets` → datasets in the active project
- `get_dataset` → dataset details including its views
- `list_views` → views in a dataset
- `get_view` → view metadata (columns, types, row count)
- `get_data` → fetch rows (max 400 per call, use offset for pagination)

## Modification Tools
- `create_view` / `delete_view` — manage views
- `upload_file` — create a dataset from CSV/Excel
- `transform_columns`, `transform_values`, `transform_aggregate`, \
`transform_advanced` — apply transformations (see topic "transformations")
- `ai_transform` — AI-generated column from a prompt
- `sql_query` — transform via natural language or raw SQL
- `export_data` / `export_to_database` — export results
""",
    "transformations": """\
# Available Transformations

Each transformation is applied via one of four tools using a `type` parameter. \
Every transformation adds a pipeline task that can be undone with `delete_task`.

## Column Structure (`transform_columns`)

| type | Description |
|------|-------------|
| `add_column` | Create empty columns of a specified type (TEXT, NUMERIC, DATE). \
Useful for placeholders — does not populate values. |
| `delete_columns` | Permanently remove columns from the view. |
| `copy_columns` | Duplicate column values into new columns, optionally with conditions. |
| `combine_columns` | Merge multiple columns with separators (spaces, commas, etc.) \
into one column. String-based only. Supports conditions. |
| `convert_type` | Change column type (TEXT ↔ NUMERIC ↔ DATE). Invalid values \
become NULL. Auto-detects date formats. |

## Value Transformations (`transform_values`)

| type | Description |
|------|-------------|
| `filter_rows` | Keep or remove rows matching conditions. Supports AND/OR logic, \
comparisons between columns, case sensitivity. |
| `set_values` | Insert/label values conditionally. Good for grading, tagging, \
classifying. Supports new or existing columns. |
| `math` | Arithmetic using columns, constants, and functions (SUM, AVG, MIN, \
MAX, COUNT, INT, ABS). Follows BODMAS. Supports conditions. |
| `text_transform` | Standardize case (UPPER/LOWER/TITLE) and trim whitespace. \
Applies to one or more columns. Supports conditions. |
| `replace_values` | Find and replace text in columns. Supports case sensitivity, \
whole-word matching, and conditions. |
| `bulk_replace` | Group multiple variations and replace with a single standardized \
value. Operates one column at a time. |
| `split_column` | Split a text column by delimiter into multiple new columns. |
| `substring` | Extract substrings by position, delimiter, keyword, or regex. \
Supports conditions. |

## Aggregation & Reshaping (`transform_aggregate`)

| type | Description |
|------|-------------|
| `pivot` | Group rows and aggregate values (SUM, AVG, COUNT, MIN, MAX). \
**Should be applied last** — replaces the original row structure. |
| `window` | Row-aware calculations without collapsing rows: aggregation \
(running SUM, AVG), ranking (RANK, DENSE_RANK, ROW_NUMBER, NTILE), and \
relative (LAG, LEAD, FIRST_VALUE, LAST_VALUE). Supports partition and sort. |
| `crosstab` | Pivot a column's values into new column headers with aggregation. |
| `unnest` | Transform wide format to long format (unpivot). Columns must share \
the same data type. |
| `fill_missing` | Fill blank cells from nearest non-empty cell above or below. \
Supports grouping to fill within logical subsets. |
| `limit_rows` | Keep top or bottom N rows. Supports sorting. |
| `discard_duplicates` | Remove rows with identical values. Can ignore specific \
columns during comparison. |

## Advanced (`transform_advanced`)

| type | Description |
|------|-------------|
| `join` | Combine with another view using LEFT, RIGHT, INNER, or OUTER join. \
Equality-based key matching only. |
| `lookup` | VLOOKUP-style: fetch one column from a reference view by matching key. |
| `json_extract` | Parse JSON text into structured columns (objects) or rows (lists). |
| `extract_date` | Extract components (year, month, day, hour, weekday, quarter, etc.) \
from a date column. |
| `date_diff` | Calculate time difference between two date columns in chosen units. |
| `increment_date` | Add or subtract time (years, months, days, hours, etc.) from \
a date column. Supports conditions. |

## AI & SQL

| Tool | Description |
|------|-------------|
| `ai_transform` | AI generates a new column from a natural language prompt and \
context columns (up to 20). |
| `sql_query` | Transform via natural language intent (auto-generates SQL) or \
direct raw SQL. Supports filter, rank, aggregate. |

## Key Rules
- `pivot` / `crosstab` should be the **last** transformation — they reshape the data.
- Math operations only work on NUMERIC columns.
- Text operations only work on TEXT columns — convert first if needed.
- Verify column availability with `get_view` before referencing columns.
""",
    "conditions": """\
# Building Conditions

Conditions are used in `filter_rows`, `set_values`, `combine_columns`, `math`, \
`text_transform`, `replace_values`, `substring`, `copy_columns`, and \
`increment_date`.

## Simple Condition
```json
{"column": "Sales", "operator": "GTE", "value": 1000}
```

## Compound Condition (AND/OR)
```json
{
  "logic": "AND",
  "conditions": [
    {"column": "Status", "operator": "EQ", "value": "Active"},
    {"column": "Sales", "operator": "GTE", "value": 500}
  ]
}
```

## Available Operators

### Comparison
- `EQ` — equals
- `NEQ` — not equals
- `GT` — greater than
- `GTE` — greater than or equal
- `LT` — less than
- `LTE` — less than or equal

### Text
- `CONTAINS` — text contains value
- `NOT_CONTAINS` — text does not contain value
- `STARTS_WITH` — text starts with value
- `ENDS_WITH` — text ends with value
- `MATCHES_REGEX` — matches regex pattern

### List
- `IN_LIST` — value is in a list (value should be a list)
- `NOT_IN_LIST` — value is not in a list

### Null/Empty
- `IS_EMPTY` — cell is null or blank (no value needed)
- `IS_NOT_EMPTY` — cell has a value (no value needed)

### Column-to-Column
- `EQ_COL` — equals another column (value = column name)
- `NEQ_COL`, `GT_COL`, `GTE_COL`, `LT_COL`, `LTE_COL` — same for other comparisons

## Nesting
Compound conditions can be nested arbitrarily:
```json
{
  "logic": "OR",
  "conditions": [
    {"column": "Region", "operator": "EQ", "value": "East"},
    {
      "logic": "AND",
      "conditions": [
        {"column": "Region", "operator": "EQ", "value": "West"},
        {"column": "Sales", "operator": "GTE", "value": 10000}
      ]
    }
  ]
}
```
""",
    "data_cleaning": """\
# Data Cleaning Workflow

When asked about data quality, cleaning opportunities, or data issues:

## Step 1: Inspect
- Call `get_view` to see all columns, their types, and row count.
- Call `get_data` with limit=200 to sample actual values.

## Step 2: Identify Issues

| Issue | How to spot it | Fix with |
|-------|---------------|----------|
| Mixed case ("new york" vs "New York") | Distinct values differ only by case | `transform_values` type=`text_transform` (UPPER/LOWER/TITLE) |
| Leading/trailing whitespace | Values have invisible padding | `transform_values` type=`text_transform` with trim=true |
| Type mismatch (numbers as TEXT) | Column type is TEXT but values are numeric | `transform_columns` type=`convert_type` |
| Dates stored as TEXT | Date-looking values in TEXT columns | `transform_columns` type=`convert_type` to DATE |
| Missing/blank values | Empty cells or NULLs | `transform_aggregate` type=`fill_missing` or `transform_values` type=`set_values` |
| Duplicate rows | Identical rows appear multiple times | `transform_aggregate` type=`discard_duplicates` |
| Inconsistent values (typos) | Same entity spelled differently | `transform_values` type=`replace_values` or `bulk_replace` |
| Composite columns ("City, State") | Multiple data points in one column | `transform_values` type=`split_column` |

## Step 3: Report
Present each issue with:
- Affected column name
- Example problematic values
- Recommended tool, type, and key parameters
- Severity (how much it impacts analysis)

## Step 4: Confirm
Always ask the user which fixes to apply before making changes. \
Transformations are reversible (`delete_task`) but it's better to confirm first.

## Recommended Order
1. Type conversions (so subsequent operations work correctly)
2. Trim whitespace and standardize case
3. Replace/fix inconsistent values
4. Handle missing values
5. Remove duplicates (last, since earlier fixes may resolve apparent duplicates)
""",
}

TOPIC_LIST = ", ".join(f"`{t}`" for t in HELP_TOPICS)


@mcp.tool()
def get_help(topic: str) -> str:
    """Get detailed guidance on a Mammoth topic. Call this before applying \
transformations or analyzing data quality.

    Args:
        topic: One of: overview, transformations, conditions, data_cleaning.
    """
    doc = HELP_TOPICS.get(topic)
    if doc:
        return doc
    return (
        f"Unknown topic '{topic}'. "
        f"Available topics: {TOPIC_LIST}."
    )
