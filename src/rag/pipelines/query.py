"""
Query Pipeline - Semantic search and Q&A functionality
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack_integrations.components.embedders.ollama import OllamaTextEmbedder
from haystack_integrations.components.generators.ollama import OllamaGenerator
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from src.rag.config import OllamaConfig, ollama_config
from src.rag.exceptions import QueryError

if TYPE_CHECKING:
    from haystack import Document as HaystackDocument


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class QueryFilters:
    """Filters for search queries"""

    vaults: list[str] | None = None  # Filter by vault names
    tags: list[str] | None = None  # Filter by tags (AND)
    date_from: date | None = None  # Filter by created date (>=)
    date_to: date | None = None  # Filter by created date (<=)


@dataclass
class SearchResult:
    """Single search result"""

    content: str  # Matched chunk content
    score: float  # Similarity score 0.0-1.0
    file_path: str  # Source file path
    title: str  # Document title
    vault: str  # Vault name
    position: int  # Chunk position in document


@dataclass
class SearchResponse:
    """Response from search query"""

    query: str
    results: list[SearchResult]
    total: int


@dataclass
class Answer:
    """Answer from Q&A query"""

    text: str  # Generated answer
    sources: list[SearchResult]  # Referenced chunks
    confidence: float  # 0.0-1.0


# =============================================================================
# Q&A Prompt Template
# =============================================================================

QA_PROMPT_TEMPLATE = """以下のコンテキストを参考にして、質問に回答してください。

コンテキスト:
{% for doc in documents %}
---
出典: {{ doc.meta.title }} ({{ doc.meta.vault }})
{{ doc.content }}
{% endfor %}
---

質問: {{ query }}

回答の際は以下のルールに従ってください:
1. コンテキストに基づいて回答してください
2. コンテキストに情報がない場合は「情報が見つかりませんでした」と回答してください
3. 回答の根拠となる出典を明記してください
4. 日本語で回答してください

回答:"""


# =============================================================================
# Filter Building
# =============================================================================


def build_qdrant_filters(filters: QueryFilters | None) -> dict[str, Any] | None:
    """
    Build Qdrant filter dict from QueryFilters.

    Args:
        filters: Query filters to convert.

    Returns:
        Qdrant filter dict or None if no filters.
    """
    if filters is None:
        return None

    conditions: list[dict[str, Any]] = []

    # Vault filter
    if filters.vaults:
        if len(filters.vaults) == 1:
            conditions.append({
                "field": "meta.vault",
                "operator": "==",
                "value": filters.vaults[0],
            })
        else:
            conditions.append({
                "field": "meta.vault",
                "operator": "in",
                "value": filters.vaults,
            })

    # Tags filter (AND - all tags must match)
    if filters.tags:
        for tag in filters.tags:
            conditions.append({
                "field": "meta.tags",
                "operator": "contains",
                "value": tag,
            })

    # Date from filter
    if filters.date_from:
        conditions.append({
            "field": "meta.created",
            "operator": ">=",
            "value": filters.date_from.isoformat(),
        })

    # Date to filter
    if filters.date_to:
        conditions.append({
            "field": "meta.created",
            "operator": "<=",
            "value": filters.date_to.isoformat(),
        })

    if not conditions:
        return None

    if len(conditions) == 1:
        return conditions[0]

    return {"operator": "AND", "conditions": conditions}


# =============================================================================
# Search Pipeline
# =============================================================================


def create_search_pipeline(
    store: QdrantDocumentStore, config: OllamaConfig | None = None
) -> Pipeline:
    """
    Create Haystack search pipeline with embedding retrieval.

    Pipeline components:
    1. OllamaTextEmbedder - Embed the query text
    2. QdrantEmbeddingRetriever - Retrieve similar documents

    Args:
        store: QdrantDocumentStore instance.
        config: Ollama configuration for embedding server.

    Returns:
        Configured Haystack Pipeline for search.
    """
    if config is None:
        config = ollama_config

    pipeline = Pipeline()

    # Query embedder
    embedder = OllamaTextEmbedder(
        url=config.remote_url,
        model=config.embedding_model,
        timeout=config.embedding_timeout,
    )

    # Retriever
    retriever = QdrantEmbeddingRetriever(document_store=store)

    # Add components
    pipeline.add_component("embedder", embedder)
    pipeline.add_component("retriever", retriever)

    # Connect components
    pipeline.connect("embedder.embedding", "retriever.query_embedding")

    return pipeline


# =============================================================================
# Search Function
# =============================================================================


def _convert_to_search_result(doc: "HaystackDocument", score: float) -> SearchResult:
    """Convert Haystack Document to SearchResult."""
    meta = doc.meta or {}
    return SearchResult(
        content=doc.content or "",
        score=score,
        file_path=meta.get("file_path", ""),
        title=meta.get("title", ""),
        vault=meta.get("vault", ""),
        position=meta.get("position", 0),
    )


def search(
    pipeline: Pipeline,
    query: str,
    filters: QueryFilters | None = None,
    top_k: int = 5,
) -> SearchResponse:
    """
    Execute semantic search query.

    Args:
        pipeline: Configured search pipeline from create_search_pipeline().
        query: Search query text.
        filters: Optional filters for vault, tags, date range.
        top_k: Number of results to return (default: 5).

    Returns:
        SearchResponse with results.

    Raises:
        QueryError: If search fails.
    """
    if not query or not query.strip():
        raise QueryError("Empty query provided", query=query, stage="validation")

    try:
        # Build Qdrant filters
        qdrant_filters = build_qdrant_filters(filters)

        # Run pipeline
        result = pipeline.run({
            "embedder": {"text": query},
            "retriever": {"top_k": top_k, "filters": qdrant_filters},
        })

        # Extract documents from result
        documents = result.get("retriever", {}).get("documents", [])

        # Convert to SearchResults
        search_results: list[SearchResult] = []
        for doc in documents:
            score = doc.score if hasattr(doc, "score") and doc.score is not None else 0.0
            search_results.append(_convert_to_search_result(doc, score))

        return SearchResponse(
            query=query,
            results=search_results,
            total=len(search_results),
        )

    except QueryError:
        raise
    except Exception as e:
        raise QueryError(
            f"Search failed: {e}",
            query=query,
            stage="retrieval",
        ) from e


# =============================================================================
# Q&A Pipeline
# =============================================================================


def create_qa_pipeline(
    store: QdrantDocumentStore, config: OllamaConfig | None = None
) -> Pipeline:
    """
    Create Haystack Q&A pipeline with LLM generation.

    Pipeline components:
    1. OllamaTextEmbedder - Embed the query text
    2. QdrantEmbeddingRetriever - Retrieve relevant documents
    3. PromptBuilder - Build prompt with context
    4. OllamaGenerator - Generate answer

    Args:
        store: QdrantDocumentStore instance.
        config: Ollama configuration for embedding and LLM servers.

    Returns:
        Configured Haystack Pipeline for Q&A.
    """
    if config is None:
        config = ollama_config

    pipeline = Pipeline()

    # Query embedder (remote server)
    embedder = OllamaTextEmbedder(
        url=config.remote_url,
        model=config.embedding_model,
        timeout=config.embedding_timeout,
    )

    # Retriever
    retriever = QdrantEmbeddingRetriever(document_store=store)

    # Prompt builder
    prompt_builder = PromptBuilder(template=QA_PROMPT_TEMPLATE)

    # LLM generator (local server)
    generator = OllamaGenerator(
        url=config.local_url,
        model=config.llm_model,
        timeout=config.llm_timeout,
        generation_kwargs={"num_ctx": config.num_ctx},
    )

    # Add components
    pipeline.add_component("embedder", embedder)
    pipeline.add_component("retriever", retriever)
    pipeline.add_component("prompt_builder", prompt_builder)
    pipeline.add_component("generator", generator)

    # Connect components
    pipeline.connect("embedder.embedding", "retriever.query_embedding")
    pipeline.connect("retriever.documents", "prompt_builder.documents")
    pipeline.connect("prompt_builder.prompt", "generator.prompt")

    return pipeline


# =============================================================================
# Ask Function
# =============================================================================


def ask(
    pipeline: Pipeline,
    question: str,
    filters: QueryFilters | None = None,
    top_k: int = 5,
) -> Answer:
    """
    Ask a question and get LLM-generated answer with sources.

    Args:
        pipeline: Configured Q&A pipeline from create_qa_pipeline().
        question: Question to ask.
        filters: Optional filters for vault, tags, date range.
        top_k: Number of source documents to use (default: 5).

    Returns:
        Answer with generated text and sources.

    Raises:
        QueryError: If Q&A fails.
    """
    if not question or not question.strip():
        raise QueryError("Empty question provided", query=question, stage="validation")

    try:
        # Build Qdrant filters
        qdrant_filters = build_qdrant_filters(filters)

        # Run pipeline
        result = pipeline.run({
            "embedder": {"text": question},
            "retriever": {"top_k": top_k, "filters": qdrant_filters},
            "prompt_builder": {"query": question},
        })

        # Extract answer
        replies = result.get("generator", {}).get("replies", [])
        answer_text = replies[0] if replies else ""

        # Extract source documents
        documents = result.get("retriever", {}).get("documents", [])

        # Convert to SearchResults for sources
        sources: list[SearchResult] = []
        for doc in documents:
            score = doc.score if hasattr(doc, "score") and doc.score is not None else 0.0
            sources.append(_convert_to_search_result(doc, score))

        # Calculate confidence based on source scores
        if sources:
            avg_score = sum(s.score for s in sources) / len(sources)
            confidence = min(avg_score, 1.0)  # Cap at 1.0
        else:
            confidence = 0.0

        return Answer(
            text=answer_text,
            sources=sources,
            confidence=confidence,
        )

    except QueryError:
        raise
    except Exception as e:
        raise QueryError(
            f"Q&A failed: {e}",
            query=question,
            stage="generation",
        ) from e
