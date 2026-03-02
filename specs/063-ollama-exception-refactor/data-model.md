# Data Model: call_ollama 例外ベースリファクタリング + 汎用ログコンテキスト

**Date**: 2026-03-01
**Feature**: 063-ollama-exception-refactor

## Entities

### 1. LogContext (contextvars モジュール)

ログコンテキストを管理するためのモジュール。

**Location**: `src/obsidian_etl/utils/log_context.py`

```python
# モジュールレベル変数
_file_id_var: ContextVar[str]  # デフォルト: ""

# 関数
set_file_id(file_id: str) -> None
get_file_id() -> str
clear_file_id() -> None
```

**State Transitions**:

```
[未設定] --set_file_id(id)--> [設定済み] --clear_file_id()--> [未設定]
                                  |
                                  +--set_file_id(new_id)--> [設定済み(上書き)]
```

---

### 2. ContextAwareFormatter (logging.Formatter 継承)

file_id を自動的にログメッセージにプレフィックスとして追加するフォーマッター。

**Location**: `src/obsidian_etl/utils/log_context.py`

```python
class ContextAwareFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str
```

**Behavior**:

| file_id 状態 | 出力形式 |
|-------------|---------|
| 設定済み | `[file_id] メッセージ` |
| 未設定 | `メッセージ` |

---

### 3. OllamaError (Exception 階層)

Ollama API エラーを表す例外クラス階層。

**Location**: `src/obsidian_etl/utils/ollama.py`

```
Exception
└── OllamaError
    ├── OllamaEmptyResponseError
    ├── OllamaTimeoutError
    └── OllamaConnectionError
```

**Attributes**:

| クラス | 属性 | 型 | 説明 |
|-------|------|-----|------|
| OllamaError | message | str | エラーメッセージ |
| OllamaError | context_len | int | 入力コンテキストの文字数 |

---

## Function Signatures

### log_context.py

```python
from contextvars import ContextVar

_file_id_var: ContextVar[str] = ContextVar("file_id", default="")

def set_file_id(file_id: str) -> None:
    """Set file_id for current context."""
    ...

def get_file_id() -> str:
    """Get file_id from current context."""
    ...

def clear_file_id() -> None:
    """Clear file_id from current context."""
    ...

class ContextAwareFormatter(logging.Formatter):
    """Formatter that prepends [file_id] when available."""

    def format(self, record: logging.LogRecord) -> str:
        ...
```

### ollama.py (変更後)

```python
class OllamaError(Exception):
    """Base exception for Ollama API errors."""

    def __init__(self, message: str, context_len: int = 0) -> None:
        ...

class OllamaEmptyResponseError(OllamaError):
    """LLM returned empty or whitespace-only response."""
    pass

class OllamaTimeoutError(OllamaError):
    """Request timed out."""
    pass

class OllamaConnectionError(OllamaError):
    """Failed to connect to Ollama server."""
    pass

def call_ollama(
    system_prompt: str,
    user_message: str,
    model: str,
    base_url: str = "http://localhost:11434",
    num_ctx: int = 65536,
    num_predict: int = -1,
    temperature: float = 0.2,
    timeout: int = 120,
    warmup_timeout: int = 30,
) -> str:  # 変更: tuple[str, str | None] → str
    """Call Ollama API.

    Returns:
        Response content string.

    Raises:
        OllamaEmptyResponseError: When LLM returns empty response.
        OllamaTimeoutError: When request times out.
        OllamaConnectionError: When connection fails.
        OllamaWarmupError: When model warmup fails.
    """
    ...
```

---

## Configuration Changes

### conf/base/logging.yml

```yaml
version: 1

disable_existing_loggers: false

formatters:
  simple:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    datefmt: "%Y-%m-%dT%H:%M:%S"

  context_aware:
    (): obsidian_etl.utils.log_context.ContextAwareFormatter
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    datefmt: "%Y-%m-%dT%H:%M:%S"

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: context_aware  # 変更: simple → context_aware
    stream: ext://sys.stdout

  info_file:
    class: logging.FileHandler
    level: INFO
    formatter: context_aware  # 変更: simple → context_aware
    filename: logs/info.log
    mode: a

loggers:
  kedro:
    level: INFO

  obsidian_etl:
    level: INFO

root:
  level: WARNING
  handlers: [console]
```

---

## Validation Rules

### OllamaError

- `message` は空文字列でも可
- `context_len` は 0 以上の整数

### file_id

- 空文字列はコンテキスト未設定を意味する
- 12文字の SHA256 ハッシュプレフィックスが一般的だが、任意の文字列を許容

---

## Relationships

```
ContextAwareFormatter --uses--> get_file_id()
                                    |
                                    v
nodes.py --calls--> set_file_id() --sets--> _file_id_var

call_ollama() --raises--> OllamaError
                              |
                              v
caller (nodes.py) --catches--> OllamaError --logs--> logger.warning()
                                                          |
                                                          v
                                               ContextAwareFormatter --prepends--> [file_id]
```
