# Capability-matrix drift workflow

The committed `release-capability-matrix.json` is the canonical repository
inventory. The historical workbook supplies past evidence context only; do not
copy its changing counts over the committed matrix.

After obtaining a candidate OpenAPI JSON, generate a local, deterministic
review queue:

```bash
cd mammoth-cli
python scripts/report_release_capability_drift.py \
  --openapi /path/to/candidate-openapi.json \
  --report-out /tmp/release-capability-drift.json \
  --scaffold-out /tmp/release-capability-additions.json
```

Identity is exact uppercase HTTP method plus path. An unchanged identity keeps
its existing capability ID, support status, evidence, mappings, and remarks.
The report only scaffolds additions as `Unassessed`; it does not implement a
route, infer a CLI mapping, or promote support. It queues additions for an
agent to discover, implement, test, and submit for review. It also flags
removals, operation-ID changes, and normalized per-operation semantic changes
(parameters, request bodies, and responses) for human review before changing a
canonical row. By default it uses the committed
`spec/openapi/release-20260916.json`, the 528-operation release baseline that
matches this matrix. Supply `--baseline-openapi` only when the matrix has been
reviewed against a different release revision. Without a matching baseline,
method/path additions and removals can be compared, but semantic change
detection is incomplete; use `sync_openapi.py --check-live` as the broader
snapshot-level complement.

Each canonical row records `method`, `path`, `operation_id`, the CLI command
and `schema_id` when reviewed (otherwise `null`), the SDK symbol when reviewed
(otherwise `null`), separate `mapping_state` and `mapping_gap_reason`, support
`status`, `evidence`, `evidence_version`, and `remarks`. Mapping is structural
information, not a live-support claim.

The historical M0 pinned snapshot is 445 operations across 287 paths. The
release matrix is a separate 528-operation/355-path inventory; never use the
M0 denominator to reconcile release status counts.

## Maintained matrix (derived mapping)

The mapping fields of every row are derived, not hand-edited. Refresh them
after any change to the server spec, the command manifests or the SDK:

```bash
cd mammoth-cli
# 1. Pin a new server spec (offline, from a checkout of server master):
python scripts/sync_openapi.py --from-file master.json --name master-YYYYMMDD \
  --source-ref origin/master --source-sha <git sha> --method "<how it was generated>"
# 2. Re-derive the matrix JSON and Markdown:
python scripts/generate_release_capability_matrix.py
# 3. CI runs the same script with --check; it fails when the files are stale.
python scripts/generate_release_capability_matrix.py --check
```

What the generator does:

* Every operation in the newest `spec/openapi/master-<YYYYMMDD>.json` gets a row.
  A new operation is scaffolded as `Unassessed` with a `NEW-` id.
* `scripts/_route_scan.py` reads which SDK function calls which route. The
  manifests say which command wraps which SDK function. Together they set
  `canonical_command`, `sdk_symbol`, `bound_commands` and `mapping_state`:
  `cli_and_sdk_mapped`, `cli_mapped`, `sdk_only`, `alias`, `protocol_only`,
  `internal_only`, `unmapped` or `removed_on_server`.
* `protocol_only` and `internal_only` come from the reviewed tables in
  `scripts/_command_map.py`. Add an operation there, with a reason, when no CLI
  user should drive it.
* `unrouted_sdk_calls` lists SDK calls to a route the server does not serve:
  `removed_on_server`, or `pending_server_release` when
  `PENDING_SERVER_RELEASE` names the unmerged server branch.
* `commands_without_route` lists commands that reach no route through a row
  (local or wrapper commands).
* `status`, `remarks`, `evidence` and `evidence_version` are never changed.
