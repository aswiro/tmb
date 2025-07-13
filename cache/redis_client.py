import json
from typing import Any

import redis.asyncio as redis
from config.settings import settings


class RedisClient:
    def __init__(self):
        self.redis: redis.Redis | None = None

    async def connect(self):
        """Connect to Redis"""
        conn_kwargs = {
            "host": settings.redis_host,
            "port": settings.redis_port,
            "db": settings.redis_db,
            "encoding": "utf-8",
            "decode_responses": True,
            "health_check_interval": 30,
        }

        self.redis = redis.Redis(**conn_kwargs)
        # Test connection
        await self.redis.ping()

    async def close(self, **kwargs):  # noqa: ARG002
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Any | None:
        """Get value from Redis"""
        if not self.redis:
            return None

        value = await self.redis.get(key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in Redis"""
        if not self.redis:
            return False

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        return await self.redis.set(key, value, ex=ttl)

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.redis:
            return False

        return bool(await self.redis.delete(key))

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.redis:
            return False

        return bool(await self.redis.exists(key))

    async def get_keys(self, pattern: str) -> list[str]:
        """Get keys matching pattern"""
        if not self.redis:
            return []

        return await self.redis.keys(pattern)

    async def flush_db(self):
        """Flush current Redis database"""
        if self.redis:
            await self.redis.flushdb()


# Global Redis client instance
redis_client = RedisClient()
