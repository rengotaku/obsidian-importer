# Phase 4 RED Tests

## Summary

- Phase: Phase 4 - User Story 2 (Failed Item Auto-Retry)
- FAIL test count: 0 (Tests PASS - Logic already implemented in Phase 3)
- Test file: `src/etl/tests/test_resume_mode.py`

## Test Status

**IMPORTANT**: All 3 Phase 4 tests PASS because the retry logic for failed/skipped items was already implemented in Phase 3.

The `CompletedItemsCache.from_jsonl()` method only includes items with `status="success"` in the cache. This means:
- `status="failed"` items are NOT in cache, so they are reprocessed
- `status="skipped"` items are NOT in cache, so they are reprocessed

This behavior satisfies FR-008 and FR-009 from spec.md:
- **FR-008**: System must treat failed items as retry targets
- **FR-009**: System must treat skipped items as retry targets

## Test List

| Test Class | Test Method | Expected Behavior | Status |
|-----------|-------------|-------------------|--------|
| TestRetryFailedItems | test_retry_failed_items | 3 failed items all reprocessed | PASS |
| TestSkipSuccessRetryFailed | test_skip_success_retry_failed | 3 success skipped, 2 failed reprocessed | PASS |
| TestRetrySkippedItems | test_retry_skipped_items | 2 skipped items reprocessed, 1 success skipped | PASS |

## Test Implementations

### T039: test_retry_failed_items

```python
class TestRetryFailedItems(unittest.TestCase):
    """T039: Test that all failed items are reprocessed in Resume mode."""

    def test_retry_failed_items(self):
        """pipeline_stages.jsonl に3件の失敗アイテムがある場合、全て再処理される。

        Given: pipeline_stages.jsonl with 3 failed items
        When: Resume mode runs
        Then: All 3 failed items are reprocessed (not skipped)
        """
        # Create JSONL with 3 failed items
        # Load cache - should be empty (no success items)
        # Run ResumableStage
        # Assert: all 3 items processed
```

### T040: test_skip_success_retry_failed

```python
class TestSkipSuccessRetryFailed(unittest.TestCase):
    """T040: Test that success items are skipped while failed items are retried."""

    def test_skip_success_retry_failed(self):
        """3件成功、2件失敗のログ: 3件スキップ、2件再処理。

        Given: 3 success items + 2 failed items in log
        When: Resume mode runs
        Then: 3 items skipped, 2 items reprocessed
        """
        # Create JSONL with 3 success + 2 failed
        # Load cache - should contain 3 success items
        # Run ResumableStage with 5 items
        # Assert: 2 processed (failed), 3 skipped (success)
```

### T041: test_retry_skipped_items

```python
class TestRetrySkippedItems(unittest.TestCase):
    """T041: Test that skipped items are reprocessed in Resume mode."""

    def test_retry_skipped_items(self):
        """status="skipped" のアイテムは Resume 時に再処理される。

        Given: Items with status="skipped" in log
        When: Resume mode runs
        Then: Skipped items are reprocessed (not skipped again)
        """
        # Create JSONL with 2 skipped + 1 success
        # Load cache - should contain only 1 success item
        # Run ResumableStage with 3 items
        # Assert: 2 processed (skipped), 1 skipped (success)
```

## Implementation Notes

The retry logic is inherent to the `CompletedItemsCache` design:

```python
@dataclass
class CompletedItemsCache:
    items: set[str]
    stage: StageType

    @classmethod
    def from_jsonl(cls, path: Path, stage: StageType) -> "CompletedItemsCache":
        completed_items = set()
        # ... parse JSONL ...
        for record in records:
            # Only include SUCCESS items
            if record.get("status") == "success" and record.get("stage") == stage.value:
                completed_items.add(record["item_id"])
        return cls(items=completed_items, stage=stage)
```

## Next Steps

Since all Phase 4 tests PASS:
1. Phase 4 GREEN implementation is not needed (already done)
2. Proceed to Phase 4 verification tasks (T048-T050)
3. Or proceed to Phase 5 (User Story 3 - Crash Recovery)

## Test Output

```
$ python -m unittest src.etl.tests.test_resume_mode -v 2>&1 | grep -E "test_retry|test_skip_success"
test_retry_failed_items (src.etl.tests.test_resume_mode.TestRetryFailedItems.test_retry_failed_items) ... ok
test_retry_skipped_items (src.etl.tests.test_resume_mode.TestRetrySkippedItems.test_retry_skipped_items) ... ok
test_skip_success_retry_failed (src.etl.tests.test_resume_mode.TestSkipSuccessRetryFailed.test_skip_success_retry_failed) ... ok

----------------------------------------------------------------------
Ran 26 tests in 0.036s

OK
```
