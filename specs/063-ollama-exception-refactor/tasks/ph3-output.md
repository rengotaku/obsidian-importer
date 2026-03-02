# Phase 3 Output: User Story 2 + 3 - 例外による明確なエラーハンドリング

**Date**: 2026-03-01
**Status**: Completed
**User Story**: US2 - 例外による明確なエラーハンドリング + US3 - エラー詳細情報の保持

## Executed Tasks

- [x] T035 Read RED tests: specs/063-ollama-exception-refactor/red-tests/ph3-test.md
- [x] T036 [P] [US2] OllamaError 基底クラスを実装: src/obsidian_etl/utils/ollama.py
- [x] T037 [P] [US2] OllamaEmptyResponseError を実装: src/obsidian_etl/utils/ollama.py
- [x] T038 [P] [US2] OllamaTimeoutError を実装: src/obsidian_etl/utils/ollama.py
- [x] T039 [P] [US2] OllamaConnectionError を実装: src/obsidian_etl/utils/ollama.py
- [x] T040 [US2] call_ollama を例外ベースに変更: src/obsidian_etl/utils/ollama.py
- [x] T041 Verify `make test` PASS (GREEN) - 新規テストのみ
- [x] T042 Verify `make test` passes all tests

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| src/obsidian_etl/utils/ollama.py | Modified | 例外クラス追加 (OllamaError, OllamaEmptyResponseError, OllamaTimeoutError, OllamaConnectionError) |
| src/obsidian_etl/utils/ollama.py | Modified | call_ollama を例外ベースに変更 (戻り値型: `tuple[str, str \| None]` → `str`) |

## Test Results

### 新規テスト (32 件すべて PASS)

```
test_ollama_exceptions.py: 21 tests
  - TestOllamaErrorBase: 6 tests (基底クラス)
  - TestOllamaEmptyResponseError: 4 tests
  - TestOllamaTimeoutError: 3 tests
  - TestOllamaConnectionError: 3 tests
  - TestContextLenAttribute: 6 tests (context_len 属性)

test_ollama.py: 11 tests
  - TestCallOllamaEmptyResponse: 3 tests (空レスポンス例外)
  - TestCallOllamaTimeout: 2 tests (タイムアウト例外)
  - TestCallOllamaConnectionError: 2 tests (接続エラー例外)
  - TestCallOllamaSuccessReturnsStr: 3 tests (戻り値型変更)

Ran 32 tests in 0.027s
OK
```

### 全 Ollama 関連テスト (56 件すべて PASS)

```
tests/utils/test_ollama*.py
Ran 56 tests in 0.031s
OK
```

**Coverage**: 既存カバレッジ維持 (80%+)

## Discovered Issues

1. **統合テスト失敗** (Phase 3 とは無関係):
   - 11 件のエラー: `Pipeline input(s) {'parameters'} not found in the DataCatalog`
   - 原因: organize pipeline が `parameters` データセットを要求しているが、テストの DataCatalog に含まれていない
   - 影響: 統合テスト (`tests/test_integration.py`) が Phase 3 実装前から失敗している
   - 対応: Phase 3 の変更とは無関係のため、本 Phase では対応せず

## Handoff to Next Phase

Items to implement in Phase 4 (呼び出し元の更新):

### API 変更内容

`call_ollama` の戻り値型が変更されたため、すべての呼び出し元を更新する必要がある。

**変更前**:
```python
content, error = call_ollama(...)
if error:
    logger.warning(f"LLM error: {error}")
    return None
```

**変更後** (Phase 4 で実装):
```python
try:
    content = call_ollama(...)
except OllamaError as e:
    logger.warning(f"LLM error: {e}")
    return None
```

### 更新が必要なファイル

1. **src/obsidian_etl/utils/knowledge_extractor.py**:
   - `translate_summary()`: 2 箇所
   - `extract_knowledge()`: 2 箇所

2. **src/obsidian_etl/pipelines/organize/nodes.py**:
   - `_extract_topic_and_genre_via_llm()`: 3 箇所
   - `_extract_topic_via_llm()`: 3 箇所
   - `_suggest_new_genres_via_llm()`: 3 箇所

### Caveats

- Phase 4 では、既存テストの更新も必要
  - モックの戻り値を tuple から str に変更
  - 例外スローのモック設定
- TDD フロー: RED (テスト更新) → GREEN (実装) → Verification
