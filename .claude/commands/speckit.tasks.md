---
description: Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts.
handoffs: 
  - label: Analyze For Consistency
    agent: speckit.analyze
    prompt: Run a project analysis for consistency
    send: true
  - label: Implement Project
    agent: speckit.implement
    prompt: Start the implementation in phases
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `.specify/scripts/bash/check-prerequisites.sh --json` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load design documents**: Read from FEATURE_DIR:
   - **Required**: plan.md (tech stack, libraries, structure), spec.md (user stories with priorities)
   - **Optional**: data-model.md (entities), contracts/ (API endpoints), research.md (decisions), quickstart.md (test scenarios)
   - Note: Not all projects have all documents. Generate tasks based on what's available.

3. **Execute task generation workflow**:
   - Load plan.md and extract tech stack, libraries, project structure
   - Load spec.md and extract user stories with their priorities (P1, P2, P3, etc.)
   - If data-model.md exists: Extract entities and map to user stories
   - If contracts/ exists: Map endpoints to user stories
   - If research.md exists: Extract decisions for setup tasks
   - Generate tasks organized by user story (see Task Generation Rules below)
   - Generate dependency graph showing user story completion order
   - Create parallel execution examples per user story
   - Validate task completeness (each user story has all needed tasks, independently testable)

4. **Generate tasks.md**: Use `.specify/templates/tasks-template.md` as structure, fill with:
   - Correct feature name from plan.md
   - Phase 1: Setup tasks (project initialization)
   - Phase 2: Foundational tasks (blocking prerequisites for all user stories)
   - Phase 3+: One phase per user story (in priority order from spec.md)
   - Each phase includes: story goal, independent test criteria, tests (if requested), implementation tasks
   - Final Phase: Polish & cross-cutting concerns
   - All tasks must follow the strict checklist format (see Task Generation Rules below)
   - Clear file paths for each task
   - Dependencies section showing story completion order
   - Parallel execution examples per story
   - Implementation strategy section (MVP first, incremental delivery)

5. **Report**: Output path to generated tasks.md and summary:
   - Total task count
   - Task count per user story
   - Parallel opportunities identified
   - Independent test criteria for each story
   - Suggested MVP scope (typically just User Story 1)
   - Format validation: Confirm ALL tasks follow the checklist format (checkbox, ID, labels, file paths)

Context for task generation: $ARGUMENTS

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by user story to enable independent implementation and testing.

**TDD is MANDATORY**: User Story phases MUST follow TDD workflow (Test Design → Test Implementation RED → Implementation GREEN → Verification).

**Output Language**: All generated files under specs/ (tasks.md, phase outputs, RED test outputs) MUST be written in **Japanese**.

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [P?] [Story?] Description with file path
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **[P] marker**: Include ONLY if task is parallelizable (different files, no dependencies on incomplete tasks)
4. **[Story] label**: REQUIRED for user story phase tasks only
   - Format: [US1], [US2], [US3], etc. (maps to user stories from spec.md)
   - Setup phase: NO story label
   - Foundational phase: NO story label  
   - User Story phases: MUST have story label
   - Polish phase: NO story label
5. **Description**: Clear action with exact file path

**Examples**:

- ✅ CORRECT: `- [ ] T001 Create project structure per implementation plan`
- ✅ CORRECT: `- [ ] T005 [P] Implement authentication middleware in src/middleware/auth.py`
- ✅ CORRECT: `- [ ] T012 [P] [US1] Create User model in src/models/user.py`
- ✅ CORRECT: `- [ ] T014 [US1] Implement UserService in src/services/user_service.py`
- ❌ WRONG: `- [ ] Create User model` (missing ID and Story label)
- ❌ WRONG: `T001 [US1] Create model` (missing checkbox)
- ❌ WRONG: `- [ ] [US1] Create User model` (missing Task ID)
- ❌ WRONG: `- [ ] T001 [US1] Create model` (missing file path)

### Task Organization

1. **From User Stories (spec.md)** - PRIMARY ORGANIZATION:
   - Each user story (P1, P2, P3...) gets its own phase
   - Map all related components to their story:
     - Test Design: Create test skeleton tasks
     - Test Implementation: assertions + RED verification
     - Implementation: Models, Services, Endpoints
     - Verification: GREEN verification + coverage
   - Mark story dependencies (most stories should be independent)

2. **From Contracts**:
   - Map each contract/endpoint → to the user story it serves
   - Each contract → TDD workflow in that story's phase

3. **From Data Model**:
   - Map each entity to the user story(ies) that need it
   - If entity serves multiple stories: Put in earliest story or Setup phase
   - Relationships → service layer tasks in appropriate story phase

4. **From Setup/Infrastructure**:
   - Shared infrastructure → Setup phase (Phase 1)
   - Foundational/blocking tasks → Foundational phase (Phase 2)
   - Story-specific setup → within that story's phase

### Phase Structure

- **Phase 1**: Setup (project initialization) - Main agent execution (NO TDD)
- **Phase 2+**: Foundational/User Stories - TDD flow (if test implementation section exists)
  - Each phase should be a complete, independently testable increment
- **Final Phase**: Polish & Cross-Cutting Concerns - speckit:phase-executor only (NO TDD)

### TDD Phase Structure (Foundational/User Story Phases)

TDD Phase structure:

```markdown
## Phase N: {title}

### Input
- [ ] T0XX Read setup analysis: {FEATURE_DIR}/tasks/ph1-output.md
- [ ] T0XX Read previous phase output: {FEATURE_DIR}/tasks/ph{N-1}-output.md

### Test Implementation (RED)
- [ ] T0XX [USX] Implement tests for {feature} in {test_file}
- [ ] T0XX Verify `make test` FAIL (RED)
- [ ] T0XX Generate RED output: {FEATURE_DIR}/red-tests/ph{N}-test.md

### Implementation (GREEN)
- [ ] T0XX Read RED tests: {FEATURE_DIR}/red-tests/ph{N}-test.md
- [ ] T0XX [USX] Implement {feature} in {src_file}
- [ ] T0XX Verify `make test` PASS (GREEN)

### Verification
- [ ] T0XX Verify `make coverage` ≥80%
- [ ] T0XX Generate phase output: {FEATURE_DIR}/tasks/ph{N}-output.md
```

**TDD Subagent Roles**:
- **speckit:tdd-generator**: Input → Test Implementation (RED) → `red-tests/ph{N}-test.md` output
- **speckit:phase-executor**: `red-tests/ph{N}-test.md` input → Implementation (GREEN) → Verification → `tasks/ph{N}-output.md` output
- RED/GREEN verification tasks are mandatory (for state tracking on interruption)
- For multiple features, repeat "Test Implementation → Implementation" per feature

**REQUIRED**: Each phase MUST end with a `make test` verification task:
```text
- [ ] T0XX Run `make test` to verify all tests pass
```
This ensures incremental validation and prevents regression at each phase boundary.

### Phase Input/Output (REQUIRED)

**Input**: Each phase (except Phase 1) MUST start by reading setup analysis AND previous phase output:
```text
- [ ] T0XX Read setup analysis: {FEATURE_DIR}/tasks/ph1-output.md
- [ ] T0XX Read previous phase output: {FEATURE_DIR}/tasks/ph{N-1}-output.md
```

**Note**: Phase 2 only reads ph1-output.md (setup analysis = previous phase).

**TDD Phase Output (2 stages)**:

1. **RED Output** (speckit:tdd-generator): `{FEATURE_DIR}/red-tests/ph{N}-test.md`
   - Format: `.specify/templates/red-test-template.md`

2. **Phase Output** (speckit:phase-executor): `{FEATURE_DIR}/tasks/ph{N}-output.md`
   - Format: `.specify/templates/phN-output-template.md`

**Directory Structure**:
```
{FEATURE_DIR}/
├── red-tests/           # speckit:tdd-generator output (FAIL test info)
│   ├── ph2-test.md
│   └── ph3-test.md
└── tasks/               # speckit:phase-executor output (Phase completion info)
    ├── ph1-output.md
    └── ph2-output.md
```

### Test Maintenance (REQUIRED for existing codebases)

**When modifying existing code with tests**, you MUST include test update tasks:

1. **New Parameters/Features**: If adding parameters or features to existing functions, add tests covering:
   - New parameter variations (e.g., `subfolder` parameter added → test with/without subfolder)
   - Edge cases (empty string, special formats)
   - Integration with existing behavior

2. **Test Task Format**:
   ```text
   - [ ] T0XX [P] Add tests for new {feature} in {test_file}
   ```

3. **Verification**: Run `make test` after implementation to confirm all tests pass

**Example**: Adding `subfolder` parameter to `get_destination_path()`:
```text
- [ ] T015 [P] Add test_destination_with_subfolder in tests/test_files.py
- [ ] T016 [P] Add test_destination_with_new_subfolder in tests/test_files.py
- [ ] T017 Run make test to verify all tests pass
```
