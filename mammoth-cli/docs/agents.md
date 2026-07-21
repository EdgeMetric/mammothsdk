# Agent and CI usage

[Documentation index](llms.txt)

The CLI is built to be driven by autonomous agents and CI jobs.

## Always run in machine mode

```bash
mammoth <command> --output json --no-input
```

- `--output json` (or `ndjson` for streams) emits a stable envelope.
- `--no-input` never prompts; a missing required input fails instead of waiting.
- `--no-progress` and machine output suppress color and progress rendering.

## Read the envelope, not the text

Success on stdout:

```json
{"schema_version": 1, "data": <result>, "meta": {"command": "...", "workspace_id": 4, "project_id": 180}}
```

Error on stderr:

```json
{"schema_version": 1, "error": {"code": "...", "message": "...", "hint": "...", "retryable": false, "recovery_commands": ["..."]}}
```

Branch on the exit code and the stable `error.code`. See
[troubleshooting](troubleshooting.md) for the code table.

## Structured input

Pass multi-field requests as one document instead of many flags:

```bash
mammoth view transform math 1039 --project 180 --output json --no-input \
  --input '{"expression": "price * qty", "new_column": "total"}'
mammoth <command> --input request.yaml --output json --no-input
echo '{"...": "..."}' | mammoth <command> --input - --input-format json --output json --no-input
```

## Confirmations without a terminal

Destructive commands need `--yes`; high-impact commands also need
`--confirm TARGET`. There is no prompt under `--no-input`. See
[safety](safety.md).

## Discovery

```bash
mammoth capability list --output json --no-input      # every operation
mammoth schema list --output json --no-input          # every command's schema
mammoth schema get <command.id> --output json --no-input
```

## Machine-readable docs

`docs/llms.txt` indexes the guides and command families; `docs/llms-full.txt`
lists every command with its mutation class, confirmation policy, and backing
SDK symbol.
