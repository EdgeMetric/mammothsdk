#!/usr/bin/env python3
"""Fetch and pin the production Mammoth OpenAPI snapshot.

This is an explicit maintenance operation. It reaches the network. Ordinary CI
must not run it; CI validates the committed snapshot only.

The live OpenAPI generator is nondeterministic. Repeated fetches keep the path
and operation counts stable but change examples, some defaults, parameter order,
and some descriptions. This script does two things:

1. Save the raw response, with credential-shaped example values redacted (see
   :func:`scrub_examples`), and its SHA-256 to ``spec/openapi/openapi.json``
   and ``spec/openapi/metadata.json``. That snapshot is the pinned contract and
   ships inside the wheel, so it must never carry a real key.
2. Write a normalized *contract projection* to ``spec/openapi/projection.json``.
   The projection removes ``example``/``examples``, sorts parameter arrays by
   location then name, and sorts object keys. A primary reviewer compares the
   projection across fetches to classify semantic differences before replacing
   the pinned snapshot.

Usage::

    python scripts/sync_openapi.py            # fetch, write snapshot + projection + _spec.json pins
    python scripts/sync_openapi.py --check    # re-project committed snapshot only
    python scripts/sync_openapi.py --scrub    # redact the committed snapshot in place
    python scripts/sync_openapi.py --check-live  # opt-in semantic contract drift check
    python scripts/sync_openapi.py --from-file master.json --name master-20261002 \\
        --source-ref origin/master --source-sha <git sha> --method "<how it was generated>"

``--from-file`` pins a spec generated offline from server source (for example
``litestar`` ``app.openapi_schema`` exported from a checkout) as a NEW named
snapshot ``spec/openapi/<name>.json`` plus ``<name>.metadata.json``. It never
touches the production snapshot above. The release capability matrix is derived
from the newest ``master-<YYYYMMDD>.json``.

After reviewing a newly fetched candidate, generate a local release-matrix
drift queue with ``report_release_capability_drift.py``. That report is keyed
by method/path and never promotes or implements a capability automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
#: Each build records the spec it was generated from; both ship inside their wheel.
PIN_PATHS = (
    SPEC_DIR.parents[2] / "mammoth" / "_spec.json",
    SPEC_DIR.parents[1] / "mammoth_cli" / "_spec.json",
)

#: ``--check-live`` exit code for real drift; any other non-zero code is an error
#: (network failure, bad JSON, crash) and must never trigger a publish.
DRIFT_EXIT = 2

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}

#: Example fields whose string values are replaced before the snapshot is
#: written.  The backend generates its examples from live objects, so a
#: client-app key or a webhook key can appear verbatim in the document.
_SECRET_FIELDS = (
    "api_key",
    "api_secret",
    "secret",
    "token",
    "password",
    "access_key",
    "secret_key",
    "secret_access_key",
    "private_key",
    "client_secret",
    "access_token",
    "refresh_token",
)
_REDACTED = "REDACTED_EXAMPLE"
_SECRET_VALUE = re.compile(r'"(' + "|".join(_SECRET_FIELDS) + r')"(\s*:\s*)"[^"]*"')
# A bare ``key`` is a common map example ("key": "value"); redact it only when
# the value looks like a generated credential.
_KEY_VALUE = re.compile(r'"key"(\s*:\s*)"([A-Za-z0-9_-]{16,})"')
_WEBHOOK_PATH = re.compile(r"(/webhook/data/)[A-Za-z0-9_-]{16,}")


def scrub_examples(text: str) -> str:
    """Return ``text`` with credential-shaped example values redacted.

    Only string *values* are touched; property names, schemas, and the
    document's structure are unchanged, so the contract projection is the
    same before and after.
    """
    text = _SECRET_VALUE.sub(lambda m: f'"{m.group(1)}"{m.group(2)}"{_REDACTED}"', text)
    text = _KEY_VALUE.sub(lambda m: f'"key"{m.group(1)}"{_REDACTED}"', text)
    return _WEBHOOK_PATH.sub(lambda m: f"{m.group(1)}{_REDACTED}", text)


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


def _strip_documentation(node: Any) -> Any:
    """Remove presentation-only fields from a semantic contract comparison."""
    if isinstance(node, dict):
        return {
            key: _strip_documentation(value)
            for key, value in sorted(node.items())
            if key
            not in {
                "default",
                "description",
                "example",
                "examples",
                "externalDocs",
                "summary",
                "title",
            }
        }
    if isinstance(node, list):
        return [_strip_documentation(item) for item in node]
    return node


def semantic_contract(document: dict[str, Any]) -> dict[str, Any]:
    """Return the API surface used by live drift monitoring.

    Unlike the operation inventory, this retains parameters, request bodies,
    responses, component schemas, requiredness, and types. Documentation and
    examples and server-supplied defaults are excluded because they do not
    change the accepted or returned wire shape. The production fleet can also
    serve different UI defaults during a rolling deployment; monitoring them
    would make this scheduled structural check nondeterministic.
    """
    projected = _strip_documentation(document)
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
                    key=lambda parameter: (
                        str(parameter.get("in", "")) if isinstance(parameter, dict) else "",
                        str(parameter.get("name", "")) if isinstance(parameter, dict) else "",
                    ),
                )
    return projected


def spec_sha256(document: dict[str, Any]) -> str:
    """Hash the semantic contract, never raw bytes (the live generator is nondeterministic)."""
    canonical = json.dumps(semantic_contract(document), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def write_pin(document: dict[str, Any], source_ref: str, source_sha: str | None) -> None:
    """Record the spec an SDK/CLI build was generated from."""
    pin = {
        "spec_sha256": spec_sha256(document),
        "source_ref": source_ref,
        "source_sha": source_sha,
    }
    for path in PIN_PATHS:
        write_json(path, pin)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch(source_ref: str | None = None, source_sha: str | None = None) -> None:
    raw, _ = fetch_document()
    raw = scrub_examples(raw.decode("utf-8")).encode("utf-8")
    document = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()

    SPEC_DIR.mkdir(parents=True, exist_ok=True)
    # Preserve the redacted bytes as the pinned contract.
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
    write_pin(document, source_ref or SOURCE_URL, source_sha)

    print(json.dumps(metadata, indent=2))


def pin_from_file(
    source: Path, name: str, source_ref: str, source_sha: str, method: str
) -> dict[str, Any]:
    """Pin an offline-generated spec as ``spec/openapi/<name>.json`` and return its metadata."""
    document = json.loads(scrub_examples(source.read_text(encoding="utf-8")))
    raw = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    SPEC_DIR.mkdir(parents=True, exist_ok=True)
    (SPEC_DIR / f"{name}.json").write_bytes(raw)
    metadata = {
        "artifact": "mammoth-cli-server-openapi-snapshot",
        "source_ref": source_ref,
        "source_sha": source_sha,
        "generation_method": method,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "openapi_version": document.get("openapi"),
        "api_version": document.get("info", {}).get("version"),
        "path_count": len(document.get("paths", {})),
        "operation_count": count_operations(document),
        "schema_count": len(document.get("components", {}).get("schemas", {})),
    }
    write_json(SPEC_DIR / f"{name}.metadata.json", metadata)
    return metadata


def scrub() -> int:
    """Redact the committed snapshot in place and re-pin its digest."""
    text = SNAPSHOT_PATH.read_text(encoding="utf-8")
    scrubbed = scrub_examples(text)
    if scrubbed == text:
        print("snapshot already clean")
        return 0
    raw = scrubbed.encode("utf-8")
    SNAPSHOT_PATH.write_bytes(raw)
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    metadata["sha256"] = hashlib.sha256(raw).hexdigest()
    metadata["redacted_example_fields"] = list(_SECRET_FIELDS) + ["key (credential-shaped)"]
    write_json(METADATA_PATH, metadata)
    print(f"snapshot scrubbed: {metadata['sha256']}")
    return 0


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
    if scrub_examples(raw.decode("utf-8")) != raw.decode("utf-8"):
        print("snapshot carries credential-shaped example values; run --scrub", file=sys.stderr)
        return 1
    write_json(PROJECTION_PATH, project_contract(document))
    print(f"snapshot ok: {digest} operations={count_operations(document)}")
    return 0


def check_live() -> int:
    """Compare the normalized semantic API contract with production.

    This is intentionally opt-in rather than part of ordinary CI: network
    availability must not make the deterministic contract suite flaky.
    """
    committed = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    _, live = fetch_document()
    committed_ops = operation_inventory(committed)
    live_ops = operation_inventory(live)
    added = sorted(live_ops - committed_ops)
    removed = sorted(committed_ops - live_ops)
    semantic_changed = semantic_contract(committed) != semantic_contract(live)
    if not added and not removed and not semantic_changed:
        print(f"live semantic contract matches snapshot: operations={len(live_ops)}")
        return 0
    print("live OpenAPI contract differs from the pinned snapshot", file=sys.stderr)
    for identity in added:
        print(f"+ {identity}", file=sys.stderr)
    for identity in removed:
        print(f"- {identity}", file=sys.stderr)
    if semantic_changed and not added and not removed:
        print("~ request, response, parameter, or component schema changed", file=sys.stderr)
    return DRIFT_EXIT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="re-project committed snapshot only")
    modes.add_argument("--scrub", action="store_true", help="redact the committed snapshot")
    modes.add_argument(
        "--check-live",
        action="store_true",
        help="opt-in comparison of the live and pinned semantic contracts",
    )
    parser.add_argument("--from-file", type=Path, help="pin this offline-generated spec")
    parser.add_argument("--name", help="snapshot name for --from-file, e.g. master-20261002")
    parser.add_argument("--source-ref", help="git ref the spec was generated from")
    parser.add_argument("--source-sha", help="git sha the spec was generated from")
    parser.add_argument("--method", help="how the spec was generated")
    args = parser.parse_args()
    if args.from_file:
        required = (args.name, args.source_ref, args.source_sha, args.method)
        if not all(required):
            parser.error("--from-file needs --name, --source-ref, --source-sha and --method")
        print(
            json.dumps(
                pin_from_file(
                    args.from_file, args.name, args.source_ref, args.source_sha, args.method
                ),
                indent=2,
            )
        )
        return 0
    if args.check:
        return check()
    if args.scrub:
        return scrub()
    if args.check_live:
        return check_live()
    fetch(args.source_ref, args.source_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
