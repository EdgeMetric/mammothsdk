# SDK API documentation coverage

This page does not claim that the SDK reference is complete. The checked-in
inventory tool reports every public method declared on `MammothClient`,
`ViewsResource`, and API client classes, then records either its owning MkDocs
source page or the explicit `no_owner_page` gap. It does **not** verify that a
specific method is rendered, visible, or linked by an individual HTML anchor.

Run it from the repository root:

```bash
python scripts/sdk_docs_inventory.py --output sdk-docs-inventory.json
```

The report is deterministic and includes its denominator, owner-page mapping
count, owner-page gap count, and an entry for every symbol. On the current
source it inventories 432 methods; 250 map to an owning reference page and
182 have no owning page. Per-method rendered anchors are unassessed for all
432 methods. These numbers are observations of this revision, not a support or
qualification claim. CI tests ensure the inventory remains deterministic and
that gaps stay visible when the public surface changes.

The safe setup, URL parsing, view-list, and file-upload examples are also
signature-validated in `tests/unit/test_sdk_docs_inventory.py`. That limited
suite does not exercise remote API calls or prove every rendered code block.
