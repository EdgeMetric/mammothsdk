# What Mammoth is, and what it can do

Read this when the task is stated as a business goal ("combine these files",
"a monthly summary per region", "feed this to Power BI") and you need to know
which Mammoth feature does it, or when you think the CLI cannot do something
the web app can.

## Why Mammoth exists

Mammoth Analytics is a cloud platform that turns raw business data into
output people can trust and that stays current, without code. It has two
layers:

- **Preparation (the engine).** Data comes in from files, URLs or
  connectors. It is cleaned, reshaped, joined and calculated in a
  **pipeline**: an ordered list of tasks on a **view**. The pipeline re-runs
  when new data arrives, so a monthly report is built once and refreshed,
  not rebuilt.
- **Output.** Dashboards (and presentations, documents and Q&A pages) are
  built from a prepared view. Data is also delivered: CSV downloads,
  databases, cloud storage, BI tools, or another Mammoth dataset. Every
  number is computed from the prepared data, never written by a model.

People use it to replace manual spreadsheet work: an analyst automating a
recurring report, a small practice producing client deliverables, a team
feeding clean data to Tableau or Power BI. Every step is visible and
repeatable, which is the point: someone else can inspect, re-run or take
over the work. So, as an agent, build the steps **in Mammoth** (as pipeline
tasks, dashboards and exports) rather than computing a result locally and
uploading it; a local result does not refresh and cannot be inspected.

## How Mammoth organises data

```
workspace            account and billing; an API token belongs to one workspace
└─ project           a container with its own members; work stays inside one
   └─ dataset        data from an upload, URL or connector; each import is a batch
      └─ view        a working copy of the dataset's rows; a dataset can have several
         ├─ pipeline tasks run top to bottom; each `view transform` adds one at the end
         ├─ exports   CSV, databases, cloud storage, BI tools, another dataset
         └─ dashboards built from the view's prepared rows
```

- An upload returns a **dataset** id. Transforms, joins, exports and
  dashboards take a **view** id (`view list DATASET_ID`).
- Columns have a **display name** (what people see, and what every CLI
  input uses) and an internal name (`column_7`), which you never type.
- A task that ran is part of the view: later data refreshes run it again.
  Draft mode (`view draft enter` / `submit`) holds several tasks and runs
  them together.

## What it can do, and where that is in the CLI

| Goal | Web app | CLI |
|---|---|---|
| Bring data in | Data → new dataset | `file upload`, `dataset create` (URL), `connector ...` |
| Add rows to existing data | a new batch on the dataset | `file upload FILE --input '{"append_to_ds_id": DATASET_ID}'` |
| Clean and reshape | View → Transform menu | `view transform OPERATION` (table below) |
| Combine two sources | Transform → Join, Lookup | `view transform join`, `view transform lookup` |
| Summarise | Transform → Group & Pivot | `view transform pivot`, `view transform crosstab` |
| Check data quality in the pipeline | Data Check, Checkpoint Alert | `view data-check create`, `view checkpoint create` |
| Reuse a value or a SQL block | Parameters, Snippets | `parameter ...`, `snippet ...` |
| Inspect or restore pipeline history | Version history | `view version list`, `view version apply` |
| Build a dashboard | Publish | `dashboard create-blank`, `dashboard v3 generate`, `dashboard canvas ...` |
| Deliver data | Export, Send to dataset | `view export csv`, `view export postgres` (and other destinations), `view export dataset` |
| Automate | Automations | `automation ...`, `workflow ...` |
| Undo a delete | Trash | `trash list`, `trash restore` |

Whether a route ran on release is in [capabilities](capabilities.md); read
it before you promise a deliverable. `schedule` is not implemented on
release.

## The Transform menu, command by command

The web app groups its pipeline tasks in a Transform menu. Each data task is
a `mammoth view transform` command; `mammoth view transform --help` lists
them with one line each, and `mammoth schema get view.transform.join` (or
any other operation) gives the input. Send to Dataset is `view export dataset`; Data Check and
Checkpoint Alert are the `view data-check` and `view checkpoint` families.

| You want to | Web app task | Command |
|---|---|---|
| Keep or remove rows that match a condition | Conditional Filter | `filter` (`filter_type` `SHOW` or `REMOVE`) |
| Remove duplicate rows | Remove Duplicate Rows | `discard-duplicates` |
| Keep the first or last N rows by an order | Show Top/Bottom Rows | `limit-rows` (`n`, `order_by`, `bottom`) |
| Write a value where a condition holds, or a label or bucket column | Label & Insert Values | `set-values` |
| Fill blanks with the previous or next row's value | Fill Missing Values | `fill-missing` |
| Find and replace one value | Find & Replace | `replace` |
| Map many spellings to one value | Bulk Replace | `bulk-replace` |
| Change case or trim spaces | Text Formatting | `text` |
| Take part of a text value (characters or regex) | Extract Text | `substring` |
| Split one column into several | Split Into Multiple Columns | `split` |
| Join several columns into one text column | Combine Columns & Text | `combine-columns` |
| Change a column's type | Convert Column Type | `convert-type` |
| Calculate a column from others | Math Function | `math` |
| Rank, running total, previous or next row | Window function | `window` |
| Nth smallest or largest across columns | Obtain Large or Small Values | `small-large` |
| Take a year, month, weekday from a date | Extract Date Part | `extract-date` |
| Days (or months, ...) between two dates | Calculate Date Difference | `date-diff` |
| Shift a date by an interval | Add / Subtract Date Values | `increment-date` |
| Add an empty column | Add Column | `add-column` |
| Copy a column under a new name | Copy Columns | `copy-columns` |
| Rename a column | Rename (column header) | `rename-columns` (a view setting, not a task) |
| Sort the rows | Sort (grid) | `sort` (a view setting, not a task) |
| Remove columns | Remove Column | `delete-columns` |
| Add columns from another view by matching keys | Join | `join` (`INNER`, `LEFT`, `RIGHT`, `OUTER`) |
| Bring one value per key from another view | Lookup | `lookup` |
| Totals, counts, averages per group | Group & Pivot | `pivot` (replaces the view's columns) |
| A rows-by-columns summary table | Group & Pivot (crosstab) | `crosstab` (writes a new dataset) |
| Turn wide columns into label/value rows | Unpivot | `unnest` |
| Read fields out of a JSON column | Extract JSON | `json-extract` |
| Classify, tag or summarise rows with AI | Generative AI | `ai` |
| One SQL query over the view | AI SQL Query | `add-sql` (replaces the view's columns), `generate-sql` (writes the query from plain words; apply it with `add-sql`) |
| Copy rows into another dataset, refreshed with the pipeline | Send to Dataset | `view export dataset` (not a `view transform`) |

`join` or `lookup`: `join` adds the chosen columns from every matching row
(a key that repeats on the other side repeats rows); `lookup` brings one
value per key into one new column. Before either, confirm the key columns
in both views have the same type and values; recipes/transforms.md has the
read-back.

## View settings, and what has no command

Two commands change how the view shows its rows, not the rows. They add no
pipeline task, like their web counterparts (a column-header rename, a grid
sort):

- **Rename a column:** `view transform rename-columns` with `{"renames":
  {"cust_id": "Customer ID"}}`. The column keeps its internal name, so
  earlier tasks keep working; later commands, data reads, exports and
  dashboards use the new name. To name a column you create, use its
  `new_column` or `as_name` field instead.
- **Sort the rows:** `view transform sort` with `{"order_by": [["Revenue",
  "DESC"]]}` (up to three columns; `[]` clears it). Data reads and exports
  return rows in this order. To keep only the top N rows, use `limit-rows`
  with `order_by`; for a rank column, `window` (`RANK`, `ROW_NUMBER`).

No command:

- **Union or append two views.** There is no union task. Upload a file into
  an existing dataset with `append_to_ds_id`, or send a view's rows into an
  existing dataset with `view export dataset` (`target_ds_id` and
  `save_as_mode` `APPEND_TO_DS`). An append is a standing link: it is stored
  as a pipeline step of the source view, so every later re-run of that view
  appends again into the target dataset, not just the first run. To stack
  rows into a brand-new dataset instead of an existing one, omit
  `target_ds_id`. A row present in both sources lands twice: note the
  appended view's `row_count` (`view get`), run `view transform
  discard-duplicates` on it (`ignore_columns` for any column you added per
  source, e.g. a region tag, since it would make shared rows differ), read
  `row_count` again, and report the difference as duplicates removed.
- **Hide or reorder columns.** Display changes in the web app; they do not
  change the data.

## The web app and the CLI

Both call the same API. Do not switch to the web app in a browser for a
task the CLI covers. Before you conclude that the CLI cannot do something,
run `mammoth view transform --help`, search in plain words (`mammoth schema
find "merge two datasets"` finds `join`; a search with no full match lists
`suggestions`), and read "View settings, and what has no command" above.
If it is still missing, report the gap with the command you tried; do not
work around it in the browser or by computing the result locally.
