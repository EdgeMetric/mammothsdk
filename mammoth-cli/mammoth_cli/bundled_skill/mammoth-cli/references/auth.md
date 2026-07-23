# Authentication and profiles

Required: API key, API secret, workspace id. Optional: a one-label server
prefix (default `app`, resolving to `https://app.mammoth.io/api/v2`).

## Precedence
1. Explicit credentials given to the current command (secure prompt or stdin).
2. Environment: `MAMMOTH_API_KEY`, `MAMMOTH_API_SECRET`, `MAMMOTH_WORKSPACE_ID`
   (all three required together), plus optional `MAMMOTH_SERVER_PREFIX`. Setting
   only some of the three is rejected (`incomplete_environment_auth`) rather than
   falling back to a saved profile.
3. The selected or `--profile` profile's saved credentials.

The only supported configuration is the API key, API secret, workspace id, and
an optional one-label server prefix (default `app`). There is no base-url
override.

## Commands
```bash
mammoth auth login --output json --no-input      # stores secret in the OS keyring
mammoth auth status --output json --no-input
mammoth auth logout --profile default --output json --no-input --yes
```

Secrets live in the OS keyring (or a `0600` file fallback). They are never
printed, logged, or included in any envelope. Never pass a secret as a plain
argument; use the prompt, environment, or `--input`.
