"""Handlers for the sub-client-backed ``view`` command family.

This package covers dataview operations, checkpoints, data checks, derivatives,
versions, pipeline/task operations, exports, and AI helpers that are backed by
real SDK sub-clients (``DataviewsAPI``, ``CheckpointsAPI``, ``DataChecksAPI``,
``DerivativesAPI``, ``PipelineAPI``, ``PipelineVersionsAPI``, ``ExportsAPI``,
``AIAPI``). It intentionally excludes ``view transform *`` (pipeline
transformation builders), the interactive ``view draft *`` workflow commands,
and ``view create/get/delete`` — those are implemented elsewhere.

Most commands here are project-scoped (their SDK signature carries a
``project_id`` parameter) and take a ``dataset_id`` and/or ``dataview_id`` as
leading positionals, in the order those ids appear in the signature. A few
pipeline/task/AI commands have no ``project_id`` parameter at all — those pass
``None`` as the project id in the envelope metadata, mirroring
:mod:`mammoth_cli.commands.project`'s read handlers. Handlers dispatch through
the generic :meth:`~mammoth_cli.services.protocol.MammothService.call` seam to
the public SDK method named by the command's reviewed manifest ``sdk_symbol``.

The code lives in submodules, one per cluster of commands; the command registry
points at them directly so running one command imports only what it needs. Names
from the former single module stay reachable as ``mammoth_cli.commands.view.X``
through a lazy module ``__getattr__`` (it imports the submodules on first use).
"""

from __future__ import annotations

import importlib
import time
from typing import Any

__all__ = ["time"]

_SUBMODULES = (
    "_common",
    "listing",
    "columns",
    "lifecycle",
    "data_read",
    "join_check",
    "column_checks",
    "aggregate",
    "explore",
    "formatting",
    "checks",
    "derivatives",
    "pipeline",
    "export",
    "export_specialized",
    "export_dataset",
    "settle",
    "upload",
)


def __getattr__(name: str) -> Any:
    if name.startswith("__"):
        raise AttributeError(name)
    for submodule in _SUBMODULES:
        module = importlib.import_module(f"{__name__}.{submodule}")
        if name in vars(module):
            return vars(module)[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
