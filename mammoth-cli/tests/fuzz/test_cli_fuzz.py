"""Input fuzz of every ``mammoth`` command, the way users type them.

Run (about 20 minutes on 8 cores; the suite is excluded from the default run)::

    pytest -m fuzz tests/fuzz

Every command and subcommand comes from the real Typer app tree. A failing case
that matches ``known_bugs`` is XFAIL naming the bug; any other failure is red.
``MAMMOTH_FUZZ_REPORT`` sets where the markdown report goes, and
``MAMMOTH_FUZZ_WORKERS`` the parallelism.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import pytest

from tests.fuzz import harness, known_bugs, report

pytestmark = pytest.mark.fuzz

WORKERS = int(os.environ.get("MAMMOTH_FUZZ_WORKERS", min(8, os.cpu_count() or 2)))


@lru_cache(maxsize=1)
def _env() -> dict[str, str]:
    return harness.child_env(harness.make_home())


@lru_cache(maxsize=1)
def _tree() -> list[harness.Node]:
    return harness.load_tree(_env())


def _cases() -> list[harness.Case]:
    globals_ = harness.global_names(_tree())
    return [c for node in _tree() for c in harness.cases_for(node, globals_)]


def _leaves() -> list[harness.Node]:
    return [n for n in _tree() if not n.is_group]


CASES = _cases()
LEAVES = _leaves()
_DONE: dict[object, object] = {}


@pytest.fixture(scope="session", autouse=True)
def _prefetch(request: pytest.FixtureRequest) -> None:
    """Run every selected case in a thread pool up front; tests only judge."""
    jobs: list[tuple[object, object]] = []
    for item in request.session.items:
        callspec = getattr(item, "callspec", None)
        if callspec is None:
            continue
        if "case" in callspec.params:
            jobs.append((callspec.params["case"], "case"))
        elif "node" in callspec.params:
            jobs.append((callspec.params["node"], "node"))
    env = _env()

    def run(job: tuple[object, object], zygotes: harness.ZygotePool | None) -> None:
        subject, kind = job
        if kind == "case":
            assert isinstance(subject, harness.Case)
            _DONE[subject] = (
                zygotes.run(subject.argv) if zygotes else harness.run_cli(subject.argv, env)
            )
        else:
            assert isinstance(subject, harness.Node)
            _DONE[subject] = harness.fuzz_prompts(subject, env)

    cold = bool(os.environ.get("MAMMOTH_FUZZ_COLD"))
    zygotes = None if cold else harness.ZygotePool(env, WORKERS)
    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            list(pool.map(lambda job: run(job, zygotes), jobs))
    finally:
        if zygotes:
            zygotes.close()


def _settle(command: str, label: str, problems: list[str], line: str) -> str | None:
    """Record the row; return the failure text, or xfail when the bug is known."""
    if not problems:
        report.record(report.Row(command, label, "PASS", line))
        return None
    bug = known_bugs.match(command, label, problems)
    if bug is not None:
        report.record(report.Row(command, label, f"XFAIL {bug.key}: {'; '.join(problems)}", line))
        pytest.xfail(f"{bug.key}: {bug.summary}")
    report.record(report.Row(command, label, f"FAIL: {'; '.join(problems)}", line))
    return f"{command} [{label}]: {'; '.join(problems)}"


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_command_input(case: harness.Case) -> None:
    result = _DONE[case]
    assert isinstance(result, harness.Result)
    failure = _settle(
        case.command, case.label, harness.judge(case, result), result.first_stderr_line
    )
    assert failure is None, f"{failure}\nargv: {[a[:40] for a in case.argv]}"


@pytest.mark.parametrize("node", LEAVES, ids=[n.command for n in LEAVES])
def test_prompts_in_a_real_pty(node: harness.Node) -> None:
    rows = _DONE[node]
    if rows is None:
        report.record(report.Row(node.command, "pty prompts", "SKIP no prompt", ""))
        pytest.skip("command never waits for input")
    assert isinstance(rows, list)
    failures: list[str] = []
    xfail: str | None = None
    for row in rows:
        try:
            failure = _settle(row.command, f"pty {row.label}", row.problems, row.first_line)
        except pytest.xfail.Exception as exc:
            xfail = str(exc)
            continue
        if failure:
            failures.append(failure)
    assert not failures, "\n".join(failures)
    if xfail:
        pytest.xfail(xfail)
