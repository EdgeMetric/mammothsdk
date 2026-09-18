"""Generated examples remain shell-safe, typed, and accepted by the real parser."""

from __future__ import annotations

import json
import shlex

from jsonschema import validate

from mammoth_cli.commands.schema import schema_entries
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.runtime.strict import validate_input_fields


def test_every_generated_example_parses_and_has_valid_structured_input() -> None:
    import mammoth_cli.app as app_module

    secret_fields = {
        record["command_id"]: record.get("secret_fields") or [] for record in load_commands()
    }
    for schema in schema_entries():
        example = schema["runnable_example"]
        if example is None:
            continue
        tokens = shlex.split(example)
        assert tokens[0] == "mammoth", schema["command_id"]
        if "--input" in tokens:
            raw_input = tokens[tokens.index("--input") + 1]
            if raw_input == "/private/path/request.json":
                # A secret-bearing request is published as a protected file
                # reference, never as inline JSON; the example must name a
                # secret field so the redirection is justified.
                assert secret_fields[schema["command_id"]], schema["command_id"]
            else:
                document = json.loads(raw_input)
                validate_input_fields(schema["command_id"], document)
                validate(document, schema["input_schema"])
        command = app_module._root_click_command()
        path = schema["command_path"].split()
        for part in path:
            command = command.commands[part]
        # Build the real leaf Click context (including positional and option
        # conversion) without invoking its handler or touching the network.
        context = command.make_context(schema["command_id"], tokens[1 + len(path) :])
        assert context.params, schema["command_id"]
