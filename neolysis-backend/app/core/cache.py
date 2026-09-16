import asyncio
import redis.asyncio as redis
from typing import Optional, Any
import json
from app.config import settings
from loguru import logger

class Cache:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._connect_attempted: bool = False

    async def connect(self):
        try:
            # Bounded connect/socket timeouts are essential here: the default
            # REDIS_URL points at the Docker Compose hostname "redis", which
            # fails DNS resolution when running outside Docker and can
            # otherwise stall every cache-touching request for several
            # seconds on some systems while the OS resolver times out.
            self._redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
            )
            await asyncio.wait_for(self._redis.ping(), timeout=1.5)
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None

    async def ensure_connected(self):
        """
        Idempotent, lazy connect: tries once per process lifetime and never retries
        automatically afterwards. Callers that only need best-effort caching (like
        the embedding cache) should use this instead of connect() to avoid a fresh
        connection attempt/ping on every call when Redis is not running.
        """
        if self._connect_attempted:
            return
        self._connect_attempted = True
        await self.connect()

    async def get(self, key: str) -> Optional[Any]:
        if not self._redis:
            return None
        data = await self._redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        if not self._redis:
            return
        await self._redis.set(key, json.dumps(value), ex=ttl)

    async def close(self):
        if self._redis:
            await self._redis.close()

cache = Cache()
