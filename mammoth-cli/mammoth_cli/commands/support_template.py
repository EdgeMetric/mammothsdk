"""``support template``: staff commands that curate the dashboard template gallery."""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.commands.support import (
    _bound_document,
    _confirm,
    _forward_optional,
    _meta,
    _require_field,
    _require_int_positional,
    _symbol,
)
from mammoth_cli.errors.envelope import (
    CODE_MISSING_ARGUMENT,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.runtime.confirm import (
    POLICY_YES_ALWAYS,
    enforce_confirmation,
)
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.session import open_service
from mammoth_cli.services.local_files import refuse_existing_file

# -- Curated template catalog (dashboards v3 admin) ---------------------------------
#
# Every route refuses a caller without a Mammoth staff (platform-admin) role, and
# acts on CURATED templates only. The help line of each command says so first.


def _require_text_positional(invocation: Invocation, name: str, human: str) -> str:
    """Return a required string positional by its declared name, or raise usage."""
    value = invocation.positional(name)
    if not value:
        raise CliError(
            code=CODE_MISSING_ARGUMENT,
            message=f"A {human} is required.",
            exit_status=EXIT_USAGE,
            hint=f"Pass the {human} as a positional argument.",
        )
    return str(value)


def _template_read(invocation: Invocation) -> HandlerResult:
    """Call a slug-addressed read of the curated catalog."""
    slug = _require_text_positional(invocation, "slug", "template slug")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), slug=slug)
    return data, _meta(invocation, auth.workspace_id)


def _template_write(invocation: Invocation, verb: str) -> HandlerResult:
    """Call a slug-addressed write of the curated catalog after ``--confirm SLUG``."""
    slug = _require_text_positional(invocation, "slug", "template slug")
    _confirm(invocation, action=f"{verb} curated template '{slug}'", target=slug)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), slug=slug)
    return data, _meta(invocation, auth.workspace_id)


def support_template_list(invocation: Invocation) -> HandlerResult:
    """Platform admin only: list every curated template, drafts and faults first."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_template_edit(invocation: Invocation) -> HandlerResult:
    """Platform admin only: edit a curated template's filing ('changes' from '--input')."""
    slug = _require_text_positional(invocation, "slug", "template slug")
    document = _bound_document(invocation)
    changes = _require_field(document, "changes")
    _confirm(invocation, action=f"edit curated template '{slug}'", target=slug)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), slug=slug, changes=changes)
    return data, _meta(invocation, auth.workspace_id)


def support_template_data_preview(invocation: Invocation) -> HandlerResult:
    """Platform admin only: read up to 50 rows of the data a curated template opens on."""
    return _template_read(invocation)


def support_template_canvas(invocation: Invocation) -> HandlerResult:
    """Platform admin only: read a curated template's canvas, drafts included."""
    return _template_read(invocation)


def support_template_publish(invocation: Invocation) -> HandlerResult:
    """Platform admin only: take a curated draft live in every customer's gallery."""
    return _template_write(invocation, "publish")


def support_template_unpublish(invocation: Invocation) -> HandlerResult:
    """Platform admin only: take a live or retired curated template back to draft."""
    return _template_write(invocation, "unpublish")


def support_template_retire(invocation: Invocation) -> HandlerResult:
    """Platform admin only: retire a curated template (kept, no longer offered)."""
    return _template_write(invocation, "retire")


def support_template_thumbnail_clear(invocation: Invocation) -> HandlerResult:
    """Platform admin only: remove a curated template's picture."""
    return _template_write(invocation, "remove the picture of")


def support_template_discard(invocation: Invocation) -> HandlerResult:
    """Platform admin only: permanently remove a curated draft, its board and its data."""
    return _template_write(invocation, "discard")


def support_template_thumbnail_set(invocation: Invocation) -> HandlerResult:
    """Platform admin only: upload or replace a curated template's picture from FILE."""
    slug = _require_text_positional(invocation, "slug", "template slug")
    file_path = _require_text_positional(invocation, "file", "image file path")
    _confirm(invocation, action=f"replace the picture of curated template '{slug}'", target=slug)
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), slug=slug, file=file_path)
    return data, _meta(invocation, auth.workspace_id)


def support_template_inspect(invocation: Invocation) -> HandlerResult:
    """Platform admin only: read a template file (.zip) without importing it."""
    file_path = _require_text_positional(invocation, "file", "template file path")
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), file=file_path)
    return data, _meta(invocation, auth.workspace_id)


def support_template_import(invocation: Invocation) -> HandlerResult:
    """Platform admin only: import a template file (.zip) as a curated draft. '--yes' required."""
    file_path = _require_text_positional(invocation, "file", "template file path")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"file": file_path}
    _forward_optional(document, kwargs, ("dataset",))
    enforce_confirmation(
        invocation,
        policy=POLICY_YES_ALWAYS,
        action=f"import template file {file_path} into the curated catalog",
    )
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation), **kwargs)
    return data, _meta(invocation, auth.workspace_id)


def support_template_snapshots(invocation: Invocation) -> HandlerResult:
    """Platform admin only: list every stored dataset the template catalog holds."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_template_audit(invocation: Invocation) -> HandlerResult:
    """Platform admin only: re-run every curated-catalog gate (read-only)."""
    with open_service(invocation) as (service, auth):
        data = service.call(_symbol(invocation))
    return data, _meta(invocation, auth.workspace_id)


def support_template_export(invocation: Invocation) -> HandlerResult:
    """Platform admin only: download a curated template as a .zip template file."""
    slug = _require_text_positional(invocation, "slug", "template slug")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {"slug": slug}
    _forward_optional(document, kwargs, ("output_path", "with_data"))
    refuse_existing_file(invocation, kwargs.get("output_path") or f"{kwargs['slug']}.zip")
    with open_service(invocation) as (service, auth):
        path = service.call(_symbol(invocation), **kwargs)
    return {"output_path": str(path)}, _meta(invocation, auth.workspace_id)


def support_template_export_dashboard(invocation: Invocation) -> HandlerResult:
    """Platform admin only: download a dashboard you can edit as a .zip template file."""
    dashboard_id = _require_int_positional(invocation, "dashboard id")
    document = _bound_document(invocation)
    kwargs: dict[str, Any] = {
        "dashboard_id": dashboard_id,
        "slug": _require_field(document, "slug"),
    }
    _forward_optional(document, kwargs, ("output_path", "with_data"))
    refuse_existing_file(invocation, kwargs.get("output_path") or f"{kwargs['slug']}.zip")
    with open_service(invocation) as (service, auth):
        path = service.call(_symbol(invocation), **kwargs)
    return {"output_path": str(path)}, _meta(invocation, auth.workspace_id)
