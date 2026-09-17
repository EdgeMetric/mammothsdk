# Public CLI 1.1.12 folder receipts

Each file is the exact captured stream from one command. `*.stdout` and `*.stderr` are kept separate; exit codes are recorded below. No credentials or secrets are included.

- CLI wheel SHA-256: `135b3384742d66ca4168b5afc2762a9c2502263228d6ee1a45f38560abf81a2e`
- SDK: `mammoth-io==0.7.1`
- Scope: workspace 4/project 3, disposable folder ID 5; project 180 used only for wrong-scope read.
- Version: `version.stdout`; successful CRUD/list cases have empty stderr; authorization/error cases have empty stdout and JSON stderr.
- Status: `version=0`, `create=0`, `get=0`, `get-fields=0`, `list-filter=0`, `missing=4`, `wrong-scope=4`, `update=0`, `get-updated=0`, `delete=0`, `final-list=0`.
