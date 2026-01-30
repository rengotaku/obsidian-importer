# Tasks: エラーファイルのリトライ機能

**Input**: Design documents from `/specs/018-retry-errors/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: ユニットテストを含む（既存テスト構造に従う）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project**: `development/scripts/llm_import/` - 既存モジュール構造
- **Tests**: `development/scripts/llm_import/tests/`

---

## Phase 1: Setup

**Purpose**: 新規ファイル作成と基本構造

- [ ] T001 Create retry.py module in development/scripts/llm_import/common/retry.py
- [ ] T002 [P] Create test_retry.py in development/scripts/llm_import/tests/test_retry.py

---

## Phase 2: Foundational (Core Retry Logic)

**Purpose**: リトライ処理の基盤となる関数群（すべての User Story で使用）

**⚠️ CRITICAL**: User Story の実装前に完了必須

- [ ] T003 Implement find_session_dirs() in development/scripts/llm_import/common/retry.py
- [ ] T004 Implement load_errors_json() in development/scripts/llm_import/common/retry.py
- [ ] T005 [P] Implement SessionInfo dataclass in development/scripts/llm_import/common/retry.py
- [ ] T006 Implement get_sessions_with_errors() in development/scripts/llm_import/common/retry.py
- [ ] T007 [P] Add unit tests for find_session_dirs() in development/scripts/llm_import/tests/test_retry.py
- [ ] T008 [P] Add unit tests for load_errors_json() in development/scripts/llm_import/tests/test_retry.py
- [ ] T009 Run make test to verify foundational tests pass

**Checkpoint**: 基盤関数が完成、User Story 実装開始可能

---

## Phase 3: User Story 1 - エラーファイルの自動リトライ (Priority: P1) 🎯 MVP

**Goal**: `make retry SESSION=xxx` で指定セッションのエラーをリトライ実行

**Independent Test**: `make retry SESSION=import_20260116_203426` を実行し、errors.json のファイルのみが処理されることを確認

### Implementation for User Story 1

- [ ] T010 [US1] Add --retry-errors argument to create_parser() in development/scripts/llm_import/cli.py
- [ ] T011 [US1] Add --session argument to create_parser() in development/scripts/llm_import/cli.py
- [ ] T012 [US1] Add --timeout argument to create_parser() in development/scripts/llm_import/cli.py
- [ ] T013 [US1] Implement validate_session() in development/scripts/llm_import/common/retry.py
- [ ] T014 [US1] Implement get_phase1_output_path() in development/scripts/llm_import/common/retry.py
- [ ] T015 [US1] Add source_session parameter to SessionLogger.__init__() in development/scripts/llm_import/common/session_logger.py
- [ ] T016 [US1] Update SessionLogger.start_session() to write source_session to session.json in development/scripts/llm_import/common/session_logger.py
- [ ] T017 [US1] Add write_retry_header() method to SessionLogger in development/scripts/llm_import/common/session_logger.py
- [ ] T018 [US1] Implement process_retry() main function in development/scripts/llm_import/common/retry.py
- [ ] T019 [US1] Add retry mode handling to main() in development/scripts/llm_import/cli.py
- [ ] T020 [US1] Add retry target to Makefile
- [ ] T021 [P] [US1] Add unit tests for validate_session() in development/scripts/llm_import/tests/test_retry.py
- [ ] T022 [P] [US1] Add unit tests for process_retry() in development/scripts/llm_import/tests/test_retry.py
- [ ] T023 [US1] Run make test to verify US1 tests pass

**Checkpoint**: `make retry SESSION=xxx` が動作、新しいセッションが作成される

---

## Phase 4: User Story 2 - セッション指定によるリトライ (Priority: P2)

**Goal**: セッション未指定時に一覧表示、1件のみなら自動選択

**Independent Test**: `make retry` を実行し、複数セッション時は一覧表示、1件のみなら自動実行されることを確認

### Implementation for User Story 2

- [ ] T024 [US2] Implement format_session_list() in development/scripts/llm_import/common/retry.py
- [ ] T025 [US2] Implement select_session_interactive() in development/scripts/llm_import/common/retry.py
- [ ] T026 [US2] Update retry mode handling in main() for session selection logic in development/scripts/llm_import/cli.py
- [ ] T027 [P] [US2] Add unit tests for format_session_list() in development/scripts/llm_import/tests/test_retry.py
- [ ] T028 [P] [US2] Add unit tests for select_session_interactive() in development/scripts/llm_import/tests/test_retry.py
- [ ] T029 [US2] Run make test to verify US2 tests pass

**Checkpoint**: `make retry` がセッション一覧を表示、または自動選択で実行

---

## Phase 5: User Story 3 - プレビューモードでのリトライ確認 (Priority: P3)

**Goal**: `make retry ACTION=preview` でリトライ対象を確認（処理は実行しない）

**Independent Test**: `make retry ACTION=preview SESSION=xxx` でエラー一覧が表示され、ファイルが変更されないことを確認

### Implementation for User Story 3

- [ ] T030 [US3] Implement format_error_preview() in development/scripts/llm_import/common/retry.py
- [ ] T031 [US3] Implement preview_retry() in development/scripts/llm_import/common/retry.py
- [ ] T032 [US3] Update retry mode handling in main() to support --preview in development/scripts/llm_import/cli.py
- [ ] T033 [US3] Update Makefile retry target for ACTION=preview support
- [ ] T034 [P] [US3] Add unit tests for format_error_preview() in development/scripts/llm_import/tests/test_retry.py
- [ ] T035 [P] [US3] Add unit tests for preview_retry() in development/scripts/llm_import/tests/test_retry.py
- [ ] T036 [US3] Run make test to verify US3 tests pass

**Checkpoint**: `make retry ACTION=preview` が動作、エラー一覧を表示

---

## Phase 6: Polish & Edge Cases

**Purpose**: エッジケース対応と最終検証

- [ ] T037 [P] Add error handling for missing errors.json in development/scripts/llm_import/common/retry.py
- [ ] T038 [P] Add error handling for invalid JSON in errors.json in development/scripts/llm_import/common/retry.py
- [ ] T039 [P] Add error handling for missing Phase 1 output files in development/scripts/llm_import/common/retry.py
- [ ] T040 [P] Add edge case tests in development/scripts/llm_import/tests/test_retry.py
- [ ] T041 Run make test to verify all tests pass
- [ ] T042 Run make check and make lint to verify code quality
- [ ] T043 Manual integration test: make retry with real session data

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational; can parallel with US1 but builds on US1's CLI changes
- **User Story 3 (Phase 5)**: Depends on Foundational; can parallel with US1/US2
- **Polish (Phase 6)**: Depends on all user stories

### User Story Dependencies

- **User Story 1 (P1)**: Core retry functionality - MVP
- **User Story 2 (P2)**: Session selection - extends US1's CLI handling
- **User Story 3 (P3)**: Preview mode - independent, uses US1's retry logic read-only

### Within Each User Story

- CLI arguments before implementation
- Core functions before integration
- Tests after implementation (verify)
- `make test` at story checkpoint

### Parallel Opportunities

Within Phase 2:
- T005, T007, T008 can run in parallel

Within Phase 3 (US1):
- T021, T022 can run in parallel after T018

Within Phase 4 (US2):
- T027, T028 can run in parallel after T025

Within Phase 5 (US3):
- T034, T035 can run in parallel after T031

Within Phase 6:
- T037, T038, T039, T040 can all run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# After T003, T004, T006 complete sequentially:
Task: "Add unit tests for find_session_dirs()" [T007]
Task: "Add unit tests for load_errors_json()" [T008]
```

## Parallel Example: User Story 1

```bash
# After T018 (process_retry) completes:
Task: "Add unit tests for validate_session()" [T021]
Task: "Add unit tests for process_retry()" [T022]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T009)
3. Complete Phase 3: User Story 1 (T010-T023)
4. **STOP and VALIDATE**: `make retry SESSION=xxx` works
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. User Story 1 → `make retry SESSION=xxx` works (MVP!)
3. User Story 2 → `make retry` shows session list or auto-selects
4. User Story 3 → `make retry ACTION=preview` works
5. Polish → Edge cases handled, all tests pass

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing KnowledgeExtractor is reused for Phase 2 processing
