# Phase 6: CLI Implementation - Output

**Date**: 2026-01-19
**Status**: Complete

## Summary

Phase 6 implemented the CLI entry point with argparse, providing commands for import, organize, status, retry, and clean operations. All commands follow the contracts/cli.md specification.

## Tasks Completed

| Task | Description | Status |
|------|-------------|--------|
| T066 | Read previous phase output: ph5-output.md | Done |
| T067 | Create test for CLI argument parsing | Done |
| T068 | Create test for CLI exit codes | Done |
| T069 | Implement CLI entry point with argparse | Done |
| T070 | Implement `import` command | Done |
| T071 | Implement `organize` command | Done |
| T072 | Implement `status` command | Done |
| T073 | Implement `retry` command | Done |
| T074 | Implement `clean` command | Done |
| T075 | Create `__main__.py` | Done |
| T076 | Run make test | Done (164 tests pass) |
| T077 | Generate phase output | Done |

## Artifacts Created

### Directory Structure Update

```
src/etl/
├── __init__.py
├── __main__.py           # NEW: Module entry point
├── cli.py                # NEW: CLI implementation
├── core/
│   ├── __init__.py
│   ├── status.py
│   ├── types.py
│   ├── models.py
│   ├── retry.py
│   ├── session.py
│   ├── phase.py
│   ├── stage.py
│   ├── step.py
│   └── config.py
├── phases/
│   ├── __init__.py
│   ├── import_phase.py
│   └── organize_phase.py
├── stages/
│   ├── __init__.py
│   ├── extract/
│   ├── transform/
│   └── load/
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_retry.py
    ├── test_session.py
    ├── test_phase.py
    ├── test_stages.py
    ├── test_import_phase.py
    ├── test_organize_phase.py
    └── test_cli.py          # NEW: CLI tests
```

### File Details

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `src/etl/cli.py` | CLI entry point | create_parser(), main(), run_import(), run_organize(), run_status(), run_retry(), run_clean(), ExitCode |
| `src/etl/__main__.py` | Module entry point | Enables `python -m src.etl` |
| `src/etl/tests/test_cli.py` | CLI tests | 30+ tests |

## CLI Commands

### `import` Command

```bash
python -m src.etl import --input PATH [OPTIONS]

Options:
  --input PATH     Input directory (required)
  --session ID     Reuse existing session ID
  --debug          Enable debug mode
  --dry-run        Preview without processing
  --limit N        Process first N items
```

### `organize` Command

```bash
python -m src.etl organize --input PATH [OPTIONS]

Options:
  --input PATH     Input directory (required)
  --session ID     Reuse existing session ID
  --debug          Enable debug mode
  --dry-run        Preview without processing
  --limit N        Process first N items
```

### `status` Command

```bash
python -m src.etl status [OPTIONS]

Options:
  --session ID     Show specific session
  --all            Show all sessions
  --json           Output as JSON
```

### `retry` Command

```bash
python -m src.etl retry --session ID [OPTIONS]

Options:
  --session ID     Session to retry (required)
  --phase TYPE     Retry specific phase (import|organize)
  --debug          Enable debug mode
```

### `clean` Command

```bash
python -m src.etl clean [OPTIONS]

Options:
  --days N         Clean sessions older than N days (default: 7)
  --dry-run        Preview without deleting
  --force          Skip confirmation
```

## Exit Codes

| Code | Constant | Meaning |
|------|----------|---------|
| 0 | SUCCESS | Operation completed successfully |
| 1 | ERROR | General error |
| 2 | INPUT_NOT_FOUND | Input directory or session not found |
| 3 | OLLAMA_ERROR | Ollama connection error |
| 4 | PARTIAL | Partial success (some items failed) |
| 5 | ALL_FAILED | All items failed |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ETL_DEBUG | Enable debug mode | false |
| ETL_SESSION_DIR | Session directory | .staging/@session/ |
| OLLAMA_HOST | Ollama API host | http://localhost:11434 |
| OLLAMA_TIMEOUT | API timeout (seconds) | 120 |

## Test Results

- **New Tests**: 30+ tests in test_cli.py
- **Total ETL Tests**: 164 tests
- **All Tests**: Pass

### Test Coverage

| Test Class | Tests | Status |
|------------|-------|--------|
| TestCLIArgumentParsing | 17 | Pass |
| TestCLIExitCodes | 10 | Pass |
| TestCLIImportCommand | 2 | Pass |
| TestCLIOrganizeCommand | 1 | Pass |
| TestCLIStatusCommand | 2 | Pass |
| TestCLICleanCommand | 1 | Pass |
| TestCLIMain | 1 | Pass |

## Usage Examples

```bash
# Import Claude export data
python -m src.etl import --input ~/Downloads/claude-export

# Import with debug mode
python -m src.etl import --input ./data/export --debug

# Dry-run import
python -m src.etl import --input ./data/export --dry-run --limit 5

# Organize files
python -m src.etl organize --input ./data/to-organize

# Check session status
python -m src.etl status --all

# Show specific session as JSON
python -m src.etl status --session 20260119_143052 --json

# Retry failed items
python -m src.etl retry --session 20260119_143052 --phase import

# Clean old sessions (dry-run)
python -m src.etl clean --days 7 --dry-run

# Force clean old sessions
python -m src.etl clean --days 7 --force
```

## Next Phase

**Phase 7: Migration (US3)**

Key tasks:
- Add backward-compatible Makefile targets
- Update CLAUDE.md with new ETL commands
- Verify existing legacy tests pass
- Ensure migration path is smooth

## Import Path Examples

```python
# CLI functions
from src.etl.cli import main, create_parser, ExitCode
from src.etl.cli import run_import, run_organize, run_status, run_retry, run_clean
```

## Checkpoint Validation

CLI is operational:

1. argparse-based command parser with subcommands
2. `import` command with --input, --session, --debug, --dry-run, --limit
3. `organize` command with same options as import
4. `status` command with --session, --all, --json
5. `retry` command with --session, --phase, --debug
6. `clean` command with --days, --dry-run, --force
7. Exit codes defined per contracts/cli.md
8. `python -m src.etl` execution works via __main__.py
9. Environment variable support (ETL_DEBUG, ETL_SESSION_DIR)
10. All 164 tests pass
