# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - 圧縮率検証共通処理
- FAIL テスト数: 9
- テストファイル: tests/utils/test_compression_validator.py

## FAIL テスト一覧

| テストファイル | テストクラス | テストメソッド | 期待動作 |
|---------------|-------------|---------------|---------|
| tests/utils/test_compression_validator.py | TestGetThreshold | test_get_threshold_large | 10,000文字以上で 0.10 を返す |
| tests/utils/test_compression_validator.py | TestGetThreshold | test_get_threshold_medium | 5,000-9,999文字で 0.15 を返す |
| tests/utils/test_compression_validator.py | TestGetThreshold | test_get_threshold_small | 5,000文字未満で 0.20 を返す |
| tests/utils/test_compression_validator.py | TestValidateCompression | test_validate_compression_valid | 基準達成時 is_valid=True |
| tests/utils/test_compression_validator.py | TestValidateCompression | test_validate_compression_invalid | 基準未達時 is_valid=False |
| tests/utils/test_compression_validator.py | TestValidateCompression | test_validate_compression_zero_original | original_size=0 で is_valid=True |
| tests/utils/test_compression_validator.py | TestValidateCompressionBodyNone | test_validate_compression_body_none_uses_output | body=None 時 output_size を使用 |
| tests/utils/test_compression_validator.py | TestCompressionResultDataclass | test_compression_result_has_all_fields | 全フィールドを持つ |
| tests/utils/test_compression_validator.py | TestCompressionResultDataclass | test_compression_result_is_dataclass | dataclass である |

## 実装ヒント

### ファイル作成
- `src/obsidian_etl/utils/compression_validator.py` を新規作成

### CompressionResult dataclass

```python
from dataclasses import dataclass

@dataclass
class CompressionResult:
    original_size: int
    output_size: int
    body_size: int
    ratio: float  # output_size / original_size
    body_ratio: float  # body_size / original_size
    threshold: float
    is_valid: bool
    node_name: str
```

### get_threshold(original_size: int) -> float

しきい値のロジック:
- `original_size >= 10000` -> `0.10` (10%)
- `original_size >= 5000` -> `0.15` (15%)
- `original_size < 5000` -> `0.20` (20%)

### validate_compression() 関数

```python
def validate_compression(
    original_content: str,
    output_content: str,
    body_content: str | None,
    node_name: str,
) -> CompressionResult:
```

- `body_content` が `None` の場合、`output_size` を `body_size` として使用
- `original_size == 0` の場合、ゼロ除算を回避して `is_valid=True` を返す
- `is_valid = body_ratio >= threshold`

## FAIL 出力例

```
ERROR: test_get_threshold_large (tests.utils.test_compression_validator.TestGetThreshold.test_get_threshold_large)
10,000文字以上の場合、しきい値が10% (0.10) であること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/utils/test_compression_validator.py", line 27, in test_get_threshold_large
    from obsidian_etl.utils.compression_validator import get_threshold
ModuleNotFoundError: No module named 'obsidian_etl.utils.compression_validator'

----------------------------------------------------------------------
Ran 304 tests in 0.811s

FAILED (errors=9)
```

## 次ステップ

phase-executor が以下を実行:
1. `src/obsidian_etl/utils/compression_validator.py` を作成
2. `CompressionResult` dataclass を実装
3. `get_threshold()` 関数を実装
4. `validate_compression()` 関数を実装
5. `make test` で PASS (GREEN) を確認
