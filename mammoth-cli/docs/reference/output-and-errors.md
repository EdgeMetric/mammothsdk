# Output and error envelopes

[Documentation index](../llms.txt)

Machine modes return a versioned envelope: successes go to stdout and failures
to stderr. Both carry `schema_version`. Treat the process exit code and the
stable error `code` as the control-flow interface; the prose message is for a
human reader. For resource operations, also inspect `details.operation_state`
and the returned resource/job identity. A zero exit is not a substitute for
read-back verification.

## Output modes

The `--output` flag selects how results render. Machine modes always emit the
envelope. Human modes render for a terminal reader.

| Mode | Kind | Description |
|---|---|---|
| `auto` | adaptive | Default. A table on a terminal, JSON when piped or redirected. |
| `table` | human | Aligned columns for terminal reading. |
| `json` | machine | The full envelope as one JSON object. |
| `yaml` | human | The envelope rendered as YAML. |
| `ndjson` | machine | Versioned lifecycle frames, one JSON object per line. |
| `plain` | human | Minimal text with no color or borders. |

The `auto` rule keeps interactive use readable and scripted use parseable. On a
terminal, `auto` renders a table. Off a terminal, `auto` emits JSON.

The `json` and `ndjson` modes are the machine contract. They always emit the
envelope. They never add color or progress output.

`json` emits exactly one complete object. `ndjson` emits a versioned lifecycle
stream; diagnostics remain on stderr. Do not concatenate partial objects or
infer continuation from a missing terminal frame. Use the stream's `meta.pagination`
or documented continuation fields.

## NDJSON v2 migration

`--output ndjson` now emits `stream_version: 2` lifecycle frames. This is a
wire-format change from the former item-only stream. Consumers must switch on
`event`, not assume every line is a result item. The public renderer retains an
explicit embedded-caller compatibility path (`ndjson_legacy=True`); the CLI has
no legacy-output flag.

Successful streams write these frames to **stdout**:

1. `start` with the complete `meta` object, including bounded pagination metadata.
2. Zero or more `item` frames with `index` and `data`.
3. Exactly one `end` frame with `complete: true`, `count`, and the complete `meta` object.

An empty list is therefore `start` then `end` with `count: 0`, not an empty
byte stream. A successful scalar `data: null` is one `item` frame whose `data`
is `null`, followed by `end` with `count: 1`; it is distinct from an empty list.

When failure occurs before `start`, stdout is empty. A failure after `start` or
an `item` leaves those already-written stdout frames intact, but never writes
an `end`/`complete: true` frame. When stderr remains writable, it receives one
terminal `error` frame with `complete: false` and the normal error envelope
payload. A broken stderr or terminated process cannot guarantee that error
frame. An absent `end` frame means the stream is incomplete (for example, the
caller lost the process or transport) and must not be treated as success.

Example successful list stream:

```json
{"event":"start","meta":{"pagination":{"next_cursor":"opaque","has_more":true}},"schema_version":1,"stream_version":2}
{"data":{"id":1},"event":"item","index":0,"schema_version":1,"stream_version":2}
{"complete":true,"count":1,"event":"end","meta":{"pagination":{"next_cursor":"opaque","has_more":true}},"schema_version":1,"stream_version":2}
```

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

When present in `details`, `operation_state` is one of `not_started`, `running`,
`succeeded`, `failed`, or `outcome_unknown`. A known job is safe to inspect or
wait by its returned handle. `outcome_unknown` means a mutation may have
committed; reconcile the exact target and scope before replaying it.

Branch on `error.code`, never on the message text. The `code` value is stable
across releases. The `message` text may change. See [troubleshooting](../troubleshooting.md)
for common codes and their recovery steps. See [agents](../agents.md) for the
scripted error-handling pattern.

When you save a successful result, save the `data` you need and preserve the
associated IDs. Do not assume a table layout or scrape the human renderer.

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
| 7 | Retryable read/transport condition, or a timed-out known job; inspect the envelope before acting. |
| 130 | Interrupted. |

## Schema version

The `schema_version` field is currently `1`. It is a compatibility contract.
A breaking change to the envelope shape increments this number. Check it if you
parse envelopes across CLI upgrades.
