# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - User Story 2 + 3 (例外による明確なエラーハンドリング)
- FAIL テスト数: 32 (29 ERROR + 3 FAIL)
- テストファイル: tests/utils/test_ollama_exceptions.py, tests/utils/test_ollama.py

## FAIL テスト一覧

### tests/utils/test_ollama_exceptions.py (21 tests - all ERROR)

| テストクラス | テストメソッド | 期待動作 |
|-------------|---------------|---------|
| TestOllamaErrorBase | test_ollama_error_is_exception | OllamaError は Exception のサブクラス |
| TestOllamaErrorBase | test_ollama_error_with_message | message 属性が保持される |
| TestOllamaErrorBase | test_ollama_error_with_context_len | context_len 属性が保持される |
| TestOllamaErrorBase | test_ollama_error_context_len_default_zero | context_len デフォルト値は 0 |
| TestOllamaErrorBase | test_ollama_error_str_representation | str() にメッセージが含まれる |
| TestOllamaErrorBase | test_ollama_error_can_be_raised_and_caught | raise/except が動作する |
| TestOllamaEmptyResponseError | test_is_subclass_of_ollama_error | OllamaError のサブクラス |
| TestOllamaEmptyResponseError | test_can_be_caught_as_ollama_error | OllamaError でキャッチ可能 |
| TestOllamaEmptyResponseError | test_has_message_and_context_len | message と context_len 保持 |
| TestOllamaEmptyResponseError | test_is_exception | Exception のサブクラス |
| TestOllamaTimeoutError | test_is_subclass_of_ollama_error | OllamaError のサブクラス |
| TestOllamaTimeoutError | test_can_be_caught_as_ollama_error | OllamaError でキャッチ可能 |
| TestOllamaTimeoutError | test_has_message_and_context_len | message と context_len 保持 |
| TestOllamaConnectionError | test_is_subclass_of_ollama_error | OllamaError のサブクラス |
| TestOllamaConnectionError | test_can_be_caught_as_ollama_error | OllamaError でキャッチ可能 |
| TestOllamaConnectionError | test_has_message_and_context_len | message と context_len 保持 |
| TestContextLenAttribute | test_context_len_accessible_from_empty_response_error | EmptyResponseError から context_len 取得 |
| TestContextLenAttribute | test_context_len_accessible_from_timeout_error | TimeoutError から context_len 取得 |
| TestContextLenAttribute | test_context_len_accessible_from_connection_error | ConnectionError から context_len 取得 |
| TestContextLenAttribute | test_context_len_accessible_via_base_class_catch | OllamaError でキャッチして context_len 取得 |
| TestContextLenAttribute | test_context_len_large_value | 大きな context_len 値の保持 |

### tests/utils/test_ollama.py (11 tests - 8 ERROR + 3 FAIL)

| テストクラス | テストメソッド | 期待動作 |
|-------------|---------------|---------|
| TestCallOllamaEmptyResponse | test_empty_response_raises_exception | 空レスポンスで OllamaEmptyResponseError |
| TestCallOllamaEmptyResponse | test_whitespace_only_response_raises_exception | 空白のみで OllamaEmptyResponseError |
| TestCallOllamaEmptyResponse | test_empty_response_error_has_context_len | エラーに context_len が含まれる |
| TestCallOllamaTimeout | test_timeout_raises_exception | タイムアウトで OllamaTimeoutError |
| TestCallOllamaTimeout | test_timeout_error_has_context_len | エラーに context_len が含まれる |
| TestCallOllamaConnectionError | test_connection_error_raises_exception | 接続エラーで OllamaConnectionError |
| TestCallOllamaConnectionError | test_connection_error_has_context_len | エラーに context_len が含まれる |
| TestCallOllamaSuccessReturnsStr | test_success_returns_str | 正常時に str を返す (FAIL) |
| TestCallOllamaSuccessReturnsStr | test_success_not_tuple | 戻り値が tuple ではない (FAIL) |
| TestCallOllamaSuccessReturnsStr | test_success_with_unicode_response | Unicode レスポンスが str で返る (FAIL) |

Note: TestContextLenAttribute.test_context_len_zero は OllamaError が存在しないため ERROR だが、上表の TestOllamaErrorBase と重複するためここでは省略。実際には 21 + 11 = 32 テスト。

## 実装ヒント

### 例外クラス (src/obsidian_etl/utils/ollama.py)

```python
class OllamaError(Exception):
    def __init__(self, message: str, context_len: int = 0) -> None:
        self.message = message
        self.context_len = context_len
        super().__init__(message)

class OllamaEmptyResponseError(OllamaError):
    pass

class OllamaTimeoutError(OllamaError):
    pass

class OllamaConnectionError(OllamaError):
    pass
```

### call_ollama 変更点

- 戻り値型: `tuple[str, str | None]` -> `str`
- 空レスポンス: `return content, None` -> `raise OllamaEmptyResponseError(...)`
- タイムアウト: `return "", f"Timeout..."` -> `raise OllamaTimeoutError(...)`
- 接続エラー: `return "", f"Connection error..."` -> `raise OllamaConnectionError(...)`
- 正常: `return content, None` -> `return content`

## FAIL 出力例

```
ERROR: test_ollama_error_is_exception (tests.utils.test_ollama_exceptions.TestOllamaErrorBase)
ImportError: cannot import name 'OllamaError' from 'obsidian_etl.utils.ollama'

FAIL: test_success_returns_str (tests.utils.test_ollama.TestCallOllamaSuccessReturnsStr)
AssertionError: ('Hello, world!', None) is not an instance of <class 'str'>

FAIL: test_success_not_tuple (tests.utils.test_ollama.TestCallOllamaSuccessReturnsStr)
AssertionError: ('response text', None) is an instance of <class 'tuple'>
```
