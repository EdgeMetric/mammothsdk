# Auth and scope

Use `mammoth auth status`, `mammoth doctor`, `mammoth project list`, and
`mammoth schema get project.list` with `--output json --no-input`. Require
successful `data` and observed workspace/project metadata. Never put secrets in
argv. If credentials are missing, the operator logs in from their own terminal;
see [auth](../auth.md).

```bash
mammoth context project use PROJECT_ID --profile PROFILE --output json --no-input
```

The successful envelope should identify the selected profile/workspace/project
in `data` or `meta`; retain only nonsecret IDs. A deliberately invalid or
expired profile should return the structured auth error (exit 4), which is a
stop-and-recover condition, not permission to retry mutations. Never inline
tokens or secrets in argv, logs, or evidence. Headless login may receive
protected credential JSON through stdin or a 0600 input file only when the
operator explicitly supplies that file.

Exit 4 is auth/authorization; preserve the structured error and stop safely.
