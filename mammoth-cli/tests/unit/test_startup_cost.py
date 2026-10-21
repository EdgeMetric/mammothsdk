"""Start-up cost guards: pre-compiled manifests and lazily built command groups.

Both exist so a CLI invocation does not parse 800 KiB of YAML and convert
~550 commands to Click before it can send its one request.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
import typer

from mammoth_cli import app as app_module
from mammoth_cli.testing import make_runner


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


@pytest.mark.subprocess
def test_type_system_does_not_import_pydantic() -> None:
    """Describing types needs no pydantic (~20 ms); it is looked up only if already loaded."""
    import subprocess
    import sys

    code = (
        "import sys; import mammoth_cli.services.type_system as t;"
        "assert 'pydantic' not in sys.modules;"
        "assert t._is_model(int) is False; assert 'pydantic' not in sys.modules"
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stderr[-300:]


def test_the_entry_point_turns_off_pydantic_plugin_discovery(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Plugin discovery imports every installed pydantic plugin (logfire: ~0.4 s).
    from mammoth_cli.__main__ import main

    monkeypatch.delenv("PYDANTIC_DISABLE_PLUGINS", raising=False)
    monkeypatch.setattr("sys.argv", ["mammoth", "--version"])
    assert main() == 0
    assert os.environ["PYDANTIC_DISABLE_PLUGINS"] == "__all__"


def test_an_explicit_pydantic_plugin_setting_is_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    from mammoth_cli.__main__ import main

    monkeypatch.setenv("PYDANTIC_DISABLE_PLUGINS", "logfire")
    monkeypatch.setattr("sys.argv", ["mammoth", "--version"])
    main()
    assert os.environ["PYDANTIC_DISABLE_PLUGINS"] == "logfire"


def test_keyring_backend_does_not_import_importlib_metadata() -> None:
    """``importlib.metadata`` costs start-up time; the keyring cache loads it only
    when it reads or writes its record."""
    import subprocess
    import sys

    probe = (
        "import sys, mammoth_cli.context.keyring_backend; "
        "print('importlib.metadata' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True
    ).stdout
    assert out.strip() == "False"


# Modules a run of a generic command must not import: each is needed on one path only
# (``--help`` text, an OAuth sign-in or refresh, a YAML document, a pipeline wait).
_RUN_PATH_PROBE = """
import json, sys
import typer
from mammoth_cli import app
root = typer.main.get_command(app.app)
leaf = root.get_command(None, "project").get_command(None, "list")
leaf.params, leaf.callback  # what a run reads; the help text is read only when printed
from mammoth_cli.runtime import executor, input_loader, opens, state
from mammoth_cli.output import render
from mammoth_cli.context import resolver
sys.stdout.write("\\n" + json.dumps([m for m in {watched!r} if m in sys.modules]))
"""


@pytest.mark.subprocess
def test_running_a_command_imports_only_what_that_path_needs() -> None:
    """Help-only, OAuth-only, YAML-only and pipeline-wait-only modules stay unloaded."""
    import subprocess
    import sys

    watched = (
        "mammoth_cli.commands.schema",
        "mammoth_cli.context.oauth",
        "mammoth_cli.context.oauth_loopback",
        "http.server",
        "webbrowser",
        "yaml",
        "mammoth.api.pipeline",
    )
    done = subprocess.run(
        [sys.executable, "-c", _RUN_PATH_PROBE.format(watched=watched)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert json.loads(done.stdout.rsplit("\n", 1)[-1]) == [], done.stderr[-300:]


@pytest.mark.subprocess
def test_leaf_help_does_not_import_the_handler_module_or_http_stack() -> None:
    """``project list --help`` takes its summary from the index, not the handler's module."""
    watched = (
        "mammoth_cli.commands.project",
        "mammoth_cli.runtime.session",
        "mammoth.client",
        "httpx",
    )
    assert _loaded_heavy_modules("project", "list", "--help", watched=watched) == []


def test_yaml_input_still_parses_and_reports_errors(tmp_path: Path) -> None:
    """YAML is imported on first use; strict duplicate-key and syntax errors still map."""
    from mammoth_cli.errors.envelope import CliError
    from mammoth_cli.runtime.input_loader import load_input_document

    good = tmp_path / "in.yaml"
    good.write_text("a: 1\nb: [2, 3]\n", encoding="utf-8")
    assert load_input_document(str(good), "yaml") == {"a": 1, "b": [2, 3]}
    dup = tmp_path / "dup.yaml"
    dup.write_text("a: 1\na: 2\n", encoding="utf-8")
    with pytest.raises(CliError, match="duplicate"):
        load_input_document(str(dup), "yaml")
    broken = tmp_path / "broken.yaml"
    broken.write_text("a: [1, 2\n", encoding="utf-8")
    with pytest.raises(CliError, match="not valid yaml"):
        load_input_document(str(broken), "yaml")
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{", encoding="utf-8")
    with pytest.raises(CliError, match="not valid json"):
        load_input_document(str(bad_json), "json")
