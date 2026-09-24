# ILG CLI-rebuild feasibility map — desk review

Scope: whether `mammoth` CLI 2.0.26 (bundled skill + `docs/release-capability-matrix.md`)
can execute `handoff/PROMPT.md` against `handoff/ACCEPTANCE.md` and
`handoff/PIPELINE.md`. No commands were run against a backend; only local,
offline `schema get`/`schema find` reads and static doc/matrix inspection.

---

## A. Operation inventory, phase by phase

**Phase 0 — tooling proof**
- auth status / doctor / skill path+read / project ensure
- one throwaway dataset (upload) + one transformation + one read-back

**Phase 1 — parallel send into a new project, add-only**
- Identify the two source projects and the PowerBI-sending pipelines (read-only discovery)
- Add a new "send" task per pipeline targeting the new project, alongside the existing PowerBI export, without touching/reordering/deleting existing tasks
- Do one pipeline first, confirm its existing PowerBI send is unaffected, then repeat
- Read a reference project ("Phase 0") without modifying it

**Phase 2 — conform 12 facts to Location × Month, join, check totals**
- Location canonicaliser (`CASE WHEN ... END`, drop rollups/blank locations) per fact — this is raw SQL in the web route
- Month bucketing (`DATE_TRUNC('month', ...)`) per fact — raw SQL or a date-extraction transform in the web route
- `COUNT(*)` vs `COUNT(DISTINCT Employee Reference)` vs `COUNT(DISTINCT "Forename")`-avoidance per fact — SQL aggregation
- NOT-NULL pre-filters (`Pipeline`, `O - Leavers`, `HR - Long-term Absences`)
- The DISTINCTCOUNT fix: a window function (`MIN(...) OVER (PARTITION BY ...)`) to build a first-occurrence flag, then a second aggregation task carrying three measures, then a left-join back into the consolidated table
- N-way outer join of 12+ conformed facts into one consolidated table on (Location, Month)
- Per-fact group-total check against `ACCEPTANCE.md`, as-you-go (not batched)
- Two facts (`F - YTD 2023`, Nursery Pipeline) excluded from the spine — own boards, own grain

**Phase 3 — dashboards**
- Create 3(+) dashboards/pages bound to the consolidated view(s)
- KPI cards, incl. one `countDistinct`-aggregated card that must survive a Month range filter (trap 1) without using SUM/AVG semantics
- By-Month and by-Location charts (some multi-measure: Actual vs Budget)
- A Month filter (global filter, applied across the page/board)
- A ratio/rate chart (Conversion Rate) that must not be rendered as a KPI card (trap 5)
- Currency formatting on money columns only, none on counts/occupancy (trap 6)
- Read bindings back (which column/aggregation a card is actually bound to) rather than eyeballing rendered numbers

**Phase 4 — reporting**
- Pass/fail per Definition-of-done line
- Non-reproducible items and why
- Unexplained misses vs the key
- CLI assessment for CLI owners

---

## B. Operation → CLI route → status → risk

| # | Operation | CLI command id(s) | Matrix status / remark | Runnable example in bundled docs? | Risk |
|---|---|---|---|---|---|
| 1 | auth/doctor/skill/project bootstrap | `auth status`, `doctor`, `skill path`, `project ensure` | Core commands, extensively exercised across every evidence run (haiku-e2e, haiku-etl, golden-20260919) | Yes, SKILL.md itself | **Green** |
| 2 | Upload + one transform + read-back (Phase 0 proof) | `file upload`, `view transform convert-type`/`filter`, `view data get` | `view.task.add` (REL-461): "Partial... typed transforms bulk-replace, convert-type, discard-duplicates, filter, join, pivot, set-values, text each run once on an owned fixture on release and read back with view data get against a known answer" | Yes, `recipes/end-to-end.md` | **Green** |
| 3 | Discover source projects/pipelines feeding PowerBI | `project list`, `dataset list`, `view list`, `view get`, `view pipeline items`, `view task list` | Reads; `view.pipeline.items` "ran once on CLI 1.1.11 ... one bounded item; prior owned-view evidence retained and no Full claim is made" | Partial (operations.md) | **Amber** — read routes work, but nothing in the docs shows how a *PowerBI live-link/export task* renders in `view task list`/`pipeline items` output (task-type discrimination unproven) |
| 4 | Add a **new pipeline task** that sends data to a **dataset in a different project**, without touching existing tasks | `view.export.dataset` (`target_ds_id`, no project/location field) — candidate for a persistent pipeline step; `view.export.create` (`handler_type` incl. presumably `dataset`) — the literal "add an export to the pipeline" route | `view.export.dataset`: **"untried; no live run recorded"** in `references/commands/view.md:397-405`. `view.export.create` = REL-458 "Add a export in the pipeline": **"Unassessed... CLI accepts the request (exit 0, job 358 accepted...), but job get 358 -> status:error, response:{"error":{"message":"'destination'"}}" (a raw Python KeyError repr, not a structured message)"** | No — the one worked cross-project attempt (`haiku-etl-20260919`) never got there | **Red** — see Section C |
| 5 | Same-project "export view to new dataset" (proof the underlying primitive works at all) | `view.export.dataset` | Ran once **in the same project** in `haiku-e2e-20260918`: `view export dataset 65 --input '{"dataset_name":"Regional Summary","dataset_id":45}' --yes` → dataset 47, verified by a data read. Not reflected as "ran once" in the matrix's `view` family table (still listed untried) | Yes, in capability-evidence report only, not in a recipe | **Amber** (same-project only) |
| 6 | Insert a task at a guaranteed-safe position (after all existing/pinned tasks) without an approved schema for `SEQUENCE_NUMBER`/insertion point | `view.task.add` with raw `task_spec` | `operations.md`: *"The low-level `view task add\|preview\|update` routes expose an opaque `task_spec` object in the current schema, not a discoverable task union... Use a low-level task route only when an independently documented task specification is supplied for the target backend; never infer SDK/backend keys from `schema get` or an illustrative example... Without that independent specification, report the route as unsupported/ambiguous and stop safely."* | No safe example for this exact need | **Red** — see Section C |
| 7 | Canonicaliser CASE WHEN + rollup/blank-location filtering, per fact | `view.transform.add-sql` (raw SQL) or `view.transform.filter`+`view.transform.text`/`replace` | `add-sql`: **"untried; it submits through `view.task.add`, but this transform was not among those run"** (`view.md:827-835`). `filter`/`text`/`bulk-replace` ARE in the golden-20260919 proven list | `recipes/transforms.md` shows an `add-sql` example (untested on release) | **Amber** — filter/text primitives are proven; the raw-SQL shortcut the web route actually used is unproven |
| 8 | Month bucketing (`DATE_TRUNC`) | `view.transform.extract-date`, `view.transform.date-diff`, `view.transform.increment-date`, or `add-sql` | All four: **"untried; it submits through `view.task.add`, but this transform was not among those run"** (`view.md:927-935`, `897-905`, `967-975`, `827-835`) | `end-to-end.md`/`transforms.md` give shapes, not release evidence | **Amber/Red** — nothing in the proven list buckets a date by month; the web route needed `AI SQL Query` for exactly this and found `Group & Pivot` could not do it (`PIPELINE.md:721`) |
| 9 | `COUNT(*)` / `COUNT(DISTINCT col)` per-fact aggregation | `view.transform.pivot` (has `COUNT`/aggregation functions) or `add-sql` | `pivot`: **ran once** on CLI 2.0.18, read back with `view data get` — but only one input combination proven (`view.md:1027-1035`) | Yes, `end-to-end.md` | **Amber** — plain `pivot` proven; whether its aggregation set includes `COUNT DISTINCT` specifically is not shown in the one proven run (only `SUM`/`COUNT` shapes appear in examples) |
| 10 | Window function (`MIN(...) OVER PARTITION BY ...`) for the DISTINCTCOUNT fix | `view.transform.window` | **"untried; it submits through `view.task.add`, but this transform was not among those run"** (`view.md:1107-1115`) | Minimal (`{"function":"ROW_NUMBER", ...}` placeholder only) | **Red** — this is the load-bearing transform for trap 1 and it has zero release evidence |
| 11 | N-way join into consolidated table | `view.transform.join` | **Ran once** on CLI 2.0.18 through `view.task.add`, read back with `view data get`; **"other inputs for this transform are untried"** (`view.md:977-985`) | Yes, `end-to-end.md` | **Amber** — one join proven; ACCEPTANCE.md needs ~12+ successive joins on a 2-column composite key, an input shape never exercised |
| 12 | Deliverable CSV export, mid-build safety net | `view.export.csv` | Matrix: **"untried; no live run recorded"** (`view.md:397` area / capabilities.md `view` ran-once list omits `view.export.csv`) even though `recipes/exports.md` calls it "the proven path" | Yes, `end-to-end.md`, `recipes/exports.md` | **Amber** — docs assert it's proven; the matrix itself does not list it as ran-once, which is an internal inconsistency (see Section E) |
| 13 | Dashboard creation | `dashboard.create-blank` (`dashboard.create` retired: HTTP 409 `4DASH012 DASHBOARD_LEGACY_CREATION_RETIRED`) | `dashboard.create-blank` = REL-335: **"Partial... Created dashboard 62 (sequence 1). Single invocation only."** | Yes, `recipes/dashboards.md` | **Green** for the empty shell; says nothing about content |
| 14 | KPI card / chart authoring (bindings, aggregation, filters) | No typed "add KPI/chart" command exists in the `dashboard` family at all. Only: `dashboard.canvas.get`+`dashboard.canvas.save` (raw, undocumented widget JSON), `dashboard.chat.edit` (NL prompt), `dashboard.v3.generate` (NL one-shot dashboard) | `canvas.save` = REL-513: proven only as an **idempotent round-trip** ("dashboard canvas get -> save round-trip completed cleanly... Caveat: this blan[k canvas]..."). `chat.edit` = REL-364: proven only for `display_title=Sweep Test` (a rename). `v3.generate` = REL-339: proven only for one generic "Summarize revenue by region" prompt | `dashboards.md`: *"Never save an invented canvas. Read it, change it, write it back"* | **Red** — see Section C |
| 15 | `countDistinct` KPI aggregation that survives a Month filter | Same as #14 (canvas.save or chat.edit) | No release evidence either way; `DASHBOARD_DEFECTS_PROMPT.md` D7: *"`countDistinct` is missing from the manual KPI aggregation control... so a distinct count can only be authored via chat"* | None | **Red** — see Section C |
| 16 | Month filter on a page/board | `dashboard.query` descriptor `kind:"range"`, or canvas-level filter config (undocumented) | `dashboard.query` = REL-379: **"Partial... descriptor with kind=scalar ran cleanly"** — only `scalar` exercised, not `range`/`group` | None with `range` | **Amber/Red** |
| 17 | Read a widget's binding back to verify column/aggregation | `dashboard.canvas.get` (returns full canvas incl. widget configs) | REL-... "ran once... result keys: canvas, dashboard_id, meta, plan, specs. returned canv[as]" | Yes | **Amber** — the read primitive is proven; there is no worked example of parsing a returned widget's binding and confirming it against intent (the exact web-route failure mode: "vs Budget" labels bound to Actual columns) |
| 18 | Legacy widget-data/getDraftData/getPublishData routes | `dashboard.widget-data`, `dashboard.widget-data-by-url`, `dashboard.data.draft`, `dashboard.data.published`, `dashboard.published-data-by-url` | **All "observed blocker"**: `4DASH004 DASHBOARD_WRONG_ENGINE`, e.g. *"This dashboard uses a different rendering engine -- use the matching endpoints"* on dashboard 56, a create-blank/v3-engine dashboard | `dashboards.md` confirms: *"Legacy widget routes... answer 409 DASHBOARD_WRONG_ENGINE on a v3 dashboard"* | **Red** for these specific routes on any dashboard the CLI can actually create |
| 19 | PDF/report export of finished dashboards (Phase 4 "report") | `dashboard.pdf.export`, `dashboard.published.pdf.export`, `dashboard.video.export` | **"Not supported from the CLI on release: backend HTTP 400 4GENR001 requires params.data to be the browser-hydrated DashboardData map and states it cannot rebuild it from stored descriptors"** | `dashboards.md` states this plainly as a known limitation | **Red**, documented as such (not a surprise) |

---

## C. Hard blockers

### C1. Cross-project "send" has no proven CLI route, and the closest candidate is broken

PROMPT.md Phase 1 requires: "get the data into the new project... Do not upload CSVs," via a pipeline
task alongside the existing PowerBI export (mirroring the web route's `Unify > Send to Dataset`,
which had an explicit **project picker** — `PIPELINE.md:124-140`: *"Its config carries Destination
(New/Existing Dataset), New dataset name, and Location — and Location is a full project picker
(Select Dataset Location), so it writes across projects."*).

Two CLI candidates, both dead ends as documented:

1. **`view.export.dataset`** (`target_ds_id: int`, `dataset_name`, `save_as_mode`, `end_of_pipeline: bool`,
   no project/location field at all). `schema get view.export.dataset` reports `"scope": "project"`.
   Status on release: **"untried; no live run recorded"** for this exact shape. The one deliberate
   test built to answer this question — `docs/capability-evidence/haiku-etl-20260919/BRIEF.md` step 7a:
   *"try `view export dataset` from the source view with a target dataset that lives in the target
   project... quote the exact error if the backend refuses cross-project targets"* — was never
   completed: run 1 (`REPORT.md`) hit a stuck upload worker before reaching step 7; run 2
   (`REPORT-2.md`) reached step 7 and **skipped the CLI cross-project attempt entirely**, going
   straight to "file upload the exported CSV into the target project" instead (*"The agent did not
   report trying `view export dataset` with a cross-project target."*) — precisely the fallback
   PROMPT.md forbids. So: **genuinely unknown**, not "should work."
2. **`view.export.create`** (the literal "add an export to the pipeline" route, REL-458, endpoint
   `POST .../pipeline/exports`) — the shape that would actually persist as a pipeline step riding
   the same refresh cadence as the PowerBI Live Link, matching what PIPELINE.md's route did. Status:
   **"Unassessed... CLI accepts the request (exit 0, job 358 accepted...), but job get 358 ->
   status:error, response:{"error":{"message":"'destination'"}}"** — a raw, unstructured backend
   KeyError, reproduced twice (once with `target_properties.destination` explicitly set). This is
   the route closest in spirit to the web app's pinned, auto-syncing "Send to Dataset" task, and it
   is presently broken for at least the CSV/postgres shapes tested; a `handler_type: dataset`
   variant was not tried.

Given `dataset.create` (`docs/.../dataset.md:35-43`) and `view.export.dataset`'s `scope: "project"`
both imply datasets are strictly project-scoped, there is no structural evidence the backend even
resolves a `target_ds_id` that lives outside the caller's active project. **Unknown, not assumed.**

**Verdict: Phase 1's "add a send into a new project via the pipeline, no CSVs" has no CLI route with
positive evidence. This is the single largest gap between the brief and what's proven.**

### C2. No safe, typed way to add a task without risking the pinned/existing tasks

PROMPT.md Phase 1(c): *"ADD ONLY — never modify, reorder or delete an existing task... Do ONE first
and confirm its existing send is unaffected."* PIPELINE.md's web-route finding was that a UI click
sets an insertion point (*"select the Source step... the next task you add lands after the selected
task"* — `PIPELINE.md:607-625`) and that pinned tasks (Live Link, `Publish as Dashboard` ×3) sit
untouched by insertions elsewhere.

The CLI's only mutation route into an existing pipeline is `view.task.add` with a raw `task_spec`
object (`SEQUENCE_NUMBER` field seen only in the illustrative `agent_example`, never in a proven
run). The CLI's own `operations.md` says: *"The low-level `view task add|preview|update` routes
expose an opaque `task_spec` object in the current schema, not a discoverable task union... Use a
low-level task route only when an independently documented task specification is supplied for the
target backend; never infer SDK/backend keys from `schema get` or an illustrative example...
Without that independent specification, report the route as unsupported/ambiguous and stop safely."*

There is no typed transform (join/filter/pivot/etc.) that expresses "append an export step." The
`view.export.dataset` field `end_of_pipeline: bool` is the only hint of an append-at-end mechanism,
and it is untried. Nothing in the docs shows `view.pipeline.items`/`view.task.list` output
distinguishing a pinned PowerBI/Live-Link task from an ordinary one, so an agent cannot even
mechanically confirm from a read alone that its insertion landed after, not before, the pinned tasks
— it would have to compare live-link output before/after, which is a live-backend check outside this
desk review's scope.

**Verdict: Red.** The brief's own safety rule (add-only, verify per pipeline) cannot currently be
discharged with a documented, typed CLI command; it would require the "opaque task_spec" route the
CLI's own docs tell agents to refuse.

### C3. Dashboard KPI/measure authoring has no typed route, and the DASHBOARD_DEFECTS bugs sit in the same code path the CLI uses

There is no `dashboard.kpi.*`/`dashboard.chart.*`/`dashboard.widget.create` command in the 104-command
`dashboard` family. The only three ways to put a widget on a v3 dashboard are:

- `dashboard.canvas.save` — raw canvas JSON, explicitly warned against inventing (`dashboards.md`:
  *"Never save an invented canvas. Read it, change it, write it back"*), proven only as a no-op
  round-trip (REL-513).
- `dashboard.chat.edit` — natural-language prompt, proven only for a title rename (REL-364).
- `dashboard.v3.generate` — one-shot AI dashboard generation, proven once for a generic prompt
  (REL-339), not for a from-scratch board with named KPI cards bound to named columns.

`chat.edit` and `v3.generate` run through the **same** LLM controls/guard code the web route hit —
`DASHBOARD_DEFECTS_PROMPT.md` names `llm/controls.py` (`effective_noop`, `skip_notes`) and
`llm/guards.py` (`KPI_AGGS`, `SKIP_UNIT_CURRENCY_UNEVIDENCED`) as backend files, not Vue components.
So the CLI route inherits, not sidesteps:
- **D7**: *"`countDistinct` is missing from the manual KPI aggregation control... It is supported end
  to end... But the control manifest offers only sum/avg/min/max/count/median... So a distinct count
  can only be authored via chat."* — meaning the CLI's `chat.edit` route is the documented way to get
  `countDistinct` onto a card, which puts trap 1 (the load-bearing "must read 613, not 342" check)
  behind the least-proven, most trust-fragile authoring route in the whole CLI.
- **D4**: chat reports success it didn't achieve (relabelled cards left bound to the wrong column
  while claiming "vs Budget" was added) — this is exactly the failure mode PROMPT.md Phase 3 tells
  the agent to guard against by reading bindings back, which confirms the authors of PROMPT.md already
  assumed this defect class applies regardless of route.
- **D5**: silent caps (disclosed only after claiming full success) apply to any batch of chat-driven
  edits, CLI included.
- The **repo conventions** note in `DASHBOARD_DEFECTS_PROMPT.md` — *"Two engine bundles (server +
  CLI); a re-vendor turns the BE parity corpus red only when the **server** bundle moves"* — is direct
  confirmation that `dash-engine` (where D1's top-N "% of total" bug and D3's multi-measure default-avg
  bug live) ships as a CLI-side bundle too, i.e. these are not web-UI-only defects.
- Conversely, **D2** (the web Edit-KPIs Prefix box not binding to `unit.prefix`) is a Vue panel bug
  the CLI's raw `canvas.save` route would bypass entirely — a plausible CLI advantage, but unverified
  since nobody has exercised `canvas.save` with a real `unit.prefix` write on release.

**Verdict: Red for authoring the specific measures ACCEPTANCE.md needs** (a mixed-grain
`countDistinct` card that must not use SUM/AVG/COUNT, a Month filter, Actual-vs-Budget multi-measure
charts). The mechanism exists in principle (raw canvas write, or chat), but neither has release
evidence at this level of specificity, and the chat route is documented to inherit known defects.

### C4. Reading widget bindings back is the one part of Phase 3 with real (if thin) footing

`dashboard.canvas.get` is proven to return the full canvas object including widget configs (REL-...
"result keys: canvas, dashboard_id, meta, plan, specs"), and `dashboard.query` (REL-379) is proven
for the simplest descriptor shape. Between the two, an agent can plausibly extract "what column and
aggregation is card X bound to" and cross-check it against intent — the exact check PROMPT.md Phase 3
demands ("a wrong binding renders a perfectly plausible figure"). This is the one dashboard-side
operation in this brief with a credible, if unexercised-at-this-specificity, CLI path. Legacy
widget-data endpoints are a dead end on any dashboard the CLI can create (`4DASH004
DASHBOARD_WRONG_ENGINE`, confirmed for `dashboard.widget-data`, `dashboard.data.draft`,
`dashboard.data.published`, `dashboard.published-data-by-url`, `dashboard.widget-data-by-url`).

### C5. Structural, product-level limits DASHBOARD_DEFECTS_PROMPT.md already surfaced, restated for the CLI

- **One dataview per dashboard.** ACCEPTANCE.md's own two-satellite-board design (`F - YTD 2023`,
  Nursery Pipeline) and the mixed-grain consolidated-table trick for trap 1 exist *because* of this
  limit, confirmed independently in `PIPELINE.md:1367-1374` ("A Mammoth dashboard binds exactly one
  dataview... there is no add second dataset"). The CLI does not remove this limit; it inherits it.
- **KPI strip caps at 5 cards** (DASHBOARD_DEFECTS D14) — a product limit, not CLI-specific, that
  already shaped ACCEPTANCE.md's page layout (Budget Variance on its own board).
- **Ratios cannot be KPI cards** (trap 5) is a modelling instruction to the builder, not a CLI
  capability question — noted here only because it interacts with C3: if `countDistinct` can only be
  reached via chat, and chat is the same surface that produced D1b (a nonsensical "% of total" on a
  rate column), the safest CLI path for the Conversion Rate chart is a plain bar/line built off
  `add-sql`/`pivot` data, not a chat-authored KPI.

---

## D. Recommended path

**Could an agent run PROMPT.md as written today?** No, not with the "Do not upload CSVs" and
add-only constraints intact for Phase 1, and not with confidence on the `countDistinct` KPI card in
Phase 3. The rest (Phase 0, Phase 2's typed-transform portions, Phase 4 reporting) is workable.

**Which reduction to use:** run **`F - SchoolPnL` + Overview only**, not "skip Phase 1" — but treat
Phase 1 itself as the thing to de-risk first, separately, before spending any Phase-2/3 budget:

1. Prove the Phase 1 cross-project send **in a disposable pair of projects**, not on the two live
   ILG source projects, before ever touching production pipelines. Command: `view export dataset
   SRC_VIEW SRC_DS --input '{"dataset_name":"probe","target_ds_id":TARGET_DS_ID_IN_OTHER_PROJECT}'`
   (create `TARGET_DS_ID` first via a header-only upload in the target project, per
   `haiku-etl-20260919/BRIEF.md` step 7a's own recipe). Evidence needed: does it accept a
   `target_ds_id` outside the active project, and does it land as a **re-runnable pipeline step**
   (check `view.task.list`/`view.pipeline.items` afterward) or a one-off snapshot? If refused,
   quote the exact structured error (matrix precedent: `view.export.create`'s raw `'destination'`
   KeyError shows the backend can return unstructured errors here — capture and report verbatim).
2. In parallel, retry `view.export.create` with `handler_type` set to whatever the schema's
   `dataset`/internal target variant is (`schema get view.export.create --input '{"full": true}'`),
   since REL-458's failure was reproduced only for CSV/postgres-shaped `target_properties`. This is
   the route that would actually persist as a pipeline task riding the existing refresh cadence,
   which is what "parallel send" implies; `view.export.dataset` alone may only be a one-shot action.
3. Only once (1) or (2) has a positive, reproduced result on a throwaway pair of projects should
   Phase 1 touch the real ILG pipelines, one at a time, per PROMPT.md's own instruction.
4. For Phase 3, before committing to the `countDistinct` KPI card, spend one cheap probe:
   `dashboard.canvas.get` on a disposable dashboard, hand-craft one KPI widget with
   `agg: "countDistinct"` bound to the mixed-grain table's flag column, `canvas.save` it, then
   `dashboard.canvas.get` again to confirm the write held and `dashboard.query` with the matching
   descriptor to confirm the computed value. This tests C3's actual open question — whether raw
   canvas authoring can reach `countDistinct` and bypass D7's manual-control gap — without any
   ILG-real data at risk.
5. Only after 1–4 have positive evidence should the full `ACCEPTANCE.md` scope (12 facts, 7 boards)
   be attempted; until then, cap ambition at the reduction the pack already recommends.

**Ordered list of what CLI owners must fix or prove first:**

| Priority | Item | Command id | Evidence needed |
|---|---|---|---|
| 1 | Cross-project dataset target | `view.export.dataset` | One live run with `target_ds_id` in a *different* project than the caller's active one; report the exact accept/refuse behavior |
| 2 | Persistent pipeline export (not a one-shot action) | `view.export.create` | Fix the `'destination'` KeyError (REL-458) for at least one `handler_type`, then prove `end_of_pipeline`/append semantics don't disturb existing task order |
| 3 | Typed/discoverable task insertion contract | `view.task.add` | Either a typed "append task" transform, or a documented, versioned `task_spec` union so `operations.md`'s "stop safely" guidance doesn't foreclose the only add-only route |
| 4 | `countDistinct` on a KPI card via a route other than chat | `dashboard.canvas.save` | One proven run writing a widget with `agg: "countDistinct"` and reading it back correctly under a date filter |
| 5 | `view.transform.window` | `view.transform.window` | One proven run of the actual DISTINCTCOUNT-fix shape (`MIN(...) OVER (PARTITION BY ...)`), read back |
| 6 | Month-bucketing transform | `view.transform.add-sql` or `extract-date` | One proven `DATE_TRUNC('month', ...)`-equivalent run, since `pivot`/`Group & Pivot` cannot bucket a date by month (confirmed independently in `PIPELINE.md:721`) |
| 7 | Dashboard Month range filter | `dashboard.query` (`kind: "range"`) or canvas filter config | One proven run of a range/date filter descriptor, not only `kind: "scalar"` |

---

## E. Contradictions in the CLI's own docs

1. **`view.export.csv` "proven" vs. matrix "untried."** `references/recipes/exports.md` states
   flatly: *"`view export csv` and the typed destination commands are the proven path."* But
   `capabilities.md`'s `view` family "Ran once" list does not include `view.export.dataset`, and
   `references/commands/view.md:397` records `view.export.csv`'s own status as **"untried; no live
   run recorded."** The recipe's confidence is not backed by the matrix it is supposed to defer to
   (SKILL.md itself says *"capabilities wins over a recipe"* when they disagree — so an agent
   following SKILL.md's own precedence rule should distrust the recipe here).
2. **`view.export.dataset` proven once, but not credited.** `haiku-e2e-20260918/REPORT.md` shows a
   real successful run (`view export dataset 65 --input '{"dataset_name":"Regional
   Summary","dataset_id":45}' --yes` → dataset 47, read back). Neither `capabilities.md`'s ran-once
   list nor `references/commands/view.md` reflects this; both still say "untried." The evidence
   exists in `docs/capability-evidence/` but was not folded into the generated matrix/skill docs —
   exactly the kind of drift `docs/capability-drift-workflow.md` presumably exists to catch.
3. **`view.task.add` is simultaneously "proven" and "do not use blind."** `capabilities.md` and
   `view.md` report `view.task.add` (REL-461) as the vehicle behind 9 named, release-proven
   transforms. But `operations.md` in the same skill package warns the raw `task_spec` route (the
   only way to do anything `view.task.add`'s typed wrappers don't cover — including, plausibly, a
   safe append-only insertion) is "opaque... not a discoverable task union" and should be refused
   absent an independently documented spec. Both statements are true simultaneously (typed wrappers
   are fine; raw task_spec is not), but a skimming agent following only the "ran once" status could
   miss the caveat that gates the exact capability Phase 1 needs.
4. **PIPELINE.md (web route) vs. CLI docs on "how to conform a date to month."** `PIPELINE.md:721`
   found, independently and the hard way, that `Group & Pivot` (the web UI's rough equivalent of
   CLI `pivot`) *cannot* bucket a date by month, and switched to raw SQL. `recipes/transforms.md`
   presents `pivot` as the preferred, proven route for "a grouped summary" without carrying that same
   caveat forward for date-bucketing specifically — an agent relying on the CLI's own transforms
   recipe alone (without having read PIPELINE.md) would not be warned before hitting the same wall.

---

## Bottom line

Green: bootstrap, discovery reads, single typed transforms exercised on the golden fixture (filter,
convert-type, discard-duplicates, join×1, pivot×1, set-values, text, bulk-replace), dashboard shell
creation, canvas read-back.

Amber: repeated/chained joins and pivots at ACCEPTANCE.md's scale, CSV export as a safety net (docs
say proven, matrix disagrees), Month-filter and range-descriptor authoring, reading dashboard
bindings back.

Red / hard blockers: cross-project send without CSV upload (Phase 1's core requirement), a
demonstrably safe add-only task-insertion contract, the `countDistinct`-survives-a-filter KPI card
(trap 1, the brief's own "sharpest single check"), month-bucketing via any transform actually proven
on release, and the window-function transform the DISTINCTCOUNT fix depends on.

---

## Addendum 2026-09-19 — live outcome

The simulation in `ilg-sim-20260919/SUMMARY.md` ran the brief's shape on
release with CLI 2.0.28: C1 (cross-project send) is closed by
`view export dataset ... target_project_id` (SDK 0.7.13); C2 is closed for
the append case (existing export untouched, no precondition yet); C3 is
closed through `dashboard canvas save` (a `countDistinct` card persisted,
baked and evaluated to the true distinct count under a Month range; a
derived ratio measure for the rate chart; `unit.prefix` on money cards
only), with the caveat that `pages add` / chat routes still pass the LLM
guard; C4 is closed by `dashboard canvas get` → `meta.figures` →
`dashboard descriptor-data`. `add-sql` is the per-fact conform route
(single view; result types NUMERIC/TEXT/TIMESTAMPTZ). The production-readiness
page carries the updated list.
