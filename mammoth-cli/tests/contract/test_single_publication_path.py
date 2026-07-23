"""Contract guard: exactly one publication path per distribution.

This monorepo ships THREE PyPI distributions — ``mammoth-io`` (repo root),
``mammoth-cli`` (``mammoth-cli/``), and ``mammoth-mcp`` (``mammoth-mcp/``). The
release design is that each is published by EXACTLY ONE tag-triggered workflow
and by no other path:

* ``mammoth-io``  -> ``sdk-release.yml`` (tag ``sdk-v*``)
* ``mammoth-cli`` -> ``cli-release.yml`` (tag ``cli-v*``; also cuts a GitHub Release)
* ``mammoth-mcp`` -> ``publish.yml``     (tag ``mcp-v*``)

The historical hazard: ``publish.yml`` triggered on ``release: published`` and
published both ``mammoth-io`` and ``mammoth-mcp``. Because ``cli-release.yml``
creates a GitHub Release, that gave ``mammoth-io`` a SECOND publication path and
re-published MCP on every CLI release. This guard makes the invariant explicit
and enforceable:

(a) each of the three distributions is published by exactly one workflow;
(b) no workflow that publishes is triggered by a ``release:`` event (only tag
    pushes); and
(c) the distribution each publishing workflow ships is inferred from its build
    working-directory (repo root -> mammoth-io, ``mammoth-cli`` -> mammoth-cli,
    ``mammoth-mcp`` -> mammoth-mcp).
"""

from __future__ import annotations

from pathlib import Path

import yaml

# Mirror test_ci_runs_all_suites.py: this file lives at
# mammoth-cli/tests/contract/, so parents[2] is the CLI root and its parent is
# the repository root that holds .github/workflows.
_CLI_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _CLI_ROOT.parent
_WORKFLOWS_DIR = _REPO_ROOT / ".github" / "workflows"

_PUBLISH_ACTION = "pypa/gh-action-pypi-publish"

# The build working-directory that identifies each distribution. A missing or
# "." working-directory means the repo root, which builds mammoth-io.
_WORKDIR_TO_DIST = {
    None: "mammoth-io",
    ".": "mammoth-io",
    "mammoth-cli": "mammoth-cli",
    "mammoth-mcp": "mammoth-mcp",
}

_ALL_DISTRIBUTIONS = {"mammoth-io", "mammoth-cli", "mammoth-mcp"}


def _workflow_docs() -> dict[str, dict]:
    """Every parsed workflow YAML, keyed by file name."""
    docs: dict[str, dict] = {}
    for path in sorted(_WORKFLOWS_DIR.glob("*.yml")):
        docs[path.name] = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert docs, f"no workflow YAML found under {_WORKFLOWS_DIR}"
    return docs


def _steps(job: dict) -> list[dict]:
    steps = job.get("steps", []) if isinstance(job, dict) else []
    return [step for step in steps if isinstance(step, dict)]


def _job_publishes(job: dict) -> bool:
    return any(str(step.get("uses", "")).startswith(_PUBLISH_ACTION) for step in _steps(job))


def _workflow_publishes(doc: dict) -> bool:
    jobs = doc.get("jobs", {}) if isinstance(doc, dict) else {}
    return any(_job_publishes(job) for job in jobs.values())


def _trigger_section(doc: dict):
    """Return the ``on:`` mapping, tolerating PyYAML coercing ``on`` to ``True``."""
    if "on" in doc:
        return doc["on"]
    # PyYAML parses the bare key ``on`` as the boolean True.
    return doc.get(True)


def _triggers_on_release(doc: dict) -> bool:
    section = _trigger_section(doc)
    if section is None:
        return False
    if isinstance(section, str):
        return section == "release"
    if isinstance(section, list):
        return "release" in section
    if isinstance(section, dict):
        return "release" in section
    return False


def _build_working_directory(doc: dict) -> str | None:
    """Effective build working-directory: build-job default, else top-level default."""
    jobs = doc.get("jobs", {})
    build_job = jobs.get("build", {}) if isinstance(jobs, dict) else {}
    job_wd = build_job.get("defaults", {}).get("run", {}).get("working-directory")
    if job_wd is not None:
        return job_wd
    return doc.get("defaults", {}).get("run", {}).get("working-directory")


def _published_distribution(doc: dict) -> str:
    working_dir = _build_working_directory(doc)
    assert working_dir in _WORKDIR_TO_DIST, (
        f"unrecognized build working-directory {working_dir!r}; cannot map it to one "
        f"of {sorted(_ALL_DISTRIBUTIONS)}. Update _WORKDIR_TO_DIST if a new "
        f"distribution was added."
    )
    return _WORKDIR_TO_DIST[working_dir]


def _publishing_workflows() -> dict[str, dict]:
    return {name: doc for name, doc in _workflow_docs().items() if _workflow_publishes(doc)}


def test_at_least_the_three_expected_workflows_publish() -> None:
    """Sanity: publishing workflows exist and cover the three distributions."""
    publishers = _publishing_workflows()
    assert publishers, "no workflow publishes to PyPI; expected three"
    dists = {_published_distribution(doc) for doc in publishers.values()}
    assert dists == _ALL_DISTRIBUTIONS, (
        f"publishing workflows ship {sorted(dists)}, expected {sorted(_ALL_DISTRIBUTIONS)}"
    )


def test_each_distribution_has_exactly_one_publisher() -> None:
    """(a) Every distribution is published by EXACTLY ONE workflow."""
    publishers = _publishing_workflows()
    by_dist: dict[str, list[str]] = {dist: [] for dist in _ALL_DISTRIBUTIONS}
    for name, doc in publishers.items():
        by_dist[_published_distribution(doc)].append(name)

    for dist in _ALL_DISTRIBUTIONS:
        workflows = sorted(by_dist[dist])
        assert len(workflows) == 1, (
            f"{dist} must be published by exactly one workflow, but is published by "
            f"{workflows or 'none'}. Each distribution needs a single, dedicated "
            f"tag-triggered publication path (mammoth-io=sdk-release.yml, "
            f"mammoth-cli=cli-release.yml, mammoth-mcp=publish.yml)."
        )


def test_no_publisher_is_triggered_by_a_release_event() -> None:
    """(b) No PUBLISHING workflow may be triggered by a ``release:`` event.

    ``cli-release.yml`` creates a GitHub Release; a publisher listening on
    ``release: published`` would fire on it, giving some distribution a second,
    unintended publication path. Publishers must trigger only on tag pushes.
    """
    offenders = {
        name for name, doc in _publishing_workflows().items() if _triggers_on_release(doc)
    }
    assert not offenders, (
        f"publishing workflows must not trigger on a 'release:' event: {sorted(offenders)}. "
        f"Trigger on a tag push (e.g. `on: push: tags: [...]`) instead, so a GitHub "
        f"Release created by cli-release.yml cannot fan out to a second publisher."
    )


def test_publishers_trigger_only_on_tag_pushes() -> None:
    """Publishers trigger on tag pushes, not branch pushes or pull requests."""
    for name, doc in _publishing_workflows().items():
        section = _trigger_section(doc)
        assert isinstance(section, dict), f"{name}: unexpected `on:` shape {section!r}"
        assert "push" in section, f"{name}: publisher must trigger on a push"
        push = section["push"]
        assert isinstance(push, dict) and "tags" in push, (
            f"{name}: publisher must trigger on tag pushes (`push: tags: [...]`), got {push!r}"
        )
        assert "branches" not in push, (
            f"{name}: publisher must not trigger on branch pushes, got {push!r}"
        )
        assert "pull_request" not in section, (
            f"{name}: publisher must not trigger on pull_request"
        )
