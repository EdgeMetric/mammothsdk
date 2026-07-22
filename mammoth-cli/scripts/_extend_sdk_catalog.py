#!/usr/bin/env python3
"""Extend the reviewed SDK catalog with entries for newly added SDK methods.

Phase 2 adds public typed SDK methods that implement command operations. Each
such method must appear in ``sdk-catalog.source.yaml`` mapped to its canonical
command so the regenerated ``sdk-methods.yaml`` records the command link (not a
generic SDK-only-helper disposition).

Run order:
  1. python scripts/build_manifests.py           # refresh openapi-operations.yaml
  2. python scripts/_extend_sdk_catalog.py        # append missing catalog entries
  3. python scripts/build_manifests.py            # regenerate with the links

This is idempotent: it only appends catalog entries for symbols that are present
in live introspection, are missing from the catalog, and have a reviewed
command/alias mapping derivable from the operation manifest.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPTS = Path(__file__).resolve().parent
SPEC = SCRIPTS.parent / "spec"
CATALOG_SOURCE = SPEC / "manifests" / "sdk-catalog.source.yaml"
OPERATIONS = SPEC / "manifests" / "openapi-operations.yaml"
REPO_ROOT = SCRIPTS.parent.parent

sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO_ROOT))

# Phase-2 SDK-foundation seams that intentionally have no CLI command.
SEAM_REASONS: dict[str, str] = {
    "mammoth.client.MammothClient.close": (
        "SDK-only lifecycle seam; the CLI closes the client through the context "
        "manager, not a command."
    ),
    "mammoth.client.MammothClient.wait_if_job": (
        "SDK-only generated-operation wait seam; CLI commands apply it from their "
        "reviewed wait policy rather than exposing a separate command."
    ),
    "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview": (
        "SDK-only dataview->dataset resolver seam used by public view "
        "conveniences; not a CLI command."
    ),
    "mammoth.api.pipeline.PipelineAPI.get_draft_status": (
        "Server-backed draft-status seam read by the draft verbs; surfaced "
        "through 'view draft status', not its own SDK-mapped command."
    ),
}


def _live_symbols() -> list[dict[str, Any]]:
    import inventory_sdk

    return inventory_sdk.build_document()["methods"]


def _symbol_to_command() -> dict[str, str]:
    data = yaml.safe_load(OPERATIONS.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for op in data["operations"]:
        if op.get("disposition") != "command":
            continue
        symbol = op.get("sdk_symbol")
        command = op.get("canonical_command")
        if symbol and command and symbol not in mapping:
            mapping[symbol] = command
    return mapping


def main() -> int:
    catalog = yaml.safe_load(CATALOG_SOURCE.read_text(encoding="utf-8"))
    entries: list[dict[str, Any]] = catalog["sdk_methods"]
    known = {entry["sdk_symbol"] for entry in entries}

    sym_to_cmd = _symbol_to_command()
    added: list[str] = []
    for method in _live_symbols():
        symbol = method["sdk_symbol"]
        if symbol in known:
            continue
        command = sym_to_cmd.get(symbol)
        if command is not None:
            entries.append(
                {
                    "sdk_symbol": symbol,
                    "canonical_command": command,
                    "alias_of": None,
                    "mutation_class": None,
                    "wait_policy": None,
                    "pagination_policy": None,
                    "openapi_operation_ids": [],
                }
            )
            added.append(f"{symbol} -> {command}")
        elif symbol in SEAM_REASONS:
            entries.append(
                {
                    "sdk_symbol": symbol,
                    "canonical_command": None,
                    "alias_of": None,
                    "mutation_class": None,
                    "wait_policy": None,
                    "pagination_policy": None,
                    "openapi_operation_ids": [],
                    "notes": SEAM_REASONS[symbol],
                }
            )
            added.append(f"{symbol} -> (SDK-only seam)")

    entries.sort(key=lambda entry: entry["sdk_symbol"])
    CATALOG_SOURCE.write_text(
        yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    print(f"appended {len(added)} catalog entries")
    for line in added:
        print("  ", line)
    unmapped = [
        m["sdk_symbol"]
        for m in _live_symbols()
        if m["sdk_symbol"] not in known
        and m["sdk_symbol"] not in sym_to_cmd
        and m["sdk_symbol"] not in SEAM_REASONS
    ]
    if unmapped:
        print(f"WARNING: {len(unmapped)} new symbols have no command and no seam reason:")
        for symbol in unmapped:
            print("  ", symbol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
