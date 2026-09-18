# Authentication and profiles

Required: API key, API secret, workspace id. Optional: a one-label server
prefix (default `app`, resolving to `https://app.mammoth.io/api/v2`).

## Precedence
1. Explicit login handed to the current command (secure prompt or `--input`).
2. The selected or `--profile` profile's saved credentials.

The only supported configuration is the API key, API secret, workspace id, and
an optional one-label server prefix (default `app`). There is no base-url
override.

## Cold-start sequence

For an ordinary operator, before any remote command, inspect authentication and
then verify the connection. These checks are mandatory even when a profile may
already exist:

```bash
mammoth auth status --profile PROFILE --output json --no-input
```

If status reports a missing profile or `has_credentials=false`, run the secure
login flow, then check status again:

```bash
mammoth auth login --profile PROFILE --server-prefix app
mammoth auth status --profile PROFILE --output json --no-input
```

`auth status` is a local profile/credential-presence check; it does not prove
that credentials are valid remotely. After the profile is present, verify the
live connection:

```bash
mammoth doctor --profile PROFILE --output json --no-input
```

Do not continue to schema discovery or business operations after an
authentication or doctor failure. The `app` server prefix is the default;
release or other environment credentials do not imply authorization for `app`.

For an evaluated or isolated agent, do not run these profile commands: use the
controller-provided credential broker/sidecar check instead. Never mount or
read a saved profile. If no broker is provided, stop before authenticated
actions.

## Commands
```bash
mammoth auth login --profile PROFILE --server-prefix app  # hidden prompts
mammoth auth login --profile PROFILE --input creds.json --storage file --output json --no-input
mammoth auth status --profile PROFILE --output json --no-input
mammoth auth logout --profile default --output json --no-input --yes
```

`PROFILE` means the actual nonsecret profile name selected by the operator or
reported by `auth status` (for example, `default` or `work`). Substitute that
name; never type the literal placeholder or invent a profile to evade an
authorization failure. When using the selected profile, `--profile PROFILE`
may be omitted.

For an ordinary human-operated terminal, prefer the first command: it asks
for the key and secret without putting either in shell history, argv, chat, or
logs. For headless POSIX work, create the JSON file outside the repository, set
its permissions to `0600`, and pass only its path. With a protected POSIX file,
specify `--storage file` explicitly; `--storage auto` can require an available
OS keyring and is not a reliable headless fallback. On Windows, do not use the
file backend as a secret store; use the OS keyring, a controller broker, or
stop and obtain a supported secure store. Remove any input file after the
profile is stored.

`creds.json` is a `0600` JSON file: `{"api_key": "...", "api_secret": "...",
"workspace_id": 4, "server_prefix": "app"}` (`server_prefix` optional). You can
also pipe it with `--input - --input-format json`.

Secrets live in the OS keyring (or an explicitly selected `0600` file
fallback). They are never printed, logged, or included in any envelope. Never
pass a secret as a plain argument; use the hidden prompt or `--input`.

For evaluated or isolated agents, authentication remains controller-owned: use
the provided credential broker/sidecar instead of `auth login` and never mount
or read a saved profile. If no broker is provided, stop before authenticated
actions and report the precondition failure.
