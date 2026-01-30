"""
RAG Pipelines - Indexing & Query Pipelines
"""
from src.rag.pipelines.indexing import (
    Document,
    DocumentMeta,
    IndexingResult,
    chunk_document,
    chunk_documents,
    create_indexing_pipeline,
    index_all_vaults,
    index_vault,
    parse_frontmatter,
    scan_vault,
)
from src.rag.pipelines.query import (
    Answer,
    QueryFilters,
    SearchResponse,
    SearchResult,
    ask,
    build_qdrant_filters,
    create_qa_pipeline,
    create_search_pipeline,
    search,
)

__all__ = [
    # Indexing
    "Document",
    "DocumentMeta",
    "IndexingResult",
    "chunk_document",
    "chunk_documents",
    "create_indexing_pipeline",
    "index_all_vaults",
    "index_vault",
    "parse_frontmatter",
    "scan_vault",
    # Query
    "Answer",
    "QueryFilters",
    "SearchResponse",
    "SearchResult",
    "ask",
    "build_qdrant_filters",
    "create_qa_pipeline",
    "create_search_pipeline",
    "search",
]
