"""Start-up cost guards: the manifest cache and lazily built command groups.

Both exist so a CLI invocation does not parse 800 KiB of YAML and convert
~550 commands to Click before it can send its one request.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import typer

from mammoth_cli import app as app_module
from mammoth_cli.manifest import loader
from mammoth_cli.testing import make_runner


@pytest.fixture
def cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    monkeypatch.setattr(loader, "cache_dir", lambda: tmp_path / "cache")
    monkeypatch.delenv(loader.CACHE_ENV, raising=False)
    loader.clear_cache()
    yield tmp_path / "cache"
    loader.clear_cache()


def test_first_load_writes_cache_and_second_load_reads_it(cache_dir: Path) -> None:
    first = loader.load_commands()
    files = list(cache_dir.glob("commands-*.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text()) == first

    # Poison the cache: a cache hit returns this, a YAML parse would not.
    marker = [{"command_id": "zzz.marker", "command_path": "zzz marker"}]
    files[0].write_text(json.dumps(marker))
    loader.clear_cache()
    assert loader.load_commands() == marker


def test_cache_key_changes_when_a_manifest_changes(
    cache_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loader.load_commands()
    (before,) = cache_dir.glob("commands-*.json")
    paths = sorted(loader.COMMANDS_DIR.glob("*.yaml"))
    stat = paths[0].stat()

    class _Stat:
        st_size = stat.st_size + 1
        st_mtime_ns = stat.st_mtime_ns

    real_stat = Path.stat

    def fake_stat(self: Path, *args: object, **kwargs: object) -> object:
        return _Stat() if self == paths[0] else real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", fake_stat)
    loader.clear_cache()
    loader.load_commands()
    names = {p.name for p in cache_dir.glob("commands-*.json")}
    assert before.name in names and len(names) == 2


def test_corrupt_cache_falls_back_to_yaml(cache_dir: Path) -> None:
    loader.load_commands()
    (path,) = cache_dir.glob("commands-*.json")
    path.write_text("{not json")
    loader.clear_cache()
    records = loader.load_commands()
    assert any(r["command_id"] == "view.list" for r in records)
    assert json.loads(path.read_text()) == records  # rewritten


def test_cache_can_be_disabled(cache_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(loader.CACHE_ENV, "0")
    records = loader.load_commands()
    assert any(r["command_id"] == "view.list" for r in records)
    assert not cache_dir.exists()


def test_unwritable_cache_dir_is_not_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    loader.clear_cache()
    monkeypatch.setattr(loader, "cache_dir", lambda: Path("/proc/does-not-exist/mammoth"))
    assert any(r["command_id"] == "view.list" for r in loader.load_commands())


def test_top_level_groups_are_built_on_demand() -> None:
    app_module._top_level_typer.cache_clear()
    root: Any = typer.main.get_command(app_module.app)
    eager = root.__dict__.get("_eager_commands", {})
    assert "doctor" in eager and "view" not in eager
    assert "view" in root.list_commands(None) and "dataset" in root.list_commands(None)

    view = root.get_command(None, "view")
    assert view is not None and "list" in view.commands
    assert set(root.__dict__["_eager_commands"]) >= {"doctor", "view"}
    assert "dataset" not in root.__dict__["_eager_commands"]

    # Reading ``commands`` materialises every group for tree walkers.
    assert {"view", "dataset", "dashboard"} <= set(root.commands)
    assert root.get_command(None, "no-such-group") is None


def test_lazy_root_help_and_group_help_render() -> None:
    root = make_runner().invoke(["--help"])
    assert root.exit_code == 0
    assert "view" in root.output and "dataset" in root.output
    group = make_runner().invoke(["view", "--help"])
    assert group.exit_code == 0
    assert "transform" in group.output


# Modules that must stay unloaded until a command actually dispatches: the
# generated dashboard models and the HTTP stack cost hundreds of milliseconds
# each, and `--version`, `--help` and a mistyped command never use them.
_HEAVY_MODULES = (
    "mammoth.models.dashboard_generated",
    "mammoth.api.dashboard_generated",
    "mammoth.client",
    "mammoth.view",
    "httpx",
    "keyring",
)

_PROBE = """
import json, sys
sys.argv = ["mammoth", *sys.argv[1:]]
from mammoth_cli.__main__ import main
try:
    main()
except SystemExit:
    pass
sys.stdout.write("\\n" + json.dumps([m for m in {heavy!r} if m in sys.modules]))
"""


def _loaded_heavy_modules(*argv: str) -> list[str]:
    import subprocess
    import sys

    done = subprocess.run(
        [sys.executable, "-c", _PROBE.format(heavy=_HEAVY_MODULES), *argv],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    loaded: list[str] = json.loads(done.stdout.rsplit("\n", 1)[-1])
    return loaded


@pytest.mark.subprocess
@pytest.mark.parametrize(
    "argv",
    [["--version"], ["--help"], ["project", "--help"], ["list"]],
    ids=["version", "root-help", "group-help", "unknown-command"],
)
def test_startup_before_dispatch_loads_no_heavy_modules(argv: list[str]) -> None:
    assert _loaded_heavy_modules(*argv) == []


def test_every_dashboard_command_still_has_a_handler() -> None:
    """Dashboard commands are matched by SDK symbol prefix, not by importing the generated list."""
    from mammoth.api.dashboard_generated import GENERATED_METHODS

    from mammoth_cli.commands.registry import HANDLERS
    from mammoth_cli.manifest.loader import load_commands

    prefix = "mammoth.api.dashboards.DashboardsAPI."
    generated = {f"{prefix}{method}" for method in GENERATED_METHODS}
    for record in load_commands():
        if record.get("sdk_symbol") in generated:
            assert str(record["command_id"]) in HANDLERS


def test_sdk_sub_clients_resolve_without_being_built_up_front() -> None:
    from mammoth.client import MammothClient

    from mammoth_cli.services.dispatch import resolve_sdk_method

    client = MammothClient(api_token="mm_unit_test_token")
    assert "projects" not in vars(client)
    method = resolve_sdk_method(client, "mammoth.api.projects.ProjectsAPI.list")
    assert callable(method)
    assert type(vars(client)["projects"]).__name__ == "ProjectsAPI"
