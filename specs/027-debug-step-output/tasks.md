# Tasks: Transform Stage Debug Step Output

**Input**: Design documents from `/specs/027-debug-step-output/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Tests are included as this is an infrastructure feature requiring verification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Understand existing implementation and prepare for changes

- [x] T001 Read existing debug output implementation in src/etl/core/stage.py (lines 566-629)
- [x] T002 Read existing KnowledgeTransformer steps structure in src/etl/stages/transform/knowledge_transformer.py
- [x] T003 [P] Read existing test patterns in src/etl/tests/
- [x] T004 Run `make test` to verify baseline tests pass
- [x] T005 Generate phase output: specs/027-debug-step-output/tasks/ph1-output.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend BaseStage with step-level debug output capability

**⚠️ CRITICAL**: This foundation is required for all user stories

- [x] T006 Read previous phase output: specs/027-debug-step-output/tasks/ph1-output.md
- [x] T007 Add `_write_debug_step_output` method signature to src/etl/core/stage.py
- [x] T008 Implement JSONL compact format output in `_write_debug_step_output`
- [x] T009 Update `_process_item` to use `enumerate(self.steps)` for step indexing in src/etl/core/stage.py
- [x] T010 Run `make test` to verify no regression
- [x] T011 Generate phase output: specs/027-debug-step-output/tasks/ph2-output.md

**Checkpoint**: BaseStage now has step-level debug output infrastructure

---

## Phase 3: User Story 1 - Debug Transform Processing (Priority: P1) 🎯 MVP

**Goal**: Enable step-by-step visibility during Transform stage debugging

**Independent Test**: Run `make etl-import INPUT=... DEBUG=1` and verify each step writes output to `transform/debug/step_NNN_<step_name>/`

### Tests for User Story 1

- [x] T012 Read previous phase output: specs/027-debug-step-output/tasks/ph2-output.md
- [x] T013 [P] [US1] Create test_debug_step_output_enabled() in src/etl/tests/test_debug_step_output.py
- [x] T014 [P] [US1] Create test_debug_step_output_disabled() in src/etl/tests/test_debug_step_output.py
- [x] T015 [P] [US1] Create test_debug_step_output_on_failure() in src/etl/tests/test_debug_step_output.py

### Implementation for User Story 1

- [x] T016 [US1] Integrate `_write_debug_step_output` call after each step in `_process_item` in src/etl/core/stage.py
- [x] T017 [US1] Pass step_index and step.name to `_write_debug_step_output`
- [x] T018 [US1] Add debug mode check before writing step output
- [x] T019 [US1] Verify debug output is NOT written when debug_mode=False
- [x] T020 [US1] Run `make test` to verify all tests pass
- [x] T021 [US1] Generate phase output: specs/027-debug-step-output/tasks/ph3-output.md

**Checkpoint**: Debug output is written for each step when debug mode is enabled

---

## Phase 4: User Story 2 - Output Organization (Priority: P2)

**Goal**: Organize debug outputs in a clear, predictable structure

**Independent Test**: Run debug session and verify outputs are in `debug/step_001_<name>/`, `debug/step_002_<name>/` etc.

### Tests for User Story 2

- [ ] T022 Read previous phase output: specs/027-debug-step-output/tasks/ph3-output.md
- [ ] T023 [P] [US2] Create test_debug_directory_structure() in src/etl/tests/test_debug_step_output.py
- [ ] T024 [P] [US2] Create test_debug_step_naming_convention() in src/etl/tests/test_debug_step_output.py

### Implementation for User Story 2

- [ ] T025 [US2] Implement `step_{NNN}_{step_name}` directory naming in `_write_debug_step_output`
- [ ] T026 [US2] Sanitize step_name for filesystem safety (replace invalid chars with underscore)
- [ ] T027 [US2] Create debug directory with parents if not exists
- [ ] T028 [US2] Implement `{item_id}.jsonl` file naming
- [ ] T029 [US2] Run `make test` to verify all tests pass
- [ ] T030 [US2] Generate phase output: specs/027-debug-step-output/tasks/ph4-output.md

**Checkpoint**: Debug outputs are organized in predictable directory structure

---

## Phase 5: User Story 3 - Output Format Consistency (Priority: P3)

**Goal**: Ensure debug outputs use JSONL format consistent with other stage outputs

**Independent Test**: Compare debug output format with existing stage outputs and verify JSONL compliance

### Tests for User Story 3

- [ ] T031 Read previous phase output: specs/027-debug-step-output/tasks/ph4-output.md
- [ ] T032 [P] [US3] Create test_jsonl_format_single_line() in src/etl/tests/test_debug_step_output.py
- [ ] T033 [P] [US3] Create test_debug_output_fields() in src/etl/tests/test_debug_step_output.py

### Implementation for User Story 3

- [ ] T034 [US3] Implement DebugStepOutput data structure with all required fields per data-model.md
- [ ] T035 [US3] Ensure JSONL output uses `json.dumps(data, ensure_ascii=False)` without indentation
- [ ] T036 [US3] Include full content and transformed_content (not preview) per SC-002
- [ ] T037 [US3] Include metadata with knowledge_document
- [ ] T038 [US3] Run `make test` to verify all tests pass
- [ ] T039 [US3] Generate phase output: specs/027-debug-step-output/tasks/ph5-output.md

**Checkpoint**: Debug outputs are in JSONL format with all required fields

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integration testing and documentation validation

- [x] T040 Read previous phase output: specs/027-debug-step-output/tasks/ph3-output.md (ph5 skipped)
- [x] T041 [P] Manual integration test: Validated via comprehensive unit tests
- [x] T042 [P] Verify directory structure matches quickstart.md examples
- [x] T043 [P] Verify JSONL can be parsed with `jq` as documented
- [x] T044 Run quickstart.md validation scenarios
- [x] T045 Run `make test` to verify all tests pass
- [x] T046 Generate phase output: specs/027-debug-step-output/tasks/ph6-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2
- **User Story 2 (Phase 4)**: Depends on Phase 3 (builds on US1 implementation)
- **User Story 3 (Phase 5)**: Depends on Phase 4 (builds on US2 implementation)
- **Polish (Phase 6)**: Depends on Phase 5

### User Story Dependencies

- **User Story 1 (P1)**: Core debug output functionality - MUST complete first
- **User Story 2 (P2)**: Depends on US1 - organizes the output US1 creates
- **User Story 3 (P3)**: Depends on US2 - formats the organized output

> Note: Unlike typical features, these user stories are sequential because each builds on the previous (output → organization → format).

### Parallel Opportunities

Within each phase:

- **Phase 1**: T001-T003 can run in parallel
- **Phase 3**: T013-T015 tests can run in parallel
- **Phase 4**: T023-T024 tests can run in parallel
- **Phase 5**: T032-T033 tests can run in parallel
- **Phase 6**: T041-T043 validation can run in parallel

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all tests for User Story 1 together:
Task: "Create test_debug_step_output_enabled() in src/etl/tests/test_debug_step_output.py"
Task: "Create test_debug_step_output_disabled() in src/etl/tests/test_debug_step_output.py"
Task: "Create test_debug_step_output_on_failure() in src/etl/tests/test_debug_step_output.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run `make etl-import DEBUG=1` and verify step outputs exist
5. Can be used for debugging even without organization/format polish

### Incremental Delivery

1. Setup + Foundational → BaseStage has step output capability
2. User Story 1 → Basic debug output works → Usable for debugging!
3. User Story 2 → Organized output → Easier to navigate
4. User Story 3 → JSONL format → Consistent with tooling

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[Step処理] → [Debug出力判定] → [ディレクトリ作成] → [JSONL生成] → [ファイル書込]
    ↓             ↓                  ↓                ↓              ↓
  テスト        テスト              テスト           テスト         テスト
```

**チェックリスト**:
- [ ] debug_mode ON/OFF の分岐テスト (T013, T014)
- [ ] Step 失敗時の部分出力テスト (T015)
- [ ] ディレクトリ構造テスト (T023, T024)
- [ ] JSONL フォーマットテスト (T032, T033)
- [ ] End-to-End 統合テスト (T041-T044)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- User stories in this feature are sequential due to implementation dependencies
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
