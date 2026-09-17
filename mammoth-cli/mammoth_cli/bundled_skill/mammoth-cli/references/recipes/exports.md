# Exports and artifacts

```bash
mammoth schema find "view export" --output json --no-input
mammoth schema get view.export.csv --output json --no-input
mammoth view export csv VIEW_ID --project PROJECT_ID --output json --no-input
mammoth view export list VIEW_ID DATASET_ID --project PROJECT_ID --output json --no-input
```

Wait/reconcile returned jobs. Verify local artifact headers, rows and hash;
for external destinations use required confirmation and destination readback.
Never put connector secrets in argv. Exit 7 or unknown outcome requires
reconciliation before replay.
