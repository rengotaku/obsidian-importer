# Phase 2 RED Tests

## サマリー
- Phase: Phase 2 - User Story 1 - 関数別パラメーター設定
- FAIL テスト数: 10
- テストファイル: `tests/utils/test_ollama_config.py`

## FAIL テスト一覧

| テストファイル | テストクラス | テストメソッド | 期待動作 |
|---------------|-------------|---------------|---------|
| tests/utils/test_ollama_config.py | TestOllamaConfigDataclass | test_ollama_config_has_all_fields | OllamaConfig が全フィールド (model, base_url, timeout, temperature, num_predict) を持つ |
| tests/utils/test_ollama_config.py | TestOllamaConfigDataclass | test_ollama_config_is_dataclass | OllamaConfig が dataclass である |
| tests/utils/test_ollama_config.py | TestOllamaConfigDataclass | test_ollama_config_defaults | OllamaConfig のデフォルト値が正しい |
| tests/utils/test_ollama_config.py | TestGetConfigExtractKnowledge | test_get_config_extract_knowledge | extract_knowledge 用設定 (num_predict=16384, timeout=300) が返される |
| tests/utils/test_ollama_config.py | TestGetConfigTranslateSummary | test_get_config_translate_summary | translate_summary 用設定 (num_predict=1024) が返される |
| tests/utils/test_ollama_config.py | TestGetConfigExtractTopic | test_get_config_extract_topic | extract_topic 用設定 (model="llama3.2:3b", num_predict=64, timeout=30) が返される |
| tests/utils/test_ollama_config.py | TestFunctionOverridePriority | test_function_override_priority | 関数別設定がデフォルト値をオーバーライドする |
| tests/utils/test_ollama_config.py | TestFunctionOverridePriority | test_function_override_all_fields | 全フィールドオーバーライドが適用される |
| tests/utils/test_ollama_config.py | TestGetConfigUnknownFunction | test_unknown_function_uses_defaults | 未知の関数名でデフォルト値が使用される |
| tests/utils/test_ollama_config.py | TestGetConfigMissingFunctionsSection | test_missing_functions_section_uses_defaults | functions セクションがない場合デフォルト値が使用される |

## 実装ヒント

### 新規モジュール作成

`src/obsidian_etl/utils/ollama_config.py` を作成:

```python
from dataclasses import dataclass

@dataclass
class OllamaConfig:
    """Ollama configuration for a specific function."""
    model: str = "gemma3:12b"
    base_url: str = "http://localhost:11434"
    timeout: int = 120
    temperature: float = 0.2
    num_predict: int = -1  # -1 = unlimited


def get_ollama_config(params: dict, function_name: str) -> OllamaConfig:
    """
    Merge defaults and function-specific overrides.

    1. defaults から基本設定を取得
    2. functions.{function_name} でオーバーライド
    3. OllamaConfig として返却
    """
    defaults = params.get("ollama", {}).get("defaults", {})
    overrides = params.get("ollama", {}).get("functions", {}).get(function_name, {})
    merged = {**defaults, **overrides}
    return OllamaConfig(**merged)
```

### テストで期待される設定値

From `contracts/parameters.yml`:

| Function | Override Parameters |
|----------|---------------------|
| extract_knowledge | num_predict=16384, timeout=300 |
| translate_summary | num_predict=1024 |
| extract_topic | model="llama3.2:3b", num_predict=64, timeout=30 |

### Merge Priority

```
HARDCODED_DEFAULTS < ollama.defaults < ollama.functions.{name}
```

## FAIL 出力例

```
======================================================================
ERROR: test_get_config_extract_knowledge (tests.utils.test_ollama_config.TestGetConfigExtractKnowledge.test_get_config_extract_knowledge)
extract_knowledge 関数用の設定が正しく返されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/utils/test_ollama_config.py", line 85, in test_get_config_extract_knowledge
    from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config
ModuleNotFoundError: No module named 'obsidian_etl.utils.ollama_config'

======================================================================
ERROR: test_get_config_translate_summary (tests.utils.test_ollama_config.TestGetConfigTranslateSummary.test_get_config_translate_summary)
translate_summary 関数用の設定が正しく返されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/utils/test_ollama_config.py", line 135, in test_get_config_translate_summary
    from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config
ModuleNotFoundError: No module named 'obsidian_etl.utils.ollama_config'

======================================================================
ERROR: test_get_config_extract_topic (tests.utils.test_ollama_config.TestGetConfigExtractTopic.test_get_config_extract_topic)
extract_topic 関数用の設定が正しく返されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/utils/test_ollama_config.py", line 186, in test_get_config_extract_topic
    from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config
ModuleNotFoundError: No module named 'obsidian_etl.utils.ollama_config'

======================================================================
ERROR: test_function_override_priority (tests.utils.test_ollama_config.TestFunctionOverridePriority.test_function_override_priority)
関数別設定がデフォルト値をオーバーライドすること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/utils/test_ollama_config.py", line 236, in test_function_override_priority
    from obsidian_etl.utils.ollama_config import OllamaConfig, get_ollama_config
ModuleNotFoundError: No module named 'obsidian_etl.utils.ollama_config'

----------------------------------------------------------------------
Ran 323 tests in 1.194s

FAILED (errors=10)
```

## テスト実行コマンド

```bash
# 全テスト実行 (RED 確認)
make test

# 新規テストのみ実行
.venv/bin/python -m unittest tests.utils.test_ollama_config -v
```

## 次ステップ

phase-executor が「実装 (GREEN)」→「検証」を実行:

1. T018: RED tests 読み込み
2. T019: `src/obsidian_etl/utils/ollama_config.py` に OllamaConfig dataclass 作成
3. T020: `get_ollama_config()` 関数実装
4. T021: VALID_FUNCTION_NAMES 定数とバリデーション追加
5. T022: `make test` PASS 確認

## テストファイル全体

```python
"""Tests for ollama_config module.

Phase 2 RED tests: OllamaConfig dataclass, get_ollama_config function.
These tests verify:
- get_ollama_config returns correct config for each function
- Function-specific overrides take precedence over defaults
- Defaults are applied when function-specific config is missing
"""

from __future__ import annotations

import unittest


class TestOllamaConfigDataclass(unittest.TestCase):
    """OllamaConfig: dataclass with correct fields and defaults."""
    # ... (10 test methods total)


class TestGetConfigExtractKnowledge(unittest.TestCase):
    """get_ollama_config: extract_knowledge function configuration."""
    # test_get_config_extract_knowledge


class TestGetConfigTranslateSummary(unittest.TestCase):
    """get_ollama_config: translate_summary function configuration."""
    # test_get_config_translate_summary


class TestGetConfigExtractTopic(unittest.TestCase):
    """get_ollama_config: extract_topic function configuration."""
    # test_get_config_extract_topic


class TestFunctionOverridePriority(unittest.TestCase):
    """get_ollama_config: Function-specific values override defaults."""
    # test_function_override_priority
    # test_function_override_all_fields


class TestGetConfigUnknownFunction(unittest.TestCase):
    """get_ollama_config: Unknown function name falls back to defaults."""
    # test_unknown_function_uses_defaults


class TestGetConfigMissingFunctionsSection(unittest.TestCase):
    """get_ollama_config: Missing 'functions' section uses defaults."""
    # test_missing_functions_section_uses_defaults
```
