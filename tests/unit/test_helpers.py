"""Unit tests for helper utilities."""

from __future__ import annotations

from mammoth.helpers import parse_path


class TestParsePath:
    def test_simple_path(self):
        result = parse_path("/workspaces/1/projects/2")
        assert result == {"workspace_id": 1, "project_id": 2}

    def test_single_resource(self):
        result = parse_path("/workspaces/42")
        assert result == {"workspace_id": 42}

    def test_empty_path(self):
        result = parse_path("/")
        assert result == {}

    def test_deep_path(self):
        result = parse_path("/workspaces/1/projects/2/views/4")
        assert result["workspace_id"] == 1
        assert result["project_id"] == 2
        assert result["dataview_id"] == 4

    def test_full_url(self):
        result = parse_path("https://app.mammoth.io/#/workspaces/11/projects/98/views/1039")
        assert result["workspace_id"] == 11
        assert result["project_id"] == 98
        assert result["dataview_id"] == 1039
