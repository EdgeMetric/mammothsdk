# Trash, recovery and owned cleanup

```bash
mammoth schema find "trash restore delete" --output json --no-input
mammoth schema get dataset.delete --output json --no-input
mammoth dataset delete OWNED_DATASET_ID --project PROJECT_ID --output json --no-input --yes
```

Keep an immutable typed baseline. Delete only returned owned IDs, reconcile
child-to-parent jobs, verify absence and restore the complete baseline. On
timeouts or unknown effects inspect the exact target/job before retrying.
