# Quickstart: CLI Module Structure

**Feature**: CLI Module Refactoring | **Branch**: 036-cli-refactor | **Date**: 2026-01-26

## Overview

This guide helps developers understand and work with the refactored CLI structure.

## Directory Structure

```text
src/etl/cli/
├── __init__.py          # Re-exports main() for backward compatibility
├── main.py              # CLI entry point, command registry
├── common.py            # Shared utilities (ExitCode, get_session_dir)
└── commands/            # Command implementations
    ├── __init__.py
    ├── import_cmd.py    # Import command
    ├── organize_cmd.py  # Organize command
    ├── status_cmd.py    # Status command
    ├── retry_cmd.py     # Retry command
    ├── clean_cmd.py     # Clean command
    └── trace_cmd.py     # Trace command
```

---

## Adding a New Command

### Step 1: Create Command Module

Create `src/etl/cli/commands/mycommand_cmd.py`:

```python
"""My new command for ETL pipeline.

Brief description of what this command does.
"""

import argparse
from pathlib import Path

from src.etl.cli.common import ExitCode, get_session_dir


def register(subparsers) -> None:
    """Register mycommand with argparse subparsers.

    Args:
        subparsers: Argparse subparsers object
    """
    parser = subparsers.add_parser(
        "mycommand",
        help="Brief help text for command"
    )

    # Add arguments
    parser.add_argument(
        "--input",
        required=True,
        help="Input file or directory"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    # ... more arguments as needed ...


def execute(args: argparse.Namespace) -> int:
    """Execute mycommand.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # Validate inputs
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input not found: {input_path}")
            return ExitCode.FILE_NOT_FOUND

        # Execute command logic
        print(f"Processing {input_path}...")

        # Your implementation here
        # ...

        print("Success!")
        return ExitCode.SUCCESS

    except Exception as e:
        print(f"Error: {e}")
        return ExitCode.ERROR
```

### Step 2: Register Command

Edit `src/etl/cli/main.py`:

```python
# Add import at top
from src.etl.cli.commands import (
    import_cmd,
    organize_cmd,
    status_cmd,
    retry_cmd,
    clean_cmd,
    trace_cmd,
    mycommand_cmd,  # ADD THIS LINE
)

# Add to COMMANDS list
COMMANDS = [
    import_cmd,
    organize_cmd,
    status_cmd,
    retry_cmd,
    clean_cmd,
    trace_cmd,
    mycommand_cmd,  # ADD THIS LINE
]
```

### Step 3: Test Command

```bash
# Test help text
python -m src.etl mycommand --help

# Test execution
python -m src.etl mycommand --input test_data

# Run test suite
make test
```

**That's it!** No other files need modification.

---

## Modifying an Existing Command

### Step 1: Locate Command Module

Find the command module in `src/etl/cli/commands/`:
- Import command: `import_cmd.py`
- Organize command: `organize_cmd.py`
- Status command: `status_cmd.py`
- Retry command: `retry_cmd.py`
- Clean command: `clean_cmd.py`
- Trace command: `trace_cmd.py`

### Step 2: Modify register() or execute()

**Adding a new argument**:
```python
def register(subparsers):
    parser = subparsers.add_parser("import", help="...")

    # Add new argument
    parser.add_argument(
        "--new-option",
        action="store_true",
        help="Description of new option"
    )
```

**Using the new argument**:
```python
def execute(args):
    # Access new argument
    if args.new_option:
        print("New option enabled")

    # Rest of implementation
    # ...
```

### Step 3: Update Tests

Add test coverage for new functionality (if needed).

### Step 4: Validate

```bash
# Run existing tests
make test

# Test new functionality manually
python -m src.etl import --input test_data --new-option
```

---

## Testing CLI Changes

### Unit Testing a Command

The modular CLI structure enables direct unit testing of command logic without full CLI invocation. This improves testability by allowing you to:

1. Test command validation logic independently
2. Test argument registration without executing command logic
3. Mock dependencies and test error handling
4. Run tests faster without subprocess overhead

**Example Test Suite**: `src/etl/tests/cli/test_import_cmd.py`

```python
# src/etl/tests/cli/test_import_cmd.py
import unittest
from argparse import ArgumentParser, Namespace
from pathlib import Path

from src.etl.cli.commands import import_cmd
from src.etl.cli.common import ExitCode


class TestImportCommandValidation(unittest.TestCase):
    """Test import command input validation."""

    def test_import_nonexistent_input(self):
        """Test import command with nonexistent input path.

        Verifies that the command returns INPUT_NOT_FOUND exit code
        when given a path that doesn't exist.
        """
        # Arrange: Create args with nonexistent path
        args = Namespace(
            input=Path("/nonexistent/path/to/data"),
            provider="claude",
            session=None,
            debug=False,
            dry_run=False,
            limit=None,
            no_fetch_titles=False,
            chunk=False,
        )

        # Act: Execute command
        exit_code = import_cmd.execute(args)

        # Assert: Should return INPUT_NOT_FOUND
        self.assertEqual(
            exit_code,
            ExitCode.INPUT_NOT_FOUND,
            "Import should return INPUT_NOT_FOUND for nonexistent input",
        )


class TestImportCommandRegistration(unittest.TestCase):
    """Test import command argument registration."""

    def test_import_help_registration(self):
        """Test that import command registers correctly with argparse.

        Verifies that:
        1. Command name is 'import'
        2. Required --input argument is registered
        3. Optional --provider argument is registered with choices
        4. Default values are set correctly
        """
        # Arrange: Create parser and subparsers
        parser = ArgumentParser(prog="test")
        subparsers = parser.add_subparsers(dest="command")

        # Act: Register import command
        import_cmd.register(subparsers)

        # Assert: Parse test arguments
        args = parser.parse_args(["import", "--input", "/test/path"])

        self.assertEqual(args.command, "import", "Command should be 'import'")
        self.assertEqual(args.input, "/test/path", "--input should be parsed")
        self.assertEqual(
            args.provider, "claude", "--provider default should be 'claude'"
        )

    def test_import_provider_choices(self):
        """Test that --provider argument validates choices correctly."""
        # Arrange: Create parser and subparsers
        parser = ArgumentParser(prog="test")
        subparsers = parser.add_subparsers(dest="command")
        import_cmd.register(subparsers)

        # Act & Assert: Valid providers
        valid_providers = ["claude", "openai", "github"]
        for provider in valid_providers:
            args = parser.parse_args(
                ["import", "--input", "/test/path", "--provider", provider]
            )
            self.assertEqual(
                args.provider, provider, f"--provider should accept '{provider}'"
            )

        # Act & Assert: Invalid provider should raise error
        with self.assertRaises(SystemExit):
            parser.parse_args(
                ["import", "--input", "/test/path", "--provider", "invalid"]
            )
```

**Running the Tests**:

```bash
# Run specific command tests
python -m unittest src.etl.tests.cli.test_import_cmd -v

# Run all CLI tests
python -m unittest discover src.etl.tests.cli -v

# Run with detailed output
python -m unittest src.etl.tests.cli.test_import_cmd.TestImportCommandValidation.test_import_nonexistent_input -v
```

**Test Output Example**:

```
test_import_nonexistent_input ... ok
test_import_help_registration ... ok
test_import_provider_choices ... ok
test_import_required_arguments ... ok
test_import_dry_run_flag ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.002s

OK
```

**Benefits of This Pattern**:

1. **Fast Execution**: Tests run in milliseconds without subprocess overhead
2. **Isolation**: Test command logic independently of CLI framework
3. **Clear Expectations**: Arrange-Act-Assert pattern with descriptive assertions
4. **Easy Mocking**: Can mock filesystem, network, or external dependencies
5. **Granular Testing**: Test individual validation rules and edge cases

### Integration Testing

Run existing test suite:

```bash
# Run all tests
make test

# Run specific test
python -m unittest src.etl.tests.test_cli

# Run with coverage
make test  # (assuming Makefile has coverage configured)
```

### Manual Testing

```bash
# Test help text
python -m src.etl --help
python -m src.etl import --help

# Test with dry-run
python -m src.etl import --input test_data --dry-run

# Test with real data
python -m src.etl import --input ~/exports/claude
```

---

## Common Patterns

### 1. Accessing Session Directory

```python
from src.etl.cli.common import get_session_dir

def execute(args):
    session_dir = get_session_dir()
    print(f"Sessions stored at: {session_dir}")
```

### 2. Returning Exit Codes

```python
from src.etl.cli.common import ExitCode

def execute(args):
    if success:
        return ExitCode.SUCCESS
    elif partial_success:
        return ExitCode.PARTIAL_SUCCESS
    else:
        return ExitCode.FULL_FAILURE
```

### 3. Handling Errors

```python
def execute(args):
    try:
        # Validate inputs first
        if not validate_inputs(args):
            return ExitCode.ERROR

        # Execute logic
        result = perform_operation(args)

        # Return appropriate code
        return ExitCode.SUCCESS if result else ExitCode.ERROR

    except FileNotFoundError:
        print("Error: File not found")
        return ExitCode.FILE_NOT_FOUND
    except ConnectionError:
        print("Error: Cannot connect to Ollama")
        return ExitCode.CONNECTION_ERROR
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ExitCode.ERROR
```

### 4. Delegating to Phase Logic

```python
from src.etl.phases.import_phase import ImportPhase
from src.etl.core.session import SessionManager

def execute(args):
    # Create session
    session = SessionManager.create_session(
        session_dir=get_session_dir(),
        debug=args.debug,
    )

    # Execute phase
    phase = ImportPhase(
        input_path=args.input,
        session=session,
        provider=args.provider,
    )
    phase.execute()

    # Check results
    if phase.success:
        return ExitCode.SUCCESS
    elif phase.partial:
        return ExitCode.PARTIAL_SUCCESS
    else:
        return ExitCode.FULL_FAILURE
```

---

## Debugging Tips

### Enable Debug Mode

Most commands support `--debug` flag:

```bash
python -m src.etl import --input test_data --debug
```

This enables:
- Detailed logging
- Step-by-step processing output
- Error details and stack traces

### Dry-Run Mode

Preview changes without executing:

```bash
python -m src.etl import --input test_data --dry-run
python -m src.etl organize --input test_data --dry-run
python -m src.etl clean --days 7 --dry-run
```

### Check Session Status

View session processing status:

```bash
# Show latest session
python -m src.etl status

# Show specific session
python -m src.etl status --session 20260126_140000

# Show all sessions
python -m src.etl status --all

# JSON output
python -m src.etl status --session 20260126_140000 --json
```

### Trace Item Processing

For debug sessions, trace individual items:

```bash
# Trace specific item
python -m src.etl trace --session 20260126_140000 --target ALL --item conversation_id

# Trace all errors
python -m src.etl trace --session 20260126_140000 --target ERROR

# Show content diffs
python -m src.etl trace --session 20260126_140000 --target ERROR --show-content

# Show error details
python -m src.etl trace --session 20260126_140000 --target ERROR --show-error-details
```

---

## Code Style Guidelines

### File Size

- Main CLI module (`main.py`): <200 lines
- Each command module: <300 lines
- Common utilities (`common.py`): <100 lines

From CODING-STYLE.md: "Files <800 lines, preferably 200-400"

### Function Length

- `register()`: <50 lines (just argument definitions)
- `execute()`: <200 lines (delegate to helper functions if longer)
- Helper functions: <50 lines each

### Naming Conventions

- Command modules: `<command>_cmd.py` (e.g., `import_cmd.py`)
- Functions: Snake case (e.g., `execute()`, `validate_inputs()`)
- Constants: Upper snake case (e.g., `DEFAULT_SESSION_DIR`)
- Private helpers: Leading underscore (e.g., `_validate_inputs()`)

### Documentation

Every command module must have:
- Module docstring explaining command purpose
- Function docstrings for `register()` and `execute()`
- Help text for all arguments (`help=` parameter)

---

## Migration Checklist

If you're migrating existing CLI code:

- [ ] Read current cli.py to understand command logic
- [ ] Create new command module in `cli/commands/`
- [ ] Extract `register()` logic from `create_parser()`
- [ ] Extract `execute()` logic from `run_<command>()`
- [ ] Add command to COMMANDS list in `main.py`
- [ ] Run tests: `make test` (must pass 100%)
- [ ] Validate help text: `python -m src.etl <command> --help`
- [ ] Manual smoke test with sample data
- [ ] Update any documentation references

---

## Getting Help

### Documentation

- **Specification**: `specs/036-cli-refactor/spec.md`
- **Research Decisions**: `specs/036-cli-refactor/research.md`
- **Data Model**: `specs/036-cli-refactor/data-model.md`
- **Command Interface**: `specs/036-cli-refactor/contracts/command-interface.md`

### Example Commands

Browse existing command modules:
- Simple command: `status_cmd.py`
- Complex command: `import_cmd.py`
- Command with subcommands: (none currently, but pattern can be extended)

### Testing

- Run tests: `make test`
- Check coverage: `make test` (with coverage enabled)
- Manual testing: Use `--dry-run` and `--debug` flags

---

## Quick Reference

### Command Module Template

```python
"""<Command> command for ETL pipeline."""

import argparse
from src.etl.cli.common import ExitCode

def register(subparsers) -> None:
    """Register <command> with argparse."""
    parser = subparsers.add_parser("<command>", help="...")
    parser.add_argument("--option", help="...")

def execute(args: argparse.Namespace) -> int:
    """Execute <command>."""
    try:
        # Your logic here
        return ExitCode.SUCCESS
    except Exception as e:
        print(f"Error: {e}")
        return ExitCode.ERROR
```

### Adding Command to Registry

```python
# cli/main.py
from src.etl.cli.commands import <command>_cmd

COMMANDS = [..., <command>_cmd]
```

### Running Command

```bash
python -m src.etl <command> [options]
```

---

## FAQ

**Q: Do I need to update `__main__.py` when adding a command?**
A: No, only `main.py` needs updating.

**Q: Can commands share code?**
A: Yes, via `cli/common.py` or by creating shared utilities. Avoid direct imports between command modules.

**Q: How do I test just my command?**
A: `python -m unittest src.etl.tests.cli.test_<command>_cmd`

**Q: What if my command needs >300 lines?**
A: Extract helper functions or consider splitting into sub-commands. Follow CODING-STYLE.md guidance.

**Q: Can I use external libraries in my command?**
A: Only if already in project dependencies. No new dependencies without approval.

**Q: How do I debug argument parsing?**
A: Add `print(args)` at start of `execute()` or use `--help` to verify registration.

---

## Summary

**Key Files**:
- `cli/main.py`: Command registry
- `cli/common.py`: Shared utilities
- `cli/commands/<command>_cmd.py`: Command implementation

**Key Functions**:
- `register(subparsers)`: Define arguments
- `execute(args)`: Run command logic

**Key Pattern**: Each command is self-contained module with clear interface

**Next Steps**: Read `contracts/command-interface.md` for detailed API contract
