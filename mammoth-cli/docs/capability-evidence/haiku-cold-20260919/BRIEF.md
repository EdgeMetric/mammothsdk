You are a data analyst's assistant. You have never used the Mammoth CLI before and you have no skill or notes about it. Install it, learn it from the skill it ships, and do the task below end to end using only the CLI. Keep a candid log of every point where the CLI or its documentation made you guess, retry, or stop.

## Setup you must follow
- Install: create a fresh virtualenv at `<run-dir>/venv` with `python3 -m venv` and `pip install mammoth-cli==2.0.18` (PyPI). Use `<that venv>/bin/mammoth` with the absolute path every time. Do NOT run the curl installer and do NOT run `mammoth skill install` (do not write into ~/.claude or any global location).
- Learn: run `mammoth skill path --output json --no-input` to find the bundled skill directory, read its `SKILL.md`, and follow the files it points to (`references/task-start.md`, `references/capabilities.md`, the recipes) as you need them. Prefer `mammoth schema find` / `mammoth schema get COMMAND_ID --output json --no-input` over guessing. Do not read anything else on this machine except the data files below and the skill directory.
- Credentials: a profile named `release` already exists. Pass `--profile release --output json --no-input` on every command. Never look for, print, or handle credentials; never run `auth login/logout`, `config`, or `doctor --fix`. If auth fails, stop and say so.
- Scope: FIRST create your own project with `project create` (name `haiku-cold-20260919`) and do everything with `--project THAT_ID`. Never touch project 3 or any resource you did not create. At the end delete everything you created (datasets, dashboard, then the project) and confirm with `project list` that your project is gone.
- Dashboards cost money: at most one dashboard, created with `dashboard create-blank`; then one `pages add`, one canvas save, one `pdf export` attempt; then trash and delete it. Do not use `dashboard v3 generate`, `chat`, `qa`, or any AI route.
- No web access other than `pip install`. Do not run tests. Do not read repository source code.
- Time-box: if one step fails twice with the same error, record it and move on to whatever remains possible. Stop after 75 minutes regardless.
- Deleting your project needs `--yes --confirm PROJECT_ID` (the CLI tells you so). Follow the skill's `references/report-checklist.md` before you report a number.

## The data (messy on purpose; upload as-is, do not edit the files)
Directory: `<run-dir>/data/`
- `customers.csv` — customer_id, customer_name (stray spaces / mixed case), region (mixed case, padding, some blank), signup_date (mixed formats, some blank), plan (mixed case/padding)
- `orders.csv` — order_id, customer_id (a few ids have no customer), order_date (mixed formats), amount (some like `$1,234.56`, some blank, some negative), qty (some negative, blank or zero), status (mixed case/padding); contains exact duplicate rows
- `targets.csv` — region, monthly_target

## The task
1. Upload all three as datasets. If any lands in `need_action`, resolve it with the CLI (the skill has a recipe).
2. Clean orders on its view: remove exact duplicate rows; make `amount` numeric (strip `$` and `,` first); fill blank `amount` with 0; remove rows where `qty` is negative or blank; normalise `status` (trim, lower case); make `order_date` a DATE.
3. Clean customers: trim and title-case `region`; fill blank `region` with `Unknown`; trim `customer_name`.
4. Enrich orders with the customer's `region` (join/lookup on `customer_id`); then bring `monthly_target` in by `region` from targets. Say how many orders had no matching customer.
5. Produce a per-region summary: total amount, total qty, order count, `monthly_target`; the skill's transforms and end-to-end recipes say how (export the cleaned rows first, then pivot as the last step, or a SQL task); read it back with a data read and include the table in your report, and say in one line why the numbers are plausible (they must add up to the cleaned order count and not be all zero). Also export the cleaned orders view to a local CSV file in this directory and state its row count.
6. Build one blank dashboard, add one page, save a canvas that references the summary dataset (a title text and one table/chart), try a PDF export, report what happened.
7. Clean up your own resources and prove your project is gone.

## What to hand back (as your final message; also write it to `REPORT.md` in this directory if you are allowed to write files)
- Install and learn: what you ran, how long it took to find and read the skill, whether the skill's routing got you to the right recipe first time.
- For each step: the exact commands you ran, the outcome, and the ids you created.
- **Friction log** — the important part. Every time you: had to guess a field name or shape; got an error you did not understand; retried; found the skill/docs wrong, missing, or misleading; found a `schema get` example that did not run as printed; had to work around something. Quote the exact error envelope. Mark each as `CLI bug`, `docs gap`, `backend`, or `my mistake`.
- What you could not do and why.
- Final `project list` output.
- The `log_ref.run_id` of any error envelope you quote, and the output of `mammoth log tail --input '{"errors_only": true, "limit": 20}' --profile release --output json --no-input` at the end (it is local, it holds no secrets).
Claims must come from command output you actually saw; mark anything else UNVERIFIED.
