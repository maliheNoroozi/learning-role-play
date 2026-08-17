from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from loguru import logger

from api.schemas.roleplay_schemas import RoleplaySession
from api.services.roleplay.roleplay_cache import (
    RoleplayCache,
    RoleplayLockBusyError,
    RoleplayNotFoundError,
    get_roleplay_cache,
)
from api.services.roleplay.roleplay_repository import (
    RoleplayRepository,
    RoleplaySessionNotFoundError,
    get_roleplay_repository,
)


class RoleplayStore:
    """Unified session access: Redis cache-aside + Mongo write-through.

    - Reads check cache first, then Mongo, then warm the cache.
    - Writes persist to Mongo first (durable), then refresh Redis (hot path).
    - Locks are Redis-only so concurrent chat turns stay serialized.
    """

    def __init__(
        self,
        cache: RoleplayCache | None = None,
        repository: RoleplayRepository | None = None,
    ) -> None:
        self._cache = cache or get_roleplay_cache()
        self._repository = repository or get_roleplay_repository()

    def get_session(self, roleplay_id: str) -> RoleplaySession:
        try:
            return self._cache.get_session(roleplay_id)
        except RoleplayNotFoundError:
            logger.info(
                "Roleplay {} missing from cache; loading from database",
                roleplay_id,
            )

        try:
            session = self._repository.get_session(roleplay_id)
        except RoleplaySessionNotFoundError as exc:
            raise RoleplayNotFoundError(roleplay_id) from exc

        self._cache.save_session(session)
        return session

    def save_session(self, session: RoleplaySession) -> None:
        self._repository.save_session(session)
        self._cache.save_session(session)

    def delete_session(self, roleplay_id: str) -> None:
        self._cache.delete_session(roleplay_id)
        try:
            self._repository.delete_session(roleplay_id)
        except RoleplaySessionNotFoundError as exc:
            raise RoleplayNotFoundError(roleplay_id) from exc

    def list_sessions(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RoleplaySession]:
        return self._repository.list_sessions(skip=skip, limit=limit)

    @contextmanager
    def lock(self, roleplay_id: str) -> Iterator[None]:
        """Exclusive lock for one roleplay across API workers (Redis)."""
        with self._cache.lock(roleplay_id):
            yield


@lru_cache
def get_roleplay_store() -> RoleplayStore:
    return RoleplayStore()


__all__ = [
    "RoleplayLockBusyError",
    "RoleplayNotFoundError",
    "RoleplayStore",
    "get_roleplay_store",
]
