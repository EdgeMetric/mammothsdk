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
        for key in ("human_example", "agent_example"):
            tokens = shlex.split(record[key])[1:]
            assert tokens[: len(path_tokens)] == path_tokens, f"{record['command_id']}.{key}"


def test_bulk_replace_defaults_match_sdk() -> None:
    from mammoth._mixins._text_ops import TextOpsMixin

    sig = inspect.signature(TextOpsMixin.bulk_replace)
    assert sig.parameters["match_case"].default is True
    assert sig.parameters["match_words"].default is False


def test_agent_examples_use_json_no_input() -> None:
    for record in load_commands():
        if record.get("disposition") == "alias":
            continue
        assert "--output json" in record["agent_example"], record["command_id"]
        assert "--no-input" in record["agent_example"], record["command_id"]


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
        assert '"COPY": {}' in example


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
