# Uninstall

[Documentation index](llms.txt)

## Remove the agent skill

```bash
mammoth skill uninstall --output json --no-input                 # all agents, user scope
mammoth skill uninstall --output json --no-input --input '{"agents": ["cursor"]}'
```

Uninstall removes only installer-owned skill copies. A locally modified copy is
reported as `modified` and left in place.

## Remove the CLI

With uv:

```bash
uv tool uninstall mammoth-cli
```

With pipx:

```bash
pipx uninstall mammoth-cli
```

With pip:

```bash
python -m pip uninstall mammoth-cli
```

Remove the agent skill separately with `mammoth skill uninstall` (see above),
because the tool uninstall step removes only the CLI. The installer does not
edit your PATH beyond adding the tool directory; remove that line from your
shell profile if you no longer need it.

## Remove configuration

Non-secret settings live under the platform config directory
(`platformdirs.user_config_dir("mammoth-cli", "Mammoth")`) and any credential
file fallback lives beside them with `0600` permissions. Delete that directory
to remove profiles and settings. Credentials stored in the OS keyring are
removed by `mammoth auth logout --all --yes` or through your keyring tool.

Before deleting configuration, make sure no scheduled CI job relies on the
profile. Prefer `mammoth auth logout --all --yes` first: it removes stored
credentials while leaving the remaining local settings inspectable.
