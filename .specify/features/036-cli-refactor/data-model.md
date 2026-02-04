# Data Model: CLI Module Refactoring

**Feature**: CLI Module Refactoring | **Branch**: 036-cli-refactor | **Date**: 2026-01-26

## Overview

This refactoring does NOT introduce new data structures. All existing entities are preserved and relocated to maintain backward compatibility.

## Existing Entities (Preserved)

### 1. ExitCode (Enum)

**Current Location**: `src/etl/cli.py`
**New Location**: `src/etl/cli/common.py`

**Definition**:
```python
class ExitCode(IntEnum):
    """Exit codes for CLI commands."""
    SUCCESS = 0              # Operation completed successfully
    ERROR = 1                # General error
    FILE_NOT_FOUND = 2       # Input file/session not found
    CONNECTION_ERROR = 3     # Ollama connection error
    PARTIAL_SUCCESS = 4      # Some items succeeded, some failed
    FULL_FAILURE = 5         # All items failed
```

**Usage**: Returned by all command execute() functions
**Backward Compatibility**: Values unchanged, import path updates handled by refactoring

---

### 2. Session Directory Path

**Current Location**: `src/etl/cli.py` (get_session_dir function)
**New Location**: `src/etl/cli/common.py`

**Definition**:
```python
def get_session_dir() -> Path:
    """Get session directory path.

    Returns:
        Path to .staging/@session directory
    """
    return Path.home() / "Documents/Obsidian/.staging/@session"
```

**Usage**: Used by import, organize, status, retry, trace commands
**Backward Compatibility**: Logic unchanged, function signature preserved

---

### 3. Command Arguments (Namespace)

**Current Location**: Defined in `create_parser()` in `src/etl/cli.py`
**New Location**: Defined in each command's `register()` function

**Structure**: `argparse.Namespace` object with command-specific attributes

**Import Command Arguments**:
```python
Namespace(
    command="import",
    input=Path,           # Required: input directory or ZIP file
    provider=str,         # "claude" | "openai" | "github"
    session=str | None,   # Optional: reuse session ID
    debug=bool,           # Enable debug mode
    dry_run=bool,         # Preview without processing
    limit=int | None,     # Process first N items
    no_fetch_titles=bool, # Disable URL title fetching
    chunk=bool,           # Enable chunking for large files
)
```

**Organize Command Arguments**:
```python
Namespace(
    command="organize",
    input=Path,           # Required: input directory
    session=str | None,   # Optional: reuse session ID
    debug=bool,           # Enable debug mode
    dry_run=bool,         # Preview without processing
    limit=int | None,     # Process first N items
)
```

**Status Command Arguments**:
```python
Namespace(
    command="status",
    session=str | None,   # Optional: specific session
    all=bool,             # Show all sessions
    json=bool,            # Output as JSON
)
```

**Retry Command Arguments**:
```python
Namespace(
    command="retry",
    session=str,          # Required: session to retry
    phase=str | None,     # Optional: "import" | "organize"
    debug=bool,           # Enable debug mode
)
```

**Clean Command Arguments**:
```python
Namespace(
    command="clean",
    days=int,             # Clean sessions older than N days (default: 7)
    dry_run=bool,         # Preview without deleting
    force=bool,           # Skip confirmation
)
```

**Trace Command Arguments**:
```python
Namespace(
    command="trace",
    session=str,          # Required: session ID
    target=str,           # "ALL" | "ERROR"
    item=str | None,      # Required when target=ALL
    show_content=bool,    # Show content diffs
    show_error_details=bool,  # Show error details
)
```

**Backward Compatibility**: All argument names, types, and defaults preserved

---

## No New Data Structures

This refactoring focuses on code organization, not data modeling. Key points:

1. **No New Classes**: Command modules are functions, not classes (see research.md decision)
2. **No New Enums**: ExitCode is the only enum, preserved as-is
3. **No New Data Classes**: No dataclasses, TypedDict, or NamedTuple introduced
4. **No New Validation Logic**: Argument validation handled by argparse (existing behavior)

---

## Data Flow (Unchanged)

```text
User Input
    ↓
argparse (argument validation)
    ↓
Namespace object (command arguments)
    ↓
Command execute() function
    ↓
Business logic (run_import, run_organize, etc.) [UNCHANGED]
    ↓
Exit code (ExitCode enum)
```

**Key Insight**: Refactoring is structural only. Data flows through the same pipeline with the same types.

---

## Module Boundaries

### Public API (External)

**Entry Point**:
```python
python -m src.etl <command> [options]
```

**Returns**: Integer exit code (0 for success, non-zero for errors)

**Input**: Command-line arguments (strings)
**Output**: Exit code (int), side effects (files created, console output)

---

### Internal API (Command Modules)

**Command Module Interface**:
```python
# Each command module (e.g., import_cmd.py) implements:

def register(subparsers: argparse._SubParsersAction) -> None:
    """Register command arguments with argparse.

    Args:
        subparsers: Argparse subparsers object from main parser

    Returns:
        None (modifies subparsers in-place)
    """
    pass

def execute(args: argparse.Namespace) -> int:
    """Execute command with parsed arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (ExitCode enum value)
    """
    pass
```

**Contracts**:
- `register()` MUST add exactly one subparser
- `register()` MUST preserve existing argument names and types
- `execute()` MUST return ExitCode value
- `execute()` MUST NOT modify args object (read-only)

---

## State Management (Unchanged)

All state is managed by existing core modules, not by CLI:

- **Session State**: `SessionManager` in `src/etl/core/session.py`
- **Phase State**: `PhaseManager` in `src/etl/core/phase.py`
- **File State**: File system (session.json, phase.json)

CLI layer is stateless - it delegates to core modules for all state operations.

---

## Type Safety

**Current Approach**: Minimal type hints, relying on argparse validation

**Post-Refactoring**: Same approach maintained
- argparse handles type validation (type=int, choices=[], etc.)
- No mypy or type checking enforced (project convention)
- Type hints for documentation only (def execute(args: Namespace) -> int)

**Rationale**: Project uses Python 3.11+ but doesn't enforce strict typing. Maintaining consistency.

---

## Validation Rules (Preserved)

All validation logic remains in argparse definitions:

**Required Arguments**:
- import: --input
- organize: --input
- retry: --session
- trace: --session, --item (when target=ALL)

**Constrained Arguments**:
- provider: choices=["claude", "openai", "github"]
- phase: choices=["import", "organize"]
- target: choices=["ALL", "ERROR"]
- days: type=int, must be positive

**Mutually Exclusive**:
- status: --session XOR --all (both allowed, but typically one used)

**Validation Location**: In each command's `register()` function via argparse

---

## Error Handling (Preserved)

**Error Types**:
1. **Parse Errors**: Handled by argparse (exits with code 2)
2. **Validation Errors**: Handled by command logic (returns ExitCode.ERROR)
3. **File Not Found**: Returns ExitCode.FILE_NOT_FOUND
4. **Connection Errors**: Returns ExitCode.CONNECTION_ERROR
5. **Partial Failures**: Returns ExitCode.PARTIAL_SUCCESS
6. **Full Failures**: Returns ExitCode.FULL_FAILURE

**Error Flow**: Unchanged from current implementation

---

## Summary

**No Data Model Changes**: This refactoring is purely structural
**Entities Preserved**:
- ExitCode enum → moved to cli/common.py
- get_session_dir function → moved to cli/common.py
- Command arguments → defined in command modules (not changed, just relocated)

**Key Principle**: Data flows through the refactored code identically to before. Only the file organization changes.
