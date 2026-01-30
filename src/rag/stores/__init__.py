"""
RAG Stores - Qdrant Document Store
"""
from src.rag.stores.qdrant import (
    COLLECTION_NAME,
    get_collection_stats,
    get_document_store,
)

__all__ = [
    "COLLECTION_NAME",
    "get_document_store",
    "get_collection_stats",
]
