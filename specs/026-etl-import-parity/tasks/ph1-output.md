# Phase 1 Output: Setup (utils/prompts Copy)

## Summary

| Metric | Value |
|--------|-------|
| Phase | Phase 1 - Setup |
| Tasks | 12/12 completed |
| Status | Completed |
| Duration | N/A |

## Completed Tasks

| # | Task | Status |
|---|------|--------|
| T001 | Create src/etl/utils/ directory and __init__.py | Done |
| T002 | Copy ollama.py | Done |
| T003 | Copy knowledge_extractor.py | Done |
| T004 | Copy chunker.py | Done |
| T005 | Copy file_id.py | Done |
| T006 | Copy error_writer.py | Done |
| T007 | Create src/etl/prompts/ directory | Done |
| T008 | Copy knowledge_extraction.txt | Done |
| T009 | Copy summary_translation.txt | Done |
| T010 | Update import paths | Done |
| T011 | Run make test | Done (175 tests passed) |
| T012 | Generate phase output | Done |

## Created Files

### src/etl/utils/

| File | Description | Lines |
|------|-------------|-------|
| `__init__.py` | Module exports (ollama, file_id, chunker, error_writer, knowledge_extractor) | 48 |
| `ollama.py` | Ollama API client, JSON parsing helpers | 200 |
| `file_id.py` | File ID generation (SHA-256 hash) | 34 |
| `chunker.py` | Conversation chunking for large conversations | 208 |
| `error_writer.py` | Error detail Markdown file writer | 157 |
| `knowledge_extractor.py` | Knowledge extraction with LLM (KnowledgeExtractor, KnowledgeDocument) | 555 |

### src/etl/prompts/

| File | Description |
|------|-------------|
| `knowledge_extraction.txt` | System prompt for knowledge extraction |
| `summary_translation.txt` | System prompt for English-to-Japanese summary translation |

## Key Changes

### Import Path Updates

All copied modules now use `src.etl.utils` imports instead of `scripts.llm_import.common`:

```python
# Before (in converter)
from scripts.llm_import.base import BaseConversation
from scripts.llm_import.common.ollama import call_ollama

# After (in etl)
from src.etl.utils.ollama import call_ollama
from src.etl.utils.chunker import Chunker, Chunk
```

### Protocol Definitions

Replaced ABC base classes with Protocol definitions:

```python
class MessageProtocol(Protocol):
    content: str
    @property
    def role(self) -> str: ...

class ConversationProtocol(Protocol):
    title: str
    created_at: str
    @property
    def messages(self) -> list: ...
    @property
    def id(self) -> str: ...
    @property
    def provider(self) -> str: ...
```

This allows any object implementing these protocols to be used, without requiring inheritance from specific base classes.

## Exported Components

### From src.etl.utils

```python
# Ollama API
call_ollama
check_ollama_connection
parse_json_response
extract_json_from_code_block
extract_first_json_object

# File ID
generate_file_id

# Chunker
Chunker
Chunk
ChunkResult
ChunkedConversation

# Error Writer
ErrorDetail
write_error_file

# Knowledge Extractor
KnowledgeExtractor
KnowledgeDocument
ExtractionResult
CodeSnippet
extract_file_id_from_frontmatter
```

## Test Results

```
Ran 175 tests in 0.199s
OK
```

All existing tests pass. No regressions introduced.

## Next Phase Prerequisites

Phase 2 (Foundational) can now proceed with:

1. `src.etl.utils` module available for import
2. `src.etl.prompts/` directory with prompts ready
3. All utility functions (ollama, chunker, file_id, error_writer, knowledge_extractor) available

## Dependencies for Phase 2

- BaseStage in `src/etl/core/stage.py` - will add JSONL log and DEBUG output methods
- Phase context in `src/etl/core/phase.py` - will add pipeline_stages.jsonl path
- StageLogRecord dataclass in `src/etl/core/models.py` - new model for log entries
