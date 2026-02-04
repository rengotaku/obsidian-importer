# Tasks: Resume モードの再設計

**Input**: Design documents from `/specs/037-resume-mode-redesign/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

```text
src/etl/
├── core/           # フレームワーク層
├── phases/         # Phase 実装
├── stages/         # Stage 実装
├── cli/            # CLI コマンド
└── tests/          # テスト
```

---

## Phase 1: Setup (メインエージェント実行)

**Purpose**: 出力ディレクトリの初期化

- [X] T001 Create task output directories: `specs/037-resume-mode-redesign/tasks/`, `specs/037-resume-mode-redesign/red-tests/`
- [X] T002 Generate phase output: `specs/037-resume-mode-redesign/tasks/ph1-output.md`

---

## Phase 2: Foundational - CompletedItemsCache (TDD)

**Purpose**: Resume モードの基盤となる CompletedItemsCache クラスの実装

**⚠️ CRITICAL**: US1, US2, US3 の実装前にこの Phase を完了する必要がある

### 入力
- [X] T003 Read previous phase output: `specs/037-resume-mode-redesign/tasks/ph1-output.md`

### テスト実装 (RED)
- [X] T004 [P] Implement test_completed_items_cache_empty in `src/etl/tests/test_resume_mode.py`
- [X] T005 [P] Implement test_completed_items_cache_with_success in `src/etl/tests/test_resume_mode.py`
- [X] T006 [P] Implement test_completed_items_cache_ignores_failed in `src/etl/tests/test_resume_mode.py`
- [X] T007 [P] Implement test_completed_items_cache_stage_filter in `src/etl/tests/test_resume_mode.py`
- [X] T008 [P] Implement test_completed_items_cache_corrupted_jsonl in `src/etl/tests/test_resume_mode.py`
- [X] T009 Verify `make test` FAIL (RED)
- [X] T010 Generate RED output: `specs/037-resume-mode-redesign/red-tests/ph2-test.md`

### 実装 (GREEN)
- [X] T011 Read RED tests: `specs/037-resume-mode-redesign/red-tests/ph2-test.md`
- [X] T012 Implement CompletedItemsCache dataclass in `src/etl/core/models.py`
- [X] T013 Implement CompletedItemsCache.from_jsonl() in `src/etl/core/models.py`
- [X] T014 Implement CompletedItemsCache.is_completed() in `src/etl/core/models.py`
- [X] T015 Verify `make test` PASS (GREEN)

### 検証
- [X] T016 Verify `make coverage` ≥80% for CompletedItemsCache
- [X] T017 Generate phase output: `specs/037-resume-mode-redesign/tasks/ph2-output.md`

**Checkpoint**: CompletedItemsCache が動作し、JSONL から処理済みアイテムを読み込める

---

## Phase 3: User Story 1 - 中断したインポートの再開 (Priority: P1) 🎯 MVP

**Goal**: 処理済みアイテムをスキップして未処理のアイテムのみを処理する

**Independent Test**: `--session SESSION_ID` のみでインポートを実行し、処理済みアイテムがスキップされることを確認

### 入力
- [x] T018 Read previous phase output: `specs/037-resume-mode-redesign/tasks/ph2-output.md`

### テスト実装 (RED)
- [x] T019 [P] [US1] Implement test_skip_completed_item in `src/etl/tests/test_resume_mode.py`
- [x] T020 [P] [US1] Implement test_skip_not_logged in `src/etl/tests/test_resume_mode.py`
- [x] T021 [P] [US1] Implement test_extract_stage_skip in `src/etl/tests/test_resume_mode.py`
- [x] T022 [P] [US1] Implement test_transform_item_skip in `src/etl/tests/test_resume_mode.py`
- [x] T023 [P] [US1] Implement test_load_item_skip in `src/etl/tests/test_resume_mode.py`
- [x] T024 [P] [US1] Implement test_resume_partial_completion in `src/etl/tests/test_resume_mode.py`
- [x] T024a [P] [US1] Implement test_chunked_item_all_success_required in `src/etl/tests/test_resume_mode.py`
- [x] T024b [P] [US1] Implement test_chunked_item_partial_failure_retry in `src/etl/tests/test_resume_mode.py`
- [x] T025 [P] [US1] Implement test_resume_all_completed in `src/etl/tests/test_resume_mode.py`
- [x] T026 Verify `make test` FAIL (RED)
- [x] T027 Generate RED output: `specs/037-resume-mode-redesign/red-tests/ph3-test.md`

### 実装 (GREEN)
- [x] T028 Read RED tests: `specs/037-resume-mode-redesign/red-tests/ph3-test.md`
- [x] T029 [US1] Add completed_cache to StageContext in `src/etl/core/stage.py`
- [x] T030 [US1] Implement skip logic in BaseStage.run() in `src/etl/core/stage.py`
- [x] T031 [US1] Implement Extract Stage skip in ImportPhase.run() in `src/etl/phases/import_phase.py`
- [x] T032 [US1] Add skip_count tracking in BaseStage in `src/etl/core/stage.py`
- [x] T033 [US1] Update console output with skip count in `src/etl/cli/commands/import_cmd.py`
- [x] T034 Verify `make test` PASS (GREEN) - Resume Mode tests all pass (23/23)

### 検証
- [ ] T035 Verify `make coverage` ≥80% for US1 components
- [ ] T036 [US1] Manual test: Run import, interrupt, resume with --session
- [ ] T037 Generate phase output: `specs/037-resume-mode-redesign/tasks/ph3-output.md`

**Checkpoint**: US1 完了 - 処理済みアイテムがスキップされ、未処理のみ処理される

---

## Phase 4: User Story 2 - 失敗アイテムの自動リトライ (Priority: P2)

**Goal**: 前回失敗したアイテムが Resume 時に再処理される

**Independent Test**: 3件成功、2件失敗のセッションで Resume を実行し、成功3件はスキップ、失敗2件は再処理されることを確認

### 入力
- [x] T038 Read previous phase output: `specs/037-resume-mode-redesign/tasks/ph3-output.md`

### テスト実装 (RED)
- [x] T039 [P] [US2] Implement test_retry_failed_items in `src/etl/tests/test_resume_mode.py`
- [x] T040 [P] [US2] Implement test_skip_success_retry_failed in `src/etl/tests/test_resume_mode.py`
- [x] T041 [P] [US2] Implement test_retry_skipped_items in `src/etl/tests/test_resume_mode.py`
- [x] T042 Verify `make test` FAIL (RED) - **PASS**: Logic already implemented in Phase 3
- [x] T043 Generate RED output: `specs/037-resume-mode-redesign/red-tests/ph4-test.md`

### 実装 (GREEN)
- [x] T044 Read RED tests: `specs/037-resume-mode-redesign/red-tests/ph4-test.md`
- [x] T045 [US2] Verify skip logic only skips status="success" in `src/etl/core/models.py`
- [x] T046 [US2] Update statistics calculation in `src/etl/cli/utils/pipeline_stats.py`
- [x] T047 Verify `make test` PASS (GREEN)

### 検証
- [x] T048 Verify `make coverage` ≥80% for US2 components
- [x] T049 [US2] Manual test: Create session with failures, resume, verify retry
- [x] T050 Generate phase output: `specs/037-resume-mode-redesign/tasks/ph4-output.md`

**Checkpoint**: US2 完了 - 失敗アイテムが Resume 時に再処理される

---

## Phase 5: User Story 3 - クラッシュからの復旧 (Priority: P3)

**Goal**: クラッシュ後に中断箇所から処理を再開できる

**Independent Test**: 処理中にプロセスを強制終了し、再実行時に中断箇所から再開されることを確認

### 入力
- [x] T051 Read previous phase output: `specs/037-resume-mode-redesign/tasks/ph4-output.md`

### テスト実装 (RED)
- [x] T052 [P] [US3] Implement test_resume_after_crash in `src/etl/tests/test_resume_mode.py`
- [x] T053 [P] [US3] Implement test_corrupted_log_recovery in `src/etl/tests/test_resume_mode.py`
- [x] T054 [P] [US3] Implement test_partial_log_recovery in `src/etl/tests/test_resume_mode.py`
- [x] T055 Verify `make test` FAIL (RED) - **PASS**: Logic already implemented in Phase 2/3
- [x] T056 Generate RED output: `specs/037-resume-mode-redesign/red-tests/ph5-test.md`

### 実装 (GREEN)
- [x] T057 Read RED tests: `specs/037-resume-mode-redesign/red-tests/ph5-test.md`
- [x] T058 [US3] Add robust JSONL parsing with error handling in `src/etl/core/models.py`
- [x] T059 [US3] Add warning log for corrupted lines in `src/etl/core/models.py`
- [x] T060 [US3] Ensure JSONL flush after each write in `src/etl/core/stage.py`
- [x] T061 Verify `make test` PASS (GREEN)

### 検証
- [x] T062 Verify `make coverage` ≥80% for US3 components
- [x] T063 [US3] Manual test: Simulate crash, verify recovery
- [x] T064 Generate phase output: `specs/037-resume-mode-redesign/tasks/ph5-output.md`

**Checkpoint**: US3 完了 - クラッシュ後の Resume が動作する

---

## Phase 6: Polish & Cross-Cutting Concerns (phase-executor のみ)

**Purpose**: DEBUG モード廃止、CLI 更新、ドキュメント整備

### 入力
- [x] T065 Read previous phase output: `specs/037-resume-mode-redesign/tasks/ph5-output.md`

### 実装
- [x] T066 [P] Remove --debug flag from CLI (deprecated warning) in `src/etl/cli/commands/import_cmd.py`
- [x] T067 [P] Make debug_mode always True (remove conditional checks) in `src/etl/core/stage.py`
- [x] T068 [P] Update status command with skip count in `src/etl/cli/commands/status_cmd.py`
- [x] T069 [P] Update existing tests for debug_mode removal in `src/etl/tests/test_*.py`
- [x] T070 Run `make test` to verify all tests pass
- [x] T071 Run `make lint` to verify code quality

### 検証
- [x] T072 Run quickstart.md validation scenarios
- [x] T073 Verify SC-001: No duplicate LLM calls for completed items
- [x] T074 Verify SC-003: 1000 log records load <1 second
- [x] T075 Generate phase output: `specs/037-resume-mode-redesign/tasks/ph6-output.md`

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational)
                       ↓
              ┌────────┼────────┐
              ↓        ↓        ↓
         Phase 3   Phase 4   Phase 5
          (US1)    (US2)     (US3)
              └────────┼────────┘
                       ↓
                 Phase 6 (Polish)
```

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2 (CompletedItemsCache)
- **User Story 2 (P2)**: Depends on Phase 2, builds on US1 skip logic
- **User Story 3 (P3)**: Depends on Phase 2, independent of US1/US2

### Within Each User Story

1. テスト実装 (RED) → assertions 完備 → FAIL 確認
2. 実装 (GREEN) → テスト PASS
3. 検証 → カバレッジ確認

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T004-T008: 全てのテストスケルトンを並列作成可能

**Phase 3 (US1)**:
- T019-T025: 全てのテストを並列実装可能

**Phase 4 (US2)**:
- T039-T041: テストを並列実装可能

**Phase 5 (US3)**:
- T052-T054: テストを並列実装可能

**Phase 6 (Polish)**:
- T066-T069: 独立したファイル変更のため並列可能

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CompletedItemsCache)
3. Complete Phase 3: User Story 1 (中断からの再開)
4. **STOP and VALIDATE**: `--session` で Resume が動作することを確認
5. Deploy/demo if ready

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. Add US1 → Test independently → **MVP リリース可能**
3. Add US2 → Test independently → 失敗リトライ対応
4. Add US3 → Test independently → クラッシュ復旧対応
5. Phase 6 → Polish and cleanup

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[JSONL読込] → [キャッシュ構築] → [スキップ判定] → [統計計算]
     ↓            ↓              ↓            ↓
   テスト       テスト          テスト       テスト
```

**チェックリスト**:
- [ ] JSONL パース部分のテスト（破損対応含む）
- [ ] CompletedItemsCache 構築のテスト
- [ ] スキップ判定ロジックのテスト
- [ ] 統計計算のテスト
- [ ] End-to-End テスト（Resume シナリオ）

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
