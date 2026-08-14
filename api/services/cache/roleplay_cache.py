from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from redis import Redis
from redis.exceptions import LockError

from api.schemas.roleplay_schemas import RoleplaySession
from api.services.cache.config import redis_config
from api.services.config import (
    ROLEPLAY_LOCK_BLOCKING_TIMEOUT_SECONDS,
    ROLEPLAY_LOCK_TIMEOUT_SECONDS,
    ROLEPLAY_SESSION_TTL_SECONDS,
)


class RoleplayNotFoundError(LookupError):
    """Raised when a roleplay session is missing from the cache."""


class RoleplayLockBusyError(RuntimeError):
    """Raised when another worker holds the roleplay lock."""


class RoleplayCache:
    """Redis-backed store for live roleplay session state."""

    def __init__(self, redis_client: Redis | None = None) -> None:
        if redis_client is not None:
            self._redis = redis_client
            return

        self._redis = Redis(
            host=redis_config.redis_host,
            port=redis_config.redis_port,
            db=redis_config.redis_db,
            password=redis_config.redis_password or None,
            decode_responses=True,
        )

    @staticmethod
    def _session_key(roleplay_id: str) -> str:
        return f"roleplay:{roleplay_id}"

    @staticmethod
    def _lock_key(roleplay_id: str) -> str:
        return f"roleplay:{roleplay_id}:lock"

    def save_session(self, session: RoleplaySession) -> None:
        self._redis.set(
            self._session_key(session.roleplay_id),
            session.model_dump_json(),
            ex=ROLEPLAY_SESSION_TTL_SECONDS,
        )

    def get_session(self, roleplay_id: str) -> RoleplaySession:
        raw = self._redis.get(self._session_key(roleplay_id))
        if raw is None:
            raise RoleplayNotFoundError(roleplay_id)
        return RoleplaySession.model_validate_json(raw)

    def delete_session(self, roleplay_id: str) -> None:
        self._redis.delete(self._session_key(roleplay_id))

    @contextmanager
    def lock(self, roleplay_id: str) -> Iterator[None]:
        """Exclusive lock for one roleplayId across all API workers/servers."""
        lock = self._redis.lock(
            name=self._lock_key(roleplay_id),
            timeout=ROLEPLAY_LOCK_TIMEOUT_SECONDS,
            blocking_timeout=ROLEPLAY_LOCK_BLOCKING_TIMEOUT_SECONDS,
            thread_local=False,
        )
        acquired = lock.acquire(blocking=True)
        if not acquired:
            raise RoleplayLockBusyError(roleplay_id)
        try:
            yield
        finally:
            try:
                lock.release()
            except LockError:
                # Lock expired or was already released; safe to ignore on exit.
                pass


@lru_cache
def get_roleplay_cache() -> RoleplayCache:
    return RoleplayCache()
