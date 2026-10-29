"""The options every generated command takes, and its positional parameters."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Annotated, Any

import typer

from mammoth_cli import __version__
from mammoth_cli.output.policy import (
    COLOR_MODES,
    OUTPUT_AUTO,
    SELECTABLE_OUTPUTS,
    VALID_OUTPUTS,
)
from mammoth_cli.services.positional_spec import PositionalSpec

if TYPE_CHECKING:
    pass


OUTPUT_MODES = VALID_OUTPUTS


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit(0)


def _shared_option_params() -> list[inspect.Parameter]:
    """Build the global-option parameters shared by every command.

    These are the machine-output and agent-mode options every command exposes.
    They are declared once, as :class:`inspect.Parameter`s, so a dynamically
    synthesized command signature can splice them in after any positionals while
    keeping the option contract in exactly one place.
    """
    p = inspect.Parameter

    def opt(name: str, default: Any, annotation: Any) -> inspect.Parameter:
        return p(name, p.POSITIONAL_OR_KEYWORD, default=default, annotation=annotation)

    return [
        opt(
            "output",
            OUTPUT_AUTO,
            Annotated[
                str,
                typer.Option(
                    "--output",
                    "-o",
                    help="Output format. 'auto' picks a table on a terminal, JSON when piped.",
                    metavar="|".join(SELECTABLE_OUTPUTS),
                    rich_help_panel="Output and automation",
                ),
            ],
        ),
        opt(
            "profile",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--profile",
                    help="Credential profile name.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "project",
            None,
            Annotated[
                int | None,
                typer.Option(
                    "--project",
                    help="Active project id override.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "session",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--session",
                    help="Agent chat session id for 'agent action' and 'agent run' commands.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "timeout",
            None,
            Annotated[
                float | None,
                typer.Option(
                    "--timeout",
                    help="Per-request timeout seconds.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "job_timeout",
            None,
            Annotated[
                float | None,
                typer.Option(
                    "--job-timeout",
                    help="Job wait timeout seconds.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "return_running",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--return-running",
                    help=(
                        "When a job or pipeline wait runs out, exit 0 with "
                        "{status: running, job_id or dataview_id, resume} instead of a "
                        "timeout error; resume with 'mammoth job wait JOB_ID' "
                        "(reports success, failure or still running; waits at most "
                        "15 minutes by default)."
                    ),
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "pipeline_timeout",
            None,
            Annotated[
                float | None,
                typer.Option(
                    "--pipeline-timeout",
                    help="Pipeline wait timeout seconds.",
                    rich_help_panel="Context and timeouts",
                ),
            ],
        ),
        opt(
            "color",
            "auto",
            Annotated[
                str,
                typer.Option(
                    "--color",
                    help="Color policy.",
                    metavar="|".join(COLOR_MODES),
                    rich_help_panel="Output and automation",
                ),
            ],
        ),
        opt(
            "no_input",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--no-input",
                    help="Never prompt; fail instead.",
                    rich_help_panel="Output and automation",
                ),
            ],
        ),
        opt(
            "no_progress",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--no-progress",
                    help="Never render progress.",
                    rich_help_panel="Output and automation",
                ),
            ],
        ),
        opt(
            "debug",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--debug",
                    help="Emit diagnostic detail to stderr.",
                    rich_help_panel="Output and automation",
                ),
            ],
        ),
        opt(
            "yes",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--yes",
                    "-y",
                    help="Confirm a mutation without prompting.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "confirm",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--confirm",
                    help="Exact target name required for high-impact actions.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "dry_run",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--dry-run",
                    help="Resolve and validate, then report the request instead of sending it.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "allow_empty",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--allow-empty",
                    help="Add a keep filter that matches no row; without it the dry run fails.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "overwrite",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--overwrite",
                    help="Replace a local file the command writes to when it already exists.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "standing",
            False,
            Annotated[
                bool,
                typer.Option(
                    "--standing",
                    help="Stage a step that changes no row today, as a rule for future data.",
                    rich_help_panel="Safety",
                ),
            ],
        ),
        opt(
            "input_file",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--input",
                    help="Strict JSON/YAML request document, or '-' for stdin.",
                    rich_help_panel="Request input",
                ),
            ],
        ),
        opt(
            "input_format",
            None,
            Annotated[
                str | None,
                typer.Option(
                    "--input-format",
                    help="Required for stdin: json or yaml.",
                    rich_help_panel="Request input",
                ),
            ],
        ),
    ]


_SHARED_OPTION_PARAMS = _shared_option_params()


def _positional_param(spec: PositionalSpec) -> inspect.Parameter:
    """Build a Typer ``Argument`` parameter for one positional spec.

    The argument is declared with the spec's native scalar type (``int`` or
    ``str``) and its native requiredness, so ``--help`` shows the truth: a
    required id renders as ``DATASET_ID`` / ``<int>`` (not an optional
    ``[DATASET_ID]`` / ``<str>``) and Typer enforces both presence and type at
    parse time. A missing or ill-typed *required* positional raises a Click-layer
    usage error that :class:`_EnvelopeGroup` renders as the stable JSON envelope
    under a machine ``--output`` (``missing_argument`` for an absent one,
    ``usage_error`` for a bad value), preserving the machine error contract. An
    *optional* positional keeps a ``None`` default and an ``Optional`` annotation;
    the handler fills it from ``--input`` or resolved context when omitted.
    """
    if spec.required:
        return inspect.Parameter(
            spec.name,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Annotated[spec.type, typer.Argument(help=spec.help, metavar=spec.metavar)],
        )
    return inspect.Parameter(
        spec.name,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default=None,
        annotation=Annotated[
            spec.type | None, typer.Argument(help=spec.help, metavar=spec.metavar)
        ],
    )
