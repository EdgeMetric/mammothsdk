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

## Schema Awareness

Use the metadata from `get_view` and `get_data` to guide your approach:
- **Column types** determine which tools apply (NUMERIC for math, DATE for \
date ops, TEXT for text ops). CSV dates ALWAYS upload as TEXT.
- **row_count** tells you the data size — filter early on large datasets, \
check the 50K limit before `ai_transform`.
- **Sample values** from `get_data` reveal patterns: currency formatting \
("$1,234") means strip-then-convert, inconsistent casing means \
`text_transform` first, date-like text means `convert_type`.

## Common Workflows
- **Explore data**: `get_view` → `get_data` (sample) → analyze
- **Clean data**: call `get_help("data_cleaning")` for structured workflow
- **Transform data**: call `get_help("transformations")` to pick the right tool
- **Multi-step pipelines**: call `get_help("workflows")` for proven patterns
- **Condition syntax**: call `get_help("conditions")` for operators and examples
- **Hit an error?**: call `get_help("troubleshooting")` for diagnosis and recovery

## What Mammoth Cannot Do (via pipeline)
- **Rename columns** — done via Display Changes (right-click header), not pipeline
- **Regex-based splitting** — use `split_column` with delimiters or `sql_query` for regex
- **Stored procedures / UDFs** — `sql_query` supports single-statement DuckDB SQL only
- **Cross-dataset references in expressions** — join/lookup first, then compute
""",
    "transformations": """\
# Available Transformations

Each transformation is its own tool — call it directly by name. \
Every transformation adds a pipeline task that can be undone with `delete_task`.

Usage frequency from 200+ production pipelines is noted where available \
to help you pick the most battle-tested approach.

---

## Column Structure

### add_column
Create empty columns (TEXT, NUMERIC, or DATE). Use as placeholders for \
`set_values` or flag columns. *(Usage: 243 pipelines)*
```
add_column(view_id=V, column_name="Status Flag", column_type="TEXT")
```

### delete_columns
Remove columns from the view permanently. Remove unused columns early \
for better performance on wide datasets.
```
delete_columns(view_id=V, columns=["Temp Col", "Helper"])
```

### copy_columns
Duplicate column values into a new or existing column. **Always copy before \
destructive operations** like `convert_type` that overwrite the original. \
*(Usage: 416 pipelines — 2nd most used)*
```
copy_columns(view_id=V, copies=[{"source": "Revenue", "as": "Revenue Original", "type": "NUMERIC"}])
```

### combine_columns
Merge multiple columns into one with custom separators. Use for full names, \
addresses, or composite keys.
```
combine_columns(view_id=V, sources=["First Name", "Last Name"], separator=" ", new_column="Full Name")
```

### convert_type
Change column type: TEXT ↔ NUMERIC ↔ DATE. **Critical prerequisite** for \
math and date operations. Auto-detects common date formats. *(Usage: 213 pipelines)*
- **Before converting TEXT→NUMERIC**: Strip formatting first (`replace_values` \
to remove $, commas, parentheses) — dirty text converts to NULL.
- **Before converting TEXT→DATE**: Usually auto-detected; uncommon formats may \
need SQL.
- Values that fail conversion become NULL — the original column is overwritten.
```
convert_type(view_id=V, conversions=[{"column": "Revenue", "to": "NUMERIC"}, {"column": "Order Date", "to": "DATE"}])
```

---

## Value Transformations

### filter_rows
Keep or remove rows based on conditions. Supports AND/OR, nesting, \
column-to-column comparisons. **Place filters early** for performance — \
date range filters often reduce data by 90%+. *(Usage: 280 pipelines)*
```
filter_rows(view_id=V, condition={"column": "Status", "operator": "EQ", "value": "Active"}, filter_type="SHOW")
```
See `get_help("conditions")` for full operator reference.

### set_values
Insert values based on conditions — use for labeling, tagging, grading, \
or creating categorical columns. Supports multiple conditional tiers with \
a fallback default. *(Usage: 301 pipelines — 3rd most used)*
```
set_values(view_id=V, new_column="Tier", column_type="TEXT", values=[
  {"value": "High", "condition": {"column": "Revenue", "operator": "GTE", "value": 10000}},
  {"value": "Medium", "condition": {"column": "Revenue", "operator": "GTE", "value": 1000}},
  {"value": "Low"}
])
```

### math_transform
Arithmetic on NUMERIC columns with functions: SUM, AVG, MIN, MAX, COUNT, \
INT, ABS. Follows BODMAS rules. **Requires NUMERIC columns** — use \
`convert_type` first if column is TEXT. *(Usage: 569 pipelines — most used)*
```
math_transform(view_id=V, expression="Revenue - Cost", new_column="Margin")
math_transform(view_id=V, expression="Margin / Revenue * 100", new_column="Margin %")
```

### text_transform
Standardize text: change case (UPPER, LOWER, TITLE) and trim whitespace. \
**Apply before `bulk_replace`** — consistent casing makes replacement more \
effective.
```
text_transform(view_id=V, columns=["Company Name", "City"], case="TITLE", trim=true)
```

### replace_values
Find and replace text in columns. Use to strip formatting before \
`convert_type`, fix known typos, or standardize codes. Supports \
case-sensitive and whole-word matching.
```
replace_values(view_id=V, columns=["Revenue"], find="$", replace="")
replace_values(view_id=V, columns=["Revenue"], find=",", replace="")
```

### bulk_replace
Map multiple variations to one standard value. Best for data standardization \
after `text_transform` normalizes casing. AI-powered grouping in the UI.
```
bulk_replace(view_id=V, columns=["Company"], mapping=[
  {"search": ["MSFT", "Microsoft Corp", "Microsoft Inc"], "replace": "Microsoft"},
  {"search": ["AMZN", "Amazon.com"], "replace": "Amazon"}
])
```

### split_column
Split text by delimiter into multiple columns. No regex — use `sql_query` \
for regex-based splitting.
```
split_column(view_id=V, column="Full Name", delimiter=" ", new_columns=[
  {"name": "First Name", "type": "TEXT"},
  {"name": "Last Name", "type": "TEXT"}
])
```

### substring
Extract substrings by position (START/END with num_char, LEFT/RIGHT with \
char_position), delimiter, keyword, or regex pattern.
```
substring(view_id=V, column="Phone", direction="START", num_char=3, new_column="Area Code")
substring(view_id=V, column="Email", regex_pattern="@(.+)", new_column="Domain")
```

---

## Aggregation & Reshaping

### pivot
Group rows and aggregate with SUM, AVG, COUNT, MAX, MIN. Supports \
multi-level grouping. **ALWAYS apply last** — collapses rows and makes \
row-level columns unavailable. Standardize values before pivoting to \
avoid fragmented groups.
```
pivot(view_id=V, group_by=["Region", "Category"], aggregations=[
  {"column": "Revenue", "function": "SUM", "as": "Total Revenue"},
  {"column": "Order ID", "function": "COUNT", "as": "Order Count"}
])
```

### window
Row-aware calculations without collapsing rows:
- **Aggregation**: SUM, AVG, COUNT, MIN, MAX (running or group-level)
- **Ranking**: RANK, DENSE_RANK, ROW_NUMBER, NTILE
- **Relative**: LAG, LEAD, FIRST_VALUE, LAST_VALUE, NTH_VALUE

Supports partition_by, order_by, and range (UNBOUNDED vs RUNNING).
```
window(view_id=V, function="ROW_NUMBER", partition_by=["Customer ID"], order_by=[["Date", "DESC"]], new_column="Row Rank")
window(view_id=V, function="SUM", column="Revenue", partition_by=["Region"], order_by=[["Date", "ASC"]], range_type="RUNNING", new_column="Running Total")
```

### crosstab
Pivot a column's distinct values into column headers with aggregation. \
Creates a matrix view. **Apply last** like pivot.
```
crosstab(view_id=V, rows=["Region"], pivot_column="Quarter", select={"column": "Revenue", "function": "SUM"})
```

### unnest
Wide → long format: stack selected columns into rows. Only columns of \
the same type can be stacked.
```
unnest(view_id=V, columns=["Q1 Sales", "Q2 Sales", "Q3 Sales", "Q4 Sales"], label_column="Quarter", value_column="Sales")
```

### fill_missing
Fill blank cells from nearest non-empty cell above (LAST_VALUE) or below \
(FIRST_VALUE). Supports grouping and sorting.
```
fill_missing(view_id=V, column="Region", direction="LAST_VALUE", partition_by="Region Group", order_by=[["Date", "ASC"]])
```

### limit_rows
Keep top or bottom N rows. Supports sorting.
```
limit_rows(view_id=V, n=100, order_by=[["Revenue", "DESC"]])
```

### discard_duplicates
Remove rows with identical values. Can ignore specific columns. \
**Apply before `pivot`** — duplicates inflate counts/sums.
```
discard_duplicates(view_id=V)
discard_duplicates(view_id=V, ignore_columns=["Timestamp", "Row ID"])
```

---

## Advanced

### join_views
Combine with another view: LEFT, RIGHT, INNER, or OUTER join. Match on \
one or more key columns. **Before joining**: verify key types match \
(convert if needed), check key uniqueness (non-unique = row explosion).
```
join_views(view_id=V, foreign_view_id=OTHER_V, join_type="LEFT",
  on=[{"left": "Customer ID", "right": "Customer ID"}],
  select=["Customer Name", "Region"])
```
After join: call `get_view` to see new column names and check row_count.

### lookup
VLOOKUP-style: fetch one column from a reference view by matching key. \
Simpler than join for single-column enrichment.
```
lookup(view_id=V, source="Product ID", lookup_view_id=REF_V, key="Product ID", value="Product Name", new_column="Product Name")
```

### json_extract
Parse JSON text columns into structured columns (objects) or rows (lists).
```
json_extract(view_id=V, column="Metadata", json_type="OBJECT", keys=["name", "email", "phone"])
```

### extract_date
Extract date components: year, month, day, hour, minute, second, weekday, \
quarter, week, weekday_text, month_text, year_month_day, etc. **Requires \
DATE column** — use `convert_type` first.
```
extract_date(view_id=V, column="Order Date", component="month", new_column="Order Month")
extract_date(view_id=V, column="Order Date", component="year", new_column="Order Year")
```

### date_diff
Time difference between two date columns in YEAR, MONTH, DAY, HOUR, \
MINUTE, SECOND. **Requires DATE columns.**
```
date_diff(view_id=V, start="Start Date", end="End Date", component="DAY", new_column="Days Elapsed")
```

### increment_date
Add/subtract time from a date column. **Requires DATE column.**
```
increment_date(view_id=V, column="Due Date", delta={"DAYS": 30}, new_column="Extended Due Date")
increment_date(view_id=V, column="Start Date", delta={"MONTHS": -1}, new_column="Prior Month")
```

---

## AI & SQL — Power Tools

### ai_transform
Uses an OpenAI LLM to generate a **new column** from a prompt and context \
columns (up to 20). Best for language understanding: classification, \
sentiment, entity extraction, content generation. *(50K row limit, ~30-60 \
sec per 10K rows for simple tasks)*
- **Prerequisite**: OpenAI API key in workspace settings.
- **Cost**: Each row consumes tokens. Test on ~100 rows first.
- **Prefer structured tools** when logic is deterministic.
- Call `get_help("ai_transform")` for prompt tips and alternatives.

### sql_query
DuckDB SQL via natural language intent (~20 sec generation) or raw SQL. \
Best when 4+ structured tools would be needed, or for CTEs, CASE WHEN, \
subqueries, GROUP BY + HAVING.
- **Intent mode**: Describe in English → auto-generates SQL.
- **Raw SQL mode**: Write DuckDB SQL. Reference columns by display name.
- Call `get_help("sql_query")` for dialect reference and examples.

### Decision framework
1. **Structured tool first** — fastest, cheapest, most predictable
2. **SQL second** — for multi-step logic in one operation
3. **AI last** — only when language understanding is needed

---

## Key Rules
- `pivot` and `crosstab` should be the **last** transformation.
- Math operations only work on NUMERIC columns — `convert_type` first.
- Date operations only work on DATE columns — `convert_type` first.
- Always verify column names with `get_view` after structural changes.
- Copy important columns before destructive operations.
- Call `get_help("workflows")` for multi-step pipeline patterns.
""",
    "conditions": """\
# Building Conditions

Conditions are used in `filter_rows`, `set_values`, `combine_columns`, \
`copy_columns`, `math_transform`, `text_transform`, `replace_values`, \
`substring`, and `increment_date`.

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

## Practical Patterns

### Date range filtering
```json
{
  "logic": "AND",
  "conditions": [
    {"column": "Order Date", "operator": "GTE", "value": "2024-01-01"},
    {"column": "Order Date", "operator": "LTE", "value": "2024-12-31"}
  ]
}
```
Note: The column must be DATE type. If it's TEXT, use `convert_type` first.

### Multi-value matching
```json
{"column": "Status", "operator": "IN_LIST", "value": ["Active", "Pending", "Review"]}
```

### Column-to-column comparison
```json
{"column": "Actual Revenue", "operator": "GT", "value": {"column": "Target Revenue"}}
```

### Find rows with missing data
```json
{
  "logic": "OR",
  "conditions": [
    {"column": "Email", "operator": "IS_EMPTY"},
    {"column": "Phone", "operator": "IS_EMPTY"}
  ]
}
```

### Multi-tier set_values with conditions
```json
set_values(view_id=V, new_column="Priority", column_type="TEXT", values=[
  {"value": "Critical", "condition": {"logic": "AND", "conditions": [
    {"column": "Revenue", "operator": "GTE", "value": 50000},
    {"column": "Days Overdue", "operator": "GT", "value": 30}
  ]}},
  {"value": "High", "condition": {"column": "Revenue", "operator": "GTE", "value": 10000}},
  {"value": "Medium", "condition": {"column": "Revenue", "operator": "GTE", "value": 1000}},
  {"value": "Low"}
])
```

## Common Mistakes
- **IS_EMPTY needs no value**: `{"column": "X", "operator": "IS_EMPTY"}` — \
adding a value parameter will cause an error.
- **IN_LIST needs a list**: `"value": ["a", "b"]` not `"value": "a"`.
- **Numeric comparisons on TEXT columns fail silently**: Text "100" < text \
"20" alphabetically. Convert to NUMERIC first.
- **Date comparisons on TEXT columns**: Use `convert_type` to DATE first, \
otherwise comparison is alphabetical.

## Tips
- `IS_MAXVAL` / `IS_MINVAL` find extreme values without knowing the actual max/min.
- All operator names are case-insensitive but UPPERCASE is conventional.
- Column names must be **display names** (from `get_view`).
- Build complex conditions incrementally — start simple, verify, then nest.
""",
    "data_cleaning": """\
# Data Cleaning Workflow

When asked about data quality, cleaning opportunities, or data issues, \
follow this structured workflow.

## Step 1: Inspect the Data
- Call `get_view` to see all columns, types, and total row count.
- Call `get_data` with limit=200 to sample actual values.
- Look at the data carefully — use column types, value patterns, and \
distributions to guide tool selection:
  - **Column types** → determine which tools are applicable (NUMERIC for \
math, DATE for date ops)
  - **Sample values** → reveal formatting issues (currency symbols, \
inconsistent casing, date-like text)
  - **Null presence** → guide whether to fill, filter, or flag missing data
  - **Repetitive patterns** → suggest bulk_replace or text_transform targets

## Step 2: Identify Issues

### Text Quality
| Issue | How to spot | Fix |
|-------|------------|-----|
| **Mixed case** ("new york" vs "New York") | Same entity, different casing | `text_transform` with case=UPPER/LOWER/TITLE |
| **Leading/trailing whitespace** | Values look same but aren't equal | `text_transform` with trim=true |
| **Inconsistent values** (typos, abbreviations) | "NY", "New York", "new york" | `bulk_replace` to standardize |
| **Specific wrong values** | Known typos or outdated terms | `replace_values` with find/replace |
| **Currency/formatting in numbers** | "$1,234.56" in a TEXT column | `replace_values` to strip $, commas → then `convert_type` |

### Type Issues
| Issue | How to spot | Fix |
|-------|------------|-----|
| **Numbers stored as TEXT** | Column type TEXT, values are "123", "45.6" | `convert_type` with to=NUMERIC (clean first if formatted) |
| **Dates stored as TEXT** | Column type TEXT, values are "2024-01-15" | `convert_type` with to=DATE (auto-detects common formats) |
| **Mixed types in column** | Some numeric, some text in same column | `replace_values` to clean non-conforming → then `convert_type` |
| **Negative numbers as "(123)"** | Parentheses indicate negatives | `replace_values` to strip () → prepend "-" → `convert_type` |

### Structural Issues
| Issue | How to spot | Fix |
|-------|------------|-----|
| **Composite columns** | "City, State" or "First Last" in one column | `split_column` with delimiter |
| **Duplicate rows** | Identical rows appear multiple times | `discard_duplicates` |
| **Missing values** | Empty cells in important columns | `fill_missing` (directional) or `set_values` (fixed value) |
| **Unnecessary columns** | Columns with no useful data | `delete_columns` |

### Date Issues
| Issue | How to spot | Fix |
|-------|------------|-----|
| **Date components needed** | Need year/month/quarter separately | `extract_date` with component |
| **Date arithmetic needed** | Need age, duration, or future dates | `date_diff` or `increment_date` |
| **Date as TEXT** | All CSVs upload dates as TEXT | `convert_type` to DATE before any date operations |

## Step 3: Report Findings
Present each issue with:
- **Column name**: which column is affected
- **Example values**: 2-3 concrete examples of the problem
- **Recommended fix**: specific tool, type, and key parameters
- **Severity**: HIGH (blocks analysis), MEDIUM (affects accuracy), LOW (cosmetic)
- **Row impact**: estimate from sample

## Step 4: Confirm Before Acting
Always ask the user which fixes to apply before making changes. \
Transformations are reversible via `delete_task`, but agree on a plan first.

## Recommended Execution Order

Apply fixes in this order to avoid cascading issues:

1. **Trim whitespace** — `text_transform(trim=true)` removes invisible differences
2. **Standardize case** — `text_transform(case=...)` normalizes text
3. **Split composite columns** — `split_column` so individual parts can be cleaned
4. **Replace/standardize values** — `replace_values` / `bulk_replace` after \
case is uniform
5. **Strip formatting** — `replace_values` to remove $, commas, parentheses \
from number columns
6. **Convert types** — `convert_type` AFTER text is clean (dirty text → NULL)
7. **Handle missing values** — `fill_missing` or `set_values` for defaults
8. **Remove duplicates** — `discard_duplicates` last, since earlier fixes may \
resolve apparent duplicates
9. **Aggregate** — `pivot` always last (reshapes the data)

### Null Handling Implications
- NULLs are excluded from AVG calculations (divisor shrinks)
- COUNT(*) counts all rows; COUNT(column) excludes NULLs
- NULLs don't match in joins — null keys on either side won't join
- `fill_missing` only fills from adjacent rows — isolated NULLs may persist
""",
    "ai_transform": """\
# ai_transform — AI-Powered Column Generation

## What It Does
Uses an **OpenAI LLM** to generate a **new column** based on a natural language \
prompt and existing column data. The AI reads each row's context columns and \
produces a value for the new column. Null inputs produce null outputs.

## Prerequisite
Requires an **OpenAI API key** configured in the Mammoth workspace settings \
(Settings → Integrations → OpenAI). Without it, ai_transform calls will fail.

## Limits & Performance
| Metric | Value |
|--------|-------|
| **Max rows** | 50,000 (hard limit) |
| **Simple tasks** (classification, yes/no) | ~30-60 sec per 10K rows |
| **Complex tasks** (generation, multi-sentence) | ~2-5 min per 10K rows |
| **Max context columns** | 20 |

## When NOT to Use (with specific alternatives)

| Task | Use Instead | Why |
|------|-------------|-----|
| Deterministic classification by rules | `set_values` with conditions | Faster, free, predictable |
| Text cleanup (case, whitespace, find/replace) | `text_transform`, `replace_values`, `bulk_replace` | Instant, no API cost |
| Lookup-based enrichment (ID → name) | `lookup` or `join_views` | Exact matching, no hallucination |
| Numeric calculations | `math_transform` | Precise, instant |
| Date extraction | `extract_date` | Native, no cost |
| Simple pattern extraction (area code, domain) | `substring` with regex | Reliable, no API cost |

Use `ai_transform` ONLY when the task requires language understanding, fuzzy \
matching, or creative generation that structured tools cannot handle.

## Prompt Engineering Best Practices

### Be specific and constrain output values
**Bad**: "Categorize this product"
**Good**: "Classify the product into exactly one of: Electronics, Clothing, \
Food, Home, Other. Output only the category name."

### Provide examples in the prompt
"Classify the customer feedback as Positive, Negative, or Neutral. \
Examples: 'Great service!' → Positive, 'Terrible experience' → Negative, \
'It was okay' → Neutral."

### Specify output format explicitly
"Extract the city name from the address. Return only the city name with no \
extra text. If no city is found, return 'Unknown'."

### Include only necessary context columns
More columns = slower + more expensive. If classifying sentiment of a review, \
include only the review column, not the product ID or timestamp.

## Common Use Cases

### 1. Sentiment Analysis
- **Prompt**: "Analyze the sentiment of the review text. Output exactly one of: \
Positive, Negative, Neutral."
- **Context columns**: ["Review Text"]

### 2. Geographic Enrichment
- **Prompt**: "Based on the city and state, return the US region: Northeast, \
Southeast, Midwest, Southwest, West."
- **Context columns**: ["City", "State"]

### 3. Categorization
- **Prompt**: "Classify this transaction description into one category: \
Groceries, Dining, Transportation, Entertainment, Utilities, Healthcare, Other."
- **Context columns**: ["Transaction Description", "Merchant Name"]

### 4. Content Generation
- **Prompt**: "Write a one-sentence product description based on the product \
name and features. Keep it under 20 words."
- **Context columns**: ["Product Name", "Features"]

### 5. Data Standardization
- **Prompt**: "Standardize the company name to its official form. For example, \
'MSFT' → 'Microsoft', 'AMZN' → 'Amazon'. If unknown, return the original value."
- **Context columns**: ["Company Name"]

## Testing Pattern (recommended for all AI transforms)
1. `limit_rows(n=100)` — reduce to a small sample
2. `ai_transform(...)` — apply and verify results with `get_data`
3. If results look good: `delete_task` (the ai_transform) → `delete_task` \
(the limit_rows) → re-apply `ai_transform` on the full dataset
4. If results are wrong: `delete_task` both, refine prompt, repeat

## Batching Pattern (for datasets > 50K rows)
1. `filter_rows` to select a batch (e.g., rows where Region = "East")
2. `ai_transform` on the filtered subset
3. `delete_task` to remove the filter (keeps the AI column)
4. Repeat for remaining batches

## Error Handling
- If the AI produces unexpected results, use `delete_task` to undo and refine \
your prompt.
- If the task fails, check that the OpenAI API key is configured and the view \
has ≤50K rows.
""",
    "sql_query": """\
# sql_query — SQL-Powered Transformations

## Two Modes

### Intent Mode (natural language → SQL)
Describe what you want in plain English. Mammoth auto-generates DuckDB SQL and \
applies it to the view. Takes ~20 seconds for SQL generation.

```
sql_query(view_id=V, intent="Show the top 10 customers by total revenue, with their order count")
```

### Raw SQL Mode (direct DuckDB SQL)
Write DuckDB SQL directly. Reference columns by **display name** — enclose \
names with spaces in double quotes. The table is always called `dataview`.

```
sql_query(view_id=V, raw_sql="SELECT \\"Customer Name\\", SUM(\\"Order Total\\") as revenue FROM dataview GROUP BY \\"Customer Name\\" ORDER BY revenue DESC LIMIT 10")
```

**Must provide exactly one** of `intent` or `raw_sql` (not both).

## When SQL Beats Structured Tools

Use `sql_query` instead of chaining 4+ structured tools:

| Scenario | Why SQL wins |
|----------|-------------|
| Complex CASE WHEN with many branches | One SQL statement vs. multiple `set_values` calls |
| Nested subqueries or CTEs | Cannot express with structured tools |
| GROUP BY + HAVING + ORDER BY | One step vs. pivot + filter + sort |
| Deduplicate and keep most recent | ROW_NUMBER() + filter — see pattern below |
| Conditional aggregation | CASE WHEN inside SUM/COUNT |
| Multiple aggregations with different filters | Filtered aggregates in one query |

## Key Patterns

### Deduplicate and keep most recent (very common)
```sql
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY "Customer ID"
    ORDER BY "Date" DESC
  ) as rn
  FROM dataview
)
SELECT * FROM ranked WHERE rn = 1
```

### Month-over-month growth
```sql
WITH monthly AS (
  SELECT date_trunc('month', "Date") as month,
         SUM("Revenue") as revenue
  FROM dataview
  GROUP BY 1
)
SELECT month, revenue,
       LAG(revenue) OVER (ORDER BY month) as prev_revenue,
       ROUND((revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month) * 100, 1) as growth_pct
FROM monthly
ORDER BY month
```

### Conditional aggregation
```sql
SELECT "Region",
       SUM(CASE WHEN "Status" = 'Completed' THEN "Revenue" ELSE 0 END) as completed_revenue,
       SUM(CASE WHEN "Status" = 'Pending' THEN "Revenue" ELSE 0 END) as pending_revenue,
       COUNT(DISTINCT "Customer ID") as unique_customers
FROM dataview
GROUP BY "Region"
```

### Top N per group
```sql
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY "Category"
    ORDER BY "Revenue" DESC
  ) as rn
  FROM dataview
)
SELECT * FROM ranked WHERE rn <= 3
```

## DuckDB SQL Dialect Reference

### String Functions
- Concatenation: `||` or `concat(a, b, c)`
- Case: `upper()`, `lower()`, `initcap()`
- Pattern: `LIKE`, `ILIKE` (case-insensitive), `regexp_matches(col, pattern)`
- Extract: `substring(col, start, length)`, `split_part(col, delim, index)`
- Trim: `trim()`, `ltrim()`, `rtrim()`
- Replace: `replace(col, old, new)`

### Date Functions
- Current: `current_date`, `current_timestamp`
- Extract: `extract(year FROM date_col)`, `date_part('month', date_col)`
- Arithmetic: `date_col + INTERVAL '30 days'`, `date_diff('day', start, end)`
- Truncate: `date_trunc('month', date_col)`
- Format: `strftime(date_col, '%Y-%m-%d')`

### Aggregate Functions
`SUM`, `AVG`, `COUNT`, `MIN`, `MAX`, `COUNT(DISTINCT ...)`, `STRING_AGG`, \
`MEDIAN`, `PERCENTILE_CONT`, `STDDEV`, `VARIANCE`

### Window Functions
`ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `NTILE(n)`, `LAG()`, `LEAD()`, \
`FIRST_VALUE()`, `LAST_VALUE()`, `SUM() OVER()`, `AVG() OVER()`

### Other Key Features
- **CTEs**: `WITH cte AS (SELECT ...) SELECT ... FROM cte`
- **Subqueries**: In SELECT, FROM, WHERE
- **CASE WHEN**: `CASE WHEN condition THEN value ELSE default END`
- **GROUP BY + HAVING**: Full support
- **Set operations**: `UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`
- **NULL handling**: `COALESCE()`, `NULLIF()`, `IS NULL`, `IS NOT NULL`
- **Type casting**: `CAST(col AS INTEGER)`, `col::VARCHAR`
- **No stored procedures or UDFs** — single-statement queries only.

## Intent Mode Tips
- Be specific: "Count orders per customer" > "Analyze orders"
- Name columns explicitly: "Group by \\"Product Category\\" and sum \\"Revenue\\""
- State exact conditions: "where \\"Order Date\\" >= '2024-01-01'"
- Specify output: "Show customer name, total orders, and average order value"

## Performance Notes
- Intent mode takes ~20 seconds for generation (one-time cost per query).
- Raw SQL mode applies immediately.
- Both create a pipeline task that can be undone with `delete_task`.
- SQL operates on the full dataset — no row limit like `ai_transform`.
""",
    "workflows": """\
# Multi-Step Workflow Patterns

Proven patterns from 200+ production pipelines (avg 22.6 steps per pipeline). \
Use these as templates for complex tasks.

## The Pipeline Planning Process

1. **Inspect**: `get_view` → `get_data` (sample 100-200 rows) → understand \
column types, value patterns, data quality
2. **Plan**: For complex tasks (5+ steps), clone first: \
`create_view(clone_from=original_view_id)`
3. **Execute**: Apply transformations in dependency order (see below)
4. **Verify after every structural change**: Call `get_view` after join, \
pivot, split, combine, convert_type to refresh column names. Call `get_data` \
after critical steps.
5. **Check row_count after joins**: Unexpected increase = many-to-many key issue

## Default Pipeline Architecture (optimal ordering)

1. **Filter** — reduce rows early (date ranges often cut 90%+ of data)
2. **Clean types** — `convert_type` (enables all subsequent operations)
3. **Standardize** — `text_transform`, `bulk_replace` (clean values before grouping)
4. **Enrich** — `join_views`, `lookup` (add data from other views)
5. **Calculate** — `math_transform`, `window` (derive new metrics)
6. **Aggregate** — `pivot`, `crosstab` (ALWAYS last — reshapes data)

## Hard Dependency Rules

Violating these causes errors or wrong results:

- `replace_values` (strip formatting) → BEFORE `convert_type` (TEXT→NUMERIC)
- `convert_type` (TEXT→DATE) → BEFORE `extract_date`, `date_diff`, `increment_date`
- `convert_type` (TEXT→NUMERIC) → BEFORE `math_transform`
- `text_transform` (normalize case) → BEFORE `bulk_replace` (more effective)
- `bulk_replace` (standardize values) → BEFORE `pivot` (prevents fragmented groups)
- `discard_duplicates` → BEFORE `pivot` (duplicates inflate counts/sums)
- Join/lookup completes → BEFORE referencing joined columns

## When to Use SQL Instead of Chaining Tools

- 4+ structured tools for one logical operation → `sql_query`
- Complex CASE WHEN with many branches → `sql_query`
- Nested subqueries or CTEs → `sql_query`
- "Deduplicate and keep most recent" → `sql_query` with ROW_NUMBER
- See `get_help("sql_query")` for patterns

---

## Pattern 1: Data Cleaning Pipeline

**Scenario**: Dirty CSV → analysis-ready dataset

1. `text_transform(columns=[all text cols], trim=true)` — remove whitespace
2. `text_transform(columns=[categorical cols], case="TITLE")` — normalize case
3. `bulk_replace(columns=["Company"], mapping=[...])` — standardize variations
4. `replace_values(columns=["Revenue"], find="$", replace="")` — strip formatting
5. `replace_values(columns=["Revenue"], find=",", replace="")` — strip commas
6. `convert_type(conversions=[{"column":"Revenue","to":"NUMERIC"}, \
{"column":"Order Date","to":"DATE"}])`
7. `discard_duplicates()` — remove exact duplicates
8. `fill_missing(column="Region", direction="LAST_VALUE")` — fill blanks

**Verify**: `get_view` (check types changed) → `get_data` (check values)

## Pattern 2: Time-Series Analysis

**Scenario**: Transaction dates as text → time-based analytics

1. `convert_type(conversions=[{"column":"Date","to":"DATE"}])`
2. `extract_date(column="Date", component="month", new_column="Month")`
3. `extract_date(column="Date", component="year", new_column="Year")`
4. `window(function="SUM", column="Revenue", partition_by=["Year","Month"], \
order_by=[["Date","ASC"]], range_type="RUNNING", new_column="Running Total")`
5. `pivot(group_by=["Year","Month"], \
aggregations=[{"column":"Revenue","function":"SUM","as":"Monthly Revenue"}])`

**Verify**: After step 1 (check no NULLs from failed conversion), after \
step 4 (running totals make sense), after step 5 (monthly structure correct)

## Pattern 3: Multi-Table Enrichment

**Scenario**: Orders + Customers + Products → denormalized reporting view

1. `get_view` on all 3 views — verify join key columns exist and types match
2. `join_views(foreign_view_id=customers_view, join_type="LEFT", \
on=[{"left":"Customer ID","right":"Customer ID"}], \
select=["Customer Name","Region"])`
3. `get_view` — verify new columns, check row_count (should not explode)
4. `join_views(foreign_view_id=products_view, join_type="LEFT", \
on=[{"left":"Product ID","right":"Product ID"}], \
select=["Product Name","Category"])`
5. `get_view` — verify again
6. `math_transform(expression="Quantity * Unit Price", new_column="Line Total")`
7. `pivot(group_by=["Region","Category"], \
aggregations=[{"column":"Line Total","function":"SUM","as":"Total Sales"}])`

## Pattern 4: Customer Segmentation (RFM)

**Scenario**: Transaction data → customer segments

1. `convert_type` if needed (dates, amounts)
2. `date_diff(start="Last Purchase Date", end=current_date, component="DAY", \
new_column="Recency")`
3. `window(function="COUNT", partition_by=["Customer ID"], \
new_column="Frequency")`
4. `window(function="SUM", column="Amount", partition_by=["Customer ID"], \
new_column="Monetary")`
5. `set_values(new_column="Segment", values=[` \
`{"value":"VIP","condition":{"logic":"AND","conditions":[` \
`{"column":"Frequency","operator":"GTE","value":10},` \
`{"column":"Monetary","operator":"GTE","value":5000}]}},` \
`{"value":"Regular"}])`
6. `pivot` for summary by segment

## Pattern 5: Financial Report Preparation

**Scenario**: Raw financial data → report-ready aggregations

**Phase 1 — Clean**:
1. `replace_values(columns=["Revenue","Cost"], find="$", replace="")`
2. `replace_values(columns=["Revenue","Cost"], find=",", replace="")`
3. `replace_values(columns=["Revenue","Cost"], find="(", replace="-")`
4. `replace_values(columns=["Revenue","Cost"], find=")", replace="")`

**Phase 2 — Convert**:
5. `convert_type(conversions=[{"column":"Revenue","to":"NUMERIC"}, \
{"column":"Cost","to":"NUMERIC"}])`

**Phase 3 — Calculate**:
6. `math_transform(expression="Revenue - Cost", new_column="Margin")`
7. `math_transform(expression="Margin / Revenue * 100", new_column="Margin %")`

**Phase 4 — Aggregate**:
8. `pivot(group_by=["Account","Period"], \
aggregations=[{"column":"Revenue","function":"SUM","as":"Total Revenue"}, \
{"column":"Margin","function":"SUM","as":"Total Margin"}])`

## Pattern 6: Deduplicate and Keep Most Recent

**Scenario**: Multiple records per entity, keep only the latest

**Approach A — SQL (recommended)**:
```
sql_query(view_id=V, raw_sql="WITH ranked AS (SELECT *, ROW_NUMBER() OVER \
(PARTITION BY \\"Customer ID\\" ORDER BY \\"Date\\" DESC) as rn FROM dataview) \
SELECT * FROM ranked WHERE rn = 1")
```

**Approach B — Structured tools**:
1. `window(function="ROW_NUMBER", partition_by=["Customer ID"], \
order_by=[["Date","DESC"]], new_column="Row Rank")`
2. `filter_rows(condition={"column":"Row Rank","operator":"EQ","value":1})`
3. `delete_columns(columns=["Row Rank"])`

## Creative Composition: Workarounds

- **Business days between dates**: `date_diff` (calendar days) → \
`math_transform` (× 5/7 for rough estimate) → optionally join holiday \
calendar → `math_transform` (subtract holidays)
- **Conditional aggregation**: `set_values` to create flag → `filter_rows` \
on flag → `pivot`
- **Running average over N periods**: `window` with RUNNING range_type
- **Preserve originals**: `copy_columns` before destructive ops, \
`delete_columns` at end to clean up helper columns
""",
    "troubleshooting": """\
# Troubleshooting & Common Mistakes

## Things to NEVER Do

- Math on TEXT columns without `convert_type` first → error
- Date operations on TEXT dates → error (CSV dates ALWAYS upload as TEXT)
- Join without checking key types match → empty or wrong results
- `ai_transform` on >50K rows without filtering first → hits limit
- Aggregation (`pivot`) before deduplication → inflated counts/sums
- Overwrite original column without `copy_columns` first → data loss
- Reference column names from BEFORE a join/pivot/split → names change

---

## Type Mismatch Errors (most common failure)

**Symptom**: Tool fails or returns wrong results
**Diagnosis**: Call `get_view` → check column types
**Fix**: `convert_type` before the operation that needs correct type

Common cases:
- "$1,234.56" is TEXT → `replace_values` to strip $ and , → `convert_type` \
to NUMERIC
- "12/31/2024" is TEXT → `convert_type` to DATE (auto-detects common formats)
- Numeric column needs to be TEXT for joining → `convert_type` to TEXT

## Column Name Issues (second most common)

**Symptom**: Tool says "column not found"
**Cause**: Column names changed after join, pivot, split, combine, convert_type
**Fix**: ALWAYS call `get_view` after structural transformations to get fresh \
column names
**Rule**: Never cache or assume column names across multiple tool calls

## Join Issues

**Row count exploded after join**:
- Cause: Join keys not unique on at least one side (many-to-many)
- Diagnosis: Check `row_count` from `get_view` before and after join
- Fix: Deduplicate or aggregate one side before joining

**Mostly NULL values in joined columns**:
- Cause: Key values don't match (different casing, whitespace, or types)
- Fix: Standardize keys first (`text_transform`, `convert_type`) on BOTH views

**Lost rows after join**:
- Cause: Used INNER join when LEFT join was needed
- Fix: Use LEFT join to preserve all rows from the primary view

## Convert Type Issues

**Mostly NULLs after converting TEXT → NUMERIC**:
- Cause: Text contains non-numeric characters ($, commas, parentheses, units)
- Fix: Clean with `replace_values` FIRST → then `convert_type`
- Pattern: `replace_values(find="$")` → `replace_values(find=",")` → \
`convert_type(to="NUMERIC")`

**Mostly NULLs after converting TEXT → DATE**:
- Cause: Date format not auto-detected (uncommon format)
- Fix: Try `sql_query` with explicit CAST and format, or restructure text first

## Aggregation Issues

**Pivot has too many groups / fragmented groups**:
- Cause: Unstandardized values ("Corp", "CORP", "corp" = 3 groups)
- Fix: `text_transform` + `bulk_replace` BEFORE `pivot`

**Window function returns same value for all rows**:
- Cause: Missing or wrong `partition_by`
- Fix: Verify `partition_by` groups data correctly

**Crosstab creates too many columns**:
- Cause: Pivot column has too many distinct values
- Fix: Use `bulk_replace` or `set_values` to reduce categories first

## Condition Syntax Issues

- `IS_EMPTY` / `IS_NOT_EMPTY` → do NOT pass a value parameter
- `IN_LIST` → value MUST be a list: `["a","b"]`, not `"a"`
- Numeric comparisons on TEXT columns → convert first (text "100" < "20")
- Date comparisons → ensure column is DATE type, not TEXT

---

## Recovery Patterns

| Problem | Recovery |
|---------|----------|
| Wrong transformation applied | `delete_task(task_id=N)` to undo |
| Multiple wrong steps | `list_tasks` to see pipeline, `delete_task` from latest backwards |
| Entire pipeline wrong | Clone from original view (`create_view` with `clone_from`), start fresh |
| Column accidentally overwritten | `delete_task` restores the previous state |
| Too many NULLs after convert_type | `delete_task`, clean data first, then re-convert |

## Performance Issues

- **Pipeline running slow** → `filter_rows` early to reduce row count
- **Join very slow** → aggregate the larger view first, then join
- **Too many columns** → `delete_columns` early to reduce memory
- **AI transform slow** → reduce `context_columns` to only necessary ones
""",
}

TOPIC_LIST = ", ".join(f"`{t}`" for t in HELP_TOPICS)


@mcp.tool()
def get_help(topic: str) -> str:
    """Get detailed guidance on a Mammoth topic. Call this before applying \
transformations or analyzing data quality.

    Args:
        topic: One of: overview, transformations, conditions, data_cleaning, \
ai_transform, sql_query, workflows, troubleshooting.
    """
    doc = HELP_TOPICS.get(topic)
    if doc:
        return doc
    return (
        f"Unknown topic '{topic}'. "
        f"Available topics: {TOPIC_LIST}."
    )
