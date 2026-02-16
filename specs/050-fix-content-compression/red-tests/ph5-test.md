# Phase 5 RED Tests

## Summary
- Phase: Phase 5 - User Story 2: Review Folder Output
- FAIL test count: 6 (4 FAIL + 2 ERROR)
- Test files:
  - tests/pipelines/transform/test_nodes.py
  - tests/pipelines/organize/test_nodes.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/pipelines/transform/test_nodes.py | test_format_markdown_returns_tuple | `format_markdown` should return `tuple(normal_dict, review_dict)` |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_review_reason_to_review_dict | Items with `review_reason` should go to `review_dict` |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_no_review_reason_to_normal_dict | Items without `review_reason` should go to `normal_dict` |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_mixed_items | Mixed items should be correctly distributed |
| tests/pipelines/organize/test_nodes.py | test_embed_frontmatter_with_review_reason | `review_reason` should be embedded in frontmatter |
| tests/pipelines/organize/test_nodes.py | test_embed_frontmatter_review_reason_format | `review_reason` format should be preserved |

## Implementation Hints

### format_markdown (src/obsidian_etl/pipelines/transform/nodes.py)

Current signature:
```python
def format_markdown(
    partitioned_input: dict[str, Callable],
) -> dict[str, str]:
```

Change to:
```python
def format_markdown(
    partitioned_input: dict[str, Callable],
) -> tuple[dict[str, str], dict[str, str]]:
```

Logic:
- Check if item has `review_reason` field
- If yes: add to `review_dict`
- If no: add to `normal_dict`
- Return `(normal_dict, review_dict)`

### embed_frontmatter_fields (src/obsidian_etl/pipelines/organize/nodes.py)

Current `_embed_fields_in_frontmatter`:
```python
def _embed_fields_in_frontmatter(
    content: str,
    genre: str,
    topic: str,
    summary: str,
) -> str:
```

Change to:
```python
def _embed_fields_in_frontmatter(
    content: str,
    genre: str,
    topic: str,
    summary: str,
    review_reason: str | None = None,
) -> str:
```

Add to frontmatter if `review_reason` is not None:
```yaml
review_reason: "extract_knowledge: body_ratio=5.0% < threshold=10.0%"
```

## FAIL Output Example

```
======================================================================
FAIL: test_format_markdown_returns_tuple (tests.pipelines.transform.test_nodes.TestFormatMarkdownReviewOutput)
format_markdown が tuple (normal_dict, review_dict) を返すこと。
----------------------------------------------------------------------
AssertionError: {...} is not an instance of <class 'tuple'>

======================================================================
ERROR: test_format_markdown_review_reason_to_review_dict (tests.pipelines.transform.test_nodes.TestFormatMarkdownReviewOutput)
review_reason を持つアイテムが review dict に含まれること。
----------------------------------------------------------------------
ValueError: not enough values to unpack (expected 2, got 1)

======================================================================
FAIL: test_embed_frontmatter_with_review_reason (tests.pipelines.organize.test_nodes.TestEmbedFrontmatterWithReviewReason)
review_reason が frontmatter に埋め込まれること。
----------------------------------------------------------------------
AssertionError: 'review_reason:' not found in '---\ntitle: 要レビュー記事\n...'
```

## Test Details

### TestFormatMarkdownReviewOutput

Tests added to `tests/pipelines/transform/test_nodes.py`:

1. **test_format_markdown_returns_tuple**
   - Verifies return type is `tuple` with 2 elements
   - Both elements should be `dict`

2. **test_format_markdown_review_reason_to_review_dict**
   - Item with `review_reason="extract_knowledge: body_ratio=5.0% < threshold=10.0%"`
   - Should be in `review_dict`, not in `normal_dict`

3. **test_format_markdown_no_review_reason_to_normal_dict**
   - Item without `review_reason`
   - Should be in `normal_dict`, not in `review_dict`

4. **test_format_markdown_mixed_items**
   - One item with `review_reason`, one without
   - Should have 1 item in each dict

### TestEmbedFrontmatterWithReviewReason

Tests added to `tests/pipelines/organize/test_nodes.py`:

1. **test_embed_frontmatter_with_review_reason**
   - Item has `review_reason="extract_knowledge: body_ratio=5.0% < threshold=10.0%"`
   - Frontmatter should contain `review_reason:` line
   - Should contain `body_ratio=5.0%` and `threshold=10.0%`

2. **test_embed_frontmatter_without_review_reason**
   - Item has no `review_reason`
   - Frontmatter should NOT contain `review_reason:` line
   - Other fields (`genre`, `topic`) should still be present

3. **test_embed_frontmatter_review_reason_format**
   - Verifies exact format preservation
   - Format: `"node_name: body_ratio=X.X% < threshold=Y.Y%"`
