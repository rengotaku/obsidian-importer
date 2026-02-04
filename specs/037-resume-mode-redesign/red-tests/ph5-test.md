# Phase 5 RED Tests

## Summary

- Phase: Phase 5 - User Story 3 (Crash Recovery)
- FAIL Tests: **0** (All tests PASS - implementation already complete)
- Test Files: `src/etl/tests/test_resume_mode.py`

## Test Results

All Phase 5 tests **PASS** because the crash recovery functionality was already implemented in Phase 2/3:

- `CompletedItemsCache.from_jsonl()` handles corrupted JSONL gracefully (T008)
- Truncated lines are skipped with warnings
- Valid records are parsed even when surrounded by corrupted data

### Test Classes Created

| Class | Test Method | Status | Description |
|-------|-------------|--------|-------------|
| TestResumeAfterCrash | test_resume_after_crash_with_incomplete_session | PASS | Crash mid-processing recovery |
| TestResumeAfterCrash | test_resume_after_crash_preserves_previous_success | PASS | Previous success preserved after resume |
| TestCorruptedLogRecovery | test_corrupted_log_recovery_with_warning | PASS | Corrupted lines skipped with warning |
| TestCorruptedLogRecovery | test_corrupted_log_recovery_all_corrupted | PASS | All corrupted returns empty cache |
| TestCorruptedLogRecovery | test_corrupted_log_recovery_unicode_issues | PASS | Unicode issues handled gracefully |
| TestPartialLogRecovery | test_partial_log_last_line_truncated | PASS | Truncated last line skipped |
| TestPartialLogRecovery | test_partial_log_empty_last_line | PASS | Trailing empty lines ignored |
| TestPartialLogRecovery | test_partial_log_multiple_crash_recoveries | PASS | Multiple crash/resume cycles |
| TestPartialLogRecovery | test_partial_log_with_failed_items_after_crash | PASS | Failed items retried after crash |

## Test Implementation Details

### T052: test_resume_after_crash

Tests that when a session crashes mid-processing:
1. `pipeline_stages.jsonl` contains records for successfully processed items
2. Resume correctly identifies which items were processed
3. Only unprocessed items are processed on resume

```python
class TestResumeAfterCrash(unittest.TestCase):
    """T052: Test that resume correctly identifies successfully processed items after crash."""

    def test_resume_after_crash_with_incomplete_session(self):
        """Given: 10 items, crash after 5 processed
           When: Resume mode starts
           Then: 5 completed items skipped, 5 remaining processed"""
```

**Result**: PASS - `CompletedItemsCache` correctly identifies completed items.

### T053: test_corrupted_log_recovery

Tests that `CompletedItemsCache.from_jsonl()` handles corrupted JSONL:
1. Valid JSON on some lines
2. Corrupted/invalid JSON on other lines
3. Should log warning and continue processing valid lines

```python
class TestCorruptedLogRecovery(unittest.TestCase):
    """T053: Test that CompletedItemsCache handles corrupted JSONL gracefully."""

    def test_corrupted_log_recovery_with_warning(self):
        """Given: JSONL with mix of valid and corrupted records
           When: from_jsonl() is called
           Then: Valid records parsed, corrupted skipped with warning"""
```

**Result**: PASS - Already implemented in Phase 2 (T008).

### T054: test_partial_log_recovery

Tests recovery from partial JSONL writes (crash mid-write):
1. Some lines are complete valid JSON
2. Last line may be truncated (incomplete JSON from crash)
3. Should recover all complete records, skip truncated

```python
class TestPartialLogRecovery(unittest.TestCase):
    """T054: Test recovery from partial JSONL write (crash mid-write)."""

    def test_partial_log_last_line_truncated(self):
        """Given: JSONL where last line is truncated
           When: from_jsonl() is called
           Then: 49 complete records parsed, truncated line skipped"""
```

**Result**: PASS - JSONL parsing handles incomplete final line.

## Analysis: Why Tests Pass

The Phase 5 functionality was **already implemented** in earlier phases:

### Phase 2 Implementation (T012-T014)

`CompletedItemsCache.from_jsonl()` includes:
- Line-by-line parsing with try/except for JSONDecodeError
- Warning logging for corrupted lines (`logging.warning()`)
- Required field validation (stage, status, item_id)
- Empty line handling

### Key Code (from `src/etl/core/models.py`):

```python
@classmethod
def from_jsonl(cls, jsonl_path: Path, stage: StageType) -> "CompletedItemsCache":
    items: set[str] = set()

    if not jsonl_path.exists():
        return cls(items=items, stage=stage)

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
                # Field validation...
                if record["status"] == "success" and record["stage"] == stage.value:
                    items.add(record["item_id"])
            except json.JSONDecodeError as e:
                logging.warning(f"Skipping line {line_num}: corrupted JSON - {e}")
                continue

    return cls(items=items, stage=stage)
```

This implementation satisfies:
- **FR-014**: System must skip corrupted log records with warning
- **SC-004**: Crash recovery should have at most 1 duplicate processed item

## Test Output

```
test_resume_after_crash_preserves_previous_success ... ok
test_resume_after_crash_with_incomplete_session ... ok
test_corrupted_log_recovery_all_corrupted ... ok (with warnings)
test_corrupted_log_recovery_unicode_issues ... ok (with warnings)
test_corrupted_log_recovery_with_warning ... ok (with warnings)
test_partial_log_empty_last_line ... ok
test_partial_log_last_line_truncated ... ok (with warning)
test_partial_log_multiple_crash_recoveries ... ok (with warnings)
test_partial_log_with_failed_items_after_crash ... ok (with warning)

----------------------------------------------------------------------
Ran 35 tests in 0.055s

OK
```

## Next Steps

Phase 5 GREEN implementation tasks (T058-T060) may be **already complete**:

1. **T058**: Robust JSONL parsing - Already in `CompletedItemsCache.from_jsonl()`
2. **T059**: Warning log for corrupted lines - Already implemented
3. **T060**: JSONL flush after each write - Needs verification in `BaseStage`

The GREEN phase executor should:
1. Verify the existing implementation meets requirements
2. Check if JSONL flush is properly implemented
3. Document the verification results

## Appendix: Warning Log Examples

```
WARNING:root:Skipping line 2: corrupted JSON - Expecting value: line 1 column 1 (char 0)
WARNING:root:Skipping line 3: missing 'stage' field
WARNING:root:Skipping line 50: corrupted JSON - Unterminated string starting at: line 1 column 114 (char 113)
```

These warnings demonstrate FR-014 compliance - corrupted records are logged and skipped.
