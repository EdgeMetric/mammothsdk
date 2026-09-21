# ILG rebuild on prague, end to end, with the production procedure (2026-09-21)

The ILG handoff shape (`../ilg-feasibility-20260919.md`, replayed on release
in `../ilg-sim-20260919/`) run again on a second environment,
`prague.mammoth.io` ws 4, with **fresh mock data** and the procedure the real
run will use: `--dry-run` before every write and `expected_task_count` on
every pipeline write. Everything went through the `mammoth` CLI binary (one
subprocess per command); the driver `run.py` only generates the fixtures,
sequences the calls and checks each number against a key it computes from
the fixtures. Projects 4444 (target), 4445 (source A) and 4446 (source B)
were created by the run; nothing else in the workspace was touched and
project 3 was not read.

- `run.jsonl` — 126 commands (label, argv, exit, response), including the
  first attempt that stopped at the `need_action` upload.
- `results.jsonl` — 69 checks, 68 pass; the one "fail" is the driver reading
  `data.status` instead of `data.dataset.status` after `dataset get`
  (the dataset was ready; the next check counted its 302 rows).
- `fixtures/` — the four CSVs (seed 2109; raw location spellings and the
  `Total`/blank rollup rows the real feeds carry); `key.json` the expected
  numbers; `state.json` the ids created.

## What was proven

| step | commands | result |
|---|---|---|
| upload with a platform question | `file upload` → `dataset file-settings get/update` → `dataset get` | prague flags an ISO `YYYY-MM-DD` column as ambiguous (`need_action`); confirming the detected settings plus `date_format` resolved it (≈3 min to `ready` here). Release processed the same file straight to `ready`. |
| add-only cross-project sends | `view export dataset … target_project_id` ×4 after a same-project "existing" send | export 240 (the stand-in for the PowerBI send) kept id, sequence 0, start/end timestamps and `reordered: false` while three sends appended after it. |
| stale precondition | `view transform add-sql … expected_task_count: 1` on a 0-task view | `pipeline_changed`, exit 2, no task added. |
| dry runs | 17 `--dry-run` calls across sends, transforms, joins, canvas save, pages add, upstream filter | every one reported `would_call` with the resolved arguments and left the task count unchanged. |
| conform + join | 4 `add-sql` (CASE canonicaliser, `DATE_TRUNC`, `CAST … AS TIMESTAMPTZ`, UNION ALL mixed-grain), 3 `join` | 60-row spine per fact; consolidated 344 rows = 60 spine + 284 (Location, Month, Employee) rows; Sales 2,053,940.17; Places 13,308; Occupied 11,184; Target ×12 1,126,380; measure leakage onto employee rows 0 — all equal to the key. |
| materialise | `view export dataset` (same project) | dataset 2555 / view 4449, 344 rows. |
| dashboards | `dashboard create-blank`, `canvas get` → edit → `canvas save`, `job wait`, `canvas get` (`meta.figures`), `descriptor-data` | `countDistinct(Employee Ref)` = 98 unfiltered, **55** under `filter_state {"Month": ["2025-01-01","2025-03-31"]}` (key: 55); Q1 sales 501,586.29; occupancy-rate line 83.59 / 76.28 / 85.75 % (key, volume-weighted). Satellite board: 13,308 / 11,184 / 84.04 %. |
| LLM-guarded page | `dashboard pages add --yes --confirm` | page added; guard dropped the `£` prefix again ("nothing in this data says which currency"). Use `canvas save` for units. |
| propagation | `view transform filter` (REMOVE one employee) in source B | source 326 rows; consolidated re-materialised to 341 rows within 40 s; distinct staff 97; sales unchanged. |
| download | `view export csv … {"dataset_id", "output_path"}` | 341 rows on disk. |

## Learnings folded into the CLI

- **Start-up was the CLI's own slowness.** Every invocation parsed 800 KiB of
  manifest YAML with PyYAML's pure-Python loader and converted all ~550
  commands to Click: 2.44 s before the first byte left the machine. CLI 2.0.31
  uses libyaml, caches the parsed manifests as JSON keyed by the files'
  size/mtime, and builds top-level command groups on demand: **0.51 s**.
- **The rest is network and backend.** From this host: TCP 0.35 s, TLS +0.32 s,
  then **1.0–1.3 s server time per request** — the same for
  `GET /workspaces/4/projects` on release and on prague. Recorded, not
  chased (no backend changes). A pipeline write with the production
  procedure (`task list` → dry run → write, each a fresh process) costs
  ≈35 s here; the docs now say so.
- `dataset get` nests the record under `data.dataset` (status at
  `data.dataset.status`); `view export csv` takes `dataset_id` in `--input`,
  not as a second positional. Both are now stated in the recipes.
- Prague's date-ambiguity check is stricter than release's; the
  `need-action.md` recipe already covered it and now states the timing.

## Not covered

Same as the release sim: real feeds, the `.pbix`, production pipelines,
twelve facts (three plus targets here), sharing/PDF. Row volumes are
hundreds.

## Fixture left in place

Projects 4444 (datasets 2551–2555, dashboards 526, 527), 4445 (datasets
2545 — the first, unresolved upload — and 2546), 4446 (datasets 2547–2550)
on prague ws 4 are kept so the boards can be opened. Remove with:

```bash
mammoth dashboard delete 526 --profile prague --project 4444 --yes --confirm 526
mammoth dashboard delete 527 --profile prague --project 4444 --yes --confirm 527
mammoth project delete 4444 --profile prague --yes --confirm 4444
mammoth project delete 4445 --profile prague --yes --confirm 4445
mammoth project delete 4446 --profile prague --yes --confirm 4446
```
