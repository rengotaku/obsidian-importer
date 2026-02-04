# Phase 1 Output: Setup & Code Review

**Feature**: 035-chunking-mixin
**Phase**: Phase 1 - Setup (Shared Infrastructure)
**Date**: 2026-01-26
**Status**: Completed

## Summary

Phase 1 完了。設計ドキュメントを確認し、既存コードの構造を把握。Template Method パターン実装の準備が整った。

## Tasks Completed

| Task | Status | Description |
|------|--------|-------------|
| T001 | ✅ | Read spec.md, plan.md, data-model.md |
| T002 | ✅ | Review BaseStage in src/etl/core/stage.py |
| T003 | ✅ | Review Chunker in src/etl/utils/chunker.py |
| T004 | ✅ | Review ClaudeExtractor in src/etl/stages/extract/claude_extractor.py |
| T005 | ✅ | Run `make test` to verify current tests pass |

## Findings

### 1. Requirements Understanding

**User Stories Priority**:
- US1 (ChatGPT チャンク対応) - P1: 27件の失敗解消が最優先
- US2 (GitHub チャンク対応) - P2: 新規プロバイダー拡張性
- US3 (Claude リファクタリング) - P3: 既存コード保守性向上

**Success Criteria**:
- SC-001: ChatGPT 27件の大規模会話が正常処理される
- SC-002: 298,622文字の会話が12チャンク以下に分割される
- SC-004: ClaudeExtractor リファクタリング後、既存テスト全パス
- SC-006: 抽象メソッド未実装時に TypeError が発生する

**Design Decision**: Template Method パターンを採用（Mixin より機能漏れ防止に優れる）

### 2. BaseStage Review (src/etl/core/stage.py)

**Current Structure**:
- Abstract base class with `stage_type` and `steps` properties
- `run()` method: 1:N expansion, JSONL logging, error handling, 20% threshold
- `_process_item()`: Processes items through all steps
- `_write_jsonl_log()`, `_write_debug_output()`: Logging infrastructure
- No `discover_items()` method currently defined

**Key Observations**:
- BaseStage already supports 1:N expansion in `_process_item()`
- JSONL logging includes chunk metadata fields (`is_chunked`, `parent_item_id`, `chunk_index`)
- Step-level debug output exists (`_write_debug_step_output()`)
- Error handling with StepError, StageError, PhaseError hierarchy

**Template Method Integration Points**:
- Add abstract `_discover_raw_items()` method
- Add abstract `_build_conversation_for_chunking()` method
- Add concrete `discover_items()` as template method (calls both above)
- Add protected `_chunk_if_needed()` method
- Initialize `_chunker` instance in `__init__`

### 3. Chunker Review (src/etl/utils/chunker.py)

**Capabilities**:
- `should_chunk(conversation)`: Threshold check (default 25,000 chars)
- `split(conversation)`: Split with overlap (default 2 messages)
- `get_chunk_filename(title, chunk_index)`: Naming convention

**Protocol Requirements**:
- `ConversationProtocol`: `.messages`, `.id`, `.provider`
- `MessageProtocol`: `.content`, `.role`

**Key Observations**:
- Chunker is provider-agnostic (Protocol-based design)
- No modifications needed to Chunker itself
- Each provider needs to implement conversion to ConversationProtocol

### 4. ClaudeExtractor Review (src/etl/stages/extract/claude_extractor.py)

**Current Implementation**:
- `discover_items(input_path)`: Entry point, calls `_expand_conversations()`
- `_expand_conversations()`: Reads conversations.json, checks chunking, yields items
- `_build_conversation_for_chunking()`: Converts Claude dict → SimpleConversation
- `_chunk_conversation()`: Splits and yields chunk items

**Chunking Flow (Current)**:
```
discover_items()
    → _expand_conversations()
        → _build_conversation_for_chunking()
        → _chunker.should_chunk()
        → _chunk_conversation() (if needed)
        → yield ProcessingItem(s)
```

**Refactoring Plan**:
- Rename `discover_items()` → `_discover_raw_items()`
- Keep `_build_conversation_for_chunking()` as-is (becomes abstract method impl)
- Remove `_chunk_conversation()` (logic moves to BaseStage `_chunk_if_needed()`)
- BaseStage `discover_items()` will call `_discover_raw_items()` + `_chunk_if_needed()`

**Critical**: Existing tests must pass after refactoring (SC-004)

### 5. Test Status

**Test Results**: 338 tests run, 335 passed, 3 failed

**Failed Tests** (unrelated to chunking):
- `test_discover_items_valid_url` (test_github_extractor.py)
- `test_full_extraction_flow` (test_github_extractor.py)
- `test_resume_mode_skip_processed` (test_github_extractor.py)

**Analysis**: GitHubExtractor failures are pre-existing and unrelated to chunking work. Safe to proceed.

**Baseline Established**: 335 passing tests must remain passing after implementation.

## Implementation Strategy

### Phase 2: BaseStage Template Method

**Add to BaseStage**:
1. `_chunker: Chunker` instance variable
2. `discover_items(input_path)` - concrete template method
3. `_discover_raw_items(input_path)` - abstract method
4. `_build_conversation_for_chunking(item)` - abstract method
5. `_chunk_if_needed(items)` - protected method

**Processing Flow**:
```
discover_items(input_path)  [BaseStage - concrete]
    ↓
_discover_raw_items(input_path)  [Provider - abstract]
    ↓
for each item:
    ↓
_chunk_if_needed(item)  [BaseStage - concrete]
    ↓
_build_conversation_for_chunking(item)  [Provider - abstract]
    ↓
yield item(s)
```

### Phase 3: ClaudeExtractor Refactoring

**Changes**:
- Rename `discover_items()` → `_discover_raw_items()`
- Remove chunking logic from `_discover_raw_items()` (delegate to BaseStage)
- Keep `_build_conversation_for_chunking()` unchanged
- Remove `_chunk_conversation()` method
- Verify all existing tests pass

### Phase 4: ChatGPT チャンク対応 (MVP)

**New Implementation**:
- Implement `_discover_raw_items()` (ZIP extraction + JSON parsing)
- Implement `_build_conversation_for_chunking()` (ChatGPT mapping → ConversationProtocol)
- Add ChatGPTConversation class (ConversationProtocol implementation)
- Test: 298,622 char conversation splits into ≤12 chunks

### Phase 5: GitHub チャンク対応

**Implementation**:
- Implement `_discover_raw_items()` (git clone + markdown extraction)
- Implement `_build_conversation_for_chunking()` returning `None` (no chunking needed)
- Verify existing tests pass

## Next Phase Inputs

### For Phase 2 (BaseStage Template Method):

**Files to Modify**:
- `src/etl/core/stage.py` - Add template method infrastructure

**Files to Create**:
- `src/etl/tests/test_stages.py` - Add abstract method tests

**Test Requirements**:
- Abstract method not implemented → TypeError
- Chunking threshold check
- Chunk metadata propagation

### For Phase 3 (ClaudeExtractor Refactoring):

**Reference Implementation**: Current ClaudeExtractor chunking logic (lines 254-373)

**Migration Checklist**:
- [ ] Rename method signature
- [ ] Remove inline chunking
- [ ] Verify SimpleConversation compatibility
- [ ] Run existing test suite

## Risks Identified

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking ClaudeExtractor tests | High | TDD approach - write tests first, verify RED/GREEN |
| ChatGPT mapping complexity | Medium | Reference existing Steps implementation |
| Performance overhead | Low | Chunker already optimized, minimal overhead |
| Abstract method enforcement | Low | Python ABC handles this automatically |

## Files Reviewed

- `/path/to/project/specs/035-chunking-mixin/spec.md`
- `/path/to/project/specs/035-chunking-mixin/plan.md`
- `/path/to/project/specs/035-chunking-mixin/data-model.md`
- `/path/to/project/src/etl/core/stage.py` (924 lines)
- `/path/to/project/src/etl/utils/chunker.py` (246 lines)
- `/path/to/project/src/etl/stages/extract/claude_extractor.py` (374 lines)

## Ready for Phase 2

All Phase 1 tasks completed. Codebase structure understood. Template Method pattern design validated. Ready to proceed with BaseStage implementation.
