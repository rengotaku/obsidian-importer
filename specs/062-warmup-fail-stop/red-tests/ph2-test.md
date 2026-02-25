# Phase 2 RED Tests

## Summary
- Phase: Phase 2 - User Story 1: Warmup failure immediate stop
- FAIL test count: 9
- Test file: tests/test_warmup_error.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/test_warmup_error.py | test_exception_class_exists | OllamaWarmupError class can be imported from obsidian_etl.utils.ollama |
| tests/test_warmup_error.py | test_exception_has_model_attribute | OllamaWarmupError has model attribute |
| tests/test_warmup_error.py | test_exception_has_reason_attribute | OllamaWarmupError has reason attribute |
| tests/test_warmup_error.py | test_exception_str_contains_model_and_reason | str(OllamaWarmupError) contains model name and reason |
| tests/test_warmup_error.py | test_do_warmup_raises_on_timeout | _do_warmup raises OllamaWarmupError on TimeoutError |
| tests/test_warmup_error.py | test_do_warmup_raises_on_connection_refused | _do_warmup raises OllamaWarmupError on URLError |
| tests/test_warmup_error.py | test_do_warmup_raises_on_generic_exception | _do_warmup raises OllamaWarmupError on OSError |
| tests/test_warmup_error.py | test_call_ollama_propagates_warmup_error | call_ollama does not catch OllamaWarmupError |
| tests/test_warmup_error.py | test_warmed_models_not_updated_on_failure | _warmed_models not updated when warmup fails |

## Implementation Hints
- Add `OllamaWarmupError(Exception)` class to `src/obsidian_etl/utils/ollama.py` with `model` and `reason` kwargs
- Modify `_do_warmup` to raise `OllamaWarmupError` instead of `logger.warning` in the except block
- Move `_warmed_models.add(model)` in `call_ollama` to after successful `_do_warmup` return (not before)

## FAIL Output
```
ERROR: test_exception_class_exists (tests.test_warmup_error.TestOllamaWarmupError.test_exception_class_exists)
ImportError: cannot import name 'OllamaWarmupError' from 'obsidian_etl.utils.ollama'

ERROR: test_do_warmup_raises_on_timeout (tests.test_warmup_error.TestDoWarmupRaisesOnTimeout.test_do_warmup_raises_on_timeout)
ImportError: cannot import name 'OllamaWarmupError' from 'obsidian_etl.utils.ollama'

ERROR: test_call_ollama_propagates_warmup_error (tests.test_warmup_error.TestCallOllamaPropagatesWarmupError.test_call_ollama_propagates_warmup_error)
ImportError: cannot import name 'OllamaWarmupError' from 'obsidian_etl.utils.ollama'
```

## Existing Test Impact
- `tests/utils/test_ollama_warmup.py::test_warmup_handles_failure_gracefully` will need to be deleted or modified during GREEN phase, as it asserts the old behavior (no exception on failure)
