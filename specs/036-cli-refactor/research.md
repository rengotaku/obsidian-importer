# Research: CLI Module Refactoring

**Feature**: CLI Module Refactoring | **Branch**: 036-cli-refactor | **Date**: 2026-01-26

## Research Questions & Decisions

### 1. Command Registry Pattern

**Question**: How should commands be discovered and registered?

**Options Evaluated**:

1. **Manual Registration**: Explicit list of commands in main.py
   - Pros: Simple, explicit, no magic, easy to debug
   - Cons: Requires updating main.py when adding commands
   - Example: `COMMANDS = [ImportCommand, OrganizeCommand, ...]`

2. **Auto-Discovery via Naming Convention**: Scan `commands/` directory for `*_cmd.py` files
   - Pros: No main.py updates needed, follows convention over configuration
   - Cons: Magic behavior, harder to debug, potential name collisions
   - Example: `for module in glob("commands/*_cmd.py"): import_module(module)`

3. **Decorator Pattern**: Commands register themselves via decorator
   - Pros: Declarative, no central list needed
   - Cons: Module side effects, import order matters, too clever
   - Example: `@register_command class ImportCommand: ...`

**Decision**: **Manual Registration** (Option 1)

**Rationale**:
- Aligns with CODING-STYLE.md principle: "No deep nesting, no magic"
- Explicit is better than implicit (Python zen)
- Easy for new developers to understand
- Only 7 commands - manual list is manageable
- Main.py update when adding command is acceptable trade-off for clarity
- Debugging is straightforward

**Implementation**:
```python
# cli/main.py
from src.etl.cli.commands import (
    import_cmd,
    organize_cmd,
    status_cmd,
    retry_cmd,
    clean_cmd,
    trace_cmd,
)

COMMANDS = [
    import_cmd,
    organize_cmd,
    status_cmd,
    retry_cmd,
    clean_cmd,
    trace_cmd,
]
```

**Alternatives Rejected**:
- Option 2 (Auto-discovery): Too much magic, violates project simplicity principle
- Option 3 (Decorator): Module side effects, import order dependency

---

### 2. Argument Parser Architecture

**Question**: How should argparse integration work?

**Options Evaluated**:

1. **Each Command Creates Subparser**: Command module defines `register(subparsers)` function
   - Pros: Command owns its entire definition, easy to test, high cohesion
   - Cons: Each command has argparse dependency
   - Example: `def register(subparsers): parser = subparsers.add_parser("import"); parser.add_argument(...)`

2. **Central Parser Delegates to Command Builders**: main.py passes argument definitions to command modules
   - Pros: Decouples commands from argparse
   - Cons: Extra abstraction layer, more complex, harder to maintain
   - Example: `command.build_args() -> dict` then main.py applies to argparse

3. **Hybrid**: Command defines argument schema, main.py builds parser
   - Pros: Separation of concerns, testable schema
   - Cons: Too complex for 7 commands, premature abstraction
   - Example: `ARGS = {"--input": {"required": True, ...}}`

**Decision**: **Each Command Creates Subparser** (Option 1)

**Rationale**:
- Matches current cli.py structure exactly (backward compatibility)
- High cohesion: argument definition lives with command logic
- Simple to understand and maintain
- argparse is standard library, stable API
- Testing: can validate argument parsing independently
- No premature abstraction

**Implementation**:
```python
# cli/commands/import_cmd.py
def register(subparsers):
    """Register import command with argparse subparsers."""
    parser = subparsers.add_parser("import", help="Import Claude/ChatGPT export data")
    parser.add_argument("--input", required=True, help="Input directory or ZIP file")
    parser.add_argument("--provider", choices=["claude", "openai", "github"], default="claude")
    # ... more arguments ...

def execute(args):
    """Execute import command."""
    # Implementation from run_import()
    return exit_code
```

**Alternatives Rejected**:
- Option 2 (Central parser): Adds complexity without benefit for 7 commands
- Option 3 (Hybrid): Premature abstraction, YAGNI principle violation

---

### 3. Shared Utilities Extraction

**Question**: What code is shared across commands and where should it live?

**Current Shared Code** (analysis of cli.py):

1. **ExitCode Enum**: Used by all commands
   ```python
   class ExitCode(IntEnum):
       SUCCESS = 0
       ERROR = 1
       FILE_NOT_FOUND = 2
       # ... more codes ...
   ```

2. **get_session_dir() Function**: Used by import, organize, status, retry, trace
   ```python
   def get_session_dir() -> Path:
       return Path.home() / "Documents/Obsidian/.staging/@session"
   ```

3. **Imports**: Common imports like `Path`, `argparse`, `json`, etc.
   - Decision: Each command imports what it needs (no shared import file)

**Decision**: Extract to `cli/common.py`

**Rationale**:
- Logical grouping: utilities used by multiple commands
- Avoids circular imports (commands import from common, not each other)
- Small file (<100 lines) with clear purpose
- Follows project structure (utils/ pattern)

**Implementation**:
```python
# cli/common.py
"""Shared utilities for CLI commands."""
from enum import IntEnum
from pathlib import Path

class ExitCode(IntEnum):
    """Exit codes for CLI commands."""
    SUCCESS = 0
    ERROR = 1
    FILE_NOT_FOUND = 2
    CONNECTION_ERROR = 3
    PARTIAL_SUCCESS = 4
    FULL_FAILURE = 5

def get_session_dir() -> Path:
    """Get session directory path."""
    return Path.home() / "Documents/Obsidian/.staging/@session"
```

**No Shared Import File**: Each command imports only what it needs. This:
- Makes dependencies explicit
- Avoids unused imports
- Aligns with Python best practices

---

### 4. Import Path Compatibility

**Question**: How to preserve `python -m src.etl` entry point?

**Current Entry Point**:
```python
# src/etl/__main__.py
from src.etl.cli import main
if __name__ == "__main__":
    sys.exit(main())
```

**Options Evaluated**:

1. **Update __main__.py to Import from New Location**: Change import to `from src.etl.cli.main import main`
   - Pros: Clean, no indirection, explicit
   - Cons: Requires updating __main__.py
   - Example: `from src.etl.cli.main import main`

2. **Re-export from cli/__init__.py**: Keep __main__.py unchanged, re-export main() from cli/__init__.py
   - Pros: Minimal changes to entry point
   - Cons: Extra indirection, __init__.py contains re-export
   - Example: `# cli/__init__.py: from .main import main`

3. **Symlink**: Create symlink from cli.py to cli/main.py
   - Pros: Zero code changes
   - Cons: Not portable (Windows), confusing, hidden indirection
   - Example: `ln -s cli/main.py cli.py`

**Decision**: **Option 2 - Re-export from cli/__init__.py**

**Rationale**:
- Preserves existing `from src.etl.cli import main` in __main__.py
- No changes to external entry point required
- Re-export is common Python pattern for public API
- Portable across platforms (unlike symlink)
- Clear migration path: cli/__init__.py documents the structure

**Implementation**:
```python
# src/etl/cli/__init__.py
"""CLI module for ETL pipeline.

Public API:
- main(): CLI entry point
"""
from src.etl.cli.main import main

__all__ = ["main"]

# src/etl/__main__.py (NO CHANGES)
from src.etl.cli import main
if __name__ == "__main__":
    sys.exit(main())
```

**Alternative Migration Path**:
After refactoring is validated, __main__.py can optionally be updated to:
```python
from src.etl.cli.main import main  # More explicit
```
This is a future optimization, not required for initial refactoring.

**Alternatives Rejected**:
- Option 1: Requires changing entry point file (unnecessary risk)
- Option 3: Not portable, too magical

---

### 5. Testing Strategy

**Question**: How to validate refactoring without modifying tests?

**Current Test Suite** (analysis):
- Location: `src/etl/tests/`
- Framework: unittest (Python standard library)
- Execution: `make test`
- Coverage: Integration tests, unit tests
- Target: No test modifications allowed (regression validation)

**Validation Strategy**:

**Phase 1: Pre-Refactor Baseline**
1. Run full test suite: `make test` → capture output
2. Capture help text for all commands:
   ```bash
   python -m src.etl --help > baseline_help.txt
   python -m src.etl import --help > baseline_import_help.txt
   # ... for all 7 commands ...
   ```
3. Document current exit codes for each command
4. Capture current code coverage: `make test` (with coverage tool)

**Phase 2: During Refactoring**
1. Extract one command at a time
2. After each extraction:
   - Run `make test` → must pass 100%
   - Compare help text: `diff baseline_help.txt current_help.txt` → must be identical
   - Manual smoke test: run command with sample input
3. If any test fails: rollback command extraction, fix, retry

**Phase 3: Post-Refactor Validation**
1. All tests pass: `make test`
2. All help text identical: `diff` on all help outputs
3. Code coverage maintained or improved
4. Makefile targets work: `make import`, `make organize`, etc.
5. Manual regression test: run each command with real data

**Implementation**:
```bash
# Validation script (specs/036-cli-refactor/validate.sh)
#!/bin/bash
set -e

echo "=== Running test suite ==="
make test

echo "=== Validating help text ==="
for cmd in import organize status retry clean trace; do
    python -m src.etl $cmd --help > current_${cmd}_help.txt
    diff baseline_${cmd}_help.txt current_${cmd}_help.txt || {
        echo "ERROR: Help text changed for $cmd"
        exit 1
    }
done

echo "=== Validating Makefile targets ==="
make import INPUT=test_data DRY_RUN=1
make organize INPUT=test_data DRY_RUN=1

echo "✅ All validations passed"
```

**Continuous Validation**:
- Run validation script after each command extraction
- Keep old cli.py until all validations pass
- Only delete cli.py after full validation + manual testing

**Risk Mitigation**:
- Git branching: each command extraction is a separate commit
- Easy rollback if validation fails
- Test-driven refactoring: tests define success

---

## Best Practices Applied

### Python CLI Design Patterns

**Pattern 1: Command Pattern**
- Each command is a separate module with register() and execute() functions
- Decouples command definition from execution
- Source: "Design Patterns" (Gang of Four)

**Pattern 2: Registry Pattern**
- Central registry (main.py) knows about all commands
- Commands don't know about each other
- Prevents circular dependencies

**Pattern 3: Separation of Concerns**
- Parsing (argparse) separate from execution
- Business logic (run_import, etc.) unchanged
- CLI layer is thin wrapper

### Python Standard Library Patterns

**argparse Best Practices**:
- Use subparsers for multi-command CLI (current pattern)
- Keep argument definitions close to command logic
- Document with help= parameter (already done)

**Module Structure**:
- `__init__.py` for public API (re-export main())
- Flat is better than nested (commands/ not commands/import/import_cmd.py)
- Module names match command names (`import_cmd.py` for import command)

---

## Technology Choices

### No New Dependencies

**Requirement**: No new external dependencies allowed

**Validation**:
- argparse: Standard library (already used)
- pathlib: Standard library (already used)
- All imports from standard library or existing project modules

**No Frameworks**: No Click, Typer, argcomplete, etc.
- Rationale: Project uses standard library for CLI
- Consistency with existing codebase
- Reduces maintenance burden

---

## Migration Checklist

**Pre-Refactoring**:
- [x] Research questions answered
- [x] Architectural decisions documented
- [x] Validation strategy defined
- [x] Baseline test results captured

**During Refactoring**:
- [ ] Create directory structure (cli/, cli/commands/)
- [ ] Extract common.py (ExitCode, get_session_dir)
- [ ] Extract import command
- [ ] Validate (tests + help text)
- [ ] Extract organize command
- [ ] Validate
- [ ] Extract status command
- [ ] Validate
- [ ] Extract retry command
- [ ] Validate
- [ ] Extract clean command
- [ ] Validate
- [ ] Extract trace command
- [ ] Validate
- [ ] Create main.py with command registry
- [ ] Update cli/__init__.py with re-export
- [ ] Final validation (all tests + all help text)

**Post-Refactoring**:
- [ ] Delete old cli.py
- [ ] Update CLAUDE.md if needed
- [ ] Document new structure in project docs
- [ ] Create quickstart.md for developers

---

## Conclusion

All research questions resolved. Key decisions:

1. **Manual command registration**: Simple, explicit, no magic
2. **Commands own their subparser**: High cohesion, backward compatible
3. **Shared utilities in common.py**: ExitCode, get_session_dir
4. **Re-export from cli/__init__.py**: Preserves entry point compatibility
5. **Test-driven validation**: Existing tests define success criteria

**Ready for Phase 1**: Design artifacts (data-model.md, contracts/, quickstart.md)

**No Blockers**: All unknowns resolved, no [NEEDS CLARIFICATION] remaining
