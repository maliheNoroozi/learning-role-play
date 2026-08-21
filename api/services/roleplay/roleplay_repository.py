from __future__ import annotations

from functools import lru_cache
from typing import Any

from api.schemas.roleplay_schemas import RoleplaySession
from api.services.database.client import MongoDBService, get_mongodb_service

ROLEPLAY_SESSIONS_COLLECTION = "roleplay_sessions"


class RoleplaySessionNotFoundError(LookupError):
    """Raised when a roleplay session is missing from the database."""


class RoleplayRepository:
    """MongoDB-backed store for durable roleplay session state."""

    def __init__(self, mongodb_service: MongoDBService | None = None) -> None:
        self._db = mongodb_service or get_mongodb_service()
        self._db.get_collection(ROLEPLAY_SESSIONS_COLLECTION).create_index(
            "roleplay_id",
            unique=True,
        )

    def save_session(self, session: RoleplaySession) -> None:
        self._db.update_one(
            ROLEPLAY_SESSIONS_COLLECTION,
            {"roleplay_id": session.roleplay_id},
            {"$set": session.model_dump()},
            upsert=True,
        )

    def get_session(self, roleplay_id: str) -> RoleplaySession:
        document = self._db.find_one(
            ROLEPLAY_SESSIONS_COLLECTION,
            {"roleplay_id": roleplay_id},
        )
        if document is None:
            raise RoleplaySessionNotFoundError(roleplay_id)
        return self._to_session(document)

    def delete_session(self, roleplay_id: str) -> None:
        result = self._db.delete_one(
            ROLEPLAY_SESSIONS_COLLECTION,
            {"roleplay_id": roleplay_id},
        )
        if result.deleted_count == 0:
            raise RoleplaySessionNotFoundError(roleplay_id)

    def list_sessions(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RoleplaySession]:
        documents = self._db.find_many(
            ROLEPLAY_SESSIONS_COLLECTION,
            {},
            skip=skip,
            limit=limit,
        )
        return [self._to_session(document) for document in documents]

    @staticmethod
    def _to_session(document: dict[str, Any]) -> RoleplaySession:
        payload = dict(document)
        payload.pop("_id", None)
        return RoleplaySession.model_validate(payload)


@lru_cache
def get_roleplay_repository() -> RoleplayRepository:
    return RoleplayRepository()
