# Tasks: 大規模ファイルのチャンク分割処理

**Input**: Design documents from `/specs/020-large-file-chunking/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: テスト含む（既存テストファイルへの追加）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `development/scripts/llm_import/`
- **Tests**: `development/scripts/llm_import/tests/`

---

## Phase 1: Setup

**Purpose**: 新規モジュールの作成とデータ構造定義

- [ ] T001 Create chunker.py with data classes (Chunk, ChunkResult, ChunkedConversation) in development/scripts/llm_import/common/chunker.py
- [ ] T002 [P] Export new classes in development/scripts/llm_import/common/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Chunker クラスのコア機能実装（全ユーザーストーリーの基盤）

**⚠️ CRITICAL**: User Story 実装前に完了必須

- [ ] T003 Implement Chunker.__init__() with chunk_size and overlap_messages params in development/scripts/llm_import/common/chunker.py
- [ ] T004 Implement Chunker.should_chunk() method in development/scripts/llm_import/common/chunker.py
- [ ] T005 Implement Chunker.split() with message boundary logic in development/scripts/llm_import/common/chunker.py
- [ ] T006 Implement Chunker.get_chunk_filename() for numbered output files in development/scripts/llm_import/common/chunker.py

**Checkpoint**: Chunker core ready - user story integration can begin

---

## Phase 3: User Story 1 - 大規模会話の自動分割処理 (Priority: P1) 🎯 MVP

**Goal**: 25,000文字以上の会話を自動分割→各チャンク個別ファイル出力

**Independent Test**: 50,000文字以上の会話処理がエラーなく完了

### Tests for User Story 1

- [ ] T007 [P] [US1] Add test_should_chunk_large_conversation in development/scripts/llm_import/tests/test_chunker.py
- [ ] T008 [P] [US1] Add test_split_creates_chunks_at_message_boundary in development/scripts/llm_import/tests/test_chunker.py
- [ ] T009 [P] [US1] Add test_split_includes_overlap in development/scripts/llm_import/tests/test_chunker.py
- [ ] T010 [P] [US1] Add test_get_chunk_filename_format in development/scripts/llm_import/tests/test_chunker.py
- [ ] T011 [P] [US1] Add test_should_not_chunk_small_conversation in development/scripts/llm_import/tests/test_chunker.py

### Implementation for User Story 1

- [ ] T012 [US1] Modify KnowledgeExtractor.extract() to detect large conversations in development/scripts/llm_import/common/knowledge_extractor.py
- [ ] T013 [US1] Add _extract_chunked() method to KnowledgeExtractor for chunk processing in development/scripts/llm_import/common/knowledge_extractor.py
- [ ] T014 [US1] Add _process_single_chunk() helper method in development/scripts/llm_import/common/knowledge_extractor.py
- [ ] T015 [US1] Handle edge case: single message exceeds chunk_size in development/scripts/llm_import/common/chunker.py
- [ ] T016 [US1] Add test_extractor_with_chunked_conversation in development/scripts/llm_import/tests/test_knowledge_extractor.py

**Checkpoint**: 大規模ファイルの自動分割処理が完全に機能

---

## Phase 4: User Story 2 - 処理進捗の可視化 (Priority: P2)

**Goal**: チャンク処理中の進捗表示

**Independent Test**: ログに「チャンク N/M 処理中」形式で進捗表示

### Implementation for User Story 2

- [ ] T017 [US2] Add progress logging in _extract_chunked() showing chunk N/M in development/scripts/llm_import/common/knowledge_extractor.py
- [ ] T018 [US2] Add chunk splitting log (total chunks, total chars) in development/scripts/llm_import/common/knowledge_extractor.py
- [ ] T019 [US2] Add completion log for each chunk in development/scripts/llm_import/common/knowledge_extractor.py

**Checkpoint**: 進捗ログが表示され、処理状況が可視化される

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: エッジケース対応とテスト検証

- [ ] T020 [P] Add test_empty_conversation_raises_error in development/scripts/llm_import/tests/test_chunker.py
- [ ] T021 [P] Add test_chunk_failure_continues_other_chunks in development/scripts/llm_import/tests/test_chunker.py
- [ ] T022 Run make test to verify all tests pass
- [ ] T023 Run make process with large file to verify end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on User Story 1 (uses same code paths)
- **Polish (Phase 5)**: Depends on all user stories

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Adds logging to US1 implementation - logically after US1

### Within Each User Story

- Tests SHOULD be written first (TDD approach)
- Core implementation before edge case handling
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
```bash
T001 Create chunker.py
T002 [P] Export in __init__.py  # Can run in parallel with T001
```

**Phase 3 (User Story 1 - Tests)**:
```bash
T007 test_should_chunk_large_conversation
T008 test_split_creates_chunks_at_message_boundary
T009 test_split_includes_overlap
T010 test_get_chunk_filename_format
T011 test_should_not_chunk_small_conversation
# All tests can run in parallel (different test cases)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006)
3. Complete Phase 3: User Story 1 (T007-T016)
4. **STOP and VALIDATE**: Test with large conversation file
5. Deploy if functional

### Incremental Delivery

1. Setup + Foundational → Chunker ready
2. User Story 1 → Test → Large files now processable (MVP!)
3. User Story 2 → Test → Progress visible during processing
4. Polish → Test → Edge cases handled

---

## Summary

| Phase | Tasks | Parallel Tasks |
|-------|-------|----------------|
| Setup | 2 | 1 |
| Foundational | 4 | 0 |
| User Story 1 | 10 | 5 (tests) |
| User Story 2 | 3 | 0 |
| Polish | 4 | 2 |
| **Total** | **23** | **8** |

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (16 tasks)
