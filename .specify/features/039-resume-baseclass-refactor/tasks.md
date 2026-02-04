# Tasks: Resume機能の基底クラス集約リファクタリング

**Input**: Design documents from `/specs/039-resume-baseclass-refactor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (ItemStatus.SKIPPED → FILTERED 名称変更)

**Purpose**: Enum変更と全ファイルの参照更新

### 入力
- [X] T001 Read plan.md and data-model.md to understand ItemStatus change scope

### 実装
- [X] T002 Change `SKIPPED = "skipped"` to `FILTERED = "filtered"` in src/etl/core/status.py
- [X] T003 [P] Update SKIPPED → FILTERED in src/etl/core/models.py
- [X] T004 [P] Update SKIPPED → FILTERED in src/etl/core/step.py
- [X] T005 [P] Update SKIPPED → FILTERED in src/etl/core/stage.py
- [X] T006 [P] Update SKIPPED → FILTERED in src/etl/stages/extract/chatgpt_extractor.py
- [X] T007 [P] Update SKIPPED → FILTERED in src/etl/stages/transform/knowledge_transformer.py
- [X] T008 [P] Update SKIPPED → FILTERED in src/etl/stages/load/session_loader.py
- [X] T009 [P] Update SKIPPED → FILTERED in src/etl/phases/import_phase.py
- [X] T010 [P] Update SKIPPED → FILTERED in src/etl/phases/organize_phase.py

### テスト更新
- [X] T011 [P] Update SKIPPED → FILTERED in src/etl/tests/test_resume_mode.py
- [X] T012 [P] Update SKIPPED → FILTERED in src/etl/tests/test_knowledge_transformer.py
- [X] T013 [P] Update SKIPPED → FILTERED in src/etl/tests/test_stages.py
- [X] T014 [P] Update SKIPPED → FILTERED in src/etl/tests/test_import_phase.py
- [X] T015 [P] Update SKIPPED → FILTERED in src/etl/tests/test_chatgpt_transform_integration.py
- [X] T016 [P] Update SKIPPED → FILTERED in src/etl/tests/test_too_large_context.py
- [X] T017 [P] Update SKIPPED → FILTERED in src/etl/tests/test_models.py

### 検証
- [X] T018 Run `make test` to verify all tests pass after SKIPPED → FILTERED change
- [X] T019 Generate phase output: /path/to/project/specs/039-resume-baseclass-refactor/tasks/ph1-output.md

**Checkpoint**: ItemStatus.FILTERED が全ファイルで使用され、テストが通過

---

## Phase 2: User Story 1 - 中断からの再開（Resume Mode） (Priority: P1) 🎯 MVP

**Goal**: BaseStage.run() にResumeロジックを集約し、処理済みアイテムをスキップ

**Independent Test**: 10件のアイテムを処理中に5件目で強制終了し、再開時に6件目から処理が開始されることを確認

### 入力
- [x] T020 Read previous phase output: /path/to/project/specs/039-resume-baseclass-refactor/tasks/ph1-output.md

### テスト実装 (RED)
- [x] T021 [US1] Update test_resume_skips_completed_items to verify no status change (remove SKIPPED assertion) in src/etl/tests/test_resume_mode.py
- [x] T022 [US1] Update test_resume_filter_only to verify items are filtered, not yielded in src/etl/tests/test_resume_mode.py
- [x] T023 Verify `make test` FAIL (RED) - tests should fail because current implementation still yields skipped items
- [x] T024 Generate RED output: /path/to/project/specs/039-resume-baseclass-refactor/red-tests/ph2-test.md

### 実装 (GREEN)
- [x] T025 Read RED tests: /path/to/project/specs/039-resume-baseclass-refactor/red-tests/ph2-test.md
- [x] T026 [US1] Refactor BaseStage.run() to filter completed items without status change in src/etl/core/stage.py
  - Remove: `item.status = ItemStatus.SKIPPED`
  - Remove: `item.metadata["skipped_reason"] = "resume_mode"`
  - Remove: `skipped_items.append(item)` and `yield from skipped_items`
  - Add: Generator filter `items = (item for item in items if not ctx.completed_cache.is_completed(item.item_id))`
- [x] T027 Verify `make test` PASS (GREEN)

### 検証
- [x] T028 Verify `make coverage` ≥80%
- [x] T029 Generate phase output: /path/to/project/specs/039-resume-baseclass-refactor/tasks/ph2-output.md

**Checkpoint**: Resume時に処理済みアイテムがフィルタされ、ステータス変更なし

---

## Phase 3: User Story 2 - 継承クラスの実装簡素化 (Priority: P2)

**Goal**: run_with_skip() メソッドを削除し、継承クラスがResumeを意識しない設計に移行

**Independent Test**: 新規のStage実装でrun_with_skip()メソッドなしでResume機能が動作することを確認

### 入力
- [x] T030 Read previous phase output: /path/to/project/specs/039-resume-baseclass-refactor/tasks/ph2-output.md

### テスト実装 (RED)
- [x] T031 [US2] Remove or update test_run_with_skip tests in src/etl/tests/test_resume_mode.py (not test_knowledge_transformer.py)
- [x] T032 [US2] No run_with_skip tests in src/etl/tests/test_stages.py (confirmed via grep)
- [x] T033 Verify `make test` FAIL (RED) - 2 tests fail: TestTransformItemSkip, TestLoadItemSkip
- [x] T034 Generate RED output: /path/to/project/specs/039-resume-baseclass-refactor/red-tests/ph3-test.md

### 実装 (GREEN)
- [x] T035 Read RED tests: /path/to/project/specs/039-resume-baseclass-refactor/red-tests/ph3-test.md
- [x] T036 [P] [US2] Delete run_with_skip() method (lines 656-702) in src/etl/stages/transform/knowledge_transformer.py
- [x] T037 [P] [US2] Delete run_with_skip() method (lines 341-388) in src/etl/stages/load/session_loader.py
- [x] T038 Verify `make test` PASS (GREEN)

### 検証
- [x] T039 Verify `make coverage` ≥80%
- [x] T040 Generate phase output: /path/to/project/specs/039-resume-baseclass-refactor/tasks/ph3-output.md

**Checkpoint**: run_with_skip() が削除され、継承クラスはResumeを意識しない

---

## Phase 4: Resume前提条件チェックと進捗表示

**Purpose**: Extract完了チェックとResume開始時の進捗表示を実装

### 入力
- [x] T041 Read previous phase output: /path/to/project/specs/039-resume-baseclass-refactor/tasks/ph3-output.md

### テスト実装 (RED)
- [x] T042 Add test_resume_requires_extract_complete in src/etl/tests/test_import_phase.py
- [x] T043 Add test_resume_shows_progress_message in src/etl/tests/test_import_phase.py
- [x] T044 Verify `make test` FAIL (RED)
- [x] T045 Generate RED output: /path/to/project/specs/039-resume-baseclass-refactor/red-tests/ph4-test.md

### 実装 (GREEN)
- [x] T046 Read RED tests: /path/to/project/specs/039-resume-baseclass-refactor/red-tests/ph4-test.md
- [x] T047 Implement Extract completion check in ImportPhase.run() in src/etl/phases/import_phase.py
  - Check: session.json exists
  - Check: expected_total_item_count is set
  - Check: extract/output/ has files
  - Error message: "Error: Extract stage not completed. Cannot resume."
- [x] T048 Implement Resume progress display in ImportPhase.run() in src/etl/phases/import_phase.py
  - Read total from session.json → expected_total_item_count
  - Count completed from pipeline_stages.jsonl → status="success"
  - Display: "Resume mode: {completed}/{total} items already completed, starting from item {completed+1}"
- [x] T049 Verify `make test` PASS (GREEN)

### 検証
- [x] T050 Verify `make coverage` ≥80%
- [x] T051 Generate phase output: /path/to/project/specs/039-resume-baseclass-refactor/tasks/ph4-output.md

**Checkpoint**: Resume時に前提条件チェックと進捗表示が機能

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: ドキュメント更新と最終検証

### 入力
- [x] T052 Read previous phase output: /path/to/project/specs/039-resume-baseclass-refactor/tasks/ph4-output.md

### 実装
- [x] T053 Update CLAUDE.md Active Technologies section with current feature info
- [x] T054 Run quickstart.md validation scenarios manually
- [x] T055 Verify all edge cases from spec.md:
  - 強制終了がStep実行中に発生: 未完了として再処理対象
  - pipeline_stages.jsonl破損: 警告ログを出力し、破損行をスキップして処理継続
  - Extract stageでの1:N展開中断: 部分展開されたチャンクは無視し、元アイテムから再展開
  - Extract stage未完了でResume: エラーメッセージを表示して終了

### 検証
- [x] T056 Run `make test` final verification
- [x] T057 Generate phase output: /path/to/project/specs/039-resume-baseclass-refactor/tasks/ph5-output.md

**Checkpoint**: 全機能が動作し、ドキュメントが更新済み

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (US1 - Resume Mode)**: Depends on Phase 1 completion
- **Phase 3 (US2 - 継承クラス簡素化)**: Depends on Phase 2 completion
- **Phase 4 (Resume前提条件)**: Depends on Phase 3 completion
- **Phase 5 (Polish)**: Depends on Phase 4 completion

### User Story Dependencies

- **User Story 1 (P1)**: Resume機能の基盤。Phase 2で実装
- **User Story 2 (P2)**: US1の完了が前提。Phase 3で実装

### Parallel Opportunities

**Phase 1**: T003-T010（実装）とT011-T017（テスト更新）は並列実行可能

**Phase 2-4**: TDDフローのため、各フェーズ内は順次実行

**Phase 3**: T036とT037は並列実行可能（異なるファイル）

---

## Parallel Example: Phase 1

```bash
# Launch all source file updates in parallel:
Task: "Update SKIPPED → FILTERED in src/etl/core/models.py"
Task: "Update SKIPPED → FILTERED in src/etl/core/step.py"
Task: "Update SKIPPED → FILTERED in src/etl/core/stage.py"
Task: "Update SKIPPED → FILTERED in src/etl/stages/extract/chatgpt_extractor.py"
Task: "Update SKIPPED → FILTERED in src/etl/stages/transform/knowledge_transformer.py"
Task: "Update SKIPPED → FILTERED in src/etl/stages/load/session_loader.py"
Task: "Update SKIPPED → FILTERED in src/etl/phases/import_phase.py"
Task: "Update SKIPPED → FILTERED in src/etl/phases/organize_phase.py"

# Launch all test file updates in parallel:
Task: "Update SKIPPED → FILTERED in src/etl/tests/test_resume_mode.py"
Task: "Update SKIPPED → FILTERED in src/etl/tests/test_knowledge_transformer.py"
Task: "Update SKIPPED → FILTERED in src/etl/tests/test_stages.py"
Task: "Update SKIPPED → FILTERED in src/etl/tests/test_import_phase.py"
Task: "Update SKIPPED → FILTERED in src/etl/tests/test_chatgpt_transform_integration.py"
Task: "Update SKIPPED → FILTERED in src/etl/tests/test_too_large_context.py"
Task: "Update SKIPPED → FILTERED in src/etl/tests/test_models.py"
```

---

## Implementation Strategy

### MVP First (Phase 1-2 Only)

1. Complete Phase 1: ItemStatus名称変更
2. Complete Phase 2: Resume Mode基盤実装
3. **STOP and VALIDATE**: Resumeが処理済みアイテムをスキップすることを確認
4. 本番利用開始可能

### Full Implementation

1. Phase 1 → Phase 2 → MVP達成
2. Phase 3 → 継承クラス簡素化
3. Phase 4 → 前提条件チェックと進捗表示
4. Phase 5 → ドキュメント更新と最終検証

---

## Notes

- 後方互換性は不要（内部リファクタリング）
- スキップアイテムの `pipeline_stages.jsonl` への記録はスコープ外
- 既存テストの動作を維持しつつ、アサーションを更新
