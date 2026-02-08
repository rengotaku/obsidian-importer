# Phase 5 RED Tests

## Summary
- Phase: Phase 5 - US1 E2E Integration, Hook, Pipeline Registry
- Total new tests: 20 (7 PASS from existing impl, 2 FAIL, 9 ERROR)
- FAIL/ERROR test count: 11
- Test files: tests/test_hooks.py, tests/test_pipeline_registry.py, tests/test_integration.py

## Note on Hook Tests (PASS)

Hook tests (7 tests in tests/test_hooks.py) PASS because `ErrorHandlerHook` and `LoggingHook` were already implemented in Phase 1. This is expected and correct behavior - the tests validate the existing implementation.

## FAIL/ERROR Test List

| Test File | Test Method | Expected Behavior | Status |
|-----------|-------------|-------------------|--------|
| tests/test_pipeline_registry.py | test_register_pipelines_has_import_claude | import_claude pipeline registered | FAIL (KeyError) |
| tests/test_pipeline_registry.py | test_default_pipeline_is_not_empty | __default__ pipeline not empty | FAIL (0 nodes) |
| tests/test_pipeline_registry.py | test_import_claude_pipeline_has_nodes | import_claude has >0 nodes | ERROR (KeyError) |
| tests/test_pipeline_registry.py | test_import_claude_contains_extract_node | parse_claude_json node present | ERROR (KeyError) |
| tests/test_pipeline_registry.py | test_import_claude_contains_transform_nodes | transform nodes present | ERROR (KeyError) |
| tests/test_pipeline_registry.py | test_import_claude_contains_organize_nodes | organize nodes present | ERROR (KeyError) |
| tests/test_integration.py | test_e2e_claude_import_produces_organized_items | raw_claude -> organized_items | ERROR (KeyError) |
| tests/test_integration.py | test_e2e_claude_import_all_conversations_processed | 2 conversations -> 2 items | ERROR (KeyError) |
| tests/test_integration.py | test_e2e_claude_import_intermediate_datasets | parsed_items, markdown_notes produced | ERROR (KeyError) |
| tests/test_integration.py | test_e2e_organized_item_has_required_fields | genre, vault_path, final_path present | ERROR (KeyError) |
| tests/test_integration.py | test_e2e_ollama_mock_called | Ollama called for each item | ERROR (KeyError) |

## PASS Test List (Hook tests - already implemented)

| Test File | Test Method | Expected Behavior | Status |
|-----------|-------------|-------------------|--------|
| tests/test_hooks.py | test_on_node_error_logs_error | Error logged with node name | PASS |
| tests/test_hooks.py | test_on_node_error_does_not_raise | No exception re-raised | PASS |
| tests/test_hooks.py | test_on_node_error_logs_error_type | Error type in log | PASS |
| tests/test_hooks.py | test_before_node_run_records_start_time | Start time recorded | PASS |
| tests/test_hooks.py | test_after_node_run_logs_elapsed_time | Elapsed time logged | PASS |
| tests/test_hooks.py | test_after_node_run_clears_start_time | Start time cleared | PASS |
| tests/test_hooks.py | test_logging_hook_multiple_nodes | Independent tracking | PASS |

## Implementation Hints

- `src/obsidian_etl/pipeline_registry.py`: Register `import_claude` by combining:
  - `extract_claude.pipeline.create_pipeline()` (parse_claude_json node)
  - `transform.pipeline.create_pipeline()` (extract_knowledge, generate_metadata, format_markdown nodes)
  - `organize.pipeline.create_pipeline()` (classify_genre, normalize_frontmatter, clean_content, determine_vault_path, move_to_vault nodes)
- Set `__default__` to same as `import_claude` (or sum of all registered pipelines)
- E2E tests use `SequentialRunner` + `MemoryDataset` with mocked Ollama via `@patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")`

## FAIL Output Example
```
FAIL: test_register_pipelines_has_import_claude (tests.test_pipeline_registry.TestPipelineRegistry)
AssertionError: 'import_claude' not found in {'__default__': Pipeline([])}

ERROR: test_e2e_claude_import_produces_organized_items (tests.test_integration.TestE2EClaudeImport)
KeyError: 'import_claude'

FAIL: test_default_pipeline_is_not_empty (tests.test_pipeline_registry.TestPipelineRegistry)
AssertionError: 0 not greater than 0 : __default__ pipeline should not be empty
```
