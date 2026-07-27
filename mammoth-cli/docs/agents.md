# Agent and CI usage

[Documentation index](llms.txt)

This guide is for automation that must be safe to repeat and straightforward to diagnose.
Use the human guides for concepts; use runtime schemas rather than guessing an
operation's request fields.

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

Keep credentials out of arguments. Login once from a `0600` file, then verify
the profile before making changes:

```bash
chmod 600 creds.json
mammoth auth login --input creds.json --output json --no-input
mammoth doctor --output json --no-input
```

## Confirmations without a terminal

Destructive commands need `--yes`. High-impact commands also need `--confirm TARGET`. There is no prompt off a terminal. See [safety](safety.md).

## Discovery

```bash
mammoth capability list      # every operation
mammoth schema list          # every command's schema
mammoth schema get <command.id>
```

## A reliable operation loop

1. Discover the command and request shape with `schema get`.
2. Run reads with `--output json --no-input` and retain returned IDs.
3. For a mutation, supply its structured input and required `--yes` / `--confirm`.
4. Inspect the exit code and `error.code`; retry only exit code `7`.
5. Delete temporary resources when the run is complete.

## Machine-readable docs

`docs/llms.txt` indexes the guides and command families. `docs/llms-full.txt` lists every command with its mutation class, confirmation policy, and backing SDK symbol.

For the full command list, see the [command reference](reference/commands.md). For login setup, see [authentication](authentication.md).
