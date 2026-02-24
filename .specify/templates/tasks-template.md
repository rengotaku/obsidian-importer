---

description: "Task list template for feature implementation (TDD workflow)"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows Test Implementation (RED) → Implementation (GREEN) → Verification workflow.

**Language**: All content in this file should be written in **Japanese** when generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | [Story title] | P1 | FR-1,2 | Scenario 1 |
| US2 | [Story title] | P1 | FR-3 | Scenario 1 |
| US3 | [Story title] | P2 | FR-4 | Scenario 2 |

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
  - Input: Read setup analysis (ph1) AND previous phase output
  - Test Implementation (RED): Write tests first, verify FAIL
  - Implementation (GREEN): Implement to pass tests
  - Verification: Verify all tests pass, generate phase output

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure) — NO TDD

**Purpose**: Project initialization, existing code review, and change preparation

- [ ] T001 Read current implementation in src/[relevant files]
- [ ] T002 [P] Read existing tests in src/tests/[relevant test files]
- [ ] T003 Edit: specs/[###-feature-name]/tasks/ph1-output.md

---

## Phase 2: User Story 1 - [Title] (Priority: P1) MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Input

- [ ] T004 Read previous phase output: specs/[###-feature-name]/tasks/ph1-output.md

### Test Implementation (RED)

- [ ] T005 [P] [US1] Implement test for [behavior] in src/tests/test_[name].py
- [ ] T006 [P] [US1] Implement test for [edge cases] in src/tests/test_[name].py
- [ ] T007 [P] [US1] Implement test for [integration] in src/tests/test_[name].py
- [ ] T008 Verify `make test` FAIL (RED)
- [ ] T009 Generate RED output: specs/[###-feature-name]/red-tests/ph2-test.md

### Implementation (GREEN)

- [ ] T010 Read RED tests: specs/[###-feature-name]/red-tests/ph2-test.md
- [ ] T011 [P] [US1] Implement [component] in src/[location]/[file].py
- [ ] T012 [P] [US1] Implement [component] in src/[location]/[file].py
- [ ] T013 [US1] Integrate components (depends on T011, T012)
- [ ] T014 Verify `make test` PASS (GREEN)

### Verification

- [ ] T015 Verify `make test` passes all tests (no regressions)
- [ ] T016 Edit: specs/[###-feature-name]/tasks/ph2-output.md

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Input

- [ ] T017 Read setup analysis: specs/[###-feature-name]/tasks/ph1-output.md
- [ ] T018 Read previous phase output: specs/[###-feature-name]/tasks/ph2-output.md

### Test Implementation (RED)

- [ ] T019 [P] [US2] Implement test for [behavior] in src/tests/test_[name].py
- [ ] T020 [P] [US2] Implement test for [edge cases] in src/tests/test_[name].py
- [ ] T021 Verify `make test` FAIL (RED)
- [ ] T022 Generate RED output: specs/[###-feature-name]/red-tests/ph3-test.md

### Implementation (GREEN)

- [ ] T023 Read RED tests: specs/[###-feature-name]/red-tests/ph3-test.md
- [ ] T024 [P] [US2] Implement [component] in src/[location]/[file].py
- [ ] T025 [US2] Integrate with User Story 1 components (if needed)
- [ ] T026 Verify `make test` PASS (GREEN)

### Verification

- [ ] T027 Verify `make test` passes all tests (including regressions from US1)
- [ ] T028 Edit: specs/[###-feature-name]/tasks/ph3-output.md

**Checkpoint**: User Stories 1 AND 2 should both work independently

---

[Add more user story phases as needed, following the same TDD pattern]

---

## Phase N: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: Improvements that affect multiple user stories

### Input

- [ ] TXXX Read setup analysis: specs/[###-feature-name]/tasks/ph1-output.md
- [ ] TXXX Read previous phase output: specs/[###-feature-name]/tasks/ph(N-1)-output.md

### Implementation

- [ ] TXXX [P] Remove deprecated code no longer referenced
- [ ] TXXX [P] Remove obsolete tests no longer needed
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Run quickstart.md validation

### Verification

- [ ] TXXX Run `make test` to verify all tests pass after cleanup
- [ ] TXXX Edit: specs/[###-feature-name]/tasks/phN-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - Main agent direct execution
- **User Stories (Phase 2+)**: TDD flow (speckit:tdd-generator → speckit:phase-executor)
  - User stories proceed sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all user stories - speckit:phase-executor only

### Within Each User Story Phase (TDD Flow)

1. **Input**: Read setup analysis (ph1) + previous phase output (context from prior work)
2. **Test Implementation (RED)**: Write tests FIRST → verify `make test` FAIL → generate RED output
3. **Implementation (GREEN)**: Read RED tests → implement → verify `make test` PASS
4. **Verification**: Confirm no regressions → generate phase output

### Agent Delegation

- **Phase 1 (Setup)**: Main agent direct execution
- **Phase 2+ (User Stories)**: speckit:tdd-generator (RED) → speckit:phase-executor (GREEN + Verification)
- **Phase N (Polish)**: speckit:phase-executor only

### [P] Marker (No Dependencies)

`[P]` indicates "no dependencies on other tasks, execution order is flexible". Does not guarantee parallel execution.

- Setup tasks [P]: Different file/directory creation with no interdependencies
- RED tests [P]: Writing to different test files with no interdependencies
- GREEN implementation [P]: Writing to different source files with no interdependencies
- Between User Stories: Each Phase depends on previous Phase output, so [P] not applicable

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

### Phase Output Format

| Output Type | Template File |
|-------------|---------------|
| `ph1-output.md` | `.specify/templates/ph1-output-template.md` |
| `phN-output.md` | `.specify/templates/phN-output-template.md` |
| `phN-test.md` | `.specify/templates/red-test-template.md` |

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (existing code review)
2. Complete Phase 2: User Story 1 (RED → GREEN → Verification)
3. **STOP and VALIDATE**: Confirm all tests pass with `make test`
4. Verify with manual test if applicable

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → ... → Phase N
2. Each phase commits: `feat(phase-N): description`

---

## Test Coverage Rules

**Boundary Test Principle**: Write tests at **every boundary** where data transformation occurs

```
[Input] → [Parse] → [Transform] → [Output Generation] → [File Write]
   ↓         ↓          ↓              ↓                   ↓
 Test      Test       Test           Test                Test
```

**Checklist**:
- [ ] Input parsing tests
- [ ] Transformation logic tests
- [ ] **Output generation tests** (often overlooked)
- [ ] End-to-End tests (input → final output)

> ⚠️ Lesson learned: Missing output generation tests caused bugs where data wasn't reflected in final files

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD: Test Implementation (RED) → Verify FAIL → Implementation (GREEN) → Verify PASS
- RED output must be generated BEFORE implementation begins
- Commit after each phase completion
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
