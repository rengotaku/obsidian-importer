# Phase 2 RED Tests

## Summary
- Phase: Phase 2 - User Story 1: E2E output validation via golden file comparison
- FAIL test count: 34 test methods (loaded as 1 error due to ImportError)
- Test file: tests/e2e/test_golden_comparator.py

## FAIL test list

| Test file | Test class | Test method | Expected behavior |
|-----------|-----------|-------------|---------|
| tests/e2e/test_golden_comparator.py | TestSplitFrontmatterAndBody | test_normal_markdown | Markdown -> frontmatter dict + body string |
| tests/e2e/test_golden_comparator.py | TestSplitFrontmatterAndBody | test_no_frontmatter | No YAML -> empty dict + full body |
| tests/e2e/test_golden_comparator.py | TestSplitFrontmatterAndBody | test_empty_content | Empty string -> empty dict + empty body |
| tests/e2e/test_golden_comparator.py | TestSplitFrontmatterAndBody | test_frontmatter_keys_preserved | All YAML keys preserved in dict |
| tests/e2e/test_golden_comparator.py | TestSplitFrontmatterAndBody | test_body_does_not_contain_frontmatter_delimiters | Body excludes --- delimiters |
| tests/e2e/test_golden_comparator.py | TestFrontmatterSimilarity | test_identical_frontmatter | Identical -> score 1.0 |
| tests/e2e/test_golden_comparator.py | TestFrontmatterSimilarity | test_file_id_mismatch_lowers_score | file_id mismatch -> score < 1.0 |
| tests/e2e/test_golden_comparator.py | TestFrontmatterSimilarity | test_missing_keys_lower_score | Missing keys -> score < 1.0 |
| tests/e2e/test_golden_comparator.py | TestFrontmatterSimilarity | test_score_between_zero_and_one | Score range [0.0, 1.0] |
| tests/e2e/test_golden_comparator.py | TestFrontmatterSimilarity | test_similar_title_high_score | Similar title -> score > 0.8 |
| tests/e2e/test_golden_comparator.py | TestFrontmatterSimilarity | test_empty_actual_frontmatter | Empty actual -> score < 0.5 |
| tests/e2e/test_golden_comparator.py | TestBodySimilarity | test_identical_body | Identical text -> 1.0 |
| tests/e2e/test_golden_comparator.py | TestBodySimilarity | test_minor_diff_high_score | Minor diff -> >= 0.8 |
| tests/e2e/test_golden_comparator.py | TestBodySimilarity | test_major_diff_low_score | Major diff -> < 0.9 |
| tests/e2e/test_golden_comparator.py | TestBodySimilarity | test_empty_body | Both empty -> 1.0 |
| tests/e2e/test_golden_comparator.py | TestBodySimilarity | test_one_empty_one_not | One empty -> < 0.5 |
| tests/e2e/test_golden_comparator.py | TestBodySimilarity | test_score_between_zero_and_one | Score range [0.0, 1.0] |
| tests/e2e/test_golden_comparator.py | TestBodySimilarity | test_unicode_content | Japanese text comparison works |
| tests/e2e/test_golden_comparator.py | TestTotalScore | test_perfect_scores | 1.0, 1.0 -> 1.0 |
| tests/e2e/test_golden_comparator.py | TestTotalScore | test_weighted_calculation | 0.3*fm + 0.7*body |
| tests/e2e/test_golden_comparator.py | TestTotalScore | test_zero_scores | 0.0, 0.0 -> 0.0 |
| tests/e2e/test_golden_comparator.py | TestTotalScore | test_body_weighted_more | body weight > fm weight |
| tests/e2e/test_golden_comparator.py | TestTotalScore | test_boundary_threshold | fm=0.8, body=0.95 -> > 0.9 |
| tests/e2e/test_golden_comparator.py | TestTotalScore | test_just_below_threshold | fm=0.5, body=0.9 -> < 0.9 |
| tests/e2e/test_golden_comparator.py | TestCompareDirectories | test_identical_directories | Same files -> passed=True |
| tests/e2e/test_golden_comparator.py | TestCompareDirectories | test_file_count_mismatch | Different count -> passed=False |
| tests/e2e/test_golden_comparator.py | TestCompareDirectories | test_golden_dir_not_exists | Missing dir -> raises error |
| tests/e2e/test_golden_comparator.py | TestCompareDirectories | test_golden_dir_empty | Empty golden -> raises error |
| tests/e2e/test_golden_comparator.py | TestCompareDirectories | test_multiple_files_all_pass | Multiple files pass -> passed=True |
| tests/e2e/test_golden_comparator.py | TestCompareDirectories | test_one_file_below_threshold | One below -> passed=False |
| tests/e2e/test_golden_comparator.py | TestCompareDirectories | test_threshold_parameter | Custom threshold applied correctly |
| tests/e2e/test_golden_comparator.py | TestComparisonReport | test_report_contains_filename | Report has filename field |
| tests/e2e/test_golden_comparator.py | TestComparisonReport | test_report_contains_scores | Report has total/fm/body scores |
| tests/e2e/test_golden_comparator.py | TestComparisonReport | test_report_contains_missing_keys | Report has missing_keys list |
| tests/e2e/test_golden_comparator.py | TestComparisonReport | test_report_contains_diff_summary | Report has diff_summary string |
| tests/e2e/test_golden_comparator.py | TestComparisonReport | test_passed_file_has_no_missing_keys | Passed file -> missing_keys=[] |
| tests/e2e/test_golden_comparator.py | TestComparisonReport | test_report_overall_passed_flag | Report has passed boolean |

## Implementation hints
- `tests/e2e/golden_comparator.py` needs these functions:
  - `split_frontmatter_and_body(content: str) -> tuple[dict, str]` - Parse YAML frontmatter and return (dict, body_text)
  - `calculate_frontmatter_similarity(actual: dict, golden: dict) -> float` - Compare frontmatter dicts (key existence, file_id exact, title/tags via difflib)
  - `calculate_body_similarity(actual: str, golden: str) -> float` - Compare body text via `difflib.SequenceMatcher`
  - `calculate_total_score(frontmatter_score: float, body_score: float) -> float` - Return `frontmatter_score * 0.3 + body_score * 0.7`
  - `compare_directories(actual_dir: str, golden_dir: str, threshold: float) -> dict` - Compare all .md files, return `{"passed": bool, "files": [{"filename", "total_score", "frontmatter_score", "body_score", "missing_keys", "diff_summary"}]}`
- Use only standard library: `difflib.SequenceMatcher`, `yaml` (PyYAML), `os`, `pathlib`
- `split_frontmatter_and_body` should handle `---` delimited YAML frontmatter

## FAIL output
```
ERROR: tests.e2e.test_golden_comparator (unittest.loader._FailedTest.tests.e2e.test_golden_comparator)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.e2e.test_golden_comparator
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/e2e/test_golden_comparator.py", line 22, in <module>
    from tests.e2e.golden_comparator import (
ModuleNotFoundError: No module named 'tests.e2e.golden_comparator'
```

## Existing tests status
- Pre-existing failures: 3 (tests.rag.test_ollama_client) - unrelated
- Pre-existing errors: 22 (tests.rag.*) - unrelated
- New errors: 1 (tests.e2e.test_golden_comparator - ImportError)
- Total: 293 tests, 3 failures, 23 errors
