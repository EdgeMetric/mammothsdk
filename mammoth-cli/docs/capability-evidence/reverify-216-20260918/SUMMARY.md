# Re-verification of the rows fixed in 2.0.16 (2026-09-18)

Operator-run, probe project 27 (created and deleted in this sweep; dataset 58,
view 82). Release profile, CLI working tree after 2.0.16 with the SDK
conditional-format list fix applied.

| Command | Verdict | Note |
|---|---|---|
| `view conditional-format delete-all` | ok | rule_id forwarded; rule gone after the call |
| `view conditional-format create` | ok | HighlightEntry body; example hint now runnable |
| `view conditional-format list` | ok | returned `[]` on SDK 0.7.8 (mapping dropped); fixed in 0.7.9 |
| `view task preview` | backend_error | COPY spec accepted, job 406 fails with the datetime serialisation error (same as job 379) |
| `batch create` | not re-run | release route 500 after validation (HANDOVER) |
| `view export publish-db-update` | not re-run | no publish-db export exists to patch |

Also observed in this sweep, outside the four rows: `file upload` reported
`status: "ready"` for a dataset that was in `need_action` (ambiguous date
column). The handler hard-coded the status; it now reads each created
dataset back. The need-action recipe (`file-settings get` → `update` with
`date_format`) resolved the dataset to `ready` in one pass (job 399).
