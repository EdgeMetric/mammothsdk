"""Documentation command examples are complete, typed, and safe to copy.

The README and every shipped Markdown document are part of the CLI contract.
This gate deliberately parses examples without invoking their handlers: most
examples require credentials or mutate a tenant, but Click parsing is enough
to catch a renamed command, a removed positional, or a stale flag.  Inline,
fenced, multiline, and placeholder-bearing examples are all collected.  A
small, explicitly safe subset is also executed in a logged-out subprocess to
prove the advertised offline semantics still work in the real entry point.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pytest
from jsonschema import validate

from mammoth_cli.commands.schema import schema_entries
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.strict import validate_input_fields

pytestmark = pytest.mark.subprocess

_CLI_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _CLI_ROOT.parent
_MARKDOWN = (
    _REPO_ROOT / "README.md",
    _CLI_ROOT / "README.md",
    *_CLI_ROOT.joinpath("docs").rglob("*.md"),
)
_INLINE_COMMAND = re.compile(r"`(mammoth(?:\s+[^`\n]+)?)`")
_PROMPT = re.compile(r"^\s*(?:\$\s*)?(mammoth(?:\s|$).*)$")
_PLACEHOLDER = re.compile(r"<[^>]+>")
_SHELL_OPERATORS = frozenset({"|", "||", "&&", ";", ">", ">>", "<", "<<"})
_SAFE_OFFLINE = {
    "mammoth --version",
    "mammoth schema list",
    "mammoth capability list",
}
_MAMMOTH_ENV = (
    "MAMMOTH_API_KEY",
    "MAMMOTH_API_SECRET",
    "MAMMOTH_WORKSPACE_ID",
    "MAMMOTH_SERVER_PREFIX",
    "CI",
)


@dataclass(frozen=True)
class DocumentedCommand:
    source: Path
    line: int
    command: str
    runnable: bool

    @property
    def label(self) -> str:
        return f"{self.source.relative_to(_REPO_ROOT)}:{self.line}: {self.command}"


def _shell_tokens(command: str) -> list[str]:
    """Tokenize one shell command, retaining just the mammoth invocation.

    Shell redirections and a pipeline's downstream tools are not CLI flags.
    Their presence must not cause the preceding mammoth example to be skipped.
    """
    tokens = shlex.split(command, comments=True)
    for index, token in enumerate(tokens):
        if token in _SHELL_OPERATORS or token.startswith((">", "<")):
            return tokens[:index]
    return tokens


def _fenced_commands(path: Path) -> Iterable[DocumentedCommand]:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_fence = False
    pending: list[str] = []
    start = 0
    for number, raw in enumerate(lines, start=1):
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            if not in_fence and pending:
                # An unterminated quote in a fenced command is itself a broken
                # example; yield it so the parser test reports its source.
                yield DocumentedCommand(path, start, "\n".join(pending), True)
                pending = []
            continue
        if not in_fence:
            continue
        match = _PROMPT.match(raw)
        if match and not pending:
            pending = [match.group(1)]
            start = number
        elif pending:
            pending.append(raw)
        else:
            continue
        candidate = "\n".join(pending).replace("\\\n", " ")
        try:
            _shell_tokens(candidate)
        except ValueError:
            continue  # quoted multiline JSON; collect the next line
        yield DocumentedCommand(path, start, candidate, True)
        pending = []


def _inline_commands(path: Path) -> Iterable[DocumentedCommand]:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        # Reference headings name a command but deliberately omit its required
        # arguments. They are headings, not copy-and-paste examples.
        if line.lstrip().startswith("#"):
            continue
        for match in _INLINE_COMMAND.finditer(line):
            yield DocumentedCommand(path, number, match.group(1), "example" in line.lower())


def _extract_commands() -> list[DocumentedCommand]:
    """Return every documented ``mammoth`` invocation, without skip filters."""
    commands: dict[tuple[Path, int, str], DocumentedCommand] = {}
    for path in sorted(_MARKDOWN):
        for command in (*_fenced_commands(path), *_inline_commands(path)):
            commands[(command.source, command.line, command.command)] = command
    return list(commands.values())


def _replace_placeholder(match: re.Match[str]) -> str:
    value = match.group(0).lower()
    if "command" in value:
        return "view.transform.math"
    if "int" in value or "id" in value or "number" in value:
        return "1"
    return "example"


def _materialize(command: str) -> list[str]:
    """Give documentation placeholders deterministic, parser-valid values."""
    if "<command>" in command:
        # Abstract agent syntax is documented with a real command/typed request
        # so that its global flags are checked rather than skipped.
        command = command.replace("<command>", "view transform math 1")
        request = "--input '{\"expression\": \"price * qty\", \"new_column\": \"total\"}'"
        command = command.replace("--input request.yaml", request)
    text = _PLACEHOLDER.sub(_replace_placeholder, command)
    tokens = _shell_tokens(text)
    assert tokens and tokens[0] == "mammoth", command
    # Uppercase placeholders are values, not a reason to skip validation.  The
    # string value is intentionally usable for both ids (Click coerces it) and
    # JSON string fields such as folder_resource_id.
    values = ["1" if re.fullmatch(r"[A-Z][A-Z0-9_]*", token) else token for token in tokens]
    # ``mammoth COMMAND --help`` is documentation syntax, but its placeholder
    # still has to be routed through a real command group.
    return ["schema" if token == "1" and original == "COMMAND" else token
            for token, original in zip(values, tokens, strict=True)]


_COMMANDS = _extract_commands()
_SCHEMAS = {entry["command_id"]: entry for entry in schema_entries()}
_PATHS = {
    tuple(record["command_path"].split()): record["command_id"]
    for record in load_commands()
    if record.get("disposition") != "alias"
}


def _resolve_path(tokens: list[str]) -> tuple[tuple[str, ...], str]:
    candidates = [path for path in _PATHS if tokens[1 : 1 + len(path)] == list(path)]
    assert candidates, f"unknown documented command path: {' '.join(tokens)}"
    path = max(candidates, key=len)
    return path, _PATHS[path]


def _parse_with_real_click(tokens: list[str], *, require_complete: bool) -> str | None:
    """Parse the leaf command through the app's actual Click command tree."""
    import mammoth_cli.app as app_module

    root = app_module._root_click_command()
    if len(tokens) == 1:
        return None
    if tokens[1].startswith("-"):
        root_options = {option for param in root.params for option in param.opts}
        assert tokens[1] in root_options, f"unknown documented root flag: {tokens[1]}"
        return None  # eager --version/--help callbacks intentionally exit while parsing
    try:
        path, command_id = _resolve_path(tokens)
    except AssertionError:
        # ``mammoth COMMAND --help`` describes a command group rather than a
        # leaf.  It is still collected and checked against the real root tree.
        assert tokens[1] in root.commands, f"unknown documented command group: {tokens[1]}"
        assert tokens[2:] == ["--help"], f"unroutable documented command: {' '.join(tokens)}"
        return None
    if not require_complete:
        return command_id
    command = root
    for part in path:
        command = command.commands[part]
    # This constructs the real Click context and performs option/positional
    # conversion, without executing a remote or mutating handler.
    command.make_context(command_id, tokens[1 + len(path) :])
    return command_id


def _validate_structured_input(tokens: list[str], command_id: str) -> None:
    if "--input" not in tokens:
        return
    value = tokens[tokens.index("--input") + 1]
    if not value.startswith(("{", "[")):
        return  # file/stdin input is intentionally not read by this offline gate
    document = json.loads(value)
    validate_input_fields(command_id, document)
    validate(document, _SCHEMAS[command_id]["input_schema"])


def test_docs_contain_examples_from_readme_and_docs() -> None:
    sources = {command.source for command in _COMMANDS}
    assert _CLI_ROOT / "README.md" in sources
    assert any(source.parent == _CLI_ROOT / "docs" for source in sources)
    assert len(_COMMANDS) >= 40, f"only found {len(_COMMANDS)} documentation commands"
    assert any("\n" in command.command for command in _COMMANDS), "no multiline example extracted"
    assert any("<" in command.command or re.search(r"\b[A-Z][A-Z0-9_]*\b", command.command)
               for command in _COMMANDS), "no placeholder example extracted"


@pytest.mark.parametrize("documented", _COMMANDS, ids=lambda item: item.label)
def test_documented_commands_parse_and_validate_input(documented: DocumentedCommand) -> None:
    tokens = _materialize(documented.command)
    command_id = _parse_with_real_click(tokens, require_complete=documented.runnable)
    if command_id is not None and documented.runnable:
        _validate_structured_input(tokens, command_id)


@pytest.mark.parametrize("command", sorted(_SAFE_OFFLINE))
def test_safe_documented_commands_work_logged_out(command: str, tmp_path: Path) -> None:
    """Selected examples that promise offline discovery must execute successfully."""
    env = dict(os.environ)
    for key in _MAMMOTH_ENV:
        env.pop(key, None)
    env["XDG_CONFIG_HOME"] = str(tmp_path)
    env["TERMINAL_WIDTH"] = env["COLUMNS"] = "1000"
    tokens = _materialize(command)
    result = subprocess.run(
        [sys.executable, "-m", "mammoth_cli", *tokens[1:], "--output", "json", "--no-input"],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert result.returncode == 0, f"{command}\nstdout={result.stdout}\nstderr={result.stderr}"
