# Global flags

[Documentation index](../llms.txt)

Commands expose a shared set of global flags. They control rendering, profile
selection, time limits, structured input, and confirmations. Command-specific
arguments remain discoverable through `mammoth COMMAND --help` or `mammoth
schema get COMMAND.ID`.

| Flag | Purpose |
|---|---|
| `--output`, `-o` | Output format: `auto`, `table`, `json`, `yaml`, `ndjson`, or `plain`. Default `auto`. |
| `--profile` | Credential profile name to use. |
| `--project` | Active project id override. |
| `--timeout` | Per-request timeout in seconds. |
| `--job-timeout` | Job-wait timeout in seconds. |
| `--pipeline-timeout` | Pipeline-wait timeout in seconds. |
| `--color` | Color policy: `auto`, `always`, or `never`. Default `auto`. |
| `--no-input` | Never prompt; fail instead. It turns on automatically off a terminal. |
| `--no-progress` | Never render progress. |
| `--debug` | Emit diagnostic detail to stderr. |
| `--input` | Strict JSON or YAML request document path, or `-` for stdin. |
| `--input-format` | Input document format: `json` or `yaml`. Required for `--input -`. |
| `--yes`, `-y` | Confirm a mutation without prompting. |
| `--confirm TARGET` | Exact target name required for high-impact actions. |

## Choosing an output format

The default `auto` mode adapts to context. On a terminal it renders a table for
a human reader. Off a terminal it emits JSON for parsing. Set an explicit mode when
you need a fixed format.

Use `--output json` for scripts and agents. It always emits the full envelope. It
never adds color or progress output. See [output and error envelopes](output-and-errors.md)
for the envelope shape.

The `--color` flag defaults to `auto`. Color turns off when stdout is not a
terminal. Color turns off in machine output. The flag honors the `NO_COLOR`
environment variable.

For automation, make the three important choices visible in every command:

```bash
mammoth project list --output json --no-input --profile production
```

## Confirmations

Mutations that change data require confirmation. Pass `--yes` to confirm a
mutation without an interactive prompt. High-impact actions also require
`--confirm TARGET`, where `TARGET` is the exact name of the resource you act on.

Off a terminal, `--no-input` turns on automatically. A mutation without `--yes`
then fails instead of prompting. This keeps scripts safe. See [safety](../safety.md)
for the full confirmation model.

## Structured input

The `--input` flag reads a strict JSON or YAML request document. Pass a file path,
or pass `-` to read from stdin. When you read from stdin, set `--input-format` so
the CLI knows how to parse the document.

```bash
mammoth addon storage add --input request.yaml --input-format yaml --yes
```

## Related pages

See [safety](../safety.md) for confirmations and mutation classes. See
[authentication](../authentication.md) for profiles and credentials, and
[output and errors](output-and-errors.md) for the parsing contract.
