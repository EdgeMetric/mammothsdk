"""Fuzz harness for the ``mammoth`` CLI: case generation, execution and the pass rule.

Everything here drives the real entry point (``python -m mammoth_cli``) in a child
process. Nothing in the CLI is mocked or stubbed. The one thing faked is the
network: the child runs logged out in an empty HOME and with every proxy variable
pointing at a closed local port, so a request that is somehow attempted fails at
once with a connection error (an acceptable outcome) instead of reaching a server.
"""

from __future__ import annotations

import json
import os
import queue
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pexpect

HERE = Path(__file__).resolve().parent
CLI_ROOT = HERE.parent.parent
REPO_ROOT = CLI_ROOT.parent

# Documented in docs/troubleshooting.md ("Exit codes").
NO_KEYRING_BACKEND = "keyring.backends.fail.Keyring"

EXIT_SET = frozenset({0, 1, 2, 4, 5, 6, 7, 130})

SUBPROCESS_TIMEOUT = 90
LONG_VALUE = "A" * 20_000
BOGUS_FLAG = "--bogus"
# A prompt is "waiting" once output stops this long while the process is alive.
PTY_IDLE = 4.0
PTY_FIRST_OUTPUT = 40.0
PTY_MAX_PROMPTS = 4
PTY_EOF_FEEDS = 3

_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07")
_TRACEBACK = re.compile(r"Traceback \(most recent call last\)")
_API_ERROR = re.compile(r"api_error|failed unexpectedly", re.IGNORECASE)
_CONNECTION_HINT = re.compile(r"connect|network|resolve|timed out|unreachable|proxy", re.IGNORECASE)


# --------------------------------------------------------------------------- tree


@dataclass(frozen=True)
class Param:
    name: str
    kind: str
    opts: tuple[str, ...]
    is_flag: bool
    required: bool
    type: str

    @property
    def long(self) -> str | None:
        return next((o for o in self.opts if o.startswith("--")), None)

    @property
    def takes_value(self) -> bool:
        return self.kind == "argument" or not self.is_flag


@dataclass(frozen=True)
class Node:
    path: tuple[str, ...]
    is_group: bool
    params: tuple[Param, ...]

    @property
    def command(self) -> str:
        return " ".join(self.path) or "(root)"


def child_env(home: Path) -> dict[str, str]:
    """Environment for every CLI child: isolated state, no real network."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("MAMMOTH_")}
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env[key] = "http://127.0.0.1:9"
    # The OS keyring is reached over the D-Bus session; a fuzzed login, logout or
    # profile delete must never find the developer's real one.
    env.pop("DBUS_SESSION_BUS_ADDRESS", None)
    # A fuzzed ``auth login`` must never open the developer's browser.
    env["BROWSER"] = "true"
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    env["PYTHON_KEYRING_BACKEND"] = NO_KEYRING_BACKEND
    env.pop("NO_PROXY", None)
    env.pop("no_proxy", None)
    home.mkdir(parents=True, exist_ok=True)
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / "config"),
            "XDG_DATA_HOME": str(home / "data"),
            "XDG_STATE_HOME": str(home / "state"),
            "XDG_CACHE_HOME": str(home / "cache"),
            "MAMMOTH_LOG_DIR": str(home / "run-log"),
            "MAMMOTH_NO_UPDATE_CHECK": "1",
            "MAMMOTH_UPDATE_CACHE": str(home / "update-check.json"),
            "MAMMOTH_PARENT_CACHE": str(home / "view-parents.json"),
            "COLUMNS": "200",
            "PYTHONPATH": os.pathsep.join([str(REPO_ROOT), str(CLI_ROOT)]),
            "PYTHONDONTWRITEBYTECODE": "1",
            "NO_COLOR": "1",
            "TERM": "dumb",
        }
    )
    return env


def make_home() -> Path:
    return Path(tempfile.mkdtemp(prefix="mammoth-fuzz-"))


def load_tree(env: dict[str, str]) -> list[Node]:
    done = subprocess.run(
        [sys.executable, str(HERE / "dump_tree.py")],
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT,
        env=env,
        check=True,
        cwd=env["HOME"],
    )
    nodes: list[Node] = []
    for row in json.loads(done.stdout):
        params = tuple(
            Param(p["name"], p["kind"], tuple(p["opts"]), p["is_flag"], p["required"], p["type"])
            for p in row["params"]
            if not p["hidden"]
        )
        nodes.append(Node(tuple(row["path"]), row["is_group"], params))
    return nodes


def global_names(nodes: Sequence[Node]) -> frozenset[str]:
    """Options declared by most leaves are the global ones (output, profile, ...)."""
    leaves = [n for n in nodes if not n.is_group]
    counts: dict[str, int] = {}
    for leaf in leaves:
        for p in leaf.params:
            counts[p.name] = counts.get(p.name, 0) + 1
    return frozenset(name for name, c in counts.items() if c * 2 > len(leaves))


# -------------------------------------------------------------------------- cases


@dataclass(frozen=True)
class Case:
    command: str
    label: str
    argv: tuple[str, ...]
    kind: str
    # Tokens a usage error must mention (any one of them).
    names: tuple[str, ...] = ()
    # The input is invalid and silently accepting it (exit 0) is a failure.
    must_reject: bool = False
    expect_help: bool = False

    @property
    def id(self) -> str:
        return f"{self.command}|{self.label}"


def _valid_value(p: Param) -> str:
    return {"int": "1", "float": "1.5"}.get(p.type, "x")


def fillers(node: Node, skip: str | None = None) -> list[str]:
    """Valid values for every required positional/option, so the fuzzed input is reached."""
    out: list[str] = []
    for p in node.params:
        if p.name == skip or not p.required:
            continue
        if p.kind == "argument":
            out.append(_valid_value(p))
        elif p.long and p.takes_value:
            out += [p.long, _valid_value(p)]
        elif p.long:
            out.append(p.long)
    return out


def _near_miss(flag: str, real: set[str]) -> str | None:
    candidate = flag[:-1]
    return candidate if len(candidate) > 3 and candidate not in real else None


def _value_case(node: Node, p: Param, index: int) -> Case | None:
    if not p.takes_value:
        return None
    pool: list[tuple[str, str]] = [("empty", ""), ("long", LONG_VALUE)]
    if p.type in {"int", "float"}:
        pool.append(("wrong-type", "not-a-number"))
    else:
        pool.append(("garbage", "\x07;$(id)`x`"))
    kind, value = pool[index % len(pool)]
    base = list(node.path) + fillers(node, skip=p.name)
    name = p.long or p.name
    if p.kind == "argument":
        argv = [*base, value]
        label = f"arg {p.name} {kind}"
    else:
        argv = [*base, name, value]
        label = f"{name} {kind}"
    if kind == "wrong-type":
        names = (name, value)
    else:
        names = () if p.kind == "argument" else (name,)
    return Case(node.command, label, tuple(argv), "value", names, kind == "wrong-type")


def cases_for(node: Node, globals_: frozenset[str]) -> list[Case]:
    cmd, path = node.command, list(node.path)
    cases = [
        Case(cmd, "no args", tuple(path), "noargs"),
        Case(cmd, "--help", (*path, "--help"), "help", expect_help=True),
        Case(cmd, "unknown flag", (*path, BOGUS_FLAG), "unknown", (BOGUS_FLAG,), True),
    ]
    if node.is_group:
        return cases
    longs = {p.long for p in node.params if p.long}
    near = [p for p in node.params if p.name not in globals_ and p.long]
    shared = [p for p in node.params if p.name in globals_ and p.long]
    if shared:
        near.append(shared[zlib.crc32(cmd.encode()) % len(shared)])
    filled = fillers(node)
    for p in near:
        flag = _near_miss(p.long or "", set(longs))
        if flag is not None:
            argv = [*path, *filled, flag] + (["1"] if p.takes_value else [])
            cases.append(Case(cmd, f"near-miss {flag}", tuple(argv), "near-miss", (flag,), True))
    if "--server-prefix" in longs:
        argv = [*path, *filled, "--server", "koyal"]
        cases.append(Case(cmd, "--server koyal", tuple(argv), "near-miss", ("--server",), True))
    for i, p in enumerate(node.params):
        if p.name not in globals_:
            case = _value_case(node, p, i)
            if case:
                cases.append(case)
    cases.append(
        Case(
            cmd,
            "global before",
            ("--output", "json", *path, *filled),
            "global-before",
            ("--output",),
        )
    )
    cases.append(Case(cmd, "global after", (*path, *filled, "--output", "json"), "global-after"))
    return cases


# ----------------------------------------------------------------------- results


@dataclass
class Result:
    code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def output(self) -> str:
        return self.stdout + "\n" + self.stderr

    @property
    def first_stderr_line(self) -> str:
        return first_line(self.stderr)


def first_line(text: str, skip: set[str] | None = None) -> str:
    for line in _ANSI.sub("", text).replace("\r", "\n").splitlines():
        if line.strip() and line.strip() not in (skip or set()):
            return line.strip()[:140]
    return ""


def _text(data: str | bytes | None) -> str:
    if isinstance(data, bytes):
        return data.decode(errors="replace")
    return data or ""


def run_cli(argv: Sequence[str], env: dict[str, str]) -> Result:
    try:
        done = subprocess.run(
            [sys.executable, "-m", "mammoth_cli", *argv],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=SUBPROCESS_TIMEOUT,
            env=env,
            stdin=subprocess.DEVNULL,
            cwd=env["HOME"],
        )
    except subprocess.TimeoutExpired as exc:
        return Result(None, _text(exc.stdout), _text(exc.stderr), timed_out=True)
    return Result(done.returncode, done.stdout, done.stderr)


class _Zygote:
    """One warm CLI process (see ``zygote.py``) serving one request at a time."""

    def __init__(self, env: dict[str, str]) -> None:
        self.env = env
        self.proc = self._start()

    def _start(self) -> subprocess.Popen[str]:
        return subprocess.Popen(
            [sys.executable, str(HERE / "zygote.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=self.env,
            cwd=self.env["HOME"],
            start_new_session=True,
        )

    def run(self, argv: Sequence[str]) -> Result:
        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(json.dumps({"argv": list(argv)}) + "\n")
        self.proc.stdin.flush()
        timer = threading.Timer(SUBPROCESS_TIMEOUT, self.kill)
        timer.start()
        try:
            line = self.proc.stdout.readline()
        finally:
            timer.cancel()
        if not line:
            self.kill()
            self.proc = self._start()
            return Result(None, "", "", timed_out=True)
        reply = json.loads(line)
        return Result(reply["code"], reply["stdout"], reply["stderr"])

    def kill(self) -> None:
        try:
            os.killpg(self.proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def close(self) -> None:
        self.kill()
        self.proc.wait()


class ZygotePool:
    """Warm CLI processes shared by the worker threads of a run."""

    def __init__(self, env: dict[str, str], size: int) -> None:
        self._idle: queue.Queue[_Zygote] = queue.Queue()
        self._all = [_Zygote(env) for _ in range(size)]
        for z in self._all:
            self._idle.put(z)

    def run(self, argv: Sequence[str]) -> Result:
        zygote = self._idle.get()
        try:
            return zygote.run(argv)
        finally:
            self._idle.put(zygote)

    def close(self) -> None:
        for z in self._all:
            z.close()


def judge_common(result: Result) -> list[str]:
    if result.timed_out:
        return [f"hang: no exit within {SUBPROCESS_TIMEOUT}s"]
    problems: list[str] = []
    if result.code not in EXIT_SET:
        problems.append(f"exit {result.code} is outside the documented set")
    if _TRACEBACK.search(result.output):
        problems.append("Python traceback")
    if _API_ERROR.search(result.output) and not _CONNECTION_HINT.search(result.output):
        problems.append("api_error / 'failed unexpectedly' for a usage mistake")
    return problems


def names_input(names: Sequence[str], output: str) -> bool:
    """Whether the error text mentions the bad token (a flag also counts as its words)."""
    text = _ANSI.sub("", output).lower()
    spaced = text.replace("-", " ").replace("_", " ")
    for name in names:
        token = name.lower()
        if token and (
            token in text or token.strip("-").replace("-", " ").replace("_", " ") in spaced
        ):
            return True
    return False


def judge(case: Case, result: Result) -> list[str]:
    """The pass rule for a one-shot case. Returns the problems (empty means pass)."""
    problems = judge_common(result)
    if result.timed_out:
        return problems
    if case.expect_help and result.code != 0:
        problems.append(f"--help exited {result.code}, expected 0")
    if case.must_reject and result.code == 0:
        problems.append("invalid input silently accepted (exit 0)")
    if case.names and result.code == 2 or (case.names and case.must_reject):
        if not names_input(case.names, result.output):
            wanted = " or ".join(repr(n[:30]) for n in case.names)
            problems.append(f"error does not name the bad input ({wanted})")
    return problems


# --------------------------------------------------------------------------- pty


@dataclass
class PtyRun:
    code: int | None
    transcript: str
    after: str
    waiting: bool

    @property
    def tail(self) -> str:
        lines = _ANSI.sub("", self.transcript).replace("\r", "\n").strip().splitlines()
        return lines[-1] if lines else ""


def _drain(child: pexpect.spawn, first_wait: float) -> tuple[str, bool]:
    """Read until EOF (exited) or until output goes idle with the process alive."""
    text, deadline = "", time.monotonic() + first_wait
    while True:
        try:
            chunk = child.read_nonblocking(65536, timeout=PTY_IDLE)
        except pexpect.TIMEOUT:
            if text or time.monotonic() > deadline:
                return text, False
            continue
        except pexpect.EOF:
            return text, True
        text += chunk


def _send(child: pexpect.spawn, key: str) -> None:
    if key == "EOF":
        child.sendeof()
    elif key == "INT":
        child.sendintr()
    else:
        child.send(key)


def run_pty(argv: Sequence[str], keys: Sequence[str], env: dict[str, str], finish: bool) -> PtyRun:
    """Run in a real pty, sending each key when the previous output settles.

    With ``finish`` a process that is still alive after the last key is fed EOF
    (a few times) so a re-prompting command ends; one that never ends is a hang.
    """
    child = pexpect.spawn(
        sys.executable,
        ["-m", "mammoth_cli", *argv],
        env=env,
        cwd=env["HOME"],
        encoding="utf-8",
        codec_errors="replace",
        dimensions=(40, 200),
    )
    try:
        transcript, exited = _drain(child, PTY_FIRST_OUTPUT)
        after = ""
        for key in keys:
            if exited:
                break
            _send(child, key)
            after, exited = _drain(child, PTY_IDLE)
            transcript += after
        feeds = 0
        while finish and not exited and feeds < PTY_EOF_FEEDS:
            feeds += 1
            _send(child, "EOF")
            chunk, exited = _drain(child, PTY_IDLE)
            transcript += chunk
        code = _exit_code(child) if exited else None
        return PtyRun(code, transcript, after, waiting=not exited)
    finally:
        if child.isalive():
            child.terminate(force=True)
        child.close()


def _exit_code(child: pexpect.spawn) -> int | None:
    child.close()
    if child.exitstatus is not None:
        return int(child.exitstatus)
    return 128 + int(child.signalstatus or 0)


def benign_answer(prompt_tail: str) -> str:
    lowered = prompt_tail.lower()
    if "choose" in lowered:
        return "3\n"
    if "y/n" in lowered:
        return "y\n"
    return "x\n"


PTY_ACTIONS: dict[str, str] = {
    "stdin EOF": "EOF",
    "invalid choice": "zzz\n",
    "Ctrl-C": "INT",
    "empty Enter": "\n",
}


@dataclass
class PtyRow:
    command: str
    label: str
    problems: list[str]
    first_line: str
    argv: tuple[str, ...]
    keys: tuple[str, ...]


def judge_pty(run: PtyRun) -> list[str]:
    problems = judge_common(Result(run.code, "", run.transcript, timed_out=run.waiting))
    if run.waiting:
        problems = ["hang: still alive after the input and repeated EOF"]
    return problems


def fuzz_prompts(node: Node, env: dict[str, str]) -> list[PtyRow] | None:
    """Find a command's prompts in a real pty, then attack each one.

    Returns None when the command never waits for input and ends cleanly.
    """
    base = (*node.path, *fillers(node))
    variants = [base]
    if any(p.long == "--server-prefix" for p in node.params):
        # A server with a registered OAuth client opens the "Choose:" menu.
        variants.append((*base, "--server-prefix", "koyal"))
    found: list[PtyRow] = []
    for argv in variants:
        found.extend(fuzz_prompts_with(node, argv, env) or [])
    return found or None


def fuzz_prompts_with(
    node: Node, argv: tuple[str, ...], env: dict[str, str]
) -> list[PtyRow] | None:
    prompts: list[str] = []
    keys: list[str] = []
    run = run_pty(argv, keys, env, finish=False)
    plain = run
    while run.waiting and len(prompts) < PTY_MAX_PROMPTS and run.tail:
        prompts.append(run.tail)
        keys.append(benign_answer(run.tail))
        run = run_pty(argv, keys, env, finish=False)
    if not prompts:
        problems = judge_pty(plain)
        row = PtyRow(
            node.command, "tty run, no prompt", problems, first_line(plain.transcript), argv, ()
        )
        return [row] if problems else None
    rows: list[PtyRow] = []
    for index, prompt in enumerate(prompts):
        for name, action in PTY_ACTIONS.items():
            sent = (*keys[:index], action)
            attempt = run_pty(argv, sent, env, finish=True)
            suffix = " [--server-prefix koyal]" if "koyal" in argv else ""
            label = f"{name} at prompt {index + 1} {prompt[:40].strip()!r}{suffix}"
            line = first_line(
                attempt.after or attempt.transcript, skip={"zzz", "^C", "^D", prompt.strip()}
            )
            rows.append(PtyRow(node.command, label, judge_pty(attempt), line, argv, sent))
    return rows
