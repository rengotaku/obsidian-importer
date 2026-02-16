# Data Model: Ollama パラメーター関数別設定

**Feature**: 051-ollama-params-config
**Date**: 2026-02-15

## Entities

### OllamaConfig

関数別のOllamaパラメーター設定を表す。

```python
@dataclass
class OllamaConfig:
    """Ollama configuration for a specific function."""

    model: str = "gemma3:12b"
    base_url: str = "http://localhost:11434"
    timeout: int = 120
    temperature: float = 0.2
    num_predict: int = -1  # -1 = unlimited
```

#### Fields

| Field | Type | Default | Description | Validation |
|-------|------|---------|-------------|------------|
| `model` | str | `"gemma3:12b"` | 使用するモデル名 | 空文字不可 |
| `base_url` | str | `"http://localhost:11434"` | Ollama サーバー URL | 有効な URL 形式 |
| `timeout` | int | `120` | リクエストタイムアウト（秒） | 1 <= x <= 600 |
| `temperature` | float | `0.2` | サンプリング温度 | 0.0 <= x <= 2.0 |
| `num_predict` | int | `-1` | 最大出力トークン数 | -1 または 1 以上 |

#### State Transitions

N/A（設定値は不変）

---

### FunctionName

LLM呼び出し関数の識別子。

```python
class FunctionName(str, Enum):
    """Valid function names for per-function config."""

    EXTRACT_KNOWLEDGE = "extract_knowledge"
    TRANSLATE_SUMMARY = "translate_summary"
    EXTRACT_TOPIC = "extract_topic"
```

---

## YAML Schema

### parameters.yml 構造

```yaml
ollama:
  defaults:                      # Required
    model: "gemma3:12b"          # Required
    base_url: "http://localhost:11434"  # Required
    timeout: 120                 # Optional (default: 120)
    temperature: 0.2             # Optional (default: 0.2)
    num_predict: -1              # Optional (default: -1)

  functions:                     # Optional
    extract_knowledge:           # Optional
      num_predict: 16384         # Override defaults
      timeout: 300               # Long timeout for large content

    translate_summary:           # Optional
      num_predict: 1024          # Medium output

    extract_topic:               # Optional
      model: "llama3.2:3b"       # Lighter model for short output
      num_predict: 64            # Very short output
      timeout: 30                # Fast timeout
```

### Validation Rules

1. **defaults セクション**: 必須。`model` と `base_url` は必須フィールド。
2. **functions セクション**: オプション。存在しない関数名は無視。
3. **パラメーター値**:
   - `timeout`: 1〜600 の範囲外は警告を出力しデフォルト値にフォールバック
   - `temperature`: 0.0〜2.0 の範囲外は警告を出力しデフォルト値にフォールバック
   - `num_predict`: -1 または 1 以上。0 は -1 として扱う

---

## Relationships

```
parameters.yml
    │
    ├── ollama.defaults ────────────┐
    │                               │ merge
    └── ollama.functions.{name} ────┴──→ OllamaConfig
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   call_ollama   │
                                    └─────────────────┘
```

### Merge Logic

```python
def get_ollama_config(params: dict, function_name: str) -> OllamaConfig:
    """
    1. defaults から基本設定を取得
    2. functions.{function_name} でオーバーライド
    3. OllamaConfig として返却
    """
    defaults = params.get("ollama", {}).get("defaults", {})
    overrides = params.get("ollama", {}).get("functions", {}).get(function_name, {})

    merged = {**HARDCODED_DEFAULTS, **defaults, **overrides}
    return OllamaConfig(**merged)
```

---

## Migration Path

### 既存設定との互換性

**Before** (現在の構造):
```yaml
import:
  ollama:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
```

**After** (新構造):
```yaml
ollama:
  defaults:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
    num_predict: -1
```

### 移行手順

1. 既存の `import.ollama` と `organize.ollama` を `ollama.defaults` に統合
2. 関数別の設定が必要な場合は `ollama.functions` に追加
3. 既存コードは後方互換性のためフォールバック処理を維持

### 後方互換性

`get_ollama_config` は以下の順序でパラメーターを解決:

1. `ollama.functions.{function_name}.{param}` (最優先)
2. `ollama.defaults.{param}`
3. `import.ollama.{param}` (レガシー互換)
4. `organize.ollama.{param}` (レガシー互換)
5. ハードコードされたデフォルト値
