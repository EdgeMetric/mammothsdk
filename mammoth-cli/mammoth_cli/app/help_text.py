"""Help text: group descriptions, one-line command summaries and command help pages."""

from __future__ import annotations

import importlib
import inspect
import json
import re
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from mammoth_cli.commands import BESPOKE
from mammoth_cli.commands.registry import HANDLERS
from mammoth_cli.manifest.loader import command_by_id

if TYPE_CHECKING:
    pass


# Root help is the first piece of discovery most people (and agents) see.  The
# command tree itself remains manifest-driven; these labels only organize the
# existing top-level families into a small set of tasks rather than a flat list
# of several dozen nouns.
_GROUP_DESCRIPTIONS = {
    "activity": "Inspect workspace activity and audit history.",
    "addon": "Manage workspace add-ons.",
    "agent": "Work with Mammoth agent sessions, the changes a chat made, and its runs.",
    "ai": "Generate AI-assisted expressions and conditions.",
    "annotation": "Manage annotations on Mammoth resources.",
    "auth": "Sign in, sign out, and inspect credentials.",
    "automation": "Create and manage automations.",
    "batch": "Run and inspect batch operations.",
    "billing": "Manage billing and hosted checkout flows.",
    "browse": "Browse projects and workspace resources.",
    "capability": "Discover API operation support and policies.",
    "client-app": (
        "Manage the workspace's API keys (client apps): key + secret credentials "
        "for scripts and integrations."
    ),
    "token": "Create, list, and revoke long-lived API keys (aliases of client-app).",
    "collection": "Group dashboards into a collection and share the set as one.",
    "completion": "Install or print shell completion.",
    "config": "Read and update local CLI configuration.",
    "connector": "Manage data connectors and connector profiles.",
    "log": "Locate and read the local run log.",
    "history": "List the writes made from this machine, undo them, and resume a stopped run.",
    "recipe": "Run a common multi-step task as one command.",
    "context": "Inspect and select the active project context.",
    "dashboard": "Build, query, and publish dashboards.",
    "dataset": "Create, inspect, and manage datasets.",
    "external-key": "Manage LLM provider keys (OpenAI, Anthropic, etc.) used by AI features.",
    "file": (
        "Upload files (file upload; a whole local directory: file upload-folder) and manage "
        "uploaded source files. An uploaded file becomes a dataset: delete it with "
        "'dataset delete'."
    ),
    "folder": (
        "Create, rename, move and delete project folders that organize datasets, views and "
        "dashboards. To upload a local directory use 'file upload-folder'."
    ),
    "job": "Inspect and wait for asynchronous jobs.",
    "notification": "Manage workspace notifications.",
    "parameter": "Manage parameters and parameter groups.",
    "project": "Create and manage projects.",
    "report": "Create and manage reports.",
    "schedule": "Manage scheduled work.",
    "schema": "Find concise command input guidance or fetch full schemas.",
    "skill": "Install and manage the Mammoth agent skill.",
    "snippet": "Manage reusable snippets.",
    "support": "Manage support and administration resources.",
    "template": "Manage templates.",
    "trash": "Inspect, restore, and remove trashed resources.",
    "user": "Manage users and account settings.",
    "view": "Transform, query, and publish data views.",
    "webhook": "Manage webhooks.",
    "workflow": "Create and manage workflows.",
    "workspace": "Manage workspace settings and members.",
}


# One line per ``agent`` subgroup, so ``mammoth agent --help`` tells them apart.
_AGENT_SUBGROUP_DESCRIPTIONS = {
    "access": "Grant, request and review access to the Mammoth agent, and its settings.",
    "action": "List and delete the changes an agent chat made.",
    "message": "Correct the request kind of a reply in an agent chat.",
    "plan": "Approve, skip or discard the plan of an agent chat, or edit its workflow proposal.",
    "run": "Inspect and control an agent's runs.",
    "session": "List, read, delete and share agent chat sessions.",
    "turn": "Control one turn of an agent chat session.",
}


# One line per nested group below the top level, so ``mammoth view --help`` tells its
# subgroups apart instead of repeating the top-level description. ``agent`` groups are above.
_SUBGROUP_DESCRIPTIONS = {
    "addon connector": "Add or remove the connector add-on.",
    "addon storage": "Add or remove the storage add-on.",
    "addon user": "Add or remove the user add-on.",
    "agent run units": "List and read the units of work inside an agent run.",
    "ai condition": "Generate a filter condition from a description.",
    "ai expression": "Generate a column expression from a description.",
    "ai retention": "Generate a data-retention condition from a description.",
    "ai sql": "Generate SQL from a description.",
    "ai suggestion": "List AI suggestions for a view.",
    "annotation comment": "Add comments to annotations.",
    "auth connected-apps": "List and revoke the apps you have authorised.",
    "billing invoice": "List and charge invoices.",
    "billing stripe": "Manage the Stripe subscription: checkout, trial, payment methods, invoices.",
    "billing stripe held-change": "Read or cancel a held plan change.",
    "billing stripe payment-method": "List, delete and default Stripe payment methods.",
    "billing stripe storage": "Set the Stripe storage tier.",
    "billing subscription": "Read and update the subscription.",
    "browse resources": "Browse workspace resources in bulk.",
    "collection dashboards": "Add dashboards to a collection or remove them.",
    "collection files": "Upload files to a collection.",
    "collection email-updates": "Read and set a collection's email updates, and send a test.",
    "collection email-updates me": "Read and set your own email updates for a collection.",
    "collection members": "Remove members from a collection.",
    "automation route": "Preview and set which automation a watched folder's file goes to.",
    "automation run-file": "Act on a file an automation run held back.",
    "connector ai": "Chat with the connector assistant to set up a connection.",
    "connector ai session": "List connector assistant sessions and their messages.",
    "connector connection": "Create, read, update and delete connector connections.",
    "connector draft": "Build a connector step by step: sources, gaps, sample, then save.",
    "connector draft source": "List a draft's sources, preview them and find join keys.",
    "connector ds-config": "Create, read, update and delete data-source configs.",
    "connector query": "Generate connector queries and check their status.",
    "context project": "Show, select or clear the active project.",
    "dashboard audience": "Read who views a dashboard and its digest.",
    "dashboard audience digest": "Read and set the audience digest of a dashboard.",
    "dashboard canvas": "Read, save and restore a dashboard canvas.",
    "dashboard chart-type": "List, create and delete the workspace's own chart types.",
    "dashboard chat": "Edit a dashboard by chat and read the chat history.",
    "dashboard chat attachment": "Upload a file to a dashboard's chat.",
    "dashboard context": "Create, review, apply and manage dashboard contexts.",
    "dashboard data": "Read the data behind a dashboard, draft or published.",
    "dashboard embed": "Manage dashboard embedding: keys, origins, tokens and usage.",
    "dashboard embed config": "Read and set the embed configuration.",
    "dashboard email-updates": "Read and set a dashboard's email updates, and send a test.",
    "dashboard email-updates me": "Read and set your own email updates for a dashboard.",
    "dashboard live-chart": "Create live charts, set their audience and see where they are used.",
    "dashboard embed key": "Rotate the embed key.",
    "dashboard embed lifetime": "Set the embed token lifetime.",
    "dashboard embed origin": "Revoke an allowed embed origin.",
    "dashboard embed preview-token": "Create an embed preview token.",
    "dashboard embed secret": "Rotate the embed secret.",
    "dashboard embed usage": "Read embed usage and its summary.",
    "dashboard engagement": "Read a dashboard's engagement and remind its viewers.",
    "dashboard exemplar": "Extract an exemplar from a dashboard.",
    "dashboard figure": "Add, describe and read the data behind dashboard figures.",
    "dashboard filter": "Add, list and remove dashboard filters.",
    "dashboard gallery": "List and read gallery dashboards.",
    "dashboard own-data": "Start, check and finish a dashboard's own-data setup.",
    "dashboard page": "Plan dashboard pages.",
    "dashboard pages": "Add pages to a dashboard.",
    "dashboard pdf": "Export a dashboard as a PDF.",
    "dashboard published": "Read, drill into and export a published dashboard.",
    "dashboard published pdf": "Export a published dashboard as a PDF.",
    "dashboard published video": "Export a published dashboard as a video.",
    "dashboard qa": "Ask questions of a dashboard and manage the Q&A sessions.",
    "dashboard qa comment": "Create and delete Q&A comments.",
    "dashboard qa session": "Create, read, fork, rename and share Q&A sessions.",
    "dashboard qa settings": "Read and set Q&A settings.",
    "dashboard rls": "Row-level security for a dashboard.",
    "dashboard rls assignment": "List and set row-level security assignments.",
    "dashboard rls column": "List the columns row-level security can use.",
    "dashboard rls value": "List the values row-level security can use.",
    "dashboard signature": "Create, list, update and delete dashboard signatures.",
    "dashboard source": "List the data sources of dashboards.",
    "dashboard style": "Manage dashboard styles: presets, tokens, custom and default.",
    "dashboard style custom": "Create, list, update and delete custom styles.",
    "dashboard style default": "Read and set the default style.",
    "dashboard style preset": "List style presets.",
    "dashboard style token": "List style tokens.",
    "dashboard suggestion": "List dashboard suggestions.",
    "dashboard tags": "List, set, rename, merge and delete dashboard tags.",
    "dashboard template": "Create, apply and manage dashboard templates.",
    "dashboard template thumbnail": "Read, set and clear a template thumbnail.",
    "dashboard templates": "Use or list pending dashboard templates.",
    "dashboard v3": "Generate v3 dashboards.",
    "dashboard video": "Export a dashboard as a video.",
    "dataset broken-rows": "List and resolve rows that failed to load.",
    "dataset definition": "List, save and remove what terms mean for a dataset.",
    "dataset from-url": "Preview a link, follow or copy a dataset made from a link, and show them.",
    "dataset file-settings": "Read, update and undo a dataset's file settings.",
    "dataset update-method": (
        "Read or set whether a new file replaces a dataset's rows or adds to them."
    ),
    "dataset interpretation": "Preview and confirm how a file is interpreted.",
    "dataset tool-claim": "Read an emailed Open tables link and add its tables to a project.",
    "parameter group": "Create, list, update, reorder and delete parameter groups.",
    "project checkpoint": "List project checkpoints.",
    "project data-check": "List project data checks.",
    "project memory": "Add, list and remove project memory notes.",
    "project resource-dependencies": "Update project resource dependencies.",
    "project user": "Add, update and remove project users.",
    "skill agents-md": "Install the agent instructions file.",
    "support billing": "Trials, plan changes, payment retries, refunds and cancellations.",
    "support connector": "Create, list, update and delete connectors.",
    "support connector-profile": "Manage connector profiles and their connectors.",
    "support deal": "Create, read and update deals, and move them to partners.",
    "support project-move": (
        "Follow a project move between workspaces, and purge its source copies."
    ),
    "support entitlement": "Read the entitlement registry.",
    "support feature": "Create, list, update and delete features.",
    "support feature-profile": "Manage feature profiles and their features.",
    "support identity": "List and read users across workspaces.",
    "support ownership": "Transfer ownership.",
    "support partner": "Create, read and update partners, and manage their billing and invoices.",
    "support partner client": "List, delete and detach (or cancel detaching) a partner's clients.",
    "support plan": "Manage billing plans.",
    "support plan storage-option": "Manage a plan's storage options.",
    "support subscription": "Create, read and update subscriptions.",
    "support template": "Audit, edit, import, export and publish templates.",
    "support template thumbnail": "Set and clear a template thumbnail.",
    "support user": "List, register and update users.",
    "support workspace": "Manage workspaces: create, suspend, restore and delete.",
    "support workspace invite": "Cancel or resend a workspace invite.",
    "support workspace project": (
        "List a workspace's projects, check and start moving one to another workspace."
    ),
    "support workspace user": "Add, list, remove and transfer workspace users.",
    "user avatar": "Upload or delete the avatar.",
    "user preference": "Read and update user preferences.",
    "view active-user": "List the users active on a view and mark activity.",
    "view ai": "AI profile and generated data for a view.",
    "view checkpoint": "Create, list, update and delete view checkpoints.",
    "view column": "Set how a view's columns look.",
    "view column format": "Set how columns display: date or number format.",
    "view conditional-format": "Create, list, update, replace and delete conditional formats.",
    "view data": "Read, query, aggregate, compare and profile a view's data.",
    "view data-check": "Create, list, update and delete data checks on a view.",
    "view derivative": "Create, list, update and delete derivative views.",
    "view draft": "Enter, run, submit or discard a view draft.",
    "view explore-panel": "Read and change the Explore cards of a view.",
    "view export": "Export a view to a file, database or service.",
    "view exportable-config": "Read and apply a view's exportable config.",
    "view pipeline": "Read, edit, rerun and wait on a view's pipeline.",
    "view task": "Add, list, update and delete pipeline tasks.",
    "view transform": "Add transformations to a view.",
    "view variants": "Create view variants.",
    "view version": "List, read, apply and delete view versions.",
    "workflow block": "Add and configure workflow blocks.",
    "workspace export-hosts": "Read and set the hosts exports may send data to.",
    "workspace invite": "List, resend, revoke and delete workspace invites.",
    "workspace oauth-client": "Register, list, delete and revoke OAuth client grants.",
    "workspace segment": "List and update workspace segments.",
    "workspace user": "Add, list, update and remove workspace users.",
}


def _group_description(tokens: tuple[str, ...]) -> str:
    """Return the help line for the group at ``tokens``."""
    path = " ".join(tokens)
    if path in _SUBGROUP_DESCRIPTIONS:
        return _SUBGROUP_DESCRIPTIONS[path]
    if tokens[0] == "agent" and len(tokens) > 1 and tokens[1] in _AGENT_SUBGROUP_DESCRIPTIONS:
        return _AGENT_SUBGROUP_DESCRIPTIONS[tokens[1]]
    if len(tokens) > 1:
        return f"Commands for {path}."
    return _GROUP_DESCRIPTIONS.get(tokens[0], f"Commands for {path}.")


_ROOT_HELP_PANELS = {
    "auth": "Start here",
    "context": "Start here",
    "doctor": "Start here",
    "project": "Start here",
    "how": "Discover commands",
    "capabilities": "Discover commands",
    "schema": "Discover commands",
    "capability": "Discover commands",
    "browse": "Discover commands",
    "dataset": "Work with data",
    "file": "Work with data",
    "folder": "Work with data",
    "view": "Work with data",
    "job": "Work with data",
    "batch": "Work with data",
    "dashboard": "Build and share",
    "collection": "Build and share",
    "report": "Build and share",
    "template": "Build and share",
    "snippet": "Build and share",
    "automation": "Automate and integrate",
    "schedule": "Automate and integrate",
    "webhook": "Automate and integrate",
    "workflow": "Automate and integrate",
    "connector": "Automate and integrate",
    "addon": "Manage resources",
    "agent": "Manage resources",
    "ai": "Manage resources",
    "annotation": "Manage resources",
    "billing": "Manage resources",
    "client-app": "Manage resources",
    "token": "Manage resources",
    "external-key": "Manage resources",
    "notification": "Manage resources",
    "parameter": "Manage resources",
    "trash": "Manage resources",
    "user": "Manage resources",
    "workspace": "Manage resources",
    "activity": "Manage resources",
    "support": "Manage resources",
    "config": "CLI and agent tools",
    "run": "CLI and agent tools",
    "completion": "CLI and agent tools",
    "skill": "CLI and agent tools",
    "log": "CLI and agent tools",
    "history": "CLI and agent tools",
    "recipe": "CLI and agent tools",
    "upgrade": "CLI and agent tools",
    "version": "CLI and agent tools",
}


#: One-line help for commands that share the generic ``generated_dashboard`` handler, whose
#: docstring describes the dispatch, not the command. A command listed here overrides
#: the SDK method summary :func:`_sdk_method_summary` gives every other generated command.
_GENERATED_SUMMARIES = {
    "auth.connected-apps.list": "List the apps connected to your account; each id is a grant id.",
    "auth.connected-apps.revoke": (
        "Disconnect one connected app from your account. Grant id is positional."
    ),
    "collection.active-job": (
        "Show the collection's upload job still in flight. Collection id is positional."
    ),
    "collection.activity": "Show who opened a collection and which of its dashboards get opened.",
    "collection.create": "Create a collection in the active project. Name comes from '--input'.",
    "collection.dashboards.add": (
        "Add dashboards to a collection, which gives its members access to them."
    ),
    "collection.dashboards.remove": (
        "Take one dashboard out of a collection; the dashboard is kept."
    ),
    "collection.delete": "Delete a collection and end its members' access through it.",
    "collection.files.upload": (
        "Upload local files to refresh a collection's data. Paths come from '--input'."
    ),
    "collection.for-dashboard": (
        "List the collections that hold a dashboard. Dashboard id is positional."
    ),
    "collection.get": "Get one collection with its dashboards, members and refresh setup.",
    "collection.get-by-url": "Open a collection by its share url token, as a viewer does.",
    "collection.job": "Poll one collection upload job. Collection id and job id are positional.",
    "collection.list": "List the collections you manage or were shared.",
    "collection.members.remove": "Take one person off a collection by email.",
    "collection.pipeline-changes": "Show the progress of a collection's data refresh.",
    "collection.share": "Give people access to a collection by email and send them the invite.",
    "collection.update": "Change a collection's name, description, dashboard order or tab labels.",
    "dashboard.attachment-create": (
        "Upload a local workbook as a chat attachment. File path is positional."
    ),
    "dashboard.engagement.get": (
        "Show who has opened a dashboard: reach, depth, devices and actions."
    ),
    "dashboard.engagement.person": (
        "Show one person's recent visits to a dashboard. Dashboard id and user id are positional."
    ),
    "dashboard.engagement.remind": (
        "Email the share link again to people who have not opened a dashboard."
    ),
    "dashboard.own-data.accept": (
        "Apply the proposed 'use my data' version to a board; this changes it."
    ),
    "dashboard.own-data.dismiss": (
        "Drop a board's pending 'use my data' run; the board is not changed."
    ),
    "dashboard.own-data.preview": (
        "Preview a board on your own data as proposed, without saving it."
    ),
    "dashboard.own-data.start": "Fit a template board to your own data and wait for the proposal.",
    "dashboard.own-data.status": (
        "Show a board's pending 'use my data' run; status null means none."
    ),
    "workspace.current": "Show the workspace this token acts in, and the project it is fenced to.",
    "workspace.oauth-client.delete": (
        "Delete an OAuth client registration; its grants stop working."
    ),
    "workspace.oauth-client.list": "List the workspace's registered OAuth clients (no secrets).",
    "workspace.oauth-client.revoke-grant": (
        "Revoke every grant to an OAuth client; users must authorise it again."
    ),
}


def _sdk_method_summary(command_id: str) -> str:
    """First docstring line of the SDK method a generated command calls.

    The generic ``generated_dashboard`` handler's own docstring describes the
    dispatch, so these commands take their help from the SDK method instead.
    Raises when the manifest has no such method or it has no docstring.
    """
    record = command_by_id(command_id)
    if record is None:
        raise LookupError(f"{command_id}: no manifest record")
    module_name, class_name, method_name = str(record["sdk_symbol"]).rsplit(".", 2)
    method = getattr(getattr(importlib.import_module(module_name), class_name), method_name)
    doc = inspect.getdoc(method)
    if not doc:
        raise LookupError(f"{command_id}: {record['sdk_symbol']} has no docstring")
    return doc.splitlines()[0].strip().replace("``", "'")


def live_command_summary(command_id: str) -> str | None:
    """The backing handler's docstring first line, the lead of a command's help.

    Reading it imports the handler's module, so a group listing takes it from
    the generated index (:func:`_indexed_summary`) instead.
    """
    if command_id in _GENERATED_SUMMARIES:
        return _GENERATED_SUMMARIES[command_id]
    handler = HANDLERS.get(command_id) or BESPOKE.get(command_id)
    if getattr(handler, "__name__", None) == "generated_dashboard":
        return _sdk_method_summary(command_id)
    doc = inspect.getdoc(handler) if handler is not None else None
    if not doc:
        return None
    # First non-empty line, with RST inline-code backticks flattened to plain
    # quotes so the help reads as prose rather than reStructuredText.
    return doc.strip().splitlines()[0].strip().replace("``", "'") or None


@cache
def _summary_index() -> dict[str, str]:
    """Every command's help summary, generated by ``scripts/gen_help_summaries.py``."""
    path = Path(__file__).parent.parent / "commands" / "help_summaries.json"
    return cast(dict[str, str], json.loads(path.read_text(encoding="utf-8")))


def _indexed_summary(command_id: str) -> str | None:
    return _summary_index().get(command_id)


def _sdk_backed(command_id: str) -> bool:
    """Whether the command's help comes from an SDK method's docstring."""
    from mammoth_cli.commands.registry import _TARGETS

    return _TARGETS.get(command_id, "").endswith(":generated_dashboard")


#: A line of ``--help`` a command needs that its handler's shared docstring cannot carry.
_RAW_NOTE = "Input field raw: true returns DATE values with their time, not the date alone."


_RUN_HELP_NOTE = (
    'One command per line: {"cmd": "view task list", "args": ["290"], "input": {}, '
    '"flags": {"project": 1}, "id": "a"}. cmd is the command path, args its positionals, '
    "input its --input document, flags the global flags by long name (yes, confirm, dry-run, "
    "project). Prints each line's envelope plus line, cmd and exit, then a summary; stops at "
    "the first failed line (exit = its status) unless --continue. No global --yes: a "
    "mutating line carries its own. --dry-run, --profile and --project apply to every line. "
    "FILE defaults to stdin; --continue may come before or after it. Steps: name a line "
    '("name": "up") and a later line reads its result as "{{steps.up.data.dataset.id}}" in '
    'args, input or flags; "when": {"eq": [A, B]} skips a line; "for_each": "{{steps.ls.data}}" '
    'runs it once per item ("{{item}}", "{{index}}"). JSON expressions only, no code.'
)


_HELP_NOTES = {
    "run": _RUN_HELP_NOTE,
    "view.data.get": _RAW_NOTE,
    "view.data.query": _RAW_NOTE,
    "view.export.dataset": (
        "Omit dataset_name unless the user gave one; the product default 'Result Dataset' is used."
    ),
}


#: Commands whose ``--input`` fields apply to one path only; the label says which.
_INPUT_FIELDS_LABEL = {
    "auth.login": "Input fields (--method token only; --device and --method oauth take none)",
}


def _command_help(command_id: str, record: dict[str, Any] | None) -> str | None:
    """Build a command's user-facing ``--help`` summary.

    Kept deliberately distinct from ``known_restrictions`` (internal review and
    planning notes), which used to be shown here verbatim and leaked plan-document
    prose -- e.g. "specified in plan 02's ... contract" -- into the user-facing
    ``--help``. Instead the summary is the backing handler's docstring first line
    (actionable field guidance such as "``columns``/``mapping`` required"),
    followed by the manifest's runnable ``agent_example``, which already encodes
    every required positional and ``--input`` field. ``known_restrictions``
    remains available to machines through ``schema get``.
    """
    from mammoth_cli.commands.schema import IN_PLACE_RECIPE, edits_view_in_place

    parts: list[str] = []
    # The generated index equals the handler's docstring (a unit test pins it) and reading it
    # keeps the handler's module, and the SDK it imports, out of ``--help``. A command built from
    # an SDK method reads it live: the installed SDK may be newer than the index.
    summary = None if _sdk_backed(command_id) else _indexed_summary(command_id)
    summary = summary or live_command_summary(command_id)
    if summary:
        parts.append(summary)
    if record is not None and edits_view_in_place(record):
        parts.append(IN_PLACE_RECIPE)
    if command_id in _HELP_NOTES:
        parts.append(_HELP_NOTES[command_id])
    example = (record or {}).get("agent_example")
    if example:
        parts.append(f"Example: {example}")
    fields = _help_input_fields(command_id)
    if fields:
        label = _INPUT_FIELDS_LABEL.get(command_id, "Input fields")
        parts.append(f"{label}: {fields}")
    from mammoth_cli.services.field_enums import nested_choices_help

    nested = nested_choices_help(command_id)
    if nested:
        parts.append(nested)
    from mammoth_cli.runtime.compact import COMPACT_COMMANDS, FULL_FLAG, TRIMMED_READ_COMMANDS

    if command_id in TRIMMED_READ_COMMANDS:
        parts.append(
            f"The result leaves out detail you rarely need. Pass {FULL_FLAG} for all of it."
        )
    if command_id in COMPACT_COMMANDS:
        parts.append(
            "The result is compact: ids, checks, verify and a canvas summary. "
            f"Pass {FULL_FLAG} for the complete response."
        )
    from mammoth_cli.runtime.reveal import REVEAL_COMMANDS, REVEAL_FLAG

    if command_id in REVEAL_COMMANDS:
        parts.append(
            "The credential in the result is masked. Pass "
            f"{REVEAL_FLAG} to print it; it is shown only once."
        )
    return "\n\n".join(parts) or None


def _help_input_fields(command_id: str) -> str | None:
    """One line naming the ``--input`` fields, so ``--help`` can replace ``schema get``.

    Required fields come first and are marked with ``*``; each carries its
    short type, or its enum values. Bounded to keep ``--help`` readable; the
    full contract stays behind ``schema get``.
    """
    from mammoth_cli.services.command_contract import resolve_command_contract

    try:
        contract = resolve_command_contract(command_id)
    except Exception:  # noqa: BLE001 -- help must never fail on a contract quirk
        return None
    if contract is None or not contract.accepted_fields:
        return None
    rendered: list[str] = []
    fields = sorted(contract.accepted_fields, key=lambda item: (not item.required, item.name))
    for field in fields:
        label = f"{field.name}*" if field.required else field.name
        enum = field.enum_values
        # Every value: a fixed list cut short is a guess the caller cannot check.
        kind = " | ".join(str(item) for item in enum) if enum else _short_type(field.type_name)
        rendered.append(f"{label} ({kind})" if kind else label)
        if len(rendered) == 12 and len(fields) > 12:
            rendered.append(f"... {len(fields) - 12} more (schema get {command_id})")
            break
    return ", ".join(rendered)


def _short_type(type_name: str) -> str:
    """``mammoth.condition.Condition | ...`` -> ``condition``; dotted names lose their module."""
    text = str(type_name or "")
    if "condition." in text:
        return "condition"
    # Drop each dotted module path but keep the brackets around it (``list[a.b.C]``).
    text = re.sub(r"(?:\w+\.)+(\w+)", r"\1", " | ".join(p.strip() for p in text.split("|")))
    if len(text) <= _SHORT_TYPE_MAX:
        return text
    # Cut at a word, never inside one: a clipped value ('par) reads as a real one.
    return text[: _SHORT_TYPE_MAX - 4].rsplit(" ", 1)[0] + " ..."


_SHORT_TYPE_MAX = 60


# Root ``--help`` prints each top-level leaf's help; reading it from the handler
# would import the handler's module (and its SDK dependencies). A test pins this
# table to :func:`_command_help` so it cannot drift.
_ROOT_LEAF_HELP: dict[str, str] = {
    "capabilities": (
        "List what the CLI cannot do yet, and what to do instead."
        "\n\nExample: mammoth capabilities"
    ),
    "calc": (
        "Evaluate one arithmetic expression exactly."
        "\n\nExample: mammoth calc '2063664 - 1917815'"
    ),
    "doctor": (
        "Run environment and connectivity diagnostics."
        "\n\nExample: mammoth doctor\n\nInput fields: wait (int)"
    ),
    "how": (
        "Turn a plain-language goal into an ordered recipe of commands."
        "\n\nExample: mammoth how 'refresh a dataset daily'"
    ),
    "link": (
        "Read the workspace, project, folder, dataset and view ids out of a pasted app URL."
        "\n\nExample: mammoth link https://app.mammoth.io/workspaces/1/projects/2/data/datasets"
    ),
    "resolve": (
        "Say what NAME refers to: a dataset, a view or a project, with ids and projects."
        "\n\nExample: mammoth resolve uqa-w29-ren\n\nInput fields: all_projects (bool)"
    ),
    "run": (
        "Run many commands in one process: JSON Lines of cmd, args, input and flags."
        f"\n\n{_RUN_HELP_NOTE}"
        "\n\nExample: mammoth run commands.jsonl"
    ),
    "upgrade": (
        "Upgrade the mammoth CLI to the latest (or a specified) version from PyPI."
        "\n\nExample: mammoth upgrade --yes"
    ),
    "version": "Example: mammoth version",
}
