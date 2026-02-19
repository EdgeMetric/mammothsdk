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
    """Async Redis store for OAuth artefacts."""

    def __init__(self, redis_url: str, auth_code_ttl: int = 300, access_token_ttl: int = 2592000):
        self._url = redis_url
        self._auth_code_ttl = auth_code_ttl
        self._access_token_ttl = access_token_ttl
        # Create the Redis client eagerly so OAuth handlers can use it
        # before the lifespan context is entered.
        self._redis: aioredis.Redis | None = aioredis.from_url(
            redis_url, decode_responses=True
        )

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

    # ── Authorization codes ────────────────────────────────────

    async def store_code(self, code: str, data: dict) -> None:
        await self._r.set(_CODE + code, json.dumps(data), ex=self._auth_code_ttl)

    async def get_code(self, code: str) -> dict | None:
        raw = await self._r.get(_CODE + code)
        return json.loads(raw) if raw else None

    async def delete_code(self, code: str) -> None:
        await self._r.delete(_CODE + code)

    # ── Access tokens ──────────────────────────────────────────

    async def store_token(self, token: str, data: dict) -> None:
        await self._r.set(_TOKEN + token, json.dumps(data))  # No TTL — persists until revoked

    async def get_token(self, token: str) -> dict | None:
        raw = await self._r.get(_TOKEN + token)
        return json.loads(raw) if raw else None

    async def delete_token(self, token: str) -> None:
        await self._r.delete(_TOKEN + token)
