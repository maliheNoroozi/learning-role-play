from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from loguru import logger
from redis import Redis
from redis.exceptions import LockError, RedisError

from api.services.cache.config import redis_config


class RedisLockBusyError(RuntimeError):
    """Raised when a Redis lock could not be acquired in time."""


class RedisService:
    def __init__(self, redis_client: Redis | None = None) -> None:
        if redis_client is not None:
            self.redis = redis_client
            return

        self.redis = Redis(
            host=redis_config.redis_host,
            port=redis_config.redis_port,
            db=redis_config.redis_db,
            password=redis_config.redis_password or None,
            decode_responses=True,
        )

    def get(self, key: str) -> str | None:
        try:
            value = self.redis.get(key)
            if value is not None:
                logger.info("Cache hit for key {}", key)
            else:
                logger.info("Cache miss for key {}", key)
            return value
        except RedisError as error:
            logger.error("Redis error retrieving key {}: {}", key, error)
            raise

    def set(self, key: str, value: str, *, ex: int | None = None) -> None:
        try:
            self.redis.set(key, value, ex=ex)
            logger.info("Successfully set cache value for key {}", key)
        except RedisError as error:
            logger.error("Redis error setting key {}: {}", key, error)
            raise

    def delete(self, key: str) -> None:
        try:
            self.redis.delete(key)
            logger.info("Successfully deleted cache value for key {}", key)
        except RedisError as error:
            logger.error("Redis error deleting key {}: {}", key, error)
            raise

    @contextmanager
    def lock(
        self,
        key: str,
        *,
        timeout: float,
        blocking_timeout: float,
    ) -> Iterator[None]:
        """Exclusive lock for one key across all API workers/servers."""
        redis_lock = self.redis.lock(
            name=key,
            timeout=timeout,
            blocking_timeout=blocking_timeout,
            thread_local=False,
        )
        try:
            acquired = redis_lock.acquire(blocking=True)
        except RedisError as error:
            logger.error("Redis error locking key {}: {}", key, error)
            raise

        if not acquired:
            logger.warning("Failed to acquire lock for key {}", key)
            raise RedisLockBusyError(key)

        logger.info("Successfully locked cache key {}", key)
        try:
            yield
        finally:
            try:
                redis_lock.release()
            except LockError:
                # Lock expired or was already released; safe to ignore on exit.
                pass


@lru_cache
def get_redis_service() -> RedisService:
    return RedisService()
