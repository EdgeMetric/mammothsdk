# Typed transformations and drafts

```bash
mammoth schema find "convert type"
mammoth schema find "duplicate"
mammoth schema find "fill missing"
mammoth schema find "join"
mammoth schema get view.transform.join
mammoth view transform OPERATION VIEW_ID --project PROJECT_ID --input INPUT_JSON
```

Every `view transform *` and `view draft *` mutation needs the exact parent
dataset: put `"dataset_id": DATASET_ID` in `--input` (these commands take no
DATASET_ID positional). Without it the command fails closed with
`missing_argument`; it never falls back to project-wide discovery, which on
large projects browses every folder and can 500 or miss the view. Get the
parent from `view list DATASET_ID` (you already know it after upload) or
`view get VIEW_ID` (a read, which may discover it).

Prefer typed operations such as convert-type, fill-missing, replace, join,
lookup, filter and math only when the live schema
lists them. Pick the operation by what it does, not by its name:

- `fill-missing` copies the previous/next row's value into blanks
  (`direction` = `LAST_VALUE` forward-fill or `FIRST_VALUE`). It cannot write a
  literal. To fill blanks with a constant (for example `0`), use `set-values`
  on the existing column with an `IS_EMPTY` condition:

```bash
mammoth view data get VIEW_ID DATASET_ID --project PROJECT_ID   # before: note which rows have a blank revenue, and a few non-blank values
mammoth view transform set-values VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"existing_column":"revenue","values":[{"value":0}],"condition":{"column":"revenue","operator":"IS_EMPTY"}}'
mammoth view data get VIEW_ID DATASET_ID --project PROJECT_ID   # after
```

Compare the two reads: the row count is unchanged, the rows that were blank
now read `0`, and every non-blank value is identical to the before-sample.
If every row now reads `0`, or a non-blank value changed, the condition was
dropped: stop, do not build joins or summaries on this view, and report it.
Use `view data get` (paged, 400 rows per page) for this, not `view preview`
(50 rows), and sample from more than one page on a large view.

- `filter` keeps matching rows by default (`filter_type: "SHOW"`); to drop
  rows, say so: `{"condition":{"column":"units","operator":"LT","value":0},"filter_type":"REMOVE"}`. For each operation, a successful result should contain a returned
task/job reference or updated view envelope; then verify with `view task list`,
`view task get`, `view pipeline items`, or preview according to its schema.

These examples use the released route IDs and input shapes documented by the
command manifest; substitute only observed view IDs and display names:

```bash
mammoth schema get view.transform.convert-type
mammoth view transform convert-type VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"conversions":[{"column":"Amount","to":"NUMERIC"}]}'
mammoth schema get view.transform.math
mammoth view transform math VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"expression":"GDP / Population","new_column":"GDP per capita"}'
```

In a math `expression`, write a multi-word display name bare (`Quantity * Unit
Price`) or quoted (`Quantity * \"Unit Price\"` inside the JSON string).

The released catalog exposes typed dedupe through `schema find duplicate` as
`view.transform.discard-duplicates`. Inspect its optional `ignore_columns`
field before submitting. For a join, verify both schemas and
expected multiplicity:

```bash
mammoth schema get view.transform.discard-duplicates
mammoth view transform discard-duplicates VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"ignore_columns":["ID"]}'
mammoth schema get view.transform.join
mammoth view transform join VIEW_ID --project PROJECT_ID --input INPUT_JSON
```

## What most pipelines look like

These patterns come from how Mammoth pipelines are usually built. Use them
as defaults, and let the user's request override them:

- Keep it short. Most pipelines have one to three steps and touch a few
  columns. Add only the steps the deliverable needs.
- New column or overwrite? `set-values`, `math` and `lookup` take
  `new_column` (add a column) or `existing_column` (replace the values in
  place), never both. Overwriting is as common as adding. If the user said
  "fix", "clean" or "change" a column, use `existing_column`. If they said
  "add", "calculate" or "flag", use `new_column`. If it is not clear, ask.
- Joins are nearly always `LEFT` on one key column. Use `INNER`, `RIGHT`,
  `OUTER` or a key of two or more columns only when the user asks for it or
  the data needs it, and say why in your report.
- Check the key before a join or lookup. Most keys go in without a prep
  step, so a type, case or padding difference shows up as unmatched rows. Read
  both key columns first (`view data get`) and act on `join_check`.
- Date steps (`increment-date`, `extract-date`, and `text` on date columns)
  fail more often than other steps. Before a date step, confirm that the
  column type is `DATE` (`view get`); if it is `TEXT`, run `convert-type`
  first. Check the result on a few rows.
- Convert several columns to the same type in one `convert-type` call (one
  `conversions` entry for each column), not one call for each column.
- Remove duplicates near the end, after the cleanup and joins, so the check
  uses the final columns.
- `filter` also takes a plain-language `prompt` instead of a `condition`.
  Use a `condition` when the rule is exact (a column, an operator, a value).
  Use `prompt` only when the user described the rule in words and no exact
  condition expresses it, then check the kept rows.
- "Top N" means the largest values first. Use the smallest values first only
  when the user says "bottom", "lowest" or "smallest".
- The last step of a pipeline is not a signal that it is finished. Say that
  the work is done only after you verify the deliverable.

## Aggregate or summarise

For a grouped summary (totals per region, counts per status) use the typed
`pivot` when the live schema lists it, or a SQL task. A SQL task must be one
SELECT that names the view as the quoted table `"view:VIEW_ID"` (or its quoted
display name) with display-name columns; unquoted or placeholder table names
(`data`, `__TABLE__`) are rejected with "table name ... not found" or "only
select queries allowed". The result replaces the view's columns: never run it
(or `pivot`) on a view whose rows are still needed; export those rows first
(`view export csv`) and run the summary as the last step, and prefer `pivot`
(proven on release) over a SQL task. Do not build the summary on a
`view create ... "clone_from": VIEW_ID` copy: on release the clone job succeeds
but the copy answers every read with `4DTVW019` and its copied tasks never
execute. A plain `view create DATASET_ID` (no `clone_from`) gives a fresh view
of the raw upload, without the pipeline:

A task must fit the column's type: `replace-values`, `bulk-replace` and the
text operations take TEXT columns, `math` takes NUMERIC. Check `type` in the
`metadata` from `view get` first; the uploader already types `$1,234.56` as
NUMERIC, so strip nothing. When a task does not fit, the CLI answers
`pipeline_reference_error` with the column, the reason and the exact
`view task delete VIEW_ID TASK_ID --yes` that removes it; until then the view
is in `ref_error` and every read of it fails with `4DTVW019`. `convert-type`
changes the column's type when the task really needs the other one.

Every pivot `as_name` must be a display name that does not already exist on
the view (`4DTVW018 Same display name cannot be reused`): to carry a joined
column such as `monthly_target` into the summary, aggregate it under a new
name (`{"column": "monthly_target", "function": "MAX", "as_name": "target"}`)
or use the SQL task with `MAX(monthly_target) AS monthly_target`.

```bash
mammoth schema get view.transform.pivot
mammoth view transform add-sql VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"query":"SELECT region, SUM(amount) AS total_amount, COUNT(*) AS order_count FROM \"view:VIEW_ID\" GROUP BY region"}'
mammoth view data get VIEW_ID DATASET_ID --project PROJECT_ID
```

Read the data back after every value-changing step (`view data get`, or
`view preview`); a task that executed is not proof it changed the rows you
meant, and a join that matched nothing shows nulls, not a filled default. A
join that leaves most rows unmatched is not evidence about the source data
until you have sampled the key column on both sides (`view data get` on
each view) and confirmed an earlier step did not rewrite the key or the
values you are summing.

## How to look at your data

- Schema and types: `view get VIEW_ID DATASET_ID` (exact parent; the
  no-parent form discovers the parent with one request per dataset in the
  project) or `dataset get DATASET_ID`; the `metadata[].display_name` list is
  what every transform input must use. If `view get` ever returns
  `"<unserializable View>"` you are on a CLI older than 2.0.18: rerun with the
  parent, or use `view preview VIEW_ID DATASET_ID` for the column list.
- Rows and values: `view data get VIEW_ID DATASET_ID` (paged) or
  `view preview VIEW_ID` for a sample; use these after every value-changing
  step and before reporting any number.
- What actually ran: `view task list VIEW_ID`, `view task get VIEW_ID TASK_ID`,
  `view pipeline get VIEW_ID` (state, auto_run, executing task).
- Async completion: `job get JOB_ID` / `job wait JOB_ID`.
- Response shapes are not uniform: `dataset get` returns `data.dataset.{...}`,
  `view list` returns `data.dataviews[]`, `view data get` returns rows keyed by
  display name. Read the envelope you got, not the one you expected.

Prefer `pivot` over `add-sql` for a grouped summary when `capabilities.md`
lists it as run on release; `add-sql` replaces every column of the view, so
never run it on a deliverable view.

`add-sql` facts from release: the only table is `"view:VIEW_ID"` (the view
itself; a second view in FROM/JOIN is `5GENR010 only one table allowed` —
join with `view transform join` afterwards); `CASE`, `DATE_TRUNC('month',
col)`, `GROUP BY`, `COUNT(DISTINCT col)` and `UNION ALL` over the same view
work; result columns must be NUMERIC, TEXT or TIMESTAMPTZ (`CAST(x AS DATE)`
is rejected; `CAST(x || '-01' AS TIMESTAMPTZ)` turns a `YYYY-MM` text month
into a date column). A location canonicaliser plus month bucketing plus
per-cell aggregation is one `add-sql` per fact; a mixed-grain table (summary
rows plus one row per entity with NULL measures, for a `countDistinct` card)
is one `UNION ALL`. The worked run is
`docs/capability-evidence/ilg-sim-20260919/SUMMARY.md`.

Reject malformed fields with the structured error envelope and stop rather than
guessing names. Verify exact display names, join multiplicity, math values and
remote task/pipeline readback. Draft submit is not proof all tasks persisted:
discover draft enter/status/submit/discard schemas and reconcile IDs/parents.

## Pipeline, checkpoint and raw task routes

These routes forward release patch bodies that `schema get` shows only as
free-form lists. Observed shapes:

- `view pipeline edit VIEW_ID --input '{"dataset_id":DATASET_ID,"patches":[{"op":"command","path":"discard-changes","value":null}]}'`
  takes exactly one patch; `path` is one of `auto_run`, `run`, `submit-changes`,
  `reset`, `discard-changes`, `suspend`, `restore`, `discard`, `reorder`, and
  the `value` type follows the path (bool for `auto_run`, a reorder spec for
  `reorder`, `null` for commands). Prefer `view draft *` for submit/discard.
- `view task update VIEW_ID TASK_ID --input '{"dataset_id":DATASET_ID,"task_spec":{...}}'`
  sends `{"patches":[{"op":"replace","path":"params","value":task_spec}]}`;
  pass `patches` directly for other paths. Raw `task_spec` bodies use the
  backend param-template shape with internal column names, e.g. COPY is
  `{"COPY":[{"SOURCE":"column_1","AS":{"COLUMN":"Copy","TYPE":"TEXT","INTERNAL_NAME":"column_9"}}],"VERSION":2,...}`;
  prefer the typed `view transform *` commands, which build these for you.
  `view task preview` currently fails on the backend for views with a DATE
  column (`datetime is not JSON serializable`), so do not rely on it.
- `view checkpoint update` sends `{"patches":[{"op":"command","path":"approve","value":null}]}`;
  the release backend answered HTTP 500 to that shape, so treat checkpoint
  approval as unavailable until `checkpoint get` succeeds again.
- `view exportable-config apply` needs the complete object returned by
  `view exportable-config get` (tasks, dependencies, metadata, ...); a partial
  config fails the job with a bare key name instead of a validation message.
- `ai expression generate` accepts `mode` `math` or `metric` only; an invalid
  mode is refused before any request as `invalid_arguments`.
