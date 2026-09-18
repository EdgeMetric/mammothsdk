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
in `data` or `meta`; retain only nonsecret IDs. An invalid or expired profile
returns the structured auth error (exit 4), which is a stop-and-recover
condition, not permission to retry mutations. The credential rule lives in
[auth](../auth.md); this recipe does not restate it.

Exit 4 is auth/authorization; preserve the structured error and stop safely.
