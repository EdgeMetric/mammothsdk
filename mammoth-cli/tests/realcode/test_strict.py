"""Real-code tests for strict option and input-field validation.

These exercise the real validators against real manifest commands and their
real backing SDK signatures. No mocks.
"""

from __future__ import annotations

import pytest

from mammoth_cli.errors.envelope import EXIT_USAGE, CliError
from mammoth_cli.runtime.strict import validate_extra_args, validate_input_fields

_BULK_REPLACE = "view.transform.bulk-replace"


def test_unknown_option_is_rejected() -> None:
    """A stray --option token fails with a clean usage error."""
    with pytest.raises(CliError) as excinfo:
        validate_extra_args(_BULK_REPLACE, ["1039", "--colum", "Item"])
    assert excinfo.value.code == "unknown_option"
    assert excinfo.value.exit_status == EXIT_USAGE


def test_bare_positionals_are_allowed() -> None:
    """Positional tokens (ids) pass through untouched."""
    validate_extra_args(_BULK_REPLACE, ["1039"])


def test_stdin_sentinel_is_not_an_option() -> None:
    """A bare '-' (stdin sentinel) is not treated as an option."""
    validate_extra_args(_BULK_REPLACE, ["-"])


def test_unknown_input_field_is_rejected() -> None:
    """A document key the backing method cannot accept is refused."""
    with pytest.raises(CliError) as excinfo:
        validate_input_fields(_BULK_REPLACE, {"columns": ["Item"], "colums": ["x"]})
    assert excinfo.value.code == "unknown_input_field"
    assert "colums" in excinfo.value.message


def test_known_input_fields_pass() -> None:
    """Every accepted field of the backing method is allowed."""
    validate_input_fields(
        _BULK_REPLACE,
        {"columns": ["Item"], "mapping": [], "match_case": True, "match_words": False},
    )


def test_no_document_is_a_noop() -> None:
    """No document means nothing to validate."""
    validate_input_fields(_BULK_REPLACE, None)
    validate_input_fields(_BULK_REPLACE, {})


def test_unbacked_command_does_not_enforce() -> None:
    """A command without a resolvable backing symbol keeps prior behavior."""
    # 'config' commands are bespoke and have no SDK symbol; must not raise.
    validate_input_fields("config.get", {"anything": 1})
