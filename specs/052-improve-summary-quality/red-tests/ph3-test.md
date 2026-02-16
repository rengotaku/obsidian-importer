# Phase 3 RED Tests

## Summary

- Phase: Phase 3 - User Story 3 (Golden Files for Quality Testing)
- FAIL Tests: 1
- SKIP Tests: 7 (dependent on minimum file count)
- PASS Tests: 4
- Test File: tests/test_e2e_golden.py

## Test Classes Implemented

### TestGoldenFilesExist

FR-006: Golden file set (10-12 files) exists in tests/fixtures/golden/

| Test Method | Status | Description |
|-------------|--------|-------------|
| test_golden_directory_exists | PASS | tests/fixtures/golden/ directory exists |
| test_readme_exists | PASS | README.md exists in golden directory |
| test_minimum_golden_files_count | FAIL | At least 10 .md files required (currently 3) |
| test_maximum_golden_files_count | PASS | No more than 12 .md files |
| test_all_golden_files_are_markdown | PASS | All files have .md extension |

### TestGoldenFilesMeetCompressionThreshold

SC-005: All golden files meet compression threshold

| Test Method | Status | Description |
|-------------|--------|-------------|
| test_golden_files_have_valid_frontmatter | SKIP | Needs 10+ files |
| test_golden_files_have_no_review_reason | SKIP | Needs 10+ files |
| test_golden_files_have_required_frontmatter_fields | SKIP | Needs 10+ files |

### TestGoldenFilesPreserveTableStructure

FR-003: Table structure preserved in files containing tables

| Test Method | Status | Description |
|-------------|--------|-------------|
| test_golden_files_with_tables_have_valid_structure | SKIP | Needs 10+ files |
| test_at_least_one_golden_file_contains_table | SKIP | Needs 10+ files |

### TestGoldenFilesSelectionMatrix

FR-007/FR-008: Golden files cover conversation type x size matrix

| Test Method | Status | Description |
|-------------|--------|-------------|
| test_golden_files_cover_multiple_genres | SKIP | Needs 10+ files |
| test_golden_files_cover_multiple_sizes | SKIP | Needs 10+ files |

## FAIL Test Details

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/test_e2e_golden.py | test_minimum_golden_files_count | 10+ golden files in tests/fixtures/golden/ |

## Implementation Hints

- Copy golden files from `data/07_model_output/organized/` and `data/07_model_output/review/`
- Selection matrix (10 files required):
  - Technical: small, medium, large (3 files)
  - Business: small, medium (2 files)
  - Daily: small (1 file)
  - Table: medium, large (2 files)
  - Code: small, medium (2 files)
- Ensure files don't have `review_reason` in frontmatter
- At least one file should contain Markdown tables

## FAIL Output

```
======================================================================
FAIL: test_minimum_golden_files_count (tests.test_e2e_golden.TestGoldenFilesExist.test_minimum_golden_files_count)
Golden file count 3 is less than minimum 10. Files found:
  - 岩盤浴と鼻通りの改善方法.md
  - キッザニアの仕事体験とキッゾシステム.md
  - 温泉BGMシステムと自宅サウナアプリのビジネス可能性.md
----------------------------------------------------------------------
Ran 12 tests in 0.004s

FAILED (failures=1, skipped=7)
```

## Files Created

| File | Purpose |
|------|---------|
| tests/test_e2e_golden.py | E2E golden file validation tests |
| tests/fixtures/golden/README.md | Golden file list template |

## Next Steps

1. GREEN Phase: Add 7 more golden files to tests/fixtures/golden/
2. Select files from data/07_model_output/organized/ and review/
3. Update README.md with actual file list
4. Run `make test` to verify all tests pass
