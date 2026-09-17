# Auth and scope

Use `mammoth auth status`, `mammoth doctor`, `mammoth project list`, and
`mammoth schema get project.list` with `--output json --no-input`. Require
successful `data` and observed workspace/project metadata. Never put secrets in
argv; evaluated agents use the controller broker and never mount profiles.

```bash
mammoth context project use PROJECT_ID --profile PROFILE --output json --no-input
```

Exit 4 is auth/authorization; preserve the structured error and stop safely.
