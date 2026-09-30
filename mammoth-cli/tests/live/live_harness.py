"""Helpers shared by the live tests (imported by ``conftest.py`` and the test files)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from mammoth_cli import embed
from mammoth_cli.context.resolver import ExplicitLogin


@dataclass
class LiveCli:
    """Runs the real CLI in-process as one login and returns envelopes."""

    login: ExplicitLogin

    def run(self, *args: str, project: int | str | None = None) -> dict[str, Any]:
        """Run ``mammoth <args>`` (in ``project``) and return the envelope."""
        project_id = int(project) if project is not None else None
        return embed.invoke(list(args), login=self.login, project_id=project_id)

    def ok(self, *args: str, project: int | str | None = None) -> tuple[Any, dict[str, Any]]:
        """Run a command that must succeed; return its ``data`` and ``meta``."""
        envelope = self.run(*args, project=project)
        for _ in range(2):  # koyal answers 502/504 under load
            if envelope.get("error", {}).get("code") not in ("outcome_unknown", "retryable_error"):
                break
            time.sleep(15)
            envelope = self.run(*args, project=project)
        assert "error" not in envelope, f"`{' '.join(args)}` failed: {envelope.get('error')}"
        return envelope["data"], envelope["meta"]

    def err(self, *args: str, project: int | str | None = None) -> dict[str, Any]:
        """Run a command that must fail; return its ``error``."""
        envelope = self.run(*args, project=project)
        assert "error" in envelope, f"`{' '.join(args)}` should have failed: {envelope}"
        error: dict[str, Any] = envelope["error"]
        return error


def envelope_size(envelope: dict[str, Any]) -> int:
    """Characters of the envelope as the CLI prints it."""
    return len(json.dumps(envelope, sort_keys=True, ensure_ascii=False))


@dataclass(frozen=True)
class SalesData:
    """A scratch dataset with text, numeric and text-date columns, and its view."""

    project: int
    dataset: int
    view: int
