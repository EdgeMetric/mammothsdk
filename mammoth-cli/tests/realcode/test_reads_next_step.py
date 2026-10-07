"""``view analyze`` refuses a pasted list and a non-id before it reads anything."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mammoth_cli.testing import make_runner


def _run(args: list[str], tmp_path: Path) -> Any:
    doc = tmp_path / "in.json"
    doc.write_text("{}", encoding="utf-8")
    return make_runner().invoke(
        [*args, "--project", "180", "--input", str(doc), "--output", "json", "--no-input"]
    )


def test_view_analyze_refuses_a_pasted_list_and_a_non_id(tmp_path: Path) -> None:
    too_many = _run(["view", "analyze", ",".join(str(n) for n in range(1, 14)), "9"], tmp_path)
    not_an_id = _run(["view", "analyze", "7,abc", "9"], tmp_path)

    assert json.loads(too_many.output)["error"]["code"] == "too_many_ids"
    assert json.loads(not_an_id.output)["error"]["code"] == "invalid_argument"
