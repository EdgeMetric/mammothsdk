# Quick start: CSV to a transformed export

[Documentation index](llms.txt)

The mammoth CLI drives the Mammoth Analytics platform from your shell. This
guide runs the whole loop end to end in about two minutes. You pick a project,
make a folder, load a sample CSV into that folder, add a calculated column,
preview the result, and download it back as a CSV.

Output defaults to `auto`. A terminal gets a readable table. A pipe or redirect
gets JSON. So the examples below need no output flag.

## 1. Log in

```bash
mammoth auth login
```

The CLI prompts for your API key, then your API secret, then your workspace id.
It saves the login in your OS keyring and reuses it on later commands. Agents
and CI pass a file instead with `mammoth auth login --input creds.json`. See
[authentication](authentication.md).

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

## Where to go next

- [Authentication and project context](authentication.md)
- [Safe mutation and confirmation](safety.md)
- [Full command reference](reference/commands.md)
- Discover any command's inputs: `mammoth schema get view.transform.math`
