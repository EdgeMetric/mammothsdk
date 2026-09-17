# Public CLI 1.1.12 folder receipts

Each file is the exact captured stream from one command. `*.stdout` and `*.stderr` are kept separate; exit codes are recorded below. No credentials or secrets are included.

- CLI wheel SHA-256: `135b3384742d66ca4168b5afc2762a9c2502263228d6ee1a45f38560abf81a2e`
- SDK: `mammoth-io==0.7.1`
- Read-only batch summaries: [`stdout`](read-only-batch-20260917.stdout.json) and [`stderr`](read-only-batch-20260917.stderr.json)
- Scope: workspace 4/project 3, disposable folder ID 5; project 180 used only for wrong-scope read.
- Version: `version.stdout`; successful CRUD/list cases have empty stderr; authorization/error cases have empty stdout and JSON stderr.
- Status: `version=0`, `create=0`, `get=0`, `get-fields=0`, `list-filter=0`, `missing=4`, `wrong-scope=4`, `update=0`, `get-updated=0`, `delete=0`, `final-list=0`.

The additional read-only batch resolved workspace 4/project 3 and observed
project 3, datasets 33/31/30/29/28, views 46/39 under dataset 29, and empty
folder results at offset 0 with a continuation link. Dataset 29 details and
file-settings reads, plus exact-parent view 46 details, succeeded. Wrong-parent
view 46/dataset 28 and missing view 999999/dataset 29 returned exit 4 with
empty stdout and structured authorization errors on stderr. This read-only
batch does not change any row to Full: it lacks lifecycle and variant coverage.
