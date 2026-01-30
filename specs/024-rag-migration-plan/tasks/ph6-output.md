# Phase 6 Output: CLI

**Phase**: Phase 6 - CLI
**Status**: Complete
**Date**: 2026-01-18

## Summary

- Tasks: 12/12 complete (T051-T062)
- New files: 1 (src/rag/cli.py)
- Makefile targets: 4 (rag-index, rag-search, rag-ask, rag-status)

## Completed Tasks

| ID | Task | Status |
|----|------|--------|
| T051 | Read previous phase output | Done |
| T052 | Implement CLI argument parser | Done |
| T053 | Implement `cmd_index()` | Done |
| T054 | Implement `cmd_search()` | Done |
| T055 | Implement `cmd_ask()` | Done |
| T056 | Implement `cmd_status()` | Done |
| T057 | Add `rag-index` target to Makefile | Done |
| T058 | Add `rag-search` target to Makefile | Done |
| T059 | Add `rag-ask` target to Makefile | Done |
| T060 | Add `rag-status` target to Makefile | Done |
| T061 | Run CLI commands to verify | Done |
| T062 | Generate phase output | Done - This file |

## Artifacts Created

### Source Files

- `src/rag/cli.py` - CLI implementation with 4 subcommands

### Makefile Targets

- `rag-index` - Index vault documents
- `rag-search` - Semantic search
- `rag-ask` - Q&A with LLM
- `rag-status` - Show index status

## CLI Commands

### `rag index`

```bash
# Usage
python -m src.rag.cli index [--vault VAULT] [--dry-run] [--verbose]

# Makefile
make rag-index                     # Index all vaults
make rag-index VAULT=エンジニア    # Index specific vault
make rag-index ACTION=preview      # Dry run mode
```

**Exit Codes**:
| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Argument error |
| 3 | Connection error |

**Output (dry-run)**:
```
[DRY RUN] Indexing Complete
==================================================
Total documents: 10
Indexed documents: 10
Total chunks: 10
Errors: 0
Elapsed: 0.05s
```

### `rag search`

```bash
# Usage
python -m src.rag.cli search QUERY [--vault VAULT] [--tag TAG] [--top-k N] [--format FORMAT]

# Makefile
make rag-search QUERY="Kubernetes"
make rag-search QUERY="API" VAULT=エンジニア TAG=REST TOP_K=10
make rag-search QUERY="test" FORMAT=json
```

**Output (text)**:
```
Found 5 results for "Kubernetes"

1. [0.92] Kubernetes Blue-Green デプロイメント
   Vaults/エンジニア/kubernetes/blue-green.md
   ...Blue-Green デプロイは、2つの同一環境を用意し...

2. [0.87] Kubernetes Canary リリース戦略
   Vaults/エンジニア/kubernetes/canary.md
   ...Canary リリースでは、新バージョンを一部のユーザーに...
```

**Output (json)**:
```json
{
  "query": "Kubernetes",
  "results": [
    {
      "score": 0.92,
      "title": "Kubernetes Blue-Green デプロイメント",
      "file_path": "Vaults/エンジニア/kubernetes/blue-green.md",
      "vault": "エンジニア",
      "snippet": "...Blue-Green デプロイは..."
    }
  ],
  "total": 5,
  "elapsed_ms": 1250
}
```

### `rag ask`

```bash
# Usage
python -m src.rag.cli ask QUESTION [--vault VAULT] [--tag TAG] [--top-k N] [--format FORMAT] [--no-sources]

# Makefile
make rag-ask QUERY="Kubernetes Pod とは？"
make rag-ask QUERY="OAuth2とJWTの違いは？" VAULT=エンジニア
make rag-ask QUERY="test" FORMAT=json
```

**Output (text)**:
```
Q: OAuth2 と JWT の違いは？

A: OAuth2 は認可のためのフレームワークであり、JWTはトークンの形式です...

Sources:
- [1] OAuth2 認可フロー (Vaults/エンジニア/auth/oauth2.md)
- [2] JWT トークン構造 (Vaults/エンジニア/auth/jwt.md)
```

**Output (json)**:
```json
{
  "question": "OAuth2 と JWT の違いは？",
  "answer": "OAuth2 は認可のためのフレームワークであり...",
  "confidence": 0.88,
  "elapsed_ms": 3200,
  "sources": [
    {
      "title": "OAuth2 認可フロー",
      "file_path": "Vaults/エンジニア/auth/oauth2.md",
      "score": 0.91,
      "snippet": "..."
    }
  ]
}
```

### `rag status`

```bash
# Usage
python -m src.rag.cli status [--format FORMAT] [--verbose]

# Makefile
make rag-status
make rag-status FORMAT=json
```

**Output (text)**:
```
RAG Index Status
==================================================
Collection: obsidian_knowledge
Total Chunks: 4532
Embedding Dim: 1024
Similarity: cosine
```

**Output (json)**:
```json
{
  "collection_name": "obsidian_knowledge",
  "document_count": 4532,
  "embedding_dim": 1024,
  "similarity": "cosine"
}
```

## Error Handling

The CLI provides user-friendly error messages for common issues:

### Connection Errors

```
Error: Cannot connect to embedding server: Connection failed: http://ollama-server.local:11434
Server: http://ollama-server.local:11434
```

Exit code: 3 (EXIT_CONNECTION_ERROR)

### Missing Arguments

```
Error: QUERY is required
  Example: make rag-search QUERY="Kubernetes"
```

Exit code: 1

### Query Errors

```
Search error: Empty query provided
```

Exit code: 1

## Design Decisions

1. **argparse over click**: Used standard library argparse for simplicity and no external dependencies
2. **structlog for logging**: Consistent with Haystack's logging approach
3. **Exit codes**: Clear exit codes for CI/CD integration (0=success, 1=error, 2=args, 3=connection)
4. **Dual output formats**: Both text (human-readable) and JSON (machine-readable)
5. **Connection verification**: Check server connection before executing commands
6. **Verbose mode**: Optional verbose output for debugging

## Makefile Integration

The Makefile provides convenience wrappers with variable substitution:

```makefile
# Variables
VAULT=xxx          # Target vault
QUERY="text"       # Search query
TAG=xxx            # Tag filter
TOP_K=N            # Number of results
FORMAT=json        # Output format (json/text)
ACTION=preview     # For index dry-run
```

## Test Results

Verified commands:

| Command | Result |
|---------|--------|
| `python -m src.rag.cli --help` | OK - Shows help |
| `python -m src.rag.cli index --help` | OK - Shows index help |
| `python -m src.rag.cli search --help` | OK - Shows search help |
| `python -m src.rag.cli ask --help` | OK - Shows ask help |
| `python -m src.rag.cli status --help` | OK - Shows status help |
| `make rag-status` | OK - Shows collection stats |
| `make rag-status FORMAT=json` | OK - JSON output |
| `make rag-index ACTION=preview` | OK - Dry run mode |
| `make rag-search` (no QUERY) | OK - Shows error message |
| `make rag-ask` (no QUERY) | OK - Shows error message |

## Handoff to Phase 7

Phase 7 (Integration & Validation) can now:

1. Create E2E tests using CLI commands
2. Validate performance requirements
3. Test edge cases

CLI entry point:
```python
from src.rag.cli import main

# Run CLI
exit_code = main(["index", "--dry-run", "--vault", "エンジニア"])
```

Full API available:
```python
# Config
from src.rag.config import RAGConfig, OllamaConfig, QDRANT_PATH, VAULTS_DIR

# Exceptions
from src.rag.exceptions import RAGError, ConnectionError, IndexingError, QueryError

# Clients
from src.rag.clients import check_connection, get_embedding, generate_response

# Stores
from src.rag.stores import get_document_store, get_collection_stats, COLLECTION_NAME

# Pipelines
from src.rag.pipelines import (
    # Indexing
    create_indexing_pipeline,
    index_vault,
    index_all_vaults,
    scan_vault,
    chunk_document,
    chunk_documents,
    Document,
    DocumentMeta,
    IndexingResult,
    # Query
    create_search_pipeline,
    create_qa_pipeline,
    search,
    ask,
    QueryFilters,
    SearchResult,
    SearchResponse,
    Answer,
)
```

Next tasks (Phase 7):
- T063: Read this output
- T064-T066: Create E2E tests
- T067-T072: Performance validation
