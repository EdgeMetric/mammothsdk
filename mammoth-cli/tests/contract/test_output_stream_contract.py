"""Public NDJSON lifecycle framing contract."""

from __future__ import annotations

import io
import json

from mammoth_cli.output.render import NDJSON_STREAM_VERSION, render


def _frames(envelope: dict[str, object]) -> list[dict[str, object]]:
    stream = io.StringIO()
    render(envelope, output="ndjson", stream=stream)
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_ndjson_success_has_versioned_terminal_lifecycle_and_pagination() -> None:
    meta = {"pagination": {"next_cursor": "opaque", "has_more": True}}
    frames = _frames({"schema_version": 1, "data": [{"id": 1}], "meta": meta})

    assert [frame["event"] for frame in frames] == ["start", "item", "end"]
    assert all(frame["stream_version"] == NDJSON_STREAM_VERSION for frame in frames)
    assert frames[0]["meta"] == meta
    assert frames[-1] == {
        "complete": True,
        "count": 1,
        "event": "end",
        "meta": meta,
        "schema_version": 1,
        "stream_version": NDJSON_STREAM_VERSION,
    }


def test_ndjson_distinguishes_empty_list_from_scalar_null() -> None:
    empty = _frames({"schema_version": 1, "data": [], "meta": {}})
    null = _frames({"schema_version": 1, "data": None, "meta": {}})

    assert [frame["event"] for frame in empty] == ["start", "end"]
    assert empty[-1]["count"] == 0
    assert [frame["event"] for frame in null] == ["start", "item", "end"]
    assert null[1]["data"] is None
    assert null[-1]["count"] == 1


def test_ndjson_error_is_one_incomplete_terminal_frame() -> None:
    frames = _frames({"schema_version": 1, "error": {"code": "interrupted"}})

    assert frames == [
        {
            "complete": False,
            "error": {"code": "interrupted"},
            "event": "error",
            "meta": None,
            "schema_version": 1,
            "stream_version": NDJSON_STREAM_VERSION,
        }
    ]
