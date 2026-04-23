import redis.asyncio as redis
from typing import Optional, Any
import json
from app.config import settings
from loguru import logger

class Cache:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    async def connect(self):
        try:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self._redis.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None

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
