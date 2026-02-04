# Phase 2 RED Tests

## サマリー
- Phase: Phase 2 - User Story 3: Extract Output 固定ファイル名とレコード分割
- FAIL テスト数: 7
- テストファイル: `src/etl/tests/test_stages.py`

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_stages.py | test_fixed_filename_pattern_data_dump_0001 | Extract output ファイル名が data-dump-0001.jsonl になる |
| test_stages.py | test_record_splitting_at_1000_records | 1001 レコードで 2 ファイルに分割される |
| test_stages.py | test_file_index_increments_correctly | 2500 レコードで 3 ファイル (0001, 0002, 0003) に分割される |
| test_stages.py | test_transform_stage_also_uses_fixed_filename | Transform stage も固定ファイル名を使用する |
| test_stages.py | test_stage_has_output_file_index_attribute | BaseStage に _output_file_index 属性が存在する |
| test_stages.py | test_stage_has_output_record_count_attribute | BaseStage に _output_record_count 属性が存在する |
| test_stage_has_max_records_per_file_attribute | BaseStage に _max_records_per_file 属性が存在する |

## 実装ヒント

### 1. BaseStage に新規属性を追加 (`src/etl/core/stage.py`)

```python
class BaseStage(ABC):
    def __init__(self):
        # 新規属性（data-model.md より）
        self._output_file_index: int = 1  # ファイル番号（1-based）
        self._output_record_count: int = 0  # 現在のファイルのレコード数
        self._max_records_per_file: int = 1000  # ファイルあたり最大レコード数
```

### 2. `_write_output_item()` を修正

現在の実装:
```python
def _write_output_item(self, ctx: StageContext, item: ProcessingItem) -> None:
    # 現在: item.source_path.stem を使用 (例: conversations.jsonl)
    safe_name = item.source_path.stem.replace("/", "_").replace("\\", "_")
    output_file = ctx.output_path / f"{safe_name}.jsonl"
```

新しい実装:
```python
def _write_output_item(self, ctx: StageContext, item: ProcessingItem) -> None:
    # 固定ファイル名パターン: data-dump-0001.jsonl
    output_file = ctx.output_path / f"data-dump-{self._output_file_index:04d}.jsonl"

    # レコード書き込み後にカウント更新
    self._output_record_count += 1

    # 1000 レコード超過で次のファイルに切り替え
    if self._output_record_count >= self._max_records_per_file:
        self._output_file_index += 1
        self._output_record_count = 0
```

### 3. 状態遷移（data-model.md より）

```
初期状態: _output_file_index=1, _output_record_count=0
  ↓ レコード書き込み
_output_record_count++
  ↓ _output_record_count >= 1000
_output_file_index++, _output_record_count=0
```

## FAIL 出力例

```
FAIL: test_fixed_filename_pattern_data_dump_0001 (src.etl.tests.test_stages.TestExtractOutputFixedFilename)
----------------------------------------------------------------------
AssertionError: 0 != 1

# 現在は data-dump-*.jsonl ファイルが生成されない
# {safe_name}.jsonl 形式（例: conv1.jsonl）で生成されている

FAIL: test_stage_has_output_file_index_attribute (src.etl.tests.test_stages.TestExtractOutputFixedFilename)
----------------------------------------------------------------------
AssertionError: False is not true

# BaseStage に _output_file_index 属性が存在しない
```

## 検証コマンド

```bash
# テスト実行
make test

# 特定テストクラスのみ実行
python -m pytest src/etl/tests/test_stages.py::TestExtractOutputFixedFilename -v
```

## 次ステップ

phase-executor が「実装 (GREEN)」を実行:
- T010: Read RED tests
- T011: Add _output_file_index, _output_record_count, _max_records_per_file attributes to BaseStage
- T012: Modify _write_output_item() to use fixed filename pattern
- T013: Implement record splitting logic
- T014: Verify make test PASS (GREEN)
