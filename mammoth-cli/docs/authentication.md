# Authentication, profiles, prefixes, and project context

[Documentation index](llms.txt)

## Required and optional inputs

Authentication needs an API key, an API secret, and a workspace id. A one-label
server prefix is optional and defaults to `app-eu`
(`https://app-eu.mammoth.io/api/v2`).

## Precedence

The CLI resolves credentials in this order:

1. Explicit credentials given to the current command (secure prompt or stdin).
2. Environment variables: `MAMMOTH_API_KEY`, `MAMMOTH_API_SECRET`, and
   `MAMMOTH_WORKSPACE_ID` (all three required together), plus optionally
   `MAMMOTH_SERVER_PREFIX`. Supplying only some of the three is rejected
   (`incomplete_environment_auth`) instead of falling back to a profile.
3. The selected profile, or the profile named by `--profile`.

## Profiles

```bash
mammoth auth login --output json --no-input       # store a profile's secret
mammoth auth status --output json --no-input
mammoth config ... --output json --no-input       # inspect non-secret settings
mammoth auth logout --profile default --output json --no-input --yes
```

Secrets are stored in the OS keyring, or in a permission-checked `0600` file
when no keyring is available. A secret is never printed, logged, or included in
any output envelope. Never pass a secret as an ordinary argument.

## Server prefix

The endpoint is chosen by a one-label server prefix: pass `--server-prefix` to
`mammoth auth login`, set it on the profile (`mammoth config set server_prefix
...`), or supply `MAMMOTH_SERVER_PREFIX`. It defaults to `app-eu`
(`https://app-eu.mammoth.io/api/v2`). There is no base-url override — the server
prefix is the only supported endpoint input.

## Project context

A project is operational context, not authentication. It resolves from
`--project`, then the selected profile's saved active project, then none.

```bash
mammoth context project use 180 --output json --no-input
mammoth context project status --output json --no-input
mammoth context project clear --output json --no-input
```

Commands that need a project but have none fail with exit code `2` and error
code `project_required`.
