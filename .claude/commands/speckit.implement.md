---
description: Execute the implementation plan by delegating phases to subagents for processing tasks defined in tasks.md
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Check checklists status** (if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Completed items: Lines matching `- [X]` or `- [x]`
     - Incomplete items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 incomplete items
     - **FAIL**: One or more checklists have incomplete items

   - **If any checklist is incomplete**:
     - Display the table with incomplete item counts
     - **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to step 3

   - **If all checklists are complete**:
     - Display the table showing all checklists passed
     - Automatically proceed to step 3

3. Load and analyze the implementation context:
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios

4. **Project Setup Verification**:
   - Create/verify ignore files based on actual project setup (.gitignore, .dockerignore, etc.)
   - Check technology from plan.md and apply appropriate patterns

5. Parse tasks.md structure and extract:
   - **Task phases**: Setup, Tests, Core, Integration, Polish
   - **Task dependencies**: Sequential vs parallel execution rules
   - **Task details**: ID, description, file paths, parallel markers [P]
   - **Execution flow**: Order and dependency requirements

6. **Execute implementation phases**:

   ### 6.1 Phase Type Detection

   | Phase Type | Executor | Reason |
   |------------|----------|--------|
   | **Setup** (Phase 1) | Main agent | Requires context preservation |
   | **TDD Phase** (has test design section) | tdd-generator → phase-executor | TDD flow |
   | **Standard Phase** (Polish/Documentation) | phase-executor only | Integration test/verification only |

   Detection: Phase name contains "setup" → main, has "### Test Design" or "### Test Implementation" → TDD, otherwise → standard

   ### 6.2 Phase 1 (Setup) - Main agent direct execution

   If Phase 1 is Setup, execute directly without delegating to subagents:
   1. Extract Phase 1 tasks from tasks.md
   2. Execute each task sequentially
   3. Update tasks.md (`- [ ]` → `- [X]`)
   4. Generate `{FEATURE_DIR}/tasks/ph1-output.md`
   5. **Commit setup changes**:
      ```bash
      git add -A && git commit -m "chore(phase-1): Setup - {brief description}"
      ```

   ### 6.3 TDD Flow (User Story / Foundational Phase)

   **Step 1: Test Implementation (RED)**
   - Invoke `tdd-generator` via Task tool (`model: opus`)
   - Refer to `.claude/agents/tdd-generator.md` for input/output format
   - Verify tests are in FAIL state after completion
   - **Commit RED**:
     ```bash
     git add -A && git commit -m "test(phase-{N}): RED - {brief description}"
     ```

   **Step 2: Implementation (GREEN) + Verification**
   - Invoke `phase-executor` via Task tool (`model: sonnet`)
   - Refer to `.claude/agents/phase-executor.md` for input/output format
   - Verify all tests PASS after completion
   - **Commit GREEN**:
     ```bash
     git add -A && git commit -m "feat(phase-{N}): GREEN - {brief description}"
     ```

   **Step 3: Coverage Verification**
   - Verify ≥80% with `make coverage`
   - If insufficient, request additional tests from tdd-generator

   ### 6.4 Standard Flow (Polish/Documentation Phase)

   - Invoke `phase-executor` via Task tool (`model: sonnet`)
   - Refer to `.claude/agents/phase-executor.md` for input/output format
   - **Commit phase changes**:
     ```bash
     git add -A && git commit -m "feat(phase-{N}): Polish - {brief description}"
     ```

   ### 6.5 Phase Transition

   After phase completion:
   1. Display phase completion summary
   2. Display deliverables list
   3. Generate `{FEATURE_DIR}/tasks/ph{N}-output.md`
   4. **Save session context**:
      ```bash
      /sc:save   # Saves branch, status=in_progress, timestamp
      ```
   5. **All tasks completed** → Auto-proceed to next phase
   6. **Partial failure/error** → Ask user for confirmation

   ### 6.6 Final Phase Completion (REQUIRED)

   After the **final phase** (Polish) is completed:
   1. Mark session as completed:
      ```bash
      /sc:save --completed   # Sets status=completed
      ```
   2. Or delete the session memory to prevent accidental reload:
      ```bash
      mcp__serena__delete_memory(memory_file_name="session-{feature-name}")
      ```
   3. This prevents the session from being reloaded after compaction in unrelated work

7. **Progress tracking and error handling**:
   - Report progress after each completed task
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed
   - **IMPORTANT**: For completed tasks, make sure to mark the task off as [X] in the tasks file.

8. **Completion validation**:
   - Verify all phases completed
   - Run final validation: `grep -c "\- \[ \]" tasks.md` (Should be 0)
   - Check that implemented features match the original specification
   - Validate that tests pass
   - Generate completion report

## Notes

- This command requires `@phase-executor` and `@tdd-generator` subagents in `.claude/agents/`
- If tasks.md is incomplete, run `/speckit.tasks` first
- **Task tool model parameter**: tdd-generator → `opus`, phase-executor → `sonnet`
- For completed tasks, mark as `[X]` in tasks.md
