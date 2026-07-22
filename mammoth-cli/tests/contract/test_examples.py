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
