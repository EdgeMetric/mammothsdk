"""Remember which OS keyring backend the last run detected.

``keyring.get_keyring`` loads every installed backend plugin to pick one, about
0.3 s on every run that reads a keyring credential. The console entry point
calls :func:`enable`; from then on :func:`install_cached` re-selects the backend
an earlier run recorded and :func:`remember` records it. Library callers and
tests never call :func:`enable`, so they keep whichever backend they installed.

A missing, stale or unusable record is a plain miss: detection then runs as
before. A backend named by ``PYTHON_KEYRING_BACKEND`` or a ``keyringrc.cfg`` is
never cached, so the user's explicit choice always wins.
"""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

_CACHE_FILENAME = "keyring-backend.json"
_enabled = False
_recorded = False


def enable() -> None:
    """Turn the backend cache on for this process (the console entry point)."""
    global _enabled
    _enabled = True


def _cache_path() -> Path:
    from mammoth_cli.manifest.loader import cache_dir

    return cache_dir() / _CACHE_FILENAME


def _choice_is_automatic() -> bool:
    """True when neither the environment nor a keyringrc file names a backend."""
    from keyring.util import platform_

    if os.environ.get("PYTHON_KEYRING_BACKEND"):
        return False
    return not (Path(platform_.config_root()) / "keyringrc.cfg").exists()


def install_cached() -> None:
    """Select the recorded backend, skipping keyring's plugin scan."""
    global _recorded
    if not _enabled or not _choice_is_automatic():
        return
    from importlib.metadata import version

    import keyring

    try:
        cached = json.loads(_cache_path().read_text(encoding="utf-8"))
        if cached["keyring"] != version("keyring"):
            return
        module, _, name = cached["backend"].partition(":")
        backend_class = getattr(importlib.import_module(module), name)
        if backend_class.viable:
            keyring.set_keyring(backend_class())
            _recorded = True
    except (OSError, ValueError, KeyError, ImportError, AttributeError, TypeError):
        return


def remember(backend: object) -> None:
    """Record the backend in use for :func:`install_cached`; a read-only cache is skipped."""
    global _recorded
    if _recorded or not _enabled or not _choice_is_automatic():
        return
    from importlib.metadata import version

    kind = type(backend)
    record = {
        "backend": f"{kind.__module__}:{kind.__qualname__}",
        "keyring": version("keyring"),
    }
    path = _cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        scratch = path.with_suffix(f".{os.getpid()}.tmp")
        scratch.write_text(json.dumps(record), encoding="utf-8")
        scratch.replace(path)
        _recorded = True
    except OSError:
        return
