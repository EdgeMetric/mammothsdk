"""Module and console entry point for the Mammoth CLI.

This module exposes ``main`` so that both the ``mammoth`` console script and
``python -m mammoth_cli`` start the same Typer application. Keeping the entry
point here (rather than in ``app``) gives the package a stable, importable
launch symbol that does not change when the application wiring moves.
"""

from __future__ import annotations

import os
import sys
from typing import Any

_SDK_MISSING = (
    "mammoth: the mammoth-io SDK cannot be imported ({error}).\n"
    "This install is broken: mammoth-io is missing, or it was installed from a checkout "
    "that no longer exists.\n"
    "Reinstall the CLI, which brings its own mammoth-io: "
    "pipx install --force mammoth-cli (or pip install --force-reinstall mammoth-cli).\n"
)


def main() -> Any:
    """Run the Mammoth CLI application.

    Returns:
        The value returned by the Typer application, which the runtime uses as
        the process exit code.
    """
    # pydantic looks up installed plugins (entry points) the first time it builds a
    # model, and imports each one it finds: with logfire in the environment that is
    # about 0.4 s on every command that loads the SDK. The CLI uses no plugin.
    os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "__all__")
    if sys.argv[1:] == ["--version"]:
        # The answer needs none of the command tree; skip building it.
        from mammoth_cli import __version__

        sys.stdout.write(f"{__version__}\n")
        return 0
    try:
        from mammoth_cli.app import app
        from mammoth_cli.context import keyring_backend

        keyring_backend.enable()
        return app()
    except ModuleNotFoundError as exc:
        # Commands import the SDK as they run, so the failure can surface inside app().
        if exc.name is None or exc.name.split(".")[0] != "mammoth":
            raise
        sys.stderr.write(_SDK_MISSING.format(error=exc))
        return 1


if __name__ == "__main__":  # pragma: no cover
    main()
