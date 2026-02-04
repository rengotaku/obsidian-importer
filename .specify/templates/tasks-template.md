---

description: "Task list template for feature implementation (TDD workflow)"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | [Story title] | P1 | FR-1,2 | シナリオ1 |
| US2 | [Story title] | P1 | FR-3 | シナリオ1 |
| US3 | [Story title] | P2 | FR-4 | シナリオ2 |

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  Each User Story phase MUST follow the TDD structure:
  - 入力: Read previous phase output
  - テスト実装 (RED): Write tests first, verify FAIL
  - 実装 (GREEN): Implement to pass tests
  - 検証: Verify all tests pass, generate phase output

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure) — NO TDD

**Purpose**: Project initialization, existing code review, and change preparation

- [ ] T001 Read current implementation in src/[relevant files]
- [ ] T002 [P] Read existing tests in src/tests/[relevant test files]
- [ ] T003 Generate phase output: specs/[###-feature-name]/tasks/ph1-output.md

---

## Phase 2: User Story 1 - [Title] (Priority: P1) MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### 入力

- [ ] T004 Read previous phase output: specs/[###-feature-name]/tasks/ph1-output.md

### テスト実装 (RED)

- [ ] T005 [P] [US1] Implement test for [behavior] in src/tests/test_[name].py
- [ ] T006 [P] [US1] Implement test for [edge cases] in src/tests/test_[name].py
- [ ] T007 [P] [US1] Implement test for [integration] in src/tests/test_[name].py
- [ ] T008 Verify `make test` FAIL (RED)
- [ ] T009 Generate RED output: specs/[###-feature-name]/red-tests/ph2-test.md

### 実装 (GREEN)

- [ ] T010 Read RED tests: specs/[###-feature-name]/red-tests/ph2-test.md
- [ ] T011 [P] [US1] Implement [component] in src/[location]/[file].py
- [ ] T012 [P] [US1] Implement [component] in src/[location]/[file].py
- [ ] T013 [US1] Integrate components (depends on T011, T012)
- [ ] T014 Verify `make test` PASS (GREEN)

### 検証

- [ ] T015 Verify `make test` passes all tests (no regressions)
- [ ] T016 Generate phase output: specs/[###-feature-name]/tasks/ph2-output.md

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### 入力

- [ ] T017 Read previous phase output: specs/[###-feature-name]/tasks/ph2-output.md

### テスト実装 (RED)

- [ ] T018 [P] [US2] Implement test for [behavior] in src/tests/test_[name].py
- [ ] T019 [P] [US2] Implement test for [edge cases] in src/tests/test_[name].py
- [ ] T020 Verify `make test` FAIL (RED)
- [ ] T021 Generate RED output: specs/[###-feature-name]/red-tests/ph3-test.md

### 実装 (GREEN)

- [ ] T022 Read RED tests: specs/[###-feature-name]/red-tests/ph3-test.md
- [ ] T023 [P] [US2] Implement [component] in src/[location]/[file].py
- [ ] T024 [US2] Integrate with User Story 1 components (if needed)
- [ ] T025 Verify `make test` PASS (GREEN)

### 検証

- [ ] T026 Verify `make test` passes all tests (including regressions from US1)
- [ ] T027 Generate phase output: specs/[###-feature-name]/tasks/ph3-output.md

**Checkpoint**: User Stories 1 AND 2 should both work independently

---

[Add more user story phases as needed, following the same TDD pattern]

---

## Phase N: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: Improvements that affect multiple user stories

### 入力

- [ ] TXXX Read previous phase output: specs/[###-feature-name]/tasks/ph(N-1)-output.md

### 実装

- [ ] TXXX [P] Remove deprecated code no longer referenced
- [ ] TXXX [P] Remove obsolete tests no longer needed
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Run quickstart.md validation

### 検証

- [ ] TXXX Run `make test` to verify all tests pass after cleanup
- [ ] TXXX Generate phase output: specs/[###-feature-name]/tasks/phN-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - メインエージェント直接実行
- **User Stories (Phase 2+)**: TDD フロー (tdd-generator → phase-executor)
  - User stories proceed sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all user stories - phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **入力**: Read previous phase output (context from prior work)
2. **テスト実装 (RED)**: Write tests FIRST → verify `make test` FAIL → generate RED output
3. **実装 (GREEN)**: Read RED tests → implement → verify `make test` PASS
4. **検証**: Confirm no regressions → generate phase output

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2+ (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase N (Polish)**: phase-executor のみ

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。並列実行を保証するものではない。

- Setup タスクの [P]: 異なるファイル・ディレクトリの作成で相互依存なし
- RED テストの [P]: 異なるテストファイルへの書き込みで相互依存なし
- GREEN 実装の [P]: 異なるソースファイルへの書き込みで相互依存なし
- User Story 間: 各 Phase は前 Phase の出力に依存するため [P] 不可

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/[###-feature-name]/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US1 GREEN results)
│   ├── ph3-output.md           # Phase 3 output (US2 GREEN results)
│   └── phN-output.md           # Final phase output
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED test results (FAIL confirmation)
    └── ph3-test.md             # Phase 3 RED test results (FAIL confirmation)
```

### Phase Output Content

Each `phN-output.md` should contain:
- Summary of what was done
- Files created/modified
- Test results (`make test` output)
- Any decisions or deviations from the plan

### RED Test Output Content

Each `phN-test.md` should contain:
- Test code written
- `make test` output showing FAIL (RED confirmation)
- Number of failing tests and their names

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (existing code review)
2. Complete Phase 2: User Story 1 (RED → GREEN → 検証)
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. Verify with manual test if applicable

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → ... → Phase N
2. Each phase commits: `feat(phase-N): description`

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[入力] → [パース] → [変換] → [出力生成] → [ファイル書込]
   ↓        ↓         ↓          ↓            ↓
 テスト   テスト    テスト      テスト       テスト
```

**チェックリスト**:
- [ ] 入力パース部分のテスト
- [ ] 変換ロジックのテスト
- [ ] **出力生成部分のテスト**（見落としやすい）
- [ ] End-to-End テスト（入力→最終出力）

> ⚠️ 過去の教訓: 出力生成部分のテストがなく、データが最終ファイルに反映されないバグが検出されなかった

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD: テスト実装 (RED) → FAIL 確認 → 実装 (GREEN) → PASS 確認
- RED output must be generated BEFORE implementation begins
- Commit after each phase completion
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
