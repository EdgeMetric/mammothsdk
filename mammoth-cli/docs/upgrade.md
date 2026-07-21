# Upgrade

[Documentation index](llms.txt)

## Upgrade the CLI

With uv:

```bash
uv tool upgrade mammoth-cli
mammoth --version
```

With pip:

```bash
python -m pip install --upgrade mammoth-cli
```

The released installer also supports `mammoth self update [--version X.Y.Z]`,
which installs to a staging location, verifies `mammoth --version` and
`mammoth doctor`, updates the skill atomically, and records the new state. If
validation fails, it restores the previous CLI version and skill directories.

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
