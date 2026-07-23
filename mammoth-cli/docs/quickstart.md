# Five-minute quick start

[Documentation index](llms.txt)

This guide takes you from zero to a safe change in five minutes.

Output defaults to `auto`. A terminal gets a readable table. A pipe or redirect gets JSON. So the human examples below need no output flag.

## Log in

```bash
mammoth auth login -w 4
```

The command prompts for your API key and secret. Both stay hidden as you type.

Agents and CI use a file instead. Run `mammoth auth login --input creds.json`. See [authentication](authentication.md).

## Verify

```bash
mammoth doctor
```

Exit code `0` means your credentials resolve and a request succeeds.

## Pick a project

```bash
mammoth project list
mammoth context project use 180
```

The saved project applies to later commands. You can still pass `--project ID` to override it.

## Read something

```bash
mammoth dataset list --project 180
mammoth folder list --project 180
```

## Make a change safely

```bash
mammoth folder create Reports --project 180
mammoth folder delete 7 --project 180 --yes
```

Destructive commands need `--yes`. High-impact commands also need `--confirm TARGET`. See [safety](safety.md).

## Discover everything

```bash
mammoth capability list
mammoth schema get folder.create
```

See the full [command reference](reference/commands.md).

## Force JSON anywhere

Add `--output json` to any command to get the JSON envelope in a terminal. A pipe or redirect already gives you JSON without the flag.
