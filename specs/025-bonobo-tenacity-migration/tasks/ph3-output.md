# Phase 3: User Story 1 - Tenacity Retry - Output

**Date**: 2026-01-19
**Status**: Complete

## Summary

Phase 3 implemented tenacity-based retry functionality for resilient API calls with exponential backoff and jitter.

## Tasks Completed

| Task | Description | Status |
|------|-------------|--------|
| T023 | Read previous phase output: ph2-output.md | Done |
| T024 | Create test for RetryConfig conversion | Done |
| T025 | Create test for with_retry decorator | Done |
| T026 | Create test for exponential backoff + jitter | Done |
| T027 | Implement RetryConfig with tenacity settings | Done |
| T028 | Implement with_retry decorator | Done |
| T029 | Add retry logging callbacks | Done |
| T030 | Add exception-specific retry conditions | Done |
| T031 | Run make test | Done (all pass) |
| T032 | Generate phase output | Done |

## Artifacts Created

### Directory Structure Update

```
src/etl/
├── __init__.py           # (from Phase 1)
├── core/
│   ├── __init__.py       # (from Phase 1)
│   ├── status.py         # (from Phase 2)
│   ├── types.py          # (from Phase 2)
│   ├── models.py         # (from Phase 2)
│   └── retry.py          # NEW: Tenacity retry utilities
├── phases/
│   └── __init__.py       # (from Phase 1)
├── stages/
│   ├── __init__.py       # (from Phase 1)
│   ├── extract/
│   │   └── __init__.py
│   ├── transform/
│   │   └── __init__.py
│   └── load/
│       └── __init__.py
└── tests/
    ├── __init__.py       # (from Phase 1)
    ├── test_models.py    # (from Phase 2)
    └── test_retry.py     # NEW: Retry tests
```

### File Details

| File | Purpose | Contents |
|------|---------|----------|
| `src/etl/core/retry.py` | Tenacity retry utilities | with_retry decorator, build_tenacity_kwargs, DEFAULT_RETRY_CONFIG |
| `src/etl/tests/test_retry.py` | Retry tests | 23 tests for all retry functionality |

## Implementation Details

### retry.py Functions

| Function | Purpose | Signature |
|----------|---------|-----------|
| `build_tenacity_kwargs` | Convert RetryConfig to tenacity kwargs | `(config: RetryConfig, logger?) -> dict` |
| `create_retry_decorator` | Create retry decorator factory | `(config?, logger?) -> Decorator` |
| `with_retry` | Decorator factory for retry behavior | `(config?, logger?) -> Decorator` |
| `retry_call` | One-off retry call (convenience) | `(func, config?, logger?, *args, **kwargs) -> R` |

### Tenacity Integration

```python
from src.etl.core.retry import with_retry
from src.etl.core.models import RetryConfig

# Default config (3 attempts, 2-30s exponential backoff with jitter)
@with_retry()
def call_ollama(prompt: str) -> str:
    ...

# Custom config
config = RetryConfig(
    max_attempts=5,
    min_wait_seconds=1.0,
    max_wait_seconds=60.0,
    retry_exceptions=(ConnectionError, TimeoutError),
)

@with_retry(config=config, logger=my_logger)
def call_api():
    ...
```

### Features Implemented

| Feature | Description | Tenacity Mapping |
|---------|-------------|------------------|
| Max attempts | Limit retry count | `stop_after_attempt(n)` |
| Exponential backoff | Increasing wait times | `wait_exponential(min, max, multiplier)` |
| Jitter | Randomized wait times | `wait_random_exponential(min, max)` |
| Exception filtering | Retry specific exceptions | `retry_if_exception_type(exceptions)` |
| Before callback | Log before retry | `before_log(logger, level)` |
| After callback | Log after retry | `after_log(logger, level)` |

## Test Results

- **New Tests**: 23 tests in `test_retry.py`
- **Total ETL Tests**: 49 tests (26 models + 23 retry)
- **All Tests**: Pass

### Test Coverage

| Test Class | Tests | Status |
|------------|-------|--------|
| TestRetryConfigConversion | 6 | Pass |
| TestWithRetryDecorator | 6 | Pass |
| TestExponentialBackoffJitter | 3 | Pass |
| TestRetryLoggingCallbacks | 2 | Pass |
| TestExceptionSpecificRetry | 4 | Pass |
| TestCreateRetryDecorator | 2 | Pass |
| **Total** | **23** | **All Pass** |

## Makefile Update

Added ETL Pipeline Tests section to `make test`:

```makefile
@echo "───────────────────────────────────────────────────────────"
@echo "  ETL Pipeline Tests"
@echo "───────────────────────────────────────────────────────────"
@cd $(BASE_DIR) && $(PYTHON) -m unittest discover -s src/etl/tests -t . -v 2>&1
```

## Dependencies Verified

| Dependency | Version | Status |
|------------|---------|--------|
| tenacity | 9.1.2 | Used |
| Python | 3.13 | Verified |

## Next Phase

**Phase 4: User Story 4 - Session Management** (can run in parallel with completed Phase 3)

Key files to create:
- `src/etl/core/session.py` - Session dataclass and SessionManager
- `src/etl/core/phase.py` - Phase dataclass and PhaseManager
- `src/etl/core/stage.py` - Stage dataclass
- `src/etl/core/step.py` - Step dataclass and StepTracker
- `src/etl/core/config.py` - Debug mode configuration
- `src/etl/tests/test_session.py` - Session tests
- `src/etl/tests/test_phase.py` - Phase tests

## Import Path Examples

```python
# Retry utilities
from src.etl.core.retry import with_retry, DEFAULT_RETRY_CONFIG
from src.etl.core.models import RetryConfig

# Usage with default config
@with_retry()
def call_api():
    ...

# Usage with custom config
config = RetryConfig(max_attempts=5, retry_exceptions=(ConnectionError,))
@with_retry(config=config)
def call_api():
    ...
```

## Checkpoint Validation

Tenacity retry functionality is operational and independently testable:

1. `with_retry()` decorator works with default config
2. `with_retry(config=...)` works with custom config
3. Exponential backoff with jitter produces varied wait times
4. Logging callbacks trigger on retry events
5. Exception-specific retry conditions filter correctly
6. Max attempts limit is enforced
