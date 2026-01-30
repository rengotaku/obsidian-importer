# Phase 2 Output: Ollama Client

**Phase**: Phase 2 - Ollama Client
**Status**: Complete
**Date**: 2026-01-18

## Summary

- Tasks: 9/9 complete (T013-T021)
- Tests: 32/32 passed (7 from Phase 1 + 25 new)

## Completed Tasks

| ID | Task | Status |
|----|------|--------|
| T013 | Read previous phase output | Done |
| T014 | Implement `check_connection()` | Done |
| T015 | Add tests for `check_connection()` | Done |
| T016 | Implement `get_embedding()` | Done |
| T017 | Add tests for `get_embedding()` | Done |
| T018 | Implement `generate_response()` | Done |
| T019 | Add tests for `generate_response()` | Done |
| T020 | Run tests | Done - 32/32 passed |
| T021 | Generate phase output | Done - This file |

## Artifacts Created

### Source Files

- `src/rag/clients/ollama.py` - Ollama API client with 3 functions
- `src/rag/clients/__init__.py` - Updated with exports

### Test Files

- `tests/rag/test_ollama_client.py` - 25 unit tests (all mocked)

## API Implementation

### check_connection()

```python
def check_connection(url: str, timeout: int = 5) -> tuple[bool, str | None]:
    """
    Ollama server connection check via /api/tags endpoint.
    Returns (True, None) on success, (False, error_message) on failure.
    """
```

### get_embedding()

```python
def get_embedding(
    text: str,
    model: str = "bge-m3",
    url: str = "http://ollama-server.local:11434",
    timeout: int = 30,
) -> tuple[list[float] | None, str | None]:
    """
    Get text embedding via /api/embed endpoint.
    Default URL is remote server (ollama-server.local) for bge-m3 model.
    Returns (embedding, None) on success, (None, error) on failure.
    """
```

### generate_response()

```python
def generate_response(
    prompt: str,
    model: str = "gpt-oss:20b",
    url: str = "http://localhost:11434",
    num_ctx: int = 65536,
    timeout: int = 120,
) -> tuple[str | None, str | None]:
    """
    Generate LLM response via /api/generate endpoint.
    Default URL is localhost for gpt-oss:20b model.
    Uses stream=False for complete response.
    Returns (response, None) on success, (None, error) on failure.
    """
```

## Test Coverage

| Category | Tests | Description |
|----------|-------|-------------|
| check_connection | 5 | Success, timeout, connection error, HTTP error, custom timeout |
| get_embedding | 11 | Success, custom params, defaults, empty text, whitespace, timeout, connection error, invalid JSON, no embeddings |
| generate_response | 12 | Success, custom params, defaults, stream disabled, empty prompt, whitespace, timeout, connection error, no response, empty response valid |
| imports | 1 | Package-level imports work |

## Dependencies Added

- `requests` - HTTP client library (standard, widely used)

## Design Decisions

1. **Return Tuples**: All functions return `(result, error)` tuples for explicit error handling
2. **No Exceptions**: Functions catch all exceptions internally and return error messages
3. **Empty String Validation**: Empty/whitespace-only inputs are rejected before making HTTP calls
4. **Empty Response Valid**: For generate_response, empty string response is valid (not an error)
5. **Mocked Tests**: All tests mock HTTP calls - no running server required

## Issues Encountered

1. **requests not installed**: Had to install requests package in venv via `python -m pip install requests`

## Handoff to Phase 3

Phase 3 (Qdrant Store) can now use:

```python
from src.rag.clients.ollama import check_connection, get_embedding, generate_response
from src.rag.clients import check_connection, get_embedding, generate_response  # also works
```

Usage examples:

```python
# Check server connectivity
success, error = check_connection("http://ollama-server.local:11434")

# Get embedding for text
embedding, error = get_embedding("Hello world")

# Generate LLM response
response, error = generate_response("What is Python?")
```

Next tasks:
- T022: Read this output
- T023-T028: Implement Qdrant store functions
