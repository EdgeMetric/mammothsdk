"""Unit tests for the Users API client."""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pytest

from mammoth.api.users import UsersAPI


def _make_api() -> tuple[UsersAPI, MagicMock]:
    """Create a UsersAPI with a mocked client."""
    mock_client = MagicMock()
    api = UsersAPI(mock_client)
    return api, mock_client


class TestUsersAPIAvatarDelete:
    def test_avatar_delete(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        result = api.avatar_delete()
        mock_client._request_json.assert_called_once_with("DELETE", "/self/avatar")
        assert result == {}


class TestUsersAPIAvatarUpload:
    def test_avatar_upload_path(self, tmp_path):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 10, "status": "processing"}
        avatar_path = tmp_path / "avatar.png"
        avatar_path.write_bytes(b"fake-image-bytes")

        result = api.avatar_upload(avatar_path)

        mock_client._request_json.assert_called_once()
        args, kwargs = mock_client._request_json.call_args
        assert args == ("POST", "/self/avatar")
        files = kwargs["files"]
        assert len(files) == 1
        field_name, (filename, _fileobj, content_type) = files[0]
        assert field_name == "file"
        assert filename == "avatar.png"
        assert content_type == "application/octet-stream"
        assert result == {"id": 10, "status": "processing"}

    def test_avatar_upload_missing_file(self, tmp_path):
        api, _ = _make_api()
        missing_path = tmp_path / "missing.png"
        with pytest.raises(ValueError, match="File not found"):
            api.avatar_upload(missing_path)

    def test_avatar_upload_file_like_object(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"id": 11}
        buf = io.BytesIO(b"fake-bytes")
        buf.name = "custom.jpg"

        api.avatar_upload(buf)

        args, kwargs = mock_client._request_json.call_args
        assert args == ("POST", "/self/avatar")
        field_name, (filename, fileobj, content_type) = kwargs["files"][0]
        assert field_name == "file"
        assert filename == "custom.jpg"
        assert fileobj is buf
        assert content_type == "application/octet-stream"


class TestUsersAPIDeleteAccount:
    def test_delete_account_no_args(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {}
        api.delete_account()
        mock_client._request_json.assert_called_once_with("DELETE", "/self", params=None)

    def test_delete_account_validate_only(self):
        api, mock_client = _make_api()
        mock_client._request_json.return_value = {"valid": True}
        result = api.delete_account(validate_only=True)
        mock_client._request_json.assert_called_once_with(
            "DELETE", "/self", params={"validate_only": True}
        )
        assert result == {"valid": True}
