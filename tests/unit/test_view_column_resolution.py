"""Unit tests for View column resolution and metadata."""

from __future__ import annotations

import pytest

from mammoth.condition import Condition
from mammoth.exceptions import MammothColumnError
from mammoth.models.pipeline import Operator
from mammoth.view import View


class TestColumnMaps:
    """Test View._build_column_maps and column access."""

    def test_display_names(self, mock_view):
        assert "emp_id" in mock_view.display_names
        assert "base_salary" in mock_view.display_names

    def test_columns_dict(self, mock_view):
        assert mock_view.columns["emp_id"] == "column_abc1234567"
        assert mock_view.columns["base_salary"] == "column_jkl1234567"

    def test_column_types(self, mock_view):
        assert mock_view.column_types["emp_id"] == "TEXT"
        assert mock_view.column_types["base_salary"] == "NUMERIC"
        assert mock_view.column_types["joining_date"] == "DATE"


class TestResolveColumn:
    """Test View._resolve_column."""

    def test_resolve_display_name(self, mock_view):
        result = mock_view._resolve_column("emp_id")
        assert result == "column_abc1234567"

    def test_resolve_internal_name_passthrough(self, mock_view):
        result = mock_view._resolve_column("column_abc1234567")
        assert result == "column_abc1234567"

    def test_resolve_unknown_raises(self, mock_view):
        with pytest.raises(MammothColumnError, match="not found"):
            mock_view._resolve_column("nonexistent")


class TestResolveColumns:
    """Test View._resolve_columns (multiple)."""

    def test_resolve_multiple(self, mock_view):
        result = mock_view._resolve_columns(["emp_id", "base_salary"])
        assert result == ["column_abc1234567", "column_jkl1234567"]


class TestBuildAsColumn:
    """Test View._build_as_column helper."""

    def test_basic(self, mock_view):
        result = mock_view._build_as_column("New Col", "TEXT")
        assert result["COLUMN"] == "New Col"
        assert result["TYPE"] == "TEXT"
        assert result["INTERNAL_NAME"].startswith("column_")

    def test_type_uppercased(self, mock_view):
        result = mock_view._build_as_column("Col", "numeric")
        assert result["TYPE"] == "NUMERIC"


class TestNextInternalName:
    """Test View._next_internal_name generates unique names."""

    def test_format(self, mock_view):
        name = mock_view._next_internal_name()
        assert name.startswith("column_")
        assert len(name) == 17  # "column_" + 10 chars

    def test_unique(self, mock_view):
        names = {mock_view._next_internal_name() for _ in range(100)}
        assert len(names) == 100


class TestViewMetadata:
    """Test View basic metadata access."""

    def test_id(self, mock_view):
        assert mock_view.id == 1001

    def test_name(self, mock_view):
        assert mock_view.name == "Test View"

    def test_dataset_id(self, mock_view):
        assert mock_view.dataset_id == 500

    def test_repr(self, mock_view):
        r = repr(mock_view)
        assert "1001" in r
        assert "Test View" in r


def test_math_display_name_wins_over_internal_alias(mock_client):
    """A display name that equals another internal id must remain exact."""
    view = View(
        mock_client,
        {
            "id": 1,
            "metadata": [
                {"display_name": "A", "internal_name": "B", "type": "NUMERIC"},
                {"display_name": "B", "internal_name": "column_2", "type": "NUMERIC"},
            ],
        },
        2,
    )
    captured: list[dict] = []
    view._add_task = captured.append  # type: ignore[assignment]

    view.math(
        "B",
        existing_column="B",
        condition=Condition("B", Operator.GTE, 1),
    )

    payload = captured[0]
    assert payload["MATH"]["EXPRESSION"] == [{"TYPE": "COLUMN", "VALUE": "column_2"}]
    assert payload["MATH"]["DESTINATION"] == "column_2"
    assert "column_2" in payload["CONDITION"]
    assert "B" not in payload["CONDITION"]


@pytest.mark.parametrize("internals", [("first", "second", "third"), ("third", "first", "second")])
def test_three_duplicate_display_names_are_never_resolvable(mock_client, internals):
    """Ambiguity remains sticky when a third duplicate is encountered later."""
    view = View(
        mock_client,
        {
            "id": 1,
            "metadata": [
                {"display_name": "Amount", "internal_name": internal, "type": "NUMERIC"}
                for internal in internals
            ],
        },
        2,
    )
    captured: list[dict] = []
    view._add_task = captured.append  # type: ignore[assignment]

    assert "Amount" not in view.columns
    assert "Amount" in view._ambiguous_columns
    with pytest.raises((MammothColumnError, ValueError)):
        view.math(
            "Amount",
            existing_column="Amount",
            condition=Condition("Amount", Operator.GTE, 1),
        )
    assert captured == []
