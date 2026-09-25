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
| Remove columns | Remove Column | `delete-columns` |
| Add columns from another view by matching keys | Join | `join` (`INNER`, `LEFT`, `RIGHT`, `OUTER`) |
| Bring one value per key from another view | Lookup | `lookup` |
| Totals, counts, averages per group | Group & Pivot | `pivot` (replaces the view's columns) |
| A rows-by-columns summary table | Group & Pivot (crosstab) | `crosstab` (writes a new dataset) |
| Turn wide columns into label/value rows | Unpivot | `unnest` |
| Read fields out of a JSON column | Extract JSON | `json-extract` |
| Classify, tag or summarise rows with AI | Generative AI | `ai` |
| One SQL query over the view | AI SQL Query | `add-sql` (replaces the view's columns), `generate-sql` (from plain words) |
| Copy rows into another dataset, refreshed with the pipeline | Send to Dataset | `view export dataset` (not a `view transform`) |

`join` or `lookup`: `join` adds the chosen columns from every matching row
(a key that repeats on the other side repeats rows); `lookup` brings one
value per key into one new column. Before either, confirm the key columns
in both views have the same type and values; recipes/transforms.md has the
read-back.

## Not a pipeline step, and the nearest route

- **Rename a column.** The web app's rename is a display change, not a
  task; the CLI has no rename command. Name new columns when you create them
  (`new_column`, `as_name`); for an existing column, `copy-columns` under
  the new name.
- **Sort.** There is no sort task, and the CLI has no sort command. For
  "top N by X" use `limit-rows` with `order_by`; for a rank column use
  `window` (`RANK`, `ROW_NUMBER`).
- **Union or append two views.** There is no union task. Upload a file into
  an existing dataset with `append_to_ds_id`, or send a view's rows into an
  existing dataset with `view export dataset` (`target_ds_id` and
  `save_as_mode` `APPEND_TO_DS`; that mode is untried on release).
- **Hide or reorder columns.** Display changes in the web app; they do not
  change the data.

## The web app and the CLI

Both call the same API. Do not switch to the web app in a browser for a
task the CLI covers. Before you conclude that the CLI cannot do something,
run `mammoth view transform --help`, search in plain words (`mammoth schema
find "merge two datasets"` finds `join`; a search with no full match lists
`suggestions`), and read the section above. If it is still missing, report
the gap with the command you tried; do not work around it in the browser or
by computing the result locally.
