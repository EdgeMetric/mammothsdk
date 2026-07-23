# Authentication and profiles

Required: API key, API secret, workspace id. Optional: a one-label server
prefix (default `app`, resolving to `https://app.mammoth.io/api/v2`).

## Precedence
1. Explicit login handed to the current command (secure prompt or `--input`).
2. The selected or `--profile` profile's saved credentials.

The only supported configuration is the API key, API secret, workspace id, and
an optional one-label server prefix (default `app`). There is no base-url
override.

## Commands
```bash
mammoth auth login -w 4 --output json --no-input          # prompts for key + secret
mammoth auth login --input creds.json --output json --no-input   # non-interactive
mammoth auth status --output json --no-input
mammoth auth logout --profile default --output json --no-input --yes
```

`creds.json` is a `0600` JSON file: `{"api_key": "...", "api_secret": "...",
"workspace_id": 4, "server_prefix": "app"}` (`server_prefix` optional). You can
also pipe it with `--input - --input-format json`.

Secrets live in the OS keyring (or a `0600` file fallback). They are never
printed, logged, or included in any envelope. Never pass a secret as a plain
argument; use the prompt or `--input`.
