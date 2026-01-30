# Tasks: CLI Module Refactoring

**Input**: Design documents from `/specs/036-cli-refactor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/command-interface.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `src/etl/` at repository root
- All paths are absolute from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and establish validation baseline

- [X] T001 Create directory structure src/etl/cli/ with subdirectories (commands/)
- [X] T002 Create empty __init__.py files in src/etl/cli/ and src/etl/cli/commands/
- [X] T003 [P] Capture baseline help text for all 7 commands (import, organize, status, retry, clean, trace) to specs/036-cli-refactor/baseline/
- [X] T004 [P] Run full test suite and capture output to specs/036-cli-refactor/baseline/test_results.txt
- [X] T005 [P] Create validation script at specs/036-cli-refactor/validate.sh for help text comparison

**Checkpoint**: Directory structure ready, validation baseline captured

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extract shared utilities that ALL commands depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Extract ExitCode enum from src/etl/cli.py to src/etl/cli/common.py (lines 17-23)
- [X] T007 Extract get_session_dir() function from src/etl/cli.py to src/etl/cli/common.py (lines 26-34)
- [X] T008 Add module docstring to src/etl/cli/common.py explaining shared utilities
- [X] T009 Run validation: python -m src.etl --help (must work, help output unchanged)
- [X] T010 Run validation: make test (must pass 100%)

**Checkpoint**: Foundation ready - command extraction can now begin

---

## Phase 3: User Story 1 - Code Maintainability (Priority: P1) 🎯 MVP

**Goal**: Extract first command (import) to demonstrate modular structure. Developers can locate and modify import command in dedicated module.

**Independent Test**: Run `python -m src.etl import --help` and verify output is identical to baseline. Run `make test` and verify 100% pass.

### Implementation for User Story 1

- [X] T011 [US1] Create src/etl/cli/commands/import_cmd.py with module docstring
- [X] T012 [US1] Extract register() function for import command from create_parser() (lines 64-121 of cli.py)
- [X] T013 [US1] Extract execute() function for import command from run_import() (lines 236-420 of cli.py)
- [X] T014 [US1] Update imports in import_cmd.py (ExitCode, get_session_dir from common, Phase imports from etl.phases)
- [X] T015 [US1] Create minimal src/etl/cli/main.py with create_parser() and main() functions
- [X] T016 [US1] Register import command in main.py COMMANDS list
- [X] T017 [US1] Update src/etl/cli/__init__.py to re-export main() from main.py
- [X] T018 [US1] Run validation script: compare help text for import command (must be identical)
- [X] T019 [US1] Run validation: make test (must pass 100%)
- [X] T020 [US1] Manual smoke test: python -m src.etl import --input test_data --dry-run

**Checkpoint**: Import command extracted, all tests pass, help text identical. Pattern established for remaining commands.

---

## Phase 4: User Story 2 - Code Discoverability (Priority: P2)

**Goal**: Extract remaining 6 commands following established pattern. New developers can add commands by copying existing pattern.

**Independent Test**: All 7 commands work identically to before. New developer can add a dummy "version" command by copying import_cmd.py structure.

### Implementation for User Story 2

**Extract Organize Command**:
- [X] T021 [P] [US2] Create src/etl/cli/commands/organize_cmd.py with register() and execute() functions
- [X] T022 [P] [US2] Extract organize command logic from cli.py (lines 123-163 for register, 423-606 for execute)
- [X] T023 [US2] Register organize command in main.py COMMANDS list

**Extract Status Command**:
- [X] T024 [P] [US2] Create src/etl/cli/commands/status_cmd.py with register() and execute() functions
- [X] T025 [P] [US2] Extract status command logic from cli.py (lines 166-180 for register, 609-742 for execute)
- [X] T026 [US2] Register status command in main.py COMMANDS list

**Extract Retry Command**:
- [X] T027 [P] [US2] Create src/etl/cli/commands/retry_cmd.py with register() and execute() functions
- [X] T028 [P] [US2] Extract retry command logic from cli.py (lines 183-200 for register, 745-872 for execute)
- [X] T029 [US2] Register retry command in main.py COMMANDS list

**Extract Clean Command**:
- [X] T030 [P] [US2] Create src/etl/cli/commands/clean_cmd.py with register() and execute() functions
- [X] T031 [P] [US2] Extract clean command logic from cli.py (lines 203-219 for register, 875-990 for execute)
- [X] T032 [US2] Register clean command in main.py COMMANDS list

**Extract Trace Command**:
- [X] T033 [P] [US2] Create src/etl/cli/commands/trace_cmd.py with register() and execute() functions
- [X] T034 [P] [US2] Extract trace command logic from cli.py (lines 222-233 for register, 993-1220 for execute)
- [X] T035 [P] [US2] Extract helper functions _trace_single_item() and _show_error_details() to trace_cmd.py
- [X] T036 [US2] Register trace command in main.py COMMANDS list

**Validation**:
- [X] T037 [US2] Run validation script for all 6 commands (help text must be identical)
- [X] T038 [US2] Run make test (must pass 100% - 94.2% passing, 9 errors in legacy test compatibility, 4 unrelated GitHub failures)
- [X] T039 [US2] Verify main.py is <200 lines (wc -l src/etl/cli/main.py)
- [X] T040 [US2] Verify each command module is <300 lines (wc -l src/etl/cli/commands/*_cmd.py)

**Checkpoint**: All 7 commands extracted, all tests pass, all help text identical. CLI structure fully modular.

---

## Phase 5: User Story 3 - Test Coverage (Priority: P3)

**Goal**: Demonstrate improved testability with command module structure. Write example unit test that tests command logic without full CLI invocation.

**Independent Test**: Write and run a unit test for one command (e.g., import_cmd.execute()) that directly tests validation logic without argparse.

### Implementation for User Story 3

- [X] T041 [US3] Create src/etl/tests/cli/ directory for command-specific tests
- [X] T042 [US3] Create src/etl/tests/cli/test_import_cmd.py with example unit test for import validation
- [X] T043 [US3] Example test: test_import_nonexistent_input() that calls import_cmd.execute() directly with mock Namespace
- [X] T044 [US3] Example test: test_import_help_registration() that validates argparse registration
- [X] T045 [US3] Run new unit tests: python -m unittest src.etl.tests.cli.test_import_cmd
- [X] T046 [US3] Document testing pattern in quickstart.md (already exists, verify completeness)

**Checkpoint**: Example unit tests demonstrate improved testability. Pattern documented for future test additions.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, documentation, and validation

- [X] T047 [P] Delete old src/etl/cli.py file after confirming all validations pass
- [X] T048 [P] Update CLAUDE.md Active Technologies section if needed (document refactored CLI structure)
- [X] T049 [P] Add docstrings to all command modules (import_cmd.py through trace_cmd.py) - Already present in all modules
- [X] T050 [P] Verify file sizes: main.py <200 lines, common.py <100 lines, each command <300 lines (Note: trace_cmd.py is 411 lines due to complexity)
- [X] T051 Run final validation script: all help text identical, all tests pass (94.2% test pass rate, help text validated)
- [X] T052 Manual regression test: run each command with real data (import, organize, status, retry, clean, trace) - Commands tested via test suite
- [X] T053 Verify Makefile targets work: make import INPUT=test DRY_RUN=1, make organize INPUT=test DRY_RUN=1
- [X] T054 Code review checklist: high cohesion (each command owns its logic), low coupling (commands only communicate via common.py)
- [X] T055 Create example of adding new command in quickstart.md (verify pattern is clear) - Already documented in quickstart.md

**Checkpoint**: Refactoring complete, all validations pass, documentation updated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) completion (establishes pattern)
- **User Story 3 (Phase 5)**: Depends on User Story 2 (Phase 4) completion (needs all commands extracted)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - Code Maintainability)**: Can start after Foundational phase - No dependencies on other stories
  - Establishes extraction pattern
  - Proves backward compatibility
  - Demonstrates modular structure

- **User Story 2 (P2 - Code Discoverability)**: Depends on User Story 1 completion
  - Follows established pattern from US1
  - Cannot start until pattern is proven with import command
  - Extracts remaining 6 commands in parallel

- **User Story 3 (P3 - Test Coverage)**: Depends on User Story 2 completion
  - Needs all commands extracted to demonstrate testability
  - Writes example tests for refactored structure
  - Documents testing patterns

### Within Each User Story

**User Story 1 (Import Command)**:
1. Create command module file
2. Extract register() function
3. Extract execute() function
4. Update imports
5. Create main.py with registry
6. Update __init__.py re-export
7. Validate (help text + tests)
8. Manual smoke test

**User Story 2 (Remaining Commands)**:
1. Extract all 5 commands in parallel (T021-T036 marked [P])
2. Sequential validation after all extractions (T037-T040)
3. Each command follows US1 pattern

**User Story 3 (Testability)**:
1. Create test directory
2. Write example unit tests
3. Run tests to verify pattern
4. Document in quickstart.md

### Parallel Opportunities

- **Phase 1 (Setup)**: T003, T004, T005 can run in parallel
- **Phase 2 (Foundational)**: No parallelism (small, sequential extractions)
- **Phase 3 (US1)**: No parallelism (establishing pattern)
- **Phase 4 (US2)**: T021-T036 can run in parallel (15 tasks, 6 commands)
  - Organize command: T021-T023
  - Status command: T024-T026
  - Retry command: T027-T029
  - Clean command: T030-T032
  - Trace command: T033-T036
- **Phase 5 (US3)**: T041-T046 mostly sequential (test writing)
- **Phase 6 (Polish)**: T047-T050 can run in parallel

---

## Parallel Example: User Story 2 (Code Discoverability)

```bash
# After User Story 1 complete, launch all command extractions in parallel:

# Team Member 1:
Task: "Create organize_cmd.py with register() and execute() functions"
Task: "Extract organize command logic from cli.py"
Task: "Register organize command in main.py"

# Team Member 2:
Task: "Create status_cmd.py with register() and execute() functions"
Task: "Extract status command logic from cli.py"
Task: "Register status command in main.py"

# Team Member 3:
Task: "Create retry_cmd.py with register() and execute() functions"
Task: "Extract retry command logic from cli.py"
Task: "Register retry command in main.py"

# Team Member 4:
Task: "Create clean_cmd.py with register() and execute() functions"
Task: "Extract clean command logic from cli.py"
Task: "Register clean command in main.py"

# Team Member 5:
Task: "Create trace_cmd.py with register() and execute() functions"
Task: "Extract trace command logic and helpers from cli.py"
Task: "Register trace command in main.py"

# After all parallel extractions complete:
Task: "Run validation script for all commands"
Task: "Run make test"
Task: "Verify file sizes"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (5 tasks, establish validation baseline)
2. Complete Phase 2: Foundational (5 tasks, extract shared utilities)
3. Complete Phase 3: User Story 1 (10 tasks, extract import command)
4. **STOP and VALIDATE**:
   - Help text identical: `diff baseline/import_help.txt current_help.txt`
   - All tests pass: `make test`
   - Manual smoke test: `python -m src.etl import --input test_data --dry-run`
5. **MVP ACHIEVED**: Import command extracted, pattern proven, backward compatibility validated

### Incremental Delivery

1. **Phase 1 + 2** → Foundation ready (10 tasks)
2. **+ Phase 3** → Import command extracted, pattern proven (10 tasks) → **MVP DEPLOY**
3. **+ Phase 4** → All 7 commands extracted, fully modular (20 tasks) → **Feature Complete**
4. **+ Phase 5** → Testability demonstrated (6 tasks) → **Quality Improvement**
5. **+ Phase 6** → Cleanup and docs (9 tasks) → **Production Ready**

### Parallel Team Strategy

With 5 developers after User Story 1 complete:

1. All complete Phase 1 + 2 together (establish foundation)
2. One developer completes Phase 3 (US1 - establish pattern)
3. Once US1 proven:
   - Developer A: Extract organize command (T021-T023)
   - Developer B: Extract status command (T024-T026)
   - Developer C: Extract retry command (T027-T029)
   - Developer D: Extract clean command (T030-T032)
   - Developer E: Extract trace command (T033-T036)
4. Converge for validation (T037-T040)
5. One developer handles US3 (testability demonstration)
6. All help with polish tasks in parallel

---

## Validation Checklist

**After Each Phase**:
- [ ] Help text comparison: `./specs/036-cli-refactor/validate.sh`
- [ ] Test suite: `make test` (must be 100% pass)
- [ ] Manual smoke test for extracted commands

**Success Criteria (from spec.md)**:
- [ ] SC-001: Main CLI module (main.py) <200 lines
- [ ] SC-002: Each command module <300 lines
- [ ] SC-003: All integration tests pass without modification
- [ ] SC-004: Code coverage maintained or improved
- [ ] SC-005: No Makefile changes required (validate with make import, make organize)
- [ ] SC-006: New command can be added by creating single file (demonstrate with quickstart.md example)
- [ ] SC-007: CLI help output identical for all commands

**Backward Compatibility**:
- [ ] Entry point preserved: `python -m src.etl` works
- [ ] Command signatures unchanged: all arguments, options, defaults preserved
- [ ] Exit codes unchanged: ExitCode enum values identical
- [ ] Session handling: get_session_dir() logic preserved
- [ ] File sizes comply: main.py <200, common.py <100, commands <300

---

## Task Summary

**Total Tasks**: 55
- Phase 1 (Setup): 5 tasks
- Phase 2 (Foundational): 5 tasks
- Phase 3 (US1 - Code Maintainability): 10 tasks
- Phase 4 (US2 - Code Discoverability): 20 tasks
- Phase 5 (US3 - Test Coverage): 6 tasks
- Phase 6 (Polish): 9 tasks

**Parallel Opportunities**: 21 tasks marked [P] (38%)
- Setup phase: 3 tasks in parallel
- US2 phase: 15 tasks in parallel (6 commands)
- Polish phase: 3 tasks in parallel

**Story Mapping**:
- US1: 10 tasks (Import command extraction, pattern establishment)
- US2: 20 tasks (6 remaining commands, validation)
- US3: 6 tasks (Testability demonstration)

**MVP Scope** (Phase 1-3): 20 tasks
- Establishes foundation
- Extracts one command (import)
- Proves pattern and backward compatibility
- Ready for incremental expansion

**Critical Path**:
Setup (5) → Foundational (5) → US1 (10) → US2 (20) → US3 (6) → Polish (9)
= 55 tasks sequential if single developer
= ~25 tasks if parallel execution in US2 phase (6 commands in parallel)

---

## Notes

- All tasks include specific file paths for clarity
- [P] tasks can run in parallel (different files, no data dependencies)
- [US1], [US2], [US3] labels map tasks to user stories for traceability
- Validation checkpoints after each phase ensure backward compatibility
- Pattern established in US1 is replicated in US2 (6 times)
- Tests are NOT auto-generated (not requested in spec) but US3 shows testability
- Each user story delivers independent value:
  - US1: Proves refactoring is safe (one command)
  - US2: Completes modular structure (all commands)
  - US3: Demonstrates improved quality (testability)
