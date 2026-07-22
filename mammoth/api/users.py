"""Users API client for self-service account operations in Mammoth."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    from ..client import MammothClient


class UsersAPI:
    """Client for self-service user account operations.

    Access via ``client.users``::

        client.users.avatar_upload("avatar.png")
        client.users.avatar_delete()
        client.users.delete_account(validate_only=True)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def avatar_delete(self) -> dict[str, Any]:
        """Delete the current user's profile picture.

        Returns:
            Dict with the deletion result.
        """
        return self._client._request_json("DELETE", "/self/avatar")

    def avatar_upload(self, file: str | Path | BinaryIO) -> dict[str, Any]:
        """Upload a profile picture for the current user.

        Args:
            file: Path to an image file, or an open binary file-like object.

        Returns:
            Dict with the async job info for the avatar-processing job.

        Raises:
            ValueError: If *file* is a path that does not exist.
        """
        opened_file: Any = None
        try:
            if isinstance(file, (str, Path)):
                file_path = Path(file)
                if not file_path.exists():
                    raise ValueError(f"File not found: {file_path}")
                opened_file = open(file_path, "rb")  # noqa: SIM115
                file_data = [("file", (file_path.name, opened_file, "application/octet-stream"))]
            else:
                filename = getattr(file, "name", "avatar")
                if hasattr(filename, "split"):
                    filename = os.path.basename(filename)
                file_data = [("file", (filename, file, "application/octet-stream"))]

            return self._client._request_json("POST", "/self/avatar", files=file_data)
        finally:
            if opened_file is not None:
                opened_file.close()

    def delete_account(self, validate_only: bool | None = None) -> dict[str, Any]:
        """Delete the current user's account.

        Args:
            validate_only: If ``True``, only validate that the account can be
                deleted without actually deleting it.

        Returns:
            Dict with the deletion (or validation) result.
        """
        params: dict[str, Any] = {}
        if validate_only is not None:
            params["validate_only"] = validate_only
        return self._client._request_json("DELETE", "/self", params=params or None)
