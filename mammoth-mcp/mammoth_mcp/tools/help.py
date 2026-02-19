"""On-demand help docs — progressive disclosure for LLM context."""

from __future__ import annotations

from mammoth_mcp.server import mcp

HELP_TOPICS: dict[str, str] = {
    "overview": """\
# Mammoth Analytics — Key Concepts

## Entities

- **Workspace**: Top-level container that owns billing, members, and projects.
- **Project**: Groups related datasets within a workspace. Auto-discovered \
when you call `get_view` with a view ID.
- **Dataset**: One uploaded file (CSV, Excel) or connected data source. \
A dataset always has at least one view.
- **View**: A transformable lens on a dataset's data. Every transformation \
(filter, join, pivot, …) is appended as a **pipeline task**. Views share the \
underlying data but each has its own independent pipeline. You can create \
multiple views on the same dataset to explore different transformations \
without affecting each other.
- **Pipeline task**: A single transformation step applied to a view. Tasks \
are ordered and executed sequentially. Use `list_tasks` to see them and \
`delete_task` to undo any step. Deleting a task in the middle re-executes \
all subsequent tasks.
- **Column**: Each view has columns with a **display name** (human-readable, \
used in all tool parameters) and an **internal name** (system-generated, \
e.g. "column_qklgqhtw6v"). Column types: TEXT, NUMERIC, DATE, DATETIME. \
Always use `get_view` to look up current display names before referencing \
columns — names may change after transformations.

## Navigation Tools
- `list_projects` → list all projects in the workspace
- `list_datasets` → list all datasets in the active project
- `get_dataset` → get dataset details including its views
- `list_views` → list views in a dataset
- `get_view` → get view metadata: column names, types, internal names, row count
- `get_data` → fetch rows (max 400 per call, use offset for pagination)

## Modification Tools
- `create_view` / `delete_view` — manage views (clone a view to experiment safely)
- `upload_file` — upload CSV or Excel to create a new dataset
- `filter_rows`, `set_values`, `math_transform`, `pivot`, `window`, \
`join_views`, `lookup`, `convert_type`, etc. — call `get_help("transformations")` for the full list
- `ai_transform` — AI-generated column from a natural language prompt
- `sql_query` — transform via natural language intent or raw SQL
- `export_data` / `export_to_database` — export results to CSV, S3, email, \
database, or another dataset

## Common Workflows
- **Explore data**: `get_view` → `get_data` (sample) → analyze
- **Clean data**: call `get_help("data_cleaning")` for full workflow
- **Transform data**: call `get_help("transformations")` to pick the right tool
- **Conditional operations**: call `get_help("conditions")` for condition syntax
""",
    "transformations": """\
# Available Transformations

Each transformation is its own tool — call it directly by name. \
Every transformation adds a pipeline task that can be undone with `delete_task`.

---

## Column Structure

### add_column
Create one or more empty columns of a specified data type (TEXT, NUMERIC, or \
DATE). Useful for structuring datasets in advance or preparing placeholders \
for future data entry.
**Limitation**: Only creates blank columns — no values are populated. If data \
needs to be computed or entered conditionally, use `set_values` or `math` instead.

### delete_columns
Permanently delete one or more selected columns from the view.
**Limitation**: Once removed, column data is lost unless recreated manually. \
Does not support conditional or partial deletion.

### copy_columns
Duplicate values from one column into a new or existing column, optionally \
based on a condition. Useful for creating backups, consolidating sources into \
one column, or selectively transferring values.
**Limitation**: When copying numeric or date columns into text, the format \
gets locked as displayed and can't be edited later.

### combine_columns
Merge multiple column values into a single column with custom formatting. \
Users can interleave strings (spaces, commas, symbols) between column values \
to construct outputs like full names, dates, or addresses. Supports \
conditions and flexible ordering.
**Limitation**: Works only with text-compatible data. Purely string-based — \
does not perform type conversions or validations.

### convert_type
Change column type: TEXT ↔ NUMERIC ↔ DATE. Supports bulk conversion of \
multiple columns. Auto-detects date formats and provides formatting patterns \
for manual date parsing when needed.
**Limitation**: Invalid conversions result in NULL values and the original \
column is overwritten (copy first if needed). Auto-detection may fail for \
uncommon date formats. Text-to-numeric is strict — extra symbols or malformed \
numbers become NULL. Does not handle mixed-type content without prior cleaning.

---

## Value Transformations

### filter_rows
Keep or remove rows based on conditions across text, numeric, or date \
columns. Supports multiple conditions with AND/OR, nested conditions, \
comparisons between columns, and case sensitivity.
**Limitation**: Conditions are static once set. Filtering is row-level only — \
no aggregate or group-level logic. Does not delete data, only filters for \
downstream use.

### set_values
Populate or annotate columns by inserting values based on conditions. \
Supports conditional labeling, creation of new columns, and insertion of \
multiple values with different criteria. Works for text, numeric, and date \
values. Use for grading, tagging, or classifying data.
**Limitation**: No advanced expressions or cross-row logic. Data type \
mismatches not allowed. Complex logic must be split into multiple tasks.

### math_transform
Perform arithmetic using column values, constants, and functions: SUM, AVG, \
MIN, MAX, COUNT, INT, ABS. Supports BODMAS rules, nested expressions, and \
conditions. Create new numeric columns for totals, averages, percentages, \
and derived metrics.
**Limitation**: Expressions must reference valid column names. Division by \
zero yields empty values. Empty cells are treated as zeros. Only numeric \
operations — no text or date manipulation.

### text_transform
Standardize text by changing case (UPPER, LOWER, TITLE) and consolidating \
extra spaces into single spaces. Trim leading/trailing whitespace. Applies \
to one or more columns. Supports conditions.
**Limitation**: Simple formatting only — no custom case rules, partial string \
transformations, or language-specific capitalization. Handles whitespace and \
casing only, not punctuation or symbols.

### replace_values
Find and replace specific text in one or more columns, fully or partially. \
Supports multiple find-replace pairs, case sensitivity, whole-word matching, \
and conditions.
**Limitation**: Text columns only. Case sensitivity and whole-cell matching \
must be configured carefully to avoid missed replacements.

### bulk_replace
Group and replace multiple variations of values with a single standardized \
value. Useful for correcting inconsistent entries or categorizing similar \
values.
**Limitation**: Operates one column at a time. Does not handle structural \
inconsistencies — use `text_transform` for case/whitespace issues first.

### split_column
Split a text column by delimiter into multiple new columns. Supports any \
delimiter including special characters. Useful for parsing URLs, file paths, \
or composite fields like "City, State".
**Limitation**: Text columns only. If a row has fewer segments than specified \
columns, extras are empty. Extra segments beyond the count are discarded. \
No regex-based splitting.

### substring
Extract specific substrings using position-based slicing (START/END with \
num_char, LEFT/RIGHT with char_position), delimiters, keywords, or regular \
expressions. Supports conditions and custom output columns.
**Limitation**: Text columns only. Incorrect patterns across rows can lead \
to partial or empty results. Cannot chain multiple extractions in one step.

---

## Aggregation & Reshaping

### pivot
Group rows and aggregate values with SUM, AVG, COUNT, MAX, MIN. Supports \
multi-level grouping and conditions.
**IMPORTANT**: Apply **last** — once applied, the grouped structure replaces \
the original dataset, making row-level columns unavailable for subsequent \
tasks. Complete all filtering and calculations first.

### window
Row-aware calculations across partitions without collapsing rows. Supports:
- **Aggregation**: SUM, AVG, COUNT, MIN, MAX (running or group-level)
- **Ranking**: RANK, DENSE_RANK, ROW_NUMBER, NTILE
- **Relative**: LAG, LEAD, FIRST_VALUE, LAST_VALUE, NTH_VALUE
Supports partition_by, order_by, and range (UNBOUNDED vs RUNNING).
**Limitation**: Does not reduce rows. Incorrect partitioning can lead to \
inaccurate outputs. Cannot reference multiple columns dynamically.

### crosstab
Pivot a column's distinct values into new column headers with aggregation. \
Creates a matrix view useful for reports.
**IMPORTANT**: Like pivot, should be applied **last** — reshapes the data.

### unnest
Transform wide format to long format by stacking columns into rows. Select \
columns to reshape, assign custom labels. Useful for time-series or repeated \
measurements.
**Limitation**: Only columns of the same data type can be stacked together.

### fill_missing
Fill blank cells by copying from the nearest non-empty cell above \
(LAST_VALUE) or below (FIRST_VALUE). Supports grouping to fill within \
logical subsets (e.g., by patient ID) and sorting.
**Limitation**: Direction depends on chosen order — improper ordering leads \
to incorrect fills. Without grouping, values fill from across the full \
dataset.

### limit_rows
Keep only the top or bottom N rows. Supports sorting by any column.
**Limitation**: No group-wise limits. No tie handling. Without sorting, \
defaults to original row order.

### discard_duplicates
Remove rows with identical values across all columns. Can ignore specific \
columns during comparison.
**Limitation**: When columns are ignored, values from those columns are \
randomly retained. Does not control which duplicate is preserved.

---

## Advanced

### join_views
Combine with another view using LEFT, RIGHT, INNER, or OUTER join. Map \
columns across data types, select which columns to bring, and add prefixes.
**Limitation**: Equality-based key matching only. No many-to-many joins or \
custom join conditions.

### lookup
VLOOKUP-style: fetch a single column from a reference view by matching a \
shared key. Map IDs to names or codes to descriptions.
**Limitation**: Can only fetch one column (unlike join). Exact key match \
only — unmatched keys become empty.

### json_extract
Parse JSON text into structured columns (objects) or rows (lists). \
Auto-detects structure and suggests keys. Handles missing keys gracefully \
(empty cells, not errors).
**Limitation**: Does not parse dates in JSON — convert separately. Does not \
flatten deeply nested or mixed structures.

### extract_date
Extract components from a date column: year, month, day, hour, minute, \
second, weekday, quarter, week, millisecond, day_of_year, weekday_text, \
month_text, year_month_day, month_year, hour_minute_second, and more.
**Limitation**: Only works with properly formatted date columns. No custom \
formats or localized names. No timezone context.

### date_diff
Calculate time difference between two date columns in seconds, minutes, \
hours, days, months, or years.
**Limitation**: Output is always integer (rounded down). Only date columns — \
text dates must be converted first.

### increment_date
Add or subtract time units (years, months, weeks, days, hours, minutes, \
seconds) from a date column. Supports conditions and custom output columns.
**Limitation**: Only valid date columns. No auto-correction for invalid \
dates. No timezone handling.

---

## AI & SQL

### ai_transform
AI generates a new column from a natural language prompt and context columns \
(up to 20). Use for classification, extraction, summarization, or enrichment.

### sql_query
Transform via natural language intent (auto-generates SQL) or direct raw \
SQL. Supports filtering, ranking, aggregation, and complex queries.

---

## Key Rules
- `pivot` and `crosstab` should be the **last** transformation.
- Math operations only work on NUMERIC columns.
- Text operations only work on TEXT columns — `convert_type` first if needed.
- Date operations only work on DATE columns — `convert_type` first if needed.
- Always verify column names with `get_view` before referencing them.
- Copy important columns before destructive operations like `convert_type` or \
`delete_columns`.
""",
    "conditions": """\
# Building Conditions

Conditions are used in `filter_rows`, `set_values`, `combine_columns`, \
`copy_columns`, `math`, `text_transform`, `replace_values`, `substring`, \
and `increment_date`.

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

## All Available Operators

### Comparison
| Operator | Meaning | Example value |
|----------|---------|---------------|
| `EQ` | Equals | `"Active"` or `100` |
| `NE` | Not equals | `"Inactive"` |
| `GT` | Greater than | `1000` |
| `GTE` | Greater than or equal | `1000` |
| `LT` | Less than | `50` |
| `LTE` | Less than or equal | `50` |

### Text
| Operator | Meaning | Example value |
|----------|---------|---------------|
| `CONTAINS` | Text contains substring | `"york"` |
| `NOT_CONTAINS` | Text does not contain | `"test"` |
| `STARTS_WITH` | Text starts with | `"Mr."` |
| `NOT_STARTS_WITH` | Text does not start with | `"Dr."` |
| `ENDS_WITH` | Text ends with | `".com"` |
| `NOT_ENDS_WITH` | Text does not end with | `".org"` |

### List Membership
| Operator | Meaning | Example value |
|----------|---------|---------------|
| `IN_LIST` | Value is one of | `["Active", "Pending"]` |
| `NOT_IN_LIST` | Value is not one of | `["Deleted", "Archived"]` |

### Null / Empty (no value parameter needed)
| Operator | Meaning |
|----------|---------|
| `IS_EMPTY` | Cell is null or blank |
| `IS_NOT_EMPTY` | Cell has a value |

### Min / Max (no value parameter needed)
| Operator | Meaning |
|----------|---------|
| `IS_MAXVAL` | Cell has the maximum value in the column |
| `IS_NOT_MAXVAL` | Cell does not have the maximum value |
| `IS_MINVAL` | Cell has the minimum value in the column |
| `IS_NOT_MINVAL` | Cell does not have the minimum value |

## Nesting
Compound conditions can be nested to any depth:
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

## Tips
- Use `IS_EMPTY` / `IS_NOT_EMPTY` for null checks — no value parameter needed.
- Use `IN_LIST` with an array value for multi-value matching.
- `IS_MAXVAL` / `IS_MINVAL` are useful for finding extreme values without \
knowing the actual max/min.
- All operator names are case-insensitive in the SDK but UPPERCASE is \
conventional.
- Column names in conditions must be **display names** (from `get_view`).
""",
    "data_cleaning": """\
# Data Cleaning Workflow

When asked about data quality, cleaning opportunities, or data issues, \
follow this structured workflow.

## Step 1: Inspect the Data
- Call `get_view` to see all columns, their types, and the total row count.
- Call `get_data` with limit=200 to sample actual values.
- Look at the data carefully — column types, value distributions, patterns.

## Step 2: Identify Issues

### Text Quality
| Issue | How to spot | Fix |
|-------|------------|-----|
| **Mixed case** ("new york" vs "New York") | Same entity, different casing | `text_transform` with case=UPPER/LOWER/TITLE |
| **Leading/trailing whitespace** | Values look same but aren't equal | `text_transform` with trim=true |
| **Inconsistent values** (typos, abbreviations) | "NY", "New York", "new york" | `bulk_replace` to standardize |
| **Specific wrong values** | Known typos or outdated terms | `replace_values` with find/replace |

### Type Issues
| Issue | How to spot | Fix |
|-------|------------|-----|
| **Numbers stored as TEXT** | Column type TEXT but values are "123", "45.6" | `convert_type` with to=NUMERIC |
| **Dates stored as TEXT** | Column type TEXT but values are "2024-01-15" | `convert_type` with to=DATE |
| **Mixed types in column** | Some values numeric, some text in same column | Clean non-conforming values first, then convert |

### Structural Issues
| Issue | How to spot | Fix |
|-------|------------|-----|
| **Composite columns** | "City, State" or "First Last" in one column | `split_column` with delimiter |
| **Duplicate rows** | Identical rows appear multiple times | `discard_duplicates` |
| **Missing values** | Empty cells or NULLs in important columns | `fill_missing` (directional) or `set_values` (fixed value) |
| **Unnecessary columns** | Columns with no useful data | `delete_columns` |

### Date Issues
| Issue | How to spot | Fix |
|-------|------------|-----|
| **Date components needed** | Need year/month/quarter separately | `extract_date` with component |
| **Date arithmetic needed** | Need age, duration, or future dates | `date_diff` or `increment_date` |

## Step 3: Report Findings
Present each issue with:
- **Column name**: which column is affected
- **Example values**: show 2-3 concrete examples of the problem
- **Recommended fix**: specific tool, type, and key parameters
- **Severity**: HIGH (blocks analysis), MEDIUM (affects accuracy), LOW (cosmetic)
- **Row impact**: how many rows are affected (estimate from sample)

## Step 4: Confirm Before Acting
Always ask the user which fixes to apply before making any changes. \
Transformations are reversible via `delete_task`, but it's better to agree \
on a plan first.

## Recommended Execution Order
Apply fixes in this order to avoid cascading issues:
1. **Type conversions** — so subsequent operations work on correct types
2. **Split composite columns** — so individual parts can be cleaned
3. **Trim whitespace** — removes invisible differences
4. **Standardize case** — normalizes text for deduplication
5. **Replace/fix inconsistent values** — standardize after case is uniform
6. **Handle missing values** — fill or set defaults
7. **Remove duplicates** — last, since earlier fixes may resolve apparent duplicates
8. **Pivot/aggregate** — always last, reshapes the data
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
