# Phase 3 Output: ClaudeExtractor リファクタリング完了

**Feature**: 035-chunking-mixin
**Phase**: Phase 3 - User Story 3 - ClaudeExtractor Template Method Refactoring
**Date**: 2026-01-26
**Status**: ✅ COMPLETED

## Summary

Phase 3 successfully completed ClaudeExtractor refactoring to implement Template Method pattern from BaseExtractor. All 15 new refactoring tests pass, and all 25 existing ClaudeExtractor tests continue to pass, demonstrating 100% backward compatibility.

## Task Completion

| Task | Status | Description |
|------|--------|-------------|
| T018 | ✅ | Read previous phase output |
| T019 | ✅ | Create test skeleton (16 test methods) |
| T020 | ✅ | Implement test assertions in all 16 methods |
| T021 | ✅ | Comprehensive test coverage implemented |
| T022 | ✅ | RED state verified (4 failures as expected) |
| T023 | ✅ | Implement `_discover_raw_items()` |
| T024 | ✅ | Implement `_build_conversation_for_chunking()` |
| T025 | ✅ | Override `_chunk_if_needed()` for chunk-specific JSON |
| T026 | ✅ | Remove old methods (`_expand_conversations`, `_chunk_conversation`) |
| T027 | ✅ | GREEN state verified (15/15 tests passing) |
| T028 | ✅ | Existing tests verified (25/25 passing) |
| T029 | ✅ | Phase output generated |

## Implementation Details

### Refactored Methods

#### `_discover_raw_items(input_path: Path) -> Iterator[ProcessingItem]`

**Purpose**: Discover raw conversation items without chunking (Template Method hook)

**Implementation**:
- Reads `conversations.json` from input directory
- Parses JSON and validates structure
- Yields one ProcessingItem per conversation
- NO chunking logic (delegated to BaseExtractor.discover_items())
- Error handling for invalid JSON or missing files

**Key Changes**:
- Removed chunking logic from discovery phase
- Simplified to pure extraction of raw conversations
- Delegates chunking to template method

#### `_build_conversation_for_chunking(item: ProcessingItem) -> SimpleConversation | None`

**Purpose**: Convert ProcessingItem to SimpleConversation for Chunker (Template Method hook)

**Implementation**:
- Parses JSON content from item
- Converts chat_messages to SimpleMessage objects
- Creates SimpleConversation instance
- Returns None if content is invalid (skips chunking)

**Key Changes**:
- Changed signature from `dict` to `ProcessingItem`
- Added error handling (returns None instead of raising)
- Works with BaseExtractor's template method

#### `_chunk_if_needed(item: ProcessingItem) -> list[ProcessingItem]`

**Purpose**: Create chunk-specific JSON content (override BaseExtractor default)

**Implementation**:
- Checks if chunking needed via Chunker.should_chunk()
- If not needed: marks as not chunked, returns single item
- If needed: splits conversation via Chunker.split()
- Creates chunk-specific JSON for each chunk (only messages for that chunk)
- Generates chunk metadata (chunk_index, total_chunks, parent_item_id)

**Why Override**:
- BaseExtractor's default preserves original content
- ClaudeExtractor needs chunk-specific JSON (only messages for that chunk)
- Maintains backward compatibility with existing chunking behavior

### Removed Methods

- `_expand_conversations()` - logic moved to `_discover_raw_items()`
- `_chunk_conversation()` - logic moved to `_chunk_if_needed()`

### Test Coverage

**New Tests** (15 total):

1. **Abstract Method Implementation** (4 tests):
   - `test_claude_extractor_implements_discover_raw_items`
   - `test_claude_extractor_implements_build_conversation_for_chunking`
   - `test_discover_raw_items_returns_iterator`
   - `test_discover_raw_items_does_not_chunk`

2. **Chunking Behavior** (4 tests):
   - `test_small_conversation_not_chunked`
   - `test_large_conversation_chunked` (multi-message)
   - `test_chunked_items_have_correct_metadata`
   - `test_chunk_overlap_messages_included`

3. **Backward Compatibility** (3 tests):
   - `test_existing_tests_still_pass`
   - `test_same_output_for_same_input`
   - `test_discover_items_backward_compatible`

4. **Edge Cases** (4 tests):
   - `test_empty_conversations_json`
   - `test_missing_conversations_json`
   - `test_conversation_at_chunk_threshold`
   - `test_single_message_large_conversation`

## Test Results

**New Refactoring Tests**: 15/15 PASSING ✅
**Existing ClaudeExtractor Tests**: 25/25 PASSING ✅
**Total Tests in Suite**: 354 (3 failures unrelated to ClaudeExtractor)

**Pre-existing Failures** (not related to this phase):
- 3 GitHubExtractor tests (same as Phase 2)

## Files Modified

### Core

- `src/etl/stages/extract/claude_extractor.py`:
  - Implemented `_discover_raw_items()` (67 lines)
  - Implemented `_build_conversation_for_chunking()` (28 lines)
  - Overrode `_chunk_if_needed()` (65 lines)
  - Removed `_expand_conversations()` (76 lines removed)
  - Removed `_chunk_conversation()` (63 lines removed)
  - Net change: +21 lines, improved clarity

### Tests

- `src/etl/tests/test_claude_extractor_refactoring.py`:
  - Added 15 comprehensive test methods
  - 4 test classes (Abstract Methods, Chunking, Behavior, Edge Cases)
  - ~400 lines of test code

### Tasks

- `specs/035-chunking-mixin/tasks.md`:
  - Marked 12 tasks complete (T018-T029)

## Chunker Behavior Findings

During implementation, we clarified Chunker edge case behavior:

1. **Threshold Boundary** (`>= 25000` not `> 25000`):
   - Conversations at exactly 25,000 chars ARE chunked
   - `should_chunk()` uses `>=` comparison

2. **Large Single Messages**:
   - Chunker cannot split within a single message
   - Creates 1 chunk for oversized single messages
   - Marked as `is_chunked=true` with `total_chunks=1`
   - Warning logged: "単一メッセージが chunk_size を超過"

3. **Multi-Message Chunking**:
   - Splits at message boundaries only
   - Includes overlap messages for context
   - Creates multiple chunks as expected

## Backward Compatibility Verification

✅ All existing ClaudeExtractor behavior maintained:
- Discovers conversations from `conversations.json`
- Chunks large conversations (>25,000 chars)
- Creates chunk-specific JSON content
- Generates correct metadata (chunk_index, total_chunks, parent_item_id)
- Handles error cases gracefully

## Success Criteria Met

From spec.md:

- ✅ SC-004: ClaudeExtractor tests pass after refactoring (25/25 passing)
- ✅ SC-006: TypeError on missing abstract method (verified in BaseExtractor tests)
- ✅ Template Method pattern correctly implemented
- ✅ Chunking delegated to BaseExtractor
- ✅ Chunk-specific content properly created

## Next Phase Preparation

**Phase 4 (ChatGPT チャンク対応)** can now proceed:
- BaseExtractor template pattern established
- ClaudeExtractor serves as reference implementation
- Pattern verified: `_discover_raw_items()` + `_build_conversation_for_chunking()` + `_chunk_if_needed()`

**Files Ready for Phase 4**:
- `src/etl/core/extractor.py` - BaseExtractor (template pattern)
- `src/etl/stages/extract/claude_extractor.py` - Reference implementation
- `src/etl/stages/extract/chatgpt_extractor.py` - Ready to refactor

## Lessons Learned

1. **Template Method Pattern**: Successfully separated chunking concern from extraction
2. **Chunker Limitations**: Cannot split within single messages (by design)
3. **Test-First Approach**: RED-GREEN cycle caught edge cases early
4. **Override When Needed**: BaseExtractor provides default, but providers can override for specific needs

## Checkpoint

**Phase 3**: ✅ COMPLETED - ClaudeExtractor リファクタリング完了

**Status**: Ready to proceed to Phase 4 (ChatGPT チャンク対応)

**Confidence**: HIGH - All tests passing, backward compatibility verified
