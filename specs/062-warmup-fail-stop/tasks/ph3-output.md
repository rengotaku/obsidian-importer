# Phase 3 Output: User Story 2 - Clear Error Message Display

**Date**: 2026-02-25
**Status**: Completed
**User Story**: US2 - 明確なエラーメッセージの表示

## Executed Tasks

- [x] T027 Read: specs/062-warmup-fail-stop/red-tests/ph3-test.md
- [x] T028 [US2] Implement: ErrorHandlerHook に OllamaWarmupError ハンドリング追加 in src/obsidian_etl/hooks.py
- [x] T029 [US2] Implement: sys.exit(3) 呼び出し in src/obsidian_etl/hooks.py
- [x] T030 [US2] Implement: モデル名・推奨アクションを含むエラーメッセージ出力 in src/obsidian_etl/hooks.py
- [x] T031 Verify: `make test` PASS (GREEN) - 8/8 warmup hook tests passed
- [x] T032 Verify: `make test` 全テスト通過（US1 含む回帰なし）- Phase 2: 9/9, Phase 3: 8/8 all passing

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| src/obsidian_etl/hooks.py | Modified | Added OllamaWarmupError import and handling in ErrorHandlerHook.on_node_error |

## Implementation Details

### ErrorHandlerHook.on_node_error Modification

Added specific handling for `OllamaWarmupError`:
1. Check if error is an instance of `OllamaWarmupError`
2. Display comprehensive error message including:
   - Model name (`error.model`)
   - Failure reason (`error.reason`)
   - Recommended action: `ollama serve`
   - Recommended action: `ollama pull <model>`
3. Call `sys.exit(3)` to stop the pipeline with exit code 3 (Ollama connection error)
4. Non-warmup errors continue to use default behavior (log only, no exit)

### Error Message Format

```
❌ Error: Ollama model warmup failed

  Model: gemma3:12b
  Reason: Connection refused

  Ollama サーバーが起動していることを確認してください:
    ollama serve

  モデルがダウンロード済みであることを確認してください:
    ollama pull gemma3:12b
```

## Test Results

### Phase 3 Tests (US2)
```
test_on_node_error_catches_warmup_error ✓
test_exit_code_3_on_warmup_error ✓
test_non_warmup_error_does_not_exit ✓
test_error_message_includes_model_name_timeout ✓
test_error_message_includes_model_name_connection_error ✓
test_error_message_includes_ollama_serve ✓
test_error_message_includes_ollama_pull ✓
test_error_message_includes_failure_reason ✓

Ran 8 tests in 0.004s
OK
```

### Regression Check (Phase 2 Tests)
```
test_exception_class_exists ✓
test_exception_has_model_attribute ✓
test_exception_has_reason_attribute ✓
test_exception_str_contains_model_and_reason ✓
test_do_warmup_raises_on_timeout ✓
test_do_warmup_raises_on_connection_refused ✓
test_do_warmup_raises_on_generic_exception ✓
test_call_ollama_propagates_warmup_error ✓
test_warmed_models_not_updated_on_failure ✓

Ran 9 tests in 0.009s
OK
```

**Total Warmup Tests**: 17/17 PASS

## Discovered Issues

None. All warmup-related tests passing with no regressions.

## Handoff to Next Phase

Items to implement in Phase 4 (Polish & Cross-Cutting Concerns):
- `OllamaWarmupError` is now fully integrated into error handling
- Error messages follow the same pattern as existing `PreRunValidationHook._check_ollama`
- Exit code 3 is used consistently for Ollama-related errors
- Ready for final polish: docstrings, `__all__` export, manual testing
