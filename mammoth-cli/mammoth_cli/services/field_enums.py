"""Closed vocabularies for ``str``-typed request fields the SDK checks by hand.

A field annotated ``Literal[...]`` or an ``Enum`` already reaches ``schema get`` as a JSON-Schema
``enum``.  Many SDK methods instead take a plain ``str`` and list the accepted words only in their
docstring or a module ``frozenset`` (annotation target types, parameter types, snippet languages,
...).  Left alone, ``schema get`` shows an open string and a wrong word travels to the server.

This registry names those fields once.  It feeds two places:

* ``schema get`` adds the ``enum`` to the field's JSON Schema, and
* ``--input`` validation accepts the value in any case, replaces it with the canonical spelling,
  and refuses an unknown word locally with the accepted list and a "did you mean" suggestion.

Every entry mirrors a reviewed source (``mammoth/api/*.py`` docstring or constant); the unit test
``tests/unit/services/test_field_enums.py`` walks every command schema and fails when a string
field whose name is in :data:`ENUM_LIKE_FIELD_NAMES` has neither an ``enum`` nor an entry here or
in :data:`OPEN_VOCABULARY_ALLOWLIST`.
"""

from __future__ import annotations

import difflib
from typing import Any

#: The support deal / partner billing vocabularies (``mmsubscription`` constants).
_BILLING_INTERVALS = ("monthly", "yearly", "annual")
_COLLECTION_METHODS = ("send_invoice", "charge_automatically")
_PAYMENT_TERMS = ("due_on_receipt", "net15", "net30", "net45", "net60")

#: command id -> field -> accepted spellings (canonical casing).
FIELD_ENUMS: dict[str, dict[str, tuple[str, ...]]] = {
    "agent.message.set-request-kind": {
        "request_kind": ("ask", "insight", "build", "automate", "fix")
    },
    "agent.session.set-visibility": {"visibility": ("private", "shared")},
    "agent.plan.edit-proposal": {"action": ("rename", "remove")},
    "agent.run.units.list": {"state": ("queued", "running", "done", "failed", "skipped")},
    "annotation.create": {"target_type": ("dataset", "dataview", "workflow")},
    "annotation.list": {"target_type": ("dataset", "dataview", "workflow")},
    "annotation.update": {"status": ("open", "resolved")},
    "ai.expression.generate": {"mode": ("math", "metric")},
    "ai.suggestion.list": {
        "suggestion_type": (
            "extract_text",
            "add_condition",
            "generate_task",
            "apply_ai_template",
            "dashboards",
            "derivative_fuzzy_bucket",
        )
    },
    "view.ai.profile": {"action": ("stats", "insights", "data_quality", "join_recommendation")},
    "snippet.create": {
        "language": ("sql", "expression"),
        "scope": ("project", "workspace"),
    },
    "snippet.update": {"language": ("sql", "expression")},
    "parameter.create": {
        "param_type": ("NUMERIC", "TEXT", "DATE"),
        "scope": ("project", "workspace"),
    },
    "parameter.update": {"param_type": ("NUMERIC", "TEXT", "DATE")},
    "dataset.create": {"ds_creation_type": ("clone", "cloud", "sketch", "weburl")},
    "dashboard.own-data.accept": {"choice": ("proposal", "partial", "reshape")},
    "dashboard.context.review": {"scope": ("summary", "insights", "all")},
    "project.create": {
        "project_access": ("only_me", "some_members_of_workspace", "all_members_of_workspace")
    },
    "support.workspace.user.add": {
        "role": ("workspace_member", "workspace_admin", "workspace_owner", "workspace_guest")
    },
    "workspace.invite.update-role": {
        "role": ("workspace_member", "workspace_admin", "workspace_owner", "workspace_guest")
    },
    "batch.create": {"expected_destination_c_type": ("TEXT", "NUMERIC", "DATE")},
    "agent.list": {"status": ("draft", "published", "disabled")},
    "ai.retention.condition": {"mode": ("generate", "test")},
    "dataset.interpretation.confirm": {"mode": ("interpreted", "original")},
    "project.user.add": {"role": ("project_admin", "project_analyst")},
    "view.impact": {"scope": ("task", "view")},
    "webhook.create": {"mode": ("replace", "combine")},
    "webhook.update": {"mode": ("replace", "combine")},
    **{
        f"skill.{verb}": {"scope": ("user", "project")}
        for verb in ("install", "path", "uninstall", "update")
    },
    "trash.list": {
        "type": ("dataview", "dataset", "dashboard", "automation"),
        "order": ("asc", "desc"),
    },
    "support.billing.cancel-subscription": {"when": ("now", "period_end")},
    "support.billing.change-plan": {"when": ("now", "period_end")},
    "support.deal.move-to-partner": {
        "when": ("period_end", "now"),
        "billing_interval": _BILLING_INTERVALS,
    },
    "support.deal.create": {
        "billing_interval": _BILLING_INTERVALS,
        "collection_method": _COLLECTION_METHODS,
        "payment_terms": _PAYMENT_TERMS,
        "status": ("active", "trial"),
        "billing_start": ("now", "chargebee_term_end", "date"),
    },
    "support.deal.update": {
        "billing_interval": _BILLING_INTERVALS,
        "collection_method": _COLLECTION_METHODS,
        "payment_terms": _PAYMENT_TERMS,
        "status": ("active", "trial", "cancelled"),
    },
    "support.partner.client.detach": {
        "billing_interval": _BILLING_INTERVALS,
        "collection_method": _COLLECTION_METHODS,
        "payment_terms": _PAYMENT_TERMS,
    },
    "support.partner.create": {"billing_method": _COLLECTION_METHODS},
    "support.partner.update": {"billing_method": _COLLECTION_METHODS},
    "support.workspace.archive": {"storage_class": ("GLACIER_IR", "DEEP_ARCHIVE")},
    "support.identity.list": {
        "sort": ("name", "email", "last_active"),
        "order": ("asc", "desc"),
    },
}

#: The ``view transform`` ops ``view transform batch`` takes: each one's handler only binds its
#: input and calls one View method, so the batch binds and builds exactly as the single command
#: does. The rest need their own checks (an impact read, a draft apply, a new dataset) or name a
#: column an earlier step creates. ``split`` only adds columns, as ``copy-columns`` does; ``unnest``
#: and ``pivot`` replace the view's columns, so they are the batch's last step (``BATCH_LAST_OPS``).
BATCH_OPS: tuple[str, ...] = (
    "filter",
    "sort",
    "limit-rows",
    "discard-duplicates",
    "fill-missing",
    "bulk-replace",
    "replace",
    "text",
    "substring",
    "extract-date",
    "increment-date",
    "copy-columns",
    "split",
    "unnest",
    "pivot",
)

#: The batch ops that replace the view's columns: a later step is built against columns that
#: no longer exist, so they may only be the last step.
BATCH_LAST_OPS: tuple[str, ...] = ("unnest", "pivot")

#: The server's ``data_pull_file`` values for a cloud file import; the first is the app default.
DATA_PULL_FILE_VALUES: tuple[str, ...] = ("Pull same file", "Pull next file based on name pattern")

#: Fixed lists inside an ``--input`` field (a list item's key, a nested key), which a JSON
#: Schema ``enum`` on the top-level field cannot carry. ``--help`` prints each as an
#: "Allowed values" line, and the validator that checks the path imports the same tuple, so
#: the help, the error hint and the check cannot drift apart.
NESTED_CHOICES: dict[str, dict[str, tuple[str, ...]]] = {
    "view.transform.batch": {"steps[].op": BATCH_OPS},
    "dataset.create": {"dataset_spec.query_properties.data_pull_file": DATA_PULL_FILE_VALUES},
}


def allowed_values_text(values: tuple[str, ...] | list[str]) -> str:
    """``a, b, c`` with each value quoted when it has a space."""
    return ", ".join(f"'{value}'" if " " in str(value) else str(value) for value in values)


def nested_choices_help(command_id: str) -> str | None:
    """The ``--help`` line naming each nested fixed list of ``command_id``."""
    paths = NESTED_CHOICES.get(command_id)
    if not paths:
        return None
    return "Allowed values: " + "; ".join(
        f"{path}: {allowed_values_text(values)}" for path, values in paths.items()
    )


#: Field names that look like a fixed vocabulary.  A string field with one of these names must be
#: in :data:`FIELD_ENUMS`, carry an ``enum`` already, or be listed in the allow-list below.
ENUM_LIKE_FIELD_NAMES = frozenset(
    {
        "action",
        "choice",
        "ds_creation_type",
        "expected_destination_c_type",
        "language",
        "mode",
        "order",
        "param_type",
        "project_access",
        "request_kind",
        "role",
        "scope",
        "state",
        "status",
        "suggestion_type",
        "target_type",
        "visibility",
    }
)

#: ``(command id, field)`` pairs whose value is free text or an open server vocabulary.
OPEN_VOCABULARY_ALLOWLIST: dict[tuple[str, str], str] = {
    **{
        (cid, "role"): "agent roles are served by 'agent roles' (server-defined, can grow)"
        for cid in ("agent.access.set", "agent.create", "agent.update")
    },
    ("support.workspace.user.transfer", "role"): "SDK documents no closed list for this role",
    ("support.partner.update", "status"): "partner statuses are server-defined (not listed)",
    ("notification.list", "status"): "notification statuses are not documented by the SDK",
    **{
        (cid, "status"): "status filters are server-defined; the SDK documents no closed list"
        for cid in (
            "project.checkpoint.list",
            "project.data-check.list",
            "view.checkpoint.list",
            "view.data-check.list",
            "view.pipeline.items",
            "view.pipeline.items-all",
        )
    },
}


def field_enum(command_id: str, field: str) -> tuple[str, ...] | None:
    """The accepted spellings for ``field`` of ``command_id``, when it has a closed vocabulary."""
    return FIELD_ENUMS.get(command_id, {}).get(field)


def _fold(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def match_choice(value: Any, choices: tuple[Any, ...] | list[Any]) -> tuple[Any | None, str | None]:
    """Resolve ``value`` against ``choices`` ignoring case, spaces and hyphens.

    Returns ``(canonical, None)`` on a match, else ``(None, suggestion)`` where ``suggestion`` is
    the closest accepted spelling (or ``None`` when nothing is close).
    """
    if value in choices:
        return value, None
    if not isinstance(value, str):
        return None, None
    folded = {_fold(str(choice)): choice for choice in choices if isinstance(choice, str)}
    key = _fold(value)
    if key in folded:
        return folded[key], None
    close = difflib.get_close_matches(key, list(folded), n=1, cutoff=0.6)
    return None, (str(folded[close[0]]) if close else None)


def with_enum(schema: dict[str, Any], values: tuple[str, ...]) -> dict[str, Any]:
    """Return ``schema`` with an ``enum`` on its string branch (``str`` or ``str | None``)."""
    result = dict(schema)
    if result.get("type") == "string":
        result["enum"] = list(values)
        return result
    for key in ("anyOf", "oneOf"):
        members = result.get(key)
        if isinstance(members, list):
            result[key] = [
                (
                    {**m, "enum": list(values)}
                    if isinstance(m, dict) and m.get("type") == "string" and "enum" not in m
                    else m
                )
                for m in members
            ]
    return result
