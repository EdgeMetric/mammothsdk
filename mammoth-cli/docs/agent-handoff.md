# Portable agent handoff

[Documentation index](llms.txt)

This is a portable, nonsecret checkpoint for transferring an in-progress
Mammoth task between external agents or sessions. It is a record, not a new
resume subcommand and not authority to bypass permissions. The receiving
agent chooses its own continuation plan after validation and fresh reads.

## Checkpoint format

Write UTF-8 JSON with no credentials, tokens, request headers, raw input
documents, or secret-bearing response bodies. Keep IDs and hashes needed to
identify and verify state. The following shape is normative; arrays may be
empty, and producers may add additional namespaced fields:

```json
{
  "format": "mammoth-agent-handoff",
  "format_version": 1,
  "created_at": "2026-09-15T12:00:00Z",
  "producer": {
    "cli_version": "1.1.2",
    "sdk_version": "0.7.0",
    "contract_schema_version": 1,
    "skill_version": "1.0.0"
  },
  "intent": "Create a verified Revenue column and export it as CSV",
  "acceptance_criteria": [
    "The selected view contains display column Revenue",
    "The complete CSV is present at the agreed artifact location"
  ],
  "authorization": {
    "profile": "production",
    "workspace_id": 4,
    "project_id": 180,
    "allowed_operations": ["read", "reversible_pipeline", "export"]
  },
  "resources": [
    {
      "kind": "view",
      "workspace_id": 4,
      "project_id": 180,
      "dataset_id": 303686,
      "view_id": 1039,
      "created_by_task": false,
      "depends_on": []
    }
  ],
  "last_verified": {
    "at": "2026-09-15T12:02:00Z",
    "state": "ready",
    "evidence": [
      {"kind": "view_get", "resource_id": "1039", "sha256": "..."}
    ]
  },
  "pending": {
    "jobs": [],
    "unknown_outcomes": []
  },
  "completed_actions": [
    {"operation": "view.get", "resource_id": "1039", "verified_at": "2026-09-15T12:02:00Z"}
  ],
  "remaining_objectives": ["Export and verify the artifact"],
  "cleanup": {
    "owner": "receiving-agent",
    "resources_created_by_task": [],
    "dependency_order": []
  },
  "checkpoint_sha256": "sha256-of-the-file-recorded-outside-the-file"
}
```

The `checkpoint_sha256` value is optional when the transport already authenticates
the file, but a tamper-evident hash should be stored beside the checkpoint when
possible. Evidence hashes are hashes of bounded, secret-free normalized output
or artifacts; do not hash or copy a credentials file.

## Writing atomically

Write the complete document beside the destination, flush and close it, then
atomically rename it over the old checkpoint on the same filesystem. Set owner
read/write permissions where the host supports them. Never expose a partially
written checkpoint at the agreed path:

```bash
umask 077
# A producer should write task-checkpoint.json.new, fsync/close it, then rename
# it to task-checkpoint.json. Keep a sidecar hash if the transport permits it.
sha256sum task-checkpoint.json > task-checkpoint.json.sha256
```

The shell snippet is illustrative; use the host's atomic-rename API when
writing programmatically.

## Receiving procedure

Before any mutation, the receiving agent should:

1. Parse the format/version and compare CLI, SDK, contract, and skill versions
   with the installed `mammoth` and the exact installed skill.
2. Validate the sidecar or recorded hash and reject malformed, tampered, or
   stale checkpoints. Treat an absent authorization block as insufficient.
3. Confirm the named profile exists, then verify that its current authorized
   workspace matches the checkpoint. Do not import credentials from the file.
4. Re-read every resource using the recorded workspace/project/dataset/view
   scope. Confirm parent relationships, current schema/display names, job
   state, and artifact evidence; do not assume the last verified state remains.
5. Reconcile every pending known job and `outcome_unknown` before creating,
   deleting, or resubmitting anything. A known job is inspected by its handle;
   an unknown mutation is resolved by reading the exact target and scope.
6. Choose a continuation plan that satisfies the remaining objectives, or stop
   with a precise unsupported/authorization/conflict result. Update the
   checkpoint after each verified material action.

An exit 7, timeout, or exit 130 does not authorize replay. Credentials, API
secrets, raw headers, and secret response fields must never enter this document,
an agent transcript, or an evidence hash.

## Related commands and references

The checkpoint can be inspected with ordinary reads and job commands; there is
no implicit resume command:

```bash
mammoth doctor --profile PROFILE --output json --no-input
mammoth view get VIEW_ID --project PROJECT_ID --output json --no-input
mammoth job get JOB_ID --output json --no-input
```

See [agent usage](agents.md), [safe mutation](safety.md), and
[troubleshooting](troubleshooting.md).
