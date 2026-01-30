# Phase 2 RED Tests

## Summary
- Phase: Phase 2 - Foundational (CompletedItemsCache)
- FAIL Test Count: 12 test methods across 5 test classes
- Test File: `src/etl/tests/test_resume_mode.py`

## FAIL Test List

| Test File | Test Class | Test Method | Expected Behavior |
|-----------|------------|-------------|-------------------|
| test_resume_mode.py | TestCompletedItemsCacheEmpty | test_empty_jsonl_returns_empty_cache | Empty JSONL returns cache with len() == 0 |
| test_resume_mode.py | TestCompletedItemsCacheEmpty | test_nonexistent_jsonl_returns_empty_cache | Non-existent JSONL returns empty cache |
| test_resume_mode.py | TestCompletedItemsCacheEmpty | test_is_completed_returns_false_for_empty_cache | Empty cache.is_completed() always returns False |
| test_resume_mode.py | TestCompletedItemsCacheWithSuccess | test_cache_contains_success_items | status=success items are in cache, is_completed returns True |
| test_resume_mode.py | TestCompletedItemsCacheWithSuccess | test_cache_items_set_contains_correct_ids | cache.items set contains correct item_ids |
| test_resume_mode.py | TestCompletedItemsCacheIgnoresFailed | test_failed_items_not_in_cache | status=failed items are NOT in cache |
| test_resume_mode.py | TestCompletedItemsCacheIgnoresFailed | test_mixed_statuses_only_includes_success | Mixed status records, only success extracted |
| test_resume_mode.py | TestCompletedItemsCacheStageFilter | test_stage_filter_transform_only | Filter stage=TRANSFORM only |
| test_resume_mode.py | TestCompletedItemsCacheStageFilter | test_stage_filter_load_only | Filter stage=LOAD only |
| test_resume_mode.py | TestCompletedItemsCacheStageFilter | test_stage_filter_combined_with_status_filter | Stage filter combined with status filter |
| test_resume_mode.py | TestCompletedItemsCacheCorruptedJsonl | test_corrupted_line_skipped_valid_lines_parsed | Corrupted lines skipped, valid lines parsed |
| test_resume_mode.py | TestCompletedItemsCacheCorruptedJsonl | test_partially_corrupted_json_skipped | Partially corrupted JSON skipped |
| test_resume_mode.py | TestCompletedItemsCacheCorruptedJsonl | test_missing_required_fields_skipped | Missing required fields skipped |
| test_resume_mode.py | TestCompletedItemsCacheCorruptedJsonl | test_empty_lines_skipped | Empty/whitespace lines skipped |

## Implementation Hints

### Target File
`src/etl/core/models.py`

### Class Definition
```python
@dataclass
class CompletedItemsCache:
    """Cache for completed items in Resume mode.

    Reads status="success" items from pipeline_stages.jsonl
    and stores them by stage for skip determination.
    """

    items: set[str]
    """Set of successful item_ids."""

    stage: StageType
    """Target stage (TRANSFORM or LOAD)."""

    @classmethod
    def from_jsonl(cls, jsonl_path: Path, stage: StageType) -> "CompletedItemsCache":
        """Load completed items from pipeline_stages.jsonl.

        Args:
            jsonl_path: Path to pipeline_stages.jsonl
            stage: Target stage (TRANSFORM or LOAD)

        Returns:
            CompletedItemsCache instance
        """
        ...

    def is_completed(self, item_id: str) -> bool:
        """Check if item is completed."""
        return item_id in self.items

    def __len__(self) -> int:
        """Return number of completed items."""
        return len(self.items)
```

### JSONL Format
```jsonl
{"timestamp":"2026-01-26T10:00:00+00:00","session_id":"20260126_100000","filename":"conv.json","stage":"transform","step":"extract_knowledge","timing_ms":5000,"status":"success","item_id":"abc-123"}
```

### Filter Logic
1. Read JSONL file line by line
2. Parse each line as JSON (skip invalid lines)
3. Filter by `stage` == StageType.value
4. Filter by `status` == "success"
5. Extract `item_id` to items set

### Edge Cases
- Non-existent file: Return empty cache (no exception)
- Empty file: Return empty cache
- Corrupted JSON lines: Skip with warning log
- Missing item_id: Skip line
- Missing status: Skip line

## FAIL Output Example

```
ERROR: test_resume_mode (unittest.loader._FailedTest.test_resume_mode)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_resume_mode
Traceback (most recent call last):
  File "/path/to/.pyenv/versions/3.13.11/lib/python3.13/unittest/loader.py", line 137, in loadTestsFromName
    module = __import__(module_name)
  File "/path/to/project/src/etl/tests/test_resume_mode.py", line 18, in <module>
    from src.etl.core.models import CompletedItemsCache
ImportError: cannot import name 'CompletedItemsCache' from 'src.etl.core.models' (/path/to/project/src/etl/core/models.py)

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

## Next Steps

1. GREEN Phase: Implement `CompletedItemsCache` in `src/etl/core/models.py`
2. Run `make test` to verify all tests pass
3. Verify coverage >= 80%
