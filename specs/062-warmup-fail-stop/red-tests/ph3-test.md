# Phase 3 RED Tests

## Summary
- Phase: Phase 3 - User Story 2: Clear Error Message Display
- FAIL test count: 4
- PASS test count: 4 (existing behavior already satisfies these)
- Test file: tests/test_hooks_warmup.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/test_hooks_warmup.py | test_on_node_error_catches_warmup_error | ErrorHandlerHook が OllamaWarmupError を検出して sys.exit を呼ぶ |
| tests/test_hooks_warmup.py | test_exit_code_3_on_warmup_error | OllamaWarmupError 時に sys.exit(3) が呼ばれる |
| tests/test_hooks_warmup.py | test_error_message_includes_ollama_serve | エラーメッセージに "ollama serve" が含まれる |
| tests/test_hooks_warmup.py | test_error_message_includes_ollama_pull | エラーメッセージに "ollama pull" が含まれる |

## PASS Test List (already satisfied by existing behavior)

| Test File | Test Method | Reason |
|-----------|-------------|--------|
| tests/test_hooks_warmup.py | test_non_warmup_error_does_not_exit | Existing on_node_error does not call sys.exit |
| tests/test_hooks_warmup.py | test_error_message_includes_model_name_timeout | Model name included in str(OllamaWarmupError) |
| tests/test_hooks_warmup.py | test_error_message_includes_model_name_connection_error | Model name included in str(OllamaWarmupError) |
| tests/test_hooks_warmup.py | test_error_message_includes_failure_reason | Reason included in str(OllamaWarmupError) |

## Implementation Hints
- `src/obsidian_etl/hooks.py` の `ErrorHandlerHook.on_node_error` を修正
- `from obsidian_etl.utils.ollama import OllamaWarmupError` を追加
- `isinstance(error, OllamaWarmupError)` で判定
- 専用エラーメッセージ（モデル名 + 推奨アクション）をログ出力
- `sys.exit(3)` を呼び出し
- 推奨アクション: `ollama serve`, `ollama pull <model>`

## FAIL Output Examples
```
FAIL: test_on_node_error_catches_warmup_error (tests.test_hooks_warmup.TestErrorHandlerHookCatchesWarmupError)
AssertionError: Expected 'exit' to have been called once. Called 0 times.

FAIL: test_exit_code_3_on_warmup_error (tests.test_hooks_warmup.TestErrorHandlerHookExitCode)
AssertionError: Expected 'exit' to be called once. Called 0 times.

FAIL: test_error_message_includes_ollama_serve (tests.test_hooks_warmup.TestErrorMessageContainsRecommendedActions)
AssertionError: 'ollama serve' not found in "ERROR:obsidian_etl.hooks:Node 'extract_knowledge' failed: Model warmup failed: gemma3:12b: Connection refused"

FAIL: test_error_message_includes_ollama_pull (tests.test_hooks_warmup.TestErrorMessageContainsRecommendedActions)
AssertionError: 'ollama pull' not found in "ERROR:obsidian_etl.hooks:Node 'extract_knowledge' failed: Model warmup failed: gemma3:12b: Connection timed out"
```
