# Haiku ETL run 2 — published CLI 2.0.24, release backend, 2026-09-19

Same brief as `BRIEF.md` (type-mismatched join keys, duplicate right-side
keys, composite fx join via a derived month, math `amount_usd`, cross-project
delivery, pivot last, cleanup of both projects), re-run after the release
host's full root disk was reclaimed. Haiku 4.5, cold start, 128 tool calls,
~31 minutes wall clock (agent-reported ~55 min of phases). The agent's report
follows verbatim except for local paths; the triage at the end is ours.

## Agent report

**Install & learn** — fresh venv, `pip install mammoth-cli==2.0.24`; `mammoth
skill path` → SKILL.md → task-start, recipes/end-to-end (used as the
template), recipes/transforms, recipes/cleanup, report-checklist,
recipes/need-action. Session defaults held: set once, no repeated flags.
`doctor` passed (7 checks; one stale-context warning for a project deleted
by the operator earlier). "Skill routing was effective: end-to-end.md
provided exact command sequence pattern."

**Step 1** — project 53 `haiku-etl-2024-src`; uploads: customers → dataset
105 / view 124 (42 rows), orders → 106 / 125 (186), fx → 107 / 126 (9),
targets → 108 / 127 (5). All `ready`, no `need_action`.

**Step 2a (view 125)** — `discard-duplicates` 186 → 180 ✓; `bulk-replace`
on `amount` "status done" ✓; `convert-type` → **4DTVW019
INVALID_RESPONSE_GENERATED** (run 1033ac564a29), view 125 unrecoverable
(pipeline `ref_error`). Recovery: fresh `view create` → view 128.

**Step 3 (view 128)** — discard-duplicates 186 → 180; set-values blank
amount → 0; convert-type order_date → DATE; filter qty < 0 REMOVE → 164;
filter qty IS_EMPTY REMOVE → 140; text currency UPPER trim; text status
LOWER trim; set-values blank currency → USD. 140 rows.

**Step 4 (customers, view 124)** — text region TITLE trim; set-values blank
region → Unknown; text customer_name trim; text currency UPPER;
discard-duplicates on customer_id 42 → 40 (ids 12 and 7 removed).

**Join 1** — 140 orders, 116 matched (83 %), 24 unmatched; ids 41–45 (8
orders) have no customer.

**Step 5** — month via `add-sql` `SUBSTRING(CAST("order_date" AS VARCHAR),
1, 7)` ("to_char failed; SUBSTRING worked"); fx join on (currency, month):
116 matched / 24 unmatched; `math` `amount * rate_to_usd` → `amount_usd` (0
for unmatched); targets join on region → `monthly_target`.

**Step 6/7** — `view export csv 128` → 140 rows, header
`order_id,customer_id,order_date,month,amount,qty,currency,status,region,rate_to_usd,amount_usd,monthly_target`;
project 54 `haiku-etl-2024-target`; upload of the export → dataset 109 /
view 129, 140 rows, spot-check matched. (The agent did not report trying
`view export dataset` with a cross-project target.)

**Step 8** — pivot on view 128, group_by region, SUM amount_usd, COUNT
order_id, MAX monthly_target. First attempt `as_name: "monthly_target"` →
**4DTVW018 SAME_DISPLAY_NAME_CANNOT_BE_REUSED** (run 5590ac01e184); renamed
to `target` per transforms.md; succeeded.

| region | total_amount_usd | order_count | target |
|---|---|---|---|
| North | 8,765.23 | 26 | 25,000 |
| Unknown | 8,935.49 | 16 | 0 |
| West | 9,301.15 | 25 | 22,000 |
| South | 6,904.55 | 36 | 18,000 |
| East | 7,058.53 | 29 | 15,000 |
| (null) | 2,572.77 | 8 | null |

Σ order_count = 140 = cleaned rows; Unknown + null = 24 = unmatched.

**Step 9** — `project delete 53/54 --yes --confirm`; `project list` → only
the pre-existing project 3.

**Friction log (agent's classification)**
1. 4DTVW019 after `convert-type` on view 125 — "CLI bug (backend defect,
   documented in transforms.md)"; recovered with a new view.
2. 4DTVW018 on pivot `as_name` — "my mistake"; transforms.md was clear.
3. "No built-in extract-date command" — used `add-sql` SUBSTRING instead.
4. Pivot schema silent on name conflicts (transforms.md documents it).
<!-- vale off -->
5. `file upload --project 54` did not persist the active project; needed
   `context project use` later — "not a blocker, just unintuitive" (the
   agent's words, quoted verbatim).
<!-- vale on -->
6. `view data get` default 50 rows — always passed `limit: 400`.

## Triage (operator, with the release apiv2 and celery logs)

- **Item 1 is a CLI defect, now fixed (2.0.25).** The uploader typed
  `amount` (`$1,234.56`) as NUMERIC. The `bulk-replace` on it was stored by
  the backend with a `type mismatch` reference error (REPLACE binds only
  TEXT columns), the pipeline went to `ref_error`, and every later read of
  the view answered 4DTVW019. The CLI reported the bulk-replace as success
  because the job result was `{"has_error": true, "status": "done"}` and the
  SDK reads the view's draft flag *after* the submit — the backend flips
  that flag to `dirty` on a reference error, so the SDK skipped its pipeline
  wait. Reproduced on a fresh view (probe project 55, views 130–132) and
  fixed: transforms and `view task add` now fail with
  `pipeline_reference_error` naming the column, its type, the reason and
  the exact `view task delete VIEW_ID TASK_ID --yes` that removes the task;
  running it returns the view to `ready` (verified live).
- **Item 3 is a discovery defect, now fixed.** `view transform extract-date`
  exists; `schema find "date"` / `"extract date"` / `"month"` returned
  nothing because the matcher kept hyphenated ids whole. Hyphenated tokens
  are now also split, and the ETL transforms carry purpose words (month,
  multiply, upper case, blank default, summary per region all resolve).
- Item 4: pivot now carries the `as_name` rule in `known_restrictions`.
- Items 5 and 6 are by design (`--project` overrides one call; 50 rows is
  the token-safe default and `limit` is documented); no change.
- Not verified from the report: the as-is vs. fixed-key join match rates
  the brief asked for in step 4, and the cross-project `view export
  dataset` attempt in step 7 (the agent went straight to CSV + upload).
