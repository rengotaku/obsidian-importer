# Phase 2 Output: Foundational - BaseExtractor Template Completion

**Completed**: 2026-01-30
**Phase**: Foundational - BaseExtractor template completion (Priority: P1)

## Summary

- Phase: Phase 2 - BaseExtractor template completion
- Tasks: 11/11 completed (T005-T015)
- Status: Complete
- FAIL tests resolved: 3 tests now PASS

## Implementation Overview

Implemented the `_build_chunk_messages()` hook in BaseExtractor to complete the Template Method pattern. This structural change allows child extractors to customize chunk message formatting without overriding `_chunk_if_needed()`.

## Changes Made

### src/etl/core/extractor.py

**Added `_build_chunk_messages()` hook method**:

```python
def _build_chunk_messages(self, chunk: Any, conversation_dict: dict) -> list[dict] | None:
    """Build chat_messages for chunked conversation (provider-specific hook).

    This is the third hook in the Template Method pattern.
    Allows providers to customize chat_messages structure after chunking.

    Args:
        chunk: Chunked conversation object.
        conversation_dict: Original conversation dict (before chunking).

    Returns:
        List of message dicts to set in chunk_conv["chat_messages"], or None to preserve item.content.
    """
    return None
```

**Updated `_chunk_if_needed()` to call the hook**:

```python
# Parse original content as conversation dict
import json
conversation_dict = json.loads(item.content)

for chunk_index, chunk_obj in enumerate(chunked.chunks):
    # Create a copy of the conversation dict for this chunk
    chunk_conv = dict(conversation_dict)

    # Call hook to build chunk-specific chat_messages
    messages = self._build_chunk_messages(chunk_obj, chunk_conv)
    if messages is not None:
        chunk_conv["chat_messages"] = messages

    # Serialize chunk conversation back to JSON
    chunk_content = json.dumps(chunk_conv, ensure_ascii=False)

    # Create new ProcessingItem for this chunk
    chunk_item = ProcessingItem(
        # ... metadata ...
        content=chunk_content,  # Use updated chunk content
    )
```

## Test Results

### Phase 2 Tests (All PASS)

All 8 Phase 2 tests passed:

| Test | Status |
|------|--------|
| test_base_extractor_has_build_chunk_messages_method | PASS |
| test_build_chunk_messages_returns_none_by_default | PASS |
| test_child_class_can_override_build_chunk_messages | PASS |
| test_chunk_if_needed_calls_build_chunk_messages | PASS |
| test_chunk_if_needed_preserves_content_when_hook_returns_none | PASS |
| test_base_extractor_stage_type_is_extract | PASS |
| test_child_extractor_inherits_stage_type | PASS |
| test_stage_type_not_overridden_in_child | PASS |

### Regression Test Results

- Total tests: 492 (8 new Phase 2 tests added)
- Failures/Errors: 38 (same as Phase 1 baseline - no regressions)
- New test file: `src/etl/tests/test_extractor_template.py`

The 38 pre-existing failures are unrelated to Phase 2 changes:
- `_max_records_per_file` tests expect 1000 but actual is 5000 (pre-existing)
- Some import/CLI validation tests (pre-existing)
- Resume mode tests (pre-existing)

## Template Method Pattern Benefits

The completed BaseExtractor template now provides:

1. **Single Responsibility**: `_discover_raw_items()` handles discovery, `_build_chunk_messages()` handles chunk formatting, `_chunk_if_needed()` orchestrates chunking
2. **No Override Needed**: Child classes only need to implement hooks, not override template methods
3. **Structural Duplication Prevention**: Impossible to duplicate processing because the template enforces 1:N expansion only in `discover_items()`

## Next Phase: Phase 3 (US1)

Phase 3 will apply this template to ChatGPTExtractor to eliminate the N² duplication issue:

1. Expand `_discover_raw_items()` to include ZIP reading and parsing
2. Delete redundant Steps (ReadZipStep, ParseConversationsStep, ConvertFormatStep)
3. Implement `_build_chunk_messages()` for ChatGPT-specific message structure
4. Delete `_chunk_if_needed()` override
5. Delete `stage_type` override

**Expected outcome**: ChatGPT import processes N conversations → N records (no duplication)

## Files Modified

- `src/etl/core/extractor.py` - Added `_build_chunk_messages()` hook and updated `_chunk_if_needed()` to call it

## Files Created

- `specs/041-fix-extract-dedup/tasks/ph2-output.md` - This output document
