"""Contract guard: CI, release, and ``make check`` must run the WHOLE suite.

The strongest runtime suites — ``tests/realcode`` (real argv -> handler -> SDK
path) and ``tests/subprocess`` (executable behavior) — are exactly the ones a
subset-selecting invocation silently drops. A gate that runs, say,
``pytest tests/unit tests/contract tests/installer`` looks green while never
executing those suites.

This guard discovers the immediate, non-``live`` subdirectories of ``tests/``
that actually contain tests, and asserts that each authoritative gate (PR CI,
the release build gate, and the Makefile ``test`` target) invokes pytest over
the whole ``tests`` tree with ``live`` deselected as the *only* filter — i.e.
``pytest tests -m "not live" ...`` — rather than naming a subset of directories
or ignoring one. Adding a new suite directory therefore cannot be forgotten by
a gate.
"""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest
import yaml

_CLI_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _CLI_ROOT.parent
_TESTS_DIR = _CLI_ROOT / "tests"

_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "cli-ci.yml"
_RELEASE_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "cli-release.yml"
_MAKEFILE = _CLI_ROOT / "Makefile"

# The directory that is legitimately excluded from the default suite. It is
# deselected by marker, never by omitting it from the pytest target.
_LIVE_DIR = "live"


def _discovered_suites() -> set[str]:
    """Immediate subdirectories of tests/ that hold tests and are not ``live``."""
    suites: set[str] = set()
    for child in _TESTS_DIR.iterdir():
        if not child.is_dir() or child.name == _LIVE_DIR or child.name == "__pycache__":
            continue
        if any(child.rglob("test_*.py")):
            suites.add(child.name)
    return suites


def _pytest_commands(text: str) -> list[list[str]]:
    """Extract each pytest command in a shell/recipe blob as a token list.

    Every logical line containing ``pytest`` is parsed from the ``pytest`` token
    onward. This tolerates leaders such as ``poetry run``, ``$(PY) -m`` and
    ``python -m`` because we start tokenizing at ``pytest`` itself.
    """
    commands: list[list[str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if "pytest" not in line:
            continue
        idx = line.index("pytest")
        try:
            tokens = shlex.split(line[idx:])
        except ValueError:
            # Unbalanced quoting (e.g. a GitHub ``${{ }}`` fragment): fall back
            # to a whitespace split so the target tokens are still visible.
            tokens = line[idx:].split()
        commands.append(tokens)
    return commands


def _positional_targets(tokens: list[str]) -> list[str]:
    """pytest positional arguments (path-like), skipping flags and their values."""
    targets: list[str] = []
    skip_next = False
    flags_with_values = {"-m", "-p", "-k", "-o", "--ignore", "--ignore-glob", "--deselect"}
    for tok in tokens[1:]:  # drop the leading ``pytest``
        if skip_next:
            skip_next = False
            continue
        if tok in flags_with_values:
            skip_next = True
            continue
        if tok.startswith("-"):
            continue
        targets.append(tok)
    return targets


def _ci_test_job_run_blobs() -> str:
    """Concatenated run scripts of the cli-ci ``test`` job only.

    Scoped to the ``test`` job so the platform-specific installer jobs (which
    legitimately run only ``tests/installer``) do not count as the main gate.
    """
    doc = yaml.safe_load(_CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["test"]["steps"]
    return "\n".join(step.get("run", "") for step in steps if isinstance(step, dict))


def _release_gate_run_blobs() -> str:
    """Concatenated run scripts of the cli-release ``build`` job."""
    doc = yaml.safe_load(_RELEASE_WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["build"]["steps"]
    return "\n".join(step.get("run", "") for step in steps if isinstance(step, dict))


def _makefile_test_recipe() -> str:
    """The recipe lines of the Makefile ``test`` target."""
    lines = _MAKEFILE.read_text(encoding="utf-8").splitlines()
    recipe: list[str] = []
    in_target = False
    for line in lines:
        if line.startswith("test:"):
            in_target = True
            continue
        if in_target:
            # Recipe lines are tab-indented; the target ends at the first
            # non-indented, non-blank line.
            if line.startswith("\t"):
                recipe.append(line.strip())
            elif line.strip() == "":
                continue
            else:
                break
    return "\n".join(recipe)


_SITES = {
    "cli-ci.yml (test job)": _ci_test_job_run_blobs,
    "cli-release.yml (build gate)": _release_gate_run_blobs,
    "Makefile (test target)": _makefile_test_recipe,
}


def test_suites_discovered() -> None:
    """Sanity: the strongest runtime suites exist and are discovered."""
    suites = _discovered_suites()
    assert {"realcode", "subprocess"} <= suites, (
        f"expected realcode+subprocess suites under tests/, discovered {sorted(suites)}"
    )


@pytest.mark.parametrize("site_name", list(_SITES))
def test_gate_runs_whole_tests_tree(site_name: str) -> None:
    suites = _discovered_suites()
    blob = _SITES[site_name]()
    commands = _pytest_commands(blob)
    assert commands, f"{site_name}: no pytest invocation found"

    all_targets: list[str] = []
    ignored: list[str] = []
    for tokens in commands:
        all_targets.extend(_positional_targets(tokens))
        # An explicit ignore of a suite directory also defeats the whole-tree run.
        for i, tok in enumerate(tokens):
            if tok in {"--ignore", "--ignore-glob"} and i + 1 < len(tokens):
                ignored.append(tokens[i + 1])
            elif tok.startswith("--ignore=") or tok.startswith("--ignore-glob="):
                ignored.append(tok.split("=", 1)[1])

    # 1) The whole tree must be a target of some invocation.
    assert "tests" in all_targets, (
        f"{site_name}: no pytest invocation targets the whole 'tests' tree; "
        f"targets were {all_targets}. Use `pytest tests -m \"not live\" -q "
        f"-p no:cacheprovider` so suites {sorted(suites)} are all collected."
    )

    # 2) No invocation may name a subset directory as a positional target: that
    #    is exactly how realcode/subprocess get silently dropped.
    subset_targets = [
        t for t in all_targets if t != "tests" and t.replace("\\", "/").startswith("tests/")
    ]
    assert not subset_targets, (
        f"{site_name}: names a subset of test directories {subset_targets} instead "
        f"of running the whole 'tests' tree; suites {sorted(suites)} can be omitted. "
        f"Use `pytest tests -m \"not live\" -q -p no:cacheprovider`."
    )

    # 3) No suite directory may be excluded via --ignore.
    ignored_suites = [
        p for p in ignored if any(s in p for s in suites)
    ]
    assert not ignored_suites, (
        f"{site_name}: excludes suite directories via --ignore {ignored_suites}."
    )
