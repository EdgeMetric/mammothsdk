"""Manifest example and SDK-default consistency tests."""

from __future__ import annotations

import inspect
import shlex

from mammoth_cli.manifest.loader import load_commands


def test_all_examples_parse() -> None:
    for record in load_commands():
        for key in ("human_example", "agent_example"):
            example = record.get(key)
            if not example:
                continue
            tokens = shlex.split(example)
            assert tokens and tokens[0] == "mammoth", f"{record['command_id']}.{key}: {example}"


def test_all_examples_start_with_command_path() -> None:
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        path_tokens = record["command_path"].split()
        safe_schema_handoff = f"mammoth schema get {record['command_id']}"
        for key in ("human_example", "agent_example"):
            if key == "agent_example" and record[key] == safe_schema_handoff:
                # A deliberately blocked raw request shape hands the agent to
                # the schema lookup instead of advertising a runnable payload.
                assert str(record.get("known_restrictions", "")).startswith("BLOCKED[")
                continue
            tokens = shlex.split(record[key])[1:]
            assert tokens[: len(path_tokens)] == path_tokens, f"{record['command_id']}.{key}"


def test_bulk_replace_defaults_match_sdk() -> None:
    from mammoth._mixins._text_ops import TextOpsMixin

    sig = inspect.signature(TextOpsMixin.bulk_replace)
    assert sig.parameters["match_case"].default is True
    assert sig.parameters["match_words"].default is False


def test_agent_examples_carry_no_redundant_output_flags() -> None:
    """A piped run is already machine JSON and never prompts; the flags cost tokens."""
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        assert "--output json" not in record["agent_example"], record["command_id"]
        assert "--no-input" not in record["agent_example"], record["command_id"]


def test_generic_pipeline_task_examples_are_structural_and_warn_about_typed_routes() -> None:
    records = {
        record["command_id"]: record
        for record in load_commands()
        if record["command_id"] in {"view.task.add", "view.task.preview", "view.task.update"}
    }
    assert set(records) == {"view.task.add", "view.task.preview", "view.task.update"}
    for record in records.values():
        example = record["agent_example"]
        assert "sample_key" not in example
        assert '"DATAVIEW_ID": 123' in example
        # The backend COPY param template: a list of SOURCE/AS items, VERSION 2.
        assert '"COPY": [{"SOURCE": "column_1", "AS": {' in example
        assert '"INTERNAL_NAME": "column_9"' in example
        assert '"VERSION": 2' in example


def test_generated_task_docs_do_not_present_opaque_examples_as_usable_tasks() -> None:
    from pathlib import Path

    docs = Path(__file__).parents[2] / "docs" / "reference" / "commands.md"
    text = docs.read_text(encoding="utf-8")
    for command in ("view task add", "view task preview", "view task update"):
        start = text.index(f"### `mammoth {command}`")
        end = text.find("\n### `mammoth ", start + 1)
        block = text[start:] if end == -1 else text[start:end]
        assert '"sample_key"' not in block
        assert "illustrative low-level expert envelope" in block
        assert "Prefer typed view transform commands" in block
        assert "`view.transform.filter`" in block
        assert "`view.transform.math`" in block
        assert "mammoth schema get view.transform.filter" in block
        assert "`mammoth view transform ...`" not in block
