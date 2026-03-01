# Research: call_ollama 例外ベースリファクタリング + 汎用ログコンテキスト

**Date**: 2026-03-01
**Feature**: 063-ollama-exception-refactor

## 1. contextvars によるログコンテキスト管理

### Decision

Python 標準ライブラリの `contextvars` モジュールを使用して、スレッド/コルーチンセーフなログコンテキストを実装する。

### Rationale

- **標準ライブラリ**: 追加依存なし、Python 3.7+ で利用可能
- **スレッドセーフ**: 並行処理でもコンテキストが混在しない
- **シンプル**: グローバル変数よりも明示的で安全

### Implementation Pattern

```python
from contextvars import ContextVar

# コンテキスト変数の定義
_file_id_var: ContextVar[str] = ContextVar("file_id", default="")

def set_file_id(file_id: str) -> None:
    """パーティション処理開始時に呼び出す"""
    _file_id_var.set(file_id)

def get_file_id() -> str:
    """フォーマッターから呼び出す"""
    return _file_id_var.get()

def clear_file_id() -> None:
    """パーティション処理終了時に呼び出す（オプション）"""
    _file_id_var.set("")
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| threading.local | コルーチンでコンテキストが共有される問題 |
| LoggerAdapter | 各ロガー取得時にラップが必要、侵襲的 |
| logging.Filter | フォーマッターで十分、Filter は不要な複雑さ |

---

## 2. カスタムログフォーマッター

### Decision

`logging.Formatter` を継承し、file_id が設定されている場合のみプレフィックスを追加するカスタムフォーマッターを実装する。

### Rationale

- **条件付き出力**: file_id がない場合はプレフィックスなし（空文字列にならない）
- **既存コード変更不要**: フォーマッターレベルで処理するため、logger 呼び出しは変更不要
- **Kedro 互換**: logging.yml で設定可能

### Implementation Pattern

```python
import logging
from obsidian_etl.utils.log_context import get_file_id

class ContextAwareFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        file_id = get_file_id()
        if file_id:
            # file_id がある場合はプレフィックス追加
            original_msg = record.msg
            record.msg = f"[{file_id}] {original_msg}"
            result = super().format(record)
            record.msg = original_msg  # 元に戻す（再利用対策）
            return result
        return super().format(record)
```

### logging.yml Configuration

```yaml
formatters:
  context_aware:
    (): obsidian_etl.utils.log_context.ContextAwareFormatter
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    datefmt: "%Y-%m-%dT%H:%M:%S"
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| logging.Filter + extra | record.msg を変更する方がシンプル |
| structlog | 追加依存、既存コードへの影響大 |

---

## 3. Ollama 例外クラス設計

### Decision

`OllamaError` 基底クラスと、具体的なエラー種別に応じた派生クラスを定義する。

### Rationale

- **エラー種別の識別**: except ブロックで特定のエラーのみキャッチ可能
- **追加情報の保持**: `context_len` などのデバッグ情報を例外に含める
- **Python 標準パターン**: Exception 継承のベストプラクティスに従う

### Implementation Pattern

```python
class OllamaError(Exception):
    """Base exception for Ollama API errors."""

    def __init__(self, message: str, context_len: int = 0):
        self.context_len = context_len
        super().__init__(message)


class OllamaEmptyResponseError(OllamaError):
    """LLM returned empty or whitespace-only response."""
    pass


class OllamaTimeoutError(OllamaError):
    """Request timed out."""
    pass


class OllamaConnectionError(OllamaError):
    """Failed to connect to Ollama server."""
    pass
```

### call_ollama Changes

```python
def call_ollama(...) -> str:  # 戻り値を str に変更
    # ...
    if not content.strip():
        raise OllamaEmptyResponseError(
            f"Empty response from LLM",
            context_len=context_len
        )
    return content  # 成功時は str のみ
```

### Caller Pattern

```python
try:
    response = call_ollama(...)
except OllamaError as e:
    logger.warning(f"LLM error: {e} (context_len={e.context_len})")
    return "", "other"  # デフォルト値で処理継続
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| タプル返却を維持 | エラーの見落としリスク、コードの意図が不明確 |
| Result 型 | Python では例外が標準的、追加依存が必要 |

---

## 4. パーティション処理での file_id 設定

### Decision

各 nodes.py のパーティション処理ループ内で、処理開始時に `set_file_id()` を呼び出す。

### Rationale

- **最小侵襲**: 既存のループ構造を変更せず、1行追加のみ
- **明示的**: どこで file_id が設定されるか明確
- **柔軟**: 処理単位ごとに適切な file_id を設定可能

### Implementation Pattern

```python
from obsidian_etl.utils.log_context import set_file_id

def extract_knowledge(partitions: dict[str, Callable], params: dict) -> dict:
    results = {}
    for key, load_func in partitions.items():
        # パーティション処理開始時に file_id 設定
        file_id = key  # または metadata から取得
        set_file_id(file_id)

        data = load_func()
        # ... 処理 ...
        # このスコープ内のすべてのログに [file_id] が自動付与

    return results
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Kedro hooks | ノードレベルでは file_id 不明、パーティションレベルで設定必要 |
| デコレータ | パーティションループ内で設定する必要があり、デコレータでは対応困難 |
| コンテキストマネージャ | 過剰な構造、1行の set_file_id() で十分 |

---

## 5. 既存の手動プレフィックス削除

### Decision

`organize/nodes.py` にある `f"[{file_id}] ..."` 形式の手動プレフィックスをすべて削除する。

### Rationale

- **重複防止**: フォーマッターで自動追加されるため、手動追加は不要
- **一貫性**: すべてのログが同じ形式になる
- **保守性**: file_id の追加を1箇所で管理

### Affected Code

```python
# Before
logger.warning(f"[{file_id}] Failed to extract topic and genre via LLM: {error}")

# After
logger.warning(f"Failed to extract topic and genre via LLM: {error}")
```

### Search Pattern

```bash
# 影響箇所の特定
grep -n '\[{file_id}\]' src/obsidian_etl/
```

---

## Summary

| 技術選択 | 決定 | 理由 |
|---------|------|------|
| ログコンテキスト | contextvars | 標準ライブラリ、スレッドセーフ |
| フォーマッター | カスタム Formatter | 条件付き出力、既存コード変更不要 |
| 例外クラス | 階層構造 | エラー種別識別、Python 標準パターン |
| file_id 設定 | ループ内で set_file_id() | 最小侵襲、明示的 |
| 既存手動プレフィックス | 削除 | 重複防止、一貫性 |
