"""Workbook imports (Tableau, Power BI) and BI exports of a dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

from mammoth_cli.commands.dashboard._common import (
    _forward_optional,
    _generated_positionals,
    _meta,
    _require_int_positional,
    _require_str_positional,
    _symbol,
)
from mammoth_cli.commands.dashboard.generated import (
    _dump_model,
)
from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_UNSUPPORTED_CONTRACT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.confirm import (
    POLICY_CONFIRM_TARGET,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service, require_project
from mammoth_cli.services.local_files import refuse_existing_file


def _wait_workbook_job(service: Any, data: Any) -> Any:
    """Wait for the workbook job the upload started and return its finished result.

    The upload routes answer with a job handle; ``wait_if_job`` honors
    ``--job-timeout`` and is a no-op when the answer is already the result.
    """
    data = _dump_model(data)
    if isinstance(data, dict):
        data = _dump_model(service.wait_if_job(data))
    return data


def _refuse_rejected_workbook(data: Any) -> None:
    """Raise when the server rejected the upload (a junk file, an unreadable workbook)."""
    rejected = data.get("rejected") if isinstance(data, dict) else None
    if not rejected:
        return
    detail = rejected if isinstance(rejected, dict) else {"reason": str(rejected)}
    reason = str(detail.get("code") or detail.get("reason") or "not_a_workbook")
    text = detail.get("message") or detail.get("detail") or detail.get("error")
    raise CliError(
        code=reason,
        message=str(text) if text else f"The file was rejected: {reason}.",
        exit_status=EXIT_USAGE,
        hint="Pass a Tableau workbook (.twb or .twbx) or a Power BI file (.pbix).",
        details={"rejected": detail},
    )


#: Said plainly on an import result: the rows are made up to fit the workbook's fields.
_SYNTHETIC_ROWS_NOTE = (
    "The dataset holds generated sample rows (data_source fitted_sample), made up to fit "
    "the workbook's fields. They are synthetic, not the workbook's own data: load the real "
    "data into this dataset before you trust any number."
)


def dashboard_assess_twb(invocation: Invocation) -> HandlerResult:
    """Assess a local Tableau workbook through the SDK multipart seam."""
    file_path = _require_str_positional(invocation, "file")
    if not Path(file_path).is_file():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"File not found: {file_path}.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        data = _wait_workbook_job(service, service.call(_symbol(invocation), file=file_path))
    _refuse_rejected_workbook(data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_assess_pbix(invocation: Invocation) -> HandlerResult:
    """Assess a local Power BI workbook through the SDK multipart seam."""
    file_path = _require_str_positional(invocation, "file")
    if not Path(file_path).is_file():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"File not found: {file_path}.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        data = _wait_workbook_job(service, service.call(_symbol(invocation), file=file_path))
    _refuse_rejected_workbook(data)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_chat_attachment_upload(invocation: Invocation) -> HandlerResult:
    """Attach a local file to a dashboard's editor chat; the result's ``ref`` goes in a turn."""
    positionals = _generated_positionals(invocation)
    file_path = str(positionals.get("file", ""))
    if not Path(file_path).is_file():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"File not found: {file_path}.",
            exit_status=EXIT_USAGE,
        )
    with open_service(invocation) as (service, auth):
        data = service.call(
            _symbol(invocation), dashboard_id=positionals["dashboard_id"], file=file_path
        )
    return data, _meta(invocation, auth.workspace_id)


def dashboard_import_workbook(invocation: Invocation) -> HandlerResult:
    """Import a local workbook into a confirmed project scope."""
    file_path = _require_str_positional(invocation, "file")
    if not Path(file_path).is_file():
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"File not found: {file_path}.",
            exit_status=EXIT_USAGE,
        )
    document = invocation.load_input() or {}
    resolved_project = require_project(invocation)
    project_id = document.get("project_id", resolved_project)
    if "project_id" in document and (
        isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0
    ):
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="Input project_id must be a positive integer.",
            exit_status=EXIT_USAGE,
        )
    if project_id != resolved_project:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="Input project_id does not match resolved project.",
            exit_status=EXIT_USAGE,
        )
    enforce_confirmation(
        invocation,
        policy=POLICY_CONFIRM_TARGET,
        action="dashboard import workbook",
        target=str(project_id),
    )
    with open_service(invocation) as (service, auth):
        data = _wait_workbook_job(
            service, service.call(_symbol(invocation), file=file_path, project_id=project_id)
        )
    _refuse_rejected_workbook(data)
    if isinstance(data, dict) and data.get("data_source") == "fitted_sample":
        data = _flag_synthetic_import(data, file_path)
    return data, _meta(invocation, auth.workspace_id)


def _packaged_row_count(file_path: str) -> int | None:
    """Data rows in the CSV a ``.twbx`` packages (largest one), or None when it has none."""
    import csv
    import io
    import zipfile

    try:
        with zipfile.ZipFile(file_path) as bundle:
            sizes = []
            for info in bundle.infolist():
                if not info.filename.lower().endswith(".csv"):
                    continue
                with bundle.open(info) as raw:
                    # csv, not line counting: a quoted value may hold a line break.
                    text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
                    sizes.append(sum(1 for _ in csv.reader(text)) - 1)
    except (zipfile.BadZipFile, OSError, csv.Error):
        return None
    return max(sizes) if sizes and max(sizes) >= 0 else None


def _flag_synthetic_import(data: dict[str, Any], file_path: str) -> dict[str, Any]:
    """Make a fitted-sample import ``partial``: its numbers are not the workbook's.

    The backend importer substitutes generated rows for the workbook's data. That must
    not read ``settled`` with no warning, so the result is partial (exit 3) and says how
    many rows were expected and received and how to load the real data.
    """
    expected = _packaged_row_count(file_path)
    received = next(
        (data[k] for k in ("row_count", "rows", "rows_imported") if isinstance(data.get(k), int)),
        None,
    )
    warning = (
        "The imported data is synthetic: the backend replaced the workbook's data with "
        f"generated rows. Expected {expected if expected is not None else 'the workbook'}"
        f"{' rows' if expected is not None else chr(39) + 's own rows'}, received "
        f"{received if received is not None else 'a generated sample'}"
        f"{' rows' if received is not None else ''}. Do not trust any number on this dataset."
    )
    dataview_id = data.get("dataview_id")
    steps = [
        "Upload the real data as a CSV: mammoth file upload REAL.csv --project PROJECT_ID "
        "(or add it to this dataset with --input '{\"append_to_ds_id\": DATASET_ID}').",
        "Point the imported dashboard at the real dataset (dashboard figure add or "
        "dashboard chat edit), then delete the synthetic one"
        + (f" (view {dataview_id})." if dataview_id is not None else "."),
    ]
    return {
        **data,
        "synthetic_data": True,
        "data_note": _SYNTHETIC_ROWS_NOTE,
        "partial": True,
        "warnings": [warning],
        "next_steps": steps,
    }


# ── BI export (Power BI / Tableau) ───────────────────────────────────────────

_BI_TARGETS: tuple[Literal["powerbi", "tableau"], ...] = ("powerbi", "tableau")


_BI_EXPORT_EMBEDDED_REFUSAL = (
    "The file cannot be downloaded from here. Send the user to the dashboard's Publish menu"
    " (the arrow next to Publish) -> Export to Power BI / Export to Tableau."
)


def _bi_target(document: dict[str, Any]) -> Literal["powerbi", "tableau"]:
    """Read and validate the required ``target`` input field."""
    target = document.get("target")
    if target not in _BI_TARGETS:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message="Input `target` must be 'powerbi' or 'tableau'.",
            exit_status=EXIT_USAGE,
            hint='Pass --input \'{"target": "powerbi"}\' or \'{"target": "tableau"}\'.',
        )
    return cast(Literal["powerbi", "tableau"], target)


def dashboard_bi_preflight(invocation: Invocation) -> HandlerResult:
    """What a Power BI or Tableau export of this dashboard would carry.

    Side-effect free -- nothing is built and nothing is logged, so the export
    dialog can be opened and dismissed freely. Required input ``target``
    (``powerbi`` or ``tableau``) selects which release route answers.
    """
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = invocation.load_input() or {}
    target = _bi_target(document)
    symbol = f"mammoth.api.dashboards.DashboardsAPI.{target}_preflight"
    with open_service(invocation) as (service, auth):
        data = service.call(symbol, dashboard_id=dashboard_id)
    return data, _meta(invocation, auth.workspace_id)


def dashboard_bi_export(invocation: Invocation) -> HandlerResult:
    """Download this dashboard as a Power BI project (.zip) or Tableau workbook (.twbx).

    Required input ``target`` (``powerbi`` or ``tableau``) selects the release
    route. With no ``output_path`` the file is written to the current
    directory under an auto-generated name.

    Embedded (see ``mammoth_cli.runtime.embedded``) it is refused: the route
    needs the Authorization header, so a link handed to the user's browser
    401s. The user downloads it from the dashboard's own export dialog.
    """
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = invocation.load_input() or {}
    target = _bi_target(document)
    if embedded.active():
        raise CliError(
            code=CODE_UNSUPPORTED_CONTRACT,
            message=_BI_EXPORT_EMBEDDED_REFUSAL,
            exit_status=EXIT_USAGE,
            hint="Run `dashboard bi-preflight` to tell the user what will convert first.",
        )
    symbol = f"mammoth.api.dashboards.DashboardsAPI.export_{target}"
    kwargs: dict[str, Any] = {"dashboard_id": dashboard_id}
    _forward_optional(document, kwargs, ("output_path",))
    extension = "zip" if target == "powerbi" else "twbx"
    refuse_existing_file(
        invocation, kwargs.get("output_path") or f"dashboard_{dashboard_id}_{target}.{extension}"
    )
    with open_service(invocation) as (service, auth):
        preflight = _bi_preflight_or_none(service, target, dashboard_id)
        data = service.call(symbol, **kwargs)
    # The SDK returns a Path; render it as a string so the written location is
    # visible in every output mode and serializes cleanly to JSON.
    result: dict[str, Any] = {"output_path": str(data)}
    result.update(_bi_drops(preflight, target))
    return result, _meta(invocation, auth.workspace_id)


def _bi_preflight_or_none(service: Any, target: str, dashboard_id: int) -> Any:
    """The pre-flight for this export; ``None`` when it cannot be read (the export still runs)."""
    try:
        return _dump_model(
            service.call(
                f"mammoth.api.dashboards.DashboardsAPI.{target}_preflight",
                dashboard_id=dashboard_id,
            )
        )
    except Exception:  # noqa: BLE001 -- advice; the export is the command
        return None


def _bi_drops(preflight: Any, target: str) -> dict[str, Any]:
    """Name the figures the export leaves out, as a structured warning.

    The export writes a file whatever it dropped, so the result must say so:
    ``partial`` makes ``verify`` report it as not clean.
    """
    if not isinstance(preflight, dict):
        return {}
    refusals = [r for r in preflight.get("refusals") or [] if isinstance(r, dict)]
    if not refusals:
        return {}
    dropped = [{"title": r.get("title"), "reason": r.get("reason")} for r in refusals]
    total = preflight.get("figures_total")
    exported = preflight.get("figures_exported")
    return {
        "figures_total": total,
        "figures_exported": exported,
        "dropped_figures": dropped,
        "partial": True,
        "warnings": [
            {
                "issue": "figures_dropped",
                "target": target,
                "detail": (
                    f"{len(dropped)} of {total} figures are not in the file "
                    f"({exported} exported): "
                    + "; ".join(f"{d['title']} ({d['reason']})" for d in dropped)
                ),
                "dropped": dropped,
            }
        ],
    }
