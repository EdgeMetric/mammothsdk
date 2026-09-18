"""Always-on, per-invocation JSONL run log.

Every CLI invocation appends structured records to one file per day under
the log directory (``MAMMOTH_LOG_DIR``, else the platform state dir, on
Linux ``~/.local/state/mammoth-cli/logs``). Records come from three
sources:

- this module: ``command.start`` / ``command.end`` (argv with the
  ``--input`` document redacted, profile, project, versions, exit status,
  error code, duration);
- the SDK's ``mammoth`` loggers: one ``http`` record per request (method,
  path, status, duration, request id) and one ``job.poll`` record per job
  observation;
- ``mammoth_cli`` loggers, for anything a handler chooses to record.

The log never carries credentials: the SDK does not log headers or bodies,
argv redaction removes the ``--input`` document (it may hold export
passwords), and every record passes through the output normaliser's secret
redaction before it is written. Logging must never fail a command: every
filesystem operation is wrapped, and a failure silently disables the log
for the rest of the invocation.

``--debug`` mirrors the same records to stderr in a readable one-line form.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import platformdirs

from mammoth_cli import __version__ as _cli_version
from mammoth_cli.output.normalize import normalize

LOG_DIR_ENV = "MAMMOTH_LOG_DIR"
RETENTION_DAYS = 7
MAX_FILE_BYTES = 20 * 1024 * 1024
_LOGGER_NAMES = ("mammoth", "mammoth_cli")
_INPUT_OPTION = "--input"
_REDACTED_INPUT = "<redacted --input>"


def log_dir() -> Path:
    """Return the directory run logs are written to (not created)."""
    override = os.environ.get(LOG_DIR_ENV)
    if override:
        return Path(override).expanduser()
    return Path(platformdirs.user_state_dir("mammoth-cli", "Mammoth")) / "logs"


def log_file_for(day: _dt.date) -> Path:
    return log_dir() / f"{day.isoformat()}.jsonl"


def redact_argv(argv: list[str]) -> list[str]:
    """Return ``argv`` with the ``--input`` document replaced.

    ``--input`` may carry export credentials; ``--confirm`` is a resource id
    and is kept. Both ``--input DOC`` and ``--input=DOC`` forms are handled.
    """
    out: list[str] = []
    skip = False
    for arg in argv:
        if skip:
            out.append(_REDACTED_INPUT)
            skip = False
            continue
        if arg == _INPUT_OPTION:
            out.append(arg)
            skip = True
            continue
        if arg.startswith(_INPUT_OPTION + "="):
            out.append(f"{_INPUT_OPTION}={_REDACTED_INPUT}")
            continue
        out.append(arg)
    return out


class _JsonlHandler(logging.Handler):
    """Write each record as one JSON line; disable itself on the first failure."""

    def __init__(self, run: RunLog) -> None:
        super().__init__(level=logging.DEBUG)
        self._run = run

    def emit(self, record: logging.LogRecord) -> None:
        payload = getattr(record, "mammoth", None)
        if isinstance(payload, dict):
            body: dict[str, Any] = dict(payload)
            body.setdefault("event", record.name)
        else:
            body = {"event": record.name, "message": record.getMessage()}
        if record.exc_info and record.exc_info[0] is not None:
            body["exception"] = record.exc_info[0].__name__
        self._run.write(body, level=record.levelname.lower(), logger=record.name)


class _StderrHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        payload = getattr(record, "mammoth", None)
        if isinstance(payload, dict):
            fields = " ".join(f"{k}={v}" for k, v in payload.items() if k != "event")
            line = f"[mammoth {payload.get('event', record.name)}] {fields}"
        else:
            line = f"[{record.name}] {record.getMessage()}"
        try:
            sys.stderr.write(line + "\n")
        except Exception:  # noqa: S110 - a closed stderr must not fail the command
            pass


@dataclass
class RunLog:
    """One invocation's log session."""

    run_id: str
    command_id: str
    path: Path | None
    started: float = field(default_factory=time.monotonic)
    _file: Any = None
    _handlers: list[tuple[logging.Logger, logging.Handler]] = field(default_factory=list)
    _previous_levels: dict[str, int] = field(default_factory=dict)
    _disabled: bool = False

    # -- lifecycle --------------------------------------------------------

    @classmethod
    def start(
        cls,
        command_id: str,
        *,
        argv: list[str] | None = None,
        profile: str | None = None,
        project_id: int | None = None,
        debug: bool = False,
    ) -> RunLog:
        run_id = uuid.uuid4().hex[:12]
        path: Path | None = log_file_for(_dt.date.today())
        run = cls(run_id=run_id, command_id=command_id, path=path)
        run.open()
        run.attach(debug=debug)
        try:
            from mammoth import __version__ as sdk_version
        except Exception:  # pragma: no cover - SDK import failure is reported elsewhere
            sdk_version = None  # type: ignore[assignment]
        run.write(
            {
                "event": "command.start",
                "argv": redact_argv(list(sys.argv[1:] if argv is None else argv)),
                "profile": profile,
                "project_id": project_id,
                "cli_version": _cli_version,
                "sdk_version": sdk_version,
                "pid": os.getpid(),
                "python": sys.version.split()[0],
            }
        )
        return run

    def finish(self, exit_status: int, *, error_code: str | None = None) -> None:
        self.write(
            {
                "event": "command.end",
                "exit_status": exit_status,
                "error_code": error_code,
                "duration_ms": round((time.monotonic() - self.started) * 1000),
            }
        )
        self.detach()
        self.close()

    @property
    def ref(self) -> dict[str, Any] | None:
        """The ``log_ref`` an error envelope carries: where to look."""
        if self._disabled or self.path is None:
            return None
        return {"file": str(self.path), "run_id": self.run_id}

    # -- writing ----------------------------------------------------------

    def write(
        self, body: dict[str, Any], *, level: str = "info", logger: str = "mammoth_cli"
    ) -> None:
        if self._disabled or self._file is None:
            return
        record = {
            "ts": _dt.datetime.now(_dt.UTC).isoformat(timespec="milliseconds"),
            "run_id": self.run_id,
            "command_id": self.command_id,
            "level": level,
            "logger": logger,
            **normalize(body, redact_secrets=True),
        }
        try:
            self._file.write(json.dumps(record, separators=(",", ":"), default=str) + "\n")
            self._file.flush()
        except Exception:
            self._disabled = True

    # -- internals --------------------------------------------------------

    def open(self) -> None:
        if self.path is None:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if os.name == "posix":
                os.chmod(self.path.parent, 0o700)
            _rotate(self.path)
            self._file = open(self.path, "a", encoding="utf-8")
            if os.name == "posix":
                os.chmod(self.path, 0o600)
        except Exception:
            self._disabled = True
            self._file = None

    def close(self) -> None:
        try:
            if self._file is not None:
                self._file.close()
        except Exception:  # noqa: S110 - closing a log file must not fail the command
            pass
        self._file = None

    def attach(self, *, debug: bool) -> None:
        if self._disabled:
            return
        level = logging.DEBUG if debug else logging.INFO
        for name in _LOGGER_NAMES:
            logger = logging.getLogger(name)
            self._previous_levels[name] = logger.level
            if logger.level == logging.NOTSET or logger.level > level:
                logger.setLevel(level)
            handlers: list[logging.Handler] = [_JsonlHandler(self)]
            if debug:
                handlers.append(_StderrHandler(level=level))
            for handler in handlers:
                logger.addHandler(handler)
                self._handlers.append((logger, handler))

    def detach(self) -> None:
        for logger, handler in self._handlers:
            logger.removeHandler(handler)
        for name, level in self._previous_levels.items():
            logging.getLogger(name).setLevel(level)
        self._handlers.clear()


def _rotate(path: Path) -> None:
    """Keep the log directory bounded: age out old days, cap today's size."""
    directory = path.parent
    cutoff = _dt.date.today() - _dt.timedelta(days=RETENTION_DAYS)
    for candidate in directory.glob("*.jsonl"):
        stem = candidate.name.split(".", 1)[0]
        try:
            day = _dt.date.fromisoformat(stem)
        except ValueError:
            continue
        if day < cutoff:
            try:
                candidate.unlink()
            except OSError:
                pass
    try:
        if path.exists() and path.stat().st_size > MAX_FILE_BYTES:
            path.replace(path.with_name(f"{path.stem}.1.jsonl"))
    except OSError:
        pass


def log_path() -> dict[str, Any]:
    """``mammoth log path``: where the run log lives and which days are present."""
    directory = log_dir()
    try:
        days = sorted(candidate.name for candidate in directory.glob("*.jsonl"))
    except OSError:
        days = []
    return {
        "directory": str(directory),
        "today": str(log_file_for(_dt.date.today())),
        "files": days,
        "retention_days": RETENTION_DAYS,
        "override_env": LOG_DIR_ENV,
    }


def read_records(
    *,
    days: int = 1,
    limit: int = 50,
    errors_only: bool = False,
    command_id: str | None = None,
    run_id: str | None = None,
) -> list[dict[str, Any]]:
    """``mammoth log tail``: the most recent matching records, oldest first.

    ``days`` counts back from today (1 = today only); ``errors_only`` keeps
    warnings, errors, HTTP >= 400 and non-zero ``command.end`` records;
    ``command_id`` / ``run_id`` narrow to one command or one invocation
    (the ``run_id`` an error envelope's ``log_ref`` names).
    """
    today = _dt.date.today()
    files = [log_file_for(today - _dt.timedelta(days=offset)) for offset in range(days)]
    records: list[dict[str, Any]] = []
    for candidate in reversed(files):
        for extra in (candidate.with_name(f"{candidate.stem}.1.jsonl"), candidate):
            try:
                lines = extra.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in lines:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if command_id and record.get("command_id") != command_id:
                    continue
                if run_id and record.get("run_id") != run_id:
                    continue
                if errors_only and not _is_error(record):
                    continue
                records.append(record)
    return records[-limit:] if limit > 0 else records


def _is_error(record: dict[str, Any]) -> bool:
    if record.get("level") in {"error", "warning"}:
        return True
    if record.get("event") == "command.end" and record.get("exit_status") not in (0, None):
        return True
    status = record.get("status")
    return isinstance(status, int) and status >= 400
