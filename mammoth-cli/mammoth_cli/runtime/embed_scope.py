"""What an embedded call can run, and so what its discovery commands may show.

A host that embeds the CLI (:mod:`mammoth_cli.embed`) has no profile, run log, shell
or user files. Dispatch refuses the commands that need one, and ``schema list``,
``schema find``, ``capability find``, ``recipe list`` and ``how`` hide them, so an
agent is never offered a command that can only fail.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.runtime import embedded
from mammoth_cli.runtime.local_paths import local_path_commands

# Commands that act on the host machine (login, config, installs, upgrade); an
# embedded call has no profile, keyring or shell to act on.
EMBEDDED_UNAVAILABLE = frozenset(
    {
        "auth.login",
        "auth.logout",
        "config.set",
        "upgrade",
        "skill.install",
        "skill.uninstall",
        "skill.update",
        "skill.agents-md.install",
        "completion.install",
        # Reads a JSON Lines file or the host's stdin.
        "run",
        # Read or write the host's profile, run log or install state.
        "auth.status",
        "config.get",
        "config.list",
        "config.path",
        "log.path",
        "log.tail",
        "history.list",
        "history.show",
        "history.undo",
        "history.resume",
        "skill.list",
        "skill.path",
        # Write a path on the host's filesystem. The commands that read one are not
        # listed: ``local_path_commands`` derives them from the manifest.
        "view.explore-panel.export-image",
        "support.template.export",
        "support.template.export-dashboard",
    }
)


def refused_embedded(command_id: str) -> bool:
    """Whether this context is an embedded call that cannot run ``command_id``.

    Args:
        command_id: A dotted command id.

    Returns:
        True for a host-machine command or one that reads a local path, inside an
        embedded call; always False on a normal CLI run.
    """
    return embedded.active() and (
        command_id in EMBEDDED_UNAVAILABLE or command_id in local_path_commands()
    )


def hidden_embedded(command_id: str | None, server_status: Any = None) -> bool:
    """Whether discovery must leave a command out of this embedded call.

    Args:
        command_id: The command's dotted id, or None when the entry has none.
        server_status: Its manifest ``server_status``.

    Returns:
        True when the call refuses the command, or opted out of pending ones and
        the command is pending a server release.
    """
    if embedded.hides_pending() and server_status == "pending":
        return True
    return bool(command_id) and refused_embedded(str(command_id))


def recipe_hidden_embedded(recipe: dict[str, Any]) -> bool:
    """Whether a recipe uses a command this embedded call refuses.

    Args:
        recipe: A recipe from ``recipes.json``.

    Returns:
        True when a command the call cannot run is one of its ``run`` lines or, for a
        recipe with no ``run`` lines, one of its ``steps``. A runnable recipe's steps
        may show how to get its inputs (``file upload``) without running it.
    """
    if recipe.get("run"):
        commands = [line["cmd"].replace(" ", ".") for line in recipe["run"]]
    else:
        commands = [
            step["command_id"] for step in recipe.get("steps", []) if step.get("command_id")
        ]
    return any(refused_embedded(command_id) for command_id in commands)
