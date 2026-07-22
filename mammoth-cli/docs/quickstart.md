# Five-minute quick start

[Documentation index](llms.txt)

## 1. Provide credentials

```bash
export MAMMOTH_API_KEY=...
export MAMMOTH_API_SECRET=...
export MAMMOTH_WORKSPACE_ID=4
```

Or run `mammoth auth login` to store them in the OS keyring. See
[authentication](authentication.md).

## 2. Verify the environment

```bash
mammoth doctor --output json --no-input
```

Exit code `0` means credentials resolve and an authenticated request succeeds.

## 3. Pick a project

```bash
mammoth project list --output json --no-input
mammoth context project use 180 --output json --no-input
```

## 4. Read something

```bash
mammoth dataset list --project 180 --output json --no-input
mammoth folder list --project 180 --output json --no-input
```

## 5. Make a change, safely

```bash
mammoth folder create Reports --project 180 --output json --no-input
mammoth folder delete 7 --project 180 --output json --no-input --yes
```

Destructive commands need `--yes`; high-impact commands also need
`--confirm TARGET`. See [safety](safety.md).

## Discover everything

```bash
mammoth capability list --output json --no-input
mammoth schema get folder.create --output json --no-input
```

See the full [command reference](reference/commands.md).
