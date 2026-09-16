# M0 missing export-route scope proposal

Status: **proposed hold; not a closure of the M0 route gap** (2026-09-15).

The SDK introspection inventory contains 21 rows whose `alias_of` target is not
present in the command manifest. They are all typed export conveniences. The
the ledger retains as `unresolved_release_gap`; this proposal deliberately does
not claim that `view export create` is equivalent to any of them.

## Decision requested

Keep the 21 rows release-blocking until each target gets an authored command
contract and an independent wire/state oracle. Do not add generic aliases as a
count-reducing workaround. The SDK helpers differ in destination schema,
credential/secret handling, trigger and wait semantics, and (for internal
dataset export) postcondition identity. A generic export-spec pass-through would
hide those differences from an agent and would not satisfy M0.

The only feasible near-term implementation is a shared typed export family
with one dedicated manifest record per target. Reviewers must first approve the
input schemas and target-specific secret redaction, confirmation, wait and
postcondition policies. Until that work is complete, agents should discover the
existing generic export routes and return an explicit unsupported/unresolved
record for these targets.

## Exact rows

| SDK method | Missing target | Required next contract |
|---|---|---|
| `mammoth.api.exports.ExportsAPI.to_dataset` | `view.export.dataset` | dataset name/target identity, internal-dataset completion and resulting dataset id |
| `mammoth.api.exports.ExportsAPI.to_s3` | `view.export.managed-s3` | object-store target, file format, credentials and wait/result policy |
| `mammoth.client.MammothClient.branch_out` | `view.export.dataset` | dataset branch identity and postcondition verification |
| `mammoth.view.View.branch_out` | `view.export.dataset` | dataset branch identity and postcondition verification |
| `mammoth.view.ViewExport.to_azure_blob` | `view.export.azure-blob` | Azure destination and secret-bearing credential policy |
| `mammoth.view.ViewExport.to_bigquery` | `view.export.bigquery` | profile/target schema, write mode and completion policy |
| `mammoth.view.ViewExport.to_dataset` | `view.export.dataset` | dataset name/target identity, completion and resulting id |
| `mammoth.view.ViewExport.to_elasticsearch` | `view.export.elasticsearch` | endpoint/index/auth policy and completion verification |
| `mammoth.view.ViewExport.to_email` | `view.export.email` | recipients/content policy and external-effect confirmation |
| `mammoth.view.ViewExport.to_ftp` | `view.export.ftp` | endpoint/auth policy and external-effect confirmation |
| `mammoth.view.ViewExport.to_mssql` | `view.export.mssql` | database target/profile and secret handling |
| `mammoth.view.ViewExport.to_mysql` | `view.export.mysql` | database target/profile and secret handling |
| `mammoth.view.ViewExport.to_onedrive` | `view.export.onedrive` | cloud target/profile and secret handling |
| `mammoth.view.ViewExport.to_postgres` | `view.export.postgres` | database target/profile and secret handling |
| `mammoth.view.ViewExport.to_powerbi` | `view.export.powerbi` | profile/report target and external-effect confirmation |
| `mammoth.view.ViewExport.to_redshift` | `view.export.redshift` | database target/profile and secret handling |
| `mammoth.view.ViewExport.to_rest_api` | `view.export.rest` | URL/auth/header/query/body secret policy |
| `mammoth.view.ViewExport.to_s3` | `view.export.managed-s3` | object-store target, file format, credentials and wait/result policy |
| `mammoth.view.ViewExport.to_sftp` | `view.export.sftp` | endpoint/auth policy and external-effect confirmation |
| `mammoth.view.ViewExport.to_sharepoint` | `view.export.sharepoint` | cloud target/profile and secret handling |
| `mammoth.view.ViewExport.to_tableau` | `view.export.tableau` | profile/server target and secret handling |

The repeated targets are intentional: the inventory records distinct public
SDK methods. Reviewers must map each method to one command contract or a
reviewed SDK-only rationale. There are 21 SDK rows but 16 distinct target
names (the `view.export.dataset` and `view.export.managed-s3` targets have
multiple SDK entry points).

## Acceptance evidence required to close this proposal

For every target, provide a manifest/schema entry and handler and SDK argument
oracles. Add negative unknown-field and secret tests, exact parent/view identity,
mutation counts, and async timeout/unknown recovery. Also provide a disposable
live fixture or an evidence-backed backend-blocked record. Then regenerate the
M0 ledger and confirm zero `unresolved_release_gap` rows. Until those artifacts
exist, the 21 rows remain an explicit approval blocker.
