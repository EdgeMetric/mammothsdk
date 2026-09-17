# SDK API documentation coverage

This page does not claim that the SDK reference is complete. The checked-in
inventory tool reports every public method declared on `MammothClient`,
`ViewsResource`, and API client classes, then records either its owning MkDocs
reference anchor or the explicit `no_docs_anchor` gap.

Run it from the repository root:

```bash
python scripts/sdk_docs_inventory.py --output sdk-docs-inventory.json
```

The report is deterministic and includes its denominator, documented count,
gap count, and an entry for every symbol. On the current source it inventories
432 methods; 250 have an owning reference page and 182 are explicit gaps. The
numbers are observations of this revision, not a support or qualification
claim. CI tests ensure the inventory remains deterministic and that gaps stay
visible when the public surface changes.

The safe setup, URL parsing, view-list, and file-upload examples are also
signature-validated in `tests/unit/test_sdk_docs_inventory.py`. That limited
suite does not exercise remote API calls or prove every rendered code block.
