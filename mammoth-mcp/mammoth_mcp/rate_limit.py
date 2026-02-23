"""Redis-based sliding window rate limiter middleware."""

from __future__ import annotations

import time

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-user rate limiter using Redis sliding window counters.

    Keys by bearer token (authenticated requests) or client IP (pre-auth).
    Returns 429 Too Many Requests with Retry-After header when exceeded.
    """

    def __init__(self, app, *, redis_url: str, rpm: int = 60, burst: int = 10) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._redis: aioredis.Redis = aioredis.from_url(redis_url, decode_responses=True)
        self._rpm = rpm
        self._limit = rpm + burst
        self._prefix = "mammoth:ratelimit:"

    def _extract_key(self, request: Request) -> str:
        """Extract rate limit key from bearer token or client IP."""
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer ") and len(auth) > 7:
            return auth[7:][:16]  # First 16 chars of token for key
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        # Skip rate limiting for health checks and OPTIONS
        if request.url.path == "/health" or request.method == "OPTIONS":
            return await call_next(request)

        identity = self._extract_key(request)
        minute_bucket = int(time.time()) // 60
        key = f"{self._prefix}{identity}:{minute_bucket}"

        try:
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, 120)  # 2 min TTL for cleanup

            if count > self._limit:
                retry_after = 60 - (int(time.time()) % 60)
                return JSONResponse(
                    {"error": "Too Many Requests", "retry_after": retry_after},
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                )
        except aioredis.RedisError:
            pass  # Fail open — don't block requests if Redis is down

        return await call_next(request)
