# ILG rebuild, simulated end to end on release (2026-09-19)

The ILG CLI-rebuild handoff (`ilg-feasibility-20260919.md`) named four
things the CLI had no positive evidence for. This run replays the handoff's
shape on synthetic data with the CLI 2.0.28 working tree against release
ws 4, in projects the run created (57 target, 58 source A, 59 source B), and
checks every number against a key computed from the fixtures with Python.
Nothing outside those projects was touched; project 3 was not read.

`run.jsonl` is the full command log (label, argv, exit, response);
`results.jsonl` the per-command verdicts folded into the matrix;
`fixtures/` the four CSVs (synthetic; the location column carries the raw
spellings and rollup rows the real feeds have).

## Verdict per handoff blocker

| blocker (feasibility review) | outcome |
|---|---|
| C1 cross-project "send" has no proven route | **Closed.** `view export dataset VIEW --yes --input '{"dataset_name": ..., "target_project_id": 57}'` from views in projects 58 and 59 created datasets 114, 119, 120, 121 in project 57. The send is a pipeline export step (`end_of_pipeline: true`): an upstream filter in project 59 re-ran it and the target view re-materialised (347 → 344 rows) with no manual step. |
| C2 add-only next to an existing send | **Closed.** With an existing same-project send (export 6) on the HR view, the cross-project send appended as export 7; `view pipeline items ... {"fields": "__full"}` showed export 6's sequence and execution timestamps unchanged, `reordered: false`. |
| C3 no typed KPI/measure authoring, `countDistinct` unreachable | **Closed via `dashboard canvas save`.** An authored canvas with page-level `focus.kpis` including `{"field": "Employee Ref", "agg": "countDistinct"}` persisted and baked; a derived ratio measure (`canvas.derived`) gives the rate chart; `unit.prefix` on the two money cards only. The raw canvas route bypasses the LLM guard: `dashboard pages add` (guarded) dropped the same `£` prefix with "nothing in this data says which currency". |
| C4 binding read-back thin | **Closed.** `dashboard canvas get` returns `meta.figures` (`p1:kpi:2 → descriptor e17c51b8a68d1ae8`) and `plan.hints.kpis` with the agg per card; `dashboard descriptor-data` evaluates those ids under a `filter_state`. |

## Trap 1 (DISTINCTCOUNT under a date filter), reproduced

Fixture key: 347 absence rows, 111 distinct staff overall; Jan–Mar 2025 has
85 rows, 64 distinct staff, and a per-cell distinct sum of 83.

| card evaluation | value |
|---|---|
| `countDistinct(Employee Ref)`, no filter | **111** |
| same, `filter_state {"Month": ["2025-01-01", "2025-03-31"]}` | **64** |
| after removing one employee upstream in project 59 | **110** |

The table that makes this work is the handoff's own design: 60 spine rows
(Location × Month with every measure) plus one row per (Location, Month,
Employee Ref) with NULL measures — 400 rows, built with one `add-sql`
UNION ALL on the HR view, then the other facts LEFT-joined on a `Join Key`
that only spine rows can match (`loc|month` vs `loc|month#emp`), so no
measure leaks onto the employee rows (checked: 0).

## What each phase used

- **Phase 1 send.** `file upload` ×3 → `view export dataset` (same-project,
  the "existing PowerBI send" stand-in) → `view export dataset ... target_project_id`
  ×3 → `view pipeline items`, `view export list` before/after.
- **Phase 2 conform/join.** `view transform add-sql` per fact (CASE
  canonicaliser, `DATE_TRUNC('month', …)`, `SUM`/`COUNT(*)`/`COUNT(DISTINCT …)`,
  `WHERE Location NOT IN ('', 'Total')`), `view transform join` ×3,
  `view data get` after every step, `view export dataset` (same project) to
  materialise "ILG Consolidated (sim)" (dataset 122 / view 144).
  Totals: Sales 2,513,068.35; Places 11,490; Occupied 9,143; Absence rows 347;
  Monthly Target ×12 = 1,124,820 — all equal to the key.
- **Phase 3 dashboards.** `dashboard create-blank` ×2, `dashboard canvas get`
  → edit → `dashboard canvas save` (KPIs, bar with `measure2`, hbar, derived
  ratio line, table with `columns`, `range` + `multi` filters), `job wait` on
  the bake, `dashboard descriptor-data` with `filter_state`, `dashboard pages
  add --yes --confirm`. Q1-filtered figures: Sales 788,487.70, Occupied 2,189,
  occupancy rate per month 82.79 / 84.52 / 79.30 % (volume-weighted) — key.

## Backend facts learned (recorded in the manifests/recipes)

- `add-sql` is single-view: a second `"view:ID"` in FROM/JOIN → `5GENR010
  "only one table allowed"`. UNION ALL over the same view works.
- `add-sql` result columns must be NUMERIC, TEXT or TIMESTAMPTZ: `CAST(x AS
  DATE)` → `5GENR010 "Invalid column type DATE"`; use `CAST(x AS TIMESTAMPTZ)`
  or `DATE_TRUNC` (both land as DATE in the view).
- A canvas with `pages[]` bakes the *active page's* `focus`/`added`; a
  root-level `focus` is stored but produces no descriptors.
- `AddedFigure.measure` is a string; a `{num, den}` ratio is rejected with a
  pydantic detail — define it in `canvas.derived[]` and reference the id.
- `series` on a derived-measure line was ignored (ungrouped monthly series
  came back). Not investigated further.
- `dashboard pages add` needs `--yes --confirm ID` and runs through the LLM
  guard (unit evidence rule), unlike `canvas save`.
- `--input @file` is not a convention here: pass the path itself or `-`.

## Not covered

- Real ILG feeds, the `.pbix`, and the production pipelines (out of scope by
  instruction). Row volumes here are hundreds, not the 1,138-row spine.
- Twelve facts: three facts and a target table were conformed, not twelve;
  the mechanism does not change with the count.
- Publishing/sharing the dashboards and PDF export (known limitation).

## Fixture left in place

Projects 57 ('ILG sim target': datasets 113, 114, 119–122, dashboards 63,
64), 58 ('ILG sim source A'), 59 ('ILG sim source B') are kept so the
dashboards can be opened. Remove with, in this order:

```bash
mammoth dashboard delete 63 --project 57 --yes --confirm 63
mammoth dashboard delete 64 --project 57 --yes --confirm 64
mammoth project delete 57 --yes --confirm 57
mammoth project delete 58 --yes --confirm 58
mammoth project delete 59 --yes --confirm 59
```
