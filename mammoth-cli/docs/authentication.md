# Authentication and project context

[Documentation index](llms.txt)

Every session starts the same way: run `mammoth auth login` once. The CLI keeps
your secret in the OS keyring and reuses it on later commands. There is no
environment-variable shortcut. A stored login is the only way to authenticate.

New here? Install first with the [installation guide](installation.md), then
follow the [quick start](quickstart.md).

## Get an API key

You need three things: an API key, an API secret, and a workspace id.

In the Mammoth web app, open your account settings and create an API key. Mammoth
gives you a key and a matching secret as a pair. Copy both right away. Your
workspace id lives in the same account area.

One more input is optional. The server prefix names your Mammoth region and
defaults to `app`. Most users leave it alone. See
[server prefix and endpoint](#server-prefix-and-endpoint) below.

## Log in interactively

Run the login command:

```bash
mammoth auth login
```

The CLI prompts for three things in order: your API key, your API secret, and
then your workspace id. The two secret prompts stay hidden as you type. On
success the CLI saves the login and confirms.

Two flags fine-tune the login:

- `--server-prefix LABEL` sets the region label (default `app`).
- `--storage auto|keyring|file` chooses where the secret lives.

Leave `--storage` at `auto` and the CLI picks the OS keyring when one exists.

A real terminal always prompts, even when `CI` is set in your shell. Without a
terminal the CLI needs `--input` instead, as shown below.

## Log in without a terminal (agents and CI)

An agent or CI job cannot answer hidden prompts. Feed a credentials file instead:

```bash
mammoth auth login --input creds.json --output json --no-input
```

The file holds one JSON document:

```json
{
  "api_key": "your-key",
  "api_secret": "your-secret",
  "workspace_id": 4,
  "server_prefix": "app"
}
```

The `server_prefix` field is optional. The other three fields are required.

Lock the file down to owner-only before you use it:

```bash
chmod 0600 creds.json
```

The CLI rejects a world-readable file with error code `insecure_input_file`. This
guard keeps a secret off shared disks.

You can also pipe the document straight from stdin:

```bash
cat creds.json | mammoth auth login --input - --input-format json --output json --no-input
```

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

The CLI stores your secret in the OS keyring. When no keyring exists, it falls
back to a permission-checked `0600` file that only you can read.

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

Stuck on any error code above? The [troubleshooting guide](troubleshooting.md)
maps each one to a fix.
