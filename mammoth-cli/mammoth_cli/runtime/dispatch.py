"""The one use-case entry point: run a command and return its outcome as a value.

Every surface (the terminal, ``mammoth run`` lines, ``embed.invoke``) runs a command
through :func:`dispatch`. It never prints and never raises ``typer.Exit``: the surface
that called it renders the :class:`Outcome` and decides how to exit
(:func:`mammoth_cli.runtime.executor.run` is the terminal's adapter). See
``docs/adr/0001-ver3-architecture.md``.

The steps around a command's handler are interceptors (Chain of Responsibility): each
takes the request and the rest of the chain, and may refuse, wrap or follow it. An
interceptor raises to refuse; :func:`dispatch` turns whatever was raised into a failed
outcome, so the error shape is the same whichever step refused.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import typer

from mammoth_cli.errors.envelope import (
    CODE_WORKSPACE_MISMATCH,
    EXIT_API,
    EXIT_AUTH,
    EXIT_PARTIAL,
    EXIT_USAGE,
    CliError,
    cancelled_error,
    feature_unavailable_error,
    is_feature_unavailable,
    not_available_embedded_error,
    pending_server_release_error,
)
from mammoth_cli.manifest.loader import is_pending_server_release
from mammoth_cli.output.policy import VALID_OUTPUTS
from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.dryrun import refuse_unsupported_dry_run
from mammoth_cli.runtime.intent_only import refuse_hand_crafted_write
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.local_paths import local_path_commands
from mammoth_cli.runtime.shared import shared_services
from mammoth_cli.services.mapping import map_sdk_exception, running_handle

# Commands that act on the host machine (login, config, installs, upgrade); an
# embedded call has no profile, keyring or shell to act on.
EMBEDDED_UNAVAILABLE = frozenset(
    {
        "auth.login",
        "auth.logout",
        "config.set",
        "upgrade",
        "skill.install",
        "skill.uninstall",
        "skill.update",
        "skill.agents-md.install",
        "completion.install",
        # Reads a JSON Lines file or the host's stdin.
        "run",
        # Read or write the host's profile, run log or install state.
        "auth.status",
        "config.get",
        "config.list",
        "config.path",
        "log.path",
        "log.tail",
        "history.list",
        "history.show",
        "history.undo",
        "history.resume",
        # Streams JSON Lines to stdout and reads files on the host, like ``run``.
        "recipe.run",
        "skill.list",
        "skill.path",
        # Write a path on the host's filesystem. The commands that read one are not
        # listed: ``local_path_commands`` derives them from the manifest.
        "view.explore-panel.export-image",
        "support.template.export",
        "support.template.export-dashboard",
    }
)


def _refuse_if_removed(command_id: str) -> None:
    if is_feature_unavailable(command_id):
        raise feature_unavailable_error(command_id)


def _refuse_if_embedded(command_id: str) -> None:
    # A hand-crafting dashboard write that also reads a local file keeps its own, more
    # useful refusal (it names the intent commands to use instead).
    refuse_hand_crafted_write(command_id)
    if embedded.active() and (
        command_id in EMBEDDED_UNAVAILABLE or command_id in local_path_commands()
    ):
        raise not_available_embedded_error(command_id.replace(".", " "))


def _refuse_if_pending(command_id: str) -> None:
    if embedded.hides_pending() and is_pending_server_release(command_id):
        raise pending_server_release_error(command_id.replace(".", " "))


def _profile_scope_recovery(error: CliError, profile: str | None) -> CliError:
    """Add the selected profile to concrete recovery commands exactly once."""
    if not profile:
        return error
    # Profile names are admitted as ``[A-Za-z0-9][A-Za-z0-9._-]{0,63}``, so
    # this argv fragment is portable across POSIX shells and PowerShell.
    profile_option = f" --profile {profile}"
    error.recovery_commands = [
        f"{command}{profile_option}" if " --profile " not in command else command
        for command in error.recovery_commands
    ]
    return error


def _validate_output(output: str) -> None:
    """Reject an unsupported ``--output`` mode before any work is done.

    Validating up front means an invalid mode fails with a clean usage error
    instead of running the producer (and its network calls) and then crashing
    in the renderer.

    Args:
        output: The requested output mode.

    Raises:
        CliError: ``invalid_output_mode`` with :data:`EXIT_USAGE` when the mode
            is not one the renderer supports.
    """
    if output not in VALID_OUTPUTS:
        raise CliError(
            code="invalid_output_mode",
            message=f"Unsupported output mode '{output}'.",
            exit_status=EXIT_USAGE,
            hint=f"Use one of: {', '.join(VALID_OUTPUTS)}.",
        )


#: Error codes that mean "the --input document was wrong": the envelope then
#: carries the command's input contract so the next call needs no ``schema get``.
_INPUT_REJECTION_CODES = frozenset(
    {
        "unknown_input_field",
        "invalid_input_field_type",
        "missing_field",
        "invalid_input",
        "invalid_input_document",
        "invalid_arguments",
        "invalid_condition",
        "invalid_condition_value",
        "invalid_rule",
    }
)


def _attach_input_contract(error: CliError, command_id: str) -> None:
    """Add ``details["input_contract"]`` to an input-validation error, once."""
    if error.code not in _INPUT_REJECTION_CODES or "input_contract" in error.details:
        return
    from mammoth_cli.commands.schema import input_contract

    contract = input_contract(command_id)
    if contract is not None:
        error.details["input_contract"] = contract


def _with_workspace_checked(error: CliError) -> CliError:
    """Check an embedded token login's workspace hint against the server after a refusal.

    A hint saves the workspace lookup on every call, but a wrong one sends each request
    to another workspace's urls, which the server refuses (a 401 "Invalid token" or a
    403). Only then is the token's own workspace asked for (once per process, the SDK
    keeps the answer), and a different one turns the refusal into ``workspace_mismatch``.
    """
    call = embedded.current()
    if call is None or error.exit_status != EXIT_AUTH:
        return error
    login = call.login
    if login.api_token is None or login.workspace_id is None:
        return error
    from mammoth_cli.context.endpoint import resolve_base_url
    from mammoth_cli.context.resolver import resolve_token_workspace

    try:
        actual = resolve_token_workspace(
            resolve_base_url(login.server_prefix), login.api_token, None
        )
    except CliError:
        return error
    if actual == login.workspace_id:
        return error
    return CliError(
        code=CODE_WORKSPACE_MISMATCH,
        message=(
            f"The login names workspace {login.workspace_id}, but its token belongs to "
            f"workspace {actual}."
        ),
        exit_status=EXIT_AUTH,
        hint="Pass the token's own workspace id, or leave workspace_id out of the login.",
        details={"workspace_id": login.workspace_id, "token_workspace_id": actual},
        request_id=error.request_id,
    )


def _with_pin_checked(error: CliError, invocation: Invocation | None) -> CliError:
    """Make a 403's "project-limited token" hint true for this token (one lookup, 403 only)."""
    checked = _with_workspace_checked(error)
    if checked is not error or invocation is None:
        return checked

    names: dict[int, str | None] = {}

    def lookup() -> tuple[int, ...] | None:
        from mammoth_cli.runtime.session import open_service
        from mammoth_cli.runtime.token_scope import pin_names, pinned_projects

        with open_service(invocation) as (service, auth):
            # A refusal is the moment to check the real pin, not a cached answer.
            pins = pinned_projects(service, auth, profile=invocation.profile, refresh=True)
            # Same session: the names cost one more read each, never a second login.
            names.update(pin_names(service, pins))
            return pins

    from mammoth_cli.runtime.token_scope import qualify_pin_hint

    return qualify_pin_hint(error, lookup, names.get)


def verify_exit_status(data: Any) -> int:
    """Exit code for a write whose read-back says it did not take effect.

    ``verify.outcome`` ``failed`` exits 1 and ``partial`` exits 3; the envelope
    is still printed so the caller can read what happened.

    Args:
        data: A command's result.

    Returns:
        The exit status the read-back calls for, or 0.
    """
    verify = data.get("verify") if isinstance(data, dict) else None
    outcome = verify.get("outcome") if isinstance(verify, dict) else None
    if outcome == "failed":
        return EXIT_API
    if outcome == "partial":
        return EXIT_PARTIAL
    return 0


@dataclass(frozen=True)
class Request:
    """One command call, as every surface hands it to :func:`dispatch`.

    Attributes:
        command_id: The manifest command id (dotted form).
        output: The requested ``--output`` mode.
        producer: Runs the command's handler (see :data:`Producer`).
        invocation: The parsed call, when the command has one (bespoke commands may not).
        profile: The active profile name, if any.
    """

    command_id: str
    output: str
    producer: Producer
    invocation: Invocation | None = None
    profile: str | None = None


@dataclass
class Outcome:
    """What a command did, before any surface renders it.

    A success has ``error`` None; ``data`` and ``meta`` become the success envelope.
    A failure has ``error`` set, and ``cause`` when an unexpected exception was mapped.

    Attributes:
        data: The result payload.
        meta: Envelope metadata (``profile``, ``workspace_id``, ``pagination``, ...).
        exit_status: The status the command ends with (0, or a failed read-back's).
        streamed: The command printed its own envelopes (``run``); render none.
        running: A wait ran out under ``--return-running``; ``data`` is the handle.
        error: The classified error of a failed command.
        cause: The unexpected exception behind ``error``, for ``--debug`` and the run log.
    """

    data: Any = None
    meta: dict[str, Any] = field(default_factory=dict)
    exit_status: int = 0
    streamed: bool = False
    running: bool = False
    error: CliError | None = None
    cause: BaseException | None = None

    @property
    def ok(self) -> bool:
        """Whether the command succeeded; a failed read-back is still a success to render."""
        return self.error is None


#: Runs a command's handler. It returns ``(data, meta_extra)``, or an :class:`Outcome` when
#: the handler names its own exit status or printed its own envelopes (``run``).
Producer = Callable[[], tuple[Any, dict[str, Any]] | Outcome]
Next = Callable[[Request], Outcome]
Interceptor = Callable[[Request, Next], Outcome]


def check_output(request: Request, call_next: Next) -> Outcome:
    """Refuse an unsupported ``--output`` mode before any work is done."""
    _validate_output(request.output)
    return call_next(request)


def refuse_unavailable(request: Request, call_next: Next) -> Outcome:
    """Refuse a removed command, a host-only command when embedded, or a pending one."""
    _refuse_if_removed(request.command_id)
    _refuse_if_embedded(request.command_id)
    _refuse_if_pending(request.command_id)
    return call_next(request)


def gate_dry_run(request: Request, call_next: Next) -> Outcome:
    """Refuse ``--dry-run`` on a command that cannot preview its effect."""
    if request.invocation is not None and request.invocation.dry_run:
        refuse_unsupported_dry_run(request.command_id)
    return call_next(request)


def share_services(request: Request, call_next: Next) -> Outcome:
    """Let every service the handler opens share one login and connection."""
    with shared_services():
        return call_next(request)


def call_handler(request: Request) -> Outcome:
    """The end of the chain: run the handler and read its exit status from the result.

    Whatever the handler raises comes back as a failed outcome, so every interceptor
    sees the handler's result as a value (the journal records a failed write too).
    """
    try:
        result = request.producer()
    except (Exception, KeyboardInterrupt) as exc:
        return contained(request, exc)
    if isinstance(result, Outcome):
        return result
    data, meta_extra = result
    return Outcome(data=data, meta=meta_extra, exit_status=verify_exit_status(data))


#: The steps around every handler, outermost first.
INTERCEPTORS: tuple[Interceptor, ...] = (
    check_output,
    refuse_unavailable,
    gate_dry_run,
    share_services,
)


def _chain(interceptors: Sequence[Interceptor], last: Next) -> Next:
    call = last
    for interceptor in reversed(interceptors):
        call = _bind(interceptor, call)
    return call


def _bind(interceptor: Interceptor, call_next: Next) -> Next:
    return lambda request: interceptor(request, call_next)


def dispatch(request: Request, interceptors: Sequence[Interceptor] = INTERCEPTORS) -> Outcome:
    """Run one command through the interceptors and its handler.

    Args:
        request: The command call.
        interceptors: The steps around the handler, outermost first.

    Returns:
        The outcome. Every error is in it: this function only raises ``SystemExit``
        and ``BaseException``s that are not ``KeyboardInterrupt``.
    """
    try:
        return _chain(interceptors, call_handler)(request)
    except (Exception, KeyboardInterrupt) as exc:
        return contained(request, exc)


def contained(request: Request, exc: BaseException) -> Outcome:
    """The outcome of a command that raised ``exc``.

    A wait that ran out under ``--return-running`` is a success that hands back the job
    to resume; anything else is a failure (:func:`failure`).

    Args:
        request: The command call that raised.
        exc: What it raised.

    Returns:
        The outcome to render.
    """
    invocation = request.invocation
    if isinstance(exc, CliError) and invocation is not None and invocation.return_running:
        running = running_handle(exc, request.command_id)
        if running is not None:
            meta = {"profile": request.profile, **(invocation.read_meta or {})}
            return Outcome(data=running, meta=meta, running=True)
    return failure(request, exc)


def failure(request: Request, exc: BaseException) -> Outcome:
    """Classify an exception raised while running or rendering ``request``.

    Args:
        request: The command call that raised.
        exc: What it raised.

    Returns:
        A failed outcome whose error carries the recovery a caller can act on.
    """
    profile = request.profile
    cause: BaseException | None = None
    if isinstance(exc, CliError):
        error = _with_pin_checked(exc, request.invocation)
    elif isinstance(exc, KeyboardInterrupt):
        # Polling can be interrupted after a job handle was observed.  Keep
        # that handle when an SDK exception exposes one; never turn Ctrl-C
        # into a successful/empty result or a Python traceback.
        error = _profile_scope_recovery(map_sdk_exception(exc), profile)
    elif isinstance(exc, typer.Abort):
        # Ctrl-C, EOF or an unusable answer at any prompt: a clean cancel, not
        # an unexpected failure.
        error = cancelled_error()
    else:
        # Bespoke handlers should normally cross the SDK service seam, but a
        # malformed response or filesystem fault must still obey the same
        # machine envelope rather than leaking an implementation traceback.
        error = _with_pin_checked(
            _profile_scope_recovery(map_sdk_exception(exc), profile), request.invocation
        )
        cause = exc
    _attach_input_contract(error, request.command_id)
    return Outcome(error=error, cause=cause, exit_status=error.exit_status)
