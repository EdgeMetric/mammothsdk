"""The manifest-driven handler for dashboard commands with no logic of their own."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mammoth.api import agents as agents_api
from mammoth.api import dashboards as dashboards_api
from mammoth.exceptions import MammothValidationError
from pydantic import ValidationError

from mammoth_cli.commands.dashboard._common import (
    _bound_document,
    _generated_positionals,
    _meta,
    _resolve_job,
    _symbol,
)
from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.view.upload import view_profiles
from mammoth_cli.context import profiles
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    CODE_MISSING_FIELD,
    CODE_SDK_SYMBOL_UNRESOLVED,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.normalize import Revealed, normalize
from mammoth_cli.runtime import parents
from mammoth_cli.runtime.confirm import (
    POLICY_NONE,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.reveal import REVEAL_COMMANDS
from mammoth_cli.runtime.session import open_service, resolved_project
from mammoth_cli.services.argspec import arg_spec
from mammoth_cli.services.board_values import board_values, dashboard_link
from mammoth_cli.services.command_contract import bind_command_inputs
from mammoth_cli.services.dashboard_figures import (
    bake_error_problem,
    canvas_figure_problems,
)
from mammoth_cli.services.dashboard_pages import (
    check_added_pages,
    generate_substitutions,
    page_substitutions,
)
from mammoth_cli.services.dashboard_review import (
    CANVAS_GET,
    NEW_COLUMN_NOTE,
    columns_not_on_dashboard,
    has_profiles,
    reporting_month,
    review,
)
from mammoth_cli.services.dashboard_review import _profiles as _review_profiles
from mammoth_cli.services.draft_report import (
    EACH_REPORTED,
    PREVIEW_COMMAND,
    with_each_reports,
    with_preview_cap,
)
from mammoth_cli.services.mapping import map_sdk_exception
from mammoth_cli.services.read_memo import forget, remember

#: Rules the SDK method enforces before sending, run by the handler too: a dry run stops
#: at the SDK symbol, so without this it would accept input the real run refuses.
_SDK_RULES: dict[str, Callable[[dict[str, Any]], None]] = {
    "agent.access.grant.give": lambda k: agents_api.check_grant_give(
        k.get("emails") or [], str(k.get("level") or ""), k.get("items") or []
    ),
    "agent.access.grant.update": lambda k: agents_api.check_grant_update(
        k.get("level"), k.get("items")
    ),
    "agent.access.request.create": lambda k: agents_api.check_request_create(
        str(k.get("kind") or ""), str(k.get("text") or "")
    ),
    "agent.access.request.resolve": lambda k: agents_api.check_request_resolve(
        str(k.get("status") or "")
    ),
    "agent.access.settings.update": lambda k: agents_api.check_settings_update(k),
    "agent.turn.rate": lambda k: agents_api.check_rating(
        str(k.get("rating") or ""), k.get("comment")
    ),
    "dashboard.embed.lifetime.set": lambda k: dashboards_api.check_token_ttl(k.get("token_ttl")),
}


#: What the confirmation (and its refusal) names, where the command id alone would hide
#: the consequence. Formatted with the command's positionals.
_CONFIRM_ACTIONS: dict[str, str] = {
    "agent.access.grant.give": "invite people to ask the agent about projects (they are emailed)",
    "agent.access.grant.revoke": "revoke agent access grant {grant_id} (the person loses access)",
    "agent.access.request.resolve": (
        "close agent access request {request_id} for good (irreversible: it cannot be reopened "
        "and the requester is told)"
    ),
    "agent.access.settings.update": "change the AI Agent settings of the whole workspace",
    "support.plan.update-entitlements": (
        "change the entitlements of plan {plan_id} (applies to every workspace on that plan)"
    ),
}


#: Commands whose ``--confirm`` target is the workspace, not a positional.
_WORKSPACE_TARGETED = frozenset({"agent.access.settings.update"})


#: Commands whose job handle names what the job's results are (descriptor ids,
#: columns, the drilled level); the answer carries the handle and the results.
_HANDLE_KEPT = frozenset(
    {
        "dashboard.figure.drill",
        "dashboard.figure.rows",
        "dashboard.published.drill",
        "dashboard.published.rows",
        # The bake job's result does not name the chart; the handle's dashboard_id does.
        "dashboard.live-chart.create",
    }
)


def _check_sdk_rules(command_id: str, kwargs: dict[str, Any]) -> None:
    rule = _SDK_RULES.get(command_id)
    if rule is None:
        return
    try:
        rule(kwargs)
    except MammothValidationError as exc:
        raise map_sdk_exception(exc) from exc


def generated_dashboard(invocation: Invocation) -> HandlerResult:
    """Dispatch a generated dashboard command through its reviewed manifest.

    Positionals have already been typed by the shared positional resolver and
    structured input is recursively validated by :meth:`Invocation.load_input`.
    The manifest remains authoritative for both the backing SDK method and the
    mutation confirmation policy.
    """
    record = command_by_id(invocation.command_id)
    if record is None:
        raise CliError(
            code=CODE_SDK_SYMBOL_UNRESOLVED,
            message=f"No command manifest exists for '{invocation.command_id}'.",
            exit_status=EXIT_USAGE,
        )

    document = _bound_document(invocation)
    positionals = _generated_positionals(invocation)
    kwargs = bind_command_inputs(invocation.command_id, document, **positionals)

    # The generated contract treats named request bodies as opaque mappings;
    # AddPages has a release-level minItems constraint that must be enforced
    # before confirmation or transport.
    if invocation.command_id == "dashboard.pages.add" and "body" in kwargs:
        from mammoth.models.dashboards import AddPagesSpec

        try:
            kwargs["body"] = AddPagesSpec.model_validate(kwargs["body"]).model_dump(
                mode="json", exclude_none=True
            )
        except ValidationError as exc:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"Invalid add-pages request: {exc}",
                exit_status=EXIT_USAGE,
            ) from exc

    spec = arg_spec(_symbol(invocation))
    if spec is not None:
        missing = [
            field.name for field in spec.fields if field.required and field.name not in kwargs
        ]
        if missing:
            field = missing[0]
            raise CliError(
                code=CODE_MISSING_FIELD,
                message=f"This command requires the '{field}' input field.",
                exit_status=EXIT_USAGE,
                hint=f"Pass it via --input, for example: --input '{{\"{field}\": ...}}'.",
            )

    _check_sdk_rules(invocation.command_id, kwargs)
    if (
        invocation.project is not None
        and spec is not None
        and "project_id" not in kwargs
        and any(field.name == "project_id" for field in spec.fields)
    ):
        # ``--project`` names the project a new board belongs to (live-chart create,
        # template apply, v3 generate); without it the server picks the source's.
        kwargs["project_id"] = invocation.project

    policy = str(record.get("confirmation") or POLICY_NONE)
    target = next((str(value) for value in positionals.values()), None)
    action = _CONFIRM_ACTIONS.get(invocation.command_id, invocation.command_id.replace(".", " "))
    action = action.format(**positionals)
    if invocation.command_id not in _WORKSPACE_TARGETED:
        enforce_confirmation(invocation, policy=policy, action=action, target=target)

    with open_service(invocation) as (service, auth):
        if invocation.command_id in _WORKSPACE_TARGETED:
            # The target is the workspace itself, known only once the session is open.
            enforce_confirmation(
                invocation, policy=policy, action=action, target=str(auth.workspace_id)
            )
        data = service.call(_symbol(invocation), **kwargs)
        handle = data.model_dump(mode="json") if hasattr(data, "model_dump") else data
        data = _resolve_job(service, invocation, data)
        if invocation.command_id in _HANDLE_KEPT and isinstance(handle, dict):
            # The job's results are keyed by descriptor id; the handle says which
            # descriptor is the rows, the count or the drilled level, so keep both.
            data = {**handle, **data} if isinstance(data, dict) else data
        if invocation.command_id == "dashboard.pages.add" and "body" in kwargs:
            requested = kwargs["body"].get("params", {}).get("pages", [])
            data = check_added_pages(service, positionals["dashboard_id"], requested, data)
        data = _with_draft_reports(invocation.command_id, service, positionals, kwargs, data)
        if invocation.command_id in _REVIEWED_COMMANDS:
            data = _with_deliverable_check(invocation, service, auth, positionals, data, kwargs)
        if invocation.command_id in _VALUED_COMMANDS:
            data = _with_board_values(service, auth, positionals, data)
        forget(service)
    if invocation.reveal_secrets and invocation.command_id in REVEAL_COMMANDS:
        data = Revealed(normalize(data, redact_secrets=False))
    return data, _meta(invocation, auth.workspace_id)


def _with_draft_reports(
    command_id: str,
    service: Any,
    positionals: dict[str, Any],
    kwargs: dict[str, Any],
    data: Any,
) -> Any:
    """Route a connector draft read to its sample report (:mod:`...services.draft_report`)."""
    if command_id in EACH_REPORTED:
        return with_each_reports(_dump_model(data))
    if command_id == PREVIEW_COMMAND:
        return with_preview_cap(
            service,
            positionals["draft_id"],
            positionals["source_id"],
            kwargs.get("limit"),
            _dump_model(data),
        )
    return data


#: Board-building steps whose result carries the evaluated card/tile numbers.
_VALUED_COMMANDS = frozenset({"dashboard.v3.generate", "dashboard.chat.edit"})


def _with_board_values(service: Any, auth: Any, positionals: dict[str, Any], data: Any) -> Any:
    """Add ``dashboard_link`` and each KPI card's and tile's evaluated number.

    The result of a build/edit is definitions; the agent must see the numbers
    it is about to report (a rate that reads 21.9% where the data says 14.9%).
    """
    data = _dump_model(data)
    if not isinstance(data, dict):
        return data
    dashboard_id = positionals.get("dashboard_id") or data.get("id")
    if not isinstance(dashboard_id, int):
        return {**data, "values": {"unavailable": "the result names no dashboard id"}}
    return {
        **data,
        "dashboard_link": dashboard_link(auth.base_url, auth.workspace_id, dashboard_id),
        "values": board_values(service, dashboard_id),
    }


def _dump_model(value: Any) -> Any:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


#: Authoring steps whose result carries ``deliverable_check``.
_REVIEWED_COMMANDS = frozenset(
    {
        "dashboard.create-blank",
        "dashboard.canvas.save",
        "dashboard.pages.add",
        "dashboard.v3.generate",
        "dashboard.chat.edit",
    }
)


def _with_deliverable_check(
    invocation: Invocation,
    service: Any,
    auth: Any,
    positionals: dict[str, Any],
    data: Any,
    kwargs: dict[str, Any] | None = None,
) -> Any:
    """Add ``deliverable_check`` (money shown? blanks decided?) to an authoring result.

    One canvas read; advice only, so a failed read leaves the result as it was.
    The same read also catches a figure the board cannot draw (an unknown column,
    a sum over text, a bake error) and any chart the server swapped or dropped; those
    set ``bake_ok``/``partial`` so ``verify`` reports the write as not clean.
    """
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    if not isinstance(data, dict):
        return data
    dashboard_id = positionals.get("dashboard_id") or data.get("id")
    data = _reflect_not_applied(invocation.command_id, data, dashboard_id)
    if not isinstance(dashboard_id, int):
        return {
            **data,
            "deliverable_check": {
                "checked": False,
                "warnings": [],
                "error": "the result names no dashboard id, so no canvas was read",
            },
        }
    try:
        canvas = service.call(CANVAS_GET, dashboard_id=dashboard_id)
        # The board's numbers (next step of a build or edit) read the same canvas.
        remember(service, CANVAS_GET, {"dashboard_id": dashboard_id}, canvas)
        canvas_doc = _dump_model(canvas)
        warnings = _deliverable_warnings(invocation, service, auth, dashboard_id, canvas_doc)
    except Exception as exc:  # noqa: BLE001 -- advice must never fail the authoring step
        error = f"{type(exc).__name__}: {exc}"
        return {
            **data,
            "deliverable_check": {"checked": False, "warnings": [], "error": error},
        }
    check: dict[str, Any] = {"checked": True, "warnings": warnings}
    if warnings:
        check["note"] = (
            "Fix these before you report the dashboard as done, or say in your "
            "report why not."
            + (" " + NEW_COLUMN_NOTE if any("fix" in warning for warning in warnings) else "")
        )
    return {
        **data,
        "deliverable_check": check,
        **_authoring_problems(invocation, data, canvas_doc, kwargs or {}),
    }


def _reflect_not_applied(
    command_id: str, data: dict[str, Any], dashboard_id: Any
) -> dict[str, Any]:
    """A chat edit that reports ``changed: false`` was not applied, whatever its message says.

    The model's own ``message`` ("I added a Total Events card") describes what it meant
    to do. It is kept as ``model_message`` and the ``message`` says plainly that nothing
    was applied, with the fallback that works.
    """
    if command_id != "dashboard.chat.edit" or data.get("changed") is not False:
        return data
    claim = data.get("message")
    target = dashboard_id if dashboard_id is not None else "DASHBOARD_ID"
    out = {
        **data,
        "message": (
            "NOT APPLIED: the dashboard was not changed"
            + (" (the board did not bake)" if data.get("bake_ok") is False else "")
            + ". The assistant's reply below describes what it intended, not what happened."
        ),
        "next_steps": [
            f"Read the board: mammoth dashboard get {target}",
            f"Add the card directly: mammoth dashboard figure add {target} --input "
            '\'{"dataview_id": VIEW_ID, "figure": {"kind": "kpi", "measure": '
            '"COLUMN", "agg": "sum"}}\'',
        ],
    }
    if isinstance(claim, str):
        out["model_message"] = claim
    return out


def _authoring_problems(
    invocation: Invocation, data: dict[str, Any], canvas_doc: Any, kwargs: dict[str, Any]
) -> dict[str, Any]:
    """Fields that make ``verify`` report a figure that failed or was swapped as not clean."""
    command_id = invocation.command_id
    params = (kwargs.get("body") or {}).get("params") or {}
    broken: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []
    if command_id in {"dashboard.canvas.save", "dashboard.pages.add"}:
        broken = canvas_figure_problems(canvas_doc)
        bake = bake_error_problem(canvas_doc)
        if bake is not None:
            broken.append(bake)
    if command_id == "dashboard.pages.add":
        profiles = [p["name"] for p in _canvas_profiles(canvas_doc)]
        refused = (data.get("chart_check") or {}).get("refused") or []
        partial = page_substitutions(
            params.get("pages") or [], data.get("added_page_ids"), canvas_doc, refused, profiles
        )
        partial += [
            {
                "issue": "page_dropped",
                "requested": {"page": removed.get("title")},
                "used": None,
                "detail": f"page '{removed.get('title')}' got no charts and was removed.",
            }
            for removed in (data.get("chart_check") or {}).get("removed_pages") or []
        ]
    elif command_id == "dashboard.v3.generate":
        partial = generate_substitutions(params.get("intent"), canvas_doc, data.get("message"))
    elif command_id == "dashboard.chat.edit":
        partial = generate_substitutions(None, canvas_doc, data.get("message"))
    extra: dict[str, Any] = {}
    if broken:
        extra["bake_ok"] = False
        extra["figure_check"] = {
            "problems": broken,
            "notes": [str(problem["detail"]) for problem in broken],
        }
    if partial:
        extra["partial"] = True
        extra["substitution_check"] = {
            "problems": partial,
            "notes": [str(problem["detail"]) for problem in partial],
        }
    if broken or partial:
        previous = data.get("warnings")
        extra["warnings"] = [*(previous if isinstance(previous, list) else []), *broken, *partial]
    return extra


def _canvas_profiles(canvas_doc: Any) -> list[dict[str, Any]]:
    return _review_profiles(canvas_doc) if isinstance(canvas_doc, dict) else []


def _deliverable_warnings(
    invocation: Invocation,
    service: Any,
    auth: Any,
    dashboard_id: int,
    canvas_doc: Any = None,
) -> list[dict[str, Any]]:
    """Read the canvas (and its view) once and return the review's warnings."""
    if canvas_doc is None:
        canvas_doc = _dump_model(service.call(CANVAS_GET, dashboard_id=dashboard_id))
    source = (canvas_doc.get("canvas") or {}).get("dataset") or {}
    view_id = source.get("dataview_id")
    profile = invocation.profile or profiles.get_selected()
    dataset_id = (
        parents.lookup(profile, auth.workspace_id, view_id) if isinstance(view_id, int) else None
    )
    current = (
        view_profiles(service, dataset_id, view_id, resolved_project(invocation))
        if isinstance(view_id, int) and dataset_id is not None
        else None
    )
    scope = reporting_month(canvas_doc, dashboard_id)
    if not has_profiles(canvas_doc):
        return scope + review(canvas_doc, dataset_id, current)
    stale = columns_not_on_dashboard(canvas_doc, current)
    return (
        scope
        + stale
        + [
            warning
            for warning in review(canvas_doc, dataset_id)
            # On a stale board the money advice is the rebuild, not a new column.
            if not (stale and warning["issue"] in {"money_not_shown", "unit_price_summed"})
        ]
    )
