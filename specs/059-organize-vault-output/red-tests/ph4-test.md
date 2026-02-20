# Phase 4 RED Tests

## Summary
- Phase: Phase 4 - US4 Overwrite (conflict handling overwrite mode)
- FAIL test count: 2
- Test file: tests/unit/pipelines/vault_output/test_nodes.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| test_nodes.py | test_copy_to_vault_overwrite_existing | overwrite mode replaces existing file and returns status "overwritten" |
| test_nodes.py | test_handle_conflict_overwrite_mode | log_copy_summary includes "overwritten" count in result dict |

## Implementation Hints
- In `copy_to_vault()` in `src/obsidian_etl/pipelines/vault_output/nodes.py`:
  - Add `elif conflict_handling == "overwrite"` branch when file exists
  - Write file content (overwrite) and return status `"overwritten"` instead of `"copied"`
- In `log_copy_summary()` in `src/obsidian_etl/pipelines/vault_output/nodes.py`:
  - Add `overwritten` count: `sum(1 for r in copy_results if r["status"] == "overwritten")`
  - Include `"overwritten"` key in returned dict

## FAIL Output
```
FAIL: test_copy_to_vault_overwrite_existing (tests.unit.pipelines.vault_output.test_nodes.TestCopyToVault)
overwrite mode: existing file should be replaced with new content (US4).
----------------------------------------------------------------------
AssertionError: 'copied' != 'overwritten'

FAIL: test_handle_conflict_overwrite_mode (tests.unit.pipelines.vault_output.test_nodes.TestCopyToVault)
overwrite mode: copy summary should include overwritten count (US4).
----------------------------------------------------------------------
AssertionError: 'overwritten' not found in {'total': 3, 'copied': 1, 'skipped': 1, 'errors': 0}
```
