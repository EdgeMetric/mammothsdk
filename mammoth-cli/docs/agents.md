# Agent and CI usage

[Documentation index](llms.txt)

This CLI targets autonomous agents and CI jobs.

## Machine behavior is automatic

Piping or redirecting output already yields the JSON envelope. `--no-input` also turns on automatically off a terminal. So an agent needs no flags for machine behavior.

To force it explicitly, or in an unusual TTY, pass `--output json --no-input`.

```bash
mammoth <command> --output json --no-input
```

Use `ndjson` for streamed results. Machine output suppresses color and progress rendering.

## Read the envelope, not the text

Success on stdout:

```json
{"schema_version": 1, "data": <result>, "meta": {"command": "...", "workspace_id": 4, "project_id": 180}}
```

Error on stderr:

```json
{"schema_version": 1, "error": {"code": "...", "message": "...", "hint": "...", "retryable": false, "recovery_commands": ["..."]}}
```

Branch on the exit code and the stable `error.code`. See [troubleshooting](troubleshooting.md) for the code table.

## Structured input

Pass multi-field requests as one document instead of many flags:

```bash
mammoth view transform math 1039 --project 180 --input '{"expression": "price * qty", "new_column": "total"}'
mammoth <command> --input request.yaml
echo '{"...": "..."}' | mammoth <command> --input - --input-format json
```

## Confirmations without a terminal

Destructive commands need `--yes`. High-impact commands also need `--confirm TARGET`. There is no prompt off a terminal. See [safety](safety.md).

## Discovery

```bash
mammoth capability list      # every operation
mammoth schema list          # every command's schema
mammoth schema get <command.id>
```

## Machine-readable docs

`docs/llms.txt` indexes the guides and command families. `docs/llms-full.txt` lists every command with its mutation class, confirmation policy, and backing SDK symbol.

For the full command list, see the [command reference](reference/commands.md). For login setup, see [authentication](authentication.md).
