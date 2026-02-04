# Implementation Plan: CLI Module Refactoring

**Branch**: `036-cli-refactor` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/036-cli-refactor/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Refactor the monolithic `src/etl/cli.py` (1284 lines) into a modular CLI structure where each command is in its own module. The goal is to improve maintainability, discoverability, and testability while preserving 100% backward compatibility with existing commands, tests, and Makefile targets.

**Technical Approach**: Extract 7 commands (import, organize, status, retry, clean, trace) into individual command modules using a command registry pattern. Main CLI module orchestrates command discovery and registration while delegating execution to command modules.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: argparse (stdlib), pathlib (stdlib)
**Storage**: File system (session JSON files, phase JSON files)
**Testing**: unittest (stdlib) via `make test`
**Target Platform**: Linux (development), cross-platform Python
**Project Type**: Single project (CLI tool for ETL pipeline)
**Performance Goals**: CLI startup time <100ms, help text generation <50ms
**Constraints**: No new external dependencies, backward compatibility required, files <800 lines (preferably 200-400)
**Scale/Scope**: 7 commands, ~1284 lines to refactor, existing test suite must pass

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Vault Independence ✅
- **Status**: Pass
- **Rationale**: This is a code refactoring task, not content organization. No Vault interactions required.

### Obsidian Markdown Compliance ✅
- **Status**: Pass
- **Rationale**: No Markdown files are being modified. Refactoring is limited to Python source code.

### Normalization First ✅
- **Status**: Pass
- **Rationale**: Not applicable to code refactoring.

### Genre-Based Organization ✅
- **Status**: Pass
- **Rationale**: Not applicable to code refactoring.

### Automation with Oversight ✅
- **Status**: Pass
- **Rationale**: Refactoring is manual with test validation. Existing test suite provides oversight.

### Quality Standards (Code) ✅
- **Status**: Pass with constraint
- **Constraint**: CODING-STYLE.md requires files <800 lines (preferably 200-400), high cohesion, low coupling
- **Validation**: Current cli.py at 1284 lines violates this. Refactoring explicitly addresses the violation.

**Constitution Check Result**: ✅ PASS - No violations. Refactoring aligns with project quality standards.

### Post-Design Re-evaluation (Phase 1 Complete)

**Date**: 2026-01-26

After completing Phase 1 design artifacts (research.md, data-model.md, contracts/, quickstart.md):

#### Vault Independence ✅
- **Status**: Still Pass
- **Impact**: Design introduces no Vault interactions. CLI structure remains isolated from content organization.

#### Obsidian Markdown Compliance ✅
- **Status**: Still Pass
- **Impact**: No Markdown files affected by CLI refactoring.

#### Normalization First ✅
- **Status**: Still Pass
- **Impact**: Not applicable to code refactoring.

#### Genre-Based Organization ✅
- **Status**: Still Pass
- **Impact**: Not applicable to code refactoring.

#### Automation with Oversight ✅
- **Status**: Still Pass
- **Impact**: Design maintains manual refactoring approach with comprehensive test validation strategy (see research.md Section 5).

#### Quality Standards (Code) ✅
- **Status**: Pass - Design satisfies constraint
- **Design Compliance**:
  - Main CLI module: <200 lines (target defined)
  - Each command module: <300 lines (target defined)
  - Common utilities: <100 lines (target defined)
  - Total reduction: 1284 lines → ~1500 lines across 10 files (avg 150 lines/file)
  - High cohesion: Each command owns its arguments and execution logic
  - Low coupling: Commands communicate only via common.py, not each other

**Post-Design Constitution Check Result**: ✅ PASS - All design decisions align with project constitution. Ready for Phase 2 (Task Breakdown via `/speckit.tasks`).

## Project Structure

### Documentation (this feature)

```text
specs/036-cli-refactor/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

**Current Structure** (before refactoring):
```text
src/etl/
├── cli.py               # 1284 lines - MONOLITHIC
├── __main__.py          # Entry point
├── core/                # ETL core (Session, Phase, Stage)
├── phases/              # Phase implementations (ImportPhase, OrganizePhase)
├── stages/              # Stage implementations (Extract, Transform, Load)
├── utils/               # Utilities (Ollama, chunker, file_id)
├── prompts/             # LLM prompts
└── tests/               # Test suite
```

**Target Structure** (after refactoring):
```text
src/etl/
├── cli/                 # NEW: CLI module directory
│   ├── __init__.py      # Re-export main() for backward compat
│   ├── main.py          # Main entry point (<200 lines)
│   ├── registry.py      # Command discovery/registration
│   ├── common.py        # Shared utilities (get_session_dir, ExitCode)
│   └── commands/        # NEW: Command modules
│       ├── __init__.py
│       ├── import_cmd.py       # import command (<300 lines)
│       ├── organize_cmd.py     # organize command (<300 lines)
│       ├── status_cmd.py       # status command (<300 lines)
│       ├── retry_cmd.py        # retry command (<300 lines)
│       ├── clean_cmd.py        # clean command (<300 lines)
│       └── trace_cmd.py        # trace command (<300 lines)
├── __main__.py          # UPDATED: Import from cli.main
├── core/                # ETL core (NO CHANGES)
├── phases/              # Phase implementations (NO CHANGES)
├── stages/              # Stage implementations (NO CHANGES)
├── utils/               # Utilities (NO CHANGES)
├── prompts/             # LLM prompts (NO CHANGES)
└── tests/               # Test suite (NO CHANGES - must pass as-is)
```

**Structure Decision**: Single project structure with new `cli/` subdirectory. The refactoring creates a new module hierarchy under `src/etl/cli/` to organize the 7 commands, while preserving the existing entry point (`src/etl/__main__.py`) for backward compatibility with `python -m src.etl`.

### Migration Path

1. **Phase 1**: Create new `src/etl/cli/` directory structure
2. **Phase 2**: Extract `ExitCode` and `get_session_dir` to `cli/common.py`
3. **Phase 3**: Extract first command (`import`) to `cli/commands/import_cmd.py`
4. **Phase 4**: Create `cli/registry.py` and `cli/main.py`
5. **Phase 5**: Extract remaining 6 commands one by one
6. **Phase 6**: Update `src/etl/__main__.py` to import from `cli.main`
7. **Phase 7**: Delete old `cli.py` after full validation

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification. All gates pass.

---

## Phase 0: Research & Decisions

### Research Questions

1. **Command Registry Pattern**: How should commands be discovered and registered?
   - Options: Manual registration, auto-discovery via naming convention, decorator pattern
   - Decision criterion: Simplicity, maintainability, no magic

2. **Argument Parser Architecture**: How should argparse integration work?
   - Options: Each command creates its own subparser, central parser delegates to command builders, hybrid
   - Decision criterion: Backward compatibility, testability

3. **Shared Utilities**: What code is shared across commands?
   - Current: `get_session_dir()`, `ExitCode` enum
   - Decision: Extract to `cli/common.py`

4. **Import Path Compatibility**: How to preserve `python -m src.etl` entry point?
   - Options: Keep `__main__.py` importing from new location, symlink, update references
   - Decision criterion: Zero breaking changes

5. **Testing Strategy**: How to validate refactoring without modifying tests?
   - Approach: Run existing test suite as regression test
   - Validation: All tests pass, help output identical

### Research Deliverables

- `research.md` with decisions on:
  - Command registration pattern (manual vs auto-discovery)
  - Argument parser delegation strategy
  - Shared utility extraction plan
  - Import path preservation approach
  - Testing validation approach

---

## Phase 1: Design Artifacts

### Data Model

**Note**: This refactoring doesn't introduce new data structures. Existing entities are preserved:
- `ExitCode` enum (moved to `cli/common.py`)
- `SessionManager`, `PhaseManager` (unchanged in `core/`)
- Command arguments (unchanged, defined in command modules)

See `data-model.md` for detailed preservation plan.

### API Contracts

**Public CLI Interface** (must remain identical):

```python
# Entry point (preserved)
python -m src.etl <command> [options]

# Command signatures (preserved)
python -m src.etl import --input PATH [--provider PROVIDER] [options]
python -m src.etl organize --input PATH [options]
python -m src.etl status [--session ID] [--all] [--json]
python -m src.etl retry --session ID [--phase PHASE] [options]
python -m src.etl clean [--days N] [--dry-run] [--force]
python -m src.etl trace --session ID --target TARGET [options]
```

**Internal Module Interface** (new):

```python
# Command module interface (each command implements this)
class Command:
    name: str                    # Command name (e.g., "import")
    help: str                    # Help text for subparser

    def register(subparsers) -> None:
        """Register command with argparse subparsers."""

    def execute(args: argparse.Namespace) -> int:
        """Execute command, return exit code."""
```

See `contracts/` directory for detailed interface definitions.

### Quickstart

See `quickstart.md` for:
- How to add a new command
- How to modify an existing command
- How to test CLI changes
- Migration checklist for developers

---

## Phase 2: Task Breakdown

**Note**: Phase 2 is executed by `/speckit.tasks` command, NOT by `/speckit.plan`.

Task breakdown will be generated in `tasks.md` covering:
1. Directory structure creation
2. Shared utilities extraction
3. Command module creation (7 commands)
4. Registry implementation
5. Main CLI orchestration
6. Entry point migration
7. Test validation
8. Cleanup

---

## Implementation Notes

### Backward Compatibility Requirements

1. **Entry Point**: `python -m src.etl` must work identically
2. **Command Signatures**: All arguments, options, and help text preserved
3. **Exit Codes**: `ExitCode` enum values unchanged
4. **Test Suite**: All tests pass without modification
5. **Makefile**: All `make` targets work without changes
6. **Session Handling**: `get_session_dir()` logic preserved

### Validation Checklist

- [ ] All 7 commands extracted to separate modules
- [ ] Each command module <300 lines
- [ ] Main CLI module <200 lines
- [ ] `python -m src.etl --help` output identical
- [ ] Each command help text (`--help`) identical
- [ ] All integration tests pass
- [ ] All unit tests pass
- [ ] Code coverage maintained or improved
- [ ] No Makefile changes required
- [ ] Session directory handling works identically

### Risk Mitigation

**Risk**: Breaking existing tests or command behavior
**Mitigation**:
- Incremental extraction (one command at a time)
- Test after each command extraction
- Keep old `cli.py` until full validation

**Risk**: Import path changes break external scripts
**Mitigation**:
- Preserve `python -m src.etl` entry point
- Test Makefile targets after refactoring
- Document any necessary updates

**Risk**: Shared code duplication across commands
**Mitigation**:
- Extract shared utilities to `cli/common.py` first
- Identify common patterns before command extraction
- Avoid premature abstraction

---

## Success Metrics

1. **Code Size**: cli.py deleted, main.py <200 lines, each command <300 lines
2. **Test Pass Rate**: 100% (all existing tests pass)
3. **Help Output**: Identical to pre-refactor (validated via diff)
4. **Code Coverage**: Maintained or improved (measured by `make test`)
5. **Developer Velocity**: New command can be added without modifying core infrastructure

---

## References

- **Current cli.py**: 1284 lines (src/etl/cli.py)
- **CODING-STYLE.md**: Files <800 lines, preferably 200-400
- **Existing Commands**: import, organize, status, retry, clean, trace
- **Test Suite**: src/etl/tests/ (must pass without modification)
- **Makefile**: Root Makefile with CLI targets
