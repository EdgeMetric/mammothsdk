# Batch E dashboard read-only evidence — published 1.1.11

Read-only calls used published `mammoth-cli==1.1.11` / `mammoth-io==0.7.1`,
Python 3.14.4, profile `expanded-live`, workspace 4/project 3, and retained
dashboard48/view46. Dashboard metadata exposed the exact URL slug
`n0ReokM66zUyyEYI3g2mRA`, which was used for the URL lookup; no URL was
fabricated. No resources were created or mutated.

Bounded Partial proposals:

- REL-082 `dashboard.get-by-url`: exact observed slug resolved dashboard48.
- REL-110 chat history: successful empty history (`sequence=1`).
- REL-121 RLS assignments: successful disabled/empty assignment state.
- REL-122 RLS columns: successful 9 display columns.
- REL-123 RLS values: exact observed display column `Entity` returned 205 values.
- REL-126 video state: successful `{status: none, stale: false}`.

All are single retained-resource reads and do not establish Full support.

The exact rerun transcript, including UTC capture timestamps, sanitized argv,
exit codes, output hashes, and structural summaries, is in
[`RESULTS-TRANSCRIPT.json`](RESULTS-TRANSCRIPT.json). The earlier
`RESULTS.json` remains historical evidence.
