# Retained Core read batch B — 2026-09-17

Read-only evidence for observed view 46 under its exact parent dataset 29 in
workspace 4 / project 3. No fixture was created or modified. Before every call,
the matching local schema was inspected: `view.active-user.list`,
`view.conditional-format.list`, `view.derivative.list`,
`view.exportable-config.get`, `view.parameter-context`,
`view.checkpoint.list`, `view.data-check.list`, and `view.version.list`.
Those schemas require or accept the explicit parent dataset ID; every capture
uses positional `46 29`.

Execution used the public PyPI `mammoth-cli` 1.1.11 wheel, SHA-256
`25a811dad8d843731d719f20948ffe7df85dfb16a89f4cea1d8999925b54c962`,
in a fresh isolated Python 3.12 environment. Its installed SDK dependency was
`mammoth-io` 0.7.1. Each JSON file stores a UTC timestamp, sanitized argv,
package version, exit code, original structured response hashes, and a
structural-only response summary—never credentials or raw data.

All eight reads exited 0. Active users, conditional formats, derivatives,
checkpoints, and data checks were empty in this retained view. Exportable
config returned structural configuration including five tasks; parameter
context returned empty bound parameters/snippets; and version list returned
eleven items on its documented single-page boundary. These observations are
bounded to one retained view and do not support Full claims.

