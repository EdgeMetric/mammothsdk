"""commands layer for the Mammoth CLI.

Assembles :data:`BESPOKE`: fully-typed Typer command callbacks that override
the generic manifest leaf for the command ids they implement. ``app.py``
imports this module and swaps in a bespoke callback wherever one exists,
registering it at the exact same manifest path and name as the generic leaf
it replaces.
"""

from __future__ import annotations

from collections.abc import Callable

from mammoth_cli.commands import auth as auth_cmd
from mammoth_cli.commands import config as config_cmd
from mammoth_cli.commands import context as context_cmd

BESPOKE: dict[str, Callable[..., None]] = {
    "auth.login": auth_cmd.auth_login,
    "auth.status": auth_cmd.auth_status,
    "auth.logout": auth_cmd.auth_logout,
    "config.get": config_cmd.config_get,
    "config.set": config_cmd.config_set,
    "config.list": config_cmd.config_list,
    "config.path": config_cmd.config_path,
    "context.project.status": context_cmd.context_project_status,
    "context.project.use": context_cmd.context_project_use,
    "context.project.clear": context_cmd.context_project_clear,
}
