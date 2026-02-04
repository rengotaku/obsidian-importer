# Tasks: Robust JSON Parsing for LLM Responses

**Input**: Design documents from `/specs/005-robust-json-parse/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested. Manual validation via fixtures.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Target file**: `.claude/scripts/ollama_normalizer.py`
- **Fixtures**: `.claude/scripts/tests/fixtures/`

---

## Phase 1: Setup

**Purpose**: Prepare for implementation

- [x] T001 Backup current parse_json_response function in .claude/scripts/ollama_normalizer.py
- [x] T002 Add import statement for `re` module at top of .claude/scripts/ollama_normalizer.py

---

## Phase 2: Foundational (Helper Functions)

**Purpose**: Create helper functions that all user stories depend on

**⚠️ CRITICAL**: User story implementation depends on these helpers

- [x] T003 Add CODE_BLOCK_PATTERN regex constant after imports in .claude/scripts/ollama_normalizer.py
- [x] T004 Implement extract_json_from_code_block function in .claude/scripts/ollama_normalizer.py
- [x] T005 Implement extract_first_json_object function with bracket balancing in .claude/scripts/ollama_normalizer.py
- [x] T006 Implement format_parse_error helper function in .claude/scripts/ollama_normalizer.py

**Checkpoint**: All helper functions ready for parse_json_response integration

---

## Phase 3: User Story 1 & 2 - Basic & Code Block Extraction (Priority: P1) 🎯 MVP

**Goal**: Replace parse_json_response with robust implementation that handles:
- Extra text before/after JSON
- Markdown code blocks

**Independent Test**: Process a file with extra text in LLM response and verify success

### Implementation for User Story 1 & 2 (Combined - same function)

- [x] T007 [US1] Replace parse_json_response function body with new implementation in .claude/scripts/ollama_normalizer.py
- [x] T008 [US1] Add empty response check at start of parse_json_response
- [x] T009 [US2] Add code block extraction as first attempt in parse_json_response
- [x] T010 [US1] Add bracket balance extraction as fallback in parse_json_response
- [x] T011 [US1] Add improved error message with position and context

**Checkpoint**: Basic JSON extraction and code block extraction working

---

## Phase 4: User Story 3 - Nested JSON Handling (Priority: P2)

**Goal**: Handle deeply nested JSON structures correctly

**Independent Test**: Process JSON with 3+ levels of nesting

### Implementation for User Story 3

- [x] T012 [US3] Verify extract_first_json_object handles nested structures in .claude/scripts/ollama_normalizer.py
- [x] T013 [US3] Add test case for nested JSON in validation script

**Checkpoint**: Nested JSON extraction verified

---

## Phase 5: User Story 4 - Escaped Characters (Priority: P2)

**Goal**: Handle escaped quotes and brackets in string values

**Independent Test**: Process JSON containing escaped characters in strings

### Implementation for User Story 4

- [x] T014 [US4] Verify escape handling in extract_first_json_object works correctly
- [x] T015 [US4] Add test case for escaped characters in validation script

**Checkpoint**: All escape character scenarios handled

---

## Phase 6: Polish & Validation

**Purpose**: Final testing and documentation

- [x] T016 Run validation against tech_document.md fixture in .claude/scripts/tests/fixtures/
- [x] T017 Run validation against all fixtures to ensure no regression
- [x] T018 Verify processing time < 10ms with timing measurement
- [x] T019 Update TEST_RESULTS_ANALYSIS.md with new results in .claude/scripts/tests/fixtures/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup
- **User Story 1 & 2 (Phase 3)**: Depends on Foundational - CORE MVP
- **User Story 3 (Phase 4)**: Depends on Phase 3 (uses same function)
- **User Story 4 (Phase 5)**: Depends on Phase 3 (uses same function)
- **Polish (Phase 6)**: Depends on all stories complete

### Task Dependencies Within Phases

```
T001 → T002 → T003 → T004, T005, T006 (parallel)
                         ↓
                     T007-T011 (sequential)
                         ↓
                     T012-T015 (verification)
                         ↓
                     T016-T019 (validation)
```

### Parallel Opportunities

- T004, T005, T006 can be written in parallel (different functions)
- T012-T013 and T014-T015 are verification tasks that could run after Phase 3

---

## Implementation Strategy

### MVP First (Phase 1-3 Only)

1. Complete Phase 1: Setup (backup, imports)
2. Complete Phase 2: Foundational (helper functions)
3. Complete Phase 3: User Story 1 & 2 (replace parse_json_response)
4. **STOP and VALIDATE**: Test with tech_document.md fixture
5. If working, deployment ready

### Incremental Delivery

1. Setup + Foundational → Helpers ready
2. User Story 1 & 2 → Basic extraction + code blocks working → **MVP Complete**
3. User Story 3 → Nested JSON verified
4. User Story 4 → Escaped characters verified
5. Polish → Full validation and documentation

---

## Notes

- All changes are in single file: `.claude/scripts/ollama_normalizer.py`
- Existing API signature must be preserved: `parse_json_response(response: str) -> tuple[dict, str | None]`
- No external dependencies (standard library only)
- Performance target: < 10ms per response
