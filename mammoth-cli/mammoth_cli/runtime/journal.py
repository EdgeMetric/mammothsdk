"""The journal: one record before and one after every write, and how to undo it.

The run log (:mod:`mammoth_cli.runtime.runlog`) says what happened, for debugging. The
journal says what changed and how to change it back, for ``mammoth history``:

* ``begin`` is written before the write is sent (write-ahead), so a crash between the
  request and the answer still leaves a record of a write whose outcome is unknown.
* ``end`` is written after it, with the exit status, the objects the write made or
  changed (``meta.opens``) and its compensation: the ``mammoth run`` lines that undo it.
* ``undone`` is written when ``history undo`` has run the compensation.
* ``plan`` is written when a ``mammoth run`` or ``recipe run`` starts (its lines, the
  flags they share and the recipe's inputs), and ``step`` after each of its lines (its
  exit, and a named line's result up to :data:`MAX_STEP_BYTES`), so ``history resume``
  can go on from the first line that did not finish.

What can be undone is declared by each command's manifest ``undo`` (derived by
``scripts/_undo_rules.py``, overridden in ``spec/manifests/commands/<group>.yaml``), and
:func:`compensation` only reads it (a saga's compensations, run in reverse order):

* ``inverse``: run the named command with the write's own arguments (a move to the trash
  and its restore, a pause and its resume);
* ``pipeline_version``: apply the view's pipeline version from before the edit, or, when
  the view had none yet, delete the steps the edit added;
* ``trash_created``: move the objects the write made (``meta.opens`` with ``created``) to
  the trash;
* ``manual``: a command reverses it but needs an id the write made, so it is named in the
  reason and not run;
* ``irreversible`` (a permanent delete, an export, a send or any other effect outside
  Mammoth): no compensation. The ``end`` record gives the manifest's reason, and
  ``history undo`` reports it instead of pretending.
An embedded call is never journaled: the host serves many users.

Records are JSON Lines in ``<log dir>/journal/journal.jsonl``, owner-only, rotated at
:data:`MAX_BYTES`. The records of a run (``plan``, ``step``, ``item``, ``resume``) are kept
apart, one file per run in ``journal/runs/``, so a rotation never drops a plan that can still
be resumed; those files are pruned after :data:`RUN_KEEP_DAYS`. Every append takes an
advisory lock (``journal.lock``) and is one ``write``, so processes writing at once neither
interleave records nor overwrite each other's rotation. The run records hold no secret: a
value under a credential-looking key is stored as :data:`~mammoth_cli.output.normalize.REDACTED`,
and ``history resume`` refuses a line that needs one. ``MAMMOTH_CLI_JOURNAL=0`` (also false,
no, off) turns the journal off.
"""

from __future__ import annotations

import contextlib
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import time
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from mammoth_cli.context.resolver import env_token_in_use
from mammoth_cli.errors.envelope import CODE_ABORTED, EXIT_PARTIAL, EXIT_USAGE
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.output.normalize import REDACTED, normalize
from mammoth_cli.runtime import embedded, trace
from mammoth_cli.runtime.dispatch import Next, Outcome, Request
from mammoth_cli.runtime.runlog import log_dir
from mammoth_cli.runtime.session import open_service
from mammoth_cli.runtime.switches import switched_on

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

JOURNAL_ENV = "MAMMOTH_CLI_JOURNAL"
#: The journal file is rotated to ``journal.1.jsonl`` past this size.
MAX_BYTES = 10 * 1024 * 1024

#: The largest named-line result a ``step`` record keeps for ``history resume``.
MAX_STEP_BYTES = 256 * 1024
#: Run files (``journal/runs/<group>.jsonl``) older than this are deleted when a run starts.
RUN_KEEP_DAYS = 60

#: The events of a ``mammoth run`` or ``recipe run``, kept in the run's own file.
_RUN_EVENTS = frozenset({"plan", "step", "item", "resume", "ack"})
#: The commands that only run other commands; their lines are the journal entries, not them.
CONTAINER_COMMANDS = frozenset({"run", "recipe.run"})

#: What a write signed in with, kept in its ``begin`` record for the undo.
AUTH_PROFILE = "profile"
AUTH_ENV = "env"
#: ``error.code`` values of a failure after the write may have been sent.
_UNCERTAIN_CODES = frozenset({"interrupted", "timeout", "outcome_unknown"})
#: ``error.details.operation_state`` values that say the same.
_UNCERTAIN_STATES = frozenset({"outcome_unknown", "running"})
_UNSAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]")
#: Keys of a task that change without the pipeline changing, left out of its fingerprint.
_VOLATILE_TASK_KEYS = frozenset(
    {"id", "sequence", "transform_status", "reference_errors", "created", "updated"}
)

#: The manifest mutation class of a read; reads are not journaled.
_READ = "read"
#: The ``undo.strategy`` values a command's manifest declares (see ``scripts/_undo_rules.py``).
_INVERSE = "inverse"
_PIPELINE_VERSION = "pipeline_version"
_TRASH_CREATED = "trash_created"
_MANUAL = "manual"
_IRREVERSIBLE = "irreversible"
_VERSION_LIST = "mammoth.api.pipeline_versions.PipelineVersionsAPI.list"
_TASK_LIST = "mammoth.api.pipeline.PipelineAPI.list_tasks"
_FIND_DATASET = "mammoth.api.pipeline.PipelineAPI.find_dataset_for_dataview"
#: The API lists versions oldest first unless asked otherwise.
_NEWEST_FIRST = "(id:desc)"

#: Kinds of object a write can make that the trash takes back, and the command that does.
TRASH_COMMAND = {
    "view": "view trash",
    "dataset": "dataset trash",
    "dashboard": "dashboard trash",
    "automation": "automation trash",
    "folder": "folder trash",
}
#: Positional names that hold the view a pipeline command edits.
_VIEW_POSITIONALS = ("view_id", "dataview_id")


class JournalBusy(Exception):
    """Another process holds the claim that was asked for."""


class JournalStore(Protocol):
    """Where journal records are kept (the Repository port)."""

    def append(self, record: Mapping[str, Any]) -> None:
        """Keep one record; never raises."""
        ...

    def records(self) -> Iterable[dict[str, Any]]:
        """Every kept record, oldest first."""
        ...

    def claim(self, name: str) -> contextlib.AbstractContextManager[None]:
        """Hold an exclusive claim on ``name`` for the block; raise :class:`JournalBusy`."""
        ...


def _lock(fd: int, *, blocking: bool) -> None:
    """Take the advisory lock on ``fd``; raise ``OSError`` when it is held and not blocking."""
    if sys.platform == "win32":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(fd: int) -> None:
    if sys.platform == "win32":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)


@contextlib.contextmanager
def _locked_file(path: Path, *, blocking: bool) -> Iterator[None]:
    """Hold the advisory lock on the file at ``path`` (made when missing) for the block."""
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        _lock(fd, blocking=blocking)
        try:
            yield
        finally:
            _unlock(fd)
    finally:
        os.close(fd)


def _write_all(path: Path, data: bytes) -> None:
    """Append ``data`` to ``path`` with ``write`` on an ``O_APPEND`` descriptor."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view) :]
    finally:
        os.close(fd)


class FileJournal:
    """Journal records as JSON Lines in owner-only files, rotated once.

    Args:
        directory: Where ``journal.jsonl`` lives; created on the first write.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._path = directory / "journal.jsonl"
        self._runs = directory / "runs"

    def append(self, record: Mapping[str, Any]) -> None:
        """Append one record; a journal that cannot be written never fails the command.

        Args:
            record: A JSON-serialisable record.
        """
        data = (
            json.dumps(record, sort_keys=True, default=str, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        try:
            self._directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            with _locked_file(self._directory / "journal.lock", blocking=True):
                if record.get("event") in _RUN_EVENTS and record.get("group"):
                    self._append_run(record, data)
                    return
                if self._path.exists() and self._path.stat().st_size > MAX_BYTES:
                    os.replace(self._path, self._directory / "journal.1.jsonl")
                _write_all(self._path, data)
        except OSError:
            return

    def _append_run(self, record: Mapping[str, Any], data: bytes) -> None:
        self._runs.mkdir(mode=0o700, parents=True, exist_ok=True)
        if record.get("event") == "plan":
            self._prune_runs()
        _write_all(self._runs / f"{_UNSAFE_NAME.sub('_', str(record['group']))}.jsonl", data)

    def _prune_runs(self) -> None:
        oldest = time.time() - RUN_KEEP_DAYS * 86400
        for path in (*self._runs.glob("*.jsonl"), *self._directory.glob("undo-*.lock")):
            try:
                if path.stat().st_mtime < oldest:
                    path.unlink()
            except OSError:
                continue

    @contextlib.contextmanager
    def claim(self, name: str) -> Iterator[None]:
        """Hold an exclusive claim on ``name`` (released when the process dies).

        Args:
            name: What is claimed, such as ``undo-<inv>``.

        Yields:
            Nothing, while the claim is held.

        Raises:
            JournalBusy: Another process holds the claim.
        """
        path = self._directory / f"{_UNSAFE_NAME.sub('_', name)}.lock"
        stack = contextlib.ExitStack()
        try:
            self._directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            stack.enter_context(_locked_file(path, blocking=False))
        except (BlockingIOError, PermissionError) as error:
            raise JournalBusy(name) from error
        except OSError:
            # A journal that cannot be written cannot be claimed either; do not block the undo.
            pass
        with stack:
            yield

    def records(self) -> Iterable[dict[str, Any]]:
        """Read every record: the rotated file, the journal, then each run's file.

        Unreadable lines are skipped.

        Yields:
            Each record, oldest first (a run's records by the time they were written).
        """
        try:
            runs = sorted(self._runs.glob("*.jsonl"), key=lambda path: path.stat().st_mtime)
        except OSError:
            runs = []
        for path in (self._directory / "journal.1.jsonl", self._path, *runs):
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
        auth: ``profile`` when it ran with a stored profile, ``env`` when it ran with
            ``MAMMOTH_API_TOKEN``; None for a record from before this was kept.
        project_id: The project it ran in, if any.
        exit: Its exit status; None while its outcome is unknown.
        opens: The objects it made or changed.
        undo: The ``mammoth run`` lines that undo it, in order.
        irreversible: Why it cannot be undone, when it cannot.
        undone_by: The invocation that undid it, once undone.
        uncertain: Whether it failed after it may have been sent (interrupted, timed out,
            a lost connection, a job still running): it may have happened.
        acknowledged: Whether a later ``history resume`` was told to go on past it.
        undone_lines: How many of its undo lines ran already (an undo that stopped midway).
    """

    inv: str
    group: str
    command: str
    started: str
    profile: str | None = None
    auth: str | None = None
    project_id: int | None = None
    exit: int | None = None
    opens: list[dict[str, Any]] = field(default_factory=list)
    undo: list[dict[str, Any]] = field(default_factory=list)
    irreversible: str | None = None
    undone_by: str | None = None
    uncertain: bool = False
    acknowledged: bool = False
    undone_lines: int = 0

    def view(self) -> dict[str, Any]:
        """The entry as ``history`` shows it.

        Returns:
            A JSON-ready mapping, with ``status`` one of ``unknown``, ``failed``, ``done``
            or ``undone``.
        """
        if self.undone_by is not None:
            status = "undone"
        elif self.exit is None or self.uncertain:
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
            "undone_lines": self.undone_lines,
        }


def group_roots(records: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    """Map each group that resumed another run to the run it went on with.

    ``history resume`` journals under a group of its own; its ``resume`` record names the
    original run, and everything it did counts for that run (repeat resumes, undo, show).

    Args:
        records: The journal's records.

    Returns:
        ``{resuming group: the group of the run it started from}``, transitively resolved.
    """
    parent = {
        str(r["group"]): str(r["of"])
        for r in records
        if r.get("event") == "resume" and r.get("group") and r.get("of")
    }
    roots: dict[str, str] = {}
    for group in parent:
        seen = {group}
        root = parent[group]
        while root in parent and root not in seen:
            seen.add(root)
            root = parent[root]
        roots[group] = root
    return roots


def entries(store: JournalStore) -> list[Entry]:
    """Fold the journal's records into entries, oldest first.

    Args:
        store: The journal to read.

    Returns:
        One entry per journaled write. A container run's own record and a write that was
        refused before anything was sent are left out.
    """
    records = list(store.records())
    roots = group_roots(records)
    found: dict[str, Entry] = {}
    hidden: set[str] = set()
    for record in records:
        inv = record.get("inv")
        event = record.get("event")
        if event == "ack":
            _acknowledge(
                found.values(), roots.get(str(record.get("group")), record.get("group")), record
            )
            continue
        if not isinstance(inv, str):
            continue
        if event == "begin":
            if str(record.get("command") or "") in CONTAINER_COMMANDS:
                hidden.add(inv)
                continue
            group = str(record.get("group") or inv)
            found[inv] = Entry(
                inv=inv,
                group=roots.get(group, group),
                command=str(record.get("command") or ""),
                started=str(record.get("ts") or ""),
                profile=record.get("profile"),
                auth=record.get("auth"),
                project_id=record.get("project_id"),
            )
            continue
        entry = found.get(inv)
        if entry is None:
            continue
        if event == "end":
            if record.get("nothing_sent"):
                hidden.add(inv)
            entry.exit = record.get("exit")
            entry.opens = list(record.get("opens") or [])
            entry.undo = list(record.get("undo") or [])
            entry.irreversible = record.get("irreversible")
            entry.uncertain = bool(record.get("outcome_unknown"))
        elif event == "undone":
            entry.undone_by = record.get("by")
        elif event == "undo_step":
            entry.undone_lines = max(entry.undone_lines, int(record.get("lines") or 0))
    return [entry for inv, entry in found.items() if inv not in hidden]


def _acknowledge(found: Iterable[Entry], group: Any, ack: Mapping[str, Any]) -> None:
    """Mark the writes of ``group`` with an unknown outcome, begun before ``ack``, as checked."""
    for entry in found:
        if (
            entry.group == group
            and entry.started <= str(ack.get("ts") or "")
            and (entry.exit is None or entry.uncertain)
        ):
            entry.acknowledged = True


def _now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="microseconds")


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


def fingerprint(tasks: Iterable[Mapping[str, Any]]) -> str:
    """A hash of what a view's pipeline does, stable across a re-applied version.

    Args:
        tasks: The view's tasks, as ``view task list`` gives them.

    Returns:
        A short hex digest of the tasks in order, without their ids, sequence numbers,
        timestamps or run status. Secrets are redacted first, as the CLI output redacts
        them, so the raw SDK list and the ``view task list`` envelope give the same digest.
    """
    kept = [
        {
            key: value
            for key, value in task.items()
            if key not in _VOLATILE_TASK_KEYS and not key.endswith(("_id", "_at"))
        }
        for task in _without_secrets(list(tasks))
    ]
    text = json.dumps(kept, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


#: Reads the pipeline's fingerprint after an edit: ``(request, before) -> fingerprint | None``.
AfterReader = Callable[[Request, _Before], str | None]


def read_after(request: Request, before: _Before) -> str | None:
    """Fingerprint the pipeline the edit left, so an undo can tell if it changed since.

    Args:
        request: The pipeline edit that ran.
        before: What :func:`read_before` saw.

    Returns:
        The fingerprint, or None when the view could not be read (the undo then runs
        without the check).
    """
    invocation = request.invocation
    if before.view_id is None or before.dataset_id is None or invocation is None:
        return None
    try:
        with open_service(invocation) as (service, _auth):
            tasks = service.call(
                _TASK_LIST, dataview_id=before.view_id, dataset_id=before.dataset_id
            )
    except Exception:  # noqa: BLE001 -- a failed read costs the check, never the edit
        return None
    rows = tasks.get("tasks") if isinstance(tasks, dict) else tasks
    return fingerprint(rows) if isinstance(rows, list) else None


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
    undo = record.get("undo") or {}
    strategy = undo.get("strategy")
    if strategy == _INVERSE:
        target = command_by_id(undo["command"]) or {}
        args = _positional_args(request, record)
        flags.update(_carried_flags(request, target, args))
        line: dict[str, Any] = {"cmd": target.get("command_path", ""), "flags": flags}
        if args:
            line["args"] = args
        document = request.invocation.bound_input() if request.invocation else None
        if command_id.startswith("trash.") and document:
            line["input"] = document
        return [line], None
    if strategy == _PIPELINE_VERSION:
        return _pipeline_undo(before, flags)
    if strategy == _TRASH_CREATED:
        created = [
            {"cmd": TRASH_COMMAND[o["kind"]], "args": [o["id"]], "flags": flags}
            for o in outcome.meta.get("opens") or []
            if o.get("created") and o.get("kind") in TRASH_COMMAND and o.get("id") is not None
        ]
        if created:
            return list(reversed(created)), None
        if any(o.get("kind") == "dataset" for o in outcome.meta.get("opens") or []):
            return [], "It added to a dataset that already existed; rows cannot be taken out again."
        return [], "It made nothing the trash can take back."
    if strategy == _MANUAL:
        target = command_by_id(undo["command"]) or {}
        path = f"`mammoth {target.get('command_path', undo['command'])}`"
        if undo.get("note"):
            return [], f"{path} reverses it, but it is not run for you. {undo['note']}"
        return [], (
            f"{path} reverses it, but it needs the id this write made, so it is not run for you."
        )
    if strategy == _IRREVERSIBLE:
        return [], str(undo["reason"])
    return [], "No undo is declared for it."


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
    # A profile that was only the default (no --profile) is not recorded: an explicit
    # --profile outranks MAMMOTH_API_TOKEN, so the undo would run as the wrong account.
    invocation = request.invocation
    if request.profile and not (invocation is not None and invocation.profile_is_default):
        flags["profile"] = request.profile
    project = outcome.meta.get("project_id")
    if project is None and request.invocation is not None:
        project = request.invocation.project
    if project is not None:
        flags["project"] = project
    return flags


def _carried_flags(request: Request, target: Mapping[str, Any], args: list[Any]) -> dict[str, Any]:
    """The flags the inverse command needs that only the write's own call had.

    ``history undo`` runs the line with ``--yes`` alone, so a ``confirm_target`` inverse needs
    the id it will be asked to confirm (its last positional: the workspace of a partner
    detach, the only id of the others), and a command that works inside a chat session needs
    the ``--session`` the write was made with.

    Args:
        request: The write.
        target: The manifest record of the inverse command.
        args: The positional arguments the inverse line carries.

    Returns:
        The extra flags: ``confirm`` and ``session`` where they apply.
    """
    carried: dict[str, Any] = {}
    if target.get("confirmation") == "confirm_target" and args:
        carried["confirm"] = str(args[-1])
    invocation = request.invocation
    if invocation is not None and invocation.session:
        carried["session"] = invocation.session
    return carried


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
    after_reader: AfterReader = read_after,
) -> Callable[[Request, Next], Outcome]:
    """Build the interceptor that journals every write and its compensation.

    Args:
        store_for: Returns the journal to write to, or None for no journal.
        before_reader: Reads what a pipeline edit's undo needs before it runs.
        after_reader: Fingerprints the pipeline after an edit, for the undo's check.

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
            or request.command_id in CONTAINER_COMMANDS
        ):
            return call_next(request)
        store = store_for()
        if store is None:
            return call_next(request)
        traced = trace.current()
        inv = traced.invocation_id if traced is not None else ""
        strategy = (record.get("undo") or {}).get("strategy")
        before = before_reader(request) if strategy == _PIPELINE_VERSION else _Before()
        store.append(
            {
                "event": "begin",
                "inv": inv,
                "group": traced.group if traced is not None else inv,
                "ts": _now(),
                "command": request.command_id,
                "profile": request.profile,
                "auth": AUTH_ENV if env_token_in_use(invocation) else AUTH_PROFILE,
                "project_id": invocation.project,
            }
        )
        outcome = call_next(request)
        end: dict[str, Any] = {"event": "end", "inv": inv, "ts": _now()}
        if outcome.error is not None:
            end.update(exit=outcome.error.exit_status, error_code=outcome.error.code)
            if _refused_before_sending(outcome.error):
                end["nothing_sent"] = True
            elif _may_have_happened(outcome.error):
                end["outcome_unknown"] = True
        else:
            lines, reason = compensation(request, outcome, before)
            if strategy == _PIPELINE_VERSION and lines:
                after = after_reader(request, before)
                if after is not None:
                    lines = [{**line, "expect": after} for line in lines]
            end.update(
                exit=outcome.exit_status,
                opens=outcome.meta.get("opens") or [],
                undo=lines,
                irreversible=reason,
            )
        store.append(end)
        return outcome

    return interceptor


def _refused_before_sending(error: Any) -> bool:
    """Whether the command stopped on usage or a declined prompt: nothing reached the API."""
    return bool(error.exit_status == EXIT_USAGE or error.code == CODE_ABORTED)


def _may_have_happened(error: Any) -> bool:
    """Whether a failed write may still have taken effect (or still be running)."""
    state = (error.details or {}).get("operation_state")
    return bool(state in _UNCERTAIN_STATES or error.code in _UNCERTAIN_CODES)


def mark_undone(store: JournalStore, inv: str, by: str) -> None:
    """Record that ``inv`` was undone by the invocation ``by``.

    Args:
        store: The journal.
        inv: The undone write.
        by: The ``history undo`` invocation that undid it.
    """
    store.append({"event": "undone", "inv": inv, "by": by, "ts": _now()})


def mark_undo_step(store: JournalStore, inv: str, lines: int) -> None:
    """Record that the first ``lines`` undo lines of ``inv`` ran, so a retry skips them.

    Args:
        store: The journal.
        inv: The write being undone.
        lines: How many of its undo lines have run.
    """
    store.append({"event": "undo_step", "inv": inv, "lines": lines, "ts": _now()})


@dataclass
class Plan:
    """A journaled ``mammoth run`` or ``recipe run``, folded from its records.

    Attributes:
        group: The run's invocation id (the ``group`` of every write it made).
        command: ``run`` or ``recipe.run``.
        lines: Each line's physical number and text.
        defaults: The flags every line started from (flag -> token).
        scope: The values the lines read besides ``steps`` (a recipe's ``inputs``).
        keep_going: Whether the run went on past a failed line.
        past_partial: Whether the run went on past a partial line.
        finished: The lines that ran and exited 0 (or exited partial in a run that goes
            on past partial lines), by number.
        steps: The finished named lines' results, as later lines read them.
        line_steps: The same, by the line that made them.
        omitted: The named lines whose result was too large to keep.
        items: For a ``for_each`` line that did not finish, the data of each item that
            did, by item index.
    """

    group: str
    command: str
    lines: list[tuple[int, str]]
    defaults: dict[str, str] = field(default_factory=dict)
    scope: dict[str, Any] = field(default_factory=dict)
    keep_going: bool = False
    past_partial: bool = False
    finished: set[int] = field(default_factory=set)
    steps: dict[str, Any] = field(default_factory=dict)
    line_steps: dict[int, dict[str, Any]] = field(default_factory=dict)
    omitted: list[str] = field(default_factory=list)
    items: dict[int, dict[int, Any]] = field(default_factory=dict)

    def steps_without(self, rerun: Iterable[int]) -> dict[str, Any]:
        """The named results of the finished lines that are not about to run again.

        Args:
            rerun: The numbers of the lines the resume runs.

        Returns:
            The results to restore; a line that runs again makes its own name anew.
        """
        skip = set(rerun)
        restored: dict[str, Any] = {}
        for number in sorted(self.line_steps):
            if number not in skip:
                restored.update(self.line_steps[number])
        return restored

    def redacted_references(self) -> set[str]:
        """The references (``steps.NAME``, ``inputs.KEY``) whose journaled value was redacted."""
        found = {f"steps.{name}" for name, value in self.steps.items() if has_redacted(value)}
        for key, value in self.scope.items():
            if isinstance(value, Mapping):
                found |= {f"{key}.{name}" for name, item in value.items() if has_redacted(item)}
            elif has_redacted(value):
                found.add(key)
        return found


def has_redacted(value: Any) -> bool:
    """Whether ``value`` holds a secret the journal replaced.

    Args:
        value: A journaled document.

    Returns:
        True when :data:`~mammoth_cli.output.normalize.REDACTED` appears in it.
    """
    if isinstance(value, str):
        return value == REDACTED
    if isinstance(value, Mapping):
        return any(has_redacted(item) for item in value.values())
    if isinstance(value, list):
        return any(has_redacted(item) for item in value)
    return False


def _without_secrets(value: Any) -> Any:
    """``value`` with every credential-looking key's value replaced (as the output does)."""
    return json.loads(json.dumps(normalize(value), default=str))


def _redacted_line(text: str) -> str:
    """A run line's text with the secrets in its ``input`` (and other fields) replaced."""
    try:
        line = json.loads(text)
    except ValueError:
        return text
    if not isinstance(line, dict):
        return text
    return json.dumps(_without_secrets(line), default=str, separators=(",", ":"))


def record_plan(
    lines: Iterable[tuple[int, str]],
    defaults: Mapping[str, str],
    *,
    scope: Mapping[str, Any] | None,
    keep_going: bool,
    past_partial: bool,
) -> None:
    """Journal the lines a run is about to run, under the current group.

    Args:
        lines: Each line's physical number and text.
        defaults: The flags every line starts from.
        scope: The values the lines read besides ``steps``.
        keep_going: Whether the run goes on past a failed line.
        past_partial: Whether the run goes on past a partial line.
    """
    store, group = _run_store()
    if store is None:
        return
    current = trace.current()
    store.append(
        {
            "event": "plan",
            "group": group,
            "ts": _now(),
            "command": current.command_id if current is not None else "run",
            "lines": [[number, _redacted_line(text)] for number, text in lines],
            "defaults": dict(defaults),
            "scope": _without_secrets(dict(scope or {})),
            "keep_going": keep_going,
            "past_partial": past_partial,
        }
    )


def record_resume(of: str, *, acknowledged: bool) -> None:
    """Journal that the current run goes on with the run ``of``, under that run's group.

    Args:
        of: The group of the run being resumed.
        acknowledged: Whether the caller named the line to start from, which settles the
            writes of ``of`` whose outcome was unknown.
    """
    store, group = _run_store()
    if store is None:
        return
    store.append({"event": "resume", "group": group, "of": of, "ts": _now()})
    if acknowledged:
        store.append({"event": "ack", "group": of, "ts": _now()})


def record_step(number: int, exit_status: int, named: Mapping[str, Any]) -> None:
    """Journal one finished line of the current run.

    Args:
        number: The line's physical number.
        exit_status: Its exit status.
        named: The results the line added to ``steps`` (none for an unnamed line).
    """
    store, group = _run_store()
    if store is None:
        return
    kept: dict[str, Any] = {}
    omitted: list[str] = []
    for name, value in named.items():
        value = _without_secrets(value)
        size = len(json.dumps(value, default=str))
        if size <= MAX_STEP_BYTES:
            kept[name] = value
        else:
            omitted.append(name)
    record: dict[str, Any] = {
        "event": "step",
        "group": group,
        "ts": _now(),
        "line": number,
        "exit": exit_status,
        "steps": kept,
    }
    if omitted:
        record["omitted"] = omitted
    store.append(record)


def record_item(number: int, index: int, exit_status: int, data: Any) -> None:
    """Journal one finished item of a ``for_each`` line of the current run.

    Args:
        number: The line's physical number.
        index: The item's index in the list.
        exit_status: Its exit status.
        data: Its result data (dropped when it is larger than :data:`MAX_STEP_BYTES`).
    """
    store, group = _run_store()
    if store is None:
        return
    kept = _without_secrets(data)
    if len(json.dumps(kept, default=str)) > MAX_STEP_BYTES:
        kept = None
    store.append(
        {
            "event": "item",
            "group": group,
            "ts": _now(),
            "line": number,
            "index": index,
            "exit": exit_status,
            "data": kept,
        }
    )


def plan_for(store: JournalStore, group: str) -> Plan | None:
    """The journaled run with this group, with what it finished (resumes included).

    Args:
        store: The journal.
        group: The run's invocation id, or the group of a resume of it.

    Returns:
        The run, or None when the journal has no plan for it.
    """
    records = list(store.records())
    roots = group_roots(records)
    root = roots.get(group, group)
    mine = [
        record
        for record in records
        if roots.get(str(record.get("group")), record.get("group")) == root
        and record.get("event") in ("plan", "step", "item")
    ]
    # Records of a resume sit in a file of their own: put them in the order they happened.
    mine.sort(key=lambda record: str(record.get("ts") or ""))
    plan: Plan | None = None
    for record in mine:
        event = record.get("event")
        if event == "plan" and record.get("group") == root:
            plan = Plan(
                group=root,
                command=str(record.get("command") or "run"),
                lines=[(int(number), str(text)) for number, text in record.get("lines") or []],
                defaults=dict(record.get("defaults") or {}),
                scope=dict(record.get("scope") or {}),
                keep_going=bool(record.get("keep_going")),
                past_partial=bool(record.get("past_partial")),
            )
        elif plan is None:
            continue
        elif event == "step":
            _fold_step(plan, record)
        elif event == "item" and record.get("exit") == 0:
            line_items = plan.items.setdefault(int(record.get("line") or 0), {})
            line_items[int(record.get("index") or 0)] = record.get("data")
    if plan is not None:
        plan.steps = plan.steps_without(())
        for number in plan.finished:
            plan.items.pop(number, None)
    return plan


def _fold_step(plan: Plan, record: Mapping[str, Any]) -> None:
    """Add a ``step`` record to the plan: a line that did not finish restores nothing."""
    number = int(record.get("line") or 0)
    exit_status = record.get("exit")
    if exit_status == 0 or (plan.past_partial and exit_status == EXIT_PARTIAL):
        plan.finished.add(number)
        plan.line_steps[number] = dict(record.get("steps") or {})
        plan.omitted.extend(record.get("omitted") or [])
    else:
        plan.finished.discard(number)
        plan.line_steps.pop(number, None)


def _run_store() -> tuple[JournalStore | None, str]:
    """The journal and the current group, or None outside a journaled run."""
    current = trace.current()
    if current is None:
        return None, ""
    return default_store(), current.group
