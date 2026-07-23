# Output and error envelopes

[Documentation index](../llms.txt)

Every command returns a stable, versioned envelope. Success envelopes print to
stdout. Error envelopes print to stderr. Both carry `schema_version`, which is a
compatibility contract you can depend on.

## Output modes

The `--output` flag selects how results render. Machine modes always emit the
envelope. Human modes render for a terminal reader.

| Mode | Kind | Description |
|---|---|---|
| `auto` | adaptive | Default. A table on a terminal, JSON when piped or redirected. |
| `table` | human | Aligned columns for terminal reading. |
| `json` | machine | The full envelope as one JSON object. |
| `yaml` | human | The envelope rendered as YAML. |
| `ndjson` | machine | One JSON object per line for streaming. |
| `plain` | human | Minimal text with no color or borders. |

The `auto` rule keeps interactive use readable and scripted use parseable. On a
terminal, `auto` renders a table. Off a terminal, `auto` emits JSON.

The `json` and `ndjson` modes are the machine contract. They always emit the
envelope. They never add color or progress output.

## Success envelope

A successful command prints this shape to stdout.

```json
{"schema_version": 1, "data": <result>, "meta": {"command": "...", "profile": "...", "workspace_id": 4, "project_id": 180, "pagination": null}}
```

The `data` field holds the command result. The `meta` field records the command
name, active profile, workspace, project, and pagination state.

A project list looks like this.

```json
{
  "schema_version": 1,
  "data": [
    {"id": 180, "name": "Sales"},
    {"id": 181, "name": "Marketing"}
  ],
  "meta": {
    "command": "project list",
    "profile": "default",
    "workspace_id": 4,
    "project_id": 180,
    "pagination": null
  }
}
```

## Error envelope

A failed command prints this shape to stderr and sets a non-zero exit code.

```json
{"schema_version": 1, "error": {"code": "...", "message": "...", "hint": "...", "details": {}, "request_id": null, "retryable": false, "authorization_required": false, "recovery_commands": ["..."]}}
```

Each field has a fixed meaning.

| Field | Meaning |
|---|---|
| `code` | Stable machine identifier for the failure. Branch on this. |
| `message` | Human-readable summary. Do not parse it. |
| `hint` | Optional suggestion for fixing the problem. |
| `details` | Structured context about the failure. |
| `request_id` | Server request id, or `null`. Cite it in support tickets. |
| `retryable` | `true` when a retry may succeed. |
| `authorization_required` | `true` when the caller must authenticate. |
| `recovery_commands` | Exact commands to run next. |

Branch on `error.code`, never on the message text. The `code` value is stable
across releases. The `message` text may change. See [troubleshooting](../troubleshooting.md)
for common codes and their recovery steps. See [agents](../agents.md) for the
scripted error-handling pattern.

## Exit codes

The process exit code mirrors the error class. There is no exit code 3.

| Code | Meaning |
|---|---|
| 0 | Success. |
| 1 | API error. |
| 2 | Usage, input, or confirmation failure. |
| 4 | Authentication failure. |
| 5 | Not found. |
| 6 | Conflict. |
| 7 | Retryable (network or timeout). |
| 130 | Interrupted. |

## Schema version

The `schema_version` field is currently `1`. It is a compatibility contract.
A breaking change to the envelope shape increments this number. Check it if you
parse envelopes across CLI upgrades.
