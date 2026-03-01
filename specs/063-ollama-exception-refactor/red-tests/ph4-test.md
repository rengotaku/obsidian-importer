# Phase 4 RED Tests

## サマリー
- Phase: Phase 4 - 呼び出し元の更新
- FAIL テスト数: 28
- テストファイル: tests/utils/test_knowledge_extractor.py, tests/pipelines/organize/test_nodes.py

## FAIL テスト一覧

### tests/utils/test_knowledge_extractor.py (12 tests)

| テストクラス | テストメソッド | 期待動作 |
|-------------|---------------|---------|
| TestTranslateSummaryExceptionHandling | test_translate_summary_catches_ollama_error | OllamaError 発生時に (None, error_message) を返す |
| TestTranslateSummaryExceptionHandling | test_translate_summary_catches_empty_response_error | OllamaEmptyResponseError 発生時に (None, error_message) を返す |
| TestTranslateSummaryExceptionHandling | test_translate_summary_catches_timeout_error | OllamaTimeoutError 発生時に (None, error_message) を返す |
| TestTranslateSummaryExceptionHandling | test_translate_summary_catches_connection_error | OllamaConnectionError 発生時に (None, error_message) を返す |
| TestTranslateSummaryExceptionHandling | test_translate_summary_success_returns_translated | call_ollama が str を返し、翻訳結果を取得 |
| TestTranslateSummaryExceptionHandling | test_translate_summary_logs_on_error | OllamaError 発生時にログ出力 |
| TestExtractKnowledgeExceptionHandling | test_extract_knowledge_catches_ollama_error | OllamaError 発生時に (None, error_message) を返す |
| TestExtractKnowledgeExceptionHandling | test_extract_knowledge_catches_empty_response_error | OllamaEmptyResponseError 発生時に (None, error_message) を返す |
| TestExtractKnowledgeExceptionHandling | test_extract_knowledge_catches_timeout_error | OllamaTimeoutError 発生時に (None, error_message) を返す |
| TestExtractKnowledgeExceptionHandling | test_extract_knowledge_catches_connection_error | OllamaConnectionError 発生時に (None, error_message) を返す |
| TestExtractKnowledgeExceptionHandling | test_extract_knowledge_success_returns_data | call_ollama が str を返し、抽出結果を取得 |
| TestExtractKnowledgeExceptionHandling | test_extract_knowledge_logs_on_error | OllamaError 発生時にログ出力 |

### tests/pipelines/organize/test_nodes.py (16 tests)

| テストクラス | テストメソッド | 期待動作 |
|-------------|---------------|---------|
| TestExtractTopicAndGenreViaLlmExceptionHandling | test_catches_ollama_error_returns_default | OllamaError 発生時に ("", "other") を返す |
| TestExtractTopicAndGenreViaLlmExceptionHandling | test_catches_empty_response_error | OllamaEmptyResponseError 発生時に ("", "other") を返す |
| TestExtractTopicAndGenreViaLlmExceptionHandling | test_catches_timeout_error | OllamaTimeoutError 発生時に ("", "other") を返す |
| TestExtractTopicAndGenreViaLlmExceptionHandling | test_catches_connection_error | OllamaConnectionError 発生時に ("", "other") を返す |
| TestExtractTopicAndGenreViaLlmExceptionHandling | test_logs_warning_on_error | OllamaError 発生時にログ出力 |
| TestExtractTopicAndGenreViaLlmExceptionHandling | test_success_returns_topic_and_genre | call_ollama が str を返し、topic/genre 取得 |
| TestExtractTopicViaLlmExceptionHandling | test_catches_ollama_error_returns_none | OllamaError 発生時に None を返す |
| TestExtractTopicViaLlmExceptionHandling | test_catches_empty_response_error_returns_none | OllamaEmptyResponseError 発生時に None を返す |
| TestExtractTopicViaLlmExceptionHandling | test_catches_timeout_error_returns_none | OllamaTimeoutError 発生時に None を返す |
| TestExtractTopicViaLlmExceptionHandling | test_logs_warning_on_error | OllamaError 発生時にログ出力 |
| TestExtractTopicViaLlmExceptionHandling | test_success_returns_topic | call_ollama が str を返し、topic 取得 |
| TestSuggestNewGenresViaLlmExceptionHandling | test_catches_ollama_error_returns_empty_list | OllamaError 発生時に空リスト返却 |
| TestSuggestNewGenresViaLlmExceptionHandling | test_catches_timeout_error_returns_empty_list | OllamaTimeoutError 発生時に空リスト返却 |
| TestSuggestNewGenresViaLlmExceptionHandling | test_catches_connection_error_returns_empty_list | OllamaConnectionError 発生時に空リスト返却 |
| TestSuggestNewGenresViaLlmExceptionHandling | test_logs_warning_on_error | OllamaError 発生時にログ出力 |
| TestSuggestNewGenresViaLlmExceptionHandling | test_success_returns_suggestions | call_ollama が str を返し、提案リスト取得 |

## 実装ヒント

### knowledge_extractor.py (2箇所)

- `translate_summary` (line 81-93): `response, error = call_ollama(...)` を `try: response = call_ollama(...) except OllamaError as e: return None, str(e)` に変更
- `extract_knowledge` (line 128-140): 同上

### organize/nodes.py (3箇所)

- `_extract_topic_and_genre_via_llm` (line 270-283): `response, error = call_ollama(...)` を `try: response = call_ollama(...) except OllamaError as e: logger.warning(...); return "", "other"` に変更
- `_extract_topic_via_llm` (line 347-360): 同上、`return None`
- `_suggest_new_genres_via_llm` (line 745-758): 同上、`return []`

### インポート追加

- `knowledge_extractor.py`: `from obsidian_etl.utils.ollama import OllamaError` を追加
- `organize/nodes.py`: `from obsidian_etl.utils.ollama import OllamaError` を追加（call_ollama の import に追加）

## FAIL 出力例

### 例外テスト (OllamaError がキャッチされない)
```
ERROR: test_translate_summary_catches_ollama_error (tests.utils.test_knowledge_extractor.TestTranslateSummaryExceptionHandling)
  File "src/obsidian_etl/utils/knowledge_extractor.py", line 81, in translate_summary
    response, error = call_ollama(...)
  raise effect
obsidian_etl.utils.ollama.OllamaError: Test error
```

### 成功テスト (str を tuple として展開できない)
```
ERROR: test_translate_summary_success_returns_translated (tests.utils.test_knowledge_extractor.TestTranslateSummaryExceptionHandling)
  File "src/obsidian_etl/utils/knowledge_extractor.py", line 81, in translate_summary
    response, error = call_ollama(...)
ValueError: too many values to unpack (expected 2)
```
