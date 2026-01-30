# Phase 5 Output: Query Pipeline

**Phase**: Phase 5 - Query Pipeline
**Status**: Complete
**Date**: 2026-01-18

## Summary

- Tasks: 11/11 complete (T040-T050)
- Tests: 43 new tests (all mocked, no running Ollama/Qdrant required)
- Total RAG tests: 127 (all passing)

## Completed Tasks

| ID | Task | Status |
|----|------|--------|
| T040 | Read previous phase output | Done |
| T041 | Implement `create_search_pipeline()` | Done |
| T042 | Add tests for `create_search_pipeline()` | Done |
| T043 | Implement `search()` with filters | Done |
| T044 | Add tests for `search()` | Done |
| T045 | Implement `create_qa_pipeline()` | Done |
| T046 | Add tests for `create_qa_pipeline()` | Done |
| T047 | Implement `ask()` with source citations | Done |
| T048 | Add tests for `ask()` | Done |
| T049 | Run tests | Done - all 127 passed |
| T050 | Generate phase output | Done - This file |

## Artifacts Created

### Source Files

- `src/rag/pipelines/query.py` - Query pipeline implementation
- `src/rag/pipelines/__init__.py` - Updated with query exports

### Test Files

- `tests/rag/test_query.py` - 43 unit tests (all mocked)

## Data Models

### QueryFilters

```python
@dataclass
class QueryFilters:
    """Filters for search queries"""
    vaults: list[str] | None = None  # Filter by vault names
    tags: list[str] | None = None    # Filter by tags (AND)
    date_from: date | None = None    # Filter by created date (>=)
    date_to: date | None = None      # Filter by created date (<=)
```

### SearchResult

```python
@dataclass
class SearchResult:
    """Single search result"""
    content: str           # Matched chunk content
    score: float          # Similarity score 0.0-1.0
    file_path: str        # Source file path
    title: str            # Document title
    vault: str            # Vault name
    position: int         # Chunk position in document
```

### SearchResponse

```python
@dataclass
class SearchResponse:
    """Response from search query"""
    query: str
    results: list[SearchResult]
    total: int
```

### Answer

```python
@dataclass
class Answer:
    """Answer from Q&A query"""
    text: str                      # Generated answer
    sources: list[SearchResult]    # Referenced chunks
    confidence: float              # 0.0-1.0 (average of source scores)
```

## API Implementation

### build_qdrant_filters()

```python
def build_qdrant_filters(filters: QueryFilters | None) -> dict[str, Any] | None:
    """
    Build Qdrant filter dict from QueryFilters.

    Supports:
    - Single/multiple vault filter (==, in)
    - Tag filter with AND logic (contains)
    - Date range filter (>=, <=)
    - Combined filters (AND)
    """
```

### create_search_pipeline()

```python
def create_search_pipeline(
    store: QdrantDocumentStore, config: OllamaConfig | None = None
) -> Pipeline:
    """
    Create Haystack search pipeline with embedding retrieval.

    Pipeline components:
    1. OllamaTextEmbedder - Embed the query text (remote server)
    2. QdrantEmbeddingRetriever - Retrieve similar documents

    Connections:
    - embedder.embedding -> retriever.query_embedding
    """
```

### search()

```python
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
        QueryError: If query is empty or search fails.
    """
```

### create_qa_pipeline()

```python
def create_qa_pipeline(
    store: QdrantDocumentStore, config: OllamaConfig | None = None
) -> Pipeline:
    """
    Create Haystack Q&A pipeline with LLM generation.

    Pipeline components:
    1. OllamaTextEmbedder - Embed the query text (remote server)
    2. QdrantEmbeddingRetriever - Retrieve relevant documents
    3. PromptBuilder - Build prompt with context
    4. OllamaGenerator - Generate answer (local server)

    Connections:
    - embedder.embedding -> retriever.query_embedding
    - retriever.documents -> prompt_builder.documents
    - prompt_builder.prompt -> generator.prompt
    """
```

### ask()

```python
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
        Answer with generated text, sources, and confidence.

    Raises:
        QueryError: If question is empty or Q&A fails.
    """
```

## Test Coverage

| Category | Tests | Description |
|----------|-------|-------------|
| QueryFilters | 4 | Default values, vaults, tags, date range |
| SearchResult | 1 | Creation with all fields |
| SearchResponse | 1 | Creation with results |
| Answer | 1 | Creation with sources and confidence |
| build_qdrant_filters | 10 | None, empty, vault, tags, dates, combined |
| create_search_pipeline | 5 | Components, config, default config, connections, store |
| search | 8 | Empty query, success, filters, top_k, error, metadata, score |
| create_qa_pipeline | 4 | Components, config, connections, template |
| ask | 10 | Empty question, success, filters, top_k, error, replies, confidence |
| **Total** | **43** | |

## Design Decisions

1. **Separate Servers**: Embedding uses remote server (ollama-server.local), LLM uses local server
2. **Filter Building**: Qdrant filters built dynamically based on QueryFilters
3. **Tag AND Logic**: Multiple tags require ALL tags to match (AND)
4. **Confidence Calculation**: Average of source document scores
5. **Error Handling**: Empty queries raise immediately, pipeline errors wrapped in QueryError
6. **Japanese Prompt**: Q&A prompt template in Japanese for better results

## Pipeline Architecture

### Search Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                   Search Pipeline                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   Query Text                                            │
│       │                                                  │
│       ▼                                                  │
│   ┌─────────────────┐                                   │
│   │  OllamaText     │  (remote server)                  │
│   │  Embedder       │                                   │
│   └─────────────────┘                                   │
│       │                                                  │
│       │ embedding                                        │
│       ▼                                                  │
│   ┌─────────────────┐                                   │
│   │  Qdrant         │  + filters                        │
│   │  Retriever      │  + top_k                          │
│   └─────────────────┘                                   │
│       │                                                  │
│       ▼                                                  │
│   SearchResponse                                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Q&A Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                    Q&A Pipeline                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   Question                                              │
│       │                                                  │
│       ▼                                                  │
│   ┌─────────────────┐                                   │
│   │  OllamaText     │  (remote server)                  │
│   │  Embedder       │                                   │
│   └─────────────────┘                                   │
│       │                                                  │
│       │ embedding                                        │
│       ▼                                                  │
│   ┌─────────────────┐                                   │
│   │  Qdrant         │  + filters                        │
│   │  Retriever      │  + top_k                          │
│   └─────────────────┘                                   │
│       │                                                  │
│       │ documents                                        │
│       ▼                                                  │
│   ┌─────────────────┐                                   │
│   │  Prompt         │  + query                          │
│   │  Builder        │                                   │
│   └─────────────────┘                                   │
│       │                                                  │
│       │ prompt                                           │
│       ▼                                                  │
│   ┌─────────────────┐                                   │
│   │  Ollama         │  (local server)                   │
│   │  Generator      │                                   │
│   └─────────────────┘                                   │
│       │                                                  │
│       ▼                                                  │
│   Answer (text + sources + confidence)                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Q&A Prompt Template

```
以下のコンテキストを参考にして、質問に回答してください。

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

回答:
```

## Handoff to Phase 6

Phase 6 (CLI) can now use:

```python
from src.rag.pipelines import (
    # Indexing
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
    # Query
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
```

Usage examples:

```python
from src.rag.stores import get_document_store
from src.rag.pipelines import (
    create_search_pipeline,
    create_qa_pipeline,
    search,
    ask,
    QueryFilters,
)

# Create document store
store = get_document_store()

# Search example
search_pipeline = create_search_pipeline(store)
response = search(
    search_pipeline,
    "Kubernetes deployment",
    filters=QueryFilters(vaults=["エンジニア"], tags=["kubernetes"]),
    top_k=5,
)
for result in response.results:
    print(f"{result.title}: {result.score:.2f}")

# Q&A example
qa_pipeline = create_qa_pipeline(store)
answer = ask(
    qa_pipeline,
    "Kubernetes の Pod とは何ですか？",
    filters=QueryFilters(vaults=["エンジニア"]),
)
print(f"Answer: {answer.text}")
print(f"Confidence: {answer.confidence:.2f}")
for src in answer.sources:
    print(f"  Source: {src.title}")
```

Available from previous phases:

```python
# From Phase 1
from src.rag.config import RAGConfig, OllamaConfig, QDRANT_PATH, VAULTS_DIR
from src.rag.exceptions import RAGError, ConnectionError, IndexingError, QueryError

# From Phase 2
from src.rag.clients import check_connection, get_embedding, generate_response

# From Phase 3
from src.rag.stores import get_document_store, get_collection_stats, COLLECTION_NAME
```

Next tasks:
- T051: Read this output
- T052-T062: Implement CLI (cmd_index, cmd_search, cmd_ask, cmd_status, Makefile targets)
