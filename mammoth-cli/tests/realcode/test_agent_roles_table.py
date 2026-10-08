"""``mammoth agent roles`` in table mode shows one row per role."""

from __future__ import annotations

import io

from mammoth_cli.output.render import _render_table


def test_wrapped_list_result_renders_one_row_per_item() -> None:
    stream = io.StringIO()
    _render_table(
        {"result": [{"role": "admin", "read_only": False}, {"role": "viewer", "read_only": True}]},
        stream,
    )
    lines = stream.getvalue().splitlines()
    assert any("role" in line and "read_only" in line for line in lines)
    assert sum("admin" in line for line in lines) == 1
    assert sum("viewer" in line for line in lines) == 1
    assert "result" not in stream.getvalue()
