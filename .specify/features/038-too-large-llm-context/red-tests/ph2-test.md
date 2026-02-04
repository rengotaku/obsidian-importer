# Phase 2 RED Tests

## Summary

- Phase: Phase 2 - User Story 1 & 2 (LLM Context-based too_large Judgment)
- FAIL test count: 5 (4 ERROR + 1 FAIL)
- Test file: `src/etl/tests/test_too_large_context.py`

## FAIL Test List

| Test File | Test Method | Expected Behavior | Failure Reason |
|-----------|-------------|-------------------|----------------|
| test_too_large_context.py | `test_calculate_llm_context_size_basic` | Calculate LLM context size from message text | ERROR: `_calculate_llm_context_size` method does not exist |
| test_too_large_context.py | `test_calculate_llm_context_size_empty_messages` | Return ~200 (header) for 0 messages | ERROR: `_calculate_llm_context_size` method does not exist |
| test_too_large_context.py | `test_calculate_llm_context_size_null_text` | Handle null/empty text fields (count as 0 chars) | ERROR: `_calculate_llm_context_size` method does not exist |
| test_too_large_context.py | `test_calculate_llm_context_size_missing_text_field` | Handle missing text field (count as 0 chars) | ERROR: `_calculate_llm_context_size` method does not exist |
| test_too_large_context.py | `test_too_large_judgment_with_llm_context` | Item with JSON > 25K but LLM context < 25K should NOT be skipped | FAIL: Current logic uses `len(item.content)` instead of LLM context |

## PASS Tests (Already Working)

These tests pass because they test existing bypass conditions:

| Test File | Test Method | Description |
|-----------|-------------|-------------|
| test_too_large_context.py | `test_too_large_judgment_still_skips_large` | Items with LLM context > 25K are skipped |
| test_too_large_context.py | `test_chunk_enabled_bypasses_judgment` | chunk_enabled=True bypasses too_large check |
| test_too_large_context.py | `test_is_chunked_bypasses_judgment` | is_chunked=True bypasses too_large check |

## Implementation Hints

### For `_calculate_llm_context_size()` (US2)

Add this method to `ExtractKnowledgeStep` in `src/etl/stages/transform/knowledge_transformer.py`:

```python
def _calculate_llm_context_size(self, data: dict) -> int:
    """Calculate the actual LLM context size from conversation data.

    Args:
        data: Parsed conversation JSON.

    Returns:
        Estimated LLM context size (characters).
    """
    HEADER_SIZE = 200  # Fixed header (~200 chars)
    LABEL_OVERHEAD = 15  # "[User]\n" or "[Assistant]\n"

    messages = data.get("chat_messages", [])

    # Sum of message text fields
    message_size = sum(
        len(msg.get("text", "") or "")  # Handle None
        for msg in messages
    )

    # Label overhead per message
    label_size = len(messages) * LABEL_OVERHEAD

    return HEADER_SIZE + message_size + label_size
```

### For too_large Judgment Logic (US1)

Modify `ExtractKnowledgeStep.process()` to:

1. Parse JSON before the too_large check
2. Use `_calculate_llm_context_size()` instead of `len(item.content)`
3. Reuse parsed data for subsequent processing

```python
# Before (current):
if not chunk_enabled and not is_chunked and item.content:
    content_size = len(item.content)
    if content_size > self._chunk_size:
        # Skip...

# After (new):
if not chunk_enabled and not is_chunked and item.content:
    data = json.loads(item.content)  # Parse JSON first
    llm_context_size = self._calculate_llm_context_size(data)
    if llm_context_size > self._chunk_size:
        # Skip...
    # Reuse 'data' for later processing
```

### Key Changes

1. Move JSON parsing before too_large check (line ~193)
2. Add `_calculate_llm_context_size()` method
3. Store parsed `data` and reuse it (avoid double parsing)

## FAIL Output Example

```
======================================================================
ERROR: test_calculate_llm_context_size_basic (src.etl.tests.test_too_large_context.TestCalculateLlmContextSize)
Basic message size calculation test (T009).
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_too_large_context.py", line 53, in test_calculate_llm_context_size_basic
    result = step._calculate_llm_context_size(conversation_data)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'ExtractKnowledgeStep' object has no attribute '_calculate_llm_context_size'

======================================================================
FAIL: test_too_large_judgment_with_llm_context (src.etl.tests.test_too_large_context.TestTooLargeJudgmentWithLlmContext)
Previously skipped item now processable with new judgment (T012).
----------------------------------------------------------------------
AssertionError: 'too_large' == 'too_large' : Item should NOT be skipped with new LLM context-based judgment

----------------------------------------------------------------------
Ran 8 tests in 0.003s

FAILED (failures=1, errors=4)
```

## Test Data Notes

### JSON Overhead Example

The key test (`test_too_large_judgment_with_llm_context`) demonstrates the problem:

- 3 messages x 6000 chars = 18,000 chars (LLM context)
- JSON with duplicated `text` in `content[0].text` + metadata = >25,000 chars
- Current: Skipped (JSON > 25K)
- Expected: Processed (LLM context < 25K)

### Formula

```
LLM_context_size = HEADER (200) + sum(msg.text) + LABEL (15) * msg_count
```

## Next Steps

1. Implement `_calculate_llm_context_size()` method
2. Modify judgment logic in `process()` to use new method
3. Ensure JSON is parsed once and reused
4. Run `make test` to verify GREEN state
