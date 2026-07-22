#!/usr/bin/env python3
"""Fetch and pin the production Mammoth OpenAPI snapshot.

This is an explicit maintenance operation. It reaches the network. Ordinary CI
must not run it; CI validates the committed snapshot only.

The live OpenAPI generator is nondeterministic. Repeated fetches keep the path
and operation counts stable but change examples, some defaults, parameter order,
and some descriptions. This script does two things:

1. Save the exact raw response and its SHA-256 to ``spec/openapi/openapi.json``
   and ``spec/openapi/metadata.json``. The raw snapshot is the pinned contract.
2. Write a normalized *contract projection* to ``spec/openapi/projection.json``.
   The projection removes ``example``/``examples``, sorts parameter arrays by
   location then name, and sorts object keys. A primary reviewer compares the
   projection across fetches to classify semantic differences before replacing
   the pinned snapshot.

Usage::

    python scripts/sync_openapi.py            # fetch, write snapshot + projection
    python scripts/sync_openapi.py --check    # re-project committed snapshot only
    python scripts/sync_openapi.py --check-live  # opt-in operation inventory drift check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SOURCE_URL = "https://app.mammoth.io/api/v2/docs/openapi.json"
SPEC_DIR = Path(__file__).resolve().parent.parent / "spec" / "openapi"
SNAPSHOT_PATH = SPEC_DIR / "openapi.json"
METADATA_PATH = SPEC_DIR / "metadata.json"
PROJECTION_PATH = SPEC_DIR / "projection.json"

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def count_operations(document: dict[str, Any]) -> int:
    return sum(
        1
        for path_item in document.get("paths", {}).values()
        for method in path_item
        if method.lower() in HTTP_METHODS
    )


def operation_inventory(document: dict[str, Any]) -> set[str]:
    """Return the stable method-and-path operation inventory."""
    return {
        f"{method.upper()} {path}"
        for path, path_item in document.get("paths", {}).items()
        for method in path_item
        if method.lower() in HTTP_METHODS
    }


def fetch_document() -> tuple[bytes, dict[str, Any]]:
    """Fetch and decode the production document from the fixed source URL."""
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "mammoth-cli-sync/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 (fixed https host)
        raw = response.read()
    return raw, json.loads(raw)


def _strip_examples(node: Any) -> Any:
    """Recursively drop ``example``/``examples`` and sort object keys."""
    if isinstance(node, dict):
        result: dict[str, Any] = {}
        for key in sorted(node):
            if key in {"example", "examples"}:
                continue
            result[key] = _strip_examples(node[key])
        return result
    if isinstance(node, list):
        return [_strip_examples(item) for item in node]
    return node


def project_contract(document: dict[str, Any]) -> dict[str, Any]:
    """Build a review projection with stable ordering and no examples."""
    projected = _strip_examples(document)
    paths = projected.get("paths", {})
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            params = operation.get("parameters")
            if isinstance(params, list):
                operation["parameters"] = sorted(
                    params,
                    key=lambda p: (
                        str(p.get("in", "")) if isinstance(p, dict) else "",
                        str(p.get("name", "")) if isinstance(p, dict) else "",
                    ),
                )
    return projected


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch() -> None:
    raw, document = fetch_document()
    digest = hashlib.sha256(raw).hexdigest()

    SPEC_DIR.mkdir(parents=True, exist_ok=True)
    # Preserve the exact bytes as the pinned contract.
    SNAPSHOT_PATH.write_bytes(raw)

    metadata = {
        "source_url": SOURCE_URL,
        "fetched_at": datetime.now(UTC).isoformat(),
        "sha256": digest,
        "openapi_version": document.get("openapi"),
        "api_version": document.get("info", {}).get("version"),
        "path_count": len(document.get("paths", {})),
        "operation_count": count_operations(document),
        "schema_count": len(document.get("components", {}).get("schemas", {})),
    }
    write_json(METADATA_PATH, metadata)
    write_json(PROJECTION_PATH, project_contract(document))

    print(json.dumps(metadata, indent=2))


def check() -> int:
    if not SNAPSHOT_PATH.exists():
        print("no committed snapshot", file=sys.stderr)
        return 1
    raw = SNAPSHOT_PATH.read_bytes()
    document = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    if metadata.get("sha256") != digest:
        print("digest mismatch between snapshot and metadata", file=sys.stderr)
        return 1
    write_json(PROJECTION_PATH, project_contract(document))
    print(f"snapshot ok: {digest} operations={count_operations(document)}")
    return 0


def check_live() -> int:
    """Compare only stable operation identities with production.

    This is intentionally opt-in rather than part of ordinary CI: network
    availability must not make the deterministic contract suite flaky.
    """
    committed = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    _, live = fetch_document()
    committed_ops = operation_inventory(committed)
    live_ops = operation_inventory(live)
    added = sorted(live_ops - committed_ops)
    removed = sorted(committed_ops - live_ops)
    if not added and not removed:
        print(f"live inventory matches snapshot: operations={len(live_ops)}")
        return 0
    print("live OpenAPI operation inventory differs from the pinned snapshot", file=sys.stderr)
    for identity in added:
        print(f"+ {identity}", file=sys.stderr)
    for identity in removed:
        print(f"- {identity}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="re-project committed snapshot only")
    modes.add_argument(
        "--check-live",
        action="store_true",
        help="opt-in comparison of live and pinned operation identities",
    )
    args = parser.parse_args()
    if args.check:
        return check()
    if args.check_live:
        return check_live()
    fetch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
