# Upgrade

[Documentation index](llms.txt)

## Upgrade the CLI

The simplest path is the built-in command, which detects how the CLI was
installed (uv tool, pipx, or pip) and upgrades it in place. It never needs
administrator rights.

```bash
mammoth upgrade --check --output json --no-input   # report installed vs latest; changes nothing
mammoth upgrade --yes --output json --no-input      # upgrade to the latest release
mammoth upgrade --version X.Y.Z --yes               # pin an exact version
```

`--check` is read-only. The upgrade itself is a mutation with an external
effect, so at a terminal it prompts for confirmation and in non-interactive
(`--no-input` / machine-output) mode it requires `--yes`.

Under the hood this runs the same command you can also run by hand:

With uv:

```bash
uv tool upgrade mammoth-cli
mammoth --version
```

With pip:

```bash
python -m pip install --upgrade mammoth-cli
```

To move to an exact version, pass it to the tool:

```bash
uv tool install mammoth-cli==X.Y.Z         # or: pipx install --force mammoth-cli==X.Y.Z
mammoth --version
```

You can also re-run the convenience installer with `--version X.Y.Z`. After any
upgrade, run `mammoth doctor` to confirm the new version works.

## Upgrade the agent skill

```bash
mammoth skill update --output json --no-input
```

Update replaces only installer-owned copies. A locally modified skill directory
is refused unless you pass a force option, which first moves it to a
timestamped backup.

## Version policy

The CLI uses SemVer and is released under `cli-vX.Y.Z` tags, independent of the
SDK version. A new Python minor is supported only after dependencies resolve and
all checks pass; classifiers, CI, and docs update together.
