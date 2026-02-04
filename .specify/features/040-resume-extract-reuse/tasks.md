# Tasks: Resume モード Extract Output 再利用

**Input**: Design documents from `/specs/040-resume-extract-reuse/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/etl/` at repository root
- Tests: `src/etl/tests/`
- Core: `src/etl/core/`
- Phases: `src/etl/phases/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create feature branch `040-resume-extract-reuse` from current branch
- [X] T002 Create output directories: `specs/040-resume-extract-reuse/tasks/` and `specs/040-resume-extract-reuse/red-tests/`
- [X] T003 Generate phase output: `specs/040-resume-extract-reuse/tasks/ph1-output.md`

---

## Phase 2: User Story 3 - Extract Output 固定ファイル名とレコード分割 (Priority: P3 → 先行実装)

**Goal**: Extract stage の output ファイル名を固定パターン（data-dump-{番号4桁}.jsonl）にし、1000 レコードごとに分割

**Why first**: US1、US2 が依存する固定ファイル名パターンを先に実装する必要がある

**Independent Test**: Extract stage を実行し、output に data-dump-0001.jsonl 形式でファイルが生成されることを確認

### 入力
- [X] T004 Read previous phase output: `specs/040-resume-extract-reuse/tasks/ph1-output.md`

### テスト実装 (RED)
- [X] T005 [P] [US3] Add test for fixed filename pattern in `src/etl/tests/test_stages.py`
- [X] T006 [P] [US3] Add test for record splitting (1000 records) in `src/etl/tests/test_stages.py`
- [X] T007 [P] [US3] Add test for file index increment in `src/etl/tests/test_stages.py`
- [X] T008 Verify `make test` FAIL (RED)
- [X] T009 Generate RED output: `specs/040-resume-extract-reuse/red-tests/ph2-test.md`

### 実装 (GREEN)
- [X] T010 Read RED tests: `specs/040-resume-extract-reuse/red-tests/ph2-test.md`
- [X] T011 [US3] Add `_output_file_index`, `_output_record_count`, `_max_records_per_file` attributes to BaseStage in `src/etl/core/stage.py`
- [X] T012 [US3] Modify `_write_output_item()` to use fixed filename pattern `data-dump-{番号4桁}.jsonl` in `src/etl/core/stage.py`
- [X] T013 [US3] Implement record splitting logic (1000 records per file) in `src/etl/core/stage.py`
- [X] T014 Verify `make test` PASS (GREEN)

### 検証
- [X] T015 Verify `make test` passes all tests
- [X] T016 Generate phase output: `specs/040-resume-extract-reuse/tasks/ph2-output.md`

**Checkpoint**: Extract output は固定ファイル名で分割出力される

---

## Phase 3: User Story 2 - FW による Resume 制御フローの一元管理 (Priority: P2)

**Goal**: BasePhaseOrchestrator クラス（Template Method パターン）で Resume ロジックを一元管理

**Independent Test**: BasePhaseOrchestrator を継承したクラスでフックメソッドのみ実装し、run() が正しく動作することを確認

### 入力
- [X] T017 Read previous phase output: `specs/040-resume-extract-reuse/tasks/ph2-output.md`

### テスト実装 (RED)
- [X] T018 [P] [US2] Create test file `src/etl/tests/test_phase_orchestrator.py`
- [X] T019 [P] [US2] Add test for BasePhaseOrchestrator abstract methods in `src/etl/tests/test_phase_orchestrator.py`
- [X] T020 [P] [US2] Add test for run() method calling hooks in correct order in `src/etl/tests/test_phase_orchestrator.py`
- [X] T021 [P] [US2] Add test for _should_load_extract_from_output() method in `src/etl/tests/test_phase_orchestrator.py`
- [X] T022 [P] [US2] Add test for _load_extract_items_from_output() method in `src/etl/tests/test_phase_orchestrator.py`
- [X] T023 Verify `make test` FAIL (RED)
- [X] T024 Generate RED output: `specs/040-resume-extract-reuse/red-tests/ph3-test.md`

### 実装 (GREEN)
- [X] T025 Read RED tests: `specs/040-resume-extract-reuse/red-tests/ph3-test.md`
- [X] T026 [US2] Create `src/etl/core/phase_orchestrator.py` with BasePhaseOrchestrator class
- [X] T027 [US2] Implement abstract property `phase_type` in BasePhaseOrchestrator
- [X] T028 [US2] Implement abstract methods `_run_extract_stage()`, `_run_transform_stage()`, `_run_load_stage()` in BasePhaseOrchestrator
- [X] T029 [US2] Implement `_should_load_extract_from_output()` method to check for data-dump-*.jsonl in BasePhaseOrchestrator
- [X] T030 [US2] Implement `_load_extract_items_from_output()` method to restore ProcessingItem from JSONL in BasePhaseOrchestrator
- [X] T031 [US2] Implement concrete `run()` method with Template Method pattern in BasePhaseOrchestrator
- [X] T032 Verify `make test` PASS (GREEN)

### 検証
- [X] T033 Verify `make test` passes all tests
- [X] T034 Generate phase output: `specs/040-resume-extract-reuse/tasks/ph3-output.md`

**Checkpoint**: BasePhaseOrchestrator が作成され、Template Method パターンで動作する

---

## Phase 4: User Story 2 続き - ImportPhase と OrganizePhase の継承変更 (Priority: P2)

**Goal**: 既存の Phase クラスを BasePhaseOrchestrator 継承に変更

**Independent Test**: ImportPhase と OrganizePhase の両方で既存機能が動作することを確認

### 入力
- [X] T035 Read previous phase output: `specs/040-resume-extract-reuse/tasks/ph3-output.md`

### テスト実装 (RED)
- [X] T036 [P] [US2] Add test for ImportPhase inheriting BasePhaseOrchestrator in `src/etl/tests/test_phase_orchestrator.py`
- [X] T037 [P] [US2] Add test for OrganizePhase inheriting BasePhaseOrchestrator in `src/etl/tests/test_phase_orchestrator.py`
- [X] T038 [P] [US2] Add test for ImportPhase hook methods in `src/etl/tests/test_phase_orchestrator.py`
- [X] T039 Verify `make test` FAIL (RED)
- [X] T040 Generate RED output: `specs/040-resume-extract-reuse/red-tests/ph4-test.md`

### 実装 (GREEN)
- [X] T041 Read RED tests: `specs/040-resume-extract-reuse/red-tests/ph4-test.md`
- [X] T042 [US2] Modify ImportPhase to inherit from BasePhaseOrchestrator in `src/etl/phases/import_phase.py`
- [X] T043 [US2] Implement `_run_extract_stage()` hook in ImportPhase
- [X] T044 [US2] Implement `_run_transform_stage()` hook in ImportPhase
- [X] T045 [US2] Implement `_run_load_stage()` hook in ImportPhase
- [X] T046 [US2] Remove old `run()` method from ImportPhase (now provided by BasePhaseOrchestrator)
- [X] T047 [US2] Modify OrganizePhase to inherit from BasePhaseOrchestrator in `src/etl/phases/organize_phase.py`
- [X] T048 [US2] Implement hook methods in OrganizePhase
- [X] T049 [US2] Remove old `run()` method from OrganizePhase
- [X] T050 Verify `make test` PASS (GREEN)

### 検証
- [X] T051 Verify `make test` passes all tests
- [X] T052 Run `make import INPUT=... PROVIDER=claude LIMIT=1` to verify ImportPhase works
- [X] T053 Generate phase output: `specs/040-resume-extract-reuse/tasks/ph4-output.md`

**Checkpoint**: ImportPhase と OrganizePhase が BasePhaseOrchestrator を継承し、既存機能が動作する

---

## Phase 5: User Story 1 - Resume モードでの Extract 重複ログ防止 (Priority: P1)

**Goal**: Resume モードで Extract output を再利用し、重複ログを防止

**Independent Test**: Resume モードで再実行し、pipeline_stages.jsonl に Extract ログが追加されないことを確認

### 入力
- [X] T054 Read previous phase output: `specs/040-resume-extract-reuse/tasks/ph4-output.md`

### テスト実装 (RED)
- [X] T055 [P] [US1] Create/update test file `src/etl/tests/test_resume_mode.py`
- [X] T056 [P] [US1] Add test for Resume mode loading from extract/output/*.jsonl in `src/etl/tests/test_resume_mode.py`
- [X] T057 [P] [US1] Add test for no Extract log appended in Resume mode in `src/etl/tests/test_resume_mode.py`
- [X] T058 [P] [US1] Add test for standard output message "Resume mode: Loading from extract/output/*.jsonl" in `src/etl/tests/test_resume_mode.py`
- [X] T059 [P] [US1] Add test for "Extract output not found" message when output is empty in `src/etl/tests/test_resume_mode.py`
- [X] T060 Verify `make test` FAIL (RED)
- [X] T061 Generate RED output: `specs/040-resume-extract-reuse/red-tests/ph5-test.md`

### 実装 (GREEN)
- [X] T062 Read RED tests: `specs/040-resume-extract-reuse/red-tests/ph5-test.md`
- [X] T063 [US1] Implement Resume detection logic in BasePhaseOrchestrator.run() to check extract output existence
- [X] T064 [US1] Implement JSONL loading in _load_extract_items_from_output() with glob pattern `data-dump-*.jsonl`
- [X] T065 [US1] Add stdout message "Resume mode: Loading from extract/output/*.jsonl" in run()
- [X] T066 [US1] Add stdout message "Extract output not found, processing from input/" when output is empty
- [X] T067 [US1] Implement exclusion of steps.jsonl, error_details.jsonl, pipeline_stages.jsonl from Resume loading
- [X] T068 [US1] Implement broken JSON record skipping in _load_extract_items_from_output()
- [X] T069 Verify `make test` PASS (GREEN)

### 検証
- [X] T070 Verify `make test` passes all tests
- [X] T071 Manual verification: Create session, run import, then run Resume and check pipeline_stages.jsonl
- [X] T072 Generate phase output: `specs/040-resume-extract-reuse/tasks/ph5-output.md`

**Checkpoint**: Resume モードで Extract 重複ログが防止される

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [X] T073 Read previous phase output: `specs/040-resume-extract-reuse/tasks/ph5-output.md`
- [X] T074 Run full test suite: `make test`
- [X] T075 Run quickstart.md validation scenarios
- [X] T076 [P] Update CLAUDE.md if needed with new command examples
- [X] T077 [P] Code cleanup and ensure consistent style
- [X] T078 Final verification: Full pipeline test with Resume mode
- [X] T079 Generate final output: `specs/040-resume-extract-reuse/tasks/ph6-output.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (US3 - Fixed Filename)**: Depends on Phase 1 - MUST be first because US1/US2 depend on it
- **Phase 3 (US2 - BasePhaseOrchestrator)**: Depends on Phase 2
- **Phase 4 (US2 - Phase Inheritance)**: Depends on Phase 3
- **Phase 5 (US1 - Resume Logic)**: Depends on Phase 4
- **Phase 6 (Polish)**: Depends on Phase 5

### User Story Dependencies

- **User Story 3 (P3)**: First because it provides the fixed filename pattern that US1/US2 depend on
- **User Story 2 (P2)**: Second because it provides BasePhaseOrchestrator that US1 depends on
- **User Story 1 (P1)**: Last because it requires both US3 (fixed filenames) and US2 (FW orchestrator)

### Within Each Phase

- Tests MUST be written and FAIL (RED) before implementation
- Implementation follows to make tests PASS (GREEN)
- Verification confirms all tests pass
- Phase output generated for next phase input

### Parallel Opportunities

**Phase 2 (US3)**:
- T005, T006, T007 can run in parallel (different test methods)

**Phase 3 (US2)**:
- T018, T019, T020, T021, T022 can run in parallel (different test methods)

**Phase 4 (US2)**:
- T036, T037, T038 can run in parallel (different test methods)

**Phase 5 (US1)**:
- T055, T056, T057, T058, T059 can run in parallel (different test methods)

---

## Parallel Example: Phase 2 Tests

```bash
# Launch all tests for Phase 2 together:
Task: "Add test for fixed filename pattern in src/etl/tests/test_stages.py"
Task: "Add test for record splitting (1000 records) in src/etl/tests/test_stages.py"
Task: "Add test for file index increment in src/etl/tests/test_stages.py"
```

---

## Implementation Strategy

### Sequential Delivery (Recommended)

この機能は依存関係が強いため、順次実行を推奨:

1. Phase 1: Setup → 環境準備
2. Phase 2: US3 (Fixed Filename) → 固定ファイル名パターン実装
3. Phase 3: US2 (BasePhaseOrchestrator) → FW クラス作成
4. Phase 4: US2 (Inheritance) → Phase クラス継承変更
5. Phase 5: US1 (Resume Logic) → Resume ロジック実装
6. Phase 6: Polish → 最終検証

### MVP Definition

**MVP = Phase 1 + Phase 2 + Phase 3 + Phase 4 + Phase 5**

すべての User Story が相互依存しているため、MVP は全 User Story を含む。

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[Extract input] → [ProcessingItem] → [JSONL 書き込み] → [Resume 読み込み] → [Transform/Load]
      ↓                ↓                  ↓                    ↓                ↓
    テスト           テスト              テスト                テスト           テスト
```

**チェックリスト**:
- [X] Extract 入力パースのテスト（既存）
- [X] ProcessingItem シリアライズ/デシリアライズのテスト
- [X] **固定ファイル名パターン書き込みのテスト**
- [X] **Resume 時の JSONL 読み込みのテスト**
- [X] End-to-End テスト（新規セッション→ Resume）

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- User Story 実行順序は依存関係に基づく（P3 → P2 → P1）
- 各 Phase 完了後に `make test` で検証
- Phase 出力ファイルで次 Phase への引き継ぎを明確化
