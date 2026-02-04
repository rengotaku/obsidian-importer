# Feature Specification: CLI Module Refactoring

**Feature Branch**: `036-cli-refactor`
**Created**: 2026-01-26
**Status**: Draft
**Input**: User description: "src/etl/cli.pyが肥大化しているのでリファクタリング"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Code Maintainability (Priority: P1)

Developers need to understand and modify CLI command definitions without navigating through a 1284-line file. Each command should be defined in its own module, making it easy to locate and update specific command behavior.

**Why this priority**: This is the core problem. The current cli.py file at 1284 lines violates the "many small files" principle from CODING-STYLE.md and makes maintenance difficult.

**Independent Test**: Successfully extract one command (e.g., import) into its own module. Run `python -m src.etl import --help` and verify it works identically to before.

**Acceptance Scenarios**:

1. **Given** cli.py has 7 command definitions, **When** developer wants to modify the import command, **Then** developer can find the import command definition in a dedicated module (src/etl/cli/commands/import_cmd.py or similar)
2. **Given** each command is in a separate file, **When** running `make test`, **Then** all existing tests pass without modification
3. **Given** refactored CLI structure, **When** running any CLI command with existing options, **Then** behavior remains identical to pre-refactor version

---

### User Story 2 - Code Discoverability (Priority: P2)

New contributors need to understand CLI structure and add new commands without reading a monolithic file. The CLI architecture should follow a clear pattern where command registration, argument parsing, and command execution are separated.

**Why this priority**: Improves onboarding and reduces cognitive load for contributors. Important but not as critical as basic maintainability.

**Independent Test**: A new developer can add a simple "version" command by following the established pattern without modifying core CLI infrastructure.

**Acceptance Scenarios**:

1. **Given** clear CLI module structure, **When** new developer wants to add a command, **Then** they can copy an existing command module and modify it
2. **Given** separated concerns (parsing, execution, validation), **When** reviewing code, **Then** each responsibility is in a distinct, well-named module
3. **Given** consistent command structure, **When** developer needs to add a new argument to a command, **Then** the change is localized to that command's module

---

### User Story 3 - Test Coverage (Priority: P3)

Each CLI command should be independently testable without running the entire CLI infrastructure. Unit tests should be able to test command logic without invoking argparse.

**Why this priority**: Improves testability but not a blocking issue. Current code is testable, just not as cleanly as desired.

**Independent Test**: Write a unit test for one command's logic that doesn't require argparse or subprocess calls.

**Acceptance Scenarios**:

1. **Given** separated command logic, **When** writing unit tests, **Then** tests can directly call command functions without CLI parsing
2. **Given** command validation logic, **When** testing edge cases, **Then** tests can validate inputs without full CLI invocation
3. **Given** command execution functions, **When** testing, **Then** tests can mock dependencies cleanly

---

### Edge Cases

- What happens when argparse dependency changes or needs replacement? (Should be isolated in one place)
- How does the system handle backward compatibility if CLI structure changes? (Tests should catch any breakage)
- What happens if a command needs to share code with another command? (Should use shared utilities, not inheritance)
- How does the system handle global CLI options vs command-specific options? (Should have clear separation)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST preserve all existing CLI command signatures (import, organize, status, retry, clean, trace) without any changes to user-facing arguments or behavior
- **FR-002**: System MUST separate command definitions into individual modules (one module per command)
- **FR-003**: System MUST maintain a central command registry or loader that discovers and registers commands
- **FR-004**: Each command module MUST define its own argument parser and execution logic
- **FR-005**: System MUST maintain backward compatibility with existing Makefile targets and scripts
- **FR-006**: System MUST preserve all existing exit codes (ExitCode enum values)
- **FR-007**: System MUST keep main() as the entry point in cli.py or __main__.py
- **FR-008**: Refactored code MUST follow project coding style (CODING-STYLE.md): files <800 lines, high cohesion, low coupling
- **FR-009**: System MUST preserve session directory handling logic (get_session_dir)
- **FR-010**: All existing tests MUST pass without modification (test suite validates backward compatibility)

### Key Entities

- **Command Module**: Represents a single CLI command (import, organize, etc.) with its argument parser and execution logic
- **Command Registry**: Central mechanism for discovering and registering command modules
- **CLI Parser**: Top-level argparse configuration that delegates to command modules
- **Command Handler**: Execution function for each command that takes parsed arguments and returns exit code

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: cli.py (or main CLI module) reduces to under 200 lines
- **SC-002**: Each command module is under 300 lines
- **SC-003**: All existing integration tests pass without modification
- **SC-004**: Code coverage remains at or above current level (measured by `make test`)
- **SC-005**: No changes required to existing Makefile commands (make import, make organize, etc.)
- **SC-006**: New command can be added by creating a single new module file without modifying core CLI infrastructure
- **SC-007**: CLI help output (`--help`) remains identical for all commands

## Scope *(mandatory)*

### In Scope

- Splitting cli.py into multiple command modules
- Creating command registration/discovery mechanism
- Reorganizing src/etl/cli/ directory structure
- Updating imports in affected modules
- Ensuring backward compatibility

### Out of Scope

- Changing CLI command signatures or behavior
- Adding new commands
- Modifying command execution logic (phases, stages)
- Changing argparse to another CLI library
- Modifying Makefile beyond necessary import updates
- Updating test implementations (tests should pass as-is)

## Assumptions *(mandatory)*

- Python 3.11+ environment (from project requirements)
- argparse remains the CLI library (no replacement)
- Current test suite is comprehensive enough to validate backward compatibility
- Command execution logic (run_import, run_organize, etc.) is already well-structured
- Session management and Phase/Stage architecture remain unchanged
- ETL pipeline core (src/etl/core/) is stable and not part of this refactor

## Dependencies *(optional)*

### Internal Dependencies

- src/etl/core/ modules (Session, Phase, Stage, etc.) - no changes expected
- src/etl/phases/ modules - no changes expected
- Existing test suite must validate refactoring
- Makefile targets must work with new structure

### External Dependencies

- argparse (standard library)
- pathlib (standard library)
- No new external dependencies allowed

## References *(optional)*

- Current cli.py: 1284 lines with 7 commands (import, organize, status, retry, clean, trace)
- CODING-STYLE.md: "MANY SMALL FILES > FEW LARGE FILES" (200-400 lines typical, 800 max)
- Project uses Python 3.11+, standard library only for CLI
- Existing command structure uses subparsers in argparse
