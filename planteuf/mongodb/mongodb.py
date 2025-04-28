from datetime import datetime
from logging import Logger
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from planteuf.mongodb.collections import Collections
from planteuf.settings import (
    LOGGING_FILENAME,
    LOGGING_LEVEL,
    MONGO_DB,
    MONGO_HOST,
    MONGO_PASSWORD,
    MONGO_PORT,
    MONGO_USERNAME,
)
from planteuf.utils.log import get_logger


class MongoDBClientError(Exception):
    pass


class MongoDBClient:
    logging: Logger
    _client: MongoClient[Any]

    def __init__(self) -> None:
        self.logging = get_logger(name=__name__, level=LOGGING_LEVEL, filename=LOGGING_FILENAME)
        self._client = self._create_client()

    def _create_client(self) -> MongoClient[Any]:
        try:
            if not all([MONGO_USERNAME, MONGO_PASSWORD, MONGO_HOST, MONGO_PORT, MONGO_DB]):
                self.logging.error("Missing MongoDB environment variables")
                raise MongoDBClientError("Missing MongoDB environment variables")
            mongo_uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"
            client: MongoClient[Any] = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")
            self.logging.info("Successfully connected to MongoDB.")
            return client
        except ConnectionFailure:
            self.logging.exception("Failed to connect to MongoDB")
            raise MongoDBClientError("Failed to connect to MongoDB")
        except ValueError:
            self.logging.exception("Configuration error")
            raise MongoDBClientError("Configuration error")
        except Exception:
            self.logging.exception("An unexpected error occurred")
            raise MongoDBClientError("An unexpected error occurred")

    def insert_one(self, collection_name: Collections, document: BaseModel) -> Optional[str]:
        try:
            db = self._client[MONGO_DB]
            collection = db[collection_name.value]
            document_dump = document.model_dump()
            document_dump["created_at"] = datetime.now()
            document_dump["updated_at"] = datetime.now()
            result = collection.insert_one(document_dump)
            self.logging.info("Document inserted", extra={"_id": str(result.inserted_id)})
            return str(result.inserted_id)
        except Exception:
            self.logging.exception("Failed to insert document")
            raise MongoDBClientError("Failed to insert document")

    def insert_many(self, collection_name: Collections, documents: List[BaseModel]) -> Optional[List[str]]:
        try:
            db = self._client[MONGO_DB]
            collection = db[collection_name.value]
            document_dumps = [document.model_dump() for document in documents]
            for document_dump in document_dumps:
                document_dump["created_at"] = datetime.now()
                document_dump["updated_at"] = datetime.now()
            result = collection.insert_many(document_dumps)
            self.logging.info("Documents inserted", extra={"inserted_ids": [str(id) for id in result.inserted_ids]})
            return [str(id) for id in result.inserted_ids]
        except Exception:
            self.logging.exception("Failed to insert documents")
            raise MongoDBClientError("Failed to insert documents")

    def update_one(self, collection_name: Collections, document: BaseModel) -> Optional[str]:
        try:
            db = self._client[MONGO_DB]
            collection = db[collection_name.value]
            document_dump = document.model_dump()
            document_dump["updated_at"] = datetime.now()
            collection.update_one({"_id": document_dump.get("_id")}, {"$set": document_dump})
            self.logging.info("Document updated", extra={"_id": str(document_dump.get("_id"))})
            return document_dump.get("_id")
        except Exception:
            self.logging.exception("Failed to update document")
            raise MongoDBClientError("Failed to update document")

    def update_many(self, collection_name: Collections, documents: List[BaseModel]) -> Optional[List[str]]:
        try:
            db = self._client[MONGO_DB]
            collection = db[collection_name.value]
            results = []
            for document in documents:
                document_dump = document.model_dump()
                document_dump["updated_at"] = datetime.now()
                collection.update_one({"_id": document_dump.get("_id")}, {"$set": document_dump})
                self.logging.info("Document updated", extra={"_id": str(document_dump.get("_id"))})
                results.append(document_dump["_id"])
            return results
        except Exception:
            self.logging.exception("Failed to update documents")
            raise MongoDBClientError("Failed to update documents")

    def insert_or_update_one(self, collection_name: Collections, document: BaseModel) -> Optional[str]:
        try:
            db = self._client[MONGO_DB]
            collection = db[collection_name.value]
            document_dump = document.model_dump()
            if not collection.find_one({"_id": document_dump.get("_id")}):
                document_dump["created_at"] = datetime.now()
            document_dump["updated_at"] = datetime.now()
            result = collection.update_one({"_id": document_dump.get("_id")}, {"$set": document_dump}, upsert=True)
            if result.upserted_id:
                self.logging.info("Document inserted", extra={"_id": str(result.upserted_id)})
                return str(result.upserted_id)
            self.logging.info("Document updated", extra={"_id": str(document_dump.get("_id"))})
            return document_dump.get("_id")
        except Exception:
            self.logging.exception("Failed to insert or update document")
            raise MongoDBClientError("Failed to insert or update document")

    def insert_or_update_many(self, collection_name: Collections, documents: List[BaseModel]) -> Optional[List[str]]:
        try:
            db = self._client[MONGO_DB]
            collection = db[collection_name.value]
            results = []
            for document in documents:
                document_dump = document.model_dump()
                if not collection.find_one({"_id": document_dump.get("_id")}):
                    document_dump["created_at"] = datetime.now()
                document_dump["updated_at"] = datetime.now()
                result = collection.update_one({"_id": document_dump.get("_id")}, {"$set": document_dump}, upsert=True)
                if result.upserted_id:
                    self.logging.info("Document inserted", extra={"_id": str(result.upserted_id)})
                    results.append(str(result.upserted_id))
                else:
                    self.logging.info("Document updated", extra={"_id": str(document_dump.get("_id"))})
                    results.append(document_dump["_id"])
            return results
        except Exception:
            self.logging.exception("Failed to insert or update documents")
            raise MongoDBClientError("Failed to insert or update documents")

    def find_one(
        self,
        collection_name: Collections,
        document_id: str,
        projection: Dict[str, int] = {},
    ) -> Optional[Dict[str, Any]]:
        try:
            db = self._client[MONGO_DB]
            collection = db[collection_name.value]
            document = collection.find_one({"_id": document_id}, projection=projection)
            return document
        except Exception:
            self.logging.exception("Failed to find document")
            raise MongoDBClientError("Failed to find document")

    def find(
        self,
        collection_name: Collections,
        query: Dict[str, Any] = {},
        projection: Dict[str, int] = {},
    ) -> List[Dict[str, Any]]:
        try:
            db = self._client[MONGO_DB]
            collection = db[collection_name.value]
            documents = collection.find(query, projection=projection)
            return list(documents)
        except Exception:
            self.logging.exception("Failed to find documents")
            raise MongoDBClientError("Failed to find documents")
