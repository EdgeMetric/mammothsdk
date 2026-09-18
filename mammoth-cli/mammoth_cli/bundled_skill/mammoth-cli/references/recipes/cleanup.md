# Trash, recovery and explicitly authorized cleanup

Read [deliverable retention and cleanup authorization](../retention.md) first.
Classify temporary, intermediate, retained-deliverable, and protected
resources before choosing a cleanup target. “Owned” is not by itself cleanup
authorization: never delete all resources created by a task, and never delete
a requested dataset, dashboard, view, or export artifact as incidental tidy-up.

```bash
mammoth schema find "trash" --output json --no-input
mammoth schema find "restore" --output json --no-input
mammoth schema get dataset.delete --output json --no-input
mammoth dataset delete OWNED_DATASET_ID --project PROJECT_ID --output json --no-input --yes
```

Keep an immutable typed baseline: before creating anything, record every
pre-existing id by type (`project list`, `dataset list`, `dashboard list`,
`view list DATASET_ID` for each dataset you will touch). Before deleting,
diff the current lists against that baseline and delete only ids that are
absent from it and explicitly authorized as temporary/intermediate. One id
per destructive call: read it back first (`dataset get ID --project P` must
return the name you created), then `dataset delete ID`; never pass several
ids to one delete, since one transposed digit removes a protected resource
(ids are workspace-global, so a wrong `--project` does not protect you).
Deleting a project you created removes everything in it and needs
`--yes --confirm PROJECT_ID` (the exact id); only do it when the task said the
whole project was temporary. Reconcile child-to-parent jobs, verify absence
with a list, and confirm the baseline is intact. Retained deliverables remain in place for handoff. On
timeouts or unknown effects inspect the exact target/job before retrying.

Trash/restore are separate lifecycle operations: use `schema find "trash
restore"`, then `schema get` for the exact resource command. Do not assume a
delete response has a `job_id`: inspect its returned `data` keys and the
command's wait policy, then reconcile any returned job before a scoped absence
read. Never delete a numeric ID merely because it appears in a read response,
and never treat a 403/unknown result as proof of absence.
