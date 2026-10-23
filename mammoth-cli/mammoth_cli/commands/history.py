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

from typing import Any

from mammoth_cli.commands import run as run_cmd
from mammoth_cli.errors.envelope import EXIT_API, EXIT_PARTIAL, EXIT_USAGE, CliError
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.emit import run_id
from mammoth_cli.output.envelope import Meta, Result
from mammoth_cli.runtime import journal, trace
from mammoth_cli.runtime.confirm import POLICY_PROMPT_OR_YES, enforce_confirmation
from mammoth_cli.runtime.dispatch import EXIT_STATUS_META, STREAMED_META
from mammoth_cli.runtime.invocation import Invocation

HandlerResult = tuple[Any, dict[str, Any]]

CODE_HISTORY_NOT_FOUND = "history_not_found"
CODE_JOURNAL_OFF = "journal_off"
CODE_NOTHING_TO_RESUME = "nothing_to_resume"
CODE_RESUME_OUTCOME_UNKNOWN = "resume_outcome_unknown"
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
    found = [e for e in journal.entries(_store()) if target in (e.inv, e.group)]
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
    limit = int(document.get("limit") or DEFAULT_LIMIT)
    views = [entry.view() for entry in reversed(journal.entries(_store()))]
    if document.get("undoable_only"):
        views = [view for view in views if view["undoable"]]
    shown = views[:limit]
    return {"entries": shown, "count": len(shown), "total": len(views)}, {}


def history_show(invocation: Invocation) -> HandlerResult:
    """Show one write (by inv) or every write of one run (by group), with their undo lines."""
    target = _target(invocation)
    return {"id": target, "entries": [entry.view() for entry in _matching(target)]}, {}


def history_undo(invocation: Invocation) -> HandlerResult:
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
    for position, entry in enumerate(todo):
        steps: list[dict[str, Any]] = []
        failed = _undo_entry(entry, invocation, steps)
        result["undone"].append({"inv": entry.inv, "command": entry.command, "steps": steps})
        if failed is not None:
            remaining = [e.inv for e in todo[position:]]
            result["failed"] = failed
            result["not_undone"] = remaining
            # Some writes may have been undone already: partial, or failed when none was.
            result["outcome"] = "partial" if position else "failed"
            return result, {EXIT_STATUS_META: EXIT_PARTIAL if position else EXIT_API}
        if not invocation.dry_run:
            journal.mark_undone(store, entry.inv, by)
    result["outcome"] = "planned" if invocation.dry_run else "undone"
    return result, {}


def _undo_entry(
    entry: journal.Entry, invocation: Invocation, steps: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Run one write's undo lines; return the failure, or None when every line ran."""
    for line in _expanded(entry.undo, invocation, steps):
        exit_status, envelope = _run(line, invocation)
        steps.append({"cmd": line["cmd"], "args": line.get("args", []), "exit": exit_status})
        if exit_status != 0:
            error = envelope.get("error") or {}
            return {
                "inv": entry.inv,
                "cmd": line["cmd"],
                "exit": exit_status,
                "code": error.get("code"),
                "message": error.get("message") or "An undo step failed.",
            }
    return None


def _expanded(
    lines: list[dict[str, Any]], invocation: Invocation, steps: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Turn a ``keep_tasks`` line into one delete per step the edit added, newest first."""
    expanded: list[dict[str, Any]] = []
    for line in lines:
        keep = line.get("keep_tasks")
        if keep is None:
            expanded.append(line)
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


def history_resume(invocation: Invocation) -> HandlerResult:
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
    enforce_confirmation(
        invocation,
        policy=POLICY_PROMPT_OR_YES,
        action=f"resume {target} at line {remaining[0][0]} ({len(remaining)} lines)",
    )
    # The flags given to resume (a new --profile, --dry-run) win over the run's own.
    defaults = {**plan.defaults, **run_cmd.global_defaults(invocation)}
    summary = run_cmd.run_lines(
        remaining,
        defaults,
        keep_going=plan.keep_going,
        dry_run=invocation.dry_run,
        scope=plan.scope,
        past_partial=plan.past_partial,
        steps=plan.steps,
    )
    run_exit = summary["exit"]
    data = {"resumed": target, "from_line": remaining[0][0], **summary}
    meta = Meta(
        command="history resume", profile=invocation.profile, exit=run_exit, run_id=run_id()
    )
    run_cmd.write_envelope(Result(data=data, meta=meta).to_envelope())
    return None, {STREAMED_META: True, EXIT_STATUS_META: run_exit}


def _remaining(
    plan: journal.Plan, from_line: Any, store: journal.JournalStore
) -> list[tuple[int, str]]:
    """The lines a resume runs: from ``from_line``, or from the first unfinished line."""
    if from_line is not None:
        remaining = [(number, text) for number, text in plan.lines if number >= int(from_line)]
    else:
        remaining = [(number, text) for number, text in plan.lines if number not in plan.finished]
        unknown = [
            entry.inv
            for entry in journal.entries(store)
            if entry.group == plan.group and entry.exit is None
        ]
        if unknown and remaining:
            raise CliError(
                code=CODE_RESUME_OUTCOME_UNKNOWN,
                message=(
                    f"The run stopped while a write was being sent (line {remaining[0][0]}), "
                    "so it may or may not have happened."
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
