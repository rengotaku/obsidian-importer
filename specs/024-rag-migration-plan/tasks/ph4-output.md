# Phase 4 Output: Indexing Pipeline

**Phase**: Phase 4 - Indexing Pipeline
**Status**: Complete
**Date**: 2026-01-18

## Summary

- Tasks: 11/11 complete (T029-T039)
- Tests: 36 new tests (all mocked, no running Ollama/Qdrant required)
- Total RAG tests: 84 (all passing)

## Completed Tasks

| ID | Task | Status |
|----|------|--------|
| T029 | Read previous phase output | Done |
| T030 | Implement `scan_vault()` | Done |
| T031 | Add tests for `scan_vault()` | Done |
| T032 | Implement chunking logic | Done |
| T033 | Add tests for chunking | Done |
| T034 | Implement `create_indexing_pipeline()` | Done |
| T035 | Add tests for `create_indexing_pipeline()` | Done |
| T036 | Implement `index_vault()` | Done |
| T037 | Add tests for `index_vault()` | Done |
| T038 | Run tests | Done - all passed |
| T039 | Generate phase output | Done - This file |

## Artifacts Created

### Source Files

- `src/rag/pipelines/indexing.py` - Indexing pipeline implementation
- `src/rag/pipelines/__init__.py` - Updated with exports

### Test Files

- `tests/rag/test_indexing.py` - 34 unit tests (all mocked)

## Data Models

### DocumentMeta

```python
@dataclass
class DocumentMeta:
    """Document metadata from frontmatter"""
    tags: list[str] = field(default_factory=list)
    created: str = ""
    normalized: bool = False
    file_id: str = ""
```

### Document

```python
@dataclass
class Document:
    """Parsed document from vault"""
    file_path: Path
    title: str
    content: str
    metadata: DocumentMeta
    vault_name: str
```

### IndexingResult

```python
@dataclass
class IndexingResult:
    """Result of indexing operation"""
    total_docs: int
    indexed_docs: int
    total_chunks: int
    errors: list[str] = field(default_factory=list)
```

## API Implementation

### parse_frontmatter()

```python
def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown content with potential frontmatter.

    Returns:
        Tuple of (frontmatter dict, body content without frontmatter).
        Returns empty dict if no frontmatter found.
    """
```

### scan_vault()

```python
def scan_vault(vault_path: Path, vault_name: str) -> list[Document]:
    """
    Scan vault for normalized markdown files.

    Only includes files with `normalized: true` in frontmatter.

    Args:
        vault_path: Path to vault directory.
        vault_name: Name of the vault (e.g., "エンジニア").

    Returns:
        List of Document objects for normalized files.

    Raises:
        IndexingError: If vault path does not exist.
    """
```

### chunk_document()

```python
def chunk_document(
    doc: Document, chunk_size: int = 512, overlap: int = 50
) -> list[HaystackDocument]:
    """
    Split document into chunks with metadata.

    Uses Haystack DocumentSplitter with word-based splitting.

    Args:
        doc: Document to chunk.
        chunk_size: Target chunk size in words (default: 512).
        overlap: Overlap between chunks in words (default: 50).

    Returns:
        List of Haystack Document objects with metadata.
    """
```

### create_indexing_pipeline()

```python
def create_indexing_pipeline(
    store: QdrantDocumentStore, config: OllamaConfig | None = None
) -> Pipeline:
    """
    Create Haystack indexing pipeline.

    Pipeline components:
    1. OllamaDocumentEmbedder - Generate embeddings for documents
    2. DocumentWriter - Write documents to Qdrant store

    Args:
        store: QdrantDocumentStore instance.
        config: Ollama configuration for embedding server.

    Returns:
        Configured Haystack Pipeline.
    """
```

### index_vault()

```python
def index_vault(
    pipeline: Pipeline,
    vault_path: Path,
    vault_name: str,
    dry_run: bool = False,
    rag_config_override: RAGConfig | None = None,
) -> IndexingResult:
    """
    Index all documents in a vault.

    Args:
        pipeline: Configured indexing pipeline.
        vault_path: Path to vault directory.
        vault_name: Name of the vault.
        dry_run: If True, scan and chunk but don't write to store.
        rag_config_override: Optional RAG config override.

    Returns:
        IndexingResult with statistics.
    """
```

### index_all_vaults()

```python
def index_all_vaults(
    pipeline: Pipeline,
    vaults_dir: Path | None = None,
    vault_names: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, IndexingResult]:
    """
    Index all configured vaults.

    Returns:
        Dictionary mapping vault names to IndexingResult.
    """
```

## Test Coverage

| Category | Tests | Description |
|----------|-------|-------------|
| parse_frontmatter | 4 | Valid, no frontmatter, empty, invalid YAML |
| extract_metadata | 6 | Full metadata, empty, string tag, normalized values, date object |
| scan_vault | 7 | Empty, non-existent, normalized filter, nested dirs, metadata, filename fallback, content excludes frontmatter |
| chunk_document | 4 | Short doc, long doc, metadata preservation, overlap |
| chunk_documents | 2 | Multiple docs, custom config |
| create_indexing_pipeline | 4 | Components, config usage, default config, connections |
| index_vault | 7 | Empty, non-existent, counts, dry_run, pipeline calls, pipeline error, normalized filter |
| IndexingResult | 2 | Default errors, errors preserved |
| **Total** | **36** | |

## Design Decisions

1. **Word-based Chunking**: Uses Haystack DocumentSplitter with `split_by="word"` for consistent chunk sizes
2. **Metadata Preservation**: All document metadata flows through to chunks for filtering/retrieval
3. **Normalized Filter**: Only processes files with `normalized: true` in frontmatter
4. **Position Tracking**: Each chunk has a `position` metadata field for ordering
5. **Dry Run Mode**: Allows testing without writing to Qdrant
6. **Error Handling**: Pipeline errors are captured in IndexingResult.errors without raising

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Indexing Pipeline                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   scan_vault()                                          │
│       │                                                  │
│       ▼                                                  │
│   ┌─────────────┐                                       │
│   │  Documents  │  (normalized files only)              │
│   └─────────────┘                                       │
│       │                                                  │
│       ▼                                                  │
│   chunk_documents()                                     │
│       │                                                  │
│       ▼                                                  │
│   ┌─────────────────┐                                   │
│   │ Haystack Docs   │  (with metadata)                  │
│   └─────────────────┘                                   │
│       │                                                  │
│       ▼                                                  │
│   ┌─────────────────────────────────┐                   │
│   │        Haystack Pipeline        │                   │
│   │  ┌───────────┐   ┌───────────┐  │                   │
│   │  │ Embedder  │──▶│  Writer   │  │                   │
│   │  │ (Ollama)  │   │ (Qdrant)  │  │                   │
│   │  └───────────┘   └───────────┘  │                   │
│   └─────────────────────────────────┘                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Chunk Metadata Schema

```json
{
  "content": "Chunk text content...",
  "meta": {
    "file_path": "/home/user/Vaults/エンジニア/kubernetes.md",
    "title": "Kubernetes Guide",
    "vault": "エンジニア",
    "tags": ["kubernetes", "container"],
    "created": "2024-01-15",
    "file_id": "abc123def456",
    "position": 0
  }
}
```

## Handoff to Phase 5

Phase 5 (Query Pipeline) can now use:

```python
from src.rag.pipelines import (
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
```

Usage examples:

```python
from src.rag.stores import get_document_store
from src.rag.pipelines import create_indexing_pipeline, index_vault

# Create document store
store = get_document_store()

# Create indexing pipeline
pipeline = create_indexing_pipeline(store)

# Index a vault
result = index_vault(
    pipeline,
    Path("/home/user/Vaults/エンジニア"),
    "エンジニア",
    dry_run=True  # Test without writing
)

print(f"Total: {result.total_docs}, Indexed: {result.indexed_docs}, Chunks: {result.total_chunks}")
```

Available from previous phases:

```python
# From Phase 1
from src.rag.config import RAGConfig, OllamaConfig, QDRANT_PATH, VAULTS_DIR
from src.rag.exceptions import RAGError, ConnectionError, IndexingError

# From Phase 2
from src.rag.clients import check_connection, get_embedding, generate_response

# From Phase 3
from src.rag.stores import get_document_store, get_collection_stats, COLLECTION_NAME
```

Next tasks:
- T040: Read this output
- T041-T050: Implement query pipeline (create_search_pipeline, search, create_qa_pipeline, ask)
