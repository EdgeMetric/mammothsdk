"""Capability discovery generated from the reviewed manifests.

An agent uses these to discover which operations exist, their support state,
canonical command, SDK symbol, mutation class, and confirmation/wait/pagination
policies — without reading source.
"""

from __future__ import annotations

import re
from typing import Any

from mammoth_cli.manifest.loader import command_by_id, load_operations
from mammoth_cli.services.command_contract import resolve_command_contract

_MAX_FIND_RESULTS = 20
_MAX_FIND_LIMIT = 100
_STOPWORDS = frozenset({"a", "an", "the", "me", "please", "for", "to", "of", "by", "with"})
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "show": ("list", "get", "browse", "display", "view"),
    "display": ("show", "list", "get", "view"),
    "spreadsheet": ("csv", "xlsx", "excel", "file", "upload"),
    "csv": ("spreadsheet", "xlsx", "excel", "file", "upload"),
    "columns": ("column", "field", "fields", "schema"),
    "column": ("columns", "field", "fields", "schema"),
    "display-name": ("name", "column", "columns", "field", "fields", "schema"),
    "language": ("name", "column", "columns", "field", "fields", "schema", "text"),
    "clean": ("transform", "replace", "edit"),
    "remove": ("delete", "trash"),
    "import": ("upload", "create", "file"),
    "async": ("job", "wait", "poll"),
    "poll": ("job", "wait", "status"),
}


def capability_entries() -> list[dict[str, Any]]:
    """One capability record per OpenAPI operation."""
    entries: list[dict[str, Any]] = []
    for op in load_operations():
        command_id = op.get("canonical_command")
        command = command_by_id(command_id) if command_id else None
        resolved = resolve_command_contract(str(command_id)) if command_id else None
        entries.append(
            {
                "operation_id": op["operation_id"],
                "identity": op["identity"],
                "disposition": op["disposition"],
                "canonical_command": command_id,
                "command_path": command["command_path"] if command else None,
                "sdk_symbol": op.get("sdk_symbol"),
                "mutation_class": (
                    resolved.effects
                    if resolved is not None
                    else command["mutation_class"] if command else None
                ),
                "confirmation": command["confirmation"] if command else None,
                "wait_policy": (
                    resolved.wait_behavior
                    if resolved is not None
                    else command["wait_policy"] if command else None
                ),
                "pagination_policy": command["pagination_policy"] if command else None,
                "acceptance_evidence": command["acceptance_evidence"] if command else None,
                **(_contract_fields(command) if command else {}),
                "contract": _contract_fields(command) if command else None,
            }
        )
    return sorted(entries, key=lambda entry: entry["operation_id"])


def get_capability(operation_id: str) -> dict[str, Any] | None:
    for entry in capability_entries():
        if entry["operation_id"] == operation_id:
            return entry
    return None


def _contract_fields(command: dict[str, Any]) -> dict[str, Any]:
    """Build the compact execution contract from reviewed manifest fields.

    These values intentionally describe proof boundaries rather than claiming
    that a handler has been production-qualified.  ``None`` means the reviewed
    catalog has no evidence for that dimension.
    """
    command_id = str(command.get("command_id", ""))
    resolved = resolve_command_contract(command_id) if command_id else None
    path = str(command.get("command_path", ""))
    family = path.split()[0] if path else ""
    if family in {
        "project",
        "dataset",
        "file",
        "folder",
        "view",
        "batch",
        "annotation",
        "dashboard",
        "automation",
        "schedule",
        "snippet",
        "template",
        "workflow",
    }:
        scope = "project"
    elif family in {
        "workspace",
        "user",
        "support",
        "billing",
        "connector",
        "client-app",
        "external-key",
    }:
        scope = "workspace"
    elif family in {
        "auth",
        "config",
        "context",
        "completion",
        "doctor",
        "schema",
        "capability",
        "skill",
        "version",
    }:
        scope = "local"
    else:
        scope = "profile"
    # Keep capability discovery aligned with the resolved command contract
    # consumed by runtime admission and binding. The manifest fallback is for
    # genuinely local/bespoke records without a resolvable SDK signature.
    mutation = resolved.effects if resolved is not None else command.get("mutation_class")
    restrictions = command.get("known_restrictions")
    if restrictions is None:
        required_positionals = [
            str(item.get("metavar") or item.get("name"))
            for item in command.get("positionals", [])
            if item.get("required")
        ]
        if required_positionals:
            restrictions = "Required inputs: " + ", ".join(required_positionals) + "."
    if mutation in {None, "read"}:
        recovery = "Rerun only after checking the exit code and stable error code."
    else:
        recovery = (
            "Reconcile target/job state before retry; retain IDs and verify " "the postcondition."
        )
    return {
        "scope": scope,
        "effects": mutation,
        "preconditions": restrictions,
        "result": (
            resolved.result_contract if resolved is not None else command.get("result_model")
        ),
        "async": resolved.wait_behavior if resolved is not None else command.get("wait_policy"),
        "verification": command.get("acceptance_evidence"),
        "recovery": recovery,
        "limits": {
            "pagination": command.get("pagination_policy"),
            "continuation": (
                "not_proven" if command.get("pagination_policy") not in {None, "none"} else None
            ),
        },
    }


def _tokens(value: str) -> frozenset[str]:
    return frozenset(_TOKEN_RE.findall(value.casefold()))


def find_capabilities(
    query: str,
    *,
    limit: int = _MAX_FIND_RESULTS,
    cursor: int = 0,
) -> dict[str, Any]:
    """Find operation capabilities by stable intent/synonym ranking.

    Search is local and deterministic. Results are bounded and continuation is
    an explicit offset over the immutable sorted catalog; no server-complete
    claim is made for paginated API operations.
    """
    terms = tuple(token for token in _tokens(query) if token not in _STOPWORDS)
    bounded_limit = max(1, min(int(limit), _MAX_FIND_LIMIT))
    offset = max(0, int(cursor))
    ranked: list[tuple[int, dict[str, Any]]] = []
    for entry in capability_entries():
        text = " ".join(
            str(entry.get(key) or "")
            for key in (
                "operation_id",
                "identity",
                "canonical_command",
                "command_path",
                "sdk_symbol",
            )
        )
        candidates = _tokens(text)
        command_id = entry.get("canonical_command")
        command = command_by_id(command_id) if command_id else None
        if command:
            candidates |= _tokens(
                " ".join(
                    str(command.get(key) or "")
                    for key in ("human_example", "agent_example", "known_restrictions")
                )
            )
        score = 0
        for term in terms:
            aliases = frozenset((term, *_SYNONYMS.get(term, ())))
            hit = aliases & candidates
            if not hit:
                break
            score += 100 if term in candidates else 30
        else:
            command_path = str(entry.get("command_path") or "")
            action = command_path.split()[1] if len(command_path.split()) > 1 else ""
            if "show" in terms and action in {"list", "get", "browse"}:
                score += 80
            family = command_path.split()[0] if command_path else ""
            if any(term == family or term.rstrip("s") == family for term in terms):
                score += 120
            ranked.append((score, entry))
    ranked.sort(key=lambda item: (-item[0], str(item[1]["operation_id"])))
    total = len(ranked)
    matches = [entry for _, entry in ranked[offset : offset + bounded_limit]]
    has_more = offset + len(matches) < total
    continuation = (
        {
            "next_cursor": str(offset + len(matches)),
            "has_more": True,
            "limit": bounded_limit,
            "query": query,
        }
        if has_more
        else None
    )
    return {
        "query": query,
        "matches": matches,
        "total_matches": total,
        "truncated": has_more,
        "continuation": continuation,
    }
