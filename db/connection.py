from pymongo import MongoClient
from config.settings import MONGODB_URI, MONGODB_DB_NAME

_client = None


def get_client() -> MongoClient:
    """Return a singleton MongoClient."""
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
    return _client


def get_db():
    """Return the HR onboarding database."""
    return get_client()[MONGODB_DB_NAME]


def get_candidates_collection():
    """Return the candidates collection."""
    return get_db()["candidates"]
