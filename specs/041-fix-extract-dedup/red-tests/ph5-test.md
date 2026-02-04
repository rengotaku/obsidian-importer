# Phase 5 RED Tests

## Summary
- Phase: Phase 5 - User Story 3 - GitHub Extractor Template Unification
- FAIL test count: 4
- PASS test count: 2 (safety net tests for existing correct behavior)
- Test file: src/etl/tests/test_extractor_template.py

## FAIL test list

| Test file | Test method | Expected behavior |
|-----------|-------------|-------------------|
| test_extractor_template.py | TestGitHubNoDiscoverItemsOverride.test_discover_items_not_defined_on_github_extractor | `discover_items` should NOT be in `vars(GitHubExtractor)` |
| test_extractor_template.py | TestGitHubNoDiscoverItemsOverride.test_discover_items_is_inherited_from_base | `GitHubExtractor.discover_items` should be `BaseExtractor.discover_items` |
| test_extractor_template.py | TestGitHubNoStageTypeOverride.test_stage_type_not_defined_on_github_extractor | `stage_type` should NOT be in `vars(GitHubExtractor)` |
| test_extractor_template.py | TestGitHubDiscoverRawItemsReturnsIterator.test_discover_items_returns_iterator_not_list | `GitHubExtractor.discover_items` should be `BaseExtractor.discover_items` (Iterator, not list) |

## PASS test list (safety net)

| Test file | Test method | Reason for passing |
|-----------|-------------|-------------------|
| test_extractor_template.py | TestGitHubNoStageTypeOverride.test_stage_type_returns_extract_via_inheritance | Override returns same value as base (EXTRACT) |
| test_extractor_template.py | TestGitHubDiscoverRawItemsReturnsIterator.test_discover_raw_items_is_generator_function | `_discover_raw_items()` already uses yield |

## Implementation hints
- Delete `discover_items()` override from `GitHubExtractor` (lines 267-332 in github_extractor.py)
- Delete `stage_type` property override from `GitHubExtractor` (lines 189-194 in github_extractor.py)
- Ensure `_discover_raw_items()` continues to use `yield` (already correct)
- Remove unused `StageType` import if no longer needed after `stage_type` deletion

## FAIL output

```
FAIL: test_discover_items_not_defined_on_github_extractor (src.etl.tests.test_extractor_template.TestGitHubNoDiscoverItemsOverride)
AssertionError: 'discover_items' unexpectedly found in mappingproxy({...})
GitHubExtractor should NOT override discover_items() - should use BaseExtractor template method

FAIL: test_discover_items_is_inherited_from_base (src.etl.tests.test_extractor_template.TestGitHubNoDiscoverItemsOverride)
AssertionError: <function GitHubExtractor.discover_items> is not <function BaseExtractor.discover_items>
GitHubExtractor.discover_items should be inherited from BaseExtractor

FAIL: test_stage_type_not_defined_on_github_extractor (src.etl.tests.test_extractor_template.TestGitHubNoStageTypeOverride)
AssertionError: 'stage_type' unexpectedly found in mappingproxy({...})
GitHubExtractor should NOT override stage_type - should inherit from BaseExtractor

FAIL: test_discover_items_returns_iterator_not_list (src.etl.tests.test_extractor_template.TestGitHubDiscoverRawItemsReturnsIterator)
AssertionError: <function GitHubExtractor.discover_items> is not <function BaseExtractor.discover_items>
GitHubExtractor.discover_items should be BaseExtractor.discover_items (inherited, returning Iterator), not an override returning list
```
