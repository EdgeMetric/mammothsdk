"""Static parity guard: runtime confirmation gate vs. manifest ``confirmation``.

The in-app agent product decides whether to show the user a confirmation card
purely from the MANIFEST's ``confirmation`` field -- it never runs the CLI to
find out what the runtime actually enforces. A command whose handler demands
``--yes`` unconditionally when the manifest promises ``confirmation: none``
(or vice versa) is therefore invisible to that product: either the model
silently learns to always pass ``--yes`` (a runtime gate the manifest doesn't
declare bypasses nothing useful), or the manifest promises a safety check
that never fires.

This is a static, source-level sweep (it reads handler source; it invokes
nothing) over every command id registered in
:data:`mammoth_cli.commands.registry.HANDLERS`, in the same style as
``test_handler_positional_parity.py``. For each handler it collects every
*unconditional* ``enforce_confirmation(...)`` call -- one not nested inside an
``if`` -- whose ``policy=`` argument is a statically-literal ``POLICY_*``
constant, and requires the manifest's ``confirmation`` to be among those
literals.

Two shapes are deliberately NOT flagged, to keep this test's signal free of
noise from legitimate patterns already in the tree:

* A call nested inside an ``if`` guards one documented sub-case (for example
  ``batch.create``'s destructive ``delete_source_ds`` branch, or
  ``view.draft.command``'s submit/discard branch) rather than the command's
  baseline -- the manifest's ``confirmation`` describes the baseline.
* A handler with zero *unconditional literal* calls is skipped rather than
  required to be ``none``: several families (``support.py``'s ``_confirm``
  helper, for one) enforce confirmation through a shared local helper one
  call away, which this single-function scan does not chase, and flagging
  that indirection as "no gate" would be a false positive, not a finding.

Within that scope it still catches the actual shape of the bug this guards:
a handler shared by many command ids (``view_export_specialized`` served all
17 typed ``view.export.*`` routes) passing ONE hardcoded literal policy for
all of them. Before the fix this test failed with:
``view.export.dataset: manifest confirmation='none' not in the literal
policy handler view_export_specialized enforces: ['yes_always']``.
Every typed export route additionally has a direct behavioral test in
``tests/unit/commands/test_view_export_specialized.py``, which is the
authority for that family; this test is the tree-wide backstop against the
same hardcoded-literal shape recurring elsewhere.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from collections.abc import Callable
from typing import Any

from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_NONE,
    POLICY_PROMPT_OR_YES,
    POLICY_YES_ALWAYS,
)

# Every module that calls ``enforce_confirmation`` imports these four names
# unchanged from ``mammoth_cli.runtime.confirm``; resolving by name (rather
# than importing each module and touching its globals) is sufficient and
# matches how every call site in the tree actually spells the literal.
_KNOWN_POLICY_CONSTANTS = {
    "POLICY_NONE": POLICY_NONE,
    "POLICY_PROMPT_OR_YES": POLICY_PROMPT_OR_YES,
    "POLICY_CONFIRM_TARGET": POLICY_CONFIRM_TARGET,
    "POLICY_YES_ALWAYS": POLICY_YES_ALWAYS,
}
_KNOWN_POLICY_VALUES = set(_KNOWN_POLICY_CONSTANTS.values())


def _resolve_policy_literal(node: ast.expr) -> str | None:
    """Return the statically-known policy string a ``policy=`` node spells.

    ``None`` means the expression is not a bare ``POLICY_*`` name or a
    matching string literal -- i.e. it is computed at runtime (from a
    variable, a manifest lookup, ...) and this static check cannot see
    through it.
    """
    if isinstance(node, ast.Name) and node.id in _KNOWN_POLICY_CONSTANTS:
        return _KNOWN_POLICY_CONSTANTS[node.id]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value if node.value in _KNOWN_POLICY_VALUES else None
    return None


def _unconditional_literal_policies(source: str) -> set[str]:
    """Policies from ``enforce_confirmation`` calls not nested inside an ``if``.

    Walks the function body directly (not via a generic ``ast.walk``, which
    cannot tell an ``If``-nested node from a top-level one) so a call guarding
    one documented sub-case does not stand in for the command's baseline
    policy. Only calls whose ``policy=`` is a resolvable literal contribute;
    a dynamically-computed policy (``policy=policy``, a manifest lookup, ...)
    is silently ignored here -- those handlers are manifest-driven already
    and are exercised by a behavioral test instead.
    """
    tree = ast.parse(textwrap.dedent(source))
    policies: set[str] = set()

    def walk(node: ast.AST, *, inside_if: bool) -> None:
        for child in ast.iter_child_nodes(node):
            child_inside_if = inside_if or isinstance(child, ast.If)
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "enforce_confirmation"
                and not inside_if
            ):
                policy_kwarg = next((kw for kw in child.keywords if kw.arg == "policy"), None)
                if policy_kwarg is not None:
                    resolved = _resolve_policy_literal(policy_kwarg.value)
                    if resolved is not None:
                        policies.add(resolved)
            walk(child, inside_if=child_inside_if)

    walk(tree, inside_if=False)
    return policies


def _policies_for_handler(handler: Callable[..., Any]) -> set[str]:
    """``_unconditional_literal_policies`` for one handler, or empty if its
    source is unavailable (builtins, C extensions -- not expected here, but
    getsource can raise for either)."""
    try:
        source = inspect.getsource(handler)
    except OSError:  # pragma: no cover - no source available
        return set()
    except TypeError:  # pragma: no cover - no source available
        return set()
    return _unconditional_literal_policies(source)


def test_runtime_confirmation_gate_matches_manifest_for_every_command() -> None:
    records = {r["command_id"]: r for r in load_commands() if r.get("disposition") != "alias"}

    # Cache per-function-object: two command ids can share one handler
    # (``view_export_specialized``, ``generated_dashboard``), and getting
    # source + parsing it is the expensive part.
    source_cache: dict[Callable[..., Any], set[str]] = {}
    offenders: list[str] = []

    for command_id, record in records.items():
        handler = HANDLERS.get(command_id)
        if handler is None:  # not_implemented leaf, or a bespoke Typer command
            continue
        manifest_policy = record.get("confirmation")
        if not manifest_policy:  # pragma: no cover - covered by test_parity_manifest
            continue

        if handler not in source_cache:
            source_cache[handler] = _policies_for_handler(handler)
        literals = source_cache[handler]

        if not literals:
            # No unconditional literal enforce_confirmation call: either the
            # handler truly has no baseline gate (fine -- nothing to check),
            # or it enforces one dynamically/through a helper this scan does
            # not chase (also fine -- not this test's claim to make).
            continue
        if manifest_policy not in literals:
            offenders.append(
                f"{command_id}: manifest confirmation={manifest_policy!r} not in the "
                f"unconditional literal polic{'y' if len(literals) == 1 else 'ies'} handler "
                f"{handler.__qualname__} enforces: {sorted(literals)}"
            )

    assert not offenders, "runtime/manifest confirmation drift:\n" + "\n".join(offenders)


if __name__ == "__main__":
    test_runtime_confirmation_gate_matches_manifest_for_every_command()
    print("ok")
