from __future__ import annotations

import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_KEY_PREFIX = "links"


class LinkCache:
    def __init__(self, url: str, ttl_seconds: int) -> None:
        self._url = url
        self._ttl = ttl_seconds
        self._redis: aioredis.Redis | None = None

    async def start(self) -> None:
        self._redis = aioredis.Redis.from_url(self._url, decode_responses=True)

    async def stop(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def get(self, chat_id: int) -> str | None:
        if self._redis is None:
            return None
        try:
            return await self._redis.get(f"{_KEY_PREFIX}:{chat_id}")
        except Exception as exc:
            logger.warning("cache_get_failed", extra={"error": str(exc)})
            return None

    async def set(self, chat_id: int, value: str) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.set(f"{_KEY_PREFIX}:{chat_id}", value, ex=self._ttl)
        except Exception as exc:
            logger.warning("cache_set_failed", extra={"error": str(exc)})

    async def invalidate(self, chat_id: int) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.delete(f"{_KEY_PREFIX}:{chat_id}")
        except Exception as exc:
            logger.warning("cache_invalidate_failed", extra={"error": str(exc)})
