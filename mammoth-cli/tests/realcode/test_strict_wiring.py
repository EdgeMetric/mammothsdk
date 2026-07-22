"""End-to-end tests that strict validation is wired into the live app.

These drive the real Typer app in-process and the real schema command, with no
mocks, to prove the argspec/strict foundation is actually reached at runtime:

* an unknown option fails with a clean usage envelope (#3),
* an unknown --input field fails before the handler drops it (#5),
* schema discovery reports the real accepted fields (#4).
"""

from __future__ import annotations

import json
from pathlib import Path

from mammoth_cli.commands.schema import get_schema
from mammoth_cli.errors.envelope import EXIT_USAGE
from mammoth_cli.testing import make_runner

_BULK_REPLACE_ID = "view.transform.bulk-replace"


def test_unknown_option_fails_through_the_app() -> None:
    """A stray option is rejected by the live command, not silently ignored."""
    runner = make_runner()
    result = runner.invoke(["view", "get", "5", "--nope", "--output", "json", "--no-input"])
    assert result.exit_code == EXIT_USAGE
    assert "unknown_option" in result.output


def test_unknown_input_field_fails_through_the_app(tmp_path: Path) -> None:
    """An unknown --input key is rejected before the handler drops it."""
    doc = tmp_path / "in.json"
    doc.write_text(json.dumps({"columns": ["Item"], "mapping": [], "colums": 1}), encoding="utf-8")
    runner = make_runner()
    result = runner.invoke(
        [
            "view",
            "transform",
            "bulk-replace",
            "5",
            "--input",
            str(doc),
            "--output",
            "json",
            "--no-input",
        ]
    )
    assert result.exit_code == EXIT_USAGE
    assert "unknown_input_field" in result.output


def test_schema_get_reports_accepted_fields() -> None:
    """schema discovery surfaces the real backing-method field set (#4)."""
    schema = get_schema(_BULK_REPLACE_ID)
    assert schema is not None
    fields = schema["accepted_fields"]
    assert fields is not None
    names = {field["name"] for field in fields}
    assert {"columns", "mapping", "match_case"} <= names
    assert any(field["name"] == "columns" and field["required"] for field in fields)
