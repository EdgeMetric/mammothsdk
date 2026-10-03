"""Read-only handlers for the ``project`` command family.

Each handler receives the typed
:class:`~mammoth_cli.runtime.invocation.Invocation`, opens an authenticated
:class:`~mammoth_cli.services.protocol.MammothService`, and dispatches to the
public SDK method named by the command's reviewed manifest ``sdk_symbol``. No
handler constructs a client or reads process state directly; project ids come
from a positional argument or the resolved active project, and multi-field
input comes from the strict ``--input`` document.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from typing import Any

from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
    missing_project_error,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, resolved_project

HandlerResult = tuple[Any, dict[str, Any]]


def _symbol(invocation: Invocation) -> str:
    """Return the reviewed backing SDK symbol for this command."""
    record = command_by_id(invocation.command_id)
    if record is None or not record.get("sdk_symbol"):
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No SDK symbol is recorded for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )
    return str(record["sdk_symbol"])


def _string_positional(invocation: Invocation) -> str | None:
    """Return the first positional argument, or None if absent."""
    return invocation.extra_args[0] if invocation.extra_args else None


def _int_positional(invocation: Invocation, name: str) -> int | None:
    """Parse the first positional argument as an int, or return None if absent."""
    if not invocation.extra_args:
        return None
    raw = invocation.extra_args[0]
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _project_id(invocation: Invocation) -> int:
    """Resolve the target project id from a positional or the active project."""
    explicit = _int_positional(invocation, "project id")
    if explicit is not None:
        return explicit
    resolved = resolved_project(invocation)
    if resolved is None:
        raise missing_project_error()
    return resolved


def _require_input_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _meta(invocation: Invocation, auth_workspace_id: int, project_id: int | None) -> dict[str, Any]:
    """Build the common envelope metadata for a project command."""
    return {
        "profile": invocation.profile,
        "workspace_id": auth_workspace_id,
        "project_id": project_id,
    }


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy any of ``fields`` present in ``document`` into ``kwargs``."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def project_list(invocation: Invocation) -> HandlerResult:
    """List the caller's member projects in the active workspace, one page at a time.

    These are the projects the Mammoth UI shows. ``include_non_members: true``
    adds the other workspace projects (workspace owners and admins can read
    them but not open them); every row then carries ``member``.

    ``offset`` forwards for pagination past the server's 100-row page, the
    same as ``dataset list``; a short page's ``next`` in the response is
    empty. The server has no name filter for this route (unlike ``dataset
    list``'s discovery search), so none is exposed here.
    """
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"limit": int(document.get("limit", 100))}
    _forward_optional(document, kwargs, ("offset", "include_non_members"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def project_get(invocation: Invocation) -> HandlerResult:
    """Get one project by id (positional or active project)."""
    project_id = _project_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_pending_changes(invocation: Invocation) -> HandlerResult:
    """Report a project's pending pipeline changes."""
    project_id = _project_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_needs_attention(invocation: Invocation) -> HandlerResult:
    """List the Monitor "Needs Attention" rows with the dataset behind each view."""
    project_id = _project_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_memory_list(invocation: Invocation) -> HandlerResult:
    """List the caller's saved agent preferences for a project."""
    project_id = _project_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_memory_add(invocation: Invocation) -> HandlerResult:
    """Save one agent preference (``text`` from ``--input``) for the caller."""
    project_id = _project_id(invocation)
    text = _require_input_field(invocation.load_input(), "text")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id, text=text)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_memory_remove(invocation: Invocation) -> HandlerResult:
    """Remove the caller's saved preference at ``index`` (from ``--input``)."""
    project_id = _project_id(invocation)
    index = _require_input_field(invocation.load_input(), "index")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id, index=index)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_resource_status(invocation: Invocation) -> HandlerResult:
    """Report the status of a project's resources."""
    project_id = _project_id(invocation)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_resource_dependencies(invocation: Invocation) -> HandlerResult:
    """Report dependencies for the given resource ids in a project."""
    project_id = _project_id(invocation)
    document = invocation.load_input()
    resource_ids = _require_input_field(document, "resource_ids")
    kwargs: dict[str, Any] = {"project_id": project_id, "resource_ids": resource_ids}
    if document is not None and "is_recursive" in document:
        kwargs["is_recursive"] = document["is_recursive"]
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_resource_dependencies_update(invocation: Invocation) -> HandlerResult:
    """Apply confirmed data-sync patches to a project's resource graph."""
    project_id = _project_id(invocation)
    document = invocation.load_input()
    patches = _require_input_field(document, "patches")
    if not isinstance(patches, list) or not patches:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="'patches' must be a non-empty list.",
            exit_status=EXIT_USAGE,
        )
    targets: list[tuple[Any, Any]] = []
    for item in patches:
        if not isinstance(item, dict) or not isinstance(item.get("value"), dict):
            continue
        value = item["value"]
        targets.append((value.get("context_type"), value.get("context_id")))
    if len(targets) != len(set(targets)):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="'patches' must not repeat a resource target.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=f"update resource data-sync settings in project {project_id}",
            target=str(project_id),
        )
        data = service.call(_symbol(invocation), project_id=project_id, patches=patches)
        settled = service.wait_if_job(data)
    if isinstance(data, dict) and isinstance(settled, dict):
        data = {**data, **settled}
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_publish_credentials(invocation: Invocation) -> HandlerResult:
    """Report publish credentials for a project's ODBC endpoint."""
    project_id = _project_id(invocation)
    document = invocation.load_input()
    odbc_type = _require_input_field(document, "odbc_type")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id, odbc_type=odbc_type)
    return data, _meta(invocation, auth.workspace_id, project_id)


_CREATE_OPTIONAL = ("color", "project_access")
_UPDATE_OPTIONAL = ("name", "color")


def project_create(invocation: Invocation) -> HandlerResult:
    """Create a project. Name comes from a positional or the ``name`` field."""
    document = invocation.load_input() or {}
    name = _string_positional(invocation) or document.get("name")
    if not name:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A project name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or a 'name' input field.",
        )
    kwargs: dict[str, Any] = {"name": name}
    for field in _CREATE_OPTIONAL:
        if field in document:
            kwargs[field] = document[field]
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


_ENSURE_CREATE_SYMBOL = "mammoth.api.projects.ProjectsAPI.create"


def project_ensure(invocation: Invocation) -> HandlerResult:
    """Return the project with exactly this name, creating it when absent.

    Idempotent get-or-create for a scratch or working project (the "From
    Claude" convention: pick one project once, land every task's datasets
    there, sweep it with ``project delete``). Matching is exact and
    case-sensitive on the name; when several projects share the name the
    lowest id wins and ``duplicates`` lists the rest, so a re-run never
    creates a second one.
    """
    document = invocation.load_input() or {}
    name = _string_positional(invocation) or document.get("name")
    if not isinstance(name, str) or not name.strip():
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A project name is required.",
            exit_status=EXIT_USAGE,
            hint="Pass the name as a positional argument or a 'name' input field.",
        )
    with open_service(invocation) as (service, auth):
        # Walks every 100-row page of the projects route, so an exact-name
        # match anywhere in the workspace is found before anything is created.
        projects = [p for p in service.list_all_projects() if isinstance(p, dict)]
        same_name = sorted(
            (p for p in projects if isinstance(p, dict) and p.get("name") == name),
            key=lambda p: int(p.get("id") or 0),
        )
        if same_name:
            chosen = same_name[0]
            data: dict[str, Any] = {
                "project": chosen,
                "project_id": chosen.get("id"),
                "created": False,
                "duplicates": [p.get("id") for p in same_name[1:]],
            }
            data["active"] = _make_active_project(invocation, data["project_id"])
            return data, _meta(invocation, auth.workspace_id, chosen.get("id"))
        created = service.call(_ENSURE_CREATE_SYMBOL, name=name)
    record = created.get("project", created) if isinstance(created, dict) else {}
    project_id = record.get("id") if isinstance(record, dict) else None
    if project_id is None and isinstance(created, dict):
        project_id = created.get("project_id") or created.get("id")
    data = {
        "project": record if isinstance(record, dict) else created,
        "project_id": project_id,
        "created": True,
        "duplicates": [],
    }
    data["active"] = _make_active_project(invocation, project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _make_active_project(invocation: Invocation, project_id: Any) -> bool:
    """Save ``project_id`` as the profile's active project; True when saved.

    ``project ensure`` exists so an agent picks its working project once;
    saving it here means no later command needs ``--project``. A profile-less
    run (environment login) and an embedded call (the host's profile is not
    ours to write) have nowhere to save, and report ``active: false``.
    """
    if embedded.active() or not isinstance(project_id, int) or project_id <= 0:
        return False
    profile_name = invocation.profile or profiles.get_selected()
    existing = profiles.get_profile(profile_name)
    if existing is None:
        return False
    profiles.save_profile(
        profiles.ProfileRecord(
            name=existing.name,
            workspace_id=existing.workspace_id,
            server_prefix=existing.server_prefix,
            project_id=project_id,
        )
    )
    return True


def project_update(invocation: Invocation) -> HandlerResult:
    """Update a project's name or color from the ``--input`` document."""
    project_id = _project_id(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    for field in _UPDATE_OPTIONAL:
        if field in document:
            kwargs[field] = document[field]
    if len(kwargs) == 1:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message="Provide at least one of 'name' or 'color' to update.",
            exit_status=EXIT_USAGE,
            hint="Pass fields via --input.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_delete(invocation: Invocation) -> HandlerResult:
    """Delete one project (positional or active).

    A project delete cascades to every dataset, view, export and dashboard in
    it, so it needs ``--yes --confirm PROJECT_ID``: the caller must name the
    exact project, not just agree to "the active one".
    """
    project_id = _project_id(invocation)
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"delete project {project_id}",
        target=str(project_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_bulk_delete(invocation: Invocation) -> HandlerResult:
    """Delete several projects by id. Prompt or ``--yes`` required."""
    document = invocation.load_input()
    project_ids = _require_input_field(document, "project_ids")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"delete {len(project_ids)} projects",
        target=",".join(str(project_id) for project_id in sorted(set(project_ids))),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_ids=project_ids)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def _bulk_update_project_ids(patch_data: Any) -> list[int]:
    """Return the project ids a ``ProjectsPatch`` body targets, or raise usage.

    The release contract is ``{"patches": [{"op", "path": "role", "value":
    [{"project_id", ...}]}]}``: every value item names the project it changes,
    so the CLI refuses a body that would not name its targets.
    """
    patches = patch_data.get("patches") if isinstance(patch_data, dict) else None
    targets: list[int] = []
    if isinstance(patches, list) and patches:
        for op in patches:
            values = op.get("value") if isinstance(op, dict) else None
            if not isinstance(values, list) or not values:
                targets = []
                break
            for item in values:
                project_id = item.get("project_id") if isinstance(item, dict) else None
                if not isinstance(project_id, int) or isinstance(project_id, bool):
                    targets = []
                    break
                targets.append(project_id)
            else:
                continue
            break
    if not targets:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=(
                "patch_data must be a ProjectsPatch body whose every value item names a project_id."
            ),
            exit_status=EXIT_USAGE,
            hint=(
                'Shape: {"patch_data": {"patches": [{"op": "add", "path": "role", "value": '
                '[{"project_id": 41, "user_roles": [{"user_id": 3, "role": "project_admin"}]}]}]}}.'
            ),
        )
    return sorted(set(targets))


def project_bulk_update(invocation: Invocation) -> HandlerResult:
    """Apply a role patch across named projects. High-impact: ``--yes --confirm WS``."""
    document = invocation.load_input()
    patch_data = _require_input_field(document, "patch_data")
    project_ids = _bulk_update_project_ids(patch_data)
    with open_service(invocation) as (service, auth):
        enforce_confirmation(
            invocation,
            policy=POLICY_CONFIRM_TARGET,
            action=(
                f"bulk-update roles in projects {', '.join(str(p) for p in project_ids)} "
                f"of workspace {auth.workspace_id}"
            ),
            target=str(auth.workspace_id),
        )
        data = service.call(_symbol(invocation), patch_data=patch_data)
    return data, _meta(invocation, auth.workspace_id, resolved_project(invocation))


def project_sample_flow(invocation: Invocation) -> HandlerResult:
    """Create a sample flow in a project (positional or active)."""
    project_id = _project_id(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    if "label_resource_id" in document:
        kwargs["label_resource_id"] = document["label_resource_id"]
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


_LIST_FILTER_OPTIONAL = ("fields", "sort", "dataview_id", "sequence", "status")


def _list_with_filters(invocation: Invocation) -> HandlerResult:
    """Shared handler for a project-scoped list with the standard filters."""
    project_id = _project_id(invocation)
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"project_id": project_id}
    for field in _LIST_FILTER_OPTIONAL:
        if field in document:
            kwargs[field] = document[field]
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_checkpoint_list(invocation: Invocation) -> HandlerResult:
    """List a project's checkpoints, with optional filters from ``--input``."""
    return _list_with_filters(invocation)


def project_data_check_list(invocation: Invocation) -> HandlerResult:
    """List a project's data checks, with optional filters from ``--input``."""
    return _list_with_filters(invocation)


def project_user_add(invocation: Invocation) -> HandlerResult:
    """Add users to a project. High-impact: ``--yes --confirm PROJECT_ID``."""
    project_id = _project_id(invocation)
    document = invocation.load_input()
    user_ids = _require_input_field(document, "user_ids")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"add users to project {project_id}",
        target=str(project_id),
    )
    kwargs: dict[str, Any] = {"project_id": project_id, "user_ids": user_ids}
    assert document is not None
    if "role" in document:
        kwargs["role"] = document["role"]
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_user_remove(invocation: Invocation) -> HandlerResult:
    """Remove users from a project. High-impact: ``--yes --confirm PROJECT_ID``."""
    project_id = _project_id(invocation)
    document = invocation.load_input()
    user_ids = _require_input_field(document, "user_ids")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"remove users from project {project_id}",
        target=str(project_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), project_id=project_id, user_ids=user_ids)
    return data, _meta(invocation, auth.workspace_id, project_id)


def project_user_update(invocation: Invocation) -> HandlerResult:
    """Update a project member's role (``role`` required; ``user_id``/``invite_id``)."""
    project_id = _project_id(invocation)
    document = invocation.load_input()
    role = _require_input_field(document, "role")
    kwargs: dict[str, Any] = {"project_id": project_id, "role": role}
    assert document is not None
    target_count = sum(
        field in document and document[field] is not None for field in ("user_id", "invite_id")
    )
    if target_count != 1:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="Exactly one of 'user_id' or 'invite_id' is required.",
            exit_status=EXIT_USAGE,
        )
    for field in ("user_id", "invite_id"):
        if field in document:
            kwargs[field] = document[field]
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"update membership role in project {project_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


_DATASETS_LIST_SYMBOL = "mammoth.api.datasets.DatasetsAPI.list_all"
_DASHBOARDS_LIST_SYMBOL = "mammoth.api.dashboards.DashboardsAPI.list"


def _report_line(where: str, warning: dict[str, Any]) -> str:
    column = warning.get("column")
    subject = f"{where}, column {column}" if column else where
    return f"{subject}: {warning.get('issue')}. {warning.get('detail', '')}".strip()


def _scoped_id(invocation: Invocation, name: str) -> int | None:
    """The integer positional ``name`` (``dataset_id``, ``view_id``), or None if omitted."""
    raw = invocation.positional(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name.replace('_', ' ')} argument '{raw}' is not an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _scoped_dataset_id(invocation: Invocation) -> int | None:
    """The DATASET_ID that narrows ``project check`` to one dataset, or None."""
    return _scoped_id(invocation, "dataset_id")


def _scoped_view_id(invocation: Invocation, dataset_id: int | None) -> int | None:
    """The VIEW_ID that picks which view of DATASET_ID ``project check`` reads, or None."""
    view_id = _scoped_id(invocation, "view_id")
    if view_id is not None and dataset_id is None:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="A view id needs its dataset: project check PROJECT_ID DATASET_ID VIEW_ID.",
            exit_status=EXIT_USAGE,
        )
    return view_id


def _datasets_to_check(service: Any, project_id: int, scoped: int | None) -> list[Any]:
    """Every dataset of the project, or only the named one -- never a walk when scoped."""
    if scoped is not None:
        return [{"id": scoped, "name": f"dataset {scoped}"}]
    listing = service.call(_DATASETS_LIST_SYMBOL, project_id=project_id, sort="(created_at:desc)")
    return listing.get("datasets", []) if isinstance(listing, dict) else []


_CHECK_WORKERS = 2
#: Most recent datasets and dashboards one ``project check`` reads (several requests each).
_CHECK_MAX_DATASETS = 20
_CHECK_MAX_DASHBOARDS = 10


def _not_checked_line(kind: str, omitted: int, how: str) -> str:
    """The report line for resources left unchecked by the cap, and how to reach them."""
    return f"{omitted} more {kind} were not checked (only the most recent were); {how}"


def _in_worker[T](invocation: Invocation, work: Callable[[Any, Any], T]) -> T:
    """Run ``work(service, auth)`` on a service of its own, without a spinner.

    One service drives one event loop, which a second thread cannot enter
    while the first is inside it, so each worker thread opens its own.
    """
    with open_service(replace(invocation, no_progress=True)) as (service, auth):
        return work(service, auth)


def _map_checks[T](
    invocation: Invocation,
    service: Any,
    auth: Any,
    items: list[Any],
    work: Callable[[Any, Any, Any], T],
) -> list[T]:
    """``work(service, auth, item)`` for each item, several at once, in item order.

    ``project check`` made three to five sequential calls per resource, so a
    project of a few dozen took minutes (RT18-05: 6+ min). One item, or none,
    uses the service already open.
    """
    if len(items) <= 1:
        return [work(service, auth, item) for item in items]
    with ThreadPoolExecutor(max_workers=min(_CHECK_WORKERS, len(items))) as pool:
        return embedded.pool_map(
            pool,
            lambda item: _in_worker(invocation, lambda svc, ath: work(svc, ath, item)),
            items,
        )


def _preview_dataset(
    service: Any, _auth: Any, args: tuple[Any, int | None, int | None]
) -> dict[str, Any]:
    from mammoth_cli.commands.view import upload_preview

    dataset, project_id, view_id = args
    dataset_id = dataset.get("id") if isinstance(dataset, dict) else None
    if not isinstance(dataset_id, int):
        return {"preview_error": "dataset entry has no integer id"}
    return upload_preview(service, dataset_id, project_id, view_id)


def _check_dashboard(invocation: Invocation) -> Callable[[Any, Any, Any], dict[str, Any]]:
    from mammoth_cli.commands.dashboard import _with_deliverable_check

    def _check(service: Any, auth: Any, board: Any) -> dict[str, Any]:
        dashboard_id = board.get("id") if isinstance(board, dict) else None
        if not isinstance(dashboard_id, int):
            return {}
        done = _with_deliverable_check(
            invocation, service, auth, {"dashboard_id": dashboard_id}, {"id": dashboard_id}
        )
        check = done.get("deliverable_check") if isinstance(done, dict) else None
        return {"id": dashboard_id, "title": board.get("title"), "check": check or {}}

    return _check


def _dataset_entry(dataset: dict[str, Any], preview: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "dataset_id": dataset.get("id"),
        "dataset_name": dataset.get("name"),
        "view_id": preview["view_id"],
        "view_name": preview.get("view_name"),
        "row_count": preview.get("row_count"),
        "column_warnings": preview.get("column_warnings", []),
        "column_checks": preview["column_checks"],
    }
    for key in ("before_dashboard", "other_views"):
        if key in preview:
            entry[key] = preview[key]
    return entry


def _other_views_line(dataset: dict[str, Any], preview: dict[str, Any]) -> str:
    # Only the first (most recent) view is previewed and checked. Say so
    # explicitly instead of letting silence read as "this is the only view" --
    # which view to change is the user's call unless they already named one.
    other_views = preview["other_views"]
    other_desc = ", ".join(f"{v['id']} ({v.get('name')})" for v in other_views)
    return (
        f"dataset {dataset.get('name')} (id {dataset.get('id')}) has "
        f"{len(other_views) + 1} views; only view {preview['view_id']} was "
        f"checked (others: {other_desc}). Which view to change is the "
        "user's pick unless they named one."
    )


def _dataset_status(dataset: dict[str, Any], preview: dict[str, Any]) -> dict[str, Any]:
    """One status row: freshness (is the data current?) apart from data quality."""
    row: dict[str, Any] = {"kind": "dataset", "dataset_id": dataset.get("id")}
    row["name"] = dataset.get("name")
    if "preview_error" in preview:
        return {**row, "error": preview["preview_error"]}
    return {
        **row,
        "view_id": preview["view_id"],
        "view_name": preview.get("view_name"),
        "freshness": preview.get("freshness", {"state": "unknown"}),
        "data_quality": {
            "warnings": len(preview.get("column_warnings", [])),
            "rows_checked": preview["column_checks"]["rows_checked"],
        },
    }


def _dashboard_status(result: dict[str, Any]) -> dict[str, Any]:
    check = result["check"]
    row: dict[str, Any] = {"kind": "dashboard", "id": result["id"], "title": result["title"]}
    if check.get("checked") is False:
        return {**row, "error": check.get("error", "the dashboard could not be checked")}
    return {**row, "data_quality": {"warnings": len(check.get("warnings", []))}}


def _stale_lines(statuses: list[dict[str, Any]]) -> list[str]:
    return [
        f"view {row['view_id']} ({row['name']}): data is {row['freshness']['state']}"
        " (freshness, not data quality); its numbers may not be current."
        for row in statuses
        if row.get("freshness", {}).get("state") in ("running", "out_of_sync")
    ]


def project_check(invocation: Invocation) -> HandlerResult:
    """List what a report on this project must still account for.

    Read-only local composite, run before reporting: for each dataset, the
    first view's ``column_warnings`` and ``before_dashboard``; for each
    dashboard, its ``deliverable_check``. ``to_report`` flattens them into
    one line per finding; ``resources`` has one status row per dataset and
    dashboard (freshness apart from data quality, or the error that stopped
    its check). Resources are checked several at once. Given a DATASET_ID it
    reads only that dataset's first view (no dataset list, no dashboards);
    given VIEW_ID as well it reads that view instead. Every status row names
    the ``view_id`` and ``view_name`` it checked.
    Cold-agent evals (2.0.41) left one column's blanks undecided in every
    run, because the warning sat in an earlier result.
    """
    started = time.monotonic()
    project_id = _project_id(invocation)
    views: list[dict[str, Any]] = []
    dashboards: list[dict[str, Any]] = []
    to_report: list[str] = []
    checked: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []
    scoped_dataset = _scoped_dataset_id(invocation)
    scoped_view = _scoped_view_id(invocation, scoped_dataset)
    with open_service(invocation) as (service, auth):
        every_dataset = _datasets_to_check(service, project_id, scoped_dataset)
        datasets = every_dataset[:_CHECK_MAX_DATASETS]
        if len(every_dataset) > len(datasets):
            to_report.append(
                _not_checked_line(
                    "datasets",
                    len(every_dataset) - len(datasets),
                    "run 'project check DATASET_ID' for a specific one.",
                )
            )
        previews = _map_checks(
            invocation,
            service,
            auth,
            [(dataset, project_id, scoped_view) for dataset in datasets],
            _preview_dataset,
        )
        for dataset, preview in zip(datasets, previews, strict=True):
            statuses.append(_dataset_status(dataset if isinstance(dataset, dict) else {}, preview))
            if "preview_error" in preview:
                dataset_id = dataset.get("id") if isinstance(dataset, dict) else None
                skipped.append(
                    {
                        "dataset_id": dataset_id if isinstance(dataset_id, int) else None,
                        "reason": preview["preview_error"],
                    }
                )
                continue
            entry = _dataset_entry(dataset, preview)
            if "other_views" in preview and scoped_view is None:
                to_report.append(_other_views_line(dataset, preview))
            views.append(entry)
            checked.append(
                {
                    "dataset_id": dataset["id"],
                    "view_id": preview["view_id"],
                    "view_name": preview.get("view_name"),
                    "rows_checked": preview["column_checks"]["rows_checked"],
                }
            )
            where = f"view {preview['view_id']} ({dataset.get('name')})"
            to_report += [_report_line(where, w) for w in entry["column_warnings"]]
        to_report += _stale_lines(statuses)
        boards = (
            [] if scoped_dataset else service.call(_DASHBOARDS_LIST_SYMBOL, project_id=project_id)
        )
        every_board = [b for b in boards if isinstance(b, dict)] if isinstance(boards, list) else []
        if len(every_board) > _CHECK_MAX_DASHBOARDS:
            to_report.append(
                _not_checked_line(
                    "dashboards",
                    len(every_board) - _CHECK_MAX_DASHBOARDS,
                    "check one with 'dashboard get DASHBOARD_ID'.",
                )
            )
        results = _map_checks(
            invocation,
            service,
            auth,
            every_board[:_CHECK_MAX_DASHBOARDS],
            _check_dashboard(invocation),
        )
        for result in filter(None, results):
            warnings = result["check"].get("warnings", [])
            dashboards.append({"id": result["id"], "title": result["title"], "warnings": warnings})
            statuses.append(_dashboard_status(result))
            to_report += [_report_line(f"dashboard {result['id']}", w) for w in warnings]
        meta = _meta(invocation, auth.workspace_id, project_id)
    return {
        "project_id": project_id,
        "resources": statuses,
        "views": views,
        "dashboards": dashboards,
        "checked": checked,
        "skipped": skipped,
        **(
            {
                "scope": {
                    "dataset_id": scoped_dataset,
                    **({"view_id": scoped_view} if scoped_view else {}),
                    "dashboards": "not checked",
                }
            }
            if scoped_dataset
            else {}
        ),
        "to_report": to_report,
        **({} if to_report else {"note": "Nothing open in the views or dashboards."}),
        "elapsed_seconds": round(time.monotonic() - started, 1),
    }, meta
