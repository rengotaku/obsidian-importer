# Phase 1 Output: Setup

**Date**: 2026-03-01
**Status**: Completed

## Executed Tasks

- [x] T001 現在の call_ollama 実装を確認: src/obsidian_etl/utils/ollama.py
- [x] T002 [P] 呼び出し元を確認: src/obsidian_etl/utils/knowledge_extractor.py (2箇所)
- [x] T003 [P] 呼び出し元を確認: src/obsidian_etl/pipelines/organize/nodes.py (3箇所 + 手動プレフィックス)
- [x] T004 [P] パーティション処理を確認: src/obsidian_etl/pipelines/transform/nodes.py
- [x] T005 [P] パーティション処理を確認: src/obsidian_etl/pipelines/extract_claude/nodes.py
- [x] T006 [P] パーティション処理を確認: src/obsidian_etl/pipelines/extract_openai/nodes.py
- [x] T007 [P] 既存の Ollama テストを確認: tests/utils/test_ollama*.py
- [x] T008 [P] 既存の logging 設定を確認: conf/base/logging.yml

## Existing Code Analysis

### src/obsidian_etl/utils/ollama.py (lines 74-148)

**Structure**:
- `call_ollama`: Ollama API を呼び出す関数
- `_do_warmup`: モデルウォームアップヘルパー
- `_warmed_models`: ウォームアップ済みモデルの Set

**Current Signature**:
```python
def call_ollama(...) -> tuple[str, str | None]:
    """Returns: (content, None) on success, ("", error_message) on failure."""
```

**Error Handling (current)**:
- `urllib.error.URLError` → `("", f"Connection error: {e.reason}")`
- `TimeoutError` → `("", f"Timeout ({timeout}s)")`
- `json.JSONDecodeError` → `("", f"JSON parse error: {e}")`
- `Exception` → `("", f"API error: {e}")`
- Empty response → returns `(content, None)` with warning log

**Required Updates**:
1. 戻り値型: `tuple[str, str | None]` → `str`
2. エラー処理: タプル返却 → 例外スロー
3. 例外クラス追加: `OllamaError`, `OllamaEmptyResponseError`, `OllamaTimeoutError`, `OllamaConnectionError`
4. 空レスポンス: warning log → `OllamaEmptyResponseError` をスロー

### src/obsidian_etl/utils/knowledge_extractor.py

**call_ollama 呼び出し箇所**:

1. `translate_summary` (lines 80-88):
```python
response, error = call_ollama(...)
if error:
    return None, error
```

2. `extract_knowledge` (lines 127-135):
```python
response, error = call_ollama(...)
if error:
    return None, error
```

**Required Updates**:
- タプル展開 → try/except に変更
- `OllamaError` キャッチで `(None, str(e))` を返却

### src/obsidian_etl/pipelines/organize/nodes.py

**call_ollama 呼び出し箇所 (3箇所)**:

1. `_extract_topic_and_genre_via_llm` (lines 269-280):
```python
response, error = call_ollama(...)
if error:
    logger.warning(f"[{file_id}] Failed to extract topic and genre via LLM: {error}")
    return "", "other"
```

2. `_extract_topic_via_llm` (lines 350-356):
```python
response, error = call_ollama(...)
if error:
    logger.warning(f"Failed to extract topic via LLM: {error}")
    return None
```

3. `_suggest_new_genres_via_llm` (lines 745-751):
```python
response, error = call_ollama(...)
if error:
    logger.warning(f"Failed to suggest genres via LLM: {error}")
    return []
```

**手動プレフィックス (削除対象)**:
- Line 281: `f"[{file_id}] Failed to extract topic and genre via LLM: {error}"`
- Line 295: `f"[{file_id}] Invalid genre '{genre}', defaulting to 'other'"`
- Line 302: `f"[{file_id}] Failed to parse LLM response as JSON: {e}, response={response_preview}"`

**Required Updates**:
- タプル展開 → try/except `OllamaError` に変更
- 手動 `[{file_id}]` プレフィックス削除（フォーマッターで自動追加）

### src/obsidian_etl/pipelines/transform/nodes.py

**パーティション処理パターン** (lines 120-128):
```python
for partition_id, load_func in to_process:
    item = load_func()
    # ... processing ...
    logger.info(f"[{processed}/{remaining}] Processing: {partition_id}")
```

**Required Updates**:
- ループ内で `set_file_id(partition_id)` を追加

### src/obsidian_etl/pipelines/extract_claude/nodes.py

**パーティション処理パターン** (lines 53-148):
```python
for conv in conversations:
    # ... processing conv_uuid ...
```

**Note**: 会話リストをループ、partition_id は `conv_uuid` または `file_id`

**Required Updates**:
- ループ内で `set_file_id(file_id)` を追加（file_id 生成後）

### src/obsidian_etl/pipelines/extract_openai/nodes.py

**パーティション処理パターン** (lines 55-165):
```python
for zip_name, load_func in partitioned_input.items():
    # ... inner loop ...
    for conv in conversations_data:
        # ... processing ...
```

**Required Updates**:
- 内側ループで `set_file_id(file_id)` を追加（file_id 生成後）

### conf/base/logging.yml

**Current Structure**:
```yaml
formatters:
  simple:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

handlers:
  console:
    formatter: simple
  info_file:
    formatter: simple
```

**Required Updates**:
1. `context_aware` フォーマッター追加（`()`記法でカスタムクラス指定）
2. handlers の formatter を `simple` → `context_aware` に変更

## Existing Test Analysis

- `tests/utils/test_ollama_warmup.py`: ウォームアップ機能のテスト
- `tests/utils/test_ollama_config.py`: OllamaConfig と get_ollama_config のテスト
- **存在しない**: call_ollama の例外ハンドリングテスト → Phase 3 で作成

**Required New Test Files**:
- `tests/utils/test_log_context.py`: ログコンテキスト機能 (Phase 2)
- `tests/utils/test_ollama_exceptions.py`: 例外クラスのテスト (Phase 3)

## Newly Created Files

### src/obsidian_etl/utils/log_context.py (Phase 2 で実装)

- `_file_id_var`: ContextVar for file_id
- `set_file_id(file_id: str)`: コンテキストに file_id を設定
- `get_file_id() -> str`: コンテキストから file_id を取得
- `clear_file_id()`: file_id をクリア
- `ContextAwareFormatter`: file_id をログにプレフィックスとして追加

## Technical Decisions

1. **contextvars 使用**: スレッドセーフ、標準ライブラリ、追加依存なし
2. **カスタム Formatter**: 既存コード変更不要、条件付きプレフィックス追加
3. **例外階層**: OllamaError 基底クラス + 具体的なエラー種別の派生クラス
4. **set_file_id 位置**: パーティションループ内、処理開始時に設定

## Handoff to Next Phase

### Phase 2 (US1 - エラー発生時のファイル特定):

**実装対象**:
- `src/obsidian_etl/utils/log_context.py` (新規作成)
- `conf/base/logging.yml` (フォーマッター追加)

**テスト対象**:
- `tests/utils/test_log_context.py` (新規作成)

**Caveats**:
- ContextAwareFormatter は `()` 記法で logging.yml に設定
- file_id が空の場合はプレフィックスなし

### Phase 3 (US2+US3 - 例外による明確なエラーハンドリング):

**実装対象**:
- `src/obsidian_etl/utils/ollama.py` (例外クラス追加、call_ollama 変更)

**テスト対象**:
- `tests/utils/test_ollama_exceptions.py` (新規作成)
- `tests/utils/test_ollama.py` に例外スローテスト追加

**Caveats**:
- 既存の warmup テストは影響なし
- call_ollama の戻り値型変更により、すべての呼び出し元の更新が必要

### Phase 4 (呼び出し元更新):

**実装対象**:
- `src/obsidian_etl/utils/knowledge_extractor.py` (2箇所)
- `src/obsidian_etl/pipelines/organize/nodes.py` (3箇所)

### Phase 5 (file_id 設定):

**実装対象**:
- `src/obsidian_etl/pipelines/transform/nodes.py`
- `src/obsidian_etl/pipelines/organize/nodes.py`
- `src/obsidian_etl/pipelines/extract_claude/nodes.py`
- `src/obsidian_etl/pipelines/extract_openai/nodes.py`

### Phase 6 (Polish):

**実装対象**:
- organize/nodes.py の手動 `[{file_id}]` プレフィックス削除 (3箇所)
- 不要なインポート・変数の削除
