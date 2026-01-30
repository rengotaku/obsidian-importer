# Command Interface Contract

**Feature**: CLI Module Refactoring | **Version**: 1.0 | **Date**: 2026-01-26

## Overview

This document defines the interface contract that all command modules MUST implement.

## Command Module Interface

Each command module (e.g., `src/etl/cli/commands/import_cmd.py`) MUST implement two functions:

### 1. register() Function

**Signature**:
```python
def register(subparsers: argparse._SubParsersAction) -> None:
    """Register command arguments with argparse subparsers."""
```

**Purpose**: Add command-specific arguments to the main parser

**Contract**:
- MUST add exactly one subparser via `subparsers.add_parser(name, help=...)`
- MUST preserve existing argument names, types, and defaults
- MUST NOT modify global parser state beyond the command's subparser
- MUST document all arguments with `help=` parameter
- MUST call this function only once per command
- MUST NOT have side effects (no file I/O, no network calls)

**Example**:
```python
def register(subparsers):
    parser = subparsers.add_parser(
        "import",
        help="Import Claude/ChatGPT export data"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input directory or ZIP file"
    )
    parser.add_argument(
        "--provider",
        choices=["claude", "openai", "github"],
        default="claude",
        help="Source provider (default: claude)"
    )
    # ... more arguments ...
```

**Validation**:
- Help text must remain identical to pre-refactor version
- Argument names must not change
- Required arguments must remain required
- Default values must be preserved

---

### 2. execute() Function

**Signature**:
```python
def execute(args: argparse.Namespace) -> int:
    """Execute command with parsed arguments."""
```

**Purpose**: Run command logic and return exit code

**Contract**:
- MUST accept `argparse.Namespace` as sole parameter
- MUST return integer exit code from `ExitCode` enum
- MUST NOT modify `args` object (treat as read-only)
- MUST handle all errors gracefully (no uncaught exceptions)
- MAY print to stdout/stderr for user feedback
- MAY perform file I/O, network calls, subprocess execution

**Example**:
```python
def execute(args):
    try:
        # Validate inputs
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input path not found: {input_path}")
            return ExitCode.FILE_NOT_FOUND

        # Execute command logic
        result = run_import(
            input_path=input_path,
            provider=args.provider,
            debug=args.debug,
        )

        # Return appropriate exit code
        if result.success:
            return ExitCode.SUCCESS
        elif result.partial:
            return ExitCode.PARTIAL_SUCCESS
        else:
            return ExitCode.FULL_FAILURE

    except ConnectionError as e:
        print(f"Error: {e}")
        return ExitCode.CONNECTION_ERROR
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ExitCode.ERROR
```

**Exit Codes**:
- `ExitCode.SUCCESS` (0): All operations succeeded
- `ExitCode.ERROR` (1): General error
- `ExitCode.FILE_NOT_FOUND` (2): Input file/session not found
- `ExitCode.CONNECTION_ERROR` (3): Ollama connection error
- `ExitCode.PARTIAL_SUCCESS` (4): Some items succeeded, some failed
- `ExitCode.FULL_FAILURE` (5): All items failed

**Validation**:
- Exit codes must match pre-refactor behavior
- Console output format should remain similar
- Side effects (files created, database updates) must be identical

---

## Module Structure

**File Location**: `src/etl/cli/commands/<command_name>_cmd.py`

**Naming Convention**:
- Import command: `import_cmd.py`
- Organize command: `organize_cmd.py`
- Status command: `status_cmd.py`
- Retry command: `retry_cmd.py`
- Clean command: `clean_cmd.py`
- Trace command: `trace_cmd.py`

**Module Contents**:
```python
"""<Command name> command for ETL pipeline.

Description of what this command does.
"""

import argparse
from pathlib import Path
# ... other imports ...

from src.etl.cli.common import ExitCode, get_session_dir
# ... other internal imports ...

def register(subparsers) -> None:
    """Register <command> command with argparse subparsers."""
    # Implementation

def execute(args: argparse.Namespace) -> int:
    """Execute <command> command."""
    # Implementation

# Optional: Helper functions for this command only
def _validate_inputs(args):
    """Validate command inputs."""
    pass
```

**Module Size**: Each command module should be <300 lines (CODING-STYLE.md guideline)

---

## Command Registry Contract

**Main CLI** (`src/etl/cli/main.py`) is responsible for:

1. **Discovery**: Import all command modules
2. **Registration**: Call each command's `register()` function
3. **Dispatch**: Route parsed arguments to appropriate command's `execute()` function
4. **Exit**: Return exit code from `execute()` to system

**Registry Implementation**:
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

def create_parser():
    parser = argparse.ArgumentParser(
        prog="etl",
        description="ETL Pipeline for Obsidian Knowledge Base"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register all commands
    for command_module in COMMANDS:
        command_module.register(subparsers)

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    # Dispatch to appropriate command
    for command_module in COMMANDS:
        # Match command name from module
        if args.command == command_module.__name__.replace("_cmd", ""):
            return command_module.execute(args)

    # Should never reach here (argparse validates command)
    return ExitCode.ERROR
```

---

## Backward Compatibility Requirements

### 1. Command Line Interface

**MUST Preserve**:
- Command names: `import`, `organize`, `status`, `retry`, `clean`, `trace`
- Argument names: `--input`, `--provider`, `--session`, etc.
- Short flags: None currently used (none to preserve)
- Help text: Exact wording for `--help` output
- Default values: All argument defaults

**Testing**:
```bash
# Help text must be identical
python -m src.etl import --help > new_help.txt
diff old_help.txt new_help.txt  # Must show no differences
```

### 2. Exit Codes

**MUST Preserve**:
- All exit code values from `ExitCode` enum
- Exit code meanings and usage patterns
- Error message formats (where practical)

**Testing**:
```bash
# Exit codes must match
python -m src.etl status --session nonexistent; echo $?  # Should return 2 (FILE_NOT_FOUND)
python -m src.etl import --input test_data; echo $?      # Should return 0 (SUCCESS)
```

### 3. Side Effects

**MUST Preserve**:
- File creation locations (session directories, output files)
- File formats (JSON, Markdown, JSONL)
- Console output patterns (error messages, progress indicators)
- Logging behavior (if any)

### 4. Python API

**MUST Preserve**:
- Entry point: `python -m src.etl` continues to work
- Makefile integration: `make import`, `make organize`, etc.
- Import path: `from src.etl.cli import main` continues to work (via re-export)

---

## Testing Contract

### Unit Testing

Each command module SHOULD be testable independently:

```python
# Example unit test
def test_import_command_validation():
    # Mock args
    args = argparse.Namespace(
        input=Path("nonexistent"),
        provider="claude",
        debug=False,
    )

    # Execute command
    exit_code = import_cmd.execute(args)

    # Verify
    assert exit_code == ExitCode.FILE_NOT_FOUND
```

### Integration Testing

Existing integration tests MUST pass without modification:

```bash
# Run existing test suite
make test  # Must pass 100%
```

---

## Error Handling Contract

### Argument Parsing Errors

**Handled by**: argparse (automatically)
**Exit Code**: 2 (argparse default)
**Example**:
```bash
$ python -m src.etl import
usage: etl import [-h] --input INPUT ...
etl import: error: the following arguments are required: --input
$ echo $?
2
```

### Command Execution Errors

**Handled by**: Command module's `execute()` function
**Exit Code**: From `ExitCode` enum
**Example**:
```bash
$ python -m src.etl import --input nonexistent
Error: Input path not found: nonexistent
$ echo $?
2  # ExitCode.FILE_NOT_FOUND
```

### Uncaught Exceptions

**Handled by**: main.py try-catch wrapper (recommended)
**Exit Code**: 1 (ExitCode.ERROR)
**Example**:
```python
def main():
    try:
        parser = create_parser()
        args = parser.parse_args()
        return dispatch_command(args)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return ExitCode.ERROR
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ExitCode.ERROR
```

---

## Performance Requirements

**Command Startup**:
- MUST complete in <100ms for simple commands (status, help)
- SHOULD complete in <200ms for complex commands (import, organize)

**Help Text Generation**:
- MUST complete in <50ms for `--help`

**Measurement**:
```bash
time python -m src.etl --help
# Should complete in <50ms
```

---

## Documentation Requirements

Each command module MUST include:

1. **Module Docstring**: Describe command purpose
2. **Function Docstrings**: Document register() and execute()
3. **Argument Help Text**: All arguments have help= parameter
4. **Example Usage**: In quickstart.md

**Example**:
```python
"""Import command for ETL pipeline.

Imports conversation data from Claude, ChatGPT, or GitHub exports
and converts them to Obsidian markdown format.

Example:
    python -m src.etl import --input ~/exports/claude --provider claude
"""
```

---

## Summary

**Required Functions**: register(), execute()
**Required Imports**: ExitCode from cli/common
**Required Behavior**: Preserve backward compatibility
**Required Testing**: All existing tests pass
**Required Documentation**: Module and function docstrings

**Contract Violations**: Any deviation from this contract requires spec update
