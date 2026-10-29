"""The steps around a generic manifest command's handler.

Every command the manifest tree builds runs through :func:`producer` and the
interceptors in :data:`LEAF_INTERCEPTORS`: :func:`admit_input` checks the call before
anything is journaled or sent, and :func:`normalize_result` adds the read-backs and
hints to what the handler returned, inside the journal so its ``end`` record sees
``meta.opens``. See ``docs/adr/0001-ver3-architecture.md``, migration step 2.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.commands.registry import HANDLERS, Handler, HandlerResult
from mammoth_cli.errors.envelope import not_implemented_error
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import validate
from mammoth_cli.runtime.compact import with_compact
from mammoth_cli.runtime.confirm import refuse_mismatched_confirm
from mammoth_cli.runtime.dataset_health import with_dataset_health
from mammoth_cli.runtime.dispatch import (
    INTERCEPTORS,
    Interceptor,
    Next,
    Outcome,
    Producer,
    Request,
    contained,
    verify_exit_status,
)
from mammoth_cli.runtime.dryrun import DryRunStop
from mammoth_cli.runtime.dryrun_targets import resolve_dependents, resolve_targets
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.journal import journal_writes
from mammoth_cli.runtime.locked_files import with_locked_files
from mammoth_cli.runtime.new_data import with_new_data_path
from mammoth_cli.runtime.next_commands import with_next_commands
from mammoth_cli.runtime.opens import with_opens
from mammoth_cli.runtime.resource_ids import with_resource_ids
from mammoth_cli.runtime.session import open_service, resolved_project
from mammoth_cli.runtime.state import with_state
from mammoth_cli.runtime.strict import validate_extra_args
from mammoth_cli.runtime.verify import with_verify
from mammoth_cli.services.command_contract import S2_COMMANDS


def admit_input(request: Request, call_next: Next) -> Outcome:
    """Check a generic command's arguments and input before it is journaled or run.

    Args:
        request: The command call; one without an invocation passes through.
        call_next: The rest of the chain.

    Returns:
        The outcome of the rest of the chain.

    Raises:
        CliError: The arguments, positional ids, ``--confirm`` or ``--input`` are invalid.
    """
    invocation = request.invocation
    if invocation is not None:
        validate.validate_invocation(invocation)
        validate_extra_args(invocation.command_id, invocation.extra_args)
        validate.validate_positional_ids(invocation.command_id, invocation.extra_args)
        refuse_mismatched_confirm(invocation)
        # Admit structured input before resolving a handler or opening a service.
        # Handlers keep calling ``load_input``; it now returns this prepared value.
        invocation.prepare_input()
        # S2 API-backed families bind the admitted input to the SDK call here, even for
        # a zero-input command, so a binding defect never becomes a late network error.
        if invocation.command_id in S2_COMMANDS:
            invocation.bound_input()
    return call_next(request)


def normalize_result(request: Request, call_next: Next) -> Outcome:
    """Add the write read-backs, health notes, opened objects and next commands.

    A failure, a dry run and a command that printed its own envelopes are returned as
    they are. The exit status of a write whose read-back says it did not take effect is
    read from the final data.

    Args:
        request: The command call.
        call_next: The rest of the chain.

    Returns:
        The handler's outcome with its data and meta normalized.
    """
    outcome = call_next(request)
    invocation = request.invocation
    if outcome.error is not None or outcome.streamed or invocation is None or invocation.dry_run:
        return outcome
    try:
        checked = with_locked_files(with_dataset_health(apply_verify(invocation, outcome.data)))
        opened = with_opens(invocation, checked, outcome.meta)
        identified = with_resource_ids(invocation.command_id, checked, opened)
        meta = with_next_commands(invocation, identified, opened)
        data = with_compact(invocation, with_new_data_path(identified), meta)
    except (Exception, KeyboardInterrupt) as exc:
        # Inside the journal: the read-back failing is the command's failure, recorded.
        return contained(request, exc)
    exit_status = outcome.exit_status or verify_exit_status(data)
    return Outcome(data=data, meta=meta, exit_status=exit_status)


#: The steps around every generic command, outermost first.
LEAF_INTERCEPTORS: tuple[Interceptor, ...] = (
    *INTERCEPTORS,
    admit_input,
    journal_writes(),
    normalize_result,
)


def producer(invocation: Invocation) -> Producer:
    """The call that runs ``invocation``'s handler, or reports its request under ``--dry-run``.

    Args:
        invocation: The parsed command call.

    Returns:
        A zero-argument callable for :class:`~mammoth_cli.runtime.dispatch.Request`.
    """

    def run_handler() -> HandlerResult | Outcome:
        handler = HANDLERS.get(invocation.command_id)
        if handler is None:
            record = command_by_id(invocation.command_id)
            sdk_symbol = record.get("sdk_symbol", "") if record else ""
            raise not_implemented_error(invocation.command_id, sdk_symbol)
        if invocation.dry_run:
            return dry_run(handler, invocation)
        return handler(invocation)

    return run_handler


def apply_verify(invocation: Invocation, data: Any) -> Any:
    """Add the automatic write read-back to a real, mutating, API-backed result.

    A read command and a command with no reviewed ``sdk_symbol`` (a local or
    not-yet-backed command) are returned unchanged; ``--dry-run`` never reaches this.

    Two independent read-backs are layered on top of the raw result: ``verify``
    (status/row-count signals derived from the write's own response) and ``state`` (a
    fresh read of what the write actually produced, per the command's manifest
    ``readback``/``no_readback`` declaration, see :mod:`mammoth_cli.runtime.state`).

    Args:
        invocation: The parsed command call.
        data: The handler's result.

    Returns:
        ``data`` with ``verify`` and ``state`` added where the command declares them.
    """
    record = command_by_id(invocation.command_id) or {}
    if record.get("mutation_class") == "read" or not record.get("sdk_symbol"):
        return data
    return with_state(invocation, with_verify(data, invocation))


def dry_run(handler: Handler, invocation: Invocation) -> HandlerResult | Outcome:
    """Run ``handler`` until its request would leave; report that request.

    Local commands never open a service, so a dry run of one is the real run. An
    API-backed handler that returns normally under ``--dry-run`` made no gated SDK call
    at all (a pure read path); its result is returned as is.

    Args:
        handler: The command's handler.
        invocation: The parsed command call, with ``dry_run`` set.

    Returns:
        The request the handler would have sent, with its targets and dependents.
    """
    try:
        return handler(invocation)
    except DryRunStop as stop:
        with open_service(invocation) as (service, _auth):
            would_call = stop.record["would_call"]
            targets = resolve_targets(service, invocation.command_id, would_call)
            dependents = resolve_dependents(
                service, invocation.command_id, would_call, resolved_project(invocation)
            )
        impact = invocation.predicted_impact
        report = {**stop.record, "targets": targets}
        if dependents is not None:
            report["dependents"] = dependents
        if impact is not None:
            report["predicted_impact"] = impact
        return report, {"profile": invocation.profile, "project_id": resolved_project(invocation)}
