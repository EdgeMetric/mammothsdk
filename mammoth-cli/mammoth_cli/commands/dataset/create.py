"""Create a dataset (upload, clone, data pull, PDF) and predict the name it ends up with."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.dataset._common import (
    _DATASET_GET_SYMBOL,
    _forward_optional,
    _meta,
    _require_field,
    _SdkCaller,
    _symbol,
)
from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_JOB_FAILED,
    CODE_MISSING_ARGUMENT,
    EXIT_API,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services.field_enums import DATA_PULL_FILE_VALUES, allowed_values_text


def dataset_create(invocation: Invocation) -> HandlerResult:
    """Create a dataset (web URL, clone, or import from a connection such as SFTP).

    ``--input`` needs ``dataset_spec`` and ``ds_creation_type``.
    """
    project_id = require_project(invocation)
    document = invocation.load_input()
    dataset_spec = _require_field(document, "dataset_spec")
    ds_creation_type = _require_field(document, "ds_creation_type")
    _require_clone_views(ds_creation_type, dataset_spec)
    # A clone can land in another project (``dataset_spec.target_project_id``): the
    # name check and the result's scope are that project's, not the active one's.
    landing_project_id = _clone_target_project(ds_creation_type, dataset_spec) or project_id
    _default_data_pull_file(ds_creation_type, dataset_spec)
    kwargs: dict[str, Any] = {
        "dataset_spec": dataset_spec,
        "ds_creation_type": ds_creation_type,
        "project_id": project_id,
    }
    assert document is not None
    _forward_optional(document, kwargs, ("folder_resource_id",))
    with open_service(invocation) as (service, auth):
        if invocation.dry_run:
            _predict_final_name(invocation, service, dataset_spec, landing_project_id)
        data = service.call(_symbol(invocation), **kwargs)
        # ``datasets.create`` returns a bare job handle and never waits. Block on
        # it here (honoring ``--job-timeout``) so the command reports a finished
        # dataset id instead of a job id the caller must poll separately.
        settled = service.wait_if_job(data)
        result = _created_dataset(data, settled)
        _add_final_name(service, result, dataset_spec, landing_project_id)
    return result, _meta(invocation, auth.workspace_id, landing_project_id)


def _clone_target_project(ds_creation_type: object, dataset_spec: object) -> int | None:
    """The clone's ``target_project_id`` (a positive integer), or None when it is not set."""
    if ds_creation_type != "clone" or not isinstance(dataset_spec, dict):
        return None
    target = dataset_spec.get("target_project_id")
    if target is None:
        return None
    if isinstance(target, bool) or not isinstance(target, int) or target <= 0:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"dataset_spec.target_project_id must be a positive integer, got {target!r}.",
            exit_status=EXIT_USAGE,
        )
    return target


def _require_clone_views(ds_creation_type: object, dataset_spec: object) -> None:
    """Refuse a clone with no ``clone_dataview_ids``: the server would make a blank view."""
    if ds_creation_type != "clone" or not isinstance(dataset_spec, dict):
        return
    if dataset_spec.get("clone_dataview_ids") == []:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message="A clone needs at least one view in dataset_spec.clone_dataview_ids",
            exit_status=EXIT_USAGE,
            hint="Pass the source dataset's default_view id from 'mammoth view list "
            "DATASET_ID' (other views only when asked); an empty list makes a blank view.",
        )


#: The server's ``data_pull_file`` values (one list for the check, its hint and ``--help``).
_DATA_PULL_FILE_VALUES = DATA_PULL_FILE_VALUES


def _default_data_pull_file(ds_creation_type: object, dataset_spec: object) -> None:
    """Default a cloud file import's ``data_pull_file`` to "Pull same file", as the web app does.

    Raises:
        CliError: ``invalid_argument`` listing the allowed values when it is not one of them.
    """
    if ds_creation_type != "cloud" or not isinstance(dataset_spec, dict):
        return
    properties = dataset_spec.get("query_properties")
    if not isinstance(properties, dict) or not properties.get("file_path"):
        return
    pull = properties.setdefault("data_pull_file", _DATA_PULL_FILE_VALUES[0])
    if pull not in _DATA_PULL_FILE_VALUES:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="query_properties.data_pull_file must be one of "
            f"{list(_DATA_PULL_FILE_VALUES)}, got {pull!r}.",
            exit_status=EXIT_USAGE,
            hint=f"Use one of: {allowed_values_text(_DATA_PULL_FILE_VALUES)}.",
            details={"got": pull, "allowed": list(_DATA_PULL_FILE_VALUES)},
        )


def _created_dataset(handle: Any, settled: Any) -> dict[str, Any]:
    """Shape a create job (handle + settled result) into a labeled result.

    What each creation type settles with: weburl, clone and a single cloud file or
    database import carry the new dataset id (``ds_id``, ``dataset_id`` or
    ``datasource_id``); a cloud import deferred to a later start carries
    ``datasource_config_id`` and reports ``scheduled``; a bulk cloud file import
    carries ``files_found``/``created``/``failed`` and is returned as the server
    sent it; a sketch is not a job and answers with the dataset itself. A job that
    settled with none of these made nothing, so it raises with the server's reason
    rather than report success.

    Raises:
        CliError: ``job_failed`` when the settled job made no dataset.
    """
    if not isinstance(handle, dict) or "job_id" not in handle:
        return settled if isinstance(settled, dict) else {"job_id": None}
    job_id = handle["job_id"]
    ds_id = None
    config_id = None
    if isinstance(settled, dict):
        for source in (settled, settled.get("response")):
            if not isinstance(source, dict):
                continue
            ds_id = ds_id or _first_id(source, _DATASET_ID_KEYS)
            config_id = config_id or source.get("datasource_config_id")
        job_id = settled.get("job_id", job_id)
    if ds_id is None and config_id is not None:
        return {"status": "scheduled", "datasource_config_id": config_id, "job_id": job_id}
    if ds_id is None and isinstance(settled, dict) and "files_found" in settled:
        return settled
    if ds_id is None:
        reason = _job_reason(settled)
        raise CliError(
            code=CODE_JOB_FAILED,
            message="The dataset was not created"
            + (f": {reason}" if reason else f" (job {job_id} finished without a dataset id)."),
            exit_status=EXIT_API,
        )
    return {"status": "ready", "dataset_id": ds_id, "job_id": job_id}


#: Keys a settled create job may carry its dataset id under.
_DATASET_ID_KEYS = ("ds_id", "dataset_id", "datasource_id")


def _first_id(source: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """The first non-empty value of ``keys`` in ``source``, or None."""
    return next((source[key] for key in keys if source.get(key)), None)


def _job_reason(settled: Any) -> str | None:
    """The failure reason a settled job carries (``failure_reason``, ``message``, ``error``)."""
    if not isinstance(settled, dict):
        return None
    nested = settled.get("response")
    for source in (settled, nested if isinstance(nested, dict) else {}):
        for key in ("failure_reason", "message", "error"):
            if source.get(key):
                return str(source[key])
    return None


#: Pages (of 100) read to predict a final name; past it the answer is "a suffix may be added".
_NAME_PROBE_PAGES = 20


def _requested_name(dataset_spec: object) -> str | None:
    """The name the caller asked for: ``ds_name`` (clone, cloud) or ``name`` (sketch)."""
    if not isinstance(dataset_spec, dict):
        return None
    for key in ("ds_name", "name"):
        if isinstance(dataset_spec.get(key), str) and dataset_spec[key]:
            return str(dataset_spec[key])
    return None


def _project_dataset_names(service: _SdkCaller, project_id: int) -> tuple[set[str], bool]:
    """Every dataset name in the project and whether all of them were read."""
    names: set[str] = set()
    for page in range(_NAME_PROBE_PAGES):
        data = service.call(
            "mammoth.api.datasets.DatasetsAPI.list",
            project_id=project_id,
            limit=100,
            offset=page * 100,
        )
        rows = data.get("datasets", []) if isinstance(data, dict) else []
        names.update(r["name"] for r in rows if isinstance(r, dict) and "name" in r)
        if len(rows) < 100:
            return names, True
    return names, False


def _name_impact(requested: str, names: set[str], complete: bool) -> dict[str, Any]:
    """The dry-run prediction for ``requested`` against the project's dataset ``names``."""
    if requested not in names:
        free: dict[str, Any] = {"requested_name": requested, "name_taken": False}
        if complete:
            return {**free, "final_name": requested}
        return {**free, "note": "Not all datasets were read; a numeric suffix is added if taken."}
    impact: dict[str, Any] = {"requested_name": requested, "name_taken": True}
    if not complete:
        impact["note"] = f"'{requested}' is taken; a numeric suffix will be added to the name."
        return impact
    suffix = next(i for i in range(2, len(names) + 3) if f"{requested} {i}" not in names)
    impact["final_name"] = f"{requested} {suffix}"
    impact["note"] = (
        f"'{requested}' is taken; the dataset will be named '{impact['final_name']}'. "
        "Ask the user whether to use a different name."
    )
    return impact


def _predict_final_name(
    invocation: Invocation, service: _SdkCaller, dataset_spec: object, project_id: int
) -> None:
    """Dry run: say whether the requested name is taken and what the server will name it.

    The server (``Datasource.get_unique_name``) tries ``name``, ``name 2``, ``name 3``...
    against the project's live dataset names, so the answer is computed the same way.
    """
    requested = _requested_name(dataset_spec)
    if requested is not None:
        names, complete = _project_dataset_names(service, project_id)
        object.__setattr__(invocation, "predicted_impact", _name_impact(requested, names, complete))


def _add_final_name(
    service: _SdkCaller, result: dict[str, Any], dataset_spec: object, project_id: int
) -> None:
    """Add the name the server actually gave the new dataset to a create result.

    The server appends a suffix when the requested name is taken, so the
    requested name is not the dataset's name. The dataset already exists, so a failed
    lookup must not fail (and invite a duplicate) create; it is reported in ``note``.
    """
    dataset_id = result.get("dataset_id")
    if dataset_id is None:
        return
    try:
        record = service.call(
            _DATASET_GET_SYMBOL, dataset_id=dataset_id, project_id=project_id, fields="id,name"
        )
    except CliError as exc:  # the service maps every SDK API/HTTP error to CliError
        result["note"] = (
            f"Created dataset {dataset_id}; its final name could not be read back "
            f"({exc.code}). Run dataset get {dataset_id}."
        )
        return
    if not isinstance(record, dict):
        return
    name = record.get("dataset", record).get("name")
    if not isinstance(name, str):
        return
    result["name"] = name
    requested = _requested_name(dataset_spec)
    if requested is not None and requested != name:
        result["requested_name"] = requested
        result["note"] = f"The name '{requested}' was taken, so the dataset is named '{name}'."


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
