"""Redis-backed store for OAuth clients, auth codes, and access tokens."""

from __future__ import annotations

import json
import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Key prefixes
_CLIENT = "mammoth:client:"
_STATE = "mammoth:state:"
_CODE = "mammoth:code:"
_TOKEN = "mammoth:token:"


class RedisTokenStore:
    """Async Redis store for OAuth artefacts.

    When *encryption_key* is provided (a Fernet key string), credential-bearing
    values (auth codes and access tokens) are encrypted at rest in Redis.
    """

    def __init__(
        self,
        redis_url: str,
        auth_code_ttl: int = 300,
        access_token_ttl: int = 2592000,
        encryption_key: str = "",
    ):
        self._url = redis_url
        self._auth_code_ttl = auth_code_ttl
        self._access_token_ttl = access_token_ttl
        # Create the Redis client eagerly so OAuth handlers can use it
        # before the lifespan context is entered.
        self._redis: aioredis.Redis | None = aioredis.from_url(redis_url, decode_responses=True)
        # Optional Fernet encryption for credential-bearing keys
        if encryption_key:
            from cryptography.fernet import Fernet

            self._cipher: Fernet | None = Fernet(encryption_key.encode())
        else:
            self._cipher = None

    def _encrypt(self, data: str) -> str:
        """Encrypt a string value if an encryption key is configured."""
        if self._cipher:
            return self._cipher.encrypt(data.encode()).decode()
        return data

    def _decrypt(self, data: str) -> str:
        """Decrypt a string value if an encryption key is configured.

        Falls back to returning raw data if decryption fails (e.g. pre-existing
        unencrypted values from before encryption was enabled).
        """
        if self._cipher:
            try:
                return self._cipher.decrypt(data.encode()).decode()
            except Exception:
                # Pre-existing unencrypted data — return as-is
                return data
        return data

    async def connect(self) -> None:
        """Verify connectivity (call during lifespan startup)."""
        assert self._redis is not None
        await self._redis.ping()
        logger.info("Connected to Redis at %s", self._url)

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()

    @property
    def _r(self) -> aioredis.Redis:
        assert self._redis is not None, "RedisTokenStore not connected"
        return self._redis

    # ── Clients (Dynamic Client Registration) ──────────────────

    async def store_client(self, client_id: str, data: dict) -> None:
        await self._r.set(_CLIENT + client_id, json.dumps(data))

    async def get_client(self, client_id: str) -> dict | None:
        raw = await self._r.get(_CLIENT + client_id)
        return json.loads(raw) if raw else None

    # ── Authorization state (PKCE) ─────────────────────────────

    async def store_state(self, state: str, data: dict) -> None:
        await self._r.set(_STATE + state, json.dumps(data), ex=600)  # 10 min

    async def get_state(self, state: str) -> dict | None:
        raw = await self._r.get(_STATE + state)
        return json.loads(raw) if raw else None

    async def delete_state(self, state: str) -> None:
        await self._r.delete(_STATE + state)

    # ── Authorization codes (encrypted — may contain credentials) ──

    async def store_code(self, code: str, data: dict) -> None:
        await self._r.set(_CODE + code, self._encrypt(json.dumps(data)), ex=self._auth_code_ttl)

    async def get_code(self, code: str) -> dict | None:
        raw = await self._r.get(_CODE + code)
        return json.loads(self._decrypt(raw)) if raw else None

    async def delete_code(self, code: str) -> None:
        await self._r.delete(_CODE + code)

    # ── Access tokens (encrypted — contain credentials) ────────

    async def store_token(self, token: str, data: dict) -> None:
        await self._r.set(
            _TOKEN + token, self._encrypt(json.dumps(data))
        )  # No TTL — persists until explicitly revoked

    async def get_token(self, token: str) -> dict | None:
        raw = await self._r.get(_TOKEN + token)
        return json.loads(self._decrypt(raw)) if raw else None

    async def delete_token(self, token: str) -> None:
        await self._r.delete(_TOKEN + token)
