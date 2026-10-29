"""Default ``undo`` declaration of each write command, derived at manifest build time.

The ``undo`` field of a command record says how the journal reverses the write
(``mammoth_cli.runtime.journal.compensation`` reads it):

* ``{strategy: inverse, command: ID}``: run command ``ID`` with the write's own arguments;
* ``{strategy: pipeline_version}``: apply the view's pipeline version from before the edit;
* ``{strategy: trash_created}``: move the objects the write made to the trash;
* ``{strategy: manual, command: ID}``: ``ID`` reverses it, but its arguments come from the
  result (an id the write made), so the journal does not run it and says to run it;
* ``{strategy: irreversible, reason: TEXT}``: nothing reverses it, and the text says why.

This module derives the default for every write from its mutation class, its verb and
what it reads back. A command that differs (a known inverse, a more exact reason) sets
``undo`` in ``spec/manifests/commands/<group>.yaml``, which the loader lays over the
generated record.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.runtime.journal import TRASH_COMMAND
from mammoth_cli.runtime.opens import MAKES_DATASET

INVERSE = "inverse"
PIPELINE_VERSION = "pipeline_version"
TRASH_CREATED = "trash_created"
MANUAL = "manual"
IRREVERSIBLE = "irreversible"

#: Readback id names (``<kind>_id``) of the kinds the trash takes back.
_TRASHABLE_IDS = frozenset({"dataview_id", *(f"{kind}_id" for kind in TRASH_COMMAND)})
#: A move to the trash and a restore reverse each other.
_TRASH_PAIRS = {"trash": "restore", "restore": "trash"}
_FIXED_INVERSES = {"trash.add": "trash.restore", "trash.restore": "trash.add"}
#: Verbs that make something new.
_CREATE_VERBS = frozenset({"create", "duplicate", "copy", "ensure", "from-template", "generate"})

_PERMANENT = "Deletes the {n} permanently; Mammoth keeps no copy to restore."
_REMOVED = "Removes the {n} entry; the entry is not kept, so it cannot be put back."
_OVERWRITTEN = "Overwrites the {n}; the earlier value is not kept, so it cannot be restored."
_STATE = (
    "Moves the {n} on ({verb}); the earlier state is not recorded and no command moves it back."
)
_DISCARDED = "Discards the {n} for good; no copy is kept."
_ADDED = (
    "Adds to the {n}; the journal does not know the id of the added entry, so it cannot take"
    " the entry out."
)
_CREATED = "Creates a new {n}, and no delete command exists for it; remove it in the web app."
_MESSAGE = "Sends a message into the {n}; the exchange stays in its history and cannot be unsent."
_RERUN = "Starts work on the {n}; its output replaces the earlier output, which is not kept."
_COMPUTES = (
    "Only computes or reads ({verb} on the {n}) and stores nothing in the workspace, so there"
    " is nothing to reverse."
)
_RENDERS = (
    "Writes a file or render of the {n} outside Mammoth; the produced file cannot be recalled."
)

#: Reason template by the last word of the command id.
# fmt: off
_BY_VERB: dict[str, str] = {
    **dict.fromkeys(("delete", "bulk-delete", "delete-batch", "delete-all"), _PERMANENT),
    **dict.fromkeys(("remove", "remove-batch"), _REMOVED),
    **dict.fromkeys(("discard", "clear", "cleanup", "cancel"), _DISCARDED),
    "revoke": "Revoking is final: the {n} cannot be reactivated, so issue a new one.",
    "send": "Sends a request to the {n} URL; a request that was sent cannot be recalled.",
    "send-get": "Sends a request to the {n} URL; a request that was sent cannot be recalled.",
    "attachment-create": "Uploads an attachment to the {n}; no command removes it again.",
    **dict.fromkeys(
        (
            "set", "update", "edit", "rename", "save", "replace", "reorder", "order",
            "update-batch", "bulk-update", "update-role", "type", "config", "canvas", "placement",
            "audience", "swap-data", "set-visibility", "set-request-kind", "edit-proposal",
            "move", "mark", "attach-dataset", "auth", "apply", "set-default", "digest",
            "lifetime", "refresh-token",
        ),
        _OVERWRITTEN,
    ),
    **dict.fromkeys(
        (
            "approve", "skip", "stop", "retry", "extend", "pause", "resume", "accept", "confirm",
            "dismiss", "resolve", "resolve-held", "resolve-mapping", "archive", "unarchive",
            "reactivate", "restore", "accept-invite", "save-cancel-step", "start",
            "add-anyway", "use", "undo", "save-undo", "redeem", "open",
        ),
        _STATE,
    ),
    **dict.fromkeys(("add", "add-to-context", "attach"), _ADDED),
    **dict.fromkeys(("create", "create-spec", "create-from-pdf", "upload-folder"), _CREATED),
    **dict.fromkeys(("chat", "ask", "feedback", "rate", "fork"), _MESSAGE),
    **dict.fromkeys(
        ("rerun", "rerun-all-stale", "refresh", "sample-flow", "llm-task", "sync"), _RERUN
    ),
    **dict.fromkeys(
        (
            "preview", "extract", "derive", "extract-brand", "data", "widget-data", "query",
            "plan", "test", "profile", "sample", "read-tables", "fill", "figure-intent",
            "descriptor-data", "condition", "check-expression", "generate-data", "pending",
            "multi-sheet-preview", "preview-cancel", "cancel-generation", "extract-sheets",
            "published-data-by-url", "widget-data-by-url", "submit-credentials",
            "submit-column-selection", "checkout-url", "portal-url", "hosted-page", "command",
            "multi-sheet-extract", "recheck-limits", "login", "logout", "install", "uninstall",
        ),
        _COMPUTES,
    ),
    **dict.fromkeys(("export", "download", "csv"), _RENDERS),
    "upload": "Uploads a file to the {n}; the journal lacks its id, so it cannot remove it.",
}
# fmt: on

#: Destinations an export writes to, by the last word of its command.
_DESTINATIONS = {
    "azure-blob": "Azure Blob Storage",
    "bigquery": "BigQuery",
    "elasticsearch": "Elasticsearch",
    "email": "the email recipients",
    "ftp": "an FTP server",
    "sftp": "an SFTP server",
    "managed-s3": "Mammoth's managed S3 bucket",
    "mssql": "SQL Server",
    "mysql": "MySQL",
    "onedrive": "OneDrive",
    "postgres": "PostgreSQL",
    "powerbi": "Power BI",
    "redshift": "Redshift",
    "rest": "a REST endpoint",
    "rest-fill": "a REST endpoint",
    "sharepoint": "SharePoint",
    "tableau": "Tableau",
}

#: Exact reasons for commands whose verb says too little.
_PLATFORM = "Changes billing or platform records on the server; the earlier values are not kept."
SPECIFIC_REASONS = {
    "agent.access.grant.give": (
        "Gives an agent access to data; the only way to take the grant"
        " back is `agent access grant revoke`, which is final."
    ),
    "agent.access.request.resolve": (
        "Resolves an access request and tells the requester; a"
        " resolved request cannot be reopened."
    ),
    "agent.session.delete": "Deletes the chat session and its messages for good.",
    "auth.login": (
        "Signs in on this machine; sign out with `mammoth auth logout`, which the"
        " journal does not run for you."
    ),
    "auth.logout": "Signs out on this machine; sign in again with `mammoth auth login`.",
    "billing.invoice.charge": (
        "Charges the customer's card; the payment provider has taken the"
        " money and a refund is a separate, manual step."
    ),
    "billing.stripe.cancel": (
        "Cancels the Stripe subscription; whether it can be resumed depends"
        " on the billing period, so the journal does not try."
    ),
    "billing.stripe.create": (
        "Creates the Stripe customer and subscription; the provider keeps"
        " them, and Mammoth has no command that deletes them."
    ),
    "billing.stripe.end-trial": (
        "Ends the free trial now and starts billing; a trial cannot be" " started again."
    ),
    "billing.stripe.held-change.cancel": (
        "Cancels a plan change that was waiting to apply; the"
        " change cannot be queued again from the CLI."
    ),
    "billing.stripe.payment-method.set-default": (
        "Changes the default card; the earlier default" " is not recorded."
    ),
    "billing.stripe.resume": (
        "Resumes the subscription and bills from now on; a payment taken" " is not reversed here."
    ),
    "billing.stripe.retry-payment": "Charges the card again; a payment taken is not reversed here.",
    "billing.stripe.storage.set": (
        "Changes the paid storage; the earlier amount is not recorded"
        " and a charge already made stays."
    ),
    "billing.stripe.sync": (
        "Pulls the subscription state from Stripe into Mammoth; the earlier"
        " synced state is not kept."
    ),
    "billing.subscription.update": (
        "Changes the subscription and what it costs; the earlier terms"
        " are not recorded and a charge already made stays."
    ),
    "agent.turn.rate": (
        "Records a rating on the turn; the earlier rating is overwritten and not" " kept."
    ),
    "connector.ai.submit-credentials": (
        "Hands credentials to the connector assistant's draft; the"
        " draft keeps them and the earlier ones are not recorded."
    ),
    "connector.ai.submit-column-selection": (
        "Records the column choice on the connector assistant's"
        " draft; the earlier choice is not kept."
    ),
    "connector.draft.fill": "Fills the draft's fields in place; the earlier values are not kept.",
    "connector.draft.open": "Opens the draft for editing; closing it is not a recorded step.",
    "context.project.clear": (
        "Clears the project this CLI uses by default (local state); set it"
        " again with `mammoth context project use`."
    ),
    "context.project.use": (
        "Sets the project this CLI uses by default (local state); the earlier"
        " one is not kept, so set it back with `mammoth context project use`."
    ),
    "dashboard.cancel-generation": (
        "Stops the dashboard generation job; a stopped job cannot be" " resumed."
    ),
    "completion.install": (
        "Installs the shell completion script; delete the file it names to" " remove it."
    ),
    "dashboard.action": (
        "Runs a dashboard action that reaches outside Mammoth (a message or a"
        " webhook); what it sent cannot be recalled."
    ),
    "dashboard.canvas.restore": (
        "Replaces the dashboard canvas with a saved one; the canvas it" " replaced is not kept."
    ),
    "dashboard.embed.key.rotate": (
        "Rotates the embed key; the old key is gone and embeds that" " use it stop working."
    ),
    "dashboard.embed.secret.rotate": (
        "Rotates the embed secret; the old secret is gone and embeds"
        " signed with it stop working."
    ),
    "dashboard.engagement.remind": (
        "Emails a reminder to the dashboard's audience; a sent email" " cannot be recalled."
    ),
    "dashboard.import-workbook": (
        "Imports a workbook as a new dashboard and datasets; the"
        " objects are listed in its result, and the journal does not track them."
    ),
    "dashboard.tags.delete": "Deletes the tag for good; which dashboards carried it is not kept.",
    "dashboard.tags.merge": (
        "Merges the tag into another; which dashboards carried it is not" " kept."
    ),
    "dashboard.template.thumbnail.clear": (
        "Removes the template's thumbnail; the image is not" " kept."
    ),
    "dashboard.templates.use": (
        "Builds a dashboard from a template as a job; the objects it made"
        " are in its result, and the journal does not track them."
    ),
    "dataset.broken-rows.resolve": (
        "Fixes or drops the dataset's broken rows; the rows as they" " were are not kept."
    ),
    "dataset.file-settings.undo": (
        "Is itself the undo of a file-settings update; to redo it,"
        " run `dataset file-settings update` again."
    ),
    "dataset.tool-claim.redeem": "Redeems a one-time tool claim; a claim cannot be redeemed twice.",
    "file.set-password": (
        "Sets the password used to open an encrypted file; the earlier password" " is not kept."
    ),
    "folder.trash": (
        "Moves the folder to the trash, but no `folder restore` command exists;"
        " restore it from the Trash page in the web app."
    ),
    "history.resume": (
        "Re-runs the steps that had not finished; undo each step it ran with"
        " `mammoth history undo`."
    ),
    "history.undo": "Reverses an earlier write; to redo that write, run its command again.",
    "recipe.run": (
        "Runs the recipe's commands; each of them is journaled and undone by its own"
        " entry, not as one step."
    ),
    "skill.agents-md.install": (
        "Writes the Mammoth block into the AGENTS.md file; a block already"
        " there is replaced and not kept, so delete the block by hand to remove it."
    ),
    "view.explore-panel.add-to-dashboard": (
        "Puts a copy of the explore panel on a dashboard; the"
        " journal does not know the figure it made, so remove it from the dashboard."
    ),
    "support.billing.cancel-subscription": (
        "Cancels the customer's subscription at the billing"
        " provider; it cannot be reinstated from the CLI."
    ),
    "support.billing.change-plan": (
        "Moves the workspace to another plan and bills for it; the"
        " earlier plan is not recorded and a charge already made stays."
    ),
    "support.billing.end-trial": "Ends the workspace's trial now and starts billing.",
    "support.billing.refund": (
        "The payment provider pays the refund out; Mammoth cannot take it" " back."
    ),
    "support.billing.retry-payment": (
        "Charges the card again; a payment taken is not reversed" " here."
    ),
    "support.billing.start-trial": (
        "Starts the workspace's trial; the trial clock cannot be" " rewound."
    ),
    "support.deal.opt-in": "Opts the deal in; the earlier opt-in state is not recorded.",
    "support.ownership.transfer": (
        "Transfers ownership of the workspace; the previous owner is"
        " not recorded here, so transfer it back by hand."
    ),
    "support.partner.charge-invoices": (
        "Charges the partner's open invoices; payments taken are" " not reversed here."
    ),
    "support.partner.send-payment-link": (
        "Emails the partner a payment link; a sent email cannot be" " recalled."
    ),
    "support.template.discard": "Discards the template draft for good; no copy is kept.",
    "support.template.import": (
        "Imports a template into the catalogue; nothing in the journal" " names what it added."
    ),
    "support.template.retire": (
        "Retires the template from the catalogue; the CLI has no command" " that un-retires it."
    ),
    "support.user.register": "Registers a user account; Mammoth has no command that deletes one.",
    "support.workspace.chargebee-cancelled": (
        "Marks the workspace's Chargebee subscription as"
        " cancelled; the earlier billing state is not recorded."
    ),
    "support.workspace.create": "Creates a workspace as a job; the new workspace is in its result.",
    "support.workspace.invite.cancel": (
        "Cancels an invite; a cancelled invite is dead, so send a" " new one."
    ),
    "support.workspace.invite.resend": "Emails the invite again; a sent email cannot be recalled.",
    "support.workspace.user.transfer": (
        "Moves the user's ownership to another account; the earlier" " owner is not recorded here."
    ),
    "token.create": "Issues a token; the secret is shown once, and the journal does not hold it.",
    "token.revoke": "A revoked token stays revoked; issue a new one with `mammoth token create`.",
    "upgrade": (
        "Replaces the installed CLI; install the earlier version again with the installer"
        " or pip."
    ),
    "user.avatar.delete": "Deletes the profile picture; Mammoth keeps no copy of the image.",
    "user.delete-account": "Deletes the user account for good; Mammoth keeps no copy.",
    "view.active-user.mark": "Records that the user is looking at the view; it expires by itself.",
    "view.checkpoint.delete": "Deletes the checkpoint; the saved pipeline state is not kept.",
    "view.conditional-format.delete-all": (
        "Deletes every conditional format on the view; their" " rules are not kept."
    ),
    "view.conditional-format.replace": (
        "Replaces the view's conditional formats; the earlier" " rules are not kept."
    ),
    "view.draft.command": (
        "Sends a command to the view's draft; the draft's earlier steps are" " not recorded here."
    ),
    "view.draft.discard": "Discards the draft's steps for good; they are not kept.",
    "view.task.delete": (
        "Deletes a pipeline step; its settings are not kept. Take a checkpoint"
        " (`view checkpoint create`) before editing a pipeline."
    ),
    "view.version.delete": "Deletes a pipeline version; the version is not kept.",
    "workflow.cleanup": "Removes the workflow's leftover files and runs for good.",
    "workflow.save-undo": (
        "Is itself the undo of a workflow save; to redo it, run `workflow" " save` again."
    ),
    "workspace.accept-invite": (
        "Accepts the invite and joins the workspace; leaving is a"
        " separate step the journal does not run."
    ),
    "workspace.invite.resend": "Emails the invite again; a sent email cannot be recalled.",
    "workspace.invite.revoke": (
        "A revoked invite is dead; send a new invite with `workspace user" " add`."
    ),
    "workspace.oauth-client.revoke-grant": (
        "Revokes an OAuth grant; the app must be authorised" " again by its user."
    ),
    "workspace.reactivate": (
        "Reactivates a deactivated workspace; the earlier state is not" " recorded."
    ),
}


def _split(command_id: str) -> tuple[str, str]:
    """The noun phrase and the verb of a command id: ``dashboard.qa.session.delete``."""
    parts = command_id.split(".")
    if len(parts) == 1:
        return command_id, command_id
    return " ".join(parts[:-1]).replace("-", " "), parts[-1]


def _creates_trashable(record: dict[str, Any]) -> bool:
    """Whether the write can make an object the trash takes back.

    Mirrors :func:`mammoth_cli.runtime.opens.with_opens`: the readback takes the id of a
    view, dataset, dashboard, automation or folder from the result, or the command
    makes whole datasets.
    """
    if record["command_id"] in MAKES_DATASET:
        return True
    ids = (record.get("readback") or {}).get("ids") or {}
    return any(
        name in _TRASHABLE_IDS and str(source).startswith("result.") for name, source in ids.items()
    )


def _creates_other(record: dict[str, Any]) -> bool:
    """Whether the write makes an object (it does not edit its target, and reads an id back)."""
    if record.get("edits_target") is not False:
        return False
    ids = (record.get("readback") or {}).get("ids") or {}
    return any(str(source).startswith("result.") for source in ids.values())


def _reason(record: dict[str, Any]) -> str:
    """Why nothing reverses the write, from its exact entry, its export target or its verb."""
    command_id = record["command_id"]
    if command_id in SPECIFIC_REASONS:
        return SPECIFIC_REASONS[command_id]
    noun, verb = _split(command_id)
    if command_id.startswith("view.export."):
        destination = _DESTINATIONS.get(verb)
        if destination:
            return (
                f"Writes the view's data to {destination}, outside Mammoth; it cannot be recalled."
            )
        return (
            f"Changes the export target ({verb}) outside Mammoth; the earlier setting is not kept."
        )
    if "email-updates" in command_id:
        if verb == "test":
            return "Sends a test email now; a sent email cannot be recalled."
        return "Subscribes people to email updates; mail already sent cannot be recalled."
    if verb == "share":
        return "Sends the share to the people named; Mammoth cannot withdraw a sent message."
    template = _BY_VERB.get(verb)
    if template is None and verb.startswith("add-"):
        template = _ADDED
    if template is None and verb.startswith("update-"):
        template = _OVERWRITTEN
    if template is None and record["mutation_class"] == "destructive":
        template = _PERMANENT
    if template is None:
        template = _OVERWRITTEN
    return template.format(n=noun, verb=verb.replace("-", " "))


def derive_undo(record: dict[str, Any], known: set[str]) -> dict[str, Any]:
    """The default ``undo`` declaration of a write command.

    Args:
        record: The full command record (generated, with the hand-written fields over it).
        known: Every command id.

    Returns:
        The ``undo`` mapping.
    """
    command_id = record["command_id"]
    prefix, _, verb = command_id.rpartition(".")
    inverse = _FIXED_INVERSES.get(command_id)
    if inverse is None and verb in _TRASH_PAIRS:
        inverse = f"{prefix}.{_TRASH_PAIRS[verb]}"
    if inverse in known:
        return {"strategy": INVERSE, "command": inverse}
    if record["mutation_class"] == "reversible_pipeline":
        return {"strategy": PIPELINE_VERSION}
    if _creates_trashable(record):
        return {"strategy": TRASH_CREATED}
    if command_id.startswith("view.transform.") or command_id == "view.pipeline.edit":
        # A pipeline edit that no version is read before: the earlier steps are in a version.
        return {"strategy": MANUAL, "command": "view.version.apply"}
    makes = verb == "create" or (verb in _CREATE_VERBS and _creates_other(record))
    if makes and f"{prefix}.delete" in known:
        return {"strategy": MANUAL, "command": f"{prefix}.delete"}
    return {"strategy": IRREVERSIBLE, "reason": _reason(record)}
