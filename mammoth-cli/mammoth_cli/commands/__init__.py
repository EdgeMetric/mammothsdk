"""commands layer for the Mammoth CLI.

Assembles :data:`BESPOKE`: fully-typed Typer command callbacks that override
the generic manifest leaf for the command ids they implement. ``app.py``
imports this module and swaps in a bespoke callback wherever one exists,
registering it at the exact same manifest path and name as the generic leaf
it replaces.
"""

from __future__ import annotations

from collections.abc import Callable

from mammoth_cli.commands._lazy import LazyTable

_TARGETS: dict[str, str] = {
    "auth.login": "mammoth_cli.commands.auth:auth_login",
    "auth.status": "mammoth_cli.commands.auth:auth_status",
    "auth.logout": "mammoth_cli.commands.auth:auth_logout",
    "config.get": "mammoth_cli.commands.config:config_get",
    "config.set": "mammoth_cli.commands.config:config_set",
    "config.list": "mammoth_cli.commands.config:config_list",
    "config.path": "mammoth_cli.commands.config:config_path",
    "context.project.status": "mammoth_cli.commands.context:context_project_status",
    "context.project.use": "mammoth_cli.commands.context:context_project_use",
    "context.project.clear": "mammoth_cli.commands.context:context_project_clear",
    "upgrade": "mammoth_cli.commands.upgrade:upgrade_command",
}

#: Command id -> bespoke Typer callback, imported from its module on first use.
BESPOKE: LazyTable[Callable[..., None]] = LazyTable(_TARGETS)
