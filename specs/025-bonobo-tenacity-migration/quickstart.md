# Quickstart: ETL Pipeline Development

**Feature**: 025-bonobo-tenacity-migration
**Date**: 2026-01-19
**Status**: Implemented

## Prerequisites

- Python 3.11+
- Ollama (local LLM)
- Existing venv: `src/converter/.venv/`

## Setup

```bash
# Install dependencies
cd src/converter
source .venv/bin/activate
pip install tenacity

# Or via Makefile
make deps
```

## Basic Usage

### 1. Claude Conversation Import

```bash
# Import Claude export data
make etl-import INPUT=~/.staging/@llm_exports/claude/

# Dry run (preview only)
make etl-import INPUT=~/.staging/@llm_exports/claude/ DRY_RUN=1

# Debug mode with item limit
make etl-import INPUT=~/.staging/@llm_exports/claude/ DEBUG=1 LIMIT=5
```

### 2. File Organization

```bash
# Organize files to appropriate Vaults
make etl-organize INPUT=~/.staging/@index/

# Or use the alias
make organize INPUT=~/.staging/@index/

# Preview mode
make organize INPUT=~/.staging/@index/ DRY_RUN=1
```

### 3. Session Status

```bash
# Show latest session
make etl-status

# Show all sessions
make etl-status ALL=1

# Show specific session
make etl-status SESSION=20260119_143052

# JSON output
make etl-status SESSION=20260119_143052 JSON=1
```

### 4. Retry Failed Items

```bash
# Retry all failed items in a session
make etl-retry SESSION=20260119_143052

# Retry specific phase
make etl-retry SESSION=20260119_143052 PHASE=import

# With debug output
make etl-retry SESSION=20260119_143052 DEBUG=1
```

### 5. Clean Old Sessions

```bash
# Preview sessions to delete (older than 7 days)
make etl-clean DAYS=7 DRY_RUN=1

# Delete with confirmation
make etl-clean DAYS=7

# Force delete without confirmation
make etl-clean DAYS=7 FORCE=1
```

## Development

### Project Structure

```
src/etl/
├── __init__.py            # Package version
├── __main__.py            # CLI entry point (python -m src.etl)
├── cli.py                 # CLI implementation
├── core/
│   ├── config.py          # Configuration and debug mode
│   ├── models.py          # ProcessingItem, StepResult, RetryConfig, ContentMetrics
│   ├── phase.py           # Phase and PhaseManager
│   ├── retry.py           # tenacity wrapper
│   ├── session.py         # Session and SessionManager
│   ├── stage.py           # Stage, BaseStage, BaseStep
│   ├── status.py          # Status enums
│   ├── step.py            # Step and StepTracker
│   └── types.py           # PhaseType, StageType enums
├── phases/
│   ├── import_phase.py    # ImportPhase orchestration
│   └── organize_phase.py  # OrganizePhase orchestration
├── stages/
│   ├── extract/           # Extract stages
│   │   ├── claude_extractor.py
│   │   └── file_extractor.py
│   ├── transform/         # Transform stages
│   │   ├── knowledge_transformer.py
│   │   └── normalizer_transformer.py
│   └── load/              # Load stages
│       ├── session_loader.py
│       └── vault_loader.py
└── tests/                 # Unit tests
```

### Adding a New Stage

```python
# src/etl/stages/transform/my_transformer.py
from src.etl.core.stage import BaseStage, BaseStep
from src.etl.core.types import StageType
from src.etl.core.models import ProcessingItem
from src.etl.core.retry import with_retry


class MyStep(BaseStep):
    """Custom processing step."""

    @property
    def name(self) -> str:
        return "my_step"

    @with_retry()  # tenacity decorator
    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Process a single item."""
        # Your transformation logic
        item.transformed_content = self._transform(item.content)
        return item

    def _transform(self, content: str | None) -> str:
        # Ollama API call or other processing
        return content or ""


class MyTransformer(BaseStage):
    """Custom transform stage."""

    def __init__(self):
        self._steps = [MyStep()]

    @property
    def stage_type(self) -> StageType:
        return StageType.TRANSFORM

    @property
    def steps(self) -> list[BaseStep]:
        return self._steps
```

### Tenacity Retry Configuration

```python
from src.etl.core.retry import with_retry, RetryConfig

# Default configuration
@with_retry()
def call_api():
    ...

# Custom configuration
@with_retry(config=RetryConfig(
    max_attempts=5,
    min_wait_seconds=1.0,
    max_wait_seconds=60.0,
    jitter=True,
    retry_exceptions=(ConnectionError, TimeoutError),
))
def call_slow_api():
    ...

# With logging
import logging
logger = logging.getLogger(__name__)

@with_retry(config=RetryConfig(max_attempts=3), logger=logger)
def call_api_with_logging():
    ...
```

### Content Metrics

```python
from src.etl.core.models import ContentMetrics

# Calculate metrics from sizes
metrics = ContentMetrics.calculate(
    size_in=1000,
    size_out=500,
)
print(f"Delta: {metrics.delta}")  # -0.5 (50% reduction)
print(f"Review required: {metrics.review_required}")  # True

# Anomaly detection thresholds:
# - delta <= -0.5: 50%+ compression -> review required
# - delta >= 2.0: 3x+ increase -> review required
```

## Testing

```bash
# Run all tests
make test

# Run ETL tests only
cd /path/to/project
python -m unittest discover -s src/etl/tests -t . -v

# Run specific test
python -m unittest src.etl.tests.test_session -v
python -m unittest src.etl.tests.test_models -v
```

## Debug Tips

### Session Folder Inspection

```bash
# List all sessions
ls -la .staging/@session/

# Show latest session
ls -la .staging/@session/ | tail -1

# View session.json
cat .staging/@session/20260119_143052/session.json | jq

# View phase.json
cat .staging/@session/20260119_143052/import/phase.json | jq
```

### Debug Mode Logging

```bash
# Enable debug mode
make etl-import INPUT=~/.staging/@llm_exports/claude/ DEBUG=1

# Debug logs are written to each Stage folder
cat .staging/@session/20260119_143052/import/extract/debug.log
```

### Error Investigation

```bash
# Find sessions with errors
make etl-status ALL=1 | grep -v completed

# View phase status with error counts
cat .staging/@session/20260119_143052/import/phase.json | jq '.error_count'

# Retry failed items
make etl-retry SESSION=20260119_143052
```

## Migration from Legacy

| Legacy Command | New Command | Notes |
|----------------|-------------|-------|
| `make llm-import` | `make etl-import INPUT=...` | INPUT required |
| N/A | `make organize INPUT=...` | New alias |
| `make retry` | `make etl-retry SESSION=...` | SESSION required |
| `make status` | `make etl-status` | Enhanced features |

Legacy commands are preserved for backward compatibility.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Input not found |
| 3 | Ollama error |
| 4 | Partial success (some items failed) |
| 5 | All items failed |
