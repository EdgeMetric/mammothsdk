# Auth and scope

Use `mammoth auth status`, `mammoth doctor`, `mammoth project list`, and
`mammoth schema get project.list` with `--output json --no-input`. Require
successful `data` and observed workspace/project metadata. Never put secrets in
argv; evaluated agents use the controller broker and never mount profiles.

```bash
mammoth context project use PROJECT_ID --profile PROFILE --output json --no-input
```

The successful envelope should identify the selected profile/workspace/project
in `data` or `meta`; retain only nonsecret IDs. A deliberately invalid or
expired profile should return the structured auth error (exit 4), which is a
stop-and-recover condition, not permission to retry mutations. Never place
tokens or secrets in a command, JSON input, or evidence file.

Exit 4 is auth/authorization; preserve the structured error and stop safely.
