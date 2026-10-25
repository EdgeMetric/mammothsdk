"""``mammoth history``: the writes this machine made, and undoing them (#311).

Every write is journaled with the ``mammoth run`` lines that reverse it
(:mod:`mammoth_cli.runtime.journal`). ``history undo`` runs those lines for one write
(its ``inv``) or for every write of one ``mammoth run`` (its ``group``), newest first,
as a saga: it stops at the first line that fails and reports what was undone and
what was not. ``--dry-run`` previews every line instead.

Each undo line runs through the same command path as a typed command (validation,
confirmation, verify) and is journaled itself, so ``history undo`` of an undo redoes.

``history resume`` goes on with a ``mammoth run`` or ``recipe run`` that stopped (a failed
line, Ctrl-C, a crash): it restores the results of the lines that finished and runs the
rest, from the first line that did not finish. A write whose outcome is unknown (the run
stopped while it was being sent) is not sent again blindly: resume refuses until the
caller checks it and names the line to start from (``from_line``).
"""

from __future__ import annotations

import json
import re
from typing import Any

from mammoth_cli.commands import run as run_cmd
from mammoth_cli.commands.registry import HandlerResult
from mammoth_cli.context.resolver import env_token_in_use
from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENT,
    EXIT_API,
    EXIT_PARTIAL,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.emit import run_id
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.runtime import journal, trace
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.dispatch import Outcome
from mammoth_cli.runtime.invocation import Invocation

CODE_HISTORY_NOT_FOUND = "history_not_found"
CODE_JOURNAL_OFF = "journal_off"
CODE_NOTHING_TO_RESUME = "nothing_to_resume"
CODE_RESUME_OUTCOME_UNKNOWN = "resume_outcome_unknown"
CODE_RESUME_NEEDS_VALUE = "resume_secret_needed"
CODE_RESUME_RESULT_TOO_LARGE = "resume_result_too_large"
CODE_UNDO_IN_PROGRESS = "undo_in_progress"
CODE_UNDO_NEEDS_TOKEN = "undo_needs_token"  # noqa: S105 -- an error code, not a secret
CODE_VIEW_CHANGED = "view_changed_since_edit"
#: Most entries ``history list`` shows unless asked for more.
DEFAULT_LIMIT = 20


def _store() -> journal.JournalStore:
    store = journal.default_store()
    if store is None:
        raise CliError(
            code=CODE_JOURNAL_OFF,
            message="The journal is switched off, so there is no history to read or undo.",
            exit_status=EXIT_USAGE,
            hint=f"Unset {journal.JOURNAL_ENV} to journal the next writes.",
        )
    return store


def _matching(target: str) -> list[journal.Entry]:
    store = _store()
    # A resume journals under a group of its own, but its writes belong to the run it resumed.
    target = journal.group_roots(store.records()).get(target, target)
    found = [e for e in journal.entries(store) if target in (e.inv, e.group)]
    if not found:
        raise CliError(
            code=CODE_HISTORY_NOT_FOUND,
            message=f"No journaled write has the id '{target}'.",
            exit_status=EXIT_USAGE,
            hint="Run 'mammoth history list' for the ids (inv for one write, group for a run).",
            details={"id": target},
        )
    return found


def _target(invocation: Invocation) -> str:
    value = invocation.positionals.get("id")
    if not value:
        raise CliError(
            code="missing_argument",
            message="Name the write to act on: its inv, or the group of a whole run.",
            exit_status=EXIT_USAGE,
            hint="Run 'mammoth history list' for the ids.",
        )
    return str(value)


def history_list(invocation: Invocation) -> HandlerResult:
    """List the journaled writes, newest first; filter with 'limit', 'undoable_only'."""
    document = invocation.bound_input()
    limit = DEFAULT_LIMIT if document.get("limit") is None else int(document["limit"])
    if limit < 1:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=f"'limit' must be 1 or more, not {limit}.",
            exit_status=EXIT_USAGE,
            hint="Leave 'limit' out for the newest 20 entries.",
        )
    views = [entry.view() for entry in reversed(journal.entries(_store()))]
    if document.get("undoable_only"):
        views = [view for view in views if view["undoable"]]
    shown = views[:limit]
    return {"entries": shown, "count": len(shown), "total": len(views)}, {}


def history_show(invocation: Invocation) -> HandlerResult:
    """Show one write (by inv) or every write of one run (by group), with their undo lines."""
    target = _target(invocation)
    return {"id": target, "entries": [entry.view() for entry in _matching(target)]}, {}


def history_undo(invocation: Invocation) -> HandlerResult | Outcome:
    """Undo one write (by inv) or a whole run (by group), newest first. Prompt or '--yes'."""
    target = _target(invocation)
    found = _matching(target)
    todo = [entry for entry in reversed(found) if entry.view()["undoable"]]
    left_alone = [
        {
            "inv": entry.inv,
            "command": entry.command.replace(".", " "),
            "reason": entry.irreversible or f"Its status is {entry.view()['status']}.",
        }
        for entry in reversed(found)
        if entry not in todo
    ]
    result: dict[str, Any] = {
        "id": target,
        "dry_run": invocation.dry_run,
        "undone": [],
        "not_undoable": left_alone,
    }
    if not todo:
        result["outcome"] = "nothing_to_undo"
        return result, {}
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"undo {len(todo)} write(s) of {target}",
    )
    traced = trace.current()
    by = traced.invocation_id if traced is not None else ""
    store = _store()
    force = bool(invocation.bound_input().get("force"))
    for position, entry in enumerate(todo):
        steps: list[dict[str, Any]] = []
        try:
            with store.claim(f"undo-{entry.inv}"):
                if _already_undone(store, entry.inv):
                    result["undone"].append(
                        {"inv": entry.inv, "command": entry.command, "steps": []}
                    )
                    continue
                failed = _undo_entry(entry, invocation, steps, store, force=force)
        except journal.JournalBusy as busy:
            raise CliError(
                code=CODE_UNDO_IN_PROGRESS,
                message=f"Another 'history undo' is already undoing {entry.inv}.",
                exit_status=EXIT_USAGE,
                hint="Wait for it to finish, then run 'mammoth history show' for the result.",
                details={"inv": entry.inv},
            ) from busy
        result["undone"].append({"inv": entry.inv, "command": entry.command, "steps": steps})
        if failed is not None:
            remaining = [e.inv for e in todo[position:]]
            result["failed"] = failed
            result["not_undone"] = remaining
            # Some writes may have been undone already: partial, or failed when none was.
            result["outcome"] = "partial" if position else "failed"
            return Outcome(data=result, exit_status=EXIT_PARTIAL if position else EXIT_API)
        if not invocation.dry_run:
            journal.mark_undone(store, entry.inv, by)
    result["outcome"] = "planned" if invocation.dry_run else "undone"
    return result, {}


def _already_undone(store: journal.JournalStore, inv: str) -> bool:
    """Whether another undo finished this write while this one waited its turn."""
    return any(e.inv == inv and e.undone_by is not None for e in journal.entries(store))


def _undo_entry(
    entry: journal.Entry,
    invocation: Invocation,
    steps: list[dict[str, Any]],
    store: journal.JournalStore,
    *,
    force: bool = False,
) -> dict[str, Any] | None:
    """Run one write's undo lines; return the failure, or None when every line ran.

    The lines an earlier, stopped undo already ran are skipped, and each line that runs is
    recorded, so a retry goes on from the line that failed.
    """
    for index, line in enumerate(entry.undo):
        if index < entry.undone_lines and not invocation.dry_run:
            continue
        refused = _account_missing(entry, invocation)
        if refused is not None:
            return refused
        line = _as_account(entry, line)
        blocked = _changed_since(entry, line, invocation, steps, force=force)
        if blocked is not None:
            return blocked
        for step in _expanded([line], invocation, steps):
            exit_status, envelope = _run(step, invocation)
            steps.append({"cmd": step["cmd"], "args": step.get("args", []), "exit": exit_status})
            if exit_status != 0:
                error = envelope.get("error") or {}
                return {
                    "inv": entry.inv,
                    "cmd": step["cmd"],
                    "exit": exit_status,
                    "code": error.get("code"),
                    "message": error.get("message") or "An undo step failed.",
                }
        if not invocation.dry_run:
            journal.mark_undo_step(store, entry.inv, index + 1)
    return None


def _account_missing(entry: journal.Entry, invocation: Invocation) -> dict[str, Any] | None:
    """The failure to report when the write used ``MAMMOTH_API_TOKEN`` and none is set now."""
    if entry.auth != journal.AUTH_ENV or env_token_in_use(invocation):
        return None
    return {
        "inv": entry.inv,
        "cmd": entry.command.replace(".", " "),
        "exit": EXIT_USAGE,
        "code": CODE_UNDO_NEEDS_TOKEN,
        "message": (
            f"{entry.inv} was made with MAMMOTH_API_TOKEN, and none is set now, so the undo"
            " would run as another account."
        ),
        "hint": "Set MAMMOTH_API_TOKEN to the token the write used, then run the undo again.",
    }


def _as_account(entry: journal.Entry, line: dict[str, Any]) -> dict[str, Any]:
    """The line run with the stored profile the write used, not the profile selected now.

    Args:
        entry: The write being undone.
        line: One of its undo lines.

    Returns:
        The line with ``--profile`` set when the write used a stored profile and the line
        does not name one.
    """
    flags = line.get("flags") or {}
    if entry.auth != journal.AUTH_PROFILE or not entry.profile or "profile" in flags:
        return line
    return {**line, "flags": {**flags, "profile": entry.profile}}


def _changed_since(
    entry: journal.Entry,
    line: dict[str, Any],
    invocation: Invocation,
    steps: list[dict[str, Any]],
    *,
    force: bool,
) -> dict[str, Any] | None:
    """The failure to report when the view's pipeline is not what the edit left, or None.

    Applying the pipeline from before an edit also drops every edit made after it, so the
    undo of an edit checks the fingerprint taken right after the edit (``expect``).
    """
    expected = line.get("expect")
    if expected is None or force:
        return None
    view = line["args"][0]
    listing = {"cmd": "view task list", "args": [view], "flags": line.get("flags", {})}
    exit_status, envelope = _run(listing, invocation, read=True)
    steps.append({"cmd": listing["cmd"], "args": [view], "exit": exit_status})
    tasks = (envelope.get("data") or {}).get("tasks") if exit_status == 0 else None
    if isinstance(tasks, list) and journal.fingerprint(tasks) == expected:
        return None
    return {
        "inv": entry.inv,
        "cmd": line["cmd"],
        "exit": EXIT_USAGE,
        "code": CODE_VIEW_CHANGED,
        "message": (
            f"View {view} is not as the edit left it (it was changed since, or could not be"
            " read), and undoing the edit would drop those changes."
        ),
        "hint": "To undo anyway, run again with --input '{\"force\": true}'.",
    }


def _expanded(
    lines: list[dict[str, Any]], invocation: Invocation, steps: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Turn a ``keep_tasks`` line into one delete per step the edit added, newest first."""
    expanded: list[dict[str, Any]] = []
    for line in lines:
        keep = line.get("keep_tasks")
        if keep is None:
            expanded.append({key: value for key, value in line.items() if key != "expect"})
            continue
        view = line["args"][0]
        listing = {"cmd": "view task list", "args": [view], "flags": line.get("flags", {})}
        exit_status, envelope = _run(listing, invocation, read=True)
        steps.append({"cmd": listing["cmd"], "args": [view], "exit": exit_status})
        tasks = (envelope.get("data") or {}).get("tasks") or [] if exit_status == 0 else []
        added = sorted(
            (task for task in tasks if task.get("id") not in keep),
            key=lambda task: task.get("sequence") or 0,
            reverse=True,
        )
        expanded.extend(
            {"cmd": line["cmd"], "args": [view, task["id"]], "flags": line.get("flags", {})}
            for task in added
        )
    return expanded


def _run(
    line: dict[str, Any], invocation: Invocation, *, read: bool = False
) -> tuple[int, dict[str, Any]]:
    """Run one ``mammoth run`` line in this process, previewing it under ``--dry-run``."""
    flags = dict(line.get("flags") or {})
    command_id = run_cmd.resolve_command_id(line["cmd"].split())
    record = command_by_id(command_id) or {}
    if record.get("confirmation", "none") != "none":
        flags["yes"] = True
    if invocation.dry_run and not read:
        flags["dry-run"] = True
    spec = run_cmd.build_spec(
        0, {**line, "flags": flags}, {}, run_cmd.command_flags, run_cmd.resolve_command_id
    )
    return run_cmd.execute_line(spec.argv, spec.cmd)


def history_resume(invocation: Invocation) -> HandlerResult | Outcome:
    """Go on with a stopped run (by its group) from its first unfinished line. Prompt or '--yes'."""
    target = _target(invocation)
    store = _store()
    plan = journal.plan_for(store, target)
    if plan is None:
        raise CliError(
            code=CODE_HISTORY_NOT_FOUND,
            message=f"No mammoth run or recipe run has the group '{target}'.",
            exit_status=EXIT_USAGE,
            hint="Run 'mammoth history list' and use the group of the run that stopped.",
            details={"id": target},
        )
    from_line = invocation.bound_input().get("from_line")
    remaining = _remaining(plan, from_line, store)
    _refuse_secrets(plan, remaining)
    _refuse_omitted(plan, remaining)
    progress = _progress(plan, remaining) if from_line is None else None
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"resume {target} at line {remaining[0][0]} ({len(remaining)} lines)",
    )
    # The flags given to resume (a new --profile, --dry-run) win over the run's own.
    defaults = {**plan.defaults, **run_cmd.global_defaults(invocation)}
    if not invocation.dry_run:
        # The resume's own records count for the run it goes on with, so a second resume
        # skips what this one does and 'history undo' of the run reaches its writes.
        journal.record_resume(plan.group, acknowledged=from_line is not None)
    rerun = [number for number, _ in remaining]
    summary = run_cmd.run_lines(
        remaining,
        defaults,
        keep_going=plan.keep_going,
        dry_run=invocation.dry_run,
        scope=plan.scope,
        past_partial=plan.past_partial,
        steps=plan.steps_without(rerun),
        resumed=True,
        # With 'from_line' the caller starts the line over; items done before stay done only
        # when the resume picks the line up by itself.
        progress=progress,
    )
    run_exit = summary["exit"]
    data = {"resumed": target, "from_line": remaining[0][0], **summary}
    meta = Meta(
        command="history resume", profile=invocation.profile, exit=run_exit, run_id=run_id()
    )
    run_cmd.write_envelope(Result(data=data, meta=meta).to_envelope())
    return Outcome(streamed=True, exit_status=run_exit)


def _remaining(
    plan: journal.Plan, from_line: Any, store: journal.JournalStore
) -> list[tuple[int, str]]:
    """The lines a resume runs: from ``from_line``, or from the first unfinished line."""
    if from_line is not None:
        remaining = [(number, text) for number, text in plan.lines if number >= int(from_line)]
    else:
        # A line that exited partial in a run that goes on past partial lines is done.
        remaining = [(number, text) for number, text in plan.lines if number not in plan.finished]
        unknown = [
            entry.inv
            for entry in journal.entries(store)
            if entry.group == plan.group
            and (entry.exit is None or entry.uncertain)
            and not entry.acknowledged
        ]
        if unknown and remaining:
            raise CliError(
                code=CODE_RESUME_OUTCOME_UNKNOWN,
                message=(
                    f"A write of the run may or may not have happened (line {remaining[0][0]}): "
                    "it was interrupted, timed out or lost its connection while being sent."
                ),
                exit_status=EXIT_USAGE,
                hint=(
                    f"Check it with 'mammoth history show {unknown[-1]}' and the object it "
                    "makes. Then resume with --input '{\"from_line\": N}': the same line if "
                    "the write did not happen, the next one if it did."
                ),
                details={"unknown": unknown, "line": remaining[0][0]},
            )
    if not remaining:
        raise CliError(
            code=CODE_NOTHING_TO_RESUME,
            message=f"Every line of {plan.group} finished; there is nothing to resume.",
            exit_status=EXIT_USAGE,
            hint=f"Run 'mammoth history show {plan.group}' for what it did.",
            details={"id": plan.group},
        )
    return remaining


def _refuse_secrets(plan: journal.Plan, remaining: list[tuple[int, str]]) -> None:
    """Refuse a resume that needs a value the journal replaced because it is a secret."""
    redacted = plan.redacted_references()
    for number, text in remaining:
        needed = [
            reference
            for reference in sorted(redacted)
            if re.search(r"\{\{[^{}]*" + re.escape(reference) + r"(?![A-Za-z0-9_-])", text)
        ]
        if journal.has_redacted(_loads(text)) or needed:
            raise CliError(
                code=CODE_RESUME_NEEDS_VALUE,
                message=(
                    f"Line {number} holds or reads a secret that the history does not keep, "
                    "so it cannot be run again from the history."
                ),
                exit_status=EXIT_USAGE,
                hint=(
                    f"Run line {number} yourself with its secret (mammoth run, or the "
                    "command), then resume with --input '{\"from_line\": N}' for the line after it."
                ),
                details={"line": number, "references": needed},
            )


def _refuse_omitted(plan: journal.Plan, remaining: list[tuple[int, str]]) -> None:
    """Refuse a resume whose line reads the result of a line the history could not keep.

    A result over the journal's size limit is not stored, so a line that reads it would
    read nothing. The line that made it can be run again from the history.

    Args:
        plan: The run.
        remaining: The lines the resume runs.

    Raises:
        CliError: A remaining line reads a named result that was too large to keep.
    """
    made_again = {name for _, text in remaining if (name := journal.line_name(text))}
    for number, text in remaining:
        for name in sorted(set(plan.omitted) - made_again):
            if not re.search(r"\{\{\s*steps\." + re.escape(name) + r"(?![A-Za-z0-9_-])", text):
                continue
            maker = next((n for n, line in plan.lines if journal.line_name(line) == name), None)
            hint = (
                f"Resume with --input '{{\"from_line\": {maker}}}' to run the line that made it"
                " again first."
                if maker is not None
                else "Run the line that made it again, then resume after it."
            )
            raise CliError(
                code=CODE_RESUME_RESULT_TOO_LARGE,
                message=(
                    f"Line {number} reads steps.{name}, whose result was too large for the "
                    "history to keep."
                ),
                exit_status=EXIT_USAGE,
                hint=hint,
                details={"line": number, "step": name, "made_by": maker},
            )


def _progress(plan: journal.Plan, remaining: list[tuple[int, str]]) -> dict[int, dict[int, Any]]:
    """The finished items of the ``for_each`` lines a resume picks up, with their results.

    An item whose result was too large to keep is not restorable. A read is run again; a
    write is not, because running it again would repeat it.

    Args:
        plan: The run.
        remaining: The lines the resume runs.

    Returns:
        The items to treat as done, by line and index.

    Raises:
        CliError: An item of a write finished, but its result was not kept.
    """
    progress = {number: dict(items) for number, items in plan.items.items()}
    texts = dict(remaining)
    for number, indexes in sorted(plan.omitted_items.items()):
        if number not in texts:
            continue
        if not _is_read(texts[number]):
            raise CliError(
                code=CODE_RESUME_RESULT_TOO_LARGE,
                message=(
                    f"Line {number} ran for some items whose results were too large for the "
                    "history to keep, so it cannot be picked up where it stopped without "
                    "repeating them."
                ),
                exit_status=EXIT_USAGE,
                hint=(
                    f"Check what items {sorted(indexes)} did, then resume with --input "
                    f"'{{\"from_line\": {number + 1}}}' for the line after it."
                ),
                details={"line": number, "items": sorted(indexes)},
            )
        for index in indexes:
            progress.get(number, {}).pop(index, None)
    return progress


def _is_read(text: str) -> bool:
    """Whether a journaled run line runs a command that only reads."""
    line = _loads(text)
    if not isinstance(line, dict) or not isinstance(line.get("cmd"), str):
        return False
    try:
        record = command_by_id(run_cmd.resolve_command_id(line["cmd"].split())) or {}
    except CliError:
        return False
    return record.get("mutation_class") == "read"


def _loads(text: str) -> Any:
    try:
        return json.loads(text)
    except ValueError:
        return None
