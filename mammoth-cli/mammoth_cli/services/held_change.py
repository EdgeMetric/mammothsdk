"""Name a held plan change for a confirmation or a dry-run report."""

from __future__ import annotations

from typing import Any


def describe_held_change(held: Any) -> str:
    """Name a held change: its plan, billing cycle, storage, and whether it moves plan."""
    if hasattr(held, "model_dump"):
        held = held.model_dump(mode="json")
    held = held if isinstance(held, dict) else {}
    parts = [str(held.get("plan_name") or held.get("plan_id") or "unknown plan")]
    if held.get("billing_cycle"):
        parts.append(str(held["billing_cycle"]))
    if held.get("storage_gb") is not None:
        parts.append(f"{held['storage_gb']} GB storage")
    if held.get("changes_plan") is False:
        parts.append("storage only")
    return ", ".join(parts)
