# Tasks: LLMインポート エラーデバッグ改善

**Input**: Design documents from `/specs/021-import-error-debug/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Test tasks are included as this is a modification to existing tested codebase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project root**: `/path/to/project/`
- **Source**: `development/scripts/llm_import/`
- **Tests**: `development/scripts/llm_import/tests/`
- **Output**: `.staging/@plan/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create feature branch `021-import-error-debug` from current branch
- [x] T002 [P] Create `development/scripts/llm_import/common/error_writer.py` with module docstring
- [x] T003 [P] Create `development/scripts/llm_import/common/folder_manager.py` with module docstring
- [x] T004 [P] Create `development/scripts/llm_import/tests/test_error_writer.py` with test class skeleton
- [x] T005 [P] Create `development/scripts/llm_import/tests/test_folder_manager.py` with test class skeleton

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Implement `FolderManager` class in `development/scripts/llm_import/common/folder_manager.py`
  - `__init__(base_path: Path)` - @plan ベースパス設定
  - `get_session_dir(session_type: str, session_id: str) -> Path` - セッションフォルダパス取得
  - `create_session_structure(session_type: str, session_id: str) -> dict[str, Path]` - サブフォルダ作成
  - Session types: "import", "organize", "test"
  - Subfolders for import: parsed/conversations/, output/, errors/

- [x] T007 Add unit tests for `FolderManager` in `development/scripts/llm_import/tests/test_folder_manager.py`
  - `test_get_session_dir_import` - import タイプのパス生成
  - `test_get_session_dir_organize` - organize タイプのパス生成
  - `test_create_session_structure` - サブフォルダ作成確認

- [x] T008 Run `make test` to verify FolderManager tests pass

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - エラー原因の特定 (Priority: P1) 🎯 MVP

**Goal**: JSONパースエラー発生時に原文とLLM出力をファイル出力し、エラー原因を特定可能にする

**Independent Test**: エラー発生時に `@plan/import/{session_id}/errors/` にエラー詳細ファイルが出力される

### Tests for User Story 1

- [x] T009 [P] [US1] Add `test_error_detail_creation` in `development/scripts/llm_import/tests/test_error_writer.py`
- [x] T010 [P] [US1] Add `test_write_error_file` in `development/scripts/llm_import/tests/test_error_writer.py`
- [x] T011 [P] [US1] Add `test_error_file_truncation` (10MB limit) in `development/scripts/llm_import/tests/test_error_writer.py`

### Implementation for User Story 1

- [x] T012 [US1] Implement `ErrorDetail` dataclass in `development/scripts/llm_import/common/error_writer.py`
  - Fields: session_id, conversation_id, conversation_title, timestamp, error_type, error_message, error_position, error_context, original_content, llm_prompt, llm_output, stage

- [x] T013 [US1] Implement `write_error_file()` function in `development/scripts/llm_import/common/error_writer.py`
  - Input: ErrorDetail, output_dir: Path
  - Output: Markdown file at `{output_dir}/{conversation_id}.md`
  - Format: data-model.md の Error Detail File 形式
  - 10MB トランケーション対応

- [x] T014 [US1] Extend `ExtractionResult` to include prompt info in `development/scripts/llm_import/common/knowledge_extractor.py`
  - Add `user_prompt: str | None = None` field
  - Store prompt in extract() method results

- [x] T015 [US1] Modify `KnowledgeExtractor.extract()` to store prompt in result in `development/scripts/llm_import/common/knowledge_extractor.py`
  - Set `user_prompt=user_message` in ExtractionResult

- [x] T016 [US1] Modify error handling in `cmd_process()` to call `write_error_file()` in `development/scripts/llm_import/cli.py`
  - Import error_writer module
  - On Phase 2 error: create ErrorDetail from ExtractionResult
  - Call write_error_file() with session errors/ directory

- [x] T017 [US1] Run `make test` to verify all US1 tests pass

**Checkpoint**: User Story 1 complete - エラー詳細ファイル出力機能が動作

---

## Phase 4: User Story 2 - @planフォルダの構造改善 (Priority: P1)

**Goal**: @planフォルダを organize/, import/, test/ のサブフォルダに整理し、セッション管理を改善

**Independent Test**: インポート処理実行後、ファイルが `@plan/import/{session_id}/` に配置される

### Tests for User Story 2

- [x] T018 [P] [US2] Add `test_session_dir_new_structure` in `development/scripts/llm_import/tests/test_folder_manager.py`
- [x] T019 [P] [US2] Add `test_session_logger_with_folder_manager` in `development/scripts/llm_import/tests/test_cli.py`

### Implementation for User Story 2

- [x] T020 [US2] Modify `SessionLogger.__init__()` to use `FolderManager` in `development/scripts/llm_import/common/session_logger.py`
  - Import FolderManager
  - Add `folder_manager: FolderManager | None` parameter
  - Store folder_manager instance

- [x] T021 [US2] Modify `SessionLogger.start_session()` to create new folder structure in `development/scripts/llm_import/common/session_logger.py`
  - Use folder_manager.create_session_structure() if available
  - Return dict with parsed/, output/, errors/ paths
  - Backwards compatible: if no folder_manager, use legacy behavior

- [x] T022 [US2] Add `SessionLogger.get_paths()` method in `development/scripts/llm_import/common/session_logger.py`
  - Returns dict with session subdirectory paths
  - Keys: "session", "parsed", "output", "errors"

- [x] T023 [US2] Modify `cmd_process()` to use new folder structure in `development/scripts/llm_import/cli.py`
  - Create FolderManager with @plan base path
  - Pass to SessionLogger
  - Use session paths for Phase 1 output (parsed/)
  - Use session paths for error files (errors/)

- [x] T024 [US2] Run `make test` to verify all US2 tests pass

**Checkpoint**: User Story 2 complete - 新フォルダ構造でファイルが配置される

---

## Phase 5: User Story 3 - 中間ファイルの保持 (Priority: P1)

**Goal**: Phase 1出力（parsed）とPhase 2出力（@index移動前）を保持し、デバッグ可能にする

**Independent Test**: インポート処理後、parsed/ と output/ の両方にファイルが残っている

### Tests for User Story 3

- [x] T025 [P] [US3] Add `test_intermediate_files_retained` in `development/scripts/llm_import/tests/test_cli.py`
- [x] T026 [P] [US3] Add `test_output_copied_to_index` in `development/scripts/llm_import/tests/test_cli.py`

### Implementation for User Story 3

- [x] T027 [US3] Modify Phase 2 output logic in `cmd_process()` in `development/scripts/llm_import/cli.py`
  - Write Phase 2 output to session output/ directory first
  - Copy (not move) to @index/ directory
  - Keep original in output/

- [x] T028 [US3] Remove intermediate file deletion logic in `cmd_process()` in `development/scripts/llm_import/cli.py`
  - Remove `intermediate_files` list
  - Remove deletion loop at end of function
  - Keep `--no-delete` flag for backwards compatibility (no-op now)

- [x] T029 [US3] Update session.json to track intermediate files in `development/scripts/llm_import/common/session_logger.py`
  - Add `intermediate_files` to finalize() output
  - Track parsed/ and output/ file counts

- [x] T030 [US3] Run `make test` to verify all US3 tests pass

**Checkpoint**: User Story 3 complete - 中間ファイルが保持される

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integration testing and final validation

- [x] T031 Run full integration test with `make llm-import LIMIT=5`
- [x] T032 Verify error files are created in `@plan/import/{session_id}/errors/`
- [x] T033 Verify parsed files are in `@plan/import/{session_id}/parsed/conversations/`
- [x] T034 Verify output files are in `@plan/import/{session_id}/output/`
- [x] T035 Verify files are also copied to `@index/`
- [x] T036 Run `make test` to verify all tests pass
- [x] T037 Update quickstart.md with actual paths if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US2 (folder structure) should complete before US1 and US3 for optimal integration
  - US1 and US3 can proceed in parallel after US2
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - Uses FolderManager for error output path
- **User Story 2 (P1)**: Can start after Foundational - Core folder structure change
- **User Story 3 (P1)**: Can start after Foundational - Uses new folder structure from US2

### Recommended Execution Order

```
Phase 1 → Phase 2 → Phase 4 (US2) → Phase 3 (US1) + Phase 5 (US3) → Phase 6
```

US2（フォルダ構造）を先に完了することで、US1（エラー出力）とUS3（中間ファイル保持）が新構造を利用可能。

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/dataclasses before functions
- Core implementation before integration
- Story complete before moving to next

### Parallel Opportunities

- T002-T005 (Setup): All can run in parallel
- T009-T011 (US1 Tests): All can run in parallel
- T018-T019 (US2 Tests): All can run in parallel
- T025-T026 (US3 Tests): All can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Add test_error_detail_creation in tests/test_error_writer.py"
Task: "Add test_write_error_file in tests/test_error_writer.py"
Task: "Add test_error_file_truncation in tests/test_error_writer.py"

# After tests fail, implement in sequence:
Task: "Implement ErrorDetail dataclass"
Task: "Implement write_error_file function"
Task: "Modify cmd_process to call write_error_file"
```

---

## Implementation Strategy

### MVP First (User Story 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (FolderManager)
3. Complete Phase 4: User Story 2 (Folder Structure)
4. **STOP and VALIDATE**: Test folder structure independently
5. Proceed to US1 and US3

### Incremental Delivery

1. Complete Setup + Foundational → FolderManager ready
2. Add User Story 2 → Test independently → New folder structure works
3. Add User Story 1 → Test independently → Error files output works
4. Add User Story 3 → Test independently → Intermediate files retained
5. Each story adds debugging capability without breaking previous stories

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[エラー発生] → [ErrorDetail作成] → [Markdown生成] → [ファイル書込]
      ↓              ↓                ↓               ↓
    テスト         テスト           テスト          テスト
```

**チェックリスト**:
- [ ] ErrorDetail 作成のテスト
- [ ] Markdown 生成のテスト
- [ ] ファイル書込のテスト（パス、トランケーション）
- [ ] End-to-End テスト（エラー発生→ファイル出力）

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- 既存の `--no-delete` フラグは後方互換性のため残すが、動作は no-op に変更
