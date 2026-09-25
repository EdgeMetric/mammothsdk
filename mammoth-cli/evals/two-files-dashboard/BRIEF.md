You are an agent helping a business user. You have a shell. Nothing about Mammoth is installed yet and you have no other context: no repository, no docs except what the tool you install gives you.

## The user's request (verbatim)
"I have two files, t_a and t_b. Create a dashboard from them in Mammoth."

The files:
- `EVAL_DIR/data/t_a.csv`
- `EVAL_DIR/data/t_b.csv`

## Setup rules
- Install the release under test from PyPI into a fresh virtual environment: `python3 -m venv WORK_DIR/venv && WORK_DIR/venv/bin/pip install --no-cache-dir mammoth-cli==VERSION_UNDER_TEST`. Confirm `mammoth --version` prints VERSION_UNDER_TEST before anything else. If pip cannot find that version, wait a minute and retry, up to five times. Never install any other version; if it is still missing, stop and report that. Use that environment's `mammoth` binary by absolute path for every command. Then load its guide with `mammoth skill show` and follow it.
- Credentials are already stored in the CLI profile named `release`; this task targets the release environment. Run every command with the environment variable `MAMMOTH_PROFILE=release`. Never look for, print, or handle credentials; never run `auth login`, `auth logout` or `config`. If auth fails, stop and report it.
- Work only in a new project named `haiku-coldstart-RUNID` (pick any short RUNID) created with `mammoth project ensure`. Do not read, change or delete anything outside that project.
- Use only the `mammoth` CLI. Do not use a web browser, do not call the REST API or Python SDK directly, and do not compute results locally and upload them. Do not read any source code. No web access.
- Dashboards cost money: create at most one dashboard. Do not use `dashboard v3 generate`, `chat`, `qa` or other AI routes.
- If one step fails twice with the same error, record it and move on to whatever else is possible.
- At the end, delete the project you created (`mammoth project delete PROJECT_ID --yes --confirm PROJECT_ID`) and confirm it is gone with a read.

## What to hand back
1. What you understood about the two files and how they relate, and how you found out (the commands and what they showed).
2. Each step you took, with the exact command, the outcome, and the ids created. Include read-backs that prove the data is right (row counts, sample rows, match rate of any join).
3. The dashboard you built: its id, what it shows, and how you confirmed it has data.
4. A friction log: every point where you guessed a command, field name or shape; got an error you did not understand; retried; or found the guide wrong, missing or misleading. Quote the exact error envelope. Mark each as `CLI bug`, `docs gap`, `backend` or `my mistake`.
5. Cleanup proof.

Claims must come from command output you actually saw; mark anything else UNVERIFIED.
