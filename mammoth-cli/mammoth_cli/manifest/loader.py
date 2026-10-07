"""Load and validate the reviewed parity and command manifests.

These manifests are the single source of truth for capability discovery, schema
discovery, help generation, the agent skill, and the parity report. Runtime code
loads them read-only; the build scripts generate them.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import platformdirs

SPEC_ROOT = Path(__file__).resolve().parent.parent.parent / "spec"
MANIFEST_DIR = SPEC_ROOT / "manifests"
COMMANDS_DIR = MANIFEST_DIR / "commands"
SCHEMA_PATH = MANIFEST_DIR / "schema-v1.json"
OPENAPI_OPERATIONS_PATH = MANIFEST_DIR / "openapi-operations.yaml"
SDK_METHODS_PATH = MANIFEST_DIR / "sdk-methods.yaml"

MANIFEST_SCHEMA_VERSION = 1
CACHE_ENV = "MAMMOTH_CLI_MANIFEST_CACHE"
_LEGACY_CACHE_MAX_AGE_SECONDS = 7 * 24 * 3600


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    # Imported here: a warm manifest cache means most runs never parse YAML.
    import yaml

    # libyaml parses the 800 KiB of command manifests in ~0.2 s; the pure-Python
    # loader takes ~2 s, which used to be most of the CLI's start-up time.
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    return yaml.load(path.read_text(encoding="utf-8"), Loader=loader)  # noqa: S506


def cache_dir() -> Path:
    """Return the directory the parsed-manifest cache lives in (not created)."""
    return Path(platformdirs.user_cache_dir("mammoth-cli", "Mammoth"))


def _cache_enabled() -> bool:
    return os.environ.get(CACHE_ENV, "1").strip().lower() not in {"0", "false", "no", "off"}


def _commands_fingerprint(paths: list[Path]) -> str:
    """Identify the exact set of manifest files by name, size and mtime."""
    digest = hashlib.sha256()
    digest.update(str(MANIFEST_SCHEMA_VERSION).encode())
    for path in paths:
        stat = path.stat()
        digest.update(f"{path.name}\0{stat.st_size}\0{stat.st_mtime_ns}\n".encode())
    return digest.hexdigest()[:24]


def _install_id() -> str:
    """Identify this CLI install, so one install's cache never evicts another's."""
    return hashlib.sha256(str(COMMANDS_DIR).encode()).hexdigest()[:8]


def _commands_cache_path(fingerprint: str) -> Path:
    return cache_dir() / f"commands-{_install_id()}-{fingerprint}.json"


def _prune_stale_caches(current: Path) -> None:
    """Delete this install's older cache files, and unattributable ones gone cold.

    Every manifest edit or reinstall changes the fingerprint and so the file
    name; without pruning they pile up forever. Runs only after a cache miss
    wrote a new file. Files from before the install id was in the name cannot
    be attributed, so they go only once untouched for a week.
    """
    cutoff = time.time() - _LEGACY_CACHE_MAX_AGE_SECONDS
    for path in current.parent.glob("commands-*"):
        if path == current:
            continue
        try:
            ours = path.name.startswith(f"commands-{_install_id()}-")
            if ours or path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            continue


def _read_commands_cache(path: Path) -> list[dict[str, Any]] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        return None
    return data


def _write_commands_cache(path: Path, records: list[dict[str, Any]]) -> bool:
    """Write the cache atomically; a cache that cannot be written is simply skipped.

    Returns:
        True when the file was written.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(records, handle, separators=(",", ":"))
        os.replace(tmp, path)
    except OSError:
        return False
    return True


@functools.lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    schema: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return schema


@functools.lru_cache(maxsize=1)
def load_operations() -> list[dict[str, Any]]:
    data = _read_yaml(OPENAPI_OPERATIONS_PATH)
    if not data:
        return []
    return list(data.get("operations", []))


@functools.lru_cache(maxsize=1)
def load_sdk_methods() -> list[dict[str, Any]]:
    data = _read_yaml(SDK_METHODS_PATH)
    if not data:
        return []
    return list(data.get("methods", []))


@functools.lru_cache(maxsize=1)
def load_commands() -> list[dict[str, Any]]:
    """Load every command record across all command group files, sorted by id.

    The parsed records are cached as JSON under :func:`cache_dir`, keyed by the
    manifest files' names, sizes and mtimes, so a normal invocation skips YAML
    parsing entirely. Set ``MAMMOTH_CLI_MANIFEST_CACHE=0`` to bypass the cache.
    """
    if not COMMANDS_DIR.exists():
        return []
    paths = sorted(COMMANDS_DIR.glob("*.yaml"))
    cache_path: Path | None = None
    if _cache_enabled():
        try:
            cache_path = _commands_cache_path(_commands_fingerprint(paths))
        except OSError:
            cache_path = None
        if cache_path is not None:
            cached = _read_commands_cache(cache_path)
            if cached is not None:
                return cached
    records: list[dict[str, Any]] = []
    for path in paths:
        data = _read_yaml(path)
        if not data:
            continue
        records.extend(data.get("commands", []))
    records.sort(key=lambda record: record["command_id"])
    if cache_path is not None:
        if _write_commands_cache(cache_path, records):
            _prune_stale_caches(cache_path)
    return records


@dataclass(frozen=True)
class ManifestSet:
    operations: list[dict[str, Any]]
    sdk_methods: list[dict[str, Any]]
    commands: list[dict[str, Any]]


def load_all() -> ManifestSet:
    return ManifestSet(
        operations=load_operations(),
        sdk_methods=load_sdk_methods(),
        commands=load_commands(),
    )


def command_by_id(command_id: str) -> dict[str, Any] | None:
    for record in load_commands():
        if record["command_id"] == command_id:
            return record
    return None


def clear_cache() -> None:
    """Reset cached manifests (used in tests that rewrite manifest files)."""
    for func in (load_schema, load_operations, load_sdk_methods, load_commands):
        func.cache_clear()
