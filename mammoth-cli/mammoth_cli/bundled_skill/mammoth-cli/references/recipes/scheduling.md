# Recurring work: automations and schedules

Two different resources both look like "make this run on its own." Pick by
what the task actually needs to run, not by the word "schedule" in the
request:

- **`automation`** — the general-purpose recurring/triggered task engine.
  Use it for `run_data_retrieval` (refresh a cloud dataset), `append_data`
  (add new rows from a folder or dataset), `send_an_alert` (email), and
  `pull_cloud_files` (land new cloud files into a folder). Recurrence is one
  of the automation's `conditions`, type `at_specific_time`, alongside the
  `tasks` it runs. This is what "schedule a daily refresh" almost always
  means.
- **`schedule`** — a single, narrower resource that only pulls a cloud
  connector's data (`pull_cloud_data` work item). It has no other work item
  type on this backend (`ALLOWED_TASK_RESOURCE_MAP` in mvc-service only maps
  `pull_cloud_data`); do not try to fit `append_data`/`send_an_alert`/
  `pull_cloud_files` into a `schedule create` body, it will be rejected.
  `schedule list` is unimplemented on every backend release tested so far
  (`GET .../schedules` always returns HTTP 400 `5GENR011 NOT_IMPLEMENTED`,
  not intermittently) — do not poll it; there is currently no way to list
  schedules for a project from the CLI. Use `schedule get SCHEDULE_ID` with
  an id you already have (for example from a dataset's own automation/task
  metadata) instead.

PDF or image intake (`append_data` + `new_data_addition_in_folder`) needs one
destination dataset that already has a saved extraction recipe and a name
pattern the file name matches; a password-protected or unreadable file holds
for input. Read `automation capabilities` before you promise it.

`schema find "recurring work"` phrasing (e.g. "schedule a daily refresh",
"run every week automatically") resolves to `automation create`.

## Create a recurring automation

```bash
mammoth schema get automation.create   # confirm the current task/condition shapes first
mammoth automation create 'Nightly refresh' --yes --input '{
  "description": "Refresh dataset 42 every day at 02:00 UTC",
  "tasks": [
    {"task_type": "run_data_retrieval", "details": {"ds_details": [{"ds_id": 42}]}}
  ],
  "conditions": [
    {"condition_type": "at_specific_time", "details": {
      "frequency": "daily", "interval": 1, "start_at": "2027-01-01T02:00:00Z"
    }}
  ]
}'
```

`run_data_retrieval` only refreshes a cloud-connected dataset; a dataset made
from an uploaded file or a URL (`weburl`) is a one-time copy with no source
details to refresh from — say so rather than scheduling one.

That is not the same as "this dataset can never be recurring." A
file-backed dataset's pipeline re-runs on new data exactly like any other
dataset's ([how Mammoth organises
data](../about-mammoth.md#how-mammoth-organises-data)); the only difference
is that nothing pulls the next file in for you — each new batch has to be
uploaded with `append_to_ds_id` rather than fetched automatically. Once a
new file lands that way, every view on that dataset recomputes over it
automatically, so a monthly "email this view as CSV" delivery is buildable
today, with no connector:

```bash
# each month, once the new file is ready (a person or an outside script runs this):
mammoth file upload ./brand_spend_2026_10.csv --input '{"append_to_ds_id": DATASET_ID}'
# one-time setup: the recurring delivery itself, via send_an_alert
mammoth automation create 'Monthly brand spend to client' --yes --input '{
  "tasks": [
    {"task_type": "send_an_alert", "details": {
      "alert_type": "email", "recipients": ["client@example.com"],
      "subject": "Monthly brand spend report",
      "attachments": {"dataview_ids": [VIEW_ID]}
    }}
  ],
  "conditions": [
    {"condition_type": "at_specific_time", "details": {
      "frequency": "monthly", "interval": 1, "start_at": "2027-01-01T02:00:00Z"
    }}
  ]
}'
```

`send_an_alert`'s CSV attachment is exported from the view's prepared rows
at the moment the automation fires, not a copy taken at creation time (every
output in Mammoth is computed from prepared data, never cached — see
[about-mammoth.md](../about-mammoth.md)), so once this automation exists it
delivers whatever the view currently holds each month; only the file-upload
step above still needs to happen before each run.

The other three task types take the shapes documented in `schema get
automation.create` under `tasks[].details`:

- `append_data`: `destination_dataset_ids` (required) plus either
  `source_folder_resource_id` or `source_dataset_id`.
- `send_an_alert`: `alert_type` ("email"), `recipients`, `subject`, and optional
  `attachments.dataview_ids` (a list of view ids); each attached view is
  emailed as a CSV file, combined row count capped at 100,000 across all
  attachments.
- `pull_cloud_files`: `connector_key`, `connection_key`,
  `cloud_source_folder_path`, `destination_folder_resource_id`.

`conditions`/`condition_mode` are optional; an automation with no
`at_specific_time` condition runs only on demand (`automation update ID
--yes --input '{"patch": [{"op": "command", "path": "run", "value": {}}]}'`)
or via its other condition types (new file in a folder, etc.), not on a
recurrence.

## Create once: list first, update instead of create

`automation create` is not idempotent: running it twice makes two
automations that both fire (two client emails a month). Before every create:

```bash
mammoth automation list        # is there already one with this name or these recipients?
```

If one exists, change it with `automation update AUTOMATION_ID` (see below)
instead of creating another. Before a schedule that emails a client, send the
same email to the user first (or `--dry-run` the create and show the
recipients, subject and attached views) and get a yes. Give `start_at` a time
in the future; a past `start_at` may fire straight away or never.

## Read it back

```bash
mammoth automation get AUTOMATION_ID
mammoth automation list
```

**Known backend defect (observed on release, not a CLI bug):**
`automation get AUTOMATION_ID` on an automation `automation create` just
returned can come back HTTP 500 with an empty body — deterministically, not
an eventual-consistency race (confirmed by three retries seconds apart in
`docs/capability-evidence/fixture-sweep-20260919/`). `automation list` can
also fail to show that same automation. Both were root-caused by reading
mvc-service (not by a live re-run — see `docs/release-capability-matrix.json`
`REL-181`): the leading candidate is an unconditional `automation_tasks[0]`
index in `apiv2/apiv2/automations/utils.py` `get_automation_tasks()`, which
raises an unhandled `IndexError` when a GET's task lookup comes back empty —
matching the empty response body (a normal validation error returns a JSON
envelope; this does not). Do not report "the automation vanished"; if `get`
or `list` fail this way right after a create, treat the create's own 200/202
response and `automation_id` as the source of truth, and say so in the
report as "created, unconfirmed" (the create returned 200 but the read-back
failed): never re-run the create to "fix" it, which makes a duplicate. This is not something the CLI can work around — do not retry
`automation get` more than once for this.

## Update: disable / enable, change tasks, run now

```bash
# Suspend (disable)
mammoth automation update AUTOMATION_ID --yes --input '{"patch": [{"op": "replace", "path": "status", "value": "suspend"}]}'
# Resume (enable) -- the SDK sends this as the backend's real wire value ("restore"); pass "resume" here regardless
mammoth automation update AUTOMATION_ID --yes --input '{"patch": [{"op": "replace", "path": "status", "value": "resume"}]}'
# Change fields (name/description/tasks/conditions) -- at least one required
mammoth automation update AUTOMATION_ID --yes --input '{"patch": [{"op": "replace", "path": "details", "value": {"description": "new description"}}]}'
# Run immediately, independent of any recurrence condition
mammoth automation update AUTOMATION_ID --yes --input '{"patch": [{"op": "command", "path": "run", "value": {}}]}'
```

`patch` is the only top-level input field; a bare `name`/`description` field
is rejected (`missing_field`, `patch` is required) — this is documented
behavior, not a bug.

## Delete

```bash
mammoth automation delete AUTOMATION_ID --yes    # permanent
mammoth automation trash AUTOMATION_ID           # reversible; automation.restore undoes it
```

## Schedule (pull_cloud_data only)

```bash
mammoth schema get schedule.create
mammoth schedule create --yes --input '{"spec": {
  "rrule": {"frequency": "daily", "start": "2027-01-01T02:00:00Z"},
  "work_items": [{"name": "pull_cloud_data", "execution_params": {
    "schedule_type": "moment", "first_pull_at": "now", "on_refresh_action": "replace"
  }, "args": [DATASET_ID]}]
}}'
mammoth schedule get SCHEDULE_ID
mammoth schedule update SCHEDULE_ID --yes --input '{"patch": [{"op": "replace", "path": "status", "value": "pause"}]}'
mammoth schedule delete SCHEDULE_ID --yes
```
