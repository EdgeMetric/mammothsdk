"""Central validation for global options and resource-identifier positionals.

Two classes of value are never validated by Click/Typer parsing itself, and so
were reaching confirmation and the network unchecked:

* the global options every command shares — ``--project``, ``--color``, and
  the ``--timeout``/``--job-timeout``/``--pipeline-timeout`` family (see
  :func:`validate_invocation`);
* the positional resource ids a command's own signature identifies — a
  workspace, project, job, or view id (see :func:`validate_positional_ids`),
  driven by the same derived positional shape used for the surplus-argument
  check in :mod:`mammoth_cli.runtime.strict`.

Both run in ``app._execute`` before a handler is dispatched, so a bad id or
option fails with a clean usage error before any confirmation prompt or
network call rather than reaching the SDK as ``0``, a negative number, or a
silently-ignored typo.
"""

from __future__ import annotations

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.output.policy import COLOR_MODES
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.services.positionals import resolve_positionals

CODE_INVALID_OPTION_VALUE = "invalid_option_value"

# The invocation's timeout-family fields, paired with the CLI flag that sets
# each, in the order they should be checked.
_TIMEOUT_OPTIONS = (
    ("timeout", "--timeout"),
    ("job_timeout", "--job-timeout"),
    ("pipeline_timeout", "--pipeline-timeout"),
)


def _invalid_option_error(option: str, message: str, *, details: dict[str, object]) -> CliError:
    return CliError(
        code=CODE_INVALID_OPTION_VALUE,
        message=message,
        exit_status=EXIT_USAGE,
        hint=f"Check the value passed to {option}.",
        details=details,
    )


def validate_invocation(invocation: Invocation) -> None:
    """Validate the global options shared by every command.

    Args:
        invocation: The fully parsed invocation, before any confirmation
            prompt or network call.

    Raises:
        CliError: ``invalid_option_value`` with :data:`EXIT_USAGE` when
            ``--project`` is not a positive integer, ``--color`` is not one of
            :data:`mammoth_cli.output.policy.COLOR_MODES`, or a timeout option
            is not a positive number.
    """
    if invocation.project is not None and invocation.project <= 0:
        raise _invalid_option_error(
            "--project",
            f"--project must be a positive integer, got {invocation.project}.",
            details={"option": "project", "value": invocation.project},
        )

    if invocation.color not in COLOR_MODES:
        raise _invalid_option_error(
            "--color",
            f"--color must be one of {', '.join(COLOR_MODES)}; got '{invocation.color}'.",
            details={"option": "color", "value": invocation.color, "allowed": list(COLOR_MODES)},
        )

    for field_name, option in _TIMEOUT_OPTIONS:
        value = getattr(invocation, field_name)
        if value is not None and value <= 0:
            raise _invalid_option_error(
                option,
                f"{option} must be a positive number, got {value}.",
                details={"option": field_name, "value": value},
            )


def validate_positional_ids(command_id: str, extra_args: list[str]) -> None:
    """Validate that each int-typed positional token is a positive integer.

    Aligns the command's derived positionals (workspace/project/job/view ids
    and the like — see
    :func:`mammoth_cli.services.positionals.resolve_positionals`) with the
    supplied tokens by position, and checks only the ``int``-typed slots: a
    ``str``-typed positional (a project name, for example) is never a numeric
    id and is left untouched.

    Args:
        command_id: The manifest command id being invoked.
        extra_args: The trailing positional tokens Typer collected.

    Raises:
        CliError: ``invalid_option_value`` with :data:`EXIT_USAGE` when an
            int-typed positional is not a positive integer.
    """
    positionals = resolve_positionals(command_id)
    for spec, token in zip(positionals, extra_args, strict=False):
        if spec.type is not int:
            continue
        try:
            value = int(token)
        except ValueError:
            raise _invalid_option_error(
                spec.metavar,
                f"'{spec.name}' must be a positive integer, got '{token}'.",
                details={"argument": spec.name, "value": token},
            ) from None
        if value <= 0:
            raise _invalid_option_error(
                spec.metavar,
                f"'{spec.name}' must be a positive integer, got {value}.",
                details={"argument": spec.name, "value": value},
            )
