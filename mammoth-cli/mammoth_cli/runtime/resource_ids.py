"""One documented id key per resource, at the top level of a create or write result.

The API names a new resource's id differently per endpoint (``id``, ``connection_key``,
``identity_key``), and a job that produced a resource carries it nested as
``response.dataset_id``. A script then saved the whole reply as the id. This is the single
place that fixes it: a result that made a resource gets ``<resource>_id`` at the top level,
copied from wherever the reply keeps it. The original keys stay for compatibility, an id the
result already carries at the top level is never replaced, and nothing is invented when no
id is found.

The resource each create command makes is named in :data:`CREATE_RESOURCES`, one reviewed entry
per command (``dataset create`` -> ``dataset_id``, ``connector connection create`` ->
``connection_id``), or ``None`` when the reply carries no id of a resource it made (a job
handle, a token, a list of ids). The noun in the command id is not trusted: ``view variants
create`` makes views, not ``variants``. The bare ``id`` key is read only where an entry says
it is that resource's. Every object ``meta.opens`` says the write made is added as well, so a
waited upload or export that produced a dataset reports ``dataset_id`` too.
``job wait`` and ``job get`` lift the ``dataset_id``, ``view_id`` and ``dashboard_id`` their
job's ``response`` or ``result`` holds.
"""

from __future__ import annotations

from typing import Any, NamedTuple

#: Verbs whose command makes a new resource; a command id may carry a suffix (``create-blank``).
_CREATE_VERBS = ("create", "duplicate", "copy")
#: Other keys the API uses for a resource's id, by resource, tried after ``<resource>_id``.
_ID_ALIASES: dict[str, tuple[str, ...]] = {"connection": ("connection_key", "identity_key")}
#: Keys that hold a job's output, searched one level down.
_NESTED_KEYS = ("response", "result")
#: Commands that report a finished job, and the resources whose ids they lift from it.
JOB_COMMANDS = frozenset({"job.wait", "job.get"})
JOB_RESOURCES = ("dataset", "view", "dashboard")
_ID_SUFFIX = "_id"


def is_create_command(command_id: str) -> bool:
    """Whether the command makes a new resource, by its verb.

    Args:
        command_id: The dotted command id.

    Returns:
        True for ``create``, ``create-*``, ``duplicate`` and ``copy`` commands.
    """
    verb = command_id.rsplit(".", 1)[-1]
    return any(verb == name or verb.startswith(f"{name}-") for name in _CREATE_VERBS)


class Created(NamedTuple):
    """A resource a create command makes, and how its id may be read from the reply."""

    resource: str
    #: Whether the reply's bare ``id`` is this resource's id (only where that is known).
    plain_id: bool = False


#: Every create-type command (see :func:`is_create_command`) and the resource it makes, or None
#: when its reply holds no id of a resource it made: a job handle (``project copy``,
#: ``view export create``, ``support subscription create``), a token or secret, a list of
#: ids (``view variants create`` answers with ``view_ids``), or a reply nobody has verified.
#: ``plain_id`` is set only where the reply's ``id`` is known to be the new resource's.
CREATE_RESOURCES: dict[str, Created | None] = {
    "agent.access.request.create": Created("access_request"),
    "annotation.create": Created("annotation"),
    "automation.create": Created("automation"),
    "batch.create": Created("batch"),
    "batch.create-spec": Created("batch"),
    "billing.stripe.create": Created("subscription"),
    "client-app.create": None,
    "collection.create": Created("collection", plain_id=True),
    "connector.connection.create": Created("connection"),
    "connector.draft.create": Created("draft"),
    "connector.ds-config.create": None,
    "dashboard.chart-type.create": Created("chart_type"),
    "dashboard.context.create": None,
    "dashboard.create-blank": Created("dashboard"),
    "dashboard.duplicate": Created("dashboard", plain_id=True),
    "dashboard.embed.preview-token.create": None,
    "dashboard.live-chart.create": None,
    "dashboard.qa.comment.create": None,
    "dashboard.qa.session.create": None,
    "dashboard.signature.create": None,
    "dashboard.style.custom.create": None,
    "dashboard.template.create": None,
    "dataset.create": Created("dataset"),
    "dataset.create-from-pdf": Created("dataset"),
    "external-key.create": None,
    "folder.create": Created("folder", plain_id=True),
    "parameter.create": Created("parameter"),
    "parameter.duplicate": Created("parameter"),
    "parameter.group.create": Created("parameter_group"),
    "project.copy": None,
    "project.create": Created("project", plain_id=True),
    "schedule.create": Created("schedule"),
    "snippet.create": Created("snippet"),
    "snippet.duplicate": Created("snippet"),
    "support.connector-profile.create": Created("connector_profile"),
    "support.connector.create": Created("connector"),
    "support.deal.create": Created("deal", plain_id=True),
    "support.feature-profile.create": Created("feature_profile"),
    "support.feature.create": Created("feature"),
    "support.partner.create": Created("partner", plain_id=True),
    "support.plan.create": Created("plan"),
    "support.plan.storage-option.create": None,
    "support.subscription.create": None,
    "support.workspace.create": Created("workspace"),
    "template.create": Created("template"),
    "token.create": None,
    "view.checkpoint.create": Created("checkpoint"),
    "view.conditional-format.create": None,
    "view.create": Created("view"),
    "view.data-check.create": Created("data_check"),
    "view.derivative.create": Created("derivative"),
    "view.export.create": None,
    "view.transform.copy-columns": None,
    "view.variants.create": None,
    "webhook.create": Created("webhook"),
    "workflow.create": Created("workflow"),
    "workflow.duplicate": Created("workflow"),
    "workspace.create": Created("workspace"),
    "workspace.oauth-client.create": None,
}


def resource_name(command_id: str) -> str | None:
    """The resource a create command makes, from :data:`CREATE_RESOURCES`.

    Args:
        command_id: The dotted command id, such as ``connector.connection.create``.

    Returns:
        ``connection`` for that example, or None when the command makes no resource with an
        id in its reply or is not listed.
    """
    created = CREATE_RESOURCES.get(command_id)
    return created.resource if created else None


def id_key(resource: str) -> str:
    """The documented top-level key for a resource's id.

    Args:
        resource: The resource noun in snake case.

    Returns:
        ``<resource>_id``.
    """
    return f"{resource}{_ID_SUFFIX}"


def _usable(value: Any) -> bool:
    """Whether *value* can be an id: a non-bool int or a non-empty string."""
    if isinstance(value, bool):
        return False
    return isinstance(value, int) or (isinstance(value, str) and value != "")


def _find(data: dict[str, Any], resource: str, *, plain_id: bool) -> Any:
    """The id of *resource* in a reply: its own key, an alias, a nested copy, else ``id``."""
    names = (id_key(resource), *_ID_ALIASES.get(resource, ()))
    for container in (data, *(data.get(nested) for nested in _NESTED_KEYS)):
        if isinstance(container, dict):
            for name in names:
                if _usable(container.get(name)):
                    return container[name]
    if plain_id and _usable(data.get("id")):
        return data["id"]
    return None


def _made_resources(command_id: str, meta: dict[str, Any]) -> list[str]:
    """The resources a create command, or its ``meta.opens``, says were made."""
    made = [name] if (name := resource_name(command_id)) else []
    for opened in meta.get("opens") or []:
        if isinstance(opened, dict) and opened.get("created") and opened.get("kind"):
            made.append(str(opened["kind"]).replace("-", "_"))
    return list(dict.fromkeys(made))


def with_resource_ids(command_id: str, data: Any, meta: dict[str, Any]) -> Any:
    """*data* with ``<resource>_id`` at the top level for each resource the call made.

    Args:
        command_id: The dotted command id.
        data: The command's result; anything but a mapping is returned unchanged.
        meta: The call's meta, whose ``opens`` names objects the write made.

    Returns:
        The result with the documented id keys added where the reply holds the id under
        another name or nested, or ``data`` itself when nothing needs adding.
    """
    if not isinstance(data, dict):
        return data
    if command_id in JOB_COMMANDS:
        # A job's own ``id`` is the job's, so only the ``<resource>_id`` keys are lifted.
        wanted = [(name, False) for name in JOB_RESOURCES]
    else:
        created = CREATE_RESOURCES.get(command_id)
        own = created.resource if created and created.plain_id else None
        wanted = [(name, name == own) for name in _made_resources(command_id, meta)]
    added: dict[str, Any] = {}
    for resource, plain_id in wanted:
        key = id_key(resource)
        if _usable(data.get(key)):
            continue
        found = _find(data, resource, plain_id=plain_id)
        if found is not None:
            added[key] = found
    return {**data, **added} if added else data
