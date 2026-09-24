# Authentication and profiles

Required: an API token (`mm_...`) and a workspace id. Optional: a one-label
server prefix (default `app`, resolving to `https://app.mammoth.io/api/v2`).
Login accepts nothing else. If `auth status` reports `credential: key_secret`
(a profile saved by an older CLI), it still works, but ask the operator to run
`mammoth auth login` again with a token.

A token may be limited to one project. It then gets HTTP 403
`authorization_required` in every other project, including a project it has
created. When that happens, stop creating projects: ask the operator which
project the token belongs to and pass `--project ID`, or ask for a token
created without a project.

## Precedence
1. Explicit login handed to the current command (secure prompt or `--input`).
2. The selected or `--profile` profile's saved credentials.

There is no third source. The CLI and SDK do not read credentials from
environment variables, and an agent must not search the environment, shell
history, or unrelated files for them.

## How an agent obtains credentials

An agent never receives the token. When `auth status` reports a
missing profile or `has_credentials=false`, stop and hand the login to the
human operator:

1. Tell the operator where the credentials come from: in the Mammoth web app,
   **Workspace settings → API Tokens → Create token** gives a token that
   starts with `mm_`; the web app shows it only once (if it is lost, create a
   new one). The workspace id is the number after `/workspaces/`
   in the web app's address bar. Then give the exact command to run in
   **their own** terminal. For production it is:

   ```bash
   mammoth auth login
   ```

   Add `--server-prefix release` only when the task names the release
   environment, and `--profile NAME` only when the operator wants a profile
   other than `default`. The command prompts for the token with hidden
   input, then the workspace id, so no secret enters chat, argv, or history.
   Tokens are per environment and per workspace: a release token never
   authenticates on `app`.
   On macOS the Keychain may show a dialog about `mammoth-cli`; tell the
   operator to choose **Always Allow**. If the keychain cannot be used (for
   example over SSH), login falls back to the owner-only file, or the operator
   runs `mammoth auth login --storage file`.
2. Wait for the operator to confirm, then re-run
   `mammoth auth status --profile PROFILE` and
   `mammoth doctor --profile PROFILE`.
3. Do not ask the operator to paste the token into chat. Do not run
   `auth login` yourself, with or without `--input`, unless the operator has
   explicitly given you a protected `0600` credential file path to use.

The only supported configuration is the API token, the workspace id, and an optional one-label server prefix (default `app`). There is no base-url
override.

## Cold-start sequence

For an ordinary operator, identify the intended environment before any remote
command. Production means the `app` endpoint by default; use `release` only
when the task explicitly requests the release environment. Inspect
authentication and then verify the connection. These checks are mandatory even
when a profile may already exist:

```bash
mammoth auth status --profile PROFILE
```

If status reports a missing profile or `has_credentials=false`, run the secure
login flow, then check status again:

```bash
mammoth auth login                       # production; add --profile NAME if not 'default'
mammoth auth status
```

`auth status` is a local profile/credential-presence check; it does not prove
that credentials are valid remotely. Compare its reported `endpoint` with the
intended environment before proceeding. A profile for another endpoint is a
scope mismatch: stop and select or authenticate the explicitly intended
profile; do not silently reuse, rewrite, or promote it. After the profile is
present and its endpoint matches, verify the live connection:

```bash
mammoth doctor --profile PROFILE
```

`doctor` also lists the projects the credential can see (`projects` check)
and verifies that `--project` or the selected project is one of them
(`project_context` check). Pick the project id from that list; the API does
not expose write permission, so the first write is what proves it.

Do not continue to schema discovery or business operations after an
authentication or doctor failure. The `app` server prefix is the production
default; release or other environment credentials do not imply authorization
for `app`, and a release profile is not appropriate unless the task explicitly
targets release.

## Commands
```bash
mammoth auth login                                        # hidden prompts; production
mammoth auth login --server-prefix release                # release environment
mammoth auth login --profile PROFILE --input creds.json --storage file
mammoth auth status --profile PROFILE
mammoth auth logout --profile default --yes
```

`PROFILE` means the actual nonsecret profile name selected by the operator or
reported by `auth status` (for example, `default` or `work`). Substitute that
name; never type the literal placeholder or invent a profile to evade an
authorization failure. When using the selected profile, `--profile PROFILE`
may be omitted.

For an ordinary human-operated terminal, prefer the first command: it asks
for the token without putting it in shell history, argv, chat, or logs. For headless POSIX work, create the JSON file outside the repository, set
its permissions to `0600`, and pass only its path. With a protected POSIX file,
specify `--storage file` explicitly; `--storage auto` can require an available
OS keyring and is not a reliable headless fallback. On Windows, do not use the
file backend as a secret store; use the OS keyring or stop and obtain a
supported secure store. Remove any input file after the
profile is stored.

`creds.json` is a `0600` JSON file: `{"api_token": "mm_...", "workspace_id": 4,
"server_prefix": "app"}` (`server_prefix` optional). You can
also pipe it with `--input - --input-format json`.

Secrets live in the OS keyring (or an explicitly selected `0600` file
fallback). They are never printed, logged, or included in any envelope. Never
pass a secret as a plain argument; use the hidden prompt or `--input`.
