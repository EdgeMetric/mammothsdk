#!/usr/bin/env python3
"""Generate the human-readable parity report from the reviewed manifests.

The report proves that every OpenAPI operation and every public SDK method has a
reviewed disposition. Regeneration is deterministic.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SPEC = SCRIPTS.parent / "spec"
MANIFESTS = SPEC / "manifests"
REPORT = SPEC / "reports" / "parity.md"

sys.path.insert(0, str(SCRIPTS))


def _yaml(path: Path):
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build() -> str:
    metadata = json.loads((SPEC / "openapi" / "metadata.json").read_text(encoding="utf-8"))
    ops = _yaml(MANIFESTS / "openapi-operations.yaml")["operations"]
    sdk = _yaml(MANIFESTS / "sdk-methods.yaml")["methods"]
    import glob

    commands = []
    for path in sorted(glob.glob(str(MANIFESTS / "commands" / "*.yaml"))):
        commands += _yaml(Path(path))["commands"]

    disp = Counter(r["disposition"] for r in ops)
    sdk_command = sum(1 for r in sdk if r.get("canonical_command"))
    sdk_alias = sum(1 for r in sdk if r.get("alias_of"))
    sdk_exempt = sum(1 for r in sdk if not r.get("canonical_command") and not r.get("alias_of"))
    mutation = Counter(r["mutation_class"] for r in commands)
    evidence = Counter(r["acceptance_evidence"] for r in commands)

    lines: list[str] = []
    lines.append("# Mammoth CLI parity report")
    lines.append("")
    lines.append("Generated from the reviewed manifests. Do not edit by hand.")
    lines.append("")
    lines.append("## OpenAPI snapshot")
    lines.append("")
    lines.append(f"- Source: `{metadata['source_url']}`")
    lines.append(f"- SHA-256: `{metadata['sha256']}`")
    lines.append(f"- OpenAPI version: `{metadata['openapi_version']}`")
    lines.append(f"- Paths: `{metadata['path_count']}`")
    lines.append(f"- Operations: `{metadata['operation_count']}`")
    lines.append(f"- Schemas: `{metadata['schema_count']}`")
    lines.append("")
    lines.append("## Operation dispositions")
    lines.append("")
    lines.append("| Disposition | Count |")
    lines.append("|---|---:|")
    for name in ("command", "alias", "protocol_only", "deprecated", "server_unavailable"):
        lines.append(f"| {name} | {disp.get(name, 0)} |")
    lines.append(f"| **total** | **{sum(disp.values())}** |")
    lines.append("")
    lines.append("## Public SDK method parity")
    lines.append("")
    lines.append(f"- Total public methods: `{len(sdk)}`")
    lines.append(f"- With canonical command: `{sdk_command}`")
    lines.append(f"- Alias of another command: `{sdk_alias}`")
    lines.append(f"- Reviewed SDK-only exemptions: `{sdk_exempt}`")
    lines.append("")
    lines.append("## Command surface")
    lines.append("")
    lines.append(f"- Canonical + convenience commands: `{len(commands)}`")
    lines.append("")
    lines.append("### Mutation classes")
    lines.append("")
    lines.append("| Mutation class | Count |")
    lines.append("|---|---:|")
    for name in (
        "read",
        "benign_mutation",
        "reversible_pipeline",
        "destructive",
        "high_impact",
        "external_effect",
    ):
        lines.append(f"| {name} | {mutation.get(name, 0)} |")
    lines.append("")
    lines.append("### Acceptance evidence")
    lines.append("")
    lines.append("| Evidence class | Count |")
    lines.append("|---|---:|")
    for name in sorted(evidence):
        lines.append(f"| {name} | {evidence[name]} |")
    lines.append("")
    lines.append("## Protocol-only operations")
    lines.append("")
    for record in sorted(ops, key=lambda r: r["identity"]):
        if record["disposition"] == "protocol_only":
            lines.append(f"- `{record['identity']}` — {record['disposition_reason']}")
    lines.append("")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(build(), encoding="utf-8")
    print(f"wrote {REPORT}")
