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

With pip:

```bash
python -m pip uninstall mammoth-cli
```

The released installer also supports
`mammoth self uninstall [--keep-skills] [--keep-config] --yes`, which removes
only files whose current digest matches the ownership record, reports modified
files, never removes a user-provided uv, and removes a PATH entry only when the
ownership record proves the installer added it.

## Remove configuration

Non-secret settings live under the platform config directory
(`platformdirs.user_config_dir("mammoth-cli", "Mammoth")`) and any credential
file fallback lives beside them with `0600` permissions. Delete that directory
to remove profiles and settings. Credentials stored in the OS keyring are
removed by `mammoth auth logout --all --yes` or through your keyring tool.
