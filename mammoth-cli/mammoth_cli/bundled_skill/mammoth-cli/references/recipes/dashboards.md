# Dashboards

Release has retired `dashboard create` (legacy engine; HTTP 409
`4DASH012`): `schema find "dashboard create"` lists it first, do not use it.
Create with `create-blank` (or `v3 generate` when the task allows an AI route).
`dashboard source list` is an observed blocker on release (see
capabilities); verify the view binding with `dashboard get DASHBOARD_ID`
(`data.dataview_id`) instead.

```bash
mammoth schema get dashboard.create-blank
mammoth dashboard create-blank --input INPUT_JSON --project PROJECT_ID
mammoth dashboard get DASHBOARD_ID
```

Discover page/widget/publish routes and verify the binding, draft/published
data and terminal jobs. Use only returned IDs and schema confirmation policy;
do not invent dashboard JSON or opaque task specs.

Expected create-blank input is currently typed as
`{"params":{"dataview_id":VIEW_ID,"title":"TITLE"}}`; confirm with
`schema get dashboard.create-blank` first. If the dashboard is requested as a
deliverable, preserve the dashboard ID actually named in the returned `data`
object and do not clean it up. Otherwise, classify it explicitly as
temporary/intermediate before authorizing deletion. Then run:

```bash
mammoth dashboard get DASHBOARD_ID
mammoth schema find "dashboard page"
mammoth schema find "dashboard"
```

Page/widget schemas vary by release. Read each schema, use returned IDs, and
verify the binding plus draft/published data after every mutation. A
creation response alone is not proof of a usable published view.

## Authoring a board from a blank canvas

`create-blank` gives one empty page. Author it by reading the canvas,
editing the **active page** (`pages[0]`; a root-level `focus` is stored but
never baked when pages exist) and writing the whole object back:

```bash
mammoth dashboard create-blank --yes --input '{"params": {"dataview_id": VIEW_ID, "title": "Overview"}}'
mammoth dashboard canvas get DASHBOARD_ID > canvas.json      # data.canvas is the object to edit
# pages[0].focus  = {"measure": "Sales Actual", "dim": "Location",
#                    "kpis": [{"field": "Sales Actual", "agg": "sum", "label": "Sales", "unit": {"prefix": "£"}, "decimals": 0},
#                             {"field": "Employee Ref", "agg": "countDistinct", "label": "Distinct staff"}]}
# pages[0].added  = [{"kind": "bar", "title": "Actual vs Budget by Month", "measure": "Sales Actual", "measure2": "Sales Budget",
#                     "agg": "sum", "date_bucket": {"field": "Month", "unit": "month"}},
#                    {"kind": "hbar", "title": "Sales by Location", "dim": "Location", "measure": "Sales Actual", "agg": "sum", "sort": "desc"},
#                    {"kind": "line", "title": "Occupancy rate", "measure": "occupancy_rate", "date_bucket": {"field": "Month", "unit": "month"}},
#                    {"kind": "table", "title": "Detail", "columns": ["Location", "Month", "Places"], "sort_by": "Month", "limit": 100}]
# derived         = [{"id": "occupancy_rate", "label": "Occupancy rate", "numerator": "Occupied", "denominator": "Places"}]
# filters         = [{"field": "Month", "control": "range", "label": "Month"}, {"field": "Location", "control": "multi"}]
mammoth dashboard canvas save DASHBOARD_ID --input '{"body": {"params": {"canvas": <edited data.canvas>}}}'
mammoth job wait BAKE_JOB_ID                                  # data.bake_job_id from the save
```

Rules the backend enforces (each returns the pydantic path on failure):
`added[].measure` is a column name — a ratio lives in `canvas.derived[]` and
is referenced by id; `focus.kpis[].agg` accepts `countDistinct` (the only
correct aggregation for a "distinct people" card under a date filter);
`unit.prefix` goes on money cards only. `dashboard pages add --yes --confirm
ID --input '{"body": {"params": {"pages": [{"title": ..., "focus": {...},
"charts": [...]}]}}}'` adds a page, but that route runs through the LLM
guard and may drop a unit it cannot evidence (it says so in `data.message`);
`canvas save` keeps what you wrote. When the route refuses a chart (for
example a `pie` that the data does not support), `data.chart_check.refused`
names it. A new page that got no charts is removed, and
`data.chart_check.removed_pages` lists it. Add a chart of a different kind
(`hbar`, `line`, `table`) for that page.

## Put the money on the board

If the data has money (a price, an amount, revenue or cost), the dashboard
must show it. A board that shows only counts or quantities has left out the
number the user most likely wants.

- A money column must be `NUMERIC` first. `view data get` flags a money
  column that is stored as text in `column_warnings`.
- A unit price is not revenue. Do not sum a price. If the data has a
  quantity and a unit price, add a revenue column before you build the
  board, then chart the sum of that column:

```bash
mammoth view transform math VIEW_ID --project PROJECT_ID \
  --input '{"dataset_id":DATASET_ID,"expression":"qty * price","new_column":"revenue"}'
```

- Put revenue in a KPI (`focus.kpis`, `agg` `sum`, `unit.prefix` for the
  currency) and in one or more charts (revenue by product, by segment, by
  month). Rows with an empty price give an empty revenue. Say how many there
  are in your report.

**Read the bindings back, then the numbers.** `dashboard canvas get` returns
`data.meta.figures` — `"p1:kpi:2": {"descriptors": {"value": "<id>"}}` per
card and tile — and `data.plan.hints.kpis` with the agg per card. Evaluate
ids with a filter:

```bash
mammoth dashboard descriptor-data DASHBOARD_ID --input '{"body": {"params": {
  "descriptor_ids": ["<id>", "<id>"],
  "filter_state": {"Month": ["2025-01-01", "2025-03-31"]}}}}'
# -> data.results.<id>.value (scalar) or .data (rows); filter fields must be declared canvas filters
```

A card that reads the same with and without the filter, or a distinct count
that equals a row count, is a wrong binding, not a data fact.

## Canvas, widget data and PDF

Never save an invented canvas. Read it, change it, write it back:

```bash
mammoth dashboard canvas get DASHBOARD_ID   # data.canvas incl. style_tokens
mammoth dashboard canvas save DASHBOARD_ID --input '{"body":{"params":{"canvas":CANVAS_FROM_GET}}}'
```

`canvas save` with `{"canvas": {}}` fails (`dataset` and other fields are
required); the object returned by `canvas get` is the only known-good shape.
Widget ids for `dashboard data draft` / `dashboard data published` come from
that canvas: `--input '{"widget_id": "WIDGET_UUID"}'` (optional
`global_filters` / `drilldown_filters` objects). `dashboard query` needs a
descriptor with a `kind` (`scalar`, `group`, `rate`, `detail`, `options`,
`range`); `{"kind":"scalar","agg":"count"}` is the smallest that runs.

`dashboard pdf export` and `dashboard video export` cannot be completed from
the CLI: the backend requires the browser-hydrated `DashboardData` map
(pre-rendered widget results) in `params.data` and refuses to rebuild it. Report
this as a known limitation instead of retrying with `{}`.

## Publishing and the url routes

`dashboard share DASHBOARD_ID --input '{"type_of_auth":"public"}'` alone does
not publish: `was_published` stays false until you also run
`dashboard action DASHBOARD_ID --input '{"action":"publish-presentation"}'`.
`share` returns `data: null`; read the url slug back with `dashboard get`.
Only then do `dashboard published canvas URL`, `published data URL`,
`job-by-url URL JOB_ID` and the other `/dashboards/url/...` routes answer;
before that they return 404 `DASHBOARD_NOT_FOUND`. Legacy widget routes
(`widget-data`, `widget-data-by-url`, `published-data-by-url`, `data draft`,
`data published`) answer 409 `DASHBOARD_WRONG_ENGINE` on a v3 dashboard.
`video export` needs a motion-story dashboard. Revert the share
(`type_of_auth: "mammoth"`) before trashing a temporary dashboard.

