# Phase 5 RED Tests

## Summary
- Phase: Phase 5 - User Story 1: Resume mode Extract duplicate log prevention
- FAIL test count: 2
- PASS test count: 6 (BasePhaseOrchestrator tests already implemented)
- Test file: `src/etl/tests/test_resume_mode.py`

## Test Categories

### BasePhaseOrchestrator Tests (PASS - Already Implemented in Phase 3)

These tests verify that `BasePhaseOrchestrator.run()` has the Resume logic correctly implemented:

| Test Method | Description | Status |
|------------|-------------|--------|
| `test_resume_mode_loads_from_extract_output` | T056: BasePhaseOrchestrator loads from extract/output/*.jsonl | PASS |
| `test_resume_mode_no_extract_log_appended` | T057: BasePhaseOrchestrator skips Extract in Resume mode | PASS |
| `test_resume_mode_stdout_message` | T058: "Resume mode: Loading from extract/output/*.jsonl" message | PASS |
| `test_extract_output_not_found_message` | T059: "Extract output not found" message when output is empty | PASS |
| `test_resume_mode_preserves_extract_output_items` | Integration: Items are correctly restored | PASS |
| `test_resume_mode_with_multiple_data_dump_files` | Integration: Multiple data-dump files handled | PASS |

### ImportPhase Tests (FAIL - Phase 5 Target)

These tests verify that `ImportPhase.run()` uses the Resume logic from `BasePhaseOrchestrator`:

| Test Method | Description | Status |
|------------|-------------|--------|
| `test_import_phase_run_skips_extract_when_output_exists` | T056-A: ImportPhase.run() should skip Extract when output exists | FAIL |
| `test_import_phase_run_no_new_extract_logs_in_resume_mode` | T057-A: ImportPhase.run() should not append Extract logs in Resume mode | FAIL |

## FAIL Test Details

### test_import_phase_run_skips_extract_when_output_exists

**Test Class**: `TestImportPhaseResumeModeExtractReuse`

**Expected Behavior**:
When `extract/output/` contains `data-dump-*.jsonl` files, `ImportPhase.run()` should:
1. Detect Resume mode via `_should_load_extract_from_output()`
2. Skip the Extract stage (do not call `discover_items()` or `ClaudeExtractor.run()`)
3. Load ProcessingItem from JSONL files via `_load_extract_items_from_output()`

**Actual Behavior**:
`ImportPhase.run()` always calls `discover_items()` and runs Extract stage regardless of existing output.

**Error**:
```
AssertionError: True is not false : ImportPhase.run() should skip Extract stage when extract/output/*.jsonl exists. Current implementation always runs Extract regardless of existing output. Phase 5 GREEN should fix this.
```

### test_import_phase_run_no_new_extract_logs_in_resume_mode

**Test Class**: `TestImportPhaseResumeModeExtractReuse`

**Expected Behavior**:
When Resume mode is active, no new Extract logs should be appended to `pipeline_stages.jsonl`.

**Actual Behavior**:
New Extract logs are appended because `ImportPhase.run()` always runs Extract stage.

**Error**:
```
AssertionError: 3 != 2 : ImportPhase.run() should NOT add Extract logs when extract/output/*.jsonl exists. Expected 2 Extract logs, got 3. Phase 5 GREEN should fix this.
```

## Root Cause Analysis

The issue is in `src/etl/phases/import_phase.py`:

```python
# Line 156-344: ImportPhase.run()
def run(self, phase_data, debug_mode=False, limit=None, session_manager=None):
    ...
    # Line 234-248: Always runs Extract, ignores BasePhaseOrchestrator.run()
    items = extract_stage.discover_items(input_path, chunk=self._chunk)
    extract_ctx = StageContext(...)
    extracted_iter = extract_stage.run(extract_ctx, items)
    extracted = list(extracted_iter)
    ...
```

`ImportPhase.run()` completely overrides `BasePhaseOrchestrator.run()` with its own logic that:
1. Always discovers items from input
2. Always runs Extract stage
3. Does not check for existing Extract output

## Implementation Hints for GREEN Phase

### Option 1: Delegate to BasePhaseOrchestrator.run()

Modify `ImportPhase.run()` to call `super().run()` when Resume mode is detected:

```python
def run(self, phase_data, debug_mode=False, limit=None, session_manager=None):
    # Check Resume mode
    if self._should_load_extract_from_output(phase_data):
        # Delegate to BasePhaseOrchestrator.run() for Resume handling
        return super().run(phase_data, debug_mode)

    # Normal processing (existing code)
    ...
```

### Option 2: Inline Resume Logic

Add Resume mode detection at the start of `ImportPhase.run()`:

```python
def run(self, phase_data, debug_mode=False, limit=None, session_manager=None):
    ...
    # Check if Extract output exists (Resume mode)
    if self._should_load_extract_from_output(phase_data):
        logger.info("Resume mode: Loading from extract/output/*.jsonl")
        extracted = list(self._load_extract_items_from_output(phase_data))
    else:
        logger.info("Extract output not found, processing from input/")
        items = extract_stage.discover_items(input_path, chunk=self._chunk)
        extracted_iter = extract_stage.run(extract_ctx, items)
        extracted = list(extracted_iter)
    ...
```

### Key Methods to Use (from BasePhaseOrchestrator)

- `_should_load_extract_from_output(phase_data)`: Returns `True` if `data-dump-*.jsonl` exists
- `_load_extract_items_from_output(phase_data)`: Yields `ProcessingItem` from JSONL files

## Test Execution

```bash
# Run Phase 5 FAIL tests
python -m unittest src.etl.tests.test_resume_mode.TestImportPhaseResumeModeExtractReuse -v

# Run all Phase 5 tests
python -m unittest src.etl.tests.test_resume_mode.TestResumeModeExtractReuse \
    src.etl.tests.test_resume_mode.TestImportPhaseResumeModeExtractReuse \
    src.etl.tests.test_resume_mode.TestResumeModeExtractLogIntegration -v
```

## Next Steps

1. **GREEN Phase**: Modify `ImportPhase.run()` to use Resume detection logic
2. **Verify**: Run tests to confirm PASS
3. **Refactor**: Apply same pattern to `OrganizePhase.run()` if needed
