"""The ``run`` command: many commands, one process.

``mammoth run [FILE|-]`` reads JSON Lines, one command per line, and runs each through the
same path a single command takes (argument parsing, validation, confirmation, dry run,
handler, executor). Every process start pays for the interpreter, the credential lookup and a
new connection (DNS, TCP, TLS: about 0.65 s against the hosted API) before its first request;
here the lines share one process, one credential load, one SDK client and its connection
pool, and the warm caches.

Line schema (an object; every key but ``cmd`` is optional)::

    {"cmd": "view task list", "args": ["290"], "input": {...}, "flags": {"project": 1}}

* ``cmd``: the command path, as printed in ``meta.command`` (``"view task list"``).
* ``args``: the positional arguments, in order, as on the command line (ids may be numbers).
  A flag the command itself declares (``"--full"``) may be listed here too.
* ``input``: the ``--input`` request document, an object.
* ``flags``: global flags by long name without the dashes (``"dry-run": true``,
  ``"project": 3633``, ``"confirm": "42"``). ``yes`` and ``confirm`` belong here, on the line
  that needs them: ``run`` has no global ``--yes``. ``output``, ``input``, ``input-format``,
  ``no-input``, ``no-progress`` and ``color`` are owned by ``run``.
* ``id``: an optional string or number echoed back on that line's envelope.
* ``name``: names the line, so a later line can use its result as
  ``{{steps.<name>.data...}}`` in ``args``, ``input`` or ``flags`` (see
  :mod:`mammoth_cli.runtime.bindings`). A whole-value reference keeps its type.
* ``when``: a condition (``{"eq": [A, B]}``, ``{"in": ...}``, ``{"not": ...}``,
  ``{"all": [...]}``, ``{"any": [...]}``, ``{"present": REF}`` or a bare reference); a line
  whose condition is false is skipped with ``skipped: true``.
* ``for_each``: a reference to a list; the line runs once per item, with ``{{item}}`` and
  ``{{index}}`` in scope, and prints one envelope per item (with ``item``). Its step result
  is ``{"data": [each item's data], "exit": ...}``.

References read only from lines that ran before. A reference that does not resolve fails
the line with ``unresolved_reference``; under ``--dry-run`` the line is planned instead
(``data.planned``), since a preview makes no ids for later lines to use. No code runs: the
expressions are JSON, so a line can do no more than its command does.

Output is JSON Lines on stdout: one envelope per line, the envelope the single command
prints plus ``line`` (the physical line number), ``cmd`` and ``exit``, then a final summary
envelope (no ``line`` key). The run stops at the first failed line (the process exits with
that line's exit status); ``--continue`` runs every line and exits with the status of the
first failure. ``--dry-run``, ``--profile``, ``--project`` and the timeout flags given to
``run`` apply to every line (a line's own ``flags`` override all but ``--dry-run``).
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

from mammoth_cli.errors.envelope import (
    EXIT_API,
    EXIT_INTERRUPT,
    EXIT_PARTIAL,
    EXIT_USAGE,
    CliError,
    cancelled_error,
)
from mammoth_cli.output.emit import run_id
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.runtime import bindings, journal, linecapture
from mammoth_cli.runtime.dispatch import Outcome
from mammoth_cli.runtime.input_loader import MAX_INPUT_BYTES
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.shared import forget_reads, remembering_auth
from mammoth_cli.runtime.strict import NEGATIVE_NUMBER

HandlerResult = tuple[Any, dict[str, Any]]

CODE_INVALID_RUN_LINE = "invalid_run_line"
CODE_RUN_COMMAND_REFUSED = "run_command_refused"
CODE_RUN_INPUT_EMPTY = "run_input_empty"
CODE_RUN_TOO_LARGE = "run_input_too_large"
CODE_RUN_FLAG_REFUSED = "run_global_flag_refused"
CODE_UNRESOLVED_REFERENCE = "unresolved_reference"

#: Largest JSON Lines file ``run`` reads, and the largest single line.
MAX_RUN_BYTES = 16 * 1024 * 1024
MAX_LINE_BYTES = MAX_INPUT_BYTES

LINE_KEYS = ("cmd", "args", "input", "flags", "id", "name", "when", "for_each")
#: The keys whose values may hold ``{{...}}`` references.
BOUND_KEYS = ("args", "input", "flags")
_WORD = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_STEP_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,63}$")

#: Commands a line may not run: ``run`` itself (no nesting), and the two that read secrets
#: from stdin, which carries the lines.
REFUSED_COMMANDS: dict[str, str] = {
    "run": "run cannot run run: put the lines in one file.",
    "auth.login": "auth login reads secrets from stdin; run it on its own.",
    "auth.logout": "auth logout changes the saved credentials; run it on its own.",
}

#: Flags ``run`` sets itself on every line: machine output, no prompt, no spinner.
OWNED_FLAGS = frozenset(
    {"--output", "-o", "--no-input", "--no-progress", "--color", "--input", "--input-format"}
)

#: The global flags ``run`` was given that every line inherits: flag, then the attribute.
INHERITED_FLAGS: tuple[tuple[str, str], ...] = (
    ("--profile", "profile"),
    ("--project", "project"),
    ("--session", "session"),
    ("--timeout", "timeout"),
    ("--job-timeout", "job_timeout"),
    ("--pipeline-timeout", "pipeline_timeout"),
    ("--return-running", "return_running"),
    ("--allow-empty", "allow_empty"),
    ("--overwrite", "overwrite"),
    ("--standing", "standing"),
    ("--dry-run", "dry_run"),
    ("--debug", "debug"),
)

#: A line that changes these changes who the next line is: the credential memo is dropped.
_CREDENTIAL_GROUPS = frozenset({"auth", "config", "context"})


@dataclass
class LineSpec:
    """One validated line: the argv it runs as and the fields echoed on its envelope."""

    number: int
    cmd: str
    argv: list[str]
    line_id: str | int | float | None = None


@dataclass
class Totals:
    """What the run did, for the summary."""

    total: int = 0
    ok: int = 0
    failed: int = 0
    skipped: int = 0
    stopped_at: int | None = None
    first_failure: int = 0
    failures: list[int] = field(default_factory=list)


def _line_error(reason: str, hint: str | None = None, **details: Any) -> CliError:
    return CliError(
        code=CODE_INVALID_RUN_LINE,
        message=f"Invalid run line: {reason}",
        exit_status=EXIT_USAGE,
        hint=hint or "Each line is one JSON object: " + _SCHEMA_HINT,
        details={"reason": reason, **details},
    )


_SCHEMA_HINT = (
    '{"cmd": "view task list", "args": ["290"], "input": {}, "flags": {"project": 1}}. '
    "Run 'mammoth run --help' for the full schema."
)


@cache
def _flag_tables() -> tuple[frozenset[str], frozenset[str]]:
    """Every global flag spelling, and the subset that takes a value."""
    from mammoth_cli.app import _global_option_flags

    return _global_option_flags()


def _flag_token(name: str, value: Any) -> str | None:
    """The argv token for one ``flags`` entry, or None when the flag is switched off."""
    every, valued = _flag_tables()
    flag = "--" + str(name).lstrip("-").replace("_", "-")
    if flag not in every or flag in OWNED_FLAGS:
        known = sorted(f for f in every if f.startswith("--") and f not in OWNED_FLAGS)
        raise _line_error(
            f"unknown or reserved flag '{name}'.",
            hint="Use a global flag by long name without dashes: "
            + ", ".join(f.removeprefix("--") for f in known),
            flag=name,
        )
    if flag not in valued:
        if not isinstance(value, bool):
            raise _line_error(f"flag '{name}' is on/off: use true or false.", flag=name)
        return flag if value else None
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, str | int | float):
        raise _line_error(f"flag '{name}' takes a string or a number.", flag=name)
    return f"{flag}={value}"


def global_defaults(invocation: Invocation) -> dict[str, str]:
    """The flags given to ``run`` itself, which every line starts from (flag -> token)."""
    defaults: dict[str, str] = {}
    for flag, attribute in INHERITED_FLAGS:
        value = getattr(invocation, attribute)
        if attribute == "profile" and invocation.profile_is_default:
            continue
        if value is None or value is False:
            continue
        defaults[flag] = flag if value is True else f"{flag}={value}"
    return defaults


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate key '{key}'")
        document[key] = value
    return document


def _no_constant(name: str) -> Any:
    raise ValueError(f"{name} is not a JSON number")


def resolve_command_id(tokens: Sequence[str]) -> str:
    """The command id these tokens run, walked through the real Click tree.

    ``cmd`` and ``args`` are one argv to Click: ``["auth", "logout"]`` and ``["auth"]`` plus
    the argument ``"logout"`` run the same command, and ``"run inner"`` is ``run`` with the
    positional ``inner``. The walk descends while the next token names a subcommand and stops
    at the first token that does not (a positional); the refusals are checked against what it
    reaches, never against how the line spelled it.
    """
    import click

    node: Any = _click_root()
    ctx = click.Context(node)
    path: list[str] = []
    for token in tokens:
        lookup = getattr(node, "get_command", None)
        if lookup is None:
            break
        child = lookup(ctx, token)
        if child is None:
            break
        path.append(child.name or token)
        node = child
    return ".".join(path)


def parse_line(
    number: int,
    text: str,
    defaults: dict[str, str],
    command_flags: Any,
    resolve: Callable[[Sequence[str]], str] = resolve_command_id,
) -> LineSpec:
    """Validate one JSON line and build the argv it runs as.

    Raises:
        CliError: ``invalid_run_line`` (usage) for anything wrong with the line itself;
            ``run_command_refused`` for a command ``run`` does not run.
    """
    return build_spec(number, load_line(text), defaults, command_flags, resolve)


def load_line(text: str) -> dict[str, Any]:
    """Read one JSON line as an object with known keys only.

    Args:
        text: The line, without its newline.

    Returns:
        The line's object.

    Raises:
        CliError: ``invalid_run_line`` when the line is too large, not JSON, not an
            object, or has a key ``run`` does not know.
    """
    if len(text.encode("utf-8")) > MAX_LINE_BYTES:
        raise _line_error("the line is larger than 1 MiB.")
    try:
        line = json.loads(text, object_pairs_hook=_no_duplicate_keys, parse_constant=_no_constant)
    except ValueError as exc:
        raise _line_error(f"not valid JSON ({exc}).") from None
    if not isinstance(line, dict):
        raise _line_error("a line must be a JSON object.")
    unknown = sorted(set(line) - set(LINE_KEYS))
    if unknown:
        raise _line_error(
            f"unknown key(s): {', '.join(unknown)}.",
            hint="Allowed keys: " + ", ".join(LINE_KEYS) + ".",
            unknown=unknown,
        )
    return line


def build_spec(
    number: int,
    line: dict[str, Any],
    defaults: dict[str, str],
    command_flags: Any,
    resolve: Callable[[Sequence[str]], str] = resolve_command_id,
) -> LineSpec:
    """Build the argv one loaded line runs as, its references already filled in.

    Args:
        number: The line's physical number.
        line: The loaded line (:func:`load_line`).
        defaults: The flags given to ``run`` itself (flag -> token).
        command_flags: Returns the flags a command id declares.
        resolve: Walks command tokens to the command id they run.

    Returns:
        The line's argv and echoed fields.

    Raises:
        CliError: ``invalid_run_line`` or ``run_command_refused``.
    """
    cmd = line.get("cmd")
    words = cmd.split() if isinstance(cmd, str) else []
    if not words or not all(_WORD.match(word) for word in words):
        raise _line_error(
            "'cmd' must be the command path, for example \"view task list\".",
            cmd=cmd if isinstance(cmd, str) else None,
        )
    args = line.get("args", [])
    if not isinstance(args, list):
        raise _line_error("'args' must be a list of strings or numbers.")
    if any(isinstance(arg, bool) or not isinstance(arg, str | int | float) for arg in args):
        raise _line_error("'args' must hold strings or numbers only.")
    tokens = [*words, *(str(arg) for arg in args)]
    command_id = resolve(tokens)
    if command_id in REFUSED_COMMANDS:
        raise CliError(
            code=CODE_RUN_COMMAND_REFUSED,
            message=REFUSED_COMMANDS[command_id],
            exit_status=EXIT_USAGE,
            details={"cmd": " ".join(words), "command": command_id.replace(".", " ")},
        )
    argv = list(words)
    allowed_flags = command_flags(command_id)
    for arg in args:
        token = str(arg)
        if (
            token.startswith("-")
            and token not in allowed_flags
            and not NEGATIVE_NUMBER.match(token)
        ):
            raise _line_error(
                f"argument '{token}' looks like a flag; put global flags in 'flags'.",
                flag=token,
            )
        argv.append(token)
    flags = line.get("flags", {})
    if not isinstance(flags, dict):
        raise _line_error("'flags' must be an object.")
    merged = dict(defaults)
    for name, value in flags.items():
        flag_token = _flag_token(name, value)
        flag = "--" + str(name).lstrip("-").replace("_", "-")
        if flag == "--dry-run" and "--dry-run" in defaults:
            continue  # run's own --dry-run covers every line
        if flag_token is None:
            merged.pop(flag, None)
        else:
            merged[flag] = flag_token
    argv.extend(merged.values())
    document = line.get("input")
    if document is not None:
        if not isinstance(document, dict):
            raise _line_error("'input' must be an object.")
        argv.append("--input=" + json.dumps(document, ensure_ascii=False, allow_nan=False))
    line_id = line.get("id")
    if line_id is not None and (
        isinstance(line_id, bool) or not isinstance(line_id, str | int | float)
    ):
        raise _line_error("'id' must be a string or a number.")
    argv.extend(["--output", "json", "--no-input", "--no-progress"])
    return LineSpec(number=number, cmd=" ".join(words), argv=argv, line_id=line_id)


@cache
def _click_root() -> Any:
    """The Click command tree, built once; top-level groups load when a line first uses them."""
    import typer

    from mammoth_cli.app import app

    return typer.main.get_command(app)


def execute_line(argv: Sequence[str], command: str = "") -> tuple[int, dict[str, Any]]:
    """Run ``argv`` as a command in this process; return its exit status and envelope."""
    from mammoth_cli.app import _ABORT_ERRORS, _USAGE_ERRORS

    root = _click_root()
    buffer = io.StringIO()
    exit_status = 0
    with linecapture.capturing() as kept, contextlib.redirect_stdout(buffer):
        try:
            result = root.main(args=list(argv), prog_name="mammoth", standalone_mode=False)
            exit_status = result if isinstance(result, int) else 0
        except _USAGE_ERRORS as error:
            root.render_usage_error(error, list(argv))
            exit_status = int(getattr(error, "exit_code", EXIT_USAGE))
        except _ABORT_ERRORS:
            cancelled = cancelled_error()
            kept.append(cancelled.to_envelope())
            exit_status = cancelled.exit_status
        except SystemExit as exc:
            # sys.exit() and sys.exit(0) are a clean exit; a message is a failure.
            exit_status = (
                0 if exc.code is None else exc.code if isinstance(exc.code, int) else EXIT_API
            )
        except KeyboardInterrupt:
            exit_status = EXIT_INTERRUPT
            kept.append(
                CliError(
                    code="interrupted", message="The line was interrupted.", exit_status=exit_status
                ).to_envelope()
            )
        except Exception as exc:  # noqa: BLE001 -- a line fails with an envelope, never a traceback
            exit_status = EXIT_API
            kept.append(
                CliError(
                    code="internal_error",
                    message=f"{type(exc).__name__}: {exc}",
                    exit_status=EXIT_API,
                ).to_envelope()
            )
    if kept:
        return exit_status, kept[-1]
    stray = buffer.getvalue().strip()
    if exit_status == 0:
        # Help or version text: the command succeeded and printed no envelope.
        text = {"text": stray[:500]} if stray else None
        return 0, Result(data=text, meta=Meta(command=command, exit=0)).to_envelope()
    silent = CliError(
        code="no_output",
        message="This command printed text only (help or version) and no envelope.",
        exit_status=exit_status,
        details={"text": stray[:500]} if stray else {},
    )
    return exit_status, silent.to_envelope()


def write_envelope(envelope: dict[str, Any]) -> None:
    """Write one envelope as one compact line on stdout and flush it.

    Args:
        envelope: The envelope to write.
    """
    sys.stdout.write(
        json.dumps(
            envelope,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            default=str,
        )
        + "\n"
    )
    sys.stdout.flush()


def _read_source(source: str) -> str:
    """The text of the JSON Lines source: a file, or stdin for ``-``."""
    if source == "-":
        if sys.stdin is not None and sys.stdin.isatty():
            raise CliError(
                code="missing_argument",
                message="mammoth run reads JSON Lines from FILE or stdin, and stdin is a terminal.",
                exit_status=EXIT_USAGE,
                hint="Pass a file (mammoth run commands.jsonl) or pipe the lines in.",
            )
        data = sys.stdin.read(MAX_RUN_BYTES + 1).removeprefix("\ufeff")
    else:
        path = Path(source)
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                data = handle.read(MAX_RUN_BYTES + 1)
        except FileNotFoundError:
            raise CliError(
                code="input_not_found",
                message=f"No JSON Lines file found at '{source}'.",
                exit_status=EXIT_USAGE,
                hint="Check the path, or pass '-' to read from standard input.",
            ) from None
        except (OSError, UnicodeDecodeError):
            raise CliError(
                code="input_unreadable",
                message=f"Could not read '{source}' as UTF-8 text.",
                exit_status=EXIT_USAGE,
            ) from None
    if len(data) > MAX_RUN_BYTES:
        raise CliError(
            code=CODE_RUN_TOO_LARGE,
            message="The JSON Lines input is larger than 16 MiB.",
            exit_status=EXIT_USAGE,
            hint="Split it into several runs.",
        )
    return data


def _refuse_global_confirmation(invocation: Invocation) -> None:
    if invocation.yes or invocation.confirm is not None:
        raise CliError(
            code=CODE_RUN_FLAG_REFUSED,
            message="mammoth run has no global --yes or --confirm.",
            exit_status=EXIT_USAGE,
            hint=(
                'Confirm each mutating line on its own: {"cmd": ..., "flags": {"yes": true}}, '
                'plus "confirm" where the command needs the target name.'
            ),
        )


def command_flags(command_id: str) -> frozenset[str]:
    """The flags a command declares itself, which a line may list in ``args``.

    Args:
        command_id: The command id.

    Returns:
        The command's own flag spellings.
    """
    from mammoth_cli.runtime.strict import COMMAND_FLAGS

    return COMMAND_FLAGS.get(command_id, frozenset())


def run(invocation: Invocation) -> HandlerResult | Outcome:
    """Run many commands in one process: JSON Lines of cmd, args, input and flags."""
    _refuse_global_confirmation(invocation)
    # ``--continue`` is the command's own flag; wherever it came in, it is not the FILE.
    operands = [arg for arg in invocation.extra_args if arg != "--continue"]
    declared = invocation.positionals.get("file")
    source = (operands[0] if operands else declared if declared != "--continue" else None) or "-"
    keep_going = "--continue" in invocation.extra_args
    # Only "\n" ends a line: str.splitlines() also splits on U+2028, U+2029, U+0085 and
    # U+001C-1E, which JSON writers leave raw inside strings, and would shift line numbers.
    numbered = [
        (number, text.strip(" \t\r"))
        for number, text in enumerate(_read_source(str(source)).split("\n"), start=1)
        if text.strip(" \t\r")
    ]
    if not numbered:
        raise CliError(
            code=CODE_RUN_INPUT_EMPTY,
            message="The JSON Lines input has no commands.",
            exit_status=EXIT_USAGE,
            hint="Write one JSON object per line, for example " + _SCHEMA_HINT,
        )
    summary = run_lines(
        numbered,
        global_defaults(invocation),
        keep_going=keep_going,
        dry_run=invocation.dry_run,
    )
    run_exit = summary["exit"]
    meta = Meta(command="run", profile=invocation.profile, exit=run_exit, run_id=run_id())
    write_envelope(Result(data=summary, meta=meta).to_envelope())
    return Outcome(streamed=True, exit_status=run_exit)


def run_lines(
    numbered: Sequence[tuple[int, str]],
    defaults: dict[str, str],
    *,
    keep_going: bool,
    dry_run: bool,
    scope: dict[str, Any] | None = None,
    past_partial: bool = False,
    steps: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run numbered JSON Lines in order, writing each line's envelopes as it finishes.

    Args:
        numbered: Each line's physical number and text.
        defaults: The flags every line starts from (see :func:`global_defaults`).
        keep_going: Run every line even after one fails.
        dry_run: Whether the run previews only.
        scope: Values every line's references may read besides ``steps``, such as a
            recipe's ``inputs``.
        past_partial: Go on after a line that exits partial (it made what it reports,
            with a warning), counting it in ``partial_lines`` instead of ``failed``.
        steps: The named results of lines that already ran (``history resume``).

    Returns:
        The summary: line counts, where the run stopped, and its exit status.
    """
    totals = Totals(total=len(numbered))
    run_exit = 0
    steps = dict(steps or {})
    partial: list[int] = []
    if not dry_run:
        # The plan and each finished line are journaled, so 'history resume' can go on
        # from the first line that did not finish.
        journal.record_plan(
            numbered, defaults, scope=scope, keep_going=keep_going, past_partial=past_partial
        )
        if steps:
            journal.record_step(0, 0, steps)
    with remembering_auth() as credentials:
        for position, (number, text) in enumerate(numbered):
            named_before = set(steps)
            exit_status, ran_argv = _run_line(
                number, text, defaults, steps, dry_run=dry_run, scope=scope
            )
            if not dry_run:
                added = {name: steps[name] for name in steps.keys() - named_before}
                journal.record_step(number, exit_status, added)
            if ran_argv and ran_argv[0] in _CREDENTIAL_GROUPS:
                credentials.clear()
            if exit_status == 0:
                totals.ok += 1
                continue
            if past_partial and exit_status == EXIT_PARTIAL:
                partial.append(number)
                run_exit = run_exit or exit_status
                continue
            totals.failed += 1
            totals.failures.append(number)
            run_exit = run_exit or exit_status
            if exit_status == EXIT_INTERRUPT:
                # Ctrl-C ends the whole run, --continue or not: the lines after it are
                # skipped, never started.
                run_exit = EXIT_INTERRUPT
                totals.stopped_at = number
                totals.skipped = len(numbered) - position - 1
                break
            if not keep_going:
                totals.stopped_at = number
                totals.skipped = len(numbered) - position - 1
                break
    summary: dict[str, Any] = {
        "lines": totals.total,
        "ok": totals.ok,
        "failed": totals.failed,
        "skipped": totals.skipped,
        "stopped_at": totals.stopped_at,
        "failed_lines": totals.failures,
        "continue": keep_going,
        "dry_run": dry_run,
        "exit": run_exit,
    }
    if past_partial:
        summary["partial_lines"] = partial
    return summary


def _run_line(
    number: int,
    text: str,
    defaults: dict[str, str],
    steps: dict[str, Any],
    *,
    dry_run: bool,
    scope: dict[str, Any] | None = None,
) -> tuple[int, list[str]]:
    """Run one line (once, or once per ``for_each`` item) and write its envelopes.

    Args:
        number: The line's physical number.
        text: The line.
        defaults: The flags every line starts from.
        steps: The results of the named lines run so far; a named line adds its own.
        dry_run: Whether the run previews only: an unresolved reference plans the line.
        scope: Values the line's references may read besides ``steps``.

    Returns:
        The line's exit status (the first failed item's, for ``for_each``) and the
        argv of the last command it ran (empty when it ran none).
    """
    shown: dict[str, Any] = {"line": number, "cmd": _best_effort_cmd(text)}
    try:
        line = load_line(text)
        name = _step_name(line, steps)
        if "id" in line:
            shown["id"] = _line_id(line["id"])
        line_scope: dict[str, Any] = {**(scope or {}), "steps": steps}
        if "when" in line and not bindings.evaluate(line["when"], line_scope):
            write_envelope({**shown, "exit": 0, "skipped": True, **_result(shown["cmd"], None)})
            if name is not None:
                steps[name] = {"skipped": True, "data": None, "exit": 0}
            return 0, []
        items = _for_each_items(line["for_each"], line_scope) if "for_each" in line else None
    except bindings.BindingError as error:
        return _unresolved(shown, error, steps, line, dry_run=dry_run), []
    except CliError as error:
        write_envelope({**shown, "exit": error.exit_status, **error.to_envelope()})
        return error.exit_status, []
    if items is None:
        exit_status, envelope, argv = _run_once(number, line, defaults, line_scope, shown, dry_run)
        if name is not None:
            steps[name] = envelope
        return exit_status, argv
    datas: list[Any] = []
    first_exit = 0
    last_argv: list[str] = []
    for index, item in enumerate(items):
        item_scope = {**line_scope, "item": item, "index": index}
        exit_status, envelope, argv = _run_once(
            number, line, defaults, item_scope, {**shown, "item": index}, dry_run
        )
        datas.append(envelope.get("data"))
        last_argv = argv or last_argv
        if exit_status != 0:
            first_exit = exit_status
            break
    if name is not None:
        steps[name] = {"data": datas, "exit": first_exit}
    return first_exit, last_argv


def _run_once(
    number: int,
    line: dict[str, Any],
    defaults: dict[str, str],
    scope: dict[str, Any],
    shown: dict[str, Any],
    dry_run: bool,
) -> tuple[int, dict[str, Any], list[str]]:
    """Fill one line's references from ``scope``, run it, and write its envelope."""
    try:
        bound = {key: bindings.resolve(line[key], scope) for key in BOUND_KEYS if key in line}
        spec = build_spec(number, {**line, **bound}, defaults, command_flags)
        shown = {**shown, "cmd": spec.cmd}
        exit_status, envelope = execute_line(spec.argv, spec.cmd)
        forget_reads()
        argv = spec.argv
    except bindings.BindingError as error:
        exit_status = _unresolved(shown, error, {}, line, dry_run=dry_run)
        return exit_status, {"planned": dry_run, "data": None, "exit": exit_status}, []
    except CliError as error:
        exit_status, envelope, argv = error.exit_status, error.to_envelope(), []
    write_envelope({**shown, "exit": exit_status, **envelope})
    return exit_status, {**envelope, "exit": exit_status}, argv


def _result(cmd: str, data: Any) -> dict[str, Any]:
    """A success envelope for a line ``run`` answered itself (skipped or planned)."""
    return Result(data=data, meta=Meta(command=cmd, exit=0)).to_envelope()


def _step_name(line: dict[str, Any], steps: dict[str, Any]) -> str | None:
    """The line's ``name``, checked: a word, not used by an earlier line."""
    name = line.get("name")
    if name is None:
        return None
    if not isinstance(name, str) or not _STEP_NAME.match(name):
        raise _line_error(
            "'name' must be a word of letters, digits, '_' or '-', starting with a letter.",
            name=name if isinstance(name, str) else None,
        )
    if name in steps:
        raise _line_error(f"an earlier line is already named '{name}'.", name=name)
    return name


def _line_id(line_id: Any) -> str | int | float:
    if isinstance(line_id, bool) or not isinstance(line_id, str | int | float):
        raise _line_error("'id' must be a string or a number.")
    return line_id


def _for_each_items(reference: Any, scope: dict[str, Any]) -> list[Any]:
    """The list a ``for_each`` line runs over."""
    items = bindings.resolve(reference, scope)
    if not isinstance(items, list):
        raise _line_error(
            "'for_each' must be a reference to a list, such as '{{steps.list.data}}'.",
            for_each=reference if isinstance(reference, str) else None,
        )
    return items


def _unresolved(
    shown: dict[str, Any],
    error: bindings.BindingError,
    steps: dict[str, Any],
    line: dict[str, Any] | None,
    *,
    dry_run: bool,
) -> int:
    """Write the envelope of a line whose reference does not resolve; return its exit.

    Under ``--dry-run`` the line is planned, not failed: the earlier lines only previewed,
    so the values it reads do not exist yet.
    """
    name = line.get("name") if isinstance(line, dict) else None
    if dry_run:
        data = {"planned": True, "waits_on": error.path, "reason": str(error)}
        write_envelope({**shown, "exit": 0, **_result(shown["cmd"], data)})
        if isinstance(name, str) and name not in steps and _STEP_NAME.match(name):
            steps[name] = {"planned": True, "data": None, "exit": 0}
        return 0
    failure = CliError(
        code=CODE_UNRESOLVED_REFERENCE,
        message=f"Line {shown['line']}: {error}.",
        exit_status=EXIT_USAGE,
        hint=(
            "A reference reads the result of an earlier named line, such as "
            "'{{steps.upload.data.dataset_id}}'. Earlier names: "
            + (", ".join(steps) or "none")
            + "."
        ),
        details={"reference": error.path, "steps": list(steps)},
    )
    write_envelope({**shown, "exit": failure.exit_status, **failure.to_envelope()})
    return failure.exit_status


def _best_effort_cmd(text: str) -> str:
    """The ``cmd`` of a line that failed validation, when it can still be read."""
    try:
        line = json.loads(text)
    except ValueError:
        return ""
    cmd = line.get("cmd") if isinstance(line, dict) else None
    return cmd if isinstance(cmd, str) else ""
