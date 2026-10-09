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
    assert before.name not in names and len(names) == 1


def test_a_cache_miss_prunes_older_files_of_this_install_only(cache_dir: Path) -> None:
    import os
    import time

    loader.load_commands()
    (current,) = cache_dir.glob("commands-*.json")
    install = current.name.split("-")[1]
    mine_stale = cache_dir / f"commands-{install}-{'0' * 24}.json"
    other_install = cache_dir / f"commands-ffffffff-{'1' * 24}.json"
    legacy_fresh = cache_dir / f"commands-{'2' * 24}.json"
    legacy_cold = cache_dir / f"commands-{'3' * 24}.json"
    for path in (mine_stale, other_install, legacy_fresh, legacy_cold):
        path.write_text("[]")
    month_ago = time.time() - 30 * 24 * 3600
    os.utime(legacy_cold, (month_ago, month_ago))

    current.unlink()  # force a miss, which writes and then prunes
    loader.clear_cache()
    loader.load_commands()

    left = {p.name for p in cache_dir.glob("commands-*.json")}
    assert mine_stale.name not in left and legacy_cold.name not in left
    assert other_install.name in left and legacy_fresh.name in left
    assert len(left) == 3


def test_a_cache_hit_prunes_nothing(cache_dir: Path) -> None:
    loader.load_commands()
    stray = cache_dir / f"commands-ffffffff-{'4' * 24}.json"
    stray.write_text("[]")
    loader.clear_cache()
    loader.load_commands()
    assert stray.exists()


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
    assert "doctor" not in eager and "view" not in eager
    names = root.list_commands(None)
    assert {"doctor", "view", "dataset"} <= set(names)
    # Top-level leaves list ahead of groups, as they were registered.
    assert names.index("doctor") < names.index("view")

    doctor = root.get_command(None, "doctor")
    assert doctor is not None and doctor.name == "doctor"
    assert "view" not in root.__dict__["_eager_commands"]

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

# The lazy command boundary: no command module, SDK service or schema machinery
# is imported until a command is dispatched. ``--help`` and typo suggestions
# read names (and, for top-level leaves, a pinned help string), nothing more.
_ERROR_PATH_MODULES = (
    "pydantic",
    "mammoth_cli.services.command_contract",
    "mammoth_cli.runtime.executor",
)
_COMMAND_BOUNDARY = (
    "pydantic",
    "mammoth.models.pipeline",
    "mammoth_cli.commands.project",
    "mammoth_cli.commands.view",
    "mammoth_cli.commands.doctor",
    "mammoth_cli.commands.schema",
    "mammoth_cli.services.sdk_service",
    "mammoth_cli.services.command_contract",
    "mammoth_cli.runtime.session",
    "mammoth_cli.runtime.executor",
    "mammoth_cli.context.resolver",
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


def _loaded_heavy_modules(*argv: str, watched: tuple[str, ...] = _HEAVY_MODULES) -> list[str]:
    import subprocess
    import sys

    done = subprocess.run(
        [sys.executable, "-c", _PROBE.format(heavy=watched), *argv],
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


@pytest.mark.subprocess
@pytest.mark.parametrize(
    "argv",
    [["--version"], ["--help"], ["lst"]],
    ids=["version", "root-help", "typo-suggestion"],
)
def test_root_help_and_typo_import_no_command_module(argv: list[str]) -> None:
    # A typo ends in the error envelope, which legitimately loads the executor.
    emits_error = argv == ["lst"]
    boundary = tuple(m for m in _COMMAND_BOUNDARY if not (emits_error and m in _ERROR_PATH_MODULES))
    watched = (*_HEAVY_MODULES, *boundary)
    assert _loaded_heavy_modules(*argv, watched=watched) == []


_BUILD_PROBE = """
import json, sys
from mammoth_cli import app
app._load_top_level_group("project")
sys.stdout.write("\\n" + json.dumps([m for m in {watched!r} if m in sys.modules]))
"""


@pytest.mark.subprocess
def test_building_a_group_imports_no_handler_module() -> None:
    """Dispatching ``project ...`` builds the project group, not its 24 handler modules."""
    import subprocess
    import sys

    watched = (
        "httpx",
        "mammoth.client",
        "mammoth_cli.commands.project",
        "mammoth_cli.commands.view",
        "mammoth_cli.services.sdk_service",
        "mammoth_cli.runtime.session",
    )
    done = subprocess.run(
        [sys.executable, "-c", _BUILD_PROBE.format(watched=watched)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert json.loads(done.stdout.rsplit("\n", 1)[-1]) == []


def test_root_leaf_help_table_matches_the_handler_docstrings() -> None:
    """``--help`` prints a pinned string for top-level leaves; it must equal the real one."""
    from mammoth_cli.manifest.loader import command_by_id

    assert set(app_module._ROOT_LEAF_HELP) == set(app_module._LAZY_LEAF_IDS)
    for name, command_id in app_module._LAZY_LEAF_IDS.items():
        real = app_module._command_help(command_id, command_by_id(command_id))
        assert app_module._ROOT_LEAF_HELP[name] == real, name


def test_group_command_help_is_read_from_the_handler_when_printed() -> None:
    result = make_runner().invoke(["project", "list", "--help"])
    assert result.exit_code == 0
    assert "List the caller's member projects" in result.output


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


def test_help_summary_index_matches_handler_docstrings() -> None:
    """The listing reads the index, so it must not drift from the live docstrings.

    Regenerate with ``python scripts/gen_help_summaries.py``.
    """
    import importlib.util

    script = Path(__file__).resolve().parents[2] / "scripts" / "gen_help_summaries.py"
    spec = importlib.util.spec_from_file_location("gen_help_summaries", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert json.loads(module.INDEX.read_text(encoding="utf-8")) == module.live_index()


def test_group_help_does_not_import_the_sdk_models() -> None:
    """``mammoth view --help`` lists commands without importing handlers or SDK models."""
    import subprocess
    import sys

    code = (
        "import sys; from mammoth_cli.__main__ import main\n"
        "sys.argv = ['mammoth', 'view', '--help']\n"
        "try:\n    main()\nexcept SystemExit:\n    pass\n"
        "sys.stderr.write('LOADED=' + str('mammoth.view' in sys.modules or "
        "'mammoth_cli.commands.view' in sys.modules))"
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert "LOADED=False" in done.stderr, done.stderr[-300:]


def test_agent_group_is_hidden_from_root_help_but_still_runs() -> None:
    root = make_runner().invoke(["--help"])
    assert "skill" in root.output
    assert "Work with Mammoth agent sessions" not in root.output
    assert "Work with Mammoth agent sessions" in make_runner().invoke(["agent", "--help"]).output
