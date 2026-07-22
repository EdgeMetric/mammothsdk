# Authentication and profiles

Required: API key, API secret, workspace id. Optional: a one-label server
prefix (default `app-eu`, resolving to `https://app-eu.mammoth.io/api/v2`).

## Precedence
1. Explicit credentials given to the current command (secure prompt or stdin).
2. Environment: `MAMMOTH_API_KEY`, `MAMMOTH_API_SECRET`, `MAMMOTH_WORKSPACE_ID`,
   optional `MAMMOTH_SERVER_PREFIX` / `MAMMOTH_BASE_URL`.
3. The selected or `--profile` profile's saved credentials.

## Commands
```bash
mammoth auth login --output json --no-input      # stores secret in the OS keyring
mammoth auth status --output json --no-input
mammoth auth logout --profile default --output json --no-input --yes
```

Secrets live in the OS keyring (or a `0600` file fallback). They are never
printed, logged, or included in any envelope. Never pass a secret as a plain
argument; use the prompt, environment, or `--input`.
