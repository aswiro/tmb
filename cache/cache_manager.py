from typing import Any

from config.settings import settings

from cache.redis_client import redis_client


class CacheManager:
    """Cache manager for application data"""

    @staticmethod
    def _get_user_key(user_id: int) -> str:
        return f"user:{user_id}"

    @staticmethod
    def _get_group_key(group_id: int) -> str:
        return f"group:{group_id}"

    @staticmethod
    def _get_filter_rules_key(group_id: int) -> str:
        return f"filter_rules:{group_id}"

    @staticmethod
    def _get_captcha_settings_key(group_id: int) -> str:
        return f"captcha_settings:{group_id}"

    @staticmethod
    def _get_captcha_session_key(user_id: int, group_id: int) -> str:
        return f"captcha_session:{user_id}:{group_id}"

    @staticmethod
    def _get_user_group_status_key(user_id: int, group_id: int) -> str:
        return f"user_group_status:{user_id}:{group_id}"

    # User caching
    async def get_user(self, user_id: int) -> dict[str, Any] | None:
        """Get user data from cache"""
        key = self._get_user_key(user_id)
        return await redis_client.get(key)

    async def set_user(
        self, user_id: int, user_data: dict[str, Any], ttl: int | None = None
    ) -> bool:
        """Set user data in cache"""
        key = self._get_user_key(user_id)
        cache_ttl = ttl or settings.user_cache_ttl
        return await redis_client.set(key, user_data, cache_ttl)

    async def delete_user(self, user_id: int) -> bool:
        """Delete user data from cache"""
        key = self._get_user_key(user_id)
        return await redis_client.delete(key)

    # Group caching
    async def get_group(self, group_id: int) -> dict[str, Any] | None:
        """Get group data from cache"""
        key = self._get_group_key(group_id)
        return await redis_client.get(key)

    async def set_group(
        self, group_id: int, group_data: dict[str, Any], ttl: int | None = None
    ) -> bool:
        """Set group data in cache"""
        key = self._get_group_key(group_id)
        cache_ttl = ttl or settings.cache_ttl
        return await redis_client.set(key, group_data, cache_ttl)

    async def delete_group(self, group_id: int) -> bool:
        """Delete group data from cache"""
        key = self._get_group_key(group_id)
        return await redis_client.delete(key)

    # Filter rules caching
    async def get_filter_rules(self, group_id: int) -> list[dict[str, Any]] | None:
        """Get filter rules for group from cache"""
        key = self._get_filter_rules_key(group_id)
        return await redis_client.get(key)

    async def set_filter_rules(
        self, group_id: int, rules: list[dict[str, Any]], ttl: int | None = None
    ) -> bool:
        """Set filter rules for group in cache"""
        key = self._get_filter_rules_key(group_id)
        cache_ttl = ttl or settings.cache_ttl
        return await redis_client.set(key, rules, cache_ttl)

    async def delete_filter_rules(self, group_id: int) -> bool:
        """Delete filter rules from cache"""
        key = self._get_filter_rules_key(group_id)
        return await redis_client.delete(key)

    # CAPTCHA settings caching
    async def get_captcha_settings(self, group_id: int) -> dict[str, Any] | None:
        """Get CAPTCHA settings for group from cache"""
        key = self._get_captcha_settings_key(group_id)
        return await redis_client.get(key)

    async def set_captcha_settings(
        self, group_id: int, settings_data: dict[str, Any], ttl: int | None = None
    ) -> bool:
        """Set CAPTCHA settings for group in cache"""
        key = self._get_captcha_settings_key(group_id)
        cache_ttl = ttl or settings.cache_ttl
        return await redis_client.set(key, settings_data, cache_ttl)

    async def delete_captcha_settings(self, group_id: int) -> bool:
        """Delete CAPTCHA settings from cache"""
        key = self._get_captcha_settings_key(group_id)
        return await redis_client.delete(key)

    # CAPTCHA session caching
    async def get_captcha_session(
        self, user_id: int, group_id: int
    ) -> dict[str, Any] | None:
        """Get CAPTCHA session from cache"""
        key = self._get_captcha_session_key(user_id, group_id)
        return await redis_client.get(key)

    async def set_captcha_session(
        self, user_id: int, group_id: int, session_data: dict[str, Any], ttl: int
    ) -> bool:
        """Set CAPTCHA session in cache"""
        key = self._get_captcha_session_key(user_id, group_id)
        return await redis_client.set(key, session_data, ttl)

    async def delete_captcha_session(self, user_id: int, group_id: int) -> bool:
        """Delete CAPTCHA session from cache"""
        key = self._get_captcha_session_key(user_id, group_id)
        return await redis_client.delete(key)

    # User group status caching
    async def get_user_group_status(self, user_id: int, group_id: int) -> str | None:
        """Get user status in group from cache"""
        key = self._get_user_group_status_key(user_id, group_id)
        return await redis_client.get(key)

    async def set_user_group_status(
        self, user_id: int, group_id: int, status: str, ttl: int | None = None
    ) -> bool:
        """Set user status in group in cache"""
        key = self._get_user_group_status_key(user_id, group_id)
        cache_ttl = ttl or settings.user_cache_ttl
        return await redis_client.set(key, status, cache_ttl)

    async def delete_user_group_status(self, user_id: int, group_id: int) -> bool:
        """Delete user status in group from cache"""
        key = self._get_user_group_status_key(user_id, group_id)
        return await redis_client.delete(key)

    # Utility methods
    async def clear_user_cache(self, user_id: int) -> int:
        """Clear all cache entries for a user"""
        pattern = f"*{user_id}*"
        keys = await redis_client.get_keys(pattern)
        if keys:
            deleted = 0
            for key in keys:
                if await redis_client.delete(key):
                    deleted += 1
            return deleted
        return 0

    async def clear_group_cache(self, group_id: int) -> int:
        """Clear all cache entries for a group"""
        patterns = [
            f"group:{group_id}",
            f"filter_rules:{group_id}",
            f"captcha_settings:{group_id}",
            f"*:{group_id}",
        ]

        deleted = 0
        for pattern in patterns:
            keys = await redis_client.get_keys(pattern)
            for key in keys:
                if await redis_client.delete(key):
                    deleted += 1
        return deleted


# Global cache manager instance
cache_manager = CacheManager()
