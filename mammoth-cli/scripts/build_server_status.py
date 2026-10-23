#!/usr/bin/env python3
"""Derive each command's ``server_status`` from the pinned prod and master specs.

``spec/manifests/server-status.json`` says, per command, whether the production
server serves the routes the command calls:

* ``served``            every route is in the pinned prod spec (the default; not stored);
* ``pending``           a route is on server master but not in prod yet (a release away);
* ``removed_on_server`` a route is in prod but master no longer serves it.

A command's routes are the union of

* the server operations its manifest record names (``operation_ids``), and
* the routes its SDK method calls, read from the source by ``_route_scan``
  (through the same command <-> SDK-symbol mapping the capability matrix uses).

A scanned route that appears in neither spec (a dispatch template such as
``/agents/sessions/{}/runs/{}/{}``) is ignored: the operations cover it. A command
that calls no server route (local commands) is ``served``.

``mammoth_cli.manifest.loader`` merges this file into the compiled command
manifests, so ``schema`` and ``capability`` read the status without computing it.

Usage::

    python scripts/build_server_status.py          # rewrite server-status.json
    python scripts/build_server_status.py --check  # fail if it is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
CLI_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import _route_scan  # noqa: E402
from generate_release_capability_matrix import (  # noqa: E402
    OPENAPI_DIR,
    Manifests,
    current_spec_path,
    sdk_call_index,
    spec_operations,
)

OUTPUT = CLI_ROOT / "spec" / "manifests" / "server-status.json"
PROD_SPEC = OPENAPI_DIR / "openapi.json"
PROD_HOST = "app.mammoth.io"

Route = tuple[str, str]


def _routes(operations: dict[tuple[str, str], dict[str, Any]]) -> dict[Route, str | None]:
    """Normalised ``(METHOD, path)`` -> operation id for one spec."""
    return {
        (method, _route_scan.normalize_path(path)): info["operation_id"]
        for (method, path), info in operations.items()
    }


def _load(path: Path) -> tuple[dict[Route, str | None], dict[str, Any]]:
    metadata = json.loads(path.with_suffix(".metadata.json").read_text(encoding="utf-8"))
    return _routes(spec_operations(json.loads(path.read_text(encoding="utf-8")))), metadata


def classify(prod: set[Route], master: set[Route], routes: set[Route]) -> str:
    """The status of a command that calls ``routes``."""
    known = {route for route in routes if route in prod or route in master}
    if any(route in prod and route not in master for route in known):
        return "removed_on_server"
    if any(route in master and route not in prod for route in known):
        return "pending"
    return "served"


def derive() -> dict[str, Any]:
    """The full ``server-status.json`` document."""
    prod_meta_path = PROD_SPEC.with_name("metadata.json")
    prod_meta = json.loads(prod_meta_path.read_text(encoding="utf-8"))
    if PROD_HOST not in str(prod_meta.get("source_url")):
        raise SystemExit(f"{PROD_SPEC.name} is not the production spec: {prod_meta}")
    prod_routes = _routes(spec_operations(json.loads(PROD_SPEC.read_text(encoding="utf-8"))))
    master_path = current_spec_path()
    master_routes, master_meta = _load(master_path)
    manifests = Manifests()
    by_operation = {op: route for route, op in {**prod_routes, **master_routes}.items() if op}
    _, scanned = sdk_call_index()
    scanned_routes: dict[str, set[Route]] = defaultdict(set)
    for call in scanned:
        if manifests.knows(call.sdk_symbol):
            command = manifests.command_of(call.sdk_symbol)
            if command:
                scanned_routes[command].add((call.method, call.path))
    prod, master = set(prod_routes), set(master_routes)
    commands: dict[str, Any] = {}
    for command_id, record in sorted(manifests.commands.items()):
        routes = set(scanned_routes.get(command_id, ()))
        for operation_id in record.get("operation_ids") or []:
            if operation_id in by_operation:
                routes.add(by_operation[operation_id])
        status = classify(prod, master, routes)
        if status != "served":
            commands[command_id] = {
                "server_status": status,
                "routes": sorted(
                    f"{method} {path}" for method, path in routes if (method, path) in prod ^ master
                ),
            }
    return {
        "artifact": "mammoth-cli-command-server-status",
        "note": (
            "Derived by scripts/build_server_status.py; do not edit. Commands not listed "
            "are served."
        ),
        "prod_spec": {"file": f"spec/openapi/{PROD_SPEC.name}", "sha256": prod_meta["sha256"]},
        "master_spec": {
            "file": f"spec/openapi/{master_path.name}",
            "source_sha": master_meta["source_sha"],
            "sha256": master_meta["sha256"],
        },
        "commands": commands,
    }


def render(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when the file is stale")
    args = parser.parse_args()
    expected = render(derive())
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != expected:
            print(f"STALE {OUTPUT}. Run: python scripts/build_server_status.py", file=sys.stderr)
            return 1
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
