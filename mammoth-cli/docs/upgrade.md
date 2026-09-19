# Upgrade

[Documentation index](llms.txt)

## Upgrade the CLI

The built-in command detects the `uv tool`, `pipx`, or `pip` installation
method, then uses the matching upgrade path. Check first when a
reproducible environment matters.

```bash
mammoth upgrade --check   # report installed vs latest; changes nothing
mammoth upgrade --yes      # upgrade to the latest release
mammoth upgrade --version X.Y.Z --yes               # pin an exact version
```

`--check` is read-only. The upgrade itself is a mutation with an external
effect, so at a terminal it prompts for confirmation and in non-interactive
(`--no-input` / machine-output) mode it requires `--yes`.

After an upgrade, verify both the executable and connectivity:

```bash
mammoth --version
mammoth doctor
```

## Update notice

Once a day the CLI asks PyPI for the latest release, *after* a command has
written its output (3-second timeout, silent on failure) and caches the answer
next to the run log (`update-check.json` in the platform state directory).
From the next command on, while a newer release exists:

- every JSON envelope carries `meta.update_available` =
  `{"current": "...", "latest": "...", "command": "mammoth upgrade --yes"}`
  (otherwise `null`);
- human output modes print one line on stderr;
- `mammoth doctor` shows `cli_version` with the installed and latest versions.

The check never delays or blocks a command. `MAMMOTH_NO_UPDATE_CHECK=1` turns
it off; `MAMMOTH_UPDATE_CACHE=/path` moves the cache file.

## Automatic upgrade (opt-in)

`MAMMOTH_AUTO_UPGRADE=1` makes the CLI run the upgrade itself, through the
detected manager, at the start of the first command that sees a newer cached
release; the command that triggered it still completes on the version that
started it, the run log records the attempt (`auto_upgrade`), and the same
release is not installed twice. It is off by default on purpose: a pinned
environment (lock file, CI image, shared virtualenv) must never change
underneath a task. Agents should prefer the explicit path: read
`meta.update_available` and run its `command` before starting a task.

## Upgrade the agent skill

```bash
mammoth skill update
```

Update replaces only installer-owned copies. A locally modified skill directory
is refused unless you pass a force option, which first moves it to a
timestamped backup.

## Version policy

The CLI uses SemVer and is released under `cli-vX.Y.Z` tags, independent of the
SDK version. A new Python minor is supported only after dependencies resolve and
all checks pass; classifiers, CI, and docs update together.
