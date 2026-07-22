"""Install, list, locate, update, and uninstall the bundled ``mammoth-cli`` skill.

The canonical skill ships as package data under
``mammoth_cli/bundled_skill/mammoth-cli``. It is copied (never symlinked) into
each agent's skills directory at user or project scope, following the reviewed
destination contract. Ownership is tracked by per-file SHA-256 in an install
state file under ``platformdirs.user_data_dir("mammoth-cli", "Mammoth")`` so an
update or uninstall only ever touches files the installer itself wrote; an
unowned or locally modified destination is refused unless ``force`` is set,
which first moves it to a timestamped backup.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import platformdirs

from mammoth_cli.errors.envelope import EXIT_CONFLICT, EXIT_USAGE, CliError

SKILL_NAME = "mammoth-cli"
STATE_FILENAME = "install-state-v1.json"
STATE_SCHEMA_VERSION = 1

AGENTS = ("codex", "claude", "cursor")
SCOPES = ("user", "project")
_AGENT_SUBDIR = {
    "codex": ".agents/skills",
    "claude": ".claude/skills",
    "cursor": ".cursor/skills",
}


@dataclass(frozen=True)
class _Target:
    agent: str
    scope: str
    path: Path


def canonical_skill_dir() -> Path:
    """Return the packaged canonical skill directory (works offline)."""
    return Path(__file__).resolve().parent.parent / "bundled_skill" / SKILL_NAME


def _state_path() -> Path:
    return Path(platformdirs.user_data_dir("mammoth-cli", "Mammoth")) / STATE_FILENAME


def _load_state() -> dict[str, dict[str, str]]:
    path = _state_path()
    if not path.exists():
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    installs = document.get("installs", {})
    return installs if isinstance(installs, dict) else {}


def _save_state(installs: dict[str, dict[str, str]]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {"schema_version": STATE_SCHEMA_VERSION, "installs": installs}
    path.write_text(json.dumps(document, indent=1, sort_keys=True), encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_tree(root: Path) -> dict[str, str]:
    """Map each file's root-relative POSIX path to its SHA-256 digest."""
    digests: dict[str, str] = {}
    for item in sorted(root.rglob("*")):
        if item.is_file():
            digests[item.relative_to(root).as_posix()] = _sha256(item)
    return digests


def _project_root(cwd: Path) -> Path:
    for directory in (cwd, *cwd.parents):
        if (directory / ".git").exists():
            return directory
    return cwd


def _resolve_agents(agents: list[str] | None) -> list[str]:
    if not agents or "all" in agents:
        return list(AGENTS)
    unknown = [a for a in agents if a not in AGENTS]
    if unknown:
        raise CliError(
            code="unknown_agent",
            message=f"Unknown agent(s): {', '.join(unknown)}.",
            exit_status=EXIT_USAGE,
            hint=f"Choose from: {', '.join(AGENTS)}, or 'all'.",
        )
    return agents


def _targets(agents: list[str], scope: str, home: Path, cwd: Path) -> list[_Target]:
    if scope not in SCOPES:
        raise CliError(
            code="unknown_scope",
            message=f"Unknown scope '{scope}'.",
            exit_status=EXIT_USAGE,
            hint=f"Choose from: {', '.join(SCOPES)}.",
        )
    base = home if scope == "user" else _project_root(cwd)
    return [
        _Target(agent, scope, base / _AGENT_SUBDIR[agent] / SKILL_NAME) for agent in agents
    ]


def _key(target: _Target) -> str:
    return f"{target.agent}:{target.scope}:{target.path}"


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def _timestamped_backup(path: Path, stamp: str) -> Path:
    backup = path.with_name(f"{path.name}.backup-{stamp}")
    shutil.move(str(path), str(backup))
    return backup


def install(
    agents: list[str] | None = None,
    scope: str = "user",
    *,
    force: bool = False,
    home: Path | None = None,
    cwd: Path | None = None,
    timestamp: str = "backup",
) -> dict[str, object]:
    """Install the canonical skill into each requested agent/scope destination.

    Args:
        agents: Agent names (``codex``/``claude``/``cursor``) or ``["all"]``.
        scope: ``"user"`` (home) or ``"project"`` (git root, else cwd).
        force: Move an unowned or modified destination to a timestamped backup
            instead of failing.
        home: Home directory override (for tests).
        cwd: Working directory override for project scope (for tests).
        timestamp: Backup suffix; pass a caller-supplied stamp (no clock here).

    Returns:
        A summary mapping with a ``results`` list, one entry per destination.

    Raises:
        CliError: ``skill_conflict`` when a destination is unowned or locally
            modified and ``force`` is not set.
    """
    home = home or Path.home()
    cwd = cwd or Path.cwd()
    canonical = canonical_skill_dir()
    canonical_hashes = _hash_tree(canonical)
    state = _load_state()
    results: list[dict[str, object]] = []

    for target in _targets(_resolve_agents(agents), scope, home, cwd):
        key = _key(target)
        record = state.get(key)
        backup: str | None = None
        if target.path.exists():
            current = _hash_tree(target.path)
            if current == canonical_hashes:
                results.append({"target": str(target.path), "status": "identical"})
                state[key] = {"skill": SKILL_NAME, **canonical_hashes}
                continue
            owned = record is not None and {
                k: v for k, v in record.items() if k != "skill"
            } == current
            if not owned:
                if not force:
                    raise CliError(
                        code="skill_conflict",
                        message=f"'{target.path}' is not owned by the installer.",
                        exit_status=EXIT_CONFLICT,
                        hint="Re-run with force to back up and replace it.",
                        details={"path": str(target.path)},
                    )
                backup = str(_timestamped_backup(target.path, timestamp))
        _copy_tree(canonical, target.path)
        state[key] = {"skill": SKILL_NAME, **canonical_hashes}
        results.append(
            {
                "target": str(target.path),
                "status": "updated" if record is not None else "installed",
                "backup": backup,
            }
        )

    _save_state(state)
    return {"skill": SKILL_NAME, "results": results}


def list_() -> dict[str, object]:
    """List installed skill destinations and whether each is present and intact.

    Returns:
        A mapping with an ``installs`` list from the ownership state.
    """
    state = _load_state()
    installs: list[dict[str, object]] = []
    for key, record in sorted(state.items()):
        agent, scope, path_str = key.split(":", 2)
        path = Path(path_str)
        owned_hashes = {k: v for k, v in record.items() if k != "skill"}
        present = path.exists()
        intact = present and _hash_tree(path) == owned_hashes
        installs.append(
            {"agent": agent, "scope": scope, "path": path_str, "present": present, "intact": intact}
        )
    return {"skill": SKILL_NAME, "installs": installs}


def path(
    agents: list[str] | None = None,
    scope: str = "user",
    home: Path | None = None,
    cwd: Path | None = None,
) -> dict[str, object]:
    """Return the canonical source path and computed destination paths.

    Args:
        agents: Agent names or ``["all"]``.
        scope: ``"user"`` or ``"project"``.
        home: Home directory override (for tests).
        cwd: Working directory override (for tests).

    Returns:
        A mapping with ``canonical`` and a ``targets`` list.
    """
    home = home or Path.home()
    cwd = cwd or Path.cwd()
    targets = _targets(_resolve_agents(agents), scope, home, cwd)
    return {
        "skill": SKILL_NAME,
        "canonical": str(canonical_skill_dir()),
        "targets": [
            {"agent": t.agent, "scope": t.scope, "path": str(t.path)} for t in targets
        ],
    }


def uninstall(
    agents: list[str] | None = None,
    scope: str = "user",
    *,
    home: Path | None = None,
    cwd: Path | None = None,
) -> dict[str, object]:
    """Remove installer-owned skill destinations only.

    A destination whose current hashes do not match the ownership record is
    reported as ``modified`` and left in place.

    Args:
        agents: Agent names or ``["all"]``.
        scope: ``"user"`` or ``"project"``.
        home: Home directory override (for tests).
        cwd: Working directory override (for tests).

    Returns:
        A mapping with a ``results`` list, one entry per destination.
    """
    home = home or Path.home()
    cwd = cwd or Path.cwd()
    state = _load_state()
    results: list[dict[str, object]] = []
    for target in _targets(_resolve_agents(agents), scope, home, cwd):
        key = _key(target)
        record = state.get(key)
        if record is None or not target.path.exists():
            results.append({"target": str(target.path), "status": "absent"})
            state.pop(key, None)
            continue
        owned = {k: v for k, v in record.items() if k != "skill"} == _hash_tree(target.path)
        if not owned:
            results.append({"target": str(target.path), "status": "modified"})
            continue
        shutil.rmtree(target.path)
        state.pop(key, None)
        results.append({"target": str(target.path), "status": "removed"})
    _save_state(state)
    return {"skill": SKILL_NAME, "results": results}


def update(
    agents: list[str] | None = None,
    scope: str = "user",
    *,
    force: bool = False,
    home: Path | None = None,
    cwd: Path | None = None,
    timestamp: str = "backup",
) -> dict[str, object]:
    """Re-install the canonical skill into each destination (same ownership rules).

    Args:
        agents: Agent names or ``["all"]``.
        scope: ``"user"`` or ``"project"``.
        force: Back up and replace an unowned or modified destination.
        home: Home directory override (for tests).
        cwd: Working directory override (for tests).
        timestamp: Backup suffix.

    Returns:
        The same summary shape as :func:`install`.
    """
    return install(
        agents, scope, force=force, home=home, cwd=cwd, timestamp=timestamp
    )
