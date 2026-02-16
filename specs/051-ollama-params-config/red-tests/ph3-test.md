# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - User Story 2 - デフォルト値の適用
- FAIL テスト数: 8
- テストファイル: `tests/utils/test_ollama_config.py`

## FAIL テスト一覧

| テストファイル | テストクラス | テストメソッド | 期待動作 |
|---------------|-------------|---------------|---------|
| tests/utils/test_ollama_config.py | TestHardcodedDefaultsApplied | test_empty_params_returns_hardcoded_defaults | 空の params で HARDCODED_DEFAULTS が返される |
| tests/utils/test_ollama_config.py | TestHardcodedDefaultsApplied | test_empty_ollama_section_returns_hardcoded_defaults | ollama セクションが空で HARDCODED_DEFAULTS が返される |
| tests/utils/test_ollama_config.py | TestPartialDefaultsMerge | test_partial_defaults_merge | defaults で一部のみ指定した場合、残りは HARDCODED_DEFAULTS が使用される |
| tests/utils/test_ollama_config.py | TestPartialFunctionOverride | test_partial_function_override | 関数別設定で一部のみオーバーライドした場合、残りは defaults/HARDCODED が使用される |
| tests/utils/test_ollama_config.py | TestTimeoutValidation | test_timeout_below_min_raises | timeout=0 で ValueError が発生する |
| tests/utils/test_ollama_config.py | TestTimeoutValidation | test_timeout_above_max_raises | timeout=601 で ValueError が発生する |
| tests/utils/test_ollama_config.py | TestTemperatureValidation | test_temperature_below_min_raises | temperature=-0.1 で ValueError が発生する |
| tests/utils/test_ollama_config.py | TestTemperatureValidation | test_temperature_above_max_raises | temperature=2.1 で ValueError が発生する |

## 境界値テスト (PASS - バリデーション不要)

以下のテストは現在の実装で既に PASS している（境界値は有効）:

| テストクラス | テストメソッド | 期待動作 |
|-------------|---------------|---------|
| TestTimeoutValidation | test_timeout_at_boundary_valid | timeout=1, timeout=600 が正常に動作する |
| TestTemperatureValidation | test_temperature_at_boundary_valid | temperature=0.0, temperature=2.0 が正常に動作する |

## 実装ヒント

### 1. HARDCODED_DEFAULTS 定数の追加

`src/obsidian_etl/utils/ollama_config.py` に以下を追加:

```python
HARDCODED_DEFAULTS = {
    "model": "gemma3:12b",
    "base_url": "http://localhost:11434",
    "timeout": 120,
    "temperature": 0.2,
    "num_predict": -1,
}
```

### 2. get_ollama_config のマージロジック修正

現在の実装:
```python
merged = {**defaults, **overrides}
return OllamaConfig(**merged)
```

修正後:
```python
merged = {**HARDCODED_DEFAULTS, **defaults, **overrides}
return OllamaConfig(**merged)
```

### 3. バリデーションロジック追加

```python
def _validate_config(config: dict) -> dict:
    """Validate and sanitize config values."""
    # Timeout validation (1-600)
    timeout = config.get("timeout", HARDCODED_DEFAULTS["timeout"])
    if timeout < 1 or timeout > 600:
        raise ValueError(f"timeout must be between 1 and 600, got {timeout}")

    # Temperature validation (0.0-2.0)
    temperature = config.get("temperature", HARDCODED_DEFAULTS["temperature"])
    if temperature < 0.0 or temperature > 2.0:
        raise ValueError(f"temperature must be between 0.0 and 2.0, got {temperature}")

    return config
```

### Merge Priority (data-model.md より)

```
HARDCODED_DEFAULTS < ollama.defaults < ollama.functions.{function_name}
```

## FAIL 出力例

```
======================================================================
ERROR: test_empty_params_returns_hardcoded_defaults (tests.utils.test_ollama_config.TestHardcodedDefaultsApplied.test_empty_params_returns_hardcoded_defaults)
空の params で HARDCODED_DEFAULTS が返されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/utils/test_ollama_config.py", line 394, in test_empty_params_returns_hardcoded_defaults
    from obsidian_etl.utils.ollama_config import (
    ...<3 lines>...
    )
ImportError: cannot import name 'HARDCODED_DEFAULTS' from 'obsidian_etl.utils.ollama_config'

======================================================================
ERROR: test_partial_defaults_merge (tests.utils.test_ollama_config.TestPartialDefaultsMerge.test_partial_defaults_merge)
defaults で一部のみ指定した場合、残りは HARDCODED_DEFAULTS が使用されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/utils/test_ollama_config.py", line 446, in test_partial_defaults_merge
    from obsidian_etl.utils.ollama_config import (
    ...<3 lines>...
    )
ImportError: cannot import name 'HARDCODED_DEFAULTS' from 'obsidian_etl.utils.ollama_config'

======================================================================
FAIL: test_timeout_below_min_raises (tests.utils.test_ollama_config.TestTimeoutValidation.test_timeout_below_min_raises)
timeout が 0 以下の場合、ValueError が発生すること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/utils/test_ollama_config.py", line 549, in test_timeout_below_min_raises
    with self.assertRaises(ValueError) as ctx:
AssertionError: ValueError not raised

======================================================================
FAIL: test_temperature_below_min_raises (tests.utils.test_ollama_config.TestTemperatureValidation.test_temperature_below_min_raises)
temperature が 0.0 未満の場合、ValueError が発生すること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/utils/test_ollama_config.py", line 609, in test_temperature_below_min_raises
    with self.assertRaises(ValueError) as ctx:
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 333 tests in 1.143s

FAILED (failures=4, errors=4)
```

## テスト実行コマンド

```bash
# 全テスト実行 (RED 確認)
make test

# 新規テストのみ実行
.venv/bin/python -m unittest tests.utils.test_ollama_config -v

# 特定テストクラスのみ実行
.venv/bin/python -m unittest tests.utils.test_ollama_config.TestHardcodedDefaultsApplied -v
.venv/bin/python -m unittest tests.utils.test_ollama_config.TestTimeoutValidation -v
.venv/bin/python -m unittest tests.utils.test_ollama_config.TestTemperatureValidation -v
```

## 次ステップ

phase-executor が「実装 (GREEN)」→「検証」を実行:

1. T033: RED tests 読み込み
2. T034: `HARDCODED_DEFAULTS` 定数を `src/obsidian_etl/utils/ollama_config.py` に追加
3. T035: `get_ollama_config()` に timeout バリデーション (1-600) を追加
4. T036: `get_ollama_config()` に temperature バリデーション (0.0-2.0) を追加
5. T037: レガシー params フォールバック (import.ollama, organize.ollama) を追加 ※tasks.md では削除済み
6. T038: `make test` PASS 確認

## テストクラス構成

```python
# Phase 3 RED Tests: User Story 2 - デフォルト値の適用

class TestHardcodedDefaultsApplied(unittest.TestCase):
    """get_ollama_config: Empty params returns hardcoded defaults."""
    # test_empty_params_returns_hardcoded_defaults
    # test_empty_ollama_section_returns_hardcoded_defaults


class TestPartialDefaultsMerge(unittest.TestCase):
    """get_ollama_config: Partial defaults merged with hardcoded."""
    # test_partial_defaults_merge


class TestPartialFunctionOverride(unittest.TestCase):
    """get_ollama_config: Partial function override uses defaults for rest."""
    # test_partial_function_override


class TestTimeoutValidation(unittest.TestCase):
    """get_ollama_config: Timeout validation (1-600 seconds)."""
    # test_timeout_below_min_raises
    # test_timeout_above_max_raises
    # test_timeout_at_boundary_valid


class TestTemperatureValidation(unittest.TestCase):
    """get_ollama_config: Temperature validation (0.0-2.0)."""
    # test_temperature_below_min_raises
    # test_temperature_above_max_raises
    # test_temperature_at_boundary_valid
```
