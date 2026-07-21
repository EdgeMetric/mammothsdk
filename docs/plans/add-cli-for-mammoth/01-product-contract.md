# Product contract and locked decisions

## Users and success criteria

The CLI serves four equal audiences:

- A developer using an interactive terminal.
- An AI agent using deterministic machine output.
- A script or CI job that cannot answer prompts.
- An administrator using guarded high-impact operations.

A user must be able to discover, inspect, create, change, wait for, export,
trash, restore, and delete supported Mammoth resources without writing Python.

## Autonomous agent contract

An LLM agent must complete supported workflows without interactive help. Every
canonical command supports `--output json --no-input`. In this mode it never
prompts, opens a browser, starts a pager, renders progress to stdout, or asks the
agent to choose from an interactive list.

When context is missing or ambiguous, fail before mutation. Return a stable
error code, typed candidate data when safe, and exact executable recovery
commands. Mark whether the next step needs user authorization. Never hide a
required choice in prose.

Expose deterministic discovery commands:

```text
mammoth capability list --output json
mammoth capability get OPERATION_ID --output json
mammoth schema list --output json
mammoth schema get COMMAND_ID --output json
mammoth doctor --output json --no-input
```

Capability results include support state, canonical command ID, SDK symbol,
mutation class, confirmation rule, wait and pagination policies, acceptance
evidence, and known restrictions. Schema results return the exact JSON Schema,
flag/document precedence, examples, exit codes, and version. Generate both from
the reviewed manifests so help, docs, the skill, and runtime discovery cannot
diverge.

Machine success and error envelopes are versioned. They contain no Python repr,
Rich markup, terminal control code, secret, or nondeterministic prose. Sort
object keys in snapshots and give list ordering an explicit API or CLI rule.
NDJSON emits one complete object per line. Diagnostics go only to stderr.

An agent can supply every confirmation noninteractively through reviewed flags.
Commands that require new authority fail with `authorization_required`; they do
not weaken safety or wait indefinitely. Interruptions and timeouts return stable
state, known resource or job IDs, and the exact resume, wait, inspect, or cleanup
command.

## Distribution

- Distribution name: `mammoth-cli`.
- Executable: `mammoth`.
- Module entry point: `python -m mammoth_cli`.
- Initial version: `0.1.0`.
- Location: sibling `mammoth-cli/` package in this repository.
- Build backend: Poetry with `poetry-core`, consistent with the repository.
- Dependency: a declared compatible `mammoth-io` range.
- Minimum Python: 3.12. Python 3.10 and 3.11 are not supported.
- Support every stable Python release from 3.12 through the latest stable
  release available at publication. The current required matrix is 3.12,
  3.13, and 3.14.
- Primary development interpreter: Python 3.14.3.
- Set the current `requires-python` range to `>=3.12,<3.15` for both
  `mammoth-io` and `mammoth-cli`. Test the latest patch of each supported minor
  version and update the upper bound, classifiers, CI, type checks, and
  documentation only after a new stable minor passes.
- Supported systems: Linux, macOS, and Windows.

Do not publish, push, open a PR, create a release, or merge into `main` without
separate authorization.

## Authentication

Authentication has exactly three required inputs:

1. API key.
2. API secret.
3. Workspace ID.

It has one optional input:

4. Server prefix, with default `app-eu`.

Map the default as follows:

```text
app-eu -> https://app-eu.mammoth.io/api/v2
```

Accept a server prefix only when it is one valid DNS label. Reject schemes,
dots, slashes, query strings, fragments, ports, and whitespace.

Support an expert `base-url` configuration for custom deployments. It is not
an authentication input. A profile cannot define both `server-prefix` and
`base-url`.

## Profiles and credentials

Support named profiles. Store non-secret data in the OS-native `platformdirs`
configuration directory. Store secrets in the OS keyring when possible.

If no keyring is available, interactive login can offer a user-only credential
file. Noninteractive login must require an explicit file-storage option. Never
silently write secrets to plaintext.

Support stateless environment use:

```text
MAMMOTH_API_KEY
MAMMOTH_API_SECRET
MAMMOTH_WORKSPACE_ID
MAMMOTH_SERVER_PREFIX
MAMMOTH_BASE_URL
MAMMOTH_PROJECT_ID
MAMMOTH_OUTPUT
MAMMOTH_NO_INPUT
MAMMOTH_TIMEOUT
MAMMOTH_JOB_TIMEOUT
MAMMOTH_PIPELINE_TIMEOUT
```

Resolve authentication values in this order:

1. Explicit secure input to the current command.
2. Environment.
3. Selected profile.
4. The `app-eu` server-prefix default.

Never accept an API secret, password, token, or private key as an ordinary
command-line value. Use a hidden TTY prompt, stdin option, environment variable,
permission-checked file, or OS keyring.

Do not store a live key or secret in this plan, documentation, fixtures, test
snapshots, shell history, Git commits, or CI artifacts. Record only secret
variable names and non-secret target identifiers.

## Project context

A project ID is operational context. It is not authentication.

Resolve it in this order:

1. Global `--project`.
2. A project ID in an explicit Mammoth URL.
3. Saved active project context.
4. Safe and unique resource discovery.
5. Fail before the API call with an exact recovery command.

Create and list operations that cannot infer a project must require explicit or
saved context. Do not scan all projects for these operations.

Use these exact context commands:

```text
mammoth context project status [--profile NAME]
mammoth context project use PROJECT_ID [--profile NAME]
mammoth context project clear [--profile NAME]
```

`use` accepts a positive integer and saves it only in the selected profile's
nonsecret configuration. `clear` is idempotent. All three commands support
`--output json` and `--no-input`; none makes an API request unless `status` is
combined with the global diagnostic workflow.

## API coverage

The official OpenAPI operation inventory is the coverage authority. Extend the
typed SDK before adding a CLI command for an operation the SDK does not expose.

Expose production operations only. Give every OpenAPI operation one reviewed
disposition:

- `command`: a user or administrator can initiate it from the CLI.
- `alias`: another command provides identical behavior.
- `protocol_only`: an inbound webhook, OAuth callback, browser callback,
  telemetry event, health probe, or provider callback that is not a meaningful
  user command.
- `server_unavailable`: documented but unavailable on the production server.
- `deprecated`: explicitly deprecated by the OpenAPI document.

Support and billing operations remain commands when API-key authentication can
authorize them. Put them under clear `support` or `billing` groups and apply
high-impact confirmation. Do not hide them merely because ordinary users lack
permission.

No operation can use an undocumented disposition. A disposition must include
evidence and reviewer identity.

## Safety

- Prompts occur only when stdin is a TTY.
- `--no-input`, JSON mode, NDJSON mode, and CI disable all prompts.
- A normal deletion requires a prompt or `--yes`.
- A high-impact mutation also requires `--confirm TARGET`.
- Billing changes always require `--yes`; removals also require workspace
  confirmation.
- Never retry a mutation without a real server idempotency contract.
- Use real draft or preview endpoints. Never simulate a successful dry run.
- Downloads use a partial file and atomic rename.
- Existing files require `--overwrite`.
- Interruptions return exit status 130 and close sessions and files.

## Documentation language

Use a Mammoth Simplified Technical English house profile based on ASD-STE100
Issue 9 for documentation, help, prompts, warnings, errors, installers, and the
agent skill. Do not claim certification or redistribute the official standard.

House rules:

- Use one instruction in each procedural sentence.
- Use the imperative form for actions.
- Prefer active voice.
- Keep procedural sentences at 20 words or fewer.
- Keep descriptive sentences at 25 words or fewer.
- Keep paragraphs at six sentences or fewer.
- Use one approved term for each concept.
- Exclude code, flags, API fields, JSON keys, URLs, and quotations from lexical
  replacement rules.
