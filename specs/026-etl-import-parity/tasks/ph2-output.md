# Phase 2 Output: Foundational (Framework Extension)

## Summary

| Metric | Value |
|--------|-------|
| Phase | Phase 2 - Foundational |
| Tasks | 11/11 completed |
| Status | Completed |
| Tests | 184 tests passed |

## Completed Tasks

| # | Task | Status |
|---|------|--------|
| T013 | Read previous phase output | Done |
| T014 | Add StageLogRecord dataclass | Done |
| T015 | Add _write_jsonl_log() to BaseStage | Done |
| T016 | Add _write_debug_output() to BaseStage | Done |
| T017 | Modify BaseStage.run() for JSONL logging | Done |
| T018 | Modify _process_item() for DEBUG output | Done |
| T019 | Add pipeline_stages.jsonl path to Phase | Done |
| T020 | Add test for JSONL log output | Done |
| T021 | Add test for DEBUG mode output | Done |
| T022 | Run make test | Done (184 tests passed) |
| T023 | Generate phase output | Done |

## Modified Files

### src/etl/core/models.py

Added `StageLogRecord` dataclass:

```python
@dataclass
class StageLogRecord:
    """Log record for Stage processing in JSONL format."""

    timestamp: str          # ISO8601 format
    session_id: str         # Session identifier
    filename: str           # Source filename
    stage: str              # Stage name (extract, transform, load)
    step: str               # Step name
    timing_ms: int          # Processing time in milliseconds
    status: str             # success, failed, skipped
    file_id: str | None = None
    skipped_reason: str | None = None
    before_chars: int | None = None
    after_chars: int | None = None
    diff_ratio: float | None = None
```

### src/etl/core/stage.py

Added to `BaseStage`:

1. **`_write_jsonl_log()`**: Writes JSONL log record after each item processing
   - Called automatically from `run()` after each item
   - Step implementers do not need to call this directly
   - Records: timestamp, session_id, filename, stage, step, timing_ms, status, file_id, metrics

2. **`_write_debug_output()`**: Writes debug JSON file in DEBUG mode
   - Called from `_process_item()` after each step when `debug_mode=True`
   - Records: item state, content preview, metadata, error details (if any)
   - Output location: `{stage_output}/debug/{filename}_{stage}.json`

3. **Modified `run()`**:
   - Added timing measurement with `time.perf_counter()`
   - Calls `_write_jsonl_log()` after each item (success or failure)
   - Calculates content metrics (before_chars, after_chars, diff_ratio)

4. **Modified `_process_item()`**:
   - Calls `_write_debug_output()` after each step (DEBUG mode only)
   - Calls `_write_debug_output()` on skipped items (DEBUG mode only)
   - Calls `_write_debug_output()` with error on failed items (DEBUG mode only)

### src/etl/core/phase.py

Added property to `Phase`:

```python
@property
def pipeline_stages_jsonl(self) -> Path:
    """Path to pipeline_stages.jsonl log file."""
    return self.base_path / "pipeline_stages.jsonl"
```

### src/etl/tests/test_stages.py

Added test classes:

1. **`TestStageJSONLLog`** (US7 - 3 tests):
   - `test_jsonl_log_created_on_success`: Verifies JSONL file creation and content
   - `test_jsonl_log_records_failure`: Verifies failed items are logged
   - `test_jsonl_log_records_content_metrics`: Verifies before/after chars and diff_ratio

2. **`TestStageDebugOutput`** (US8 - 3 tests):
   - `test_debug_output_not_created_when_disabled`: No debug files without debug_mode
   - `test_debug_output_created_when_enabled`: Debug files created with debug_mode
   - `test_debug_output_includes_error_on_failure`: Error details in debug output

3. **`TestStageLogRecord`** (3 tests):
   - `test_to_dict_required_fields`: Required fields serialization
   - `test_to_dict_excludes_none_optional_fields`: None fields excluded
   - `test_to_dict_includes_set_optional_fields`: Set fields included

## Key Design Decisions

### 1. Framework Automatic Output

Step implementers do not need to write logging code. The framework automatically:
- Measures timing per item
- Calculates content metrics
- Writes JSONL log after each item
- Writes debug output in DEBUG mode

### 2. JSONL Log Location

`pipeline_stages.jsonl` is written to the phase folder (e.g., `.staging/@session/20260119_120000/import/pipeline_stages.jsonl`).

Each line is a JSON object:
```json
{"timestamp":"2026-01-19T12:00:00.123456+00:00","session_id":"20260119_120000","filename":"conversation.json","stage":"extract","step":"parse_json","timing_ms":45,"status":"success","file_id":"abc123","before_chars":1500,"after_chars":2000,"diff_ratio":1.333}
```

### 3. DEBUG Output Location

Debug files are written to `{stage_output}/debug/`:
```
import/
  extract/
    output/
      debug/
        conversation_extract.json
  transform/
    output/
      debug/
        conversation_transform.json
```

### 4. Status Capture Timing

- JSONL log captures **final** status (after all steps complete)
- DEBUG output captures **intermediate** status (during step execution)

## Test Results

```
Ran 184 tests in 0.220s
OK
```

All existing tests pass. No regressions introduced.

## Next Phase Prerequisites

Phase 3 (US1 + US2 - Ollama Knowledge Extraction) can now proceed with:

1. Framework automatically outputs JSONL logs for all items
2. DEBUG mode output available for debugging
3. `src.etl.utils` module with Ollama, chunker, file_id utilities ready
4. `src.etl.prompts/` with knowledge extraction prompts ready

## Dependencies for Phase 3

- `KnowledgeTransformer` in `src/etl/stages/transform/knowledge_transformer.py`
  - Will use `KnowledgeExtractor` from `src.etl.utils`
  - Will use `generate_file_id` from `src.etl.utils`
- `ClaudeExtractor` in `src/etl/stages/extract/claude_extractor.py`
- Tests in `src/etl/tests/test_knowledge_transformer.py`
