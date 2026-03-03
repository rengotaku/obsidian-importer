# Phase 4 RED Tests

## Summary
- Phase: Phase 4 - User Story 3: Log Processing Simplification
- FAIL test count: 3
- PASS test count (new): 7
- Test file: tests/utils/test_log_context.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/utils/test_log_context.py | test_dict_input_raises_type_error | dict input should raise TypeError |
| tests/utils/test_log_context.py | test_dict_input_without_metadata_raises_type_error | dict without metadata should raise TypeError |
| tests/utils/test_log_context.py | test_list_of_tuples_with_dict_raises_type_error | list[tuple] with dict content should raise TypeError |

## PASS Test List (new str-only tests)

| Test File | Test Method | Verified Behavior |
|-----------|-------------|-------------------|
| tests/utils/test_log_context.py | test_str_input_with_frontmatter_extracts_file_id | str with frontmatter extracts file_id correctly |
| tests/utils/test_log_context.py | test_str_input_without_frontmatter_falls_back_to_key | str without frontmatter falls back to partition key |
| tests/utils/test_log_context.py | test_str_input_with_empty_frontmatter_falls_back_to_key | str with frontmatter but no file_id falls back to key |
| tests/utils/test_log_context.py | test_multiple_str_items_all_processed | Multiple str items all processed correctly |
| tests/utils/test_log_context.py | test_file_id_context_active_during_yield | file_id context is active during yield, cleared after |
| tests/utils/test_log_context.py | test_list_of_tuples_input_with_str_content | list[tuple] format with str content works correctly |
| tests/utils/test_log_context.py | test_dict_input_raises_type_error (will PASS after GREEN) | dict input raises TypeError with "str" in message |

## Implementation Hints
- `src/obsidian_etl/utils/log_context.py` line 165: Remove `if isinstance(item, dict):` branch
- Add `if isinstance(item, dict): raise TypeError(...)` before str processing
- Keep `elif isinstance(item, str):` branch for frontmatter extraction
- Update docstring to reflect str-only support

## FAIL Output
```
FAIL: test_dict_input_raises_type_error (tests.utils.test_log_context.TestIterWithFileIdStrOnly.test_dict_input_raises_type_error)
dict input should raise TypeError.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/utils/test_log_context.py", line 608, in test_dict_input_raises_type_error
    with self.assertRaises(TypeError) as ctx:
AssertionError: TypeError not raised

FAIL: test_dict_input_without_metadata_raises_type_error (tests.utils.test_log_context.TestIterWithFileIdStrOnly.test_dict_input_without_metadata_raises_type_error)
metadata-less dict input should also raise TypeError.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/utils/test_log_context.py", line 624, in test_dict_input_without_metadata_raises_type_error
    with self.assertRaises(TypeError) as ctx:
AssertionError: TypeError not raised

FAIL: test_list_of_tuples_with_dict_raises_type_error (tests.utils.test_log_context.TestIterWithFileIdStrOnly.test_list_of_tuples_with_dict_raises_type_error)
list[tuple] format with dict content should raise TypeError.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/utils/test_log_context.py", line 700, in test_list_of_tuples_with_dict_raises_type_error
    with self.assertRaises(TypeError):
AssertionError: TypeError not raised
```
