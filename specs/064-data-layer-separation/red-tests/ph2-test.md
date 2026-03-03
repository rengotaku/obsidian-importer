# Phase 2 RED Tests

## Summary
- Phase: Phase 2 - User Story 1: Pipeline Data Integrity (catalog.yml paths)
- FAIL test count: 15
- Test files: tests/unit/test_catalog_paths.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/unit/test_catalog_paths.py | test_classified_items_path | classified_items path = data/05_model_input/classified |
| tests/unit/test_catalog_paths.py | test_classified_items_layer | classified_items layer = model_input |
| tests/unit/test_catalog_paths.py | test_existing_classified_items_path | existing_classified_items path = data/05_model_input/classified |
| tests/unit/test_catalog_paths.py | test_existing_classified_items_layer | existing_classified_items layer = model_input |
| tests/unit/test_catalog_paths.py | test_topic_extracted_items_path | topic_extracted_items path = data/05_model_input/topic_extracted |
| tests/unit/test_catalog_paths.py | test_topic_extracted_items_layer | topic_extracted_items layer = model_input |
| tests/unit/test_catalog_paths.py | test_normalized_items_path | normalized_items path = data/05_model_input/normalized |
| tests/unit/test_catalog_paths.py | test_normalized_items_layer | normalized_items layer = model_input |
| tests/unit/test_catalog_paths.py | test_cleaned_items_path | cleaned_items path = data/05_model_input/cleaned |
| tests/unit/test_catalog_paths.py | test_cleaned_items_layer | cleaned_items layer = model_input |
| tests/unit/test_catalog_paths.py | test_vault_determined_items_path | vault_determined_items path = data/05_model_input/vault_determined |
| tests/unit/test_catalog_paths.py | test_vault_determined_items_layer | vault_determined_items layer = model_input |
| tests/unit/test_catalog_paths.py | test_organized_items_path | organized_items path = data/05_model_input/organized |
| tests/unit/test_catalog_paths.py | test_organized_items_layer | organized_items layer = model_input |
| tests/unit/test_catalog_paths.py | test_no_json_datasets_under_model_output | No json.JSONDataset under 07_model_output/ |

## PASS Tests (already correct)

| Test File | Test Method | Reason |
|-----------|-------------|--------|
| tests/unit/test_catalog_paths.py | test_markdown_notes_path | Already at 07_model_output/notes |
| tests/unit/test_catalog_paths.py | test_markdown_notes_layer | Already model_output |
| tests/unit/test_catalog_paths.py | test_review_notes_path | Already at 07_model_output/review |
| tests/unit/test_catalog_paths.py | test_review_notes_layer | Already model_output |
| tests/unit/test_catalog_paths.py | test_organized_notes_path | Already at 07_model_output/organized |
| tests/unit/test_catalog_paths.py | test_organized_notes_layer | Already model_output |
| tests/unit/test_catalog_paths.py | test_organized_files_path | Already at 07_model_output/organized |
| tests/unit/test_catalog_paths.py | test_organized_files_layer | Already model_output |
| tests/unit/test_catalog_paths.py | test_json_datasets_use_json_type | Dataset types already correct |
| tests/unit/test_catalog_paths.py | test_md_datasets_use_text_type | Dataset types already correct |

## Implementation Hints
- `conf/base/catalog.yml` の 7 JSON datasets の `path` を `data/07_model_output/` -> `data/05_model_input/` に変更
- 各 JSON dataset の `metadata.kedro-viz.layer` を `model_output` -> `model_input` に変更
- MD datasets (markdown_notes, review_notes, organized_notes, organized_files) は変更不要

## FAIL Output Example
```
FAIL: test_classified_items_path (tests.unit.test_catalog_paths.TestJsonDatasetPaths.test_classified_items_path)
classified_items が data/05_model_input/classified に配置されること。
----------------------------------------------------------------------
AssertionError: 'data/07_model_output/classified' != 'data/05_model_input/classified'
: classified_items: expected path 'data/05_model_input/classified', got 'data/07_model_output/classified'

FAIL: test_no_json_datasets_under_model_output (tests.unit.test_catalog_paths.TestCatalogDatasetTypes.test_no_json_datasets_under_model_output)
07_model_output 配下に JSON データセットが存在しないこと (FR-001)。
----------------------------------------------------------------------
AssertionError: 'json.JSONDataset' == 'json.JSONDataset'
: classified_items: JSON dataset found under 07_model_output/ (path=data/07_model_output/classified). Should be under 05_model_input/.
```
