"""Real-code tests that an invalid ``--output`` fails cleanly before dispatch.

Finding #7 was that ``--output`` was a free string: the producer ran first and
an unknown mode only blew up inside the renderer with a traceback. The executor
now validates the mode up front. These drive the real app in-process (no mocks)
and assert a clean usage envelope, exit code, and the absence of a traceback.
"""

from __future__ import annotations

from mammoth_cli.errors.envelope import EXIT_USAGE
from mammoth_cli.testing import make_runner


def test_invalid_output_mode_is_a_clean_usage_error() -> None:
    """An unknown --output fails with EXIT_USAGE and no traceback."""
    runner = make_runner()
    result = runner.invoke(["config", "path", "--output", "jsno", "--no-input"])
    assert result.exit_code == EXIT_USAGE
    assert "invalid_output_mode" in result.output
    assert "Traceback" not in result.output


def test_valid_output_mode_is_accepted() -> None:
    """A supported --output still runs to a normal result."""
    runner = make_runner()
    result = runner.invoke(["config", "path", "--output", "json", "--no-input"])
    assert result.exit_code == 0
    assert "invalid_output_mode" not in result.output
