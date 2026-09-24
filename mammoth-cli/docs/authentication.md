# Authentication and project context

[Documentation index](llms.txt)

The CLI stores a profile and reuses it on later commands. Before a remote read
or write, inspect the selected profile with `mammoth auth status`. That local
report establishes only that a profile and credentials are present; `mammoth
doctor` validates the endpoint and a live authenticated request. If status
shows no credentials, complete the secure login flow, then require a successful
doctor result before operating. Authentication is deliberately explicit: there
is no environment-variable shortcut and no workspace `-w` login flag.

New here? Install first with the [installation guide](installation.md), then
follow the [quick start](quickstart.md).

## Get an API token

You need two things: an API token and a workspace id.

In the Mammoth web app, open **Workspace settings → API Tokens** and choose
**Create token**. The token starts with `mm_`. The web app shows it only once,
so copy it right away. If you lose it, create a new token. Your workspace id
is the number after `/workspaces/` in the web app's address bar. A token works
only in the workspace and on the server where you created it.

Older tokens came as an API key and a secret. The CLI still accepts that
pair: at the token prompt, paste the key, and the CLI then asks for the
secret.

One more input is optional. The server prefix names your Mammoth region and
defaults to `app`. Most users leave it alone. See
[server prefix and endpoint](#server-prefix-and-endpoint) below.

## Check a profile, then log in if needed

Start with a read-only status check:

```bash
mammoth auth status
```

Compare the status report's endpoint with the intended target before running
`doctor`: use the default `app` endpoint for production, and use `release` only
when release is explicitly intended. If the endpoint is wrong, stop and switch
to a separate correctly configured profile; do not run `doctor` or business
commands against the mismatched profile.

If the selected profile is missing or has no credentials, log in. A successful
status alone does not prove the credentials remain usable; run `doctor` after
login or before work with a saved profile. Do not continue to discovery or a
business command after a failed status, login, or doctor check.

## Log in interactively

Run the login command:

```bash
mammoth auth login
```

The CLI prompts for two things in order: your API token, and then your
workspace id. The token prompt stays hidden as you type. On success the CLI
saves the login and confirms.

Two flags fine-tune the login:

- `--server-prefix LABEL` sets the region label (default `app`).
- `--storage auto|keyring|file` chooses where the secret lives.

Leave `--storage` at `auto` and the CLI picks the OS keyring when one exists.

A real terminal always prompts, even when `CI` is set in your shell. Without a
terminal the CLI needs `--input` instead, as shown below.

## Log in without a terminal (agents and CI)

An agent or CI job cannot answer hidden prompts. On POSIX hosts without an OS
keyring, have the host's protected secret mechanism provision a private input
file outside the repository **before** it writes credentials. The mechanism
must create its owned directory as owner-only (`0700`) and the file as `0600`
from the outset. Do not write a secret to a normally created file and then run
`chmod`: another process may have read it already. The path below is a
placeholder for that host-provisioned file, not a directory that the agent
should create.

Pass only that file's path, and select file storage explicitly:

```bash
mammoth auth login --input /host-provisioned/credentials.json --storage file
```

The file holds one JSON document:

```json
{
  "api_token": "mm_your-token",
  "workspace_id": 4,
  "server_prefix": "app"
}
```

The `server_prefix` field is optional. The other two fields are required. For
an older key and secret, use `"api_key"` and `"api_secret"` in place of
`"api_token"`.

The private file must be owner-only (`0600`) from creation. The CLI rejects a
group- or world-readable POSIX input file with error code
`insecure_input_file`; that check is a backstop, not a safe file-creation
procedure.

On Windows, do not use this POSIX file-storage recipe. Use the Windows OS
keyring.

The CLI reads credentials from exactly two places: the login handed to the
current command, or the selected profile's secure store. It never reads them
from environment variables. An agent that finds no credentials must stop and
ask the operator to run the hidden-prompt `mammoth auth login` in their own
terminal, not ask for the key or secret in chat.

You can also pipe the document straight from stdin:

```bash
cat /host-provisioned/credentials.json | mammoth auth login --input - \
  --input-format json --storage file
```

Remove or securely rotate the input file once your runner has stored the
profile. Do not place the JSON in shell history, a repository, or build logs.

## Credential precedence

The CLI resolves credentials in a short, fixed order:

1. An explicit login handed to the current command.
2. The selected profile, or the profile named by `--profile`.

Nothing else feeds authentication. A profile with no stored credentials cannot
authenticate and fails with error code `not_authenticated`.

Login runs a lightweight connection check before it saves anything. A failed
check leaves your existing state untouched. The command exits `4` with error code
`authentication_failed`.

## Where secrets live

With `--storage auto`, the CLI uses an OS keyring when one is available. In a
non-interactive process with no keyring, it fails with `keyring_unavailable`; it
does not silently select file storage. On a POSIX host, use the protected
`--storage file` flow above when that explicit fallback is authorized.

An OS keyring can stall. On macOS the Keychain may show a dialog asking to allow
access to `mammoth-cli` (choose **Always Allow**), and over SSH it cannot show
one at all. The CLI waits up to 60 seconds, says what it is waiting on, and
then stops waiting. An interactive `auth login --storage auto` then stores the
credential in the owner-only file instead and says so. Any other command fails
with `keyring_unresponsive`; recover with `mammoth auth login --storage file`.
A profile stored in the file is always read from the file, without asking the
keyring.

The CLI never prints, logs, or returns a secret in any output. Never pass a
secret as an ordinary command argument. See [safety](safety.md) for the full
handling rules.

## Server prefix and endpoint

One DNS label picks your endpoint. The default `app` resolves to
`https://app.mammoth.io/api/v2`.

Set the prefix at login time:

```bash
mammoth auth login --server-prefix app
```

Or change it later on the active profile:

```bash
mammoth config set server_prefix app
```

The server prefix is the only endpoint input. There is no base-url override.

## Check and manage login

See your current state at any terminal:

```bash
mammoth auth status
```

The report shows the active profile, whether credentials are present, and the
endpoint in use. Add `--check` to test a live authenticated request:

```bash
mammoth auth status --check
```

Treat the reported endpoint as a preflight value, not a cosmetic detail: it
must match the intended target before `doctor`. Production uses `app`; `release`
requires explicit intent and should use its own profile. On a mismatch, stop,
select or create the separate correct profile, and recheck its status first.

After a successful status or login, run `mammoth doctor`; it reports
configuration and connectivity without displaying secrets. If status, login, or
doctor fails, stop and correct the reported precondition before discovery or
business work. See [troubleshooting](troubleshooting.md) for the exit code and
recovery path.

Remove a single profile when you no longer need it:

```bash
mammoth auth logout --profile default --yes
```

Remove every profile at once:

```bash
mammoth auth logout --all --yes
```

## Project context

A project is operational context, not authentication. Many commands read or
write data inside one project.

The active project resolves in this order:

1. An explicit `--project ID` on the command.
2. The selected profile's saved active project.
3. None.

Manage the saved project with three commands:

```bash
mammoth context project use 180
mammoth context project status
mammoth context project clear
```

A command that needs a project but finds none fails. It exits `2` with error code
`project_required`. Set a project first, then rerun the command.

For unattended work, prefer passing `--profile PROFILE` and `--project
PROJECT_ID` on each operation and record the workspace/project IDs in the
nonsecret [portable handoff](agent-handoff.md). A profile or active project is
not permission to guess a dataset or view: resolve those resources in the exact
parent scope before composing a write.

Stuck on any error code above? The [troubleshooting guide](troubleshooting.md)
maps each one to a fix.
