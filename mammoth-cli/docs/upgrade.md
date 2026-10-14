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

A pin is remembered: `--version X.Y.Z` (here or in the installer) records it in
`pin.json` next to `update-check.json`, and the automatic upgrade below then
installs nothing. `mammoth upgrade --yes` always moves to the newest release,
also from an install that was pinned with `--version`, and clears the pin. It finds the uv that the one-line
installer keeps off PATH, so it works on a fresh macOS or Linux host with no
uv of its own. Running the one-line installer again has the same effect
(with `--version` it re-pins).

`--check` is read-only. The upgrade itself is a mutation with an external
effect, so at a terminal it prompts for confirmation and in non-interactive
(`--no-input` / machine-output) mode it requires `--yes`.

After an upgrade, verify both the executable and connectivity:

```bash
mammoth --version
mammoth doctor
```

## Update notice

At most once a day the CLI asks PyPI for the latest release, *after* a command
has written its output (3-second timeout, silent on failure), and caches the
answer next to the run log (`update-check.json` in the platform state
directory).

- `mammoth doctor` shows `cli_version` with the installed and latest versions.
- When a newer release exists and the CLI will not install it by itself
  (auto-update off, the install is pinned, or the install failed), every JSON envelope carries
  `meta.update_available` = `{"current": "...", "latest": "...", "command":
  "mammoth upgrade --yes"}` (otherwise `null`) and human output prints one line
  on stderr.

The check never delays or blocks a command. `MAMMOTH_NO_UPDATE_CHECK=1` turns
it off; `MAMMOTH_UPDATE_CACHE=/path` moves the cache file.

## Automatic upgrade (on by default)

When the cached answer is older than a day, the command that finishes starts a
detached process that asks PyPI and, if a newer release exists, installs it
through the same manager detection as `mammoth upgrade`. There is no prompt.

- It runs **after** the command, not before. Replacing the installed files under
  a running command breaks its lazy imports, and a failed install must not touch
  the command that started it. The command completes on the version it started
  with; the next one runs the new version.
- It never blocks or fails a command and prints nothing. The attempt and any
  failure are written to the run log (`auto_upgrade` records); after a failed
  install `meta.update_available` returns so you can run `mammoth upgrade --yes`.
- It never runs during `mammoth upgrade` or `mammoth doctor`, inside an embedded
  agent session, or with `MAMMOTH_NO_UPDATE_CHECK=1`.
- A pinned install (`mammoth upgrade --version X.Y.Z`, or the installer's
  `--version`) is never updated by itself: the check and the
  `meta.update_available` hint stay, nothing is installed. `mammoth upgrade --yes`
  moves to the latest and clears the pin.
- Opt out with `MAMMOTH_NO_AUTO_UPDATE=1` (or `MAMMOTH_AUTO_UPGRADE=0`). The check
  and the `meta.update_available` hint stay; nothing is installed. Do this in CI
  images, lock-file environments and shared virtualenvs whose version must not
  change underneath a task.

`mammoth upgrade --yes` reports `installed_version`, the version a fresh
interpreter prints after the upgrade.

## Upgrade the agent skill

```bash
mammoth skill update
```

Update replaces only installer-owned copies. A locally modified skill directory
is refused unless you pass a force option, which first moves it to a
timestamped backup. Without an `agents` input, update touches only the copies
that are already installed. It never adds a new one.

You rarely need to run it by hand. The first command after a CLI upgrade
refreshes every installer-owned copy that you have not changed.
`mammoth doctor` reports a copy that is older than the CLI in its `skill` check.
`MAMMOTH_NO_UPDATE_CHECK=1` turns the automatic refresh off.

## Version policy

The CLI uses SemVer and is released under `cli-vX.Y.Z` tags, independent of the
SDK version. A new Python minor is supported only after dependencies resolve and
all checks pass; classifiers, CI, and docs update together.
