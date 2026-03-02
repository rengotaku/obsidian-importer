# Quickstart: call_ollama 例外ベースリファクタリング + 汎用ログコンテキスト

**Date**: 2026-03-01
**Feature**: 063-ollama-exception-refactor

## 概要

このガイドでは、実装完了後のログコンテキスト機能と例外ベース API の使い方を説明します。

---

## 1. ログコンテキストの使用

### パーティション処理での file_id 設定

```python
from obsidian_etl.utils.log_context import set_file_id

def process_partitions(partitions: dict) -> dict:
    results = {}
    for key, load_func in partitions.items():
        # パーティション処理開始時に file_id を設定
        file_id = key  # または metadata.get("file_id")
        set_file_id(file_id)

        data = load_func()
        # このスコープ内のすべてのログに [file_id] が自動付与
        logger.info("Processing started")  # → [abc123] Processing started

        # ... 処理 ...

        results[key] = processed_data

    return results
```

### 新規コードでのログ出力

file_id が設定されたコンテキスト内では、普通にログを書くだけで自動的にプレフィックスが付与されます。

```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    # 特別な対応は不要
    logger.warning("Something happened")
    # 出力: [abc123def456] Something happened
```

---

## 2. Ollama API の呼び出し

### 基本的な呼び出しパターン

```python
from obsidian_etl.utils.ollama import call_ollama, OllamaError

try:
    response = call_ollama(
        system_prompt="You are a helpful assistant.",
        user_message="Hello, world!",
        model="gemma3:27b",
    )
    # response は str 型
    print(response)

except OllamaError as e:
    # エラー時の処理
    logger.warning(f"LLM error: {e} (context_len={e.context_len})")
    # デフォルト値で処理継続
    return None
```

### 特定のエラー種別をキャッチ

```python
from obsidian_etl.utils.ollama import (
    call_ollama,
    OllamaEmptyResponseError,
    OllamaTimeoutError,
    OllamaConnectionError,
)

try:
    response = call_ollama(...)

except OllamaEmptyResponseError as e:
    logger.warning(f"Empty response: {e}")
    return "", "other"

except OllamaTimeoutError as e:
    logger.error(f"Timeout: {e}")
    raise  # タイムアウトは再スロー

except OllamaConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise
```

---

## 3. 典型的な使用例（organize/nodes.py）

```python
from obsidian_etl.utils.log_context import set_file_id
from obsidian_etl.utils.ollama import call_ollama, OllamaError

def extract_topic_and_genre(
    partitions: dict[str, Callable],
    params: dict,
) -> dict:
    results = {}

    for key, load_func in partitions.items():
        data = load_func()
        metadata = data.get("metadata", {})

        # file_id を設定（以降のログに自動付与）
        file_id = metadata.get("file_id") or key
        set_file_id(file_id)

        content = data.get("content", "")

        try:
            response = call_ollama(
                system_prompt=GENRE_PROMPT,
                user_message=content[:5000],
                model=params["model"],
            )
            topic, genre = parse_response(response)

        except OllamaError as e:
            # [file_id] が自動的にログに含まれる
            logger.warning(f"Failed to extract: {e}")
            topic, genre = "", "other"

        results[key] = {"topic": topic, "genre": genre}

    return results
```

---

## 4. テストでの使用

### ログコンテキストのテスト

```python
import unittest
from obsidian_etl.utils.log_context import set_file_id, get_file_id, clear_file_id

class TestLogContext(unittest.TestCase):
    def setUp(self):
        clear_file_id()

    def test_set_and_get(self):
        set_file_id("abc123")
        self.assertEqual(get_file_id(), "abc123")

    def test_default_empty(self):
        self.assertEqual(get_file_id(), "")
```

### 例外のテスト

```python
import unittest
from unittest.mock import patch
from obsidian_etl.utils.ollama import call_ollama, OllamaEmptyResponseError

class TestCallOllama(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_empty_response_raises(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            b'{"message": {"content": ""}}'
        )

        with self.assertRaises(OllamaEmptyResponseError) as ctx:
            call_ollama("prompt", "message", "model")

        self.assertGreater(ctx.exception.context_len, 0)
```

---

## 5. 設定

### logging.yml

カスタムフォーマッターは `conf/base/logging.yml` で設定済み：

```yaml
formatters:
  context_aware:
    (): obsidian_etl.utils.log_context.ContextAwareFormatter
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

handlers:
  console:
    formatter: context_aware
```

---

## 注意事項

1. **file_id の設定タイミング**: パーティション処理の **ループ内** で設定すること
2. **処理継続**: 例外をキャッチしてデフォルト値を返し、他のパーティションの処理を継続
3. **手動プレフィックス不要**: `f"[{file_id}] ..."` は書かない（フォーマッターが自動追加）
