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
