#!/usr/bin/env python3
"""Derive the release capability matrix from the server spec, the manifests and the SDK.

``docs/release-capability-matrix.json`` holds one row per server operation. Two
kinds of field live on a row:

* **Reviewed, stored**: ``capability``, ``status``, ``remarks``, ``evidence``,
  ``evidence_version``. This script never changes them.
* **Derived, recomputed on every run**: the mapping fields. They come from
  - the newest ``spec/openapi/master-<YYYYMMDD>.json`` (which operations exist),
  - ``scripts/_route_scan.py`` (which SDK function calls which route),
  - ``spec/manifests`` (which command wraps which SDK function), and
  - the reviewed tables in ``scripts/_command_map.py`` (protocol-only, internal).

An operation on the server with no row gets a new ``Unassessed`` row. A row
whose operation left the server is kept, with its evidence, as
``removed_on_server``.

Usage::

    python scripts/generate_release_capability_matrix.py          # re-derive both files
    python scripts/generate_release_capability_matrix.py --check  # fail if they are stale
"""

from __future__ import annotations

import argparse
import difflib
import glob
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

SCRIPTS = Path(__file__).resolve().parent
CLI_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import _command_map as cmap  # noqa: E402
import _route_scan  # noqa: E402
from _sdk_catalog import CLI_ONLY_COMMANDS  # noqa: E402
from report_release_capability_drift import scaffold_addition  # noqa: E402

DOCS = CLI_ROOT / "docs"
DEFAULT_MATRIX = DOCS / "release-capability-matrix.json"
DEFAULT_MARKDOWN = DOCS / "release-capability-matrix.md"
OPENAPI_DIR = CLI_ROOT / "spec" / "openapi"
MANIFESTS = CLI_ROOT / "spec" / "manifests"
HTTP_METHODS = ("get", "put", "post", "delete", "patch", "head", "options")
STATUSES = ("Full", "Partial", "Not supported", "Unassessed")
UNMAPPED_GAP = "No reviewed CLI command or SDK symbol recorded."
REMOVED_GAP = "The server on master no longer serves this route."
SDK_ONLY_GAP = "An SDK method calls this route; no command wraps it."
MD_COLUMNS = (
    "capability_id",
    "capability",
    "status",
    "remarks",
    "core_vs_misc",
    "operation_id",
    "method",
    "path",
    "canonical_command",
    "schema_id",
    "sdk_symbol",
    "mapping_state",
    "mapping_gap_reason",
    "evidence",
    "evidence_version",
)


# --- inputs ---------------------------------------------------------------


def current_spec_path() -> Path:
    """The newest pinned server snapshot, ``master-<YYYYMMDD>.json``."""
    found = sorted(glob.glob(str(OPENAPI_DIR / "master-????????.json")))
    if not found:
        raise SystemExit("no spec/openapi/master-<YYYYMMDD>.json snapshot; run sync_openapi.py")
    return Path(found[-1])


def spec_operations(document: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    """Server operations keyed by ``(METHOD, path)``."""
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for path, item in document.get("paths", {}).items():
        for method in HTTP_METHODS:
            operation = item.get(method)
            if isinstance(operation, dict):
                found[(method.upper(), path)] = {
                    "operation_id": operation.get("operationId"),
                    "summary": operation.get("summary") or "",
                }
    return found


class Manifests:
    """The reviewed command, SDK-method and operation manifests, indexed for lookup."""

    def __init__(self) -> None:
        sdk = yaml.safe_load((MANIFESTS / "sdk-methods.yaml").read_text(encoding="utf-8"))
        self.sdk = {record["sdk_symbol"]: record for record in sdk["methods"]}
        self.commands: dict[str, dict[str, Any]] = {}
        for source in sorted((MANIFESTS / "commands").glob("*.yaml")):
            loaded = yaml.safe_load(source.read_text(encoding="utf-8"))
            for record in loaded["commands"]:
                self.commands[record["command_id"]] = record
        operations = yaml.safe_load((MANIFESTS / "openapi-operations.yaml").read_text("utf-8"))
        self.operations = {record["operation_id"]: record for record in operations["operations"]}
        self.commands_by_operation: dict[str, set[str]] = defaultdict(set)
        self.command_by_symbol: dict[str, str] = {}
        for command_id, record in self.commands.items():
            for operation_id in record.get("operation_ids") or []:
                self.commands_by_operation[operation_id].add(command_id)
            if record.get("sdk_symbol"):
                self.command_by_symbol.setdefault(str(record["sdk_symbol"]), command_id)

    def knows(self, symbol: str) -> bool:
        """True for a public SDK method the manifests record, by method or by command."""
        return symbol in self.sdk or symbol in self.command_by_symbol

    def command_of(self, symbol: str) -> str | None:
        """The command that wraps ``symbol``: the SDK manifest first, then the command manifests."""
        record = self.sdk.get(symbol, {})
        return (
            record.get("canonical_command")
            or record.get("alias_of")
            or (self.command_by_symbol.get(symbol))
        )


# --- derivation -----------------------------------------------------------


def _bindings(
    key: tuple[str, str],
    operation_id: str | None,
    manifests: Manifests,
    calls: dict[tuple[str, str], set[str]],
) -> tuple[set[str], set[str], set[str]]:
    """Commands (direct), commands (alias only) and public SDK symbols bound to one route."""
    symbols = {s for s in calls.get((key[0], _route_scan.normalize_path(key[1])), set())}
    public = {s for s in symbols if manifests.knows(s)}
    direct = {manifests.command_of(s) for s in public} - {None}
    direct |= set(manifests.commands_by_operation.get(operation_id or "", set()))
    aliased: set[str] = set()
    record = manifests.operations.get(operation_id or "")
    if record and record.get("disposition") == "alias" and record.get("alias_of"):
        aliased.add(str(record["alias_of"]))
    for command in direct | aliased:
        command_record = manifests.commands.get(str(command), {})
        if command_record.get("sdk_symbol"):
            public.add(str(command_record["sdk_symbol"]))
    return {str(c) for c in direct}, aliased, public


def _pick(stored: Any, candidates: set[str], preferred: set[str]) -> str | None:
    """Keep the stored choice while it is still bound; otherwise the first preferred one."""
    if stored in candidates:
        return str(stored)
    pool = sorted(preferred & candidates) or sorted(candidates)
    return pool[0] if pool else None


def derive_mapping(
    row: dict[str, Any],
    live: bool,
    manifests: Manifests,
    calls: dict[tuple[str, str], set[str]],
) -> dict[str, Any]:
    """Return the derived mapping fields for one row."""
    key, operation_id = (row["method"], row["path"]), row.get("operation_id")
    none: dict[str, Any] = {"canonical_command": None, "sdk_symbol": None, "bound_commands": []}
    if not live:
        return {**none, "mapping_state": "removed_on_server", "mapping_gap_reason": REMOVED_GAP}
    reasons = {
        "protocol_only": cmap.PROTOCOL_ONLY.get(str(operation_id)),
        "internal_only": cmap.INTERNAL_ONLY.get(str(operation_id)),
    }
    record = manifests.operations.get(str(operation_id))
    if record and record.get("disposition") == "protocol_only":
        reasons["protocol_only"] = record["disposition_reason"]
    for state, reason in reasons.items():
        if reason:
            return {**none, "mapping_state": state, "mapping_gap_reason": reason}
    direct, aliased, symbols = _bindings(key, operation_id, manifests, calls)
    if direct:
        command = _pick(row.get("canonical_command"), direct | aliased, direct)
        owned = {
            str(manifests.commands[c]["sdk_symbol"])
            for c in direct | aliased
            if c in manifests.commands and manifests.commands[c].get("sdk_symbol")
        }
        symbol = _pick(row.get("sdk_symbol"), symbols, owned) if symbols else None
        return {
            "canonical_command": command,
            "sdk_symbol": symbol,
            "bound_commands": sorted(direct | aliased),
            "mapping_state": "cli_and_sdk_mapped" if symbol else "cli_mapped",
            "mapping_gap_reason": None,
        }
    if aliased:
        reason = (record or {}).get("disposition_reason") or "Alias of another command."
        return {
            **none,
            "bound_commands": sorted(aliased),
            "mapping_state": "alias",
            "mapping_gap_reason": f"{reason} Covered by: {', '.join(sorted(aliased))}.",
        }
    if symbols:
        return {
            **none,
            "sdk_symbol": sorted(symbols)[0],
            "mapping_state": "sdk_only",
            "mapping_gap_reason": SDK_ONLY_GAP,
        }
    return {**none, "mapping_state": "unmapped", "mapping_gap_reason": UNMAPPED_GAP}


def new_row(key: tuple[str, str], info: dict[str, Any], sha: str) -> dict[str, Any]:
    """A deliberately unassessed row for an operation the matrix has not seen."""
    row = scaffold_addition(
        {"method": key[0], "path": key[1], "operation_id": info["operation_id"]}
    )
    if info["summary"]:
        row["capability"] = info["summary"]
    row["remarks"] = (
        f"New on server master {sha[:10]}; assign ownership and evidence before any "
        "support claim."
    )
    return row


def sdk_call_index() -> tuple[dict[tuple[str, str], set[str]], list[_route_scan.SdkCall]]:
    scanned = _route_scan.scan_sdk()
    index: dict[tuple[str, str], set[str]] = defaultdict(set)
    for call in scanned:
        index[(call.method, call.path)].add(call.sdk_symbol)
    return index, scanned


def unrouted_calls(
    scanned: list[_route_scan.SdkCall], live_routes: set[tuple[str, str]], manifests: Manifests
) -> list[dict[str, Any]]:
    """SDK calls whose route the server on master does not serve."""
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for call in scanned:
        if (call.method, call.path) in live_routes:
            continue
        route = f"{call.method} {call.path}"
        pending = cmap.PENDING_SERVER_RELEASE.get(route)
        entry = found.setdefault(
            (call.method, call.path),
            {
                "method": call.method,
                "path": call.path,
                "state": "pending_server_release" if pending else "removed_on_server",
                "pending_in": pending,
                "sdk_symbols": [],
                "commands": [],
            },
        )
        entry["sdk_symbols"].append(call.sdk_symbol)
        command = manifests.command_of(call.sdk_symbol)
        if command:
            entry["commands"].append(command)
    for entry in found.values():
        entry["sdk_symbols"] = sorted(set(entry["sdk_symbols"]))
        entry["commands"] = sorted(set(entry["commands"]))
    return sorted(found.values(), key=lambda e: (e["path"], e["method"]))


def commands_without_route(manifests: Manifests, bound: set[str]) -> list[str]:
    """Commands that reach no server route through any matrix row (local or wrapper commands)."""
    local = set(CLI_ONLY_COMMANDS)
    return sorted(
        command_id
        for command_id, record in manifests.commands.items()
        if record.get("disposition", "command") == "command"
        and command_id not in bound
        and command_id not in local
    )


# --- build ----------------------------------------------------------------


def build_payload(source: dict[str, Any], raw: bytes) -> dict[str, Any]:
    rows = source.get("rows", source.get("operations"))
    if not isinstance(rows, list):
        raise ValueError("source must contain an operations or rows array")
    spec_file = current_spec_path()
    metadata = json.loads(spec_file.with_suffix(".metadata.json").read_text(encoding="utf-8"))
    live = spec_operations(json.loads(spec_file.read_text(encoding="utf-8")))
    manifests = Manifests()
    calls, scanned = sdk_call_index()
    stored = {(row["method"].upper(), row["path"]): row for row in rows}
    ordered = [(key, row) for key, row in ((k, stored[k]) for k in stored)]
    additions = sorted(set(live) - set(stored), key=lambda k: (k[1], k[0]))
    ordered += [(key, new_row(key, live[key], metadata["source_sha"])) for key in additions]
    safe_rows = [_final_row(row, key in live, manifests, calls) for key, row in ordered]
    counts = Counter(row["status"] for row in safe_rows)
    states = Counter(row["mapping_state"] for row in safe_rows)
    bound = {c for row in safe_rows for c in row["bound_commands"]}
    live_routes = {(method, _route_scan.normalize_path(path)) for method, path in live}
    unrouted = unrouted_calls(scanned, live_routes, manifests)
    unrouted_commands = {c for entry in unrouted for c in entry["commands"]}
    digest = source.get("source_sha256") or hashlib.sha256(raw).hexdigest()
    return {
        "artifact": "mammoth-cli-release-capability-matrix",
        "source_sha256": digest,
        "source_provenance": dict(source.get("source_provenance", source.get("provenance", {}))),
        "server_spec": {
            "file": f"spec/openapi/{spec_file.name}",
            "source_ref": metadata["source_ref"],
            "source_sha": metadata["source_sha"],
            "sha256": metadata["sha256"],
            "operations": len(live),
            "paths": len({path for _, path in live}),
        },
        "counts": {name: counts.get(name, 0) for name in STATUSES},
        "mapping_counts": dict(sorted(states.items())),
        "unrouted_sdk_calls": unrouted_calls(
            scanned, {(m, _route_scan.normalize_path(p)) for m, p in live}, manifests
        ),
        "commands_without_route": commands_without_route(manifests, bound | unrouted_commands),
        "rows": safe_rows,
        "note": (
            "Sanitized row-level inventory; workbook remains authoritative. "
            "No credentials or pilot payloads are included. Mapping fields are derived by "
            "scripts/generate_release_capability_matrix.py; status and evidence are reviewed."
        ),
    }


def _final_row(
    row: dict[str, Any],
    live: bool,
    manifests: Manifests,
    calls: dict[tuple[str, str], set[str]],
) -> dict[str, Any]:
    status = row.get("status") or "Unassessed"
    if status not in STATUSES:
        raise ValueError(f"unexpected status: {status}")
    remarks = row.get("remarks") or "Unassessed pending approval and release evidence."
    if status == "Partial" and "Partial" not in remarks:
        remarks = f"Partial bounded evidence only; {remarks}"
    mapping = derive_mapping({**row, "method": row["method"].upper()}, live, manifests, calls)
    return {
        "capability_id": row["capability_id"],
        "capability": row["capability"],
        "status": status,
        "remarks": remarks,
        "core_vs_misc": row["core_vs_misc"],
        "operation_id": row["operation_id"],
        "method": row["method"].upper(),
        "path": row["path"],
        "canonical_command": mapping["canonical_command"],
        "schema_id": mapping["canonical_command"],
        "sdk_symbol": mapping["sdk_symbol"],
        "bound_commands": mapping["bound_commands"],
        "mapping_state": mapping["mapping_state"],
        "mapping_gap_reason": mapping["mapping_gap_reason"],
        "evidence": row.get("evidence"),
        "evidence_version": row.get("evidence_version"),
    }


def _cell(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, dict):

        def item_text(item: object) -> str:
            return ", ".join(map(str, item)) if isinstance(item, list) else str(item)

        value = "; ".join(f"{k}={item_text(v)}" for k, v in value.items() if v is not None)
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(payload: dict[str, Any]) -> str:
    rows, counts, spec = payload["rows"], payload["counts"], payload["server_spec"]
    removed = sum(1 for row in rows if row["mapping_state"] == "removed_on_server")
    lines = [
        "# Release capability matrix (sanitized)",
        "",
        f"Source workbook SHA-256: `{payload['source_sha256']}`.",
        f"Server spec: `{spec['source_ref']}` at `{spec['source_sha'][:10]}`, "
        f"{spec['operations']} operations / {spec['paths']} paths "
        f"(`{spec['file']}`); {len(rows)} rows, {removed} removed on the server.",
        "Statuses: " + ", ".join(f"{counts[name]} {name}" for name in counts) + ".",
        "Mapping: " + ", ".join(f"{n} {s}" for s, n in payload["mapping_counts"].items()) + ".",
        "Mapping fields are derived (`scripts/generate_release_capability_matrix.py`); "
        "status and evidence are reviewed. This is the canonical sanitized repository "
        "inventory; historical workbooks retain their original evidence context.",
        "",
        "| ID | Capability | Status | Remarks | Group | Operation | Method | Path | CLI | "
        "Schema ID | SDK | Mapping state | Mapping gap | Evidence | Evidence version |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    lines += ["| " + " | ".join(_cell(row[key]) for key in MD_COLUMNS) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _stale(path: Path, expected: str) -> str | None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == expected:
        return None
    diff = difflib.unified_diff(
        current.splitlines(), expected.splitlines(), str(path), "derived", n=0, lineterm=""
    )
    return "\n".join(list(diff)[:40])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check", action="store_true", help="fail when the files are stale")
    args = parser.parse_args()
    raw = args.source.read_bytes()
    payload = build_payload(json.loads(raw), raw)
    identities = {(row["method"], row["path"]) for row in payload["rows"]}
    if len(identities) != len(payload["rows"]):
        raise ValueError("matrix integrity failed: duplicate method/path identity")
    outputs = {args.json_out: render_json(payload), args.markdown_out: render_markdown(payload)}
    if args.check:
        stale = {path: _stale(path, text) for path, text in outputs.items()}
        problems = {path: diff for path, diff in stale.items() if diff}
        for path, diff in problems.items():
            print(f"STALE {path}\n{diff}", file=sys.stderr)
        if problems:
            print(
                "The capability matrix no longer matches the server spec, the command "
                "manifests and the SDK. Run: python scripts/generate_release_capability_matrix.py",
                file=sys.stderr,
            )
        return 1 if problems else 0
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
