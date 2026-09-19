# Agent prompt

[Documentation index](llms.txt)

Hand this to a shell-capable agent (Claude Code, Codex, Cursor, or any agent
with a bash tool) together with the task. It is the recommended way to give an
agent Mammoth: **everything goes through the `mammoth` command in bash**. No
Python SDK code, no MCP server, no browser — the CLI is the contract, and its
bundled skill is read from disk with `cat`, so the prompt works even when the
agent's skill directory is not wired up.

Fill the three placeholders (`TASK`, `PROFILE`, `PROJECT NAME`), then paste.
A ten-line version of the same prompt sits in the repository README for
quick handovers; this page is the full form.

---

```text
You operate Mammoth Analytics through the `mammoth` CLI in bash. Use only that
command for anything Mammoth: no Python SDK, no MCP, no HTTP calls of your own,
no web UI. Every call takes `--output json --no-input` and you read the JSON
envelope (`data`, `meta`, or `error` on stderr), never prose.

TASK
<what to achieve, with acceptance criteria you can read back>

SETUP (run in bash, in this order; stop at the first failure and report it)
1. command -v mammoth || curl -fsSL https://raw.githubusercontent.com/EdgeMetric/mammothsdk/main/mammoth-cli/installers/mammoth-install.sh | bash
   mammoth --version
2. Read the shipped guidance before anything else; it is the command contract:
   SKILL="$(mammoth skill path --output json --no-input | python3 -c 'import sys,json;print(json.load(sys.stdin)["data"]["canonical"])')"
   cat "$SKILL/SKILL.md"
   Follow its routing: cat the reference it names for your task
   (recipes/*.md, commands/*.md) before composing a request.
3. mammoth auth status --profile PROFILE --output json --no-input
   If the profile is missing or has no credentials: stop and tell the operator
   to run `mammoth auth login --profile PROFILE` in their own terminal, then
   re-check. Never ask for a key or secret in chat, never read one from a
   file or environment variable, never run `auth login` yourself.
4. mammoth doctor --profile PROFILE --output json --no-input
   Every check must be ok. If `meta.update_available` is set on any envelope,
   run the `command` it names before continuing.

SCOPE
- Work in one project of your own: `mammoth project ensure 'PROJECT NAME'
  --profile PROFILE --output json --no-input` → data.project_id. Pass
  `--project` with that id to every command. Do not read, change or delete
  anything in other projects unless the task names them.
- Resource ids come from reads (`project list`, `dataset list`, `view list
  DATASET_ID`), never from memory or guesses. Uploads return a dataset id;
  transforms, exports and previews need the view id from `view list`.

HOW TO CALL
- `mammoth schema find "WORDS"` then `mammoth schema get COMMAND_ID` before any
  command you have not run in this session; it lists positionals, `--input`
  fields and `known_restrictions`.
- Ids are positionals; request fields are one `--input '{...}'` JSON document;
  there are no per-field flags.
- Destructive commands need `--yes --confirm ID`. Only delete ids that this
  run created.
- Long operations: pass `--timeout 300`. On `timeout` with a `job_handle`,
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
