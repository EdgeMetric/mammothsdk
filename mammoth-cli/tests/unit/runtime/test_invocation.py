"""One-pass prepared-input behavior for a single CLI invocation."""

from __future__ import annotations

import io

import pytest

from mammoth_cli.runtime.invocation import Invocation


def test_prepared_input_is_cached_for_the_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    class CountingInput(io.StringIO):
        reads = 0

        def read(self, size: int = -1) -> str:
            self.reads += 1
            return super().read(size)

    stream = CountingInput('{"limit": 3}')
    monkeypatch.setattr("sys.stdin", stream)
    invocation = Invocation(command_id="project.list", input_file="-", input_format="json")

    first = invocation.prepare_input()
    second = invocation.load_input()

    assert first == {"limit": 3}
    assert second is first
    assert stream.reads == 1
    assert "_prepared_input" not in repr(invocation)
