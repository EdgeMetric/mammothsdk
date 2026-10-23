"""The journal: one record before and one after every write, and how to undo it.

The run log (:mod:`mammoth_cli.runtime.runlog`) says what happened, for debugging. The
journal says what changed and how to change it back, for ``mammoth history``:

* ``begin`` is written before the write is sent (write-ahead), so a crash between the
  request and the answer still leaves a record of a write whose outcome is unknown.
* ``end`` is written after it, with the exit status, the objects the write made or
  changed (``meta.opens``) and its compensation: the ``mammoth run`` lines that undo it.
* ``undone`` is written when ``history undo`` has run the compensation.

What can be undone (a saga's compensations, run in reverse order):

* a pipeline edit (``reversible_pipeline``): apply the view's pipeline version from
  before the edit, or, when the view had none yet, delete the steps the edit added;
* an object a write made (``meta.opens`` with ``created``): move it to the trash;
* a move to the trash: restore it, and a restore: move it back.

A permanent delete, an export, a send or any other effect outside Mammoth has no
compensation: its ``end`` record says why, and ``history undo`` reports it instead of
pretending. An embedded call is never journaled: the host serves many users.

Records are JSON Lines in ``<log dir>/journal/journal.jsonl``, owner-only, rotated at
:data:`MAX_BYTES`. ``MAMMOTH_CLI_JOURNAL=0`` (also false, no, off) turns the journal off.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime import embedded, trace
from mammoth_cli.runtime.dispatch import Next, Outcome, Request
from mammoth_cli.runtime.runlog import log_dir
from mammoth_cli.runtime.session import open_service
from mammoth_cli.runtime.switches import switched_on

JOURNAL_ENV = "MAMMOTH_CLI_JOURNAL"
#: The journal file is rotated to ``journal.1.jsonl`` past this size.
MAX_BYTES = 10 * 1024 * 1024

#: The manifest mutation class of a read; reads are not journaled.
_READ = "read"
_REVERSIBLE_PIPELINE = "reversible_pipeline"
_VERSION_LIST = "mammoth.api.pipeline_versions.PipelineVersionsAPI.list"
_TASK_LIST = "mammoth.api.pipeline.PipelineAPI.list_tasks"
_FIND_DATASET = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
#: The API lists versions oldest first unless asked otherwise.
_NEWEST_FIRST = "(id:desc)"

#: Kinds of object a write can make that the trash takes back, and the command that does.
_TRASH_COMMAND = {
    "view": "view trash",
    "dataset": "dataset trash",
    "dashboard": "dashboard trash",
    "automation": "automation trash",
    "folder": "folder trash",
}
#: A move to the trash and the command that reverses it, both ways.
_INVERSE = {
    "view.trash": "view restore",
    "view.restore": "view trash",
    "dataset.trash": "dataset restore",
    "dataset.restore": "dataset trash",
    "dashboard.trash": "dashboard restore",
    "dashboard.restore": "dashboard trash",
    "automation.trash": "automation restore",
    "automation.restore": "automation trash",
    "trash.add": "trash restore",
    "trash.restore": "trash add",
}
#: Positional names that hold the view a pipeline command edits.
_VIEW_POSITIONALS = ("view_id", "dataview_id")


class JournalStore(Protocol):
    """Where journal records are kept (the Repository port)."""

    def append(self, record: Mapping[str, Any]) -> None:
        """Keep one record; never raises."""
        ...

    def records(self) -> Iterable[dict[str, Any]]:
        """Every kept record, oldest first."""
        ...


class FileJournal:
    """Journal records as JSON Lines in one owner-only file, rotated once.

    Args:
        directory: Where ``journal.jsonl`` lives; created on the first write.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._path = directory / "journal.jsonl"

    def append(self, record: Mapping[str, Any]) -> None:
        """Append one record; a journal that cannot be written never fails the command.

        Args:
            record: A JSON-serialisable record.
        """
        line = json.dumps(record, sort_keys=True, default=str, separators=(",", ":")) + "\n"
        try:
            self._directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            if self._path.exists() and self._path.stat().st_size > MAX_BYTES:
                os.replace(self._path, self._directory / "journal.1.jsonl")
            fd = os.open(self._path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as handle:
                handle.write(line)
        except OSError:
            return

    def records(self) -> Iterable[dict[str, Any]]:
        """Read every record, the rotated file first; unreadable lines are skipped.

        Yields:
            Each record, oldest first.
        """
        for path in (self._directory / "journal.1.jsonl", self._path):
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for text in lines:
                try:
                    record = json.loads(text)
                except ValueError:
                    continue
                if isinstance(record, dict):
                    yield record


def journal_dir() -> Path:
    """The journal's directory, inside the run-log directory (``MAMMOTH_LOG_DIR`` moves both).

    Returns:
        ``<log dir>/journal``; not created.
    """
    return log_dir() / "journal"


def default_store() -> JournalStore | None:
    """The journal this process writes to.

    Returns:
        The file journal, or None when it is switched off or the call is embedded.
    """
    if embedded.active() or not switched_on(JOURNAL_ENV):
        return None
    return FileJournal(journal_dir())


@dataclass
class Entry:
    """One journaled write, folded from its records.

    Attributes:
        inv: The invocation id (the run log's ``run_id``).
        group: The outermost invocation: one for a whole ``mammoth run``.
        command: The command id.
        started: When the write began (UTC, ISO 8601).
        profile: The profile it ran with, if any.
        project_id: The project it ran in, if any.
        exit: Its exit status; None while its outcome is unknown.
        opens: The objects it made or changed.
        undo: The ``mammoth run`` lines that undo it, in order.
        irreversible: Why it cannot be undone, when it cannot.
        undone_by: The invocation that undid it, once undone.
    """

    inv: str
    group: str
    command: str
    started: str
    profile: str | None = None
    project_id: int | None = None
    exit: int | None = None
    opens: list[dict[str, Any]] = field(default_factory=list)
    undo: list[dict[str, Any]] = field(default_factory=list)
    irreversible: str | None = None
    undone_by: str | None = None

    def view(self) -> dict[str, Any]:
        """The entry as ``history`` shows it.

        Returns:
            A JSON-ready mapping, with ``status`` one of ``unknown``, ``failed``, ``done``
            or ``undone``.
        """
        if self.undone_by is not None:
            status = "undone"
        elif self.exit is None:
            status = "unknown"
        else:
            status = "done" if self.exit == 0 else "failed"
        return {
            "inv": self.inv,
            "group": self.group,
            "command": self.command.replace(".", " "),
            "started": self.started,
            "status": status,
            "exit": self.exit,
            "profile": self.profile,
            "project_id": self.project_id,
            "opens": self.opens,
            "undo": self.undo,
            "undoable": status == "done" and bool(self.undo),
            "irreversible": self.irreversible,
            "undone_by": self.undone_by,
        }


def entries(store: JournalStore) -> list[Entry]:
    """Fold the journal's records into entries, oldest first.

    Args:
        store: The journal to read.

    Returns:
        One entry per journaled write.
    """
    found: dict[str, Entry] = {}
    for record in store.records():
        inv = record.get("inv")
        if not isinstance(inv, str):
            continue
        event = record.get("event")
        if event == "begin":
            found[inv] = Entry(
                inv=inv,
                group=str(record.get("group") or inv),
                command=str(record.get("command") or ""),
                started=str(record.get("ts") or ""),
                profile=record.get("profile"),
                project_id=record.get("project_id"),
            )
            continue
        entry = found.get(inv)
        if entry is None:
            continue
        if event == "end":
            entry.exit = record.get("exit")
            entry.opens = list(record.get("opens") or [])
            entry.undo = list(record.get("undo") or [])
            entry.irreversible = record.get("irreversible")
        elif event == "undone":
            entry.undone_by = record.get("by")
    return list(found.values())


def _now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")


@dataclass
class _Before:
    """What a write's compensation needs to know from before it ran."""

    view_id: int | None = None
    dataset_id: int | None = None
    version_id: int | None = None
    task_ids: list[int] | None = None


#: Reads the state a pipeline edit's undo needs: ``(request) -> _Before``.
BeforeReader = Callable[[Request], _Before]


def _positional_id(request: Request, names: Iterable[str]) -> int | None:
    invocation = request.invocation
    if invocation is None:
        return None
    for name in names:
        value = invocation.positionals.get(name)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None


def read_before(request: Request) -> _Before:
    """Read a view's latest pipeline version (or its steps) before a pipeline edit.

    One version read, plus one step listing only when the view has no version yet.
    A read that fails leaves the edit without an undo; it never stops the edit.

    Args:
        request: The pipeline edit about to run.

    Returns:
        The view, its dataset, and its latest version id or its current step ids.
    """
    view_id = _positional_id(request, _VIEW_POSITIONALS)
    invocation = request.invocation
    if view_id is None or invocation is None:
        return _Before()
    before = _Before(view_id=view_id)
    try:
        with open_service(invocation) as (service, _auth):
            dataset_id = int(service.call(_FIND_DATASET, dataview_id=view_id))
            before.dataset_id = dataset_id
            listing = service.call(
                _VERSION_LIST,
                dataset_id=dataset_id,
                dataview_id=view_id,
                sort=_NEWEST_FIRST,
                limit=1,
            )
            versions = listing.get("versions") if isinstance(listing, dict) else None
            if versions:
                before.version_id = int(versions[0]["id"])
            else:
                tasks = service.call(_TASK_LIST, dataview_id=view_id, dataset_id=dataset_id)
                rows = tasks.get("tasks") if isinstance(tasks, dict) else tasks
                before.task_ids = [int(task["id"]) for task in rows or [] if "id" in task]
    except Exception:  # noqa: BLE001 -- a failed read costs the undo, never the edit
        return _Before(view_id=view_id)
    return before


def compensation(
    request: Request, outcome: Outcome, before: _Before
) -> tuple[list[dict[str, Any]], str | None]:
    """The ``mammoth run`` lines that undo a write that succeeded, in order.

    Args:
        request: The write.
        outcome: Its successful outcome.
        before: What :func:`read_before` saw, for a pipeline edit.

    Returns:
        The lines, and why the write cannot be undone when there are none.
    """
    command_id = request.command_id
    flags = _flags(request, outcome)
    record = command_by_id(command_id) or {}
    mutation = record.get("mutation_class")
    if command_id in _INVERSE:
        line: dict[str, Any] = {"cmd": _INVERSE[command_id], "flags": flags}
        args = _positional_args(request, record)
        if args:
            line["args"] = args
        document = request.invocation.bound_input() if request.invocation else None
        if command_id.startswith("trash.") and document:
            line["input"] = document
        return [line], None
    if mutation == _REVERSIBLE_PIPELINE:
        return _pipeline_undo(before, flags)
    created = [
        {"cmd": _TRASH_COMMAND[o["kind"]], "args": [o["id"]], "flags": flags}
        for o in outcome.meta.get("opens") or []
        if o.get("created") and o.get("kind") in _TRASH_COMMAND and o.get("id") is not None
    ]
    if created:
        return list(reversed(created)), None
    if mutation == "destructive":
        return [], "It deleted something permanently; Mammoth keeps no copy to restore."
    if mutation == "external_effect":
        return [], "Its effect is outside Mammoth (an export, a message or a send)."
    return [], "No command reverses it."


def _pipeline_undo(
    before: _Before, flags: dict[str, Any]
) -> tuple[list[dict[str, Any]], str | None]:
    if before.view_id is None:
        return [], "The view it edited is not known."
    view = before.view_id
    if before.version_id is not None:
        args: list[Any] = [view, before.version_id]
        if before.dataset_id is not None:
            args.append(before.dataset_id)
        return [{"cmd": "view version apply", "args": args, "flags": flags}], None
    if before.task_ids is None:
        return [], "The view's pipeline could not be read before the edit."
    # No version yet: the steps the edit added are the ones not there before. Which
    # ones is only known once the edit ran, so the line lists them when it is undone.
    return [
        {
            "cmd": "view task delete",
            "args": [view],
            "flags": {**flags, "yes": True},
            "keep_tasks": before.task_ids,
        }
    ], None


def _flags(request: Request, outcome: Outcome) -> dict[str, Any]:
    flags: dict[str, Any] = {}
    if request.profile:
        flags["profile"] = request.profile
    project = outcome.meta.get("project_id")
    if project is None and request.invocation is not None:
        project = request.invocation.project
    if project is not None:
        flags["project"] = project
    return flags


def _positional_args(request: Request, record: Mapping[str, Any]) -> list[Any]:
    invocation = request.invocation
    if invocation is None:
        return []
    args = []
    for positional in record.get("positionals") or []:
        value = invocation.positionals.get(positional.get("name"))
        if value is None:
            break
        args.append(value)
    return args


def journal_writes(
    store_for: Callable[[], JournalStore | None] = default_store,
    before_reader: BeforeReader = read_before,
) -> Callable[[Request, Next], Outcome]:
    """Build the interceptor that journals every write and its compensation.

    Args:
        store_for: Returns the journal to write to, or None for no journal.
        before_reader: Reads what a pipeline edit's undo needs before it runs.

    Returns:
        A :data:`~mammoth_cli.runtime.dispatch.Interceptor`.
    """

    def interceptor(request: Request, call_next: Next) -> Outcome:
        record = command_by_id(request.command_id) or {}
        mutation = record.get("mutation_class")
        invocation = request.invocation
        if (
            mutation in (None, _READ)
            or invocation is None
            or invocation.dry_run
            or request.command_id.startswith("history.")
        ):
            return call_next(request)
        store = store_for()
        if store is None:
            return call_next(request)
        traced = trace.current()
        inv = traced.invocation_id if traced is not None else ""
        before = before_reader(request) if mutation == _REVERSIBLE_PIPELINE else _Before()
        store.append(
            {
                "event": "begin",
                "inv": inv,
                "group": traced.group if traced is not None else inv,
                "ts": _now(),
                "command": request.command_id,
                "profile": request.profile,
                "project_id": invocation.project,
            }
        )
        outcome = call_next(request)
        end: dict[str, Any] = {"event": "end", "inv": inv, "ts": _now()}
        if outcome.error is not None:
            end.update(exit=outcome.error.exit_status, error_code=outcome.error.code)
        else:
            lines, reason = compensation(request, outcome, before)
            end.update(
                exit=outcome.exit_status,
                opens=outcome.meta.get("opens") or [],
                undo=lines,
                irreversible=reason,
            )
        store.append(end)
        return outcome

    return interceptor


def mark_undone(store: JournalStore, inv: str, by: str) -> None:
    """Record that ``inv`` was undone by the invocation ``by``.

    Args:
        store: The journal.
        inv: The undone write.
        by: The ``history undo`` invocation that undid it.
    """
    store.append({"event": "undone", "inv": inv, "by": by, "ts": _now()})
