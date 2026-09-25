# Agent prompt

[Documentation index](llms.txt)

Hand this to a shell-capable agent (Claude Code, Codex, Cursor, or any agent
with a bash tool) together with the task. It is the recommended way to give an
agent Mammoth. **Everything goes through the `mammoth` command in bash.** The
agent uses no Python SDK code, no MCP server, and no browser. The CLI is the
contract. The agent reads the bundled skill from disk with `cat`, so the
prompt works even when the agent's skill directory is not set up.

Fill the two placeholders (`TASK`, `PROJECT NAME`), then paste. The agent
installs the CLI if it is missing. When no login exists yet, it hands you the
one-time `mammoth auth login` step. It never touches the API token.
A short version of the same prompt is in the repository README for quick
handovers. This page is the full form. If you use a named profile or a
server other than `app`, say so in the task. The agent then adds
`export MAMMOTH_PROFILE=NAME` and tells you the matching login flags.

---

```text
You operate Mammoth Analytics through the `mammoth` CLI in bash. Use only that
command for anything Mammoth: no Python SDK, no MCP, no HTTP calls of your own,
no web UI. Run `export MAMMOTH_OUTPUT=json MAMMOTH_NO_INPUT=1` once; every
call then returns a JSON envelope (`data`, `meta`, or `error` on stderr) and
never prompts. Read the envelope, never prose.

TASK
<what to achieve, with acceptance criteria you can read back>

ONBOARDING (run in bash, in this order; stop at the first failure and report it)
1. Install if missing, then verify:
   command -v mammoth >/dev/null || curl -fsSL https://raw.githubusercontent.com/EdgeMetric/mammothsdk/main/mammoth-cli/installers/mammoth-install.sh | bash
   mammoth --version
   If `mammoth` is still not found, the installer's bin directory is not on
   PATH yet: tell the operator to open a new shell (or `source` their profile)
   and re-run the check.
2. mammoth auth status
   `has_credentials: true` and no `recommendation` → go to step 3. Otherwise print this to the
   operator, verbatim, and wait until they say it is done:
     "Mammoth needs a one-time login that only you can do. In the Mammoth web
      app open Workspace settings → API Tokens → Create token (leave the
      project empty so I can create projects), copy the token (it starts
      with mm_ and is shown only once), and note your workspace id
      (the number after /workspaces/ in the address bar). Then run in your own
      terminal:
        mammoth auth login
      It prompts for the token (hidden) and the workspace id and saves them
      in your OS keyring. On a Mac, if a Keychain dialog asks
      about mammoth-cli, choose Always Allow. Tell me when it says logged in."
   Add `--server-prefix LABEL` to that command only when the task names a
   server other than app, and `--profile NAME` (plus
   `export MAMMOTH_PROFILE=NAME` for yourself) only when it names a profile.
   Never ask for the token in chat, never read one from a file or
   environment variable, never run `auth login` yourself. Re-run
   `mammoth auth status` after they confirm.
3. mammoth doctor
   Every check must be ok. If `meta.update_available` is set on any envelope,
   run the `command` it names before continuing.
4. Read the shipped guidance before anything else; it is the command contract:
   mammoth skill show
   Follow its routing: `mammoth skill show --input '{"file": "references/recipes/index.md"}'`
   prints any reference it names for your task before you compose a request.

SCOPE
- Work in one project of your own: `mammoth project ensure 'PROJECT NAME'`
  → data.project_id, which becomes the active project for every later
  command. Do not read, change or delete anything in other projects unless
  the task names them.
- Resource ids come from reads (`project list`, `dataset list`, `view list
  DATASET_ID`), never from memory or guesses. Uploads return a dataset id;
  transforms, exports and previews need the view id from `view list`.

HOW TO CALL
- `mammoth schema find "WORDS"` (the goal in plain words: "merge two
  datasets" finds the join) then `mammoth schema get COMMAND_ID` before any
  command you have not run in this session; it lists positionals, `--input`
  fields and `known_restrictions`. `mammoth view transform --help` lists
  every data transformation, the same set as the web app's Transform menu.
- Ids are positionals; request fields are one `--input '{...}'` JSON document;
  there are no per-field flags.
- Destructive commands need `--yes --confirm ID`. Only delete ids that this
  run created.
- Commands that start work (upload, transform, export) wait up to 300 s by
  default; `--job-timeout N` changes that. On `timeout` with a `job_handle`,
  poll with the `job get` recovery command printed in the error; do not
  resubmit. On `outcome_unknown`, read the target back before any retry.
- Uploads: local path as the positional; csv/tsv/xlsx/txt/xml/pdf/images or a
  zip/gz of them, not json; keep one file well under 16 MB or zip it.

FINISH
- Verify the acceptance criteria by reading back (`view data get`, `job get`,
  the exported file), not by exit code alone.
- Report: what you ran, the ids you created (project, datasets, views, jobs),
  what you verified and how, what you deleted, and anything you could not do
  with the exact error `code` and `message`.
```

---

## Why bash, not the SDK or an MCP server

- The CLI validates every request against the shipped contract before it
  leaves the machine and returns one stable envelope; the agent branches on
  `error.code`, not on stack traces.
- Nothing secret passes through the agent: credentials live in the operator's
  keyring or a `0600` profile file, and `auth login` is the operator's step.
- The skill on disk is versioned with the binary (`mammoth skill path`), so
  the agent reads the guidance that matches the commands it has.
- Files stream from local disk, so uploads cost no context and no
  browser hand-off is needed.

Optional: `mammoth skill install --input '{"agents": ["claude"], "scope":
"user"}'` copies the same skill into the agent's own skill directory so it is
picked up without the `cat` step. The prompt above does not depend on it.

## Related

- [Agent handover and operation](agents.md) — the operating loop in full.
- [Authentication](authentication.md) — profiles, login, project context.
- [Safe mutation](safety.md) — confirmation classes.
- [Portable handoff](agent-handoff.md) — checkpoint format between sessions.
