"""Handlers for the ``dataset`` command family (project-scoped).

Every dataset operation runs inside a resolved project: the project id comes
from ``--project`` or the active project, and dataset ids come from a
positional argument or the strict ``--input`` document. Handlers dispatch
through the generic :meth:`~mammoth_cli.services.protocol.MammothService.call`
seam to the public SDK method named by the command's reviewed manifest
``sdk_symbol``.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    CODE_UNSUPPORTED_CONTRACT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    POLICY_PROMPT_OR_YES,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.new_data import with_file_upload_path
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services.listing import (
    DATASET_ROW_FIELDS,
    ambiguity_note,
    dataset_summary,
    fit_budget,
    name_hit,
    search_page,
    source_of,
)

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


def _require_int_positional(invocation: Invocation, name: str) -> int:
    """Parse the first positional argument as an int, or raise ``missing_argument``."""
    value = _int_positional(invocation, name)
    if value is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return value


def _require_int_positional_at(invocation: Invocation, index: int, name: str) -> int:
    """Parse a positional integer at an explicit index."""
    if len(invocation.extra_args) <= index:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
        )
    try:
        return int(invocation.extra_args[index])
    except ValueError as exc:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"The {name} argument must be an integer.",
            exit_status=EXIT_USAGE,
        ) from exc


def _require_field(document: dict[str, Any] | None, field: str) -> Any:
    """Return a required field from the ``--input`` document, or raise usage."""
    if document is None or field not in document:
        raise CliError(
            code=CODE_MISSING_FIELD,
            message=f"This command requires the '{field}' input field.",
            exit_status=EXIT_USAGE,
            hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
        )
    return document[field]


def _meta(invocation: Invocation, workspace_id: int, project_id: int) -> dict[str, Any]:
    """Build the common envelope metadata for a dataset command."""
    return {
        "profile": invocation.profile,
        "workspace_id": workspace_id,
        "project_id": project_id,
    }


def _forward_optional(
    document: dict[str, Any], kwargs: dict[str, Any], fields: tuple[str, ...]
) -> None:
    """Copy any of ``fields`` present in ``document`` into ``kwargs``."""
    for field in fields:
        if field in document:
            kwargs[field] = document[field]


def _require_string_positional(invocation: Invocation, name: str) -> str:
    """Return the first positional as a nonblank string, or raise ``missing_argument``."""
    if not invocation.extra_args or not str(invocation.extra_args[0]).strip():
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"This command requires a {name} argument.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {name} as a positional argument.",
        )
    return str(invocation.extra_args[0])


def _visible_projects(service: Any) -> list[dict[str, Any]]:
    """Every project the credential is a member of, across all pages."""
    return list(service.list_all_projects())


def _find_in_projects(
    service: Any,
    needle: str,
    projects: list[dict[str, Any]],
    skipped: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Datasets whose name contains ``needle`` (case-insensitive), in each of ``projects``.

    A project that cannot be read does not end the search: with ``skipped`` it is
    recorded there (id, name, why) and the rest are still searched.
    """
    matches: list[dict[str, Any]] = []
    for project in projects:
        project_id = project.get("id")
        if project_id is None:
            continue
        try:
            response = service.call(
                "mammoth.api.datasets.DatasetsAPI.list_all",
                project_id=project_id,
                fields=DATASET_ROW_FIELDS,
            )
        except CliError as error:
            if skipped is None:
                raise
            skipped.append(
                {
                    "project_id": project_id,
                    "project_name": project.get("name"),
                    "error": error.message,
                }
            )
            continue
        datasets = response.get("datasets", []) if isinstance(response, dict) else []
        for dataset in datasets:
            name = dataset.get("name") if isinstance(dataset, dict) else None
            if isinstance(name, str) and needle in name.lower():
                matches.append(
                    {
                        "project_id": project_id,
                        "project_name": project.get("name"),
                        **name_hit(dataset),
                        "source": source_of(dataset),
                    }
                )
    return matches


#: Pages of resource search read for one name (100 hits each); past it the result says so.
_SEARCH_PAGES = 5
_SEARCH_PAGE_SIZE = 100


def search_hits(
    service: Any, resource_type: str, needle: str, project_id: int | None = None
) -> tuple[list[dict[str, Any]], bool]:
    """Resources of ``resource_type`` whose name contains ``needle``, from the search route.

    One request (one more per 100 hits) replaces a listing per project: the
    workspace search, or the project's own resource list when ``project_id`` is
    given. Returns the minimal rows and whether the read stopped at
    ``_SEARCH_PAGES`` pages with more hits unread.
    """
    symbol = (
        "mammoth.api.browse.BrowseAPI.resources_search"
        if project_id is None
        else "mammoth.api.browse.BrowseAPI.resources_list"
    )
    scope: dict[str, Any] = {} if project_id is None else {"project_id": project_id}
    rows: list[dict[str, Any]] = []
    cursor: str | None = None
    for _ in range(_SEARCH_PAGES):
        page = service.call(
            symbol,
            search=needle,
            resource_type=resource_type,
            limit=_SEARCH_PAGE_SIZE,
            cursor=cursor,
            fields="minimal",
            **scope,
        )
        rows += [r for r in page.get("resources", []) if isinstance(r, dict)]
        cursor = page.get("next_cursor")
        if not (page.get("has_more") and cursor):
            return rows, False
    return rows, True


def search_cut_note(kind: str) -> str:
    """Said when a name search stopped early, with how to narrow it."""
    return (
        f"The name matched more than {_SEARCH_PAGES * _SEARCH_PAGE_SIZE} {kind}, so only the "
        "first of them were read. Use a longer name, or --project, to narrow it."
    )


def _projects_holding(
    service: Any, needle: str, visible: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """The visible projects that hold a dataset whose name contains ``needle``."""
    rows, cut = search_hits(service, "datasource", needle)
    holding = {r.get("project_id") for r in rows}
    return [p for p in visible if p.get("id") in holding], cut


def _other_projects(visible: list[dict[str, Any]], project_id: int) -> list[dict[str, Any]]:
    """Every visible project except ``project_id``."""
    return [p for p in visible if p.get("id") != project_id]


def named_project(service: Any, project_id: int, visible: list[dict[str, Any]]) -> dict[str, Any]:
    """``{"id", "name"}`` of ``project_id``, so a match can say where it was found.

    A search scoped by ``--project`` knew only the id, and its matches came back
    with ``project_name: None``: the agent could not tell the user which project
    held the dataset.
    """
    for project in visible:
        if project.get("id") == project_id:
            return project
    record = service.call("mammoth.api.projects.ProjectsAPI.get", project_id=project_id)
    record = record.model_dump(mode="json") if hasattr(record, "model_dump") else record
    record = record.get("project", record) if isinstance(record, dict) else {}
    return {"id": project_id, "name": record.get("name")}


def dataset_find(invocation: Invocation) -> HandlerResult:
    """Search dataset names for a substring across every visible project.

    Read-only local composite: lists the projects the credential can see, then
    lists datasets in each and keeps a case-insensitive substring match. With
    ``--project`` that project is searched first, and the rest only when it holds
    no match: the in-product agent runs every call under the project the user
    last opened, which is often not the one the named dataset is in. Does not
    require an active project.
    """
    name_substring = _require_string_positional(invocation, "name substring")
    needle = name_substring.lower()
    skipped: list[dict[str, Any]] = []
    with open_service(invocation) as (service, auth):
        visible = _visible_projects(service)
        cut = False
        if invocation.project is not None:
            projects: list[dict[str, Any]] = [named_project(service, invocation.project, visible)]
            matches = _find_in_projects(service, needle, projects, skipped)
            if not matches:
                holding, cut = _projects_holding(service, needle, visible)
                matches = _find_in_projects(
                    service, needle, _other_projects(holding, invocation.project), skipped
                )
                projects += _other_projects(visible, invocation.project)
        else:
            projects = visible
            holding, cut = _projects_holding(service, needle, visible)
            matches = _find_in_projects(service, needle, holding, skipped)
        meta = {
            "profile": invocation.profile,
            "workspace_id": auth.workspace_id,
            "project_id": invocation.project,
        }
    result: dict[str, Any] = {
        "matches": matches,
        "projects_searched": len(projects) - len(skipped),
    }
    if skipped:
        result["projects_skipped"] = skipped
    notes = [ambiguity_note(len(matches), name_substring)]
    if cut:
        result["truncated"] = True
        notes.append(search_cut_note("datasets"))
    if note := " ".join(n for n in notes if n):
        result["note"] = note
    return result, meta


def dataset_list(invocation: Invocation) -> HandlerResult:
    """List datasets in the active project, newest first, each with what tells them apart.

    Every item carries its size, created/updated time, how its data arrived, and
    its column names and types (from the list route's stored ``stats``,
    ``sources`` and ``data_schema``), cut to fit the agent tool output cap.
    ``full: true`` returns the raw ``{id, name}`` list instead. ``name`` keeps only datasets
    whose name contains it (case-insensitive) across every page, as short rows without
    column lists; ``limit``/``offset`` then page over the matches.
    """
    project_id = require_project(invocation)
    document = invocation.load_input() or {}
    _validate_paging(document)
    kwargs: dict[str, Any] = {"project_id": project_id}
    _forward_optional(document, kwargs, ("limit", "offset", "sort"))
    name = document.get("name")
    if isinstance(name, str) and name.strip():
        return _dataset_name_search(invocation, project_id, name.strip(), document)
    compact = not document.get("full")
    if compact:
        kwargs["fields"] = DATASET_ROW_FIELDS
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    if compact:
        data = _compact_dataset_list(data, kwargs.get("offset", 0), kwargs.get("sort"))
    return data, _meta(invocation, auth.workspace_id, project_id)


def _dataset_name_search(
    invocation: Invocation, project_id: int, name: str, document: dict[str, Any]
) -> HandlerResult:
    """``dataset list`` with ``name``: every page is read here, then filtered by substring.

    The list route only filters by exact name, so the substring match is local; the
    reads are bounded by the SDK's ``max_pages``.
    """
    with open_service(invocation) as (service, auth):
        data = service.call(
            "mammoth.api.datasets.DatasetsAPI.list_all",
            project_id=project_id,
            sort=document.get("sort", "(created_at:desc)"),
            fields=DATASET_ROW_FIELDS,
        )
        records = data.get("datasets", []) if isinstance(data, dict) else []
        page = search_page(records, name, int(document.get("offset", 0)), document.get("limit"))
        if page["matched"] == 0:
            holding, cut = _projects_holding(service, name.lower(), _visible_projects(service))
            elsewhere = _find_in_projects(
                service, name.lower(), _other_projects(holding, project_id)
            )
            if elsewhere:
                page["in_other_projects"] = elsewhere
                page["note"] = (
                    f"No dataset in project {project_id} matches; the ones listed in "
                    "in_other_projects do. Run the next call with --project <its project_id>."
                )
            if cut:
                page["truncated"] = True
                page["note"] = " ".join(
                    filter(None, (page.get("note"), search_cut_note("datasets")))
                )
    page["name"] = name
    return page, _meta(invocation, auth.workspace_id, project_id)


def _compact_dataset_list(data: Any, offset: int, sort: str | None) -> Any:
    """Summarise a dataset-list page and fit it to the tool output cap."""
    datasets = data.get("datasets") if isinstance(data, dict) else None
    if not isinstance(datasets, list):
        return data
    summaries = [dataset_summary(item) for item in datasets if isinstance(item, dict)]
    kept, omitted = fit_budget(summaries)
    result: dict[str, Any] = {
        "datasets": kept,
        "shown": len(kept),
        "order": sort or "newest first (created_at desc)",
        "note": (
            "A dataset record holds no sample values; 'view list DATASET_ID' shows "
            "stored sample_values per view (all_columns: true lists every column)."
        ),
    }
    if omitted or data.get("next"):
        result["more"] = True
        result["next_offset"] = int(offset) + len(kept)
    return result


def _export_write_hint(data: dict[str, Any]) -> str | None:
    """Name the recurring export that writes into this dataset, if any.

    A dataset produced by ``view export dataset`` carries its source view and
    export ids in ``additional_info`` (``DATAVIEW_ID``/``TRIGGER_ID`` — an
    export is a ``DataviewActionTrigger`` row, so ``TRIGGER_ID`` is exactly the
    ``export_id`` argument ``view export delete`` takes). Deleting the dataset
    does not stop that export from writing into it again; name the export and
    the command that stops it (T1-O-10: an agent deleted the dataset instead).
    """
    additional_info = data.get("additional_info")
    if not isinstance(additional_info, dict):
        return None
    dataview_id = additional_info.get("DATAVIEW_ID")
    export_id = additional_info.get("TRIGGER_ID")
    if not isinstance(dataview_id, int) or not isinstance(export_id, int):
        return None
    return (
        f"This dataset is written by a recurring export from view {dataview_id} "
        f"(export {export_id}); deleting the dataset does not stop the export. "
        f"Run 'mammoth view export delete {dataview_id} {export_id}' to stop it."
    )


def _zero_view_hint(dataset_id: int) -> str:
    """Name the fix for a dataset with no queryable views yet (T1-I-13).

    Nothing is queryable until a view exists (transforms, joins, exports and
    previews all take a view id, not a dataset id) — an agent that only reads
    dataset-level metadata and never sees a zero view count can conclude "no
    correction needed" while nothing it changed is visible anywhere.
    """
    return (
        f"This dataset has no views yet; nothing is queryable until one exists. "
        f"Run 'mammoth view create {dataset_id}' to create one."
    )


def dataset_get(invocation: Invocation) -> HandlerResult:
    """Get one dataset by id in the active project."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
        views = service.call(
            "mammoth.api.dataviews.DataviewsAPI.list",
            dataset_id=dataset_id,
            project_id=project_id,
        )
    _strip_file_ingestion_automation_possible(data)
    hint = _export_write_hint(data) if isinstance(data, dict) else None
    if isinstance(data, dict) and isinstance(views, dict):
        view_count = len(views.get("dataviews") or [])
        data = {**data, "view_count": view_count}
        if view_count == 0:
            zero_hint = _zero_view_hint(dataset_id)
            hint = f"{hint} {zero_hint}" if hint else zero_hint
    if hint is not None:
        data = {**data, "hint": hint}
    return data, _meta(invocation, auth.workspace_id, project_id)


def _strip_file_ingestion_automation_possible(data: Any) -> None:
    """Drop ``automation_possible`` (T1-R-01/T1-R-07): CSV-ingestion metadata
    about whether the header-parsing pipeline can auto-process this upload
    (``api/api/file/unprocessed.py``), unrelated to whether the dataset has a
    connector to put on a scheduled refresh. Left in, an agent checking a
    dataset's automation options reads it as contradicting a correct "no
    refreshable source" claim."""
    if not isinstance(data, dict):
        return
    params = data.get("additional_info", {}).get("all_data_backup", {}).get("PARAMS", {})
    if isinstance(params, dict):
        params.pop("automation_possible", None)


def dataset_data(invocation: Invocation) -> HandlerResult:
    """Fetch a dataset's data, waiting for the backing job to complete."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "project_id": project_id}
    _forward_optional(document, kwargs, ("timeout", "poll_interval"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _validate_paging(document: dict[str, Any]) -> None:
    """Refuse a ``limit`` outside 0..100 or a negative ``offset`` before any call is made."""
    for field, minimum, maximum in (("limit", 0, 100), ("offset", 0, None)):
        value = document.get(field)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < minimum
            or (maximum is not None and value > maximum)
        ):
            bound = "between 0 and 100" if maximum is not None else "non-negative"
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"'{field}' must be {bound}.",
                exit_status=EXIT_USAGE,
            )


def dataset_batch_data(invocation: Invocation) -> HandlerResult:
    """Fetch data for a specific dataset batch."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    batch_id = _require_int_positional_at(invocation, 1, "batch id")
    document = invocation.load_input() or {}
    _validate_paging(document)
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "batch_id": batch_id,
        "project_id": project_id,
    }
    _forward_optional(document, kwargs, ("columns", "limit", "offset", "timeout", "poll_interval"))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_file_settings(invocation: Invocation) -> HandlerResult:
    """Get file settings (delimiter, header, dates, ...) for a dataset."""
    data, meta = _read_dataset(invocation)
    return with_file_upload_path(data, _require_int_positional(invocation, "dataset id")), meta


def dataset_broken_rows(invocation: Invocation) -> HandlerResult:
    """List the lines of a dataset's uploaded file that could not be parsed."""
    return _read_dataset(invocation)


def dataset_broken_rows_resolve(invocation: Invocation) -> HandlerResult:
    """Add corrected set-aside lines to a dataset, or discard them. Prompt or ``--yes``.

    ``--input`` carries ``op`` (``add`` or ``remove``), ``batch_id`` and ``rows``
    (``{"line_num", "line"}`` each, from ``dataset broken-rows list``). Returns a
    job to wait on.
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "op": _require_field(document, "op"),
        "batch_id": _require_field(document, "batch_id"),
        "rows": _require_field(document, "rows"),
        "project_id": project_id,
    }
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"{kwargs['op']} set-aside lines of dataset {dataset_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def _read_dataset(invocation: Invocation) -> HandlerResult:
    """Call this command's SDK read with the DATASET_ID positional."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    if dataset_id <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="dataset id must be positive.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_file_settings_update(invocation: Invocation) -> HandlerResult:
    """Update a dataset's file settings. Required fields come from ``--input``."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    delimiter = _require_field(document, "delimiter")
    has_header = _require_field(document, "has_header")
    initial_skip_count = _require_field(document, "initial_skip_count")
    quotechar = _require_field(document, "quotechar")
    kwargs: dict[str, Any] = {
        "dataset_id": dataset_id,
        "delimiter": delimiter,
        "has_header": has_header,
        "initial_skip_count": initial_skip_count,
        "quotechar": quotechar,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(
        document,
        kwargs,
        (
            "date_format",
            "preview_mode",
            "skip_auto_process_check",
            "date_formats",
            "set_project_level_date_format",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_file_settings_undo(invocation: Invocation) -> HandlerResult:
    """Undo the last file settings change for a dataset. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"undo file settings for dataset {dataset_id}",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


_INTERPRETATION_FIELDS = ("user_instruction", "structure_map", "destination_dataset_id")


def dataset_interpretation(invocation: Invocation) -> HandlerResult:
    """Preview or confirm how a file that can be read several ways is interpreted.

    ``--input`` carries ``user_instruction`` (plain English, e.g. one of the
    suggestions ``dataset get`` shows), a ``structure_map`` from an earlier
    preview, or a ``destination_dataset_id``; at least one is required. ``confirm``
    alone also takes ``mode``: ``"original"`` keeps the file in its uploaded layout
    (no other field then), ``"interpreted"`` is the default.
    """
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input() or {}
    kwargs: dict[str, Any] = {"dataset_id": dataset_id, "project_id": project_id}
    confirming = invocation.command_id == "dataset.interpretation.confirm"
    _forward_optional(
        document,
        kwargs,
        (*_INTERPRETATION_FIELDS, "mode") if confirming else _INTERPRETATION_FIELDS,
    )
    if not any(field in kwargs for field in (*_INTERPRETATION_FIELDS, "mode")):
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="Say how to read the file: pass one of " + ", ".join(_INTERPRETATION_FIELDS),
            exit_status=EXIT_USAGE,
            hint="Use a suggestion from 'mammoth dataset get DATASET_ID' "
            "(additional_info.interpretation.instruction_suggestions) as user_instruction.",
        )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_create(invocation: Invocation) -> HandlerResult:
    """Create a dataset from a spec and creation type (required ``--input`` fields)."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    dataset_spec = _require_field(document, "dataset_spec")
    ds_creation_type = _require_field(document, "ds_creation_type")
    kwargs: dict[str, Any] = {
        "dataset_spec": dataset_spec,
        "ds_creation_type": ds_creation_type,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("folder_resource_id",))
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
        # ``datasets.create`` returns a bare job handle and never waits. Block on
        # it here (honoring ``--job-timeout``) so the command reports a finished
        # dataset id instead of a job id the caller must poll separately.
        settled = service.wait_if_job(data)
    return _created_dataset(data, settled), _meta(invocation, auth.workspace_id, project_id)


def _created_dataset(handle: Any, settled: Any) -> dict[str, Any]:
    """Shape a create job (handle + settled result) into a labeled result.

    ``wait_if_job`` returns the completed job's inner response, where the new
    dataset id lives under ``ds_id``. Falls back to the raw job handle when the
    server returned something unrecognized, so no information is lost.
    """
    job_id = handle.get("job_id") if isinstance(handle, dict) else None
    ds_id = None
    if isinstance(settled, dict):
        ds_id = settled.get("ds_id") or settled.get("dataset_id")
        nested = settled.get("response")
        if ds_id is None and isinstance(nested, dict):
            ds_id = nested.get("ds_id") or nested.get("dataset_id")
        job_id = settled.get("job_id", job_id)
    if ds_id is None:
        # No recognizable dataset id: surface the settled payload untouched
        # rather than claim a readiness we cannot confirm.
        return settled if isinstance(settled, dict) else {"job_id": job_id}
    result: dict[str, Any] = {"status": "ready", "dataset_id": ds_id}
    if job_id is not None:
        result["job_id"] = job_id
    return result


def dataset_create_from_pdf(invocation: Invocation) -> HandlerResult:
    """Create dataset(s) from tables extracted out of a PDF file."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    file_object_id = invocation.positional("file_object_id")
    if file_object_id is None:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="This command requires a file object id argument.",
            exit_status=EXIT_USAGE,
        )
    file_object_id = int(file_object_id)
    file_name = _require_field(document, "file_name")
    kwargs: dict[str, Any] = {
        "file_object_id": file_object_id,
        "file_name": file_name,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(
        document,
        kwargs,
        (
            "file_id",
            "table_list",
            "delete_file_after_extract",
            "is_preview_needed",
            "user_instruction",
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_rename(invocation: Invocation) -> HandlerResult:
    """Rename a dataset. Dataset id is positional; new name comes from ``--input``."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    document = invocation.load_input()
    name = _require_field(document, "name")
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), dataset_id=dataset_id, name=name, project_id=project_id
        )
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_trash(invocation: Invocation) -> HandlerResult:
    """Move one dataset to the project trash (reversible)."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_restore(invocation: Invocation) -> HandlerResult:
    """Restore a trashed dataset."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete one dataset by id. Prompt or ``--yes`` required."""
    project_id = require_project(invocation)
    dataset_id = _require_int_positional(invocation, "dataset id")
    action = f"delete dataset {dataset_id}"
    with open_service(invocation) as (service, auth):
        # A read, not a mutation: the dry-run gate lets it through so the
        # confirmation message below can name the export writing into this
        # dataset (T1-O-10), the same as a real run would see.
        preview = service.call(
            "mammoth.api.datasets.DatasetsAPI.get", dataset_id=dataset_id, project_id=project_id
        )
        hint = _export_write_hint(preview) if isinstance(preview, dict) else None
        if hint is not None:
            action = f"{action}. {hint}"
        enforce_confirmation(invocation, policy=POLICY_PROMPT_OR_YES, action=action)
        ack = service.call(_symbol(invocation), dataset_id=dataset_id, project_id=project_id)
        # The server acknowledges a delete with a job handle. Settle it here so
        # the handle's id is kept as ``job.id`` (the shape ``view delete`` has).
        data = _with_job(ack, service.wait_if_job(ack))
    if hint is not None and isinstance(data, dict):
        data = {**data, "hint": hint}
    return data, _meta(invocation, auth.workspace_id, project_id)


def _with_job(handle: Any, settled: Any) -> Any:
    """Return the settled result with the acknowledged job's id as ``job.id``."""
    job_id = handle.get("job_id") if isinstance(handle, dict) else None
    if job_id is None or not isinstance(settled, dict):
        return settled
    return {**settled, "job": {"id": job_id}}


def dataset_bulk_delete(invocation: Invocation) -> HandlerResult:
    """Permanently delete the listed datasets. ``dataset_ids`` from ``--input``; ``--yes`` required.

    The route has no delete-all form: it takes an explicit ``ids`` list and
    rejects an empty one, so the CLI never confirms an implicit whole-project
    delete.
    """
    project_id = require_project(invocation)
    document = invocation.load_input()
    dataset_ids = _require_field(document, "dataset_ids")
    if (
        not isinstance(dataset_ids, list)
        or not dataset_ids
        or any(
            isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in dataset_ids
        )
    ):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="The 'dataset_ids' input field must be a non-empty list of positive integers.",
            exit_status=EXIT_USAGE,
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=(
            f"delete datasets {', '.join(str(item) for item in dataset_ids)} "
            f"in project {project_id}"
        ),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), dataset_ids=dataset_ids, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_bulk_update(invocation: Invocation) -> HandlerResult:
    """Apply a bulk patch across the active project's datasets. High-impact."""
    project_id = require_project(invocation)
    document = invocation.load_input()
    patch_data = _require_field(document, "patch_data")
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action=f"bulk-update datasets in project {project_id}",
        target=str(project_id),
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), patch_data=patch_data, project_id=project_id)
    return data, _meta(invocation, auth.workspace_id, project_id)


def dataset_update(invocation: Invocation) -> HandlerResult:
    """Reject untyped dataset patches; use a typed dataset command instead."""
    raise CliError(
        code=CODE_UNSUPPORTED_CONTRACT,
        message="Raw dataset patch operations are not available through the CLI.",
        exit_status=EXIT_USAGE,
        hint=(
            "Use 'dataset rename DATASET_ID' for a name change or 'dataset file-settings "
            "update DATASET_ID' for file settings; other update variants need a typed contract."
        ),
        details={
            "command_id": invocation.command_id,
            "blocker": "B07 DATASET_PATCH_UNTYPED",
            "typed_alternatives": ["dataset.rename", "dataset.file-settings.update"],
        },
        recovery_commands=[
            "mammoth schema get dataset.rename",
            "mammoth schema get dataset.file-settings.update",
        ],
    )
