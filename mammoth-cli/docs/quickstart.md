# Quick start: CSV to a transformed export

[Documentation index](llms.txt)

This guide completes a small, isolated loop. Choose a project, create a folder,
load a CSV, transform its default view, preview it, export it, and clean up.
The IDs in the snippets are placeholders. Keep IDs returned by your commands;
do not copy the example values into a shared project.

Output defaults to `auto`. A terminal gets a readable table. A pipe or redirect
gets JSON. So the examples below need no output flag.

## 1. Log in

```bash
mammoth auth login
```

The CLI prompts for your API key, API secret, and workspace id, then saves the
login for later commands. There is no `-w` login flag. Agents and CI pass a
protected file instead: `mammoth auth login --input creds.json --output json
--no-input`. See [authentication](authentication.md).

## 2. Pick a working project

```bash
mammoth project list
mammoth context project use 180
```

The active project applies to every later command. Add `--project ID` to one
command to target a different project without switching.

## 3. Make a folder to hold the work

```bash
mammoth folder create "Quickstart Demo"
```

The response includes the folder's `resource_id`. Copy it; the next step drops
the dataset straight into this folder.

## 4. Load a CSV into the folder

Load the sample retail dataset from its URL, and pass the `resource_id` from
step 3 as `folder_resource_id` so it lands in your folder:

```bash
mammoth dataset create --input '{
  "ds_creation_type": "weburl",
  "dataset_spec": {"url": "https://sampledata.mammoth.io/Multi-Store_Retail_Sales.csv"},
  "folder_resource_id": "FOLDER_RESOURCE_ID"
}'
```

The command waits for the load to finish and reports the result:

```json
{"status": "ready", "dataset_id": 303686, "job_id": 14794754}
```

Take the `dataset_id` into the next step. Have the file on disk instead? Upload
it directly — same folder field, same finished result:

```bash
mammoth file upload ./Multi-Store_Retail_Sales.csv --input '{"folder_resource_id": "FOLDER_RESOURCE_ID"}'
```

Both commands block until the dataset is ready, so there is no job id to poll by
hand.

## 5. Find the view

Transformations act on a view. Every dataset opens with a default one:

```bash
mammoth view list DATASET_ID
```

Take the `id` of the first view for the next steps.

## 6. Add a calculated column

Columns go by their display names, the same names shown in the app. Multiply
two of them into a new `revenue` column:

```bash
mammoth view transform math VIEW_ID --input '{"expression": "quantity_sold * unit_price", "new_column": "revenue"}'
```

Filter rows the same way, by column name:

```bash
mammoth view transform filter VIEW_ID --input '{"condition": {"column": "category", "operator": "EQ", "value": "Apparel"}}'
```

Both transforms run on the server, wait for the job, and refresh the view.

## 7. Preview the result

```bash
mammoth view preview VIEW_ID
```

Columns show their display names, including the new `revenue`. With no input it
returns 50 rows and every column. Adjust with
`--input '{"rows": 100, "cols": 10}'`. The dataset is resolved from the view; to
skip that lookup, pass it as `mammoth view preview VIEW_ID DATASET_ID`.

## 8. Download as a CSV

```bash
mammoth view export csv VIEW_ID
```

The CLI runs the export, waits for it, and writes the file to the current
directory. Choose the path with `--input '{"output_path": "./revenue.csv"}'`.

## 9. Clean up the demo

If this was a disposable exercise, remove the dataset you created. Deletion is
intentional: inspect the ID first, then pass `--yes`.

```bash
mammoth dataset delete DATASET_ID --yes
```

The folder may then be empty. Delete it only if it contains no work you need:

```bash
mammoth folder delete FOLDER_ID --yes --input '{"remove_contents": false}'
```

If a command needs an input you have not seen here, ask the installed CLI:

```bash
mammoth schema get view.transform.math --output json --no-input
```

## Where to go next

- [Authentication and project context](authentication.md)
- [Safe mutation and confirmation](safety.md)
- [Full command reference](reference/commands.md)
- Discover any command's inputs: `mammoth schema get view.transform.math`
