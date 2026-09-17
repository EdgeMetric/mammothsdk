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
removals and operation-ID changes for human semantic review before changing a
canonical row.

Each canonical row records `method`, `path`, `operation_id`, the CLI command
and `schema_id` when reviewed (otherwise `null`), the SDK symbol when reviewed
(otherwise `null`), separate `mapping_state` and `mapping_gap_reason`, support
`status`, `evidence`, `evidence_version`, and `remarks`. Mapping is structural
information, not a live-support claim.

The historical M0 pinned snapshot is 445 operations across 287 paths. The
release matrix is a separate 528-operation/355-path inventory; never use the
M0 denominator to reconcile release status counts.
