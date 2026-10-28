"""Usage errors explained: an unknown command, option or missing argument, with the fix."""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Sequence
from functools import cache
from typing import TYPE_CHECKING, Any

from typer._click import exceptions as _typer_click_exceptions

from mammoth_cli.app.options import (
    _shared_option_params,
)
from mammoth_cli.app.tree import _command_records, _command_tree
from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.policy import (
    OUTPUT_AUTO,
    SELECTABLE_OUTPUTS,
    canonical_output,
    resolve_output,
)
from mammoth_cli.services.positionals import resolve_positionals

if TYPE_CHECKING:
    pass


# Typer (pinned >=0.27,<0.28) ships a *vendored* click fork (``typer._click``)
# and does NOT depend on the external ``click`` package. Command resolution
# raises that fork's ``UsageError``/``Abort``, so the interceptor keys on the
# vendored classes only -- importing the external ``click`` here would add a
# phantom dependency that is absent from a clean wheel install.
_USAGE_ERRORS: tuple[type[BaseException], ...] = (_typer_click_exceptions.UsageError,)


_abort_type = getattr(_typer_click_exceptions, "Abort", None)


_ABORT_ERRORS: tuple[type[BaseException], ...] = (
    (_abort_type,) if isinstance(_abort_type, type) else ()
)


# Raised by a group invoked with no subcommand (``no_args_is_help``). Click has
# already printed the help text by then, so it carries a deliberately *empty*
# message -- which would reach an agent as a ``usage_error`` saying nothing.
_NO_ARGS_ERROR: type[BaseException] | None = getattr(
    _typer_click_exceptions, "NoArgsIsHelpError", None
)


_NO_SUCH_COMMAND = re.compile(r"No such command '(?P<name>[^']*)'")


def _output_mode_from_argv(argv: Sequence[str] | None) -> str:
    """Recover the requested ``--output`` mode from raw argv tokens.

    Used when a Click ``UsageError`` is raised *before* the per-command option
    is parsed (an unknown command, an unexpected argument, a bad option value),
    so the top-level error renderer can still honor the machine-output contract.
    Defaults to the same ``auto`` default the ``--output`` option declares, then
    resolves it against whether stdout is a terminal — so a piped invocation
    gets the machine envelope even for an error raised before option parsing.
    """
    tokens = list(argv) if argv is not None else sys.argv[1:]
    mode = OUTPUT_AUTO
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in ("--output", "-o"):
            if index + 1 < len(tokens):
                mode = tokens[index + 1]
            index += 2
            continue
        if token.startswith("--output="):
            mode = token.split("=", 1)[1]
        elif token.startswith("-o") and len(token) > 2:
            mode = token[2:]
        index += 1
    mode = canonical_output(mode)
    if mode == OUTPUT_AUTO:
        # ``MAMMOTH_OUTPUT`` is the session default an agent exports once; honour it here too.
        requested = canonical_output(os.environ.get("MAMMOTH_OUTPUT", "").strip().lower())
        if requested in SELECTABLE_OUTPUTS:
            mode = requested
    if mode not in SELECTABLE_OUTPUTS:
        # A value the command would reject (``--output xml``) must not turn the
        # error into prose: judge it by where stdout goes, like the default.
        mode = OUTPUT_AUTO
    return resolve_output(mode, is_tty=sys.stdout.isatty())


def _unknown_flag_in(error: Any, tokens: Sequence[str]) -> str | None:
    """The first ``--flag`` in ``tokens`` that neither a global option nor the command declares."""
    known, _valued = _global_option_flags()
    command = getattr(getattr(error, "ctx", None), "command", None)
    known = known | {
        flag
        for param in getattr(command, "params", [])
        for flag in (*param.opts, *param.secondary_opts)
    }
    return next(
        (
            token.split("=", 1)[0]
            for token in tokens
            if token.startswith("--") and token.split("=", 1)[0] not in known
        ),
        None,
    )


@cache
def _global_option_flags() -> tuple[frozenset[str], frozenset[str]]:
    """Return every global option spelling, and the subset that takes a value.

    Derived from :func:`_shared_option_params` so the two stay in lockstep: a
    global option added there is recognized here without a second edit. Typer
    stores the first declaration string in ``default`` and any alias in
    ``param_decls``, so both are collected.
    """
    every: set[str] = set()
    valued: set[str] = set()
    for param in _shared_option_params():
        decls: list[str] = []
        for meta in getattr(param.annotation, "__metadata__", ()):
            first = getattr(meta, "default", None)
            if isinstance(first, str) and first.startswith("-"):
                decls.append(first)
            decls.extend(d for d in getattr(meta, "param_decls", None) or () if d.startswith("-"))
        if not decls:
            continue
        every.update(decls)
        # A boolean flag takes no value, so it must not swallow the next token
        # when the corrected command line is rebuilt.
        if getattr(param.annotation, "__origin__", None) is not bool:
            valued.update(decls)
    return frozenset(every), frozenset(valued)


def missing_argument_hint(tokens: Sequence[str]) -> str:
    """The command's usage line and runnable example, for a ``missing_argument`` error.

    The command is the longest run of leading words that names one; with none, the
    generic pointer to the schema.
    """
    generic = "Check the command schema with 'mammoth schema get'."
    path_to_command, _ = _command_tree()
    words = [token for token in tokens if not token.startswith("-")]
    for length in range(len(words), 0, -1):
        command_id = path_to_command.get(tuple(words[:length]))
        if command_id is None:
            continue
        slots = " ".join(
            spec.metavar if spec.required else f"[{spec.metavar}]"
            for spec in resolve_positionals(command_id)
        )
        usage = " ".join(part for part in ("mammoth", *words[:length], slots) if part)
        example = (command_by_id(command_id) or {}).get("agent_example")
        return f"Usage: {usage}." + (f" Example: {example}" if example else "")
    return generic


def _corrected_command(tokens: Sequence[str]) -> str | None:
    """Rebuild an invocation with leading global options moved after the command.

    ``mammoth --profile prod doctor`` becomes ``mammoth doctor --profile prod``.
    Returns None when there is nothing to move or nothing to move it behind.
    """
    every, valued = _global_option_flags()
    leading: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        name = token.split("=", 1)[0]
        if name not in every:
            break
        leading.append(token)
        index += 1
        if "=" not in token and name in valued and index < len(tokens):
            leading.append(tokens[index])
            index += 1
    rest = list(tokens[index:])
    if not leading or not rest:
        return None
    return " ".join(["mammoth", *rest, *leading])


def _parent_words(context: Any) -> list[str]:
    """The command words above an unknown one, without the program name."""
    words: list[str] = []
    while context is not None and getattr(context, "parent", None) is not None:
        words.insert(0, str(context.info_name))
        context = context.parent
    return words


def _unknown_command_report(error: Any) -> CliError | None:
    """``No such command 'X'``: name the nearest commands and the discovery commands."""
    from mammoth_cli.services.suggest import DISCOVERY_HINT, command_suggestions

    match = _NO_SUCH_COMMAND.search(error.format_message() or "")
    if match is None or match.group("name").startswith("-"):
        return None
    name = match.group("name")
    parent = _parent_words(getattr(error, "ctx", None))
    paths = [str(record["command_path"]).split() for record in _command_records()]
    suggestions = command_suggestions(parent, name, paths)
    where = f" under 'mammoth {' '.join(parent)}'" if parent else ""
    message = f"No such command '{name}'{where}."
    if suggestions:
        message += f" Did you mean: {', '.join(suggestions)}?"
    goal = name.replace('"', "")
    return CliError(
        code="usage_error",
        message=message,
        exit_status=EXIT_USAGE,
        hint=DISCOVERY_HINT,
        details={"command": name, "did_you_mean": suggestions},
        recovery_commands=[
            *(f"{suggestion} --help" for suggestion in suggestions[:2]),
            f'mammoth how "{goal}"',
            f'mammoth schema find "{goal}"',
        ],
    )


def _unknown_option_report(error: Any, option: str) -> CliError:
    """An unknown ``--option``: name the nearest valid one (global or the command's own)."""
    from mammoth_cli.services.suggest import option_suggestion

    command = getattr(getattr(error, "ctx", None), "command", None)
    known = set(_global_option_flags()[0]) | {
        flag
        for param in getattr(command, "params", [])
        for flag in (*param.opts, *param.secondary_opts)
    }
    suggestion = option_suggestion(option, sorted(known))
    close = sorted(getattr(error, "possibilities", None) or [])
    if suggestion is None and close:
        # Click's own guess also catches a prefix ('--server' for '--server-prefix').
        suggestion = {"flag": close[0], "hint": f"Did you mean {' or '.join(close)}?"}
    details: dict[str, Any] = {"option": option}
    if suggestion is not None:
        details["did_you_mean"] = suggestion["flag"]
    return CliError(
        code="unknown_option",
        message=f"Unknown option '{option}'.",
        exit_status=EXIT_USAGE,
        hint=(
            suggestion["hint"]
            if suggestion is not None
            else "Run the command with --help to list its options."
        ),
        details=details,
    )


def _usage_error_report(error: Any, tokens: Sequence[str]) -> CliError | None:
    """Classify a usage error whose own Click message is empty or misleading.

    Returns None when Click's message already reads well, so the generic
    ``usage_error`` envelope and Click's own human rendering are kept.
    """
    if _NO_ARGS_ERROR is not None and isinstance(error, _NO_ARGS_ERROR):
        context = getattr(error, "ctx", None)
        path = getattr(context, "command_path", None) or "mammoth"
        # The root group is the one with no parent context; the program name
        # itself can contain spaces (``python -m mammoth_cli``), so it is not a
        # reliable signal.
        is_root = context is not None and getattr(context, "parent", None) is None
        subject = "command" if is_root else "subcommand"
        # No recovery command: the caller has to choose a command, and there is
        # no single runnable one to replay. The message and hint carry it.
        return CliError(
            code="usage_error",
            message=f"No {subject} given for '{path}'.",
            exit_status=EXIT_USAGE,
            hint=f"Run '{path} --help' to list the available {subject}s.",
            details={"command_path": path},
        )

    match = _NO_SUCH_COMMAND.search(error.format_message() or "")
    if match is None:
        return None
    name = match.group("name").split("=", 1)[0]
    if not name.startswith("-"):
        return _unknown_command_report(error)
    if name not in _global_option_flags()[0]:
        return None
    # Only leaf commands declare the global options, so a group reads one as a
    # subcommand name and reports a misleading "No such command '--profile'".
    context = getattr(error, "ctx", None)
    path = getattr(context, "command_path", None) or "mammoth"
    if context is not None and getattr(context, "parent", None) is not None:
        # The option sits after a group that still needs a subcommand.
        return CliError(
            code="usage_error",
            message=f"'{path}' is a command group; it needs a subcommand before '{name}'.",
            exit_status=EXIT_USAGE,
            hint=f"Run '{path} --help' to list its subcommands.",
            details={"option": name, "command_path": path},
        )
    corrected = _corrected_command(tokens)
    return CliError(
        code="usage_error",
        message=f"Global option '{name}' must come after the command, not before it.",
        exit_status=EXIT_USAGE,
        hint=(
            f"Try: {corrected}"
            if corrected
            else "Every command declares the global options itself, so they follow the command."
        ),
        details={"option": name},
        recovery_commands=[corrected] if corrected else [],
    )
