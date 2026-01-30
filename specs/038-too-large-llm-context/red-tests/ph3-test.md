# Phase 3 RED Tests

## Summary

- Phase: Phase 3 - ChatGPT Compatibility (P1)
- Test Status: **PASS (Already Compatible)**
- Test File: `src/etl/tests/test_too_large_context.py`

## Test Outcome

The test `test_calculate_llm_context_size_chatgpt_format` **PASSED immediately** without any code changes. This confirms that the `_calculate_llm_context_size()` implementation is already ChatGPT-compatible.

### Why the Test Passed

According to research.md (Section 5):

> ChatGPT exports use 'mapping' structure but ExtractKnowledgeStep receives normalized data with 'chat_messages' array after extraction.
> Both Claude and ChatGPT use 'text' field for message content.
> **Compatibility**: The calculation logic can be shared.

The current implementation in `_calculate_llm_context_size()` uses:

```python
messages = data.get("chat_messages", [])
message_size = sum(
    len(msg.get("text", "") or "")
    for msg in messages
)
```

This works for both:
- **Claude format**: Native `chat_messages` array with `text` field
- **ChatGPT format**: Normalized by `OpenAIExtractor` to `chat_messages` array with `text` field

## Test Details

### Test Method

| Test File | Test Method | Expected Behavior | Status |
|-----------|-------------|-------------------|--------|
| `test_too_large_context.py` | `test_calculate_llm_context_size_chatgpt_format` | Calculate LLM context size for ChatGPT-normalized data | PASS |

### Test Data

```python
chatgpt_data = {
    "uuid": "chatgpt-uuid",
    "name": "ChatGPT Conversation",
    "created_at": "2026-01-27T10:00:00Z",
    "chat_messages": [
        {"sender": "human", "text": "Hello ChatGPT"},       # 13 chars
        {"sender": "assistant", "text": "Hello! How can I help you?"},  # 26 chars
        {"sender": "human", "text": "What's the weather?"},  # 19 chars
    ],
}
```

### Expected Calculation

| Component | Value |
|-----------|-------|
| HEADER_SIZE | 200 |
| Message text sum | 13 + 26 + 19 = 58 |
| Label overhead | 3 * 15 = 45 |
| **Total** | **303** |

### Test Result

```
test_calculate_llm_context_size_chatgpt_format (src.etl.tests.test_too_large_context.TestCalculateLlmContextSize.test_calculate_llm_context_size_chatgpt_format)
Test _calculate_llm_context_size with ChatGPT export format (T025). ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

## Implementation Hints

**No implementation changes needed** - the existing code is already ChatGPT-compatible.

The GREEN phase (T028-T030) can:
1. Skip code changes (T029)
2. Simply verify compatibility is maintained
3. Proceed to verification phase

## All Tests Status

| Test Class | Test Count | Status |
|------------|------------|--------|
| `TestCalculateLlmContextSize` | 5 (including new ChatGPT test) | PASS |
| `TestTooLargeJudgmentWithLlmContext` | 4 | PASS |
| **Total** | **9** | **PASS** |

## Next Steps

Since the test passed immediately:

1. **GREEN Phase (T028-T030)**: Mark as complete - no code changes needed
2. **Verification Phase (T031-T032)**: Confirm all tests pass, generate phase output

This is the expected outcome based on research.md findings - the abstraction at the extractor level normalizes both Claude and ChatGPT data to the same `chat_messages` format before reaching `_calculate_llm_context_size()`.
