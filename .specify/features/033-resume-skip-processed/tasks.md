# Tasks: Resume モードでの処理済みアイテムスキップ機能

**Input**: Design documents from `/specs/033-resume-skip-processed/`
**Prerequisites**: plan.md (✅), spec.md (✅), data-model.md (✅), contracts/api.md (✅), quickstart.md (✅)

**Tests**: テスト作成は spec.md で明示的に要求されていないため、最小限の検証のみ実施

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## User Story Mapping

| Story | Title | Priority | FR |
|-------|-------|----------|-----|
| US1 | 中断されたインポートの高速再開 | P1 | FR1 |
| US2 | 入力ファイルの保持 | P1 | FR3 |
| US3 | 処理状態の明確なログ出力 | P2 | FR4, FR6 |
| US4 | セッション統計の正確な記録 | P2 | FR5 |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure confirmation

- [x] T001 Read previous phase output: N/A (initial phase)
- [x] T002 Verify branch `033-resume-skip-processed` is checked out
- [x] T003 [P] Confirm existing test suite passes with `make test`
- [x] T004 Run `make test` to verify all tests pass
- [x] T005 Generate phase output: specs/033-resume-skip-processed/tasks/ph1-output.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data model changes that ALL user stories depend on

**⚠️ CRITICAL**: US1-US4 cannot proceed until PhaseStats.skipped_count is implemented

- [x] T006 Read previous phase output: specs/033-resume-skip-processed/tasks/ph1-output.md
- [x] T007 Add `skipped_count: int = 0` field to PhaseStats in src/etl/core/session.py
- [x] T008 Update `PhaseStats.to_dict()` to include `skipped_count` in src/etl/core/session.py
- [x] T009 Update `PhaseStats.from_dict()` with `data.get("skipped_count", 0)` for backward compatibility in src/etl/core/session.py
- [x] T010 Run `make test` to verify all tests pass
- [x] T011 Generate phase output: specs/033-resume-skip-processed/tasks/ph2-output.md

**Checkpoint**: PhaseStats data model ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 中断されたインポートの高速再開 (Priority: P1) 🎯 MVP

**Goal**: Transform Stage で処理済みアイテムをスキップし、LLM 呼び出しを回避

**Independent Test**: `knowledge_extracted: true` のアイテムが LLM 呼び出しなしで即座にスキップされることを確認

### Implementation for User Story 1

- [x] T012 Read previous phase output: specs/033-resume-skip-processed/tasks/ph2-output.md
- [x] T013 [US1] Add `_is_already_processed()` method to ExtractKnowledgeStep in src/etl/stages/transform/knowledge_transformer.py
- [x] T014 [US1] Add skip logic at start of `ExtractKnowledgeStep.process()` in src/etl/stages/transform/knowledge_transformer.py
- [x] T015 [US1] Set `item.status = ItemStatus.SKIPPED` and `item.metadata["skipped_reason"] = "already_processed"` when skipping
- [x] T016 [US1] Ensure `item.transformed_content = item.content` is set for skipped items to preserve content
- [x] T017 Run `make test` to verify all tests pass
- [x] T018 Generate phase output: specs/033-resume-skip-processed/tasks/ph3-output.md

**Checkpoint**: User Story 1 complete - 処理済みアイテムが Transform でスキップされる

---

## Phase 4: User Story 2 - 入力ファイルの保持 (Priority: P1)

**Goal**: Resume モードで入力ファイルを上書きコピーしない

**Independent Test**: Resume 実行前後で `extract/input/` のファイルタイムスタンプが変化しない

### Implementation for User Story 2

- [x] T019 Read previous phase output: specs/033-resume-skip-processed/tasks/ph3-output.md
- [x] T020 [US2] Wrap input file copy logic with `if not session_id:` condition in src/etl/cli.py (around line 285-306)
- [x] T021 [US2] Add validation for empty `extract/input/` on Resume mode in src/etl/cli.py
- [x] T022 [US2] Add error message `[Error] No input files found in session: {session_id}` and return `ExitCode.INPUT_NOT_FOUND` if empty
- [x] T023 Run `make test` to verify all tests pass
- [x] T024 Generate phase output: specs/033-resume-skip-processed/tasks/ph4-output.md

**Checkpoint**: User Story 2 complete - Resume 時に入力ファイルが保持される

---

## Phase 5: User Story 3 - 処理状態の明確なログ出力 (Priority: P2)

**Goal**: コンソール出力にスキップ数を含める、steps.jsonl に skipped_reason を記録

**Independent Test**: Resume 完了後のログに `N success, M failed, K skipped` 形式で出力される

### Implementation for User Story 3

- [x] T025 Read previous phase output: specs/033-resume-skip-processed/tasks/ph4-output.md
- [x] T026 [US3] Add `items_skipped` counter variable in `ImportPhase.run()` in src/etl/phases/import_phase.py
- [x] T027 [US3] Count `ItemStatus.SKIPPED` items separately (not as `items_processed`) in src/etl/phases/import_phase.py
- [x] T028 [US3] Update console output format to include skipped count in src/etl/cli.py (around line 344)
- [x] T029 [US3] Modify print format to `[Phase] import completed ({success} success, {failed} failed, {skipped} skipped)` when skipped > 0
- [x] T030 Run `make test` to verify all tests pass
- [x] T031 Generate phase output: specs/033-resume-skip-processed/tasks/ph5-output.md

**Checkpoint**: User Story 3 complete - スキップ数がログに表示される

---

## Phase 6: User Story 4 - セッション統計の正確な記録 (Priority: P2)

**Goal**: session.json に skipped_count を記録

**Independent Test**: Resume 完了後の session.json に `phases.import.skipped_count` フィールドが存在する

### Implementation for User Story 4

- [x] T032 Read previous phase output: specs/033-resume-skip-processed/tasks/ph5-output.md
- [x] T033 [US4] Add `items_skipped` to PhaseResult dataclass in src/etl/phases/import_phase.py (or verify already added)
- [x] T034 [US4] Update PhaseStats creation in cli.py to include `skipped_count=result.items_skipped` in src/etl/cli.py (around line 318)
- [x] T035 [US4] Update status command to display skipped_count in src/etl/cli.py (status command section)
- [x] T036 Run `make test` to verify all tests pass
- [x] T037 Generate phase output: specs/033-resume-skip-processed/tasks/ph6-output.md

**Checkpoint**: User Story 4 complete - session.json に skipped_count が記録される

---

## Phase 7: Polish & Final Verification

**Purpose**: Cross-cutting concerns and final validation

- [x] T038 Read previous phase output: specs/033-resume-skip-processed/tasks/ph6-output.md
- [x] T039 [P] Verify backward compatibility: new session without `--session` works as before
- [x] T040 [P] Verify old session.json without `skipped_count` loads correctly
- [x] T041 Manual E2E test: Create partial session, Resume, verify skip behavior
- [x] T042 Update CLAUDE.md if any new CLI options or behavior changes need documentation
- [x] T043 Run `make test` to verify all tests pass
- [x] T044 Generate phase output: specs/033-resume-skip-processed/tasks/ph7-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 - PhaseStats changes BLOCK all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 - Transform skip implementation
- **User Story 2 (Phase 4)**: Depends on Phase 2 - CLI input copy skip (can parallel with US1)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (needs skip count from Transform)
- **User Story 4 (Phase 6)**: Depends on Phase 5 (needs skip count reporting)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (PhaseStats.skipped_count)
    ↓
    ├── Phase 3: US1 (Transform skip) ─────┐
    │                                       │
    └── Phase 4: US2 (CLI input skip) [P]  │
                                            ↓
                                     Phase 5: US3 (Log output)
                                            ↓
                                     Phase 6: US4 (session.json)
                                            ↓
                                     Phase 7: Polish
```

### Parallel Opportunities

**Within Phase 2 (Foundational)**:
- T007, T008, T009 are sequential (same file dependencies)

**After Phase 2**:
- Phase 3 (US1) and Phase 4 (US2) can run in parallel (different files)

**Within Phase 7 (Polish)**:
- T039 and T040 can run in parallel (different verification targets)

---

## Parallel Example: Phases 3 & 4

```bash
# These can run concurrently after Phase 2 completes:

# Developer A: User Story 1 (Transform skip)
Task: "Add _is_already_processed() method in knowledge_transformer.py"
Task: "Add skip logic at start of process() in knowledge_transformer.py"

# Developer B: User Story 2 (CLI input skip)
Task: "Wrap input file copy with session_id check in cli.py"
Task: "Add validation for empty extract/input/ in cli.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (PhaseStats.skipped_count)
3. Complete Phase 3: User Story 1 (Transform skip)
4. Complete Phase 4: User Story 2 (CLI input skip)
5. **STOP and VALIDATE**: Test Resume with partial session
6. Deploy/demo if ready - core functionality complete

### Full Feature Delivery

1. Setup + Foundational → Foundation ready
2. US1 + US2 → Core functionality (MVP!)
3. US3 → Better logging visibility
4. US4 → Complete statistics tracking
5. Polish → Final verification

---

## Files Modified Summary

| File | Changes |
|------|---------|
| `src/etl/core/session.py` | PhaseStats.skipped_count 追加 |
| `src/etl/stages/transform/knowledge_transformer.py` | 処理済みスキップロジック追加 |
| `src/etl/cli.py` | Resume 入力コピースキップ、ログ出力更新 |
| `src/etl/phases/import_phase.py` | skipped_count 集計 |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 と US2 は独立実装可能（並列実行可）
- US3 は US1 のスキップカウントに依存
- US4 は US3 のカウント出力に依存
- 後方互換性: `skipped_count` 未設定の古い session.json は `0` でデフォルト
