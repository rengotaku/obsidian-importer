# Phase 4 RED Tests

## Summary
- Phase: Phase 4 - extract_knowledge 修正 (User Story 2)
- FAIL test count: 1
- Test files: `tests/pipelines/transform/test_nodes.py`

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_adds_review_reason | When compression ratio is below threshold, item should have `review_reason` field with format "extract_knowledge: body_ratio=X.X% < threshold=Y.Y%" |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_no_review_reason_when_valid | When compression ratio meets threshold, item should NOT have `review_reason` field |

## Test Class: TestExtractKnowledgeReviewReason

### test_extract_knowledge_adds_review_reason

**Purpose**: Verify that low compression ratio items get `review_reason` field added (instead of being excluded).

**Test Setup**:
- Original content: 10,000 chars ("A" * 10000)
- Summary content: 500 chars ("B" * 500)
- Expected body_ratio: 5.0% (500/10000)
- Expected threshold: 10.0% (compression_validator threshold for 10000+ chars)
- Condition: 5.0% < 10.0% -> should add review_reason

**Expected Behavior**:
1. Item should be included in output (not excluded)
2. Item should have `review_reason` field
3. `review_reason` format: "extract_knowledge: body_ratio=5.0% < threshold=10.0%"

**Current Behavior (FAIL reason)**:
- Item IS included in output (passes current min_content_ratio=5.0%)
- Item does NOT have `review_reason` field (not implemented)

### test_extract_knowledge_no_review_reason_when_valid

**Purpose**: Verify that valid compression ratio items do NOT get `review_reason` field.

**Test Setup**:
- Original content: 5,000 chars ("A" * 5000)
- Summary content: 1,000 chars ("B" * 1000)
- Expected body_ratio: 20.0% (1000/5000)
- Expected threshold: 15.0% (compression_validator threshold for 5000-9999 chars)
- Condition: 20.0% >= 15.0% -> should NOT add review_reason

**Expected Behavior**:
1. Item should be included in output
2. Item should NOT have `review_reason` field
3. `generated_metadata` should be present normally

**Current Behavior**: This test currently passes because item is included without review_reason.

## Implementation Hints

### Files to Modify
- `src/obsidian_etl/pipelines/transform/nodes.py`

### Changes Required

1. **Import compression_validator**:
```python
from obsidian_etl.utils.compression_validator import validate_compression
```

2. **Replace ratio check logic** (lines 154-166):

**Current code**:
```python
# Check content compression ratio (detect abnormal shrinkage)
original_len = len(item["content"])
output_len = len(summary_content)
if original_len > 0:
    ratio = output_len / original_len * 100
    min_ratio = params.get("transform", {}).get("min_content_ratio", 5.0)
    if ratio < min_ratio:
        logger.warning(
            f"Low content ratio ({ratio:.1f}% < {min_ratio}%) for {partition_id}: "
            f"{original_len} -> {output_len} chars. Item excluded."
        )
        skipped_empty += 1
        continue  # <-- REMOVE THIS: Don't exclude item
```

**New code**:
```python
# Check content compression ratio using compression_validator
compression_result = validate_compression(
    original_content=item["content"],
    output_content=summary_content,
    body_content=summary_content,  # For extract_knowledge, body = summary_content
    node_name="extract_knowledge",
)

if not compression_result.is_valid:
    # Add review_reason to item (don't exclude)
    item["review_reason"] = (
        f"{compression_result.node_name}: "
        f"body_ratio={compression_result.body_ratio:.1%} < "
        f"threshold={compression_result.threshold:.1%}"
    )
    logger.warning(
        f"Low content ratio for {partition_id}: {item['review_reason']}. "
        f"Item marked for review."
    )
    # DO NOT continue - process the item normally
```

3. **Key difference from current behavior**:
- Current: Item is excluded (skipped) when ratio is below threshold
- New: Item is included with `review_reason` field added

## FAIL Output

```
======================================================================
FAIL: test_extract_knowledge_adds_review_reason (tests.pipelines.transform.test_nodes.TestExtractKnowledgeReviewReason.test_extract_knowledge_adds_review_reason)
圧縮率が基準未達の場合、item に review_reason が追加されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/transform/test_nodes.py", line 1096, in test_extract_knowledge_adds_review_reason
    self.assertIn("review_reason", item)
AssertionError: 'review_reason' not found in {'item_id': 'low-ratio-item', ...}

----------------------------------------------------------------------
Ran 306 tests in 0.812s

FAILED (failures=1)
```

## Notes

- The current implementation uses a flat `min_content_ratio=5.0%` threshold
- The new implementation will use `compression_validator.get_threshold()` which returns size-based thresholds:
  - 10,000+ chars: 10%
  - 5,000-9,999 chars: 15%
  - <5,000 chars: 20%
- This makes the threshold more lenient for large conversations (which naturally compress more)
