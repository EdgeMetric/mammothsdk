"""Module and console entry point for the Mammoth CLI.

This module exposes ``main`` so that both the ``mammoth`` console script and
``python -m mammoth_cli`` start the same Typer application. Keeping the entry
point here (rather than in ``app``) gives the package a stable, importable
launch symbol that does not change when the application wiring moves.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.app import app


def main() -> Any:
    """Run the Mammoth CLI application.

    Returns:
        The value returned by the Typer application, which the runtime uses as
        the process exit code.
    """
    return app()


if __name__ == "__main__":  # pragma: no cover
    main()
