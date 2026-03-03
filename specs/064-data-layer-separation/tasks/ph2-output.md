# Phase 2 Output: User Story 1 - Pipeline Data Integrity

**Date**: 2026-03-03
**Status**: Completed
**User Story**: US1 - パイプライン実行時のデータ整合性

## Executed Tasks

- [x] T011 Read: `specs/064-data-layer-separation/red-tests/ph2-test.md`
- [x] T012 [US1] Edit: `conf/base/catalog.yml` の `classified_items` パスを `data/05_model_input/classified` に変更
- [x] T013 [P] [US1] Edit: `conf/base/catalog.yml` の `existing_classified_items` パスを `data/05_model_input/classified` に変更
- [x] T014 [P] [US1] Edit: `conf/base/catalog.yml` の `topic_extracted_items` パスを `data/05_model_input/topic_extracted` に変更
- [x] T015 [P] [US1] Edit: `conf/base/catalog.yml` の `normalized_items` パスを `data/05_model_input/normalized` に変更
- [x] T016 [P] [US1] Edit: `conf/base/catalog.yml` の `cleaned_items` パスを `data/05_model_input/cleaned` に変更
- [x] T017 [P] [US1] Edit: `conf/base/catalog.yml` の `vault_determined_items` パスを `data/05_model_input/vault_determined` に変更
- [x] T018 [P] [US1] Edit: `conf/base/catalog.yml` の `organized_items` パスを `data/05_model_input/organized` に変更
- [x] T019 [US1] Create: `data/05_model_input/` ディレクトリ構造を作成（.gitkeep 含む）
- [x] T020 Verify: `make test` PASS (GREEN)
- [x] T021 Verify: `make test` がすべてのテストを通過

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| conf/base/catalog.yml | Modified | Updated 7 JSON datasets: paths changed from `data/07_model_output/` to `data/05_model_input/`, kedro-viz layer changed from `model_output` to `model_input` |
| data/05_model_input/classified/.gitkeep | New | Directory placeholder for classified JSON files |
| data/05_model_input/topic_extracted/.gitkeep | New | Directory placeholder for topic_extracted JSON files |
| data/05_model_input/normalized/.gitkeep | New | Directory placeholder for normalized JSON files |
| data/05_model_input/cleaned/.gitkeep | New | Directory placeholder for cleaned JSON files |
| data/05_model_input/vault_determined/.gitkeep | New | Directory placeholder for vault_determined JSON files |
| data/05_model_input/organized/.gitkeep | New | Directory placeholder for organized JSON files |

## Test Results

```
test_catalog_paths.py - All 25 tests PASS:
  - 14 JSON dataset tests (path & layer verification)
  - 8 MD dataset tests (path & layer verification)
  - 3 dataset type consistency tests

Previously failing tests (now PASS):
  ✅ test_classified_items_path
  ✅ test_classified_items_layer
  ✅ test_existing_classified_items_path
  ✅ test_existing_classified_items_layer
  ✅ test_topic_extracted_items_path
  ✅ test_topic_extracted_items_layer
  ✅ test_normalized_items_path
  ✅ test_normalized_items_layer
  ✅ test_cleaned_items_path
  ✅ test_cleaned_items_layer
  ✅ test_vault_determined_items_path
  ✅ test_vault_determined_items_layer
  ✅ test_organized_items_path
  ✅ test_organized_items_layer
  ✅ test_no_json_datasets_under_model_output

Ran 25 tests in 0.017s - OK
```

**Coverage**: Not applicable (configuration changes only, no new code)

## Discovered Issues

1. **Pre-existing integration test errors**: 18 integration tests failing with "Pipeline input(s) {'parameters'} not found in the DataCatalog" - これは本フィーチャーとは無関係な既存の問題。別途対応が必要。

## Handoff to Next Phase

Items to implement in Phase 3 (US2 - 既存データの移行):

**What's Complete**:
- Catalog configuration correctly separates JSON (05_model_input) from MD (07_model_output)
- All dataset definitions follow Kedro layer conventions
- Directory structure created with .gitkeep files
- Tests validate data layer separation requirements (FR-001, FR-002, FR-003, FR-008)

**What's Needed Next**:
- Migration script to move existing JSON files from `data/07_model_output/` to `data/05_model_input/`
- Script should handle:
  - Moving JSON files only (preserve MD files in 07_model_output)
  - Idempotent operation (safe to run multiple times)
  - Dry-run mode for safety
  - Summary reporting (files moved, skipped)

**API/Interface Established**:
- Data layer separation structure is now defined in catalog.yml
- All Kedro pipelines will now read/write JSON to 05_model_input/
- MD output continues to go to 07_model_output/

**Caveats**:
- Existing data in production/local environments still in old location (07_model_output)
- Pipeline will work with new structure but existing JSON files need manual migration
- Migration script (Phase 3) is required before running pipeline on existing data
