"""External Keys API client for managing API keys in Mammoth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mammoth.exceptions import MammothValidationError
from mammoth.models.external_keys import ExternalKeyType, ModelConfigSpec

if TYPE_CHECKING:
    from ..client import MammothClient

# Argument validation messages (raised before any API call).
ERR_KEY_NAME_EMPTY = "`key_name` must be a non-empty string."
ERR_SECURE_KEY_TOO_SHORT = "`secure_key` must be at least 3 characters."
ERR_MODEL_SETTINGS_NEEDS_MODEL = "`model_settings` requires `model_id` to be set."

_SECURE_KEY_MIN_LEN = 3


class ExternalKeysAPI:
    """Client for managing external API keys.

    Access via client.external_keys::

        keys = client.external_keys.list()
        key = client.external_keys.create(name="My Key")
        client.external_keys.delete(key_id)
    """

    def __init__(self, client: MammothClient) -> None:
        self._client = client

    def _ws(self) -> int:
        return self._client.workspace_id

    def list(self) -> dict[str, Any]:
        """List all external API keys.

        Returns:
            Dict with API keys list.
        """
        ws = self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/external_keys")

    def get(self, key_id: int) -> dict[str, Any]:
        """Get external key details.

        Args:
            key_id: ID of the API key.

        Returns:
            Dict with key details.
        """
        ws = self._ws()
        return self._client._request_json("GET", f"/workspaces/{ws}/external_keys/{key_id}")

    def create(
        self,
        key_type: ExternalKeyType,
        key_name: str,
        secure_key: str,
        description: str | None = None,
        model_id: str | None = None,
        model_settings: ModelConfigSpec | None = None,
    ) -> dict[str, Any]:
        """Create a new external (LLM provider) API key.

        Args:
            key_type: Provider the key authenticates against.
            key_name: Human-readable name for the key.
            secure_key: The secret key value (>= 3 characters).
            description: Optional description of the key's purpose.
            model_id: Optional specific model to use (defaults to the
                provider's recommended model server-side).
            model_settings: Optional per-key model configuration overrides;
                requires *model_id* to be set.

        Returns:
            Dict with created key info.

        Raises:
            MammothValidationError: If *key_name* is empty, *secure_key* is too
                short, or *model_settings* is given without *model_id*.

        Example::

            client.external_keys.create(
                key_type=ExternalKeyType.ANTHROPIC,
                key_name="My Claude key",
                secure_key="sk-ant-...",
            )
        """
        if not key_name:
            raise MammothValidationError(ERR_KEY_NAME_EMPTY)
        if len(secure_key) < _SECURE_KEY_MIN_LEN:
            raise MammothValidationError(ERR_SECURE_KEY_TOO_SHORT)
        if model_settings is not None and not model_id:
            raise MammothValidationError(ERR_MODEL_SETTINGS_NEEDS_MODEL)

        body: dict[str, Any] = {
            "key_type": key_type.value,
            "key_name": key_name,
            "secure_key": secure_key,
        }
        if description is not None:
            body["description"] = description
        if model_id is not None:
            body["model_id"] = model_id
        if model_settings is not None:
            # Backend reads the aliased wire key "model_config".
            body["model_config"] = model_settings.model_dump(exclude_none=True)

        ws = self._ws()
        return self._client._request_json("POST", f"/workspaces/{ws}/external_keys", json=body)

    def delete(self, key_id: int) -> dict[str, Any]:
        """Delete an external API key.

        Args:
            key_id: ID of the key to delete.

        Returns:
            Dict with deletion result.
        """
        ws = self._ws()
        return self._client._request_json("DELETE", f"/workspaces/{ws}/external_keys/{key_id}")
