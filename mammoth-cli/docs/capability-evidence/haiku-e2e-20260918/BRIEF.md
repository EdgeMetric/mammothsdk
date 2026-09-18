You are a data analyst's assistant. You have the `mammoth` CLI installed and a skill that documents it. Do the task below end to end using only the CLI, and keep a candid log of every point where the CLI or its documentation made you guess, retry, or stop.

## Setup you must follow
- CLI binary: `/home/euler/mammoth/mammothsdk/mammoth-cli/.venv/bin/mammoth` (use this absolute path every time).
- Read the bundled skill first: `/home/euler/mammoth/mammothsdk/mammoth-cli/mammoth_cli/bundled_skill/mammoth-cli/SKILL.md` and follow the files it points to when you need them (`references/task-start.md`, the recipes). Prefer `mammoth schema find` / `mammoth schema get COMMAND_ID --output json --no-input` over guessing.
- Credentials are already stored in the profile named `release`. Pass `--profile release --output json --no-input` on every command. Never look for, print, or handle credentials; never run `auth login/logout` or `config`. If auth fails, stop and say so.
- Work only in project 3 (`--project 3`). Pre-existing datasets 28, 29, 30, 31, 33, their views, and dashboard 48 must never be modified, transformed, or deleted. Mutate only resources you created in this run. At the end delete what you created (datasets, dashboard), then confirm with `dataset list` and `dashboard list` that only the pre-existing ones remain.
- Dashboards cost money: at most one dashboard, created with `dashboard create-blank`; then one canvas save, one `pages add`, one `pdf export`; then trash and delete it. Do not use `dashboard v3 generate`, `chat`, `qa`, or any AI route.
- Do not read or modify repository source code. No web access. Do not run tests.
- Time-box: if one step fails twice with the same error, record it and move on to whatever remains possible.

## The task
Files (upload these; do not edit them):
- `/tmp/claude-1000/-home-euler-mammoth-mammothsdk/aec77d33-c4b6-4a6f-b36b-5bb563cd5a89/scratchpad/haiku-e2e/data/stores.csv` — store_id, store_name, region, opened_on
- `.../data/sales_2025.csv` — store_id, month, units, revenue, lfl_growth_pct (has some blank revenue and some negative units)
- `.../data/targets.csv` — region, annual_target

1. Upload all three as datasets. If any dataset stops in a `need_action` status, resolve it with the CLI (the skill has a recipe) — do not ask a human to use the UI.
2. On the sales dataset's view: remove rows where `units` is negative; fill blank `revenue` with 0; make sure `revenue` and `units` are numeric.
3. Enrich sales with the store's `region` (join or lookup on `store_id` against the stores dataset), then bring in `annual_target` by `region` from targets.
4. Produce a per-region summary: total revenue, total units, and `annual_target`, as a new dataset (pivot/crosstab/export to dataset — whichever the CLI supports; verify the result with a data read).
5. Build one blank dashboard, add one page, save a canvas that references the summary dataset (keep it minimal; a title text and one table/chart is enough), export a PDF, confirm the artifact exists.
6. Clean up your own resources and prove the baseline is intact.

## What to hand back
A report with:
- For each step: the exact commands you ran (redact nothing except there is nothing secret in them), the outcome, and the ids you created.
- **Friction log** — the important part. Every time you: had to guess a field name or shape; got an error you did not understand; retried; found the skill/docs wrong, missing, or misleading; found a `schema get` example that did not run as printed; had to work around something. Quote the exact error envelope. Mark each as `CLI bug`, `docs gap`, `backend`, or `my mistake`.
- What you could not do and why.
- Final `dataset list` and `dashboard list` output showing the baseline.
Claims must come from command output you actually saw; mark anything else UNVERIFIED.
