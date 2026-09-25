---
name: mammoth-cli
version: 2.0.46
description: "Use Mammoth Analytics from a terminal: install or authenticate the CLI, discover its live command contract, and safely manage projects, data, views, pipelines (join, merge, pivot, filter, clean), dashboards, exports, and handoffs."
---

# Mammoth CLI

Use this skill for Mammoth shell work, not for Python SDK integration. The
CLI is the contract: it validates every request locally, returns one JSON
envelope, and needs no flag for that when you pipe its output.

## What Mammoth is

Mammoth Analytics is a no-code data platform. Data comes in from files, URLs
or connectors and lands in a **dataset**. It is cleaned, joined, reshaped and
calculated in a **pipeline** of tasks on a **view**, and the result is
published as a dashboard or delivered as a CSV, a database table, a BI feed
or another dataset. The pipeline re-runs when new data arrives, so build the
steps in Mammoth rather than computing a result locally. The web app and
this CLI call the same API: every task in the web app's Transform menu is a
`mammoth view transform` command. The data model, the high-level
capabilities and the full web-to-CLI map are in
[about Mammoth](references/about-mammoth.md).

## Start

```bash
mammoth doctor                          # auth, endpoint, connectivity, version; must succeed
mammoth project ensure 'PROJECT NAME'   # get-or-create; becomes the active project
```

`doctor` failing is a precondition failure, not a reason to try the business
command anyway. When the connection check fails with a 502, 504 or timeout,
`mammoth doctor --input '{"wait": 300}'` probes again for up to that many
seconds; go on only when it passes. Production is the `app` endpoint; use `release` only when the
task names it, and check `meta.profile`/`auth status` `endpoint` match the
intended environment before doing anything. If no profile has credentials,
tell the operator to run `mammoth auth login` in their own terminal (add
`--profile NAME` only for a profile other than `default`; [auth](references/auth.md)
says where the token comes from) and wait; never ask for the token in chat,
never read one from a file or environment variable, never run `auth login`
yourself. If any envelope carries `meta.update_available`, run its `command`
before the next step.

## Defaults you do not repeat

- Piped stdout is compact JSON and prompts are off. Only in a session that
  is not piped, `export MAMMOTH_OUTPUT=json MAMMOTH_NO_INPUT=1` once.
- `project ensure` saves the active project; `--project` only overrides it.
  `MAMMOTH_PROFILE` / `MAMMOTH_PROJECT` also work as session defaults.
- The CLI remembers which dataset owns each view from any read (`view list
  DATASET_ID`, `view get VIEW_ID`, an upload). After that, no `dataset_id`
  on transforms, exports or deletes. If a command asks for the parent
  `DATASET_ID`, read the view once and repeat it; an explicit value always
  wins.
- Commands that start platform work wait up to 300 s for the job; on
  `timeout` use the `job get` recovery command printed, do not resubmit.

## Find the command for a goal

State the goal in plain words; the search knows common phrasing, and
`view transform --help` is the Transform menu with one line per task:

```bash
mammoth schema find "merge two datasets"   # -> view.transform.join
mammoth view transform --help              # every data transformation
```

| Goal | Command |
|---|---|
| Combine two datasets on a key (merge, VLOOKUP) | `view transform join`; one value per key: `view transform lookup` |
| Add rows to an existing dataset | `file upload FILE --input '{"append_to_ds_id": DATASET_ID}'` |
| Keep or remove rows | `view transform filter` |
| Remove duplicate rows | `view transform discard-duplicates` |
| Totals, counts, averages per group | `view transform pivot` |
| A calculated column | `view transform math` |
| Blanks to a constant, or to the previous row's value | `view transform set-values` (`IS_EMPTY`), `view transform fill-missing` |
| Clean text | `view transform text`, `replace`, `bulk-replace` |
| Change a column's type | `view transform convert-type` |
| Rename a column, sort the rows (view settings, not tasks) | `view transform rename-columns`, `view transform sort` |
| Rank, running total, previous row | `view transform window` |
| A dashboard | `dashboard create-blank` ([dashboards](references/recipes/dashboards.md)) |
| Deliver the rows | `view export csv`, `view export postgres` (and other destinations), `view export dataset` |
| Run something on a schedule or on new data (refresh, append, alert) | `automation create`: a condition (`at_specific_time`, new file in a folder, ...) and tasks (`run_data_retrieval`, `append_data`, `send_an_alert`, `pull_cloud_files`). `schedule create` only pulls a connector's data. A dataset made from an uploaded file has no source to refresh from; say so. Full recipe, including a known `automation get` backend caveat: [recurring work](references/recipes/scheduling.md) |

A search with no full match returns `suggestions` and a `hint`. Before you
conclude the CLI cannot do something the web app does, check
`view transform --help` and "View settings, and what has no command" in
[about Mammoth](references/about-mammoth.md). Do not switch to the web app
in a browser, or compute the result locally, for work the CLI covers;
report a real gap with the command you tried.

## Several files, one deliverable

Users often upload related files without saying how they relate ("make a
dashboard from t_a and t_b"). Work it out from the data before you build:

1. Upload every file. Each upload result carries a `view` preview of what
   Mammoth made of the file (`view_id`, column types, sample rows,
   `column_warnings`, and `before_dashboard`). Do not open the local files
   (`cat`, `head`): what counts is what Mammoth made of them. Run `view data
   get VIEW_ID` for each view. The warnings list numbers or dates stored as
   text, and blanks, each with the fix.
2. Find the keys. A column in one view whose values appear in a column of
   the other (`customer_id` and `id`, `order_ref` and `order_no`) is a
   foreign key; the view with many rows per key is the main one.
3. Make the keys match before the join: same type (`convert-type`), same
   case and padding (`text`), no blanks (`set-values`, `filter`).
4. Act on every `column_warnings` entry for a column the deliverable uses:
   run its `fix` (`convert-type` to `NUMERIC` or `DATE`; the values that are
   not numbers become empty). A text `price` cannot be summed on a dashboard.
   Then decide on each `blank_values` entry: fill, filter, or keep. Write one
   line for each in your report (the column, the count, what you did and
   why). A blank that you saw but did not mention is a miss.
5. `view transform join` the lookup view into the main view (`LEFT`). The
   result's `join_check` gives `match_rate`, `unmatched_rows` and
   `unmatched_keys`; put them in your report, and stop to compare the keys
   if more than a few rows found no match.
6. If the data has money, add it before you make the dashboard: `revenue`
   (`math`, `qty * price`, `new_column`), the `fix` in `before_dashboard`.
   A dashboard sees only the columns the view had when it was made.
7. Build the dashboard from the joined view
   ([dashboards](references/recipes/dashboards.md)) and chart the sum of
   revenue. Do not sum a unit price. `create-blank`, `canvas save` and
   `pages add` return `deliverable_check`: fix each warning, or say in the
   report why not.

For the defaults that most pipelines use (new column or overwrite, `LEFT`
joins, date steps), see
[transforms](references/recipes/transforms.md#what-most-pipelines-look-like).
Say what you inferred (which columns you joined on, what you converted) in
your report. If no column links the files, ask before you combine them.

## Calling a command

- Ids are positionals; request fields are one `--input '{...}'` document;
  there are no per-field flags (`project create NAME`, not `--name`).
- `mammoth skill show --input '{"file": "references/recipes/transforms.md"}'`
  prints any file of this skill; `mammoth skill agents-md install` writes a
  steering block into a repository's AGENTS.md so later sessions start here.
- `COMMAND --help` lists the input fields with types; `mammoth schema get
  COMMAND_ID` is the full contract (add `--input '{"full": true}'` for the
  JSON Schema); `schema list` is the family index, `schema list view` one
  family, `schema find WORDS` a search.
- Uploads return a **dataset** id; transforms, joins, exports and previews
  take the **view** id from `view list DATASET_ID`.
- `view list` and `view get` return the brief record (id, ds_id, name,
  status, row_count, `metadata` columns and types, pipeline state);
  `view get ... --input '{"fields": "__full"}'` or `view list ... --input
  '{"full": true}'` returns the dependency and display trees too.
- Column inputs and expressions use the exact **display names** the view
  returns, never backend aliases.
- `--dry-run` on any API-backed command resolves everything and reports the
  request instead of sending it; use it before a write you are not sure of.
- Deletes need `--yes`; high-impact ones (`project delete`, access changes)
  also need `--confirm ID`, and `schema get` shows which. Preserve requested
  deliverables; cleanup is exact-ID authorized and
  never means delete-all-owned-resources: delete only ids this run created,
  one per call, and read back that they are gone.
- A command whose schema lists `secret_fields` takes `--input FILE` (mode
  0600); secrets never go in argv, notes, checkpoints or replies.

## Verify before you report

- A success envelope proves the call, not the outcome. After a row-scoped
  change (set-values, filter, replace, join, fill) run `view data get
  VIEW_ID` (50 rows by default, `limit` to change) and check rows the
  condition should have touched and rows it should not have. Sample the
  target column *before* the change so the after-read has a comparison.
- A uniform result (every amount 0, every region "Unknown", most join rows
  unmatched) means the previous step went wrong; stop and re-inspect it.
- `column_warnings` on a data read and `join_check` on a join are findings,
  not decoration: fix each one the deliverable depends on, or say in the
  report why you kept it. `view data get` pages with `{"offset": 51,
  "limit": 50}`.
- A timeout, exit 7 or interruption does not prove failure; reconcile an
  `outcome_unknown` (`job get`, `view task list`) before replaying.
- Before you report, run `mammoth project check PROJECT_ID`. Its `to_report`
  has one line for each open finding in every view and dashboard (blanks,
  text numbers, money not shown, columns a dashboard cannot see). Fix each
  one, or give it one line in the report.
- Run the [report checklist](references/report-checklist.md) before stating
  a number or calling a step done. When files here disagree,
  [capabilities](references/capabilities.md) wins over a recipe, and a recipe
  over the generated command catalog.

## Route only what the task needs

- **What Mammoth is, its data model, which feature fits a business goal, or
  a web-app task you cannot find in the CLI:** [about Mammoth](references/about-mammoth.md)
- **Cold start, task plan, or unsupported route:** [task start](references/task-start.md)
- **Login, profiles, and authorized scope:** [auth](references/auth.md)
- **Nested input, output envelopes, confirmations, jobs, or recovery:**
  [input](references/input.md), [machine output](references/machine-output.md),
  [safety](references/safety.md), or [jobs and drafts](references/jobs-drafts.md)
- **Import, resources, transforms, pipelines, dashboards, exports, or cleanup:**
  [recipes](references/recipes/index.md) — the
  [worked example](references/recipes/end-to-end.md) is the whole flow
- **Which id is which, appending rows, response shapes, and other one-off
  rules:** [operations](references/operations.md)
- **Something failed or you are unsure whether to continue:**
  [recovery](references/recovery.md) — failure modes by message and the
  stop-condition list
- **A known command family or exact command:** [command catalog](references/command-index.md)
  — a lookup for the one command you need, not upfront reading; each entry
  carries its release status line, and a `not supported` or `observed
  blocker` entry names the route to use instead
- **Whether a route is proven, known-blocked, or untried on release:**
  [capabilities](references/capabilities.md) — read it before promising a
  deliverable or reporting a failure as a backend fault
- **Pause or transfer to another agent:** [handoff](references/handoff.md)

## Handoff checklist

Before yielding work, write a nonsecret checkpoint with the intent and
acceptance criteria; authorized profile/workspace/project; observed resource
parents; verified evidence hashes; known jobs and unknown outcomes; remaining
objectives; and exact cleanup ownership. The receiving agent validates that
record and re-reads remote state before deciding what to do next. The handoff
is not a resume command or a grant of authority.
