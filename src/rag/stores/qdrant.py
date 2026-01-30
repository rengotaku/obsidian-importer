"""
Qdrant Document Store - ベクトルストアのファクトリと管理機能
"""
from __future__ import annotations

from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from src.rag.config import QDRANT_PATH, RAGConfig, rag_config

# =============================================================================
# Constants
# =============================================================================

COLLECTION_NAME = "obsidian_knowledge"


# =============================================================================
# Factory Functions
# =============================================================================


def get_document_store(config: RAGConfig | None = None) -> QdrantDocumentStore:
    """
    Create or get Qdrant document store with local file persistence.

    Uses qdrant-haystack integration with local storage path.

    Args:
        config: RAG configuration. Uses default if None.

    Returns:
        QdrantDocumentStore instance configured for local persistence.

    Note:
        - Collection name: "obsidian_knowledge"
        - Vector dimension: 1024 (bge-m3)
        - Distance metric: Cosine
        - Persistence path: data/qdrant/
    """
    if config is None:
        config = rag_config

    # Ensure data directory exists
    QDRANT_PATH.mkdir(parents=True, exist_ok=True)

    store = QdrantDocumentStore(
        path=str(QDRANT_PATH),
        index=COLLECTION_NAME,
        embedding_dim=config.embedding_dim,
        similarity="cosine",
        recreate_index=False,
        return_embedding=False,
    )

    return store


# =============================================================================
# Collection Management
# =============================================================================


def get_collection_stats(store: QdrantDocumentStore) -> dict:
    """
    Get collection statistics from Qdrant store.

    Args:
        store: QdrantDocumentStore instance.

    Returns:
        Dictionary containing:
        - document_count: Number of documents in collection
        - collection_name: Name of the collection
        - embedding_dim: Vector dimension
        - similarity: Distance metric

    Note:
        Uses store.count_documents() for document count.
    """
    document_count = store.count_documents()

    return {
        "document_count": document_count,
        "collection_name": COLLECTION_NAME,
        "embedding_dim": store.embedding_dim,
        "similarity": store.similarity,
    }
