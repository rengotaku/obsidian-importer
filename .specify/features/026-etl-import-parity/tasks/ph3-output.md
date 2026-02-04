# Phase 3 Output: US1 + US2 - Ollama Knowledge Extraction + file_id (MVP)

## Summary

| Metric | Value |
|--------|-------|
| Phase | Phase 3 - US1 + US2 (MVP) |
| Tasks | 11/11 completed |
| Status | Completed |
| Tests | 194 tests passed |

## Completed Tasks

| # | Task | Status |
|---|------|--------|
| T024 | Read previous phase output | Done |
| T025 | Add test for ExtractKnowledgeStep with mocked Ollama | Done |
| T026 | Add test for GenerateMetadataStep file_id generation | Done |
| T027 | Add test for FormatMarkdownStep output format | Done |
| T028 | Replace stub in ExtractKnowledgeStep with KnowledgeExtractor.extract() | Done |
| T029 | Add Ollama error handling with tenacity retry | Done |
| T030 | Implement file_id generation in GenerateMetadataStep | Done |
| T031 | Update FormatMarkdownStep to use KnowledgeDocument.to_markdown() | Done |
| T032 | Add metadata keys (knowledge_extracted, file_id) | Done |
| T033 | Run make test | Done (194 tests passed) |
| T034 | Generate phase output | Done |

## New/Modified Files

### src/etl/stages/transform/knowledge_transformer.py (Modified)

Major changes:

1. **ExtractKnowledgeStep** - Now uses Ollama for knowledge extraction:
   - Imports `KnowledgeExtractor`, `KnowledgeDocument`, `ExtractionResult` from `src.etl.utils`
   - Creates `ConversationData` and `Message` dataclasses conforming to protocol
   - Calls `_extract_with_retry()` with tenacity decorator
   - Handles extraction failure with detailed error metadata
   - Sets `knowledge_extracted` and `knowledge_document` in item metadata

2. **GenerateMetadataStep** - Now generates file_id:
   - Imports `generate_file_id` from `src.etl.utils.file_id`
   - Generates 12-character hex file_id for all items
   - Updates `knowledge_document.file_id` if present
   - Includes file_id in generated_metadata

3. **FormatMarkdownStep** - Now uses KnowledgeDocument.to_markdown():
   - Checks for `knowledge_document` in metadata
   - Uses `KnowledgeDocument.to_markdown()` if available
   - Falls back to original formatting for non-conversation items

Key code additions:

```python
# ConversationData for KnowledgeExtractor protocol
@dataclass
class Message:
    content: str
    _role: str

    @property
    def role(self) -> str:
        return self._role

@dataclass
class ConversationData:
    title: str
    created_at: str
    _messages: list[Message]
    _id: str
    _provider: str
    summary: str | None = None

    @property
    def messages(self) -> list[Message]:
        return self._messages

    @property
    def id(self) -> str:
        return self._id

    @property
    def provider(self) -> str:
        return self._provider
```

```python
# Tenacity retry decorator on ExtractKnowledgeStep
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True,
)
def _extract_with_retry(self, conversation: ConversationData) -> ExtractionResult:
    return self._extractor.extract(conversation)
```

### src/etl/tests/test_knowledge_transformer.py (New)

New test file with 10 test cases:

1. **TestExtractKnowledgeStepWithMockedOllama** (3 tests):
   - `test_extract_knowledge_calls_extractor`: Verifies KnowledgeExtractor.extract() is called
   - `test_extract_knowledge_handles_extraction_failure`: Verifies RuntimeError on failure
   - `test_extract_knowledge_sets_metadata_keys`: Verifies knowledge_extracted metadata

2. **TestGenerateMetadataStepFileId** (3 tests):
   - `test_file_id_generated_for_conversation`: Verifies 12-char hex file_id
   - `test_file_id_deterministic`: Same content + path = same file_id
   - `test_file_id_different_for_different_content`: Different content = different file_id

3. **TestFormatMarkdownStepOutput** (3 tests):
   - `test_format_markdown_uses_knowledge_document`: Uses to_markdown() method
   - `test_format_markdown_includes_code_snippets`: Code snippets in output
   - `test_format_markdown_fallback_for_non_conversation`: Fallback for other types

4. **TestKnowledgeTransformerStage** (1 test):
   - `test_knowledge_transformer_has_correct_steps`: Correct step order

## Key Design Decisions

### 1. Protocol-based Conversation Data

Created `ConversationData` and `Message` dataclasses that conform to `KnowledgeExtractor`'s protocol expectations:
- Uses property methods for `messages`, `id`, `provider`
- Allows clean separation between ETL pipeline data model and extraction logic

### 2. Tenacity Retry Integration

ExtractKnowledgeStep uses tenacity decorator for Ollama API resilience:
- 3 attempts maximum
- Exponential backoff (2-30 seconds)
- Retries on `ConnectionError` and `TimeoutError`
- Re-raises after exhaustion for proper error handling

### 3. Metadata Key Strategy

ProcessingItem.metadata keys used:
- `knowledge_extracted`: bool - Whether Ollama extraction succeeded
- `knowledge_document`: KnowledgeDocument - Extracted document object
- `file_id`: str - 12-char hex hash for file tracking
- `extraction_error`: str - Error message if extraction failed
- `llm_prompt`: str - LLM prompt (for debugging on error)
- `llm_raw_response`: str - Raw LLM response (for debugging on error)

### 4. file_id Generation

Uses `generate_file_id(content, path)` from `src.etl.utils.file_id`:
- SHA-256 hash of content + POSIX path
- First 12 characters (48 bits)
- Deterministic for same input
- Compatible with normalizer's algorithm

## Test Results

```
Ran 194 tests in 0.211s
OK
```

All existing tests pass. 10 new tests added for knowledge_transformer.

## Next Phase Prerequisites

Phase 4 (US3 - Chunking) can now proceed with:

1. `ExtractKnowledgeStep` has working Ollama integration
2. `KnowledgeExtractor.should_chunk()` and `extract_chunked()` available
3. file_id generation working for all items
4. Test patterns established for mocking Ollama

## Dependencies for Phase 4

- `KnowledgeExtractor.should_chunk()` - Already implemented in utils
- `KnowledgeExtractor.extract_chunked()` - Already implemented in utils
- `Chunker` class - Already copied to src/etl/utils/chunker.py
- Chunk metadata handling in ProcessingItem

## MVP Checkpoint

With Phase 3 complete, the MVP is functional:

1. **Ollama Knowledge Extraction**: Conversations are processed through Ollama for summary, tags, code snippets
2. **file_id Generation**: All output files have unique 12-char hex identifiers
3. **Markdown Output**: Uses KnowledgeDocument.to_markdown() for consistent formatting
4. **Error Handling**: Extraction failures are properly handled with retry and error metadata

The basic import pipeline can now process Claude conversation exports end-to-end.
