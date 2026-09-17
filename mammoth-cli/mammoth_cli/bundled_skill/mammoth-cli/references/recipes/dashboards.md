# Dashboards

Dashboard inputs are generated and release-dependent:

```bash
mammoth schema find "dashboard create source page widget" --output json --no-input
mammoth schema get dashboard.create-blank --output json --no-input
mammoth dashboard create-blank --input INPUT_JSON --project PROJECT_ID --output json --no-input --yes
mammoth dashboard get DASHBOARD_ID --output json --no-input
mammoth dashboard source list --output json --no-input
```

Discover page/widget/publish routes and verify source binding, draft/published
data and terminal jobs. Use only returned IDs and schema confirmation policy;
do not invent dashboard JSON or opaque task specs.
