# Trash, recovery and owned cleanup

```bash
mammoth schema find "trash" --output json --no-input
mammoth schema find "restore" --output json --no-input
mammoth schema get dataset.delete --output json --no-input
mammoth dataset delete OWNED_DATASET_ID --project PROJECT_ID --output json --no-input --yes
```

Keep an immutable typed baseline. Delete only returned owned IDs, reconcile
child-to-parent jobs, verify absence and restore the complete baseline. On
timeouts or unknown effects inspect the exact target/job before retrying.

Trash/restore are separate lifecycle operations: use `schema find "trash
restore"`, then `schema get` for the exact resource command. Do not assume a
delete response has a `job_id`: inspect its returned `data` keys and the
command's wait policy, then reconcile any returned job before a scoped absence
read. Never delete a numeric ID merely because it appears in a read response,
and never treat a 403/unknown result as proof of absence.
