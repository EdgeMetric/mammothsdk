You are a data engineer's assistant. You have never used the Mammoth CLI before and have no notes about it. Install it, learn it from the skill it ships, and do the task below end to end using only the CLI. Keep a candid log of every point where the CLI or its documentation made you guess, retry, or stop.

## Setup you must follow
- Install: create a fresh virtualenv at `<run-dir>/venv` with `python3 -m venv` and `pip install mammoth-cli==2.0.23` (PyPI). Put `<run-dir>/venv/bin` first on PATH for your shell so `mammoth` resolves to it. Do NOT run the curl installer and do NOT run `mammoth skill install` (do not write into ~/.claude or any global location).
- Session defaults, once, in every shell you use: `export MAMMOTH_PROFILE=release MAMMOTH_OUTPUT=json MAMMOTH_NO_INPUT=1`. After that do not pass `--profile`, `--output` or `--no-input` on any command; if you find you need one of them anyway, that is a friction item — record it.
- Learn: `mammoth skill path` → read `SKILL.md` in `data.canonical`, then the files it routes you to (`references/task-start.md`, the recipes under `references/recipes/`, `references/commands/*.md`). Use `mammoth schema find "WORDS"` and `mammoth schema get COMMAND_ID` before any command you have not run yet (`schema get ... --input '{"full": true}'` for the JSON Schema when the brief form is not enough). Do not read anything else on this machine except the data files below and the skill directory.
- Credentials: a profile named `release` already exists with credentials in the OS keyring. Never look for, print, or handle credentials; never run `auth login/logout`, `config set`, or `doctor --fix`. If `mammoth doctor` fails on auth, stop and say so.
- Scope: create your own projects with `mammoth project ensure NAME` — first `haiku-etl-2023-src` (all the ETL happens here) and later `haiku-etl-2023-target` (the cross-project delivery). `project ensure` makes the project active, so no `--project` is needed; when you switch projects use `mammoth context project use PROJECT_ID` (or `--project` on the single command). Never touch project 3 or any resource you did not create. At the end delete everything you created (datasets, then both projects) and prove with `project list` that both are gone.
- No dashboards, no AI routes (`ai *`, `dashboard v3 generate/chat/qa`), no web access other than `pip install`. Do not run tests. Do not read repository source code.
- Time-box: if one step fails twice with the same error, record it and move on. Stop after 90 minutes regardless.
- Follow the skill's `references/report-checklist.md` before you report a number. Claims must come from command output you actually saw; mark anything else UNVERIFIED.

## The data (messy on purpose; upload as-is, do not edit the files)
Directory: `<run-dir>/data/`
- `customers.csv` — customer_id (zero-padded text like `001`, one has a leading space), customer_name (stray spaces / mixed case), region (mixed case, padding, some blank), currency (mixed case). Two customer_ids appear twice with different regions.
- `orders.csv` — order_id, customer_id (plain integers; a few have no customer), order_date (mixed formats, some blank), amount (`$1,234.56` style, plain, blank, or negative), qty (blank, zero, negative), currency (mixed case, some blank), status (mixed case/padding). Contains exact duplicate rows.
- `fx.csv` — currency, month (`2026-01`), rate_to_usd. Composite key.
- `targets.csv` — region, monthly_target.

## The task
1. In the source project upload all four files. Resolve any `need_action` dataset with the CLI (the skill has a recipe). Record the row counts you start from.
2. Clean orders on its view: remove exact duplicates; `amount` numeric (strip `$` and `,` first) with blanks → 0; drop rows with negative or blank `qty`; normalise `status` and `currency` (trim, upper case for currency, lower case for status); blank `currency` → `USD`; `order_date` → DATE.
3. Clean customers: trim and title-case `region`, blank → `Unknown`; trim `customer_name`; upper-case `currency`. **Deduplicate on customer_id** (keep one row per id) and state how many rows that removed — a later join must not fan out.
4. **Tricky join 1 — key types differ.** Orders carry `customer_id` as a number, customers as zero-padded text (`001`, one with a leading space). Bring the customer's `region` onto orders. First try the join as-is and measure the match rate (`view data get` / a filter on the joined column); then fix the key (convert or pad on one side — the skill's transforms reference lists the operations) and join again. Report both match rates and the number of orders that genuinely have no customer (ids 41–45).
5. **Tricky join 2 — composite key.** Bring `rate_to_usd` onto orders from fx by (`currency`, month of `order_date`). You will need a month column derived from `order_date` (`extract-date` or a text operation) shaped like fx's `month`. Then compute `amount_usd = amount * rate_to_usd` with the math transform. Orders whose month or currency has no fx row must be visible: say how many, and what `amount_usd` shows for them.
6. Enrich with `monthly_target` from targets by `region` and export the enriched orders view to a local CSV in this directory (state the row count and the header).
7. **Cross-project delivery.** Create the target project. Get the enriched orders into it as a dataset, and say exactly which route worked:
   a. try `view export dataset` from the source view with a target dataset that lives in the target project (you will have to create that dataset in the target project first, e.g. by uploading the exported CSV or a header-only file, then use `target_ds_id`); quote the exact error if the backend refuses cross-project targets;
   b. if (a) is refused, `file upload` the exported CSV into the target project.
   Prove the delivery with `dataset get` / `view data get` in the target project: row count and one spot-check row that matches the source.
8. Back in the source project, produce a per-region summary (total `amount_usd`, order count, `monthly_target`) as the **last** step on the enriched view (pivot or a SQL task; the end-to-end recipe explains why it is last), read it back, include the table, and say in one line why the numbers are plausible (order counts add up to the cleaned row count; region `Unknown` holds the unmatched customers).
9. Clean up both projects and prove they are gone.

## What to hand back (as your final message; also write it to `REPORT.md` in this directory)
- Install and learn: what you ran, how long it took to find and read the skill, whether the skill's routing got you to the right recipe first time, and whether the session defaults (no repeated flags, active project, view id alone after `view list`) held or where they did not.
- For each step: the exact commands you ran, the outcome, and the ids you created.
- **Friction log** — the important part. Every time you: had to guess a field name or shape; got an error you did not understand; retried; found the skill/docs wrong, missing, or misleading; found a `schema get` example that did not run as printed; had to work around something. Quote the exact error envelope (they are compact JSON; quote them as printed). Mark each as `CLI bug`, `docs gap`, `backend`, or `my mistake`.
- Token/verbosity notes: any command whose output was much larger than you needed, and what you would have wanted instead.
- What you could not do and why.
- Final `project list` output.
- The `log_ref.run_id` of any error envelope you quote, and the output of `mammoth log tail --input '{"errors_only": true, "limit": 30}'` at the end (it is local, it holds no secrets).
