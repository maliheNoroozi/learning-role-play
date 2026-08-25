from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from api.schemas.roleplay_schemas import RoleplaySession
from api.services.cache.client import (
    RedisLockBusyError,
    RedisService,
    get_redis_service,
)
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

    def __init__(self, redis_service: RedisService | None = None) -> None:
        self._redis = redis_service or get_redis_service()

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
        try:
            with self._redis.lock(
                self._lock_key(roleplay_id),
                timeout=ROLEPLAY_LOCK_TIMEOUT_SECONDS,
                blocking_timeout=ROLEPLAY_LOCK_BLOCKING_TIMEOUT_SECONDS,
            ):
                yield
        except RedisLockBusyError as exc:
            raise RoleplayLockBusyError(roleplay_id) from exc


@lru_cache
def get_roleplay_cache() -> RoleplayCache:
    return RoleplayCache()
