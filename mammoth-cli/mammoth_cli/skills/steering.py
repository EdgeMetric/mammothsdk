"""Steering text for agent instruction files, and the bundled-skill reader.

``mammoth skill agents-md install`` writes one ``<mammoth-cli>…</mammoth-cli>``
block into a repository's ``AGENTS.md`` (or ``CLAUDE.md``); re-running replaces
the block in place, so upgrading the CLI and reinstalling refreshes stale
instructions without duplicating them. ``mammoth skill show`` prints the
bundled ``SKILL.md`` (or one of its reference files) so a cold-start agent
loads the guide with one command instead of resolving a path and reading it.
"""

from __future__ import annotations

import re
from pathlib import Path

from mammoth_cli import __version__
from mammoth_cli.skills.installer import SKILL_NAME, canonical_skill_dir

BLOCK_OPEN = "<mammoth-cli>"
BLOCK_CLOSE = "</mammoth-cli>"
DEFAULT_STEERING_PATH = "AGENTS.md"

#: The steering block, without the tags. Kept short on purpose: it points the
#: agent at ``mammoth skill show``, which holds the actual guide.
STEERING_BODY = """## Mammoth Analytics

Use the `mammoth` CLI for all Mammoth work; do not call the REST API or the
Python SDK directly, and do not drive the web app in a browser: every web
Transform-menu task is a `mammoth view transform` command (`mammoth view
transform --help`). Before the first Mammoth command in a session run
`mammoth doctor` (it must pass), then `mammoth skill show` and follow that
guide. If `mammoth` is missing, install it with `pip install mammoth-cli`
(or `uv tool install mammoth-cli`). If `mammoth auth status` shows no
credentials, tell the operator the exact `mammoth auth login` command to run
in their own terminal and wait; never ask for, read, or pass a key or secret.
Piped output is compact JSON. Take ids only from reads; run `mammoth schema get
COMMAND_ID` before a command you have not used; destructive commands need
`--yes --confirm ID`, and only for ids this task created.
"""

_BLOCK_RE = re.compile(re.escape(BLOCK_OPEN) + r".*?" + re.escape(BLOCK_CLOSE) + r"\n?", re.DOTALL)


def steering_block() -> str:
    """The full block, tags included, as written into the instructions file."""
    stamp = (
        f"<!-- written by mammoth-cli {__version__}; "
        "rerun `mammoth skill agents-md install` to refresh -->"
    )
    return f"{BLOCK_OPEN}\n{stamp}\n{STEERING_BODY}{BLOCK_CLOSE}\n"


def install_steering(path: str | None = None, cwd: Path | None = None) -> dict[str, object]:
    """Create or refresh the steering block in ``path`` (default ``AGENTS.md``).

    Returns:
        ``{"path", "action", "skill_version"}`` where ``action`` is
        ``created`` (file did not exist), ``replaced`` (an earlier block was
        updated in place), ``appended`` (file existed without a block) or
        ``unchanged`` (the block was already current).
    """
    base = cwd or Path.cwd()
    target = Path(path or DEFAULT_STEERING_PATH)
    if not target.is_absolute():
        target = base / target
    block = steering_block()
    if target.exists():
        current = target.read_text(encoding="utf-8")
        if _BLOCK_RE.search(current):
            updated = _BLOCK_RE.sub(lambda _m: block, current, count=1)
            action = "unchanged" if updated == current else "replaced"
        else:
            separator = "" if current.endswith("\n") or not current else "\n"
            updated = f"{current}{separator}\n{block}" if current else block
            action = "appended"
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        updated = block
        action = "created"
    if action != "unchanged":
        target.write_text(updated, encoding="utf-8")
    return {"path": str(target), "action": action, "skill_version": __version__}


def show(file: str | None = None) -> dict[str, object]:
    """Return the text of ``SKILL.md`` or of one bundled reference file.

    Args:
        file: A path relative to the skill directory, such as
            ``references/recipes/transforms.md``. Defaults to ``SKILL.md``.

    Raises:
        FileNotFoundError: when ``file`` is not a bundled skill file (paths
            outside the skill directory are refused the same way).
    """
    root = canonical_skill_dir().resolve()
    relative = file or "SKILL.md"
    candidate = (root / relative).resolve()
    if root not in candidate.parents and candidate != root:
        raise FileNotFoundError(relative)
    if not candidate.is_file():
        raise FileNotFoundError(relative)
    return {
        "skill": SKILL_NAME,
        "file": relative,
        "path": str(candidate),
        "text": candidate.read_text(encoding="utf-8"),
    }
