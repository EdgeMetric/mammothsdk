# Quick start: an explicit, verifiable CSV workflow

[Documentation index](llms.txt)

This walkthrough is one small example, not the complete CLI surface. It keeps
the project, dataset, and view IDs returned by each read. It uses display names
for columns, verifies each mutation, and cleans up only resources it created. A
dataset may have no usable default view, so the view is always selected
explicitly.

Output defaults to `auto`: a terminal gets a readable table, while a pipe or
redirect gets JSON. The commands below use explicit machine flags where a
script needs to parse the result.

## 1. Authenticate and choose scope

```bash
# Verify and read the installed agent skill before operating.
mammoth skill list --output json --no-input
mammoth skill path --output json --no-input
# Check whether the selected profile and stored credentials are present.
mammoth auth status --output json --no-input
# Compare the reported endpoint with the intended target before doctor:
# app is production; release is only for an explicitly intended release run.
# Human terminal only, if status shows no usable credentials:
mammoth auth login
mammoth doctor --output json --no-input
mammoth project list --output json --no-input
```

If the status endpoint is not the intended target, stop before `doctor` and
select or create a separate profile for the correct endpoint. Do not reuse a
production profile for release (or vice versa).

Select an authorized project and pass it explicitly on subsequent commands:

```bash
mammoth context project use PROJECT_ID --output json --no-input
```

For CI or an agent on POSIX, use a private owner-only (0600) credentials file
outside the repository with `mammoth auth login --input
/private/path/credentials.json --storage file --output json --no-input`; see
[authentication](authentication.md). Do not put secrets in chat, prompts, or
arguments. On Windows, use an approved OS keyring instead. An agent that finds
no credentials asks the operator to run the hidden-prompt login in their own
terminal; the CLI does not read credentials from environment variables.

## 2. Create and record a disposable resource

Discover the request shape before writing:

```bash
mammoth schema get folder.create --output json --no-input
```

Then create a folder and save its returned resource ID in your task record:

```bash
mammoth folder create "Quickstart Demo" --project PROJECT_ID \
  --output json --no-input
```

Use the returned `resource_id` as `FOLDER_RESOURCE_ID`; never copy the
placeholder into a shared project.

## 3. Load data and verify the dataset

```bash
mammoth dataset create --project PROJECT_ID --input '{
  "ds_creation_type": "weburl",
  "dataset_spec": {"url": "https://sampledata.mammoth.io/Multi-Store_Retail_Sales.csv"},
  "folder_resource_id": "FOLDER_RESOURCE_ID"
}' --output json --no-input
```

Record the returned `dataset_id` and any `job_id`. If the command reports a
known job, inspect or wait for that job; if a mutation times out without a
confirmed handle, treat the outcome as unknown and read the project/dataset
state before creating another dataset.

## 4. Discover and select a view explicitly

```bash
mammoth view list DATASET_ID --project PROJECT_ID --output json --no-input
mammoth view get VIEW_ID --project PROJECT_ID --output json --no-input
```

Choose the view whose returned identity and schema satisfy the task. Do not
assume the first, default, or only-looking view is correct. Save its
`dataset_id`, `view_id`, and displayed column names in the task record.

## 5. Transform with display names

Ask the installed CLI for the exact contract, then compose a request with the
names shown by `view get` or preview metadata:

```bash
mammoth schema get view.transform.math --output json --no-input
mammoth view transform math VIEW_ID --project PROJECT_ID \
  --input '{"expression": "Quantity Sold * Unit Price", "new_column": "Revenue"}' \
  --output json --no-input
```

Never substitute backend/internal column identifiers. If a display name is
missing or ambiguous, refresh the exact view schema and stop before mutation.

## 6. Verify, then export

```bash
mammoth view get VIEW_ID --project PROJECT_ID --output json --no-input
mammoth view preview VIEW_ID DATASET_ID --project PROJECT_ID \
  --input '{"rows": 50, "cols": 10}' --output json --no-input
mammoth view export csv VIEW_ID --project PROJECT_ID \
  --input '{"output_path": "./revenue.csv"}' --output json --no-input
```

Verify the returned schema contains `Revenue` and that the preview/export
matches the acceptance criteria. A completed process is not enough: compare
returned IDs, state, and artifact evidence. If an export job is known, inspect
it; if the write outcome is unknown, reconcile the remote export before
starting another export.

## 7. Clean up from the recorded dependency graph

Inspect the dataset you created, then delete it explicitly:

```bash
mammoth dataset get DATASET_ID --project PROJECT_ID --output json --no-input
mammoth dataset delete DATASET_ID --project PROJECT_ID --yes \
  --output json --no-input
```

Verify disappearance or the deletion job before removing its folder. Delete a
folder only when its dependency list proves it contains no work you need:

```bash
mammoth folder delete FOLDER_ID --project PROJECT_ID --yes \
  --input '{"remove_contents": false}' --output json --no-input
```

For handoff or interruption, write the nonsecret checkpoint in
[agent-handoff.md](agent-handoff.md). The receiving agent verifies scope and
remote state before deciding whether to continue, reconcile, or clean up.

## Where to go next

- [Authentication and project context](authentication.md)
- [Agent and CI usage](agents.md)
- [Safe mutation and confirmation](safety.md)
- [Output and errors](reference/output-and-errors.md)
- [Full command reference](reference/commands.md)
