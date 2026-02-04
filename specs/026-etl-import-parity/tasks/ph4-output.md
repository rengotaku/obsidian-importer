# Phase 4 Output: US3 - Large Conversation Chunking

## Summary

| Metric | Value |
|--------|-------|
| Phase | Phase 4 - US3 (Chunking) |
| Tasks | 11/11 completed |
| Status | Completed |
| Tests | 201 tests passed |

## Completed Tasks

| # | Task | Status |
|---|------|--------|
| T035 | Read previous phase output | Done |
| T036 | Add test for should_chunk() | Done |
| T037 | Add test for chunk splitting with multiple outputs | Done |
| T038 | Add test for partial chunk failure handling | Done |
| T039 | Add _should_chunk() method to ExtractKnowledgeStep | Done |
| T040 | Add _handle_chunked_conversation() method | Done |
| T041 | Modify process() to branch on chunk decision | Done |
| T042 | Add chunk metadata (is_chunked, chunk_index, total_chunks) | Done |
| T043 | Handle chunk expansion (1 input -> N outputs) in KnowledgeTransformer | Done |
| T044 | Run make test | Done (201 tests passed) |
| T045 | Generate phase output | Done |

## New/Modified Files

### src/etl/stages/transform/knowledge_transformer.py (Modified)

Major changes:

1. **ExtractKnowledgeStep** - Now supports chunking for large conversations:
   - Added `CHUNK_SIZE = 25000` constant
   - Added `_pending_expansion` instance variable for chunk results
   - Added `_should_chunk(item)` method (T039)
   - Added `_handle_chunked_conversation(item)` method (T040)
   - Modified `process()` to branch on chunk decision (T041)
   - Added `process_with_expansion()` method for chunk expansion

2. **KnowledgeTransformer** - Overrides `run()` to handle chunk expansion:
   - Uses `process_with_expansion()` to get potentially multiple items
   - Processes each chunk through GenerateMetadata and FormatMarkdown steps
   - Handles partial chunk failures (some succeed, some fail)

Key code additions:

```python
# ExtractKnowledgeStep._should_chunk()
def _should_chunk(self, item: ProcessingItem) -> bool:
    """Check if conversation should be chunked."""
    source_type = item.metadata.get("source_type", "")
    if source_type != "conversation":
        return False
    if not item.content:
        return False
    try:
        data = json.loads(item.content)
    except json.JSONDecodeError:
        return False
    conversation = self._build_conversation(data, item)
    return self._extractor.should_chunk(conversation)

# ExtractKnowledgeStep._handle_chunked_conversation()
def _handle_chunked_conversation(self, item: ProcessingItem) -> list[ProcessingItem]:
    """Handle chunked conversation extraction."""
    data = json.loads(item.content)
    conversation = self._build_conversation(data, item)
    chunk_results = self._extractor.extract_chunked(conversation)
    total_chunks = len(chunk_results)
    result_items: list[ProcessingItem] = []

    for chunk_index, (filename, result) in enumerate(chunk_results):
        chunk_item = ProcessingItem(
            item_id=f"{item.item_id}#chunk{chunk_index}",
            ...
        )
        chunk_item.metadata["is_chunked"] = True
        chunk_item.metadata["chunk_index"] = chunk_index
        chunk_item.metadata["total_chunks"] = total_chunks
        chunk_item.metadata["chunk_filename"] = filename
        ...
        result_items.append(chunk_item)
    return result_items

# ExtractKnowledgeStep.process_with_expansion()
def process_with_expansion(self, item: ProcessingItem) -> list[ProcessingItem]:
    """Process item with potential expansion to multiple items."""
    self._pending_expansion = None
    try:
        result = self.process(item)
    except RuntimeError:
        if self._pending_expansion:
            return self._pending_expansion
        raise
    if self._pending_expansion:
        return self._pending_expansion
    return [result]
```

### src/etl/tests/test_knowledge_transformer.py (Modified)

Added 7 new test cases for US3:

1. **TestShouldChunk** (3 tests):
   - `test_should_chunk_returns_true_for_large_conversation`: > 25000 chars
   - `test_should_chunk_returns_false_for_small_conversation`: < 25000 chars
   - `test_should_chunk_returns_false_for_non_conversation`: memories, projects

2. **TestChunkSplittingMultipleOutputs** (2 tests):
   - `test_chunked_conversation_produces_multiple_items`: Verifies N items from 1 input
   - `test_chunk_items_have_unique_ids`: Each chunk has unique item_id with #chunkN suffix

3. **TestPartialChunkFailureHandling** (2 tests):
   - `test_partial_failure_returns_successful_chunks`: Some succeed, some fail
   - `test_all_chunks_fail_returns_failed_items`: All chunks fail gracefully

## Key Design Decisions

### 1. Chunk Metadata Strategy

Each chunked ProcessingItem contains:
- `is_chunked: bool` - True for chunked conversations
- `chunk_index: int` - 0-indexed chunk number
- `total_chunks: int` - Total number of chunks
- `chunk_filename: str` - Generated filename (e.g., "Title_001.md")

### 2. Item ID Format for Chunks

Chunks use a unique ID format: `{original_id}#chunk{index}`
- Example: `uuid-123#chunk0`, `uuid-123#chunk1`, `uuid-123#chunk2`

### 3. Expansion Handling via process_with_expansion()

ExtractKnowledgeStep provides `process_with_expansion()` method that:
- Returns `list[ProcessingItem]` instead of single item
- Handles both chunked (N items) and non-chunked (1 item) cases
- Stores results in `_pending_expansion` for later retrieval

### 4. KnowledgeTransformer.run() Override

The stage overrides `run()` to:
1. Call `process_with_expansion()` on ExtractKnowledgeStep
2. For each resulting item, process through GenerateMetadata and FormatMarkdown
3. Handle partial failures (continue with successful chunks)
4. Write JSONL logs for each chunk separately

## Test Results

```
Ran 201 tests in 0.248s
OK
```

All existing tests pass. 7 new tests added for chunking functionality.

## Chunking Behavior

### Thresholds

| Metric | Value |
|--------|-------|
| Chunk size threshold | 25000 characters |
| Overlap messages | 2 messages |

### Example: 90000 char conversation

| Chunk | Content | Output |
|-------|---------|--------|
| Chunk 0 | Messages 1-25 | Title_001.md |
| Chunk 1 | Messages 24-50 (2 overlap) | Title_002.md |
| Chunk 2 | Messages 49-75 (2 overlap) | Title_003.md |
| Chunk 3 | Messages 74-100 (2 overlap) | Title_004.md |

### Chunk Metadata in Output

Each chunk file includes:
- `source_conversation: {uuid}#chunk{index}`
- `title: {Title} (Part {N})`

## Next Phase Prerequisites

Phase 5 (US4 - Translation) can now proceed with:

1. `ExtractKnowledgeStep` has chunking support
2. `KnowledgeExtractor.is_english_summary()` available
3. `KnowledgeExtractor.translate_summary()` available
4. Test patterns established for mocking Ollama

## Dependencies for Phase 5

- `KnowledgeExtractor.is_english_summary()` - Already implemented in utils
- `KnowledgeExtractor.translate_summary()` - Already implemented in utils
- `summary_translation.txt` prompt - Already copied to src/etl/prompts/

## Phase 4 Checkpoint

With Phase 4 complete:

1. **Large Conversation Chunking**: Conversations > 25000 chars are split into multiple chunks
2. **1 Input -> N Outputs**: Single conversation can produce multiple output files
3. **Chunk Metadata**: Each chunk has tracking metadata (index, total, filename)
4. **Partial Failure Handling**: If some chunks fail, successful ones still process

The import pipeline can now handle arbitrarily large conversations.
