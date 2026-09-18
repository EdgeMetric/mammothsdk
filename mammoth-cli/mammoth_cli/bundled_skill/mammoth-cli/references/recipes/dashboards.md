# Dashboards

Dashboard inputs are generated and release-dependent:

```bash
mammoth schema find "dashboard create" --output json --no-input
mammoth schema find "dashboard source" --output json --no-input
mammoth schema get dashboard.create-blank --output json --no-input
mammoth dashboard create-blank --input INPUT_JSON --project PROJECT_ID --output json --no-input --yes
mammoth dashboard get DASHBOARD_ID --output json --no-input
mammoth dashboard source list --output json --no-input
```

Discover page/widget/publish routes and verify source binding, draft/published
data and terminal jobs. Use only returned IDs and schema confirmation policy;
do not invent dashboard JSON or opaque task specs.

Expected create-blank input is currently typed as
`{"params":{"dataview_id":VIEW_ID,"title":"TITLE"}}`; confirm with
`schema get dashboard.create-blank` first. If the dashboard is requested as a
deliverable, preserve the dashboard ID actually named in the returned `data`
object and do not clean it up. Otherwise, classify it explicitly as
temporary/intermediate before authorizing deletion. Then run:

```bash
mammoth dashboard get DASHBOARD_ID --output json --no-input
mammoth dashboard source list --output json --no-input
mammoth schema find "dashboard page" --output json --no-input
mammoth schema find "dashboard" --output json --no-input
```

Page/widget schemas vary by release. Read each schema, use returned IDs, and
verify dashboard source plus draft/published data after every mutation. A
creation response alone is not proof of a usable published view.

## Canvas, widget data and PDF

Never save an invented canvas. Read it, change it, write it back:

```bash
mammoth dashboard canvas get DASHBOARD_ID --output json --no-input   # data.canvas incl. style_tokens
mammoth dashboard canvas save DASHBOARD_ID --input '{"body":{"params":{"canvas":CANVAS_FROM_GET}}}' --output json --no-input
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
this as a known limitation instead of retrying with `{}`. `dashboard create`
(legacy engine) is retired on release (HTTP 409 `4DASH012`); use
`create-blank` or `v3 generate`.

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

