from __future__ import annotations

from functools import lru_cache
from typing import Any
from urllib.parse import quote_plus

from loguru import logger
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from api.services.database.config import mongodb_config


def _build_mongo_uri() -> str:
    host = mongodb_config.mongodb_host
    port = mongodb_config.mongodb_port
    if mongodb_config.mongodb_user and mongodb_config.mongodb_password:
        user = quote_plus(mongodb_config.mongodb_user)
        password = quote_plus(mongodb_config.mongodb_password)
        return f"mongodb://{user}:{password}@{host}:{port}"
    return f"mongodb://{host}:{port}"


class MongoDBService:
    def __init__(self, client: MongoClient | None = None) -> None:
        self.client = client or MongoClient(_build_mongo_uri())
        try:
            self.client.admin.command("ping")
        except PyMongoError as error:
            logger.error("Error connecting to MongoDB: {}", error)
            raise
        self.database = self.client[mongodb_config.mongodb_db]

    def get_collection(self, name: str):
        return self.database[name]

    def insert_one(self, collection: str, document: dict[str, Any]):
        try:
            result = self.get_collection(collection).insert_one(document)
            logger.info(
                "Successfully inserted one document into collection {}", collection
            )
            return result
        except PyMongoError as error:
            logger.error(
                "Error inserting one document into collection {}: {}",
                collection,
                error,
            )
            raise

    def insert_many(self, collection: str, documents: list[dict[str, Any]]):
        try:
            result = self.get_collection(collection).insert_many(documents)
            logger.info(
                "Successfully inserted {} documents into collection {}",
                len(result.inserted_ids),
                collection,
            )
            return result
        except PyMongoError as error:
            logger.error(
                "Error inserting many documents into collection {}: {}",
                collection,
                error,
            )
            raise

    def find_one(self, collection: str, query: dict[str, Any]):
        try:
            return self.get_collection(collection).find_one(query)
        except PyMongoError as error:
            logger.error(
                "Error finding one document in collection {}: {}", collection, error
            )
            raise

    def find_many(
        self,
        collection: str,
        query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        try:
            cursor = self.get_collection(collection).find(query).skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)
            return list(cursor)
        except PyMongoError as error:
            logger.error(
                "Error finding many documents in collection {}: {}", collection, error
            )
            raise

    def update_one(
        self,
        collection: str,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
    ):
        try:
            result = self.get_collection(collection).update_one(
                query, update, upsert=upsert
            )
            logger.info(
                "Successfully updated one document in collection {} "
                "(matched {}, modified {}, upserted_id {})",
                collection,
                result.matched_count,
                result.modified_count,
                result.upserted_id,
            )
            return result
        except PyMongoError as error:
            logger.error(
                "Error updating one document in collection {}: {}", collection, error
            )
            raise

    def update_many(
        self,
        collection: str,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
    ):
        try:
            result = self.get_collection(collection).update_many(
                query, update, upsert=upsert
            )
            logger.info(
                "Successfully updated documents in collection {} "
                "(matched {}, modified {})",
                collection,
                result.matched_count,
                result.modified_count,
            )
            return result
        except PyMongoError as error:
            logger.error(
                "Error updating many documents in collection {}: {}", collection, error
            )
            raise

    def delete_one(self, collection: str, query: dict[str, Any]):
        try:
            result = self.get_collection(collection).delete_one(query)
            logger.info(
                "Successfully deleted one document from collection {} (deleted {})",
                collection,
                result.deleted_count,
            )
            return result
        except PyMongoError as error:
            logger.error(
                "Error deleting one document in collection {}: {}", collection, error
            )
            raise

    def delete_many(self, collection: str, query: dict[str, Any]):
        try:
            result = self.get_collection(collection).delete_many(query)
            logger.info(
                "Successfully deleted documents from collection {} (deleted {})",
                collection,
                result.deleted_count,
            )
            return result
        except PyMongoError as error:
            logger.error(
                "Error deleting many documents in collection {}: {}", collection, error
            )
            raise


@lru_cache
def get_mongodb_service() -> MongoDBService:
    return MongoDBService()
