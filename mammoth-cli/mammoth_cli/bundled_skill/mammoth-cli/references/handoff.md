# Portable task handoff

Use a nonsecret JSON checkpoint when another agent or session must continue.
This is a record, not a resume subcommand. The receiving agent chooses
its own plan only after fresh reads.

A handoff may reference the authorized profile name, but must not copy its
path or contents into the checkpoint. The receiving agent re-checks
`auth status` and `doctor`; if credentials are missing on its host, the
operator logs in from their own terminal as described in [auth](auth.md).

## Required record

Include `format: "mammoth-agent-handoff"`, `format_version`, producer
`cli_version`, `sdk_version`, `contract_schema_version`, and `skill_version`
(the `version:` field in this skill's `SKILL.md` frontmatter; `mammoth
--version` gives the other two);
the intent and acceptance criteria; authorized `profile` name and exact
workspace/project scope; observed resources with dataset/view parents and
dependencies; last verified state and hashes of bounded secret-free evidence;
pending known jobs and `unknown_outcomes`; completed actions; remaining
objectives; and a cleanup owner plus dependency order.

Never include API keys, API secrets, tokens, headers, credentials files, raw
secret-bearing input, or unredacted response bodies. IDs and display names are
safe only when needed to identify the authorized task.

Write the file atomically: write a same-directory temporary file, flush and
close it, then rename it over the destination. Keep a sidecar SHA-256 when the
transport permits it. Do not publish a partially written checkpoint.

## Receiving a checkpoint

1. Compare the recorded CLI/SDK/contract/skill versions with the installed
   versions and read the exact installed skill.
2. Validate the format, sidecar hash, authorized scope, and profile. Do not
   import credentials from the checkpoint.
3. Re-read every resource with its recorded workspace/project/dataset/view
   parent. Verify current schema, display names, jobs, and artifact evidence.
4. Inspect every known job and reconcile every `outcome_unknown` before any
   mutation. A timeout or exit 130 does not authorize replay.
5. Continue, clean up, or stop with a precise unsupported/authorization/
   conflict result. Update the checkpoint after each verified action.

Useful read commands include:

```bash
mammoth doctor --profile PROFILE --output json --no-input
mammoth view get VIEW_ID --project PROJECT_ID --output json --no-input
mammoth job get JOB_ID --output json --no-input
```

The required fields and receiving procedure above are self-contained for a
cold-start agent; no repository checkout or unshipped document is required.
