# Phase 3 RED Tests

## Summary
- Phase: Phase 3 - User Story 2 - FW による Resume 制御フローの一元管理
- FAIL テスト数: 20
- テストファイル: `src/etl/tests/test_phase_orchestrator.py`

## FAIL テスト一覧

| テストファイル | テストクラス | テストメソッド | 期待動作 |
|---------------|-------------|---------------|---------|
| test_phase_orchestrator.py | TestBasePhaseOrchestratorAbstract | test_base_phase_orchestrator_is_abstract | BasePhaseOrchestrator は ABC として定義され、直接インスタンス化できない |
| test_phase_orchestrator.py | TestBasePhaseOrchestratorAbstract | test_base_phase_orchestrator_requires_phase_type_property | phase_type プロパティ未実装で TypeError |
| test_phase_orchestrator.py | TestBasePhaseOrchestratorAbstract | test_base_phase_orchestrator_requires_run_extract_stage | _run_extract_stage 未実装で TypeError |
| test_phase_orchestrator.py | TestBasePhaseOrchestratorAbstract | test_base_phase_orchestrator_requires_run_transform_stage | _run_transform_stage 未実装で TypeError |
| test_phase_orchestrator.py | TestBasePhaseOrchestratorAbstract | test_base_phase_orchestrator_requires_run_load_stage | _run_load_stage 未実装で TypeError |
| test_phase_orchestrator.py | TestBasePhaseOrchestratorRunOrder | test_run_calls_stages_in_etl_order | run() が Extract -> Transform -> Load の順で呼び出す |
| test_phase_orchestrator.py | TestBasePhaseOrchestratorRunOrder | test_run_returns_phase_result | run() が PhaseResult を返す |
| test_phase_orchestrator.py | TestBasePhaseOrchestratorRunOrder | test_run_passes_items_between_stages | run() がアイテムを各ステージ間で受け渡す |
| test_phase_orchestrator.py | TestShouldLoadExtractFromOutput | test_returns_true_when_data_dump_files_exist | data-dump-*.jsonl 存在時に True 返す |
| test_phase_orchestrator.py | TestShouldLoadExtractFromOutput | test_returns_false_when_no_data_dump_files | data-dump 非存在時に False 返す |
| test_phase_orchestrator.py | TestShouldLoadExtractFromOutput | test_returns_false_when_output_folder_missing | output フォルダ非存在時に False 返す |
| test_phase_orchestrator.py | TestShouldLoadExtractFromOutput | test_excludes_steps_jsonl_from_detection | steps.jsonl を検出対象から除外 |
| test_phase_orchestrator.py | TestShouldLoadExtractFromOutput | test_excludes_error_details_jsonl_from_detection | error_details.jsonl を検出対象から除外 |
| test_phase_orchestrator.py | TestShouldLoadExtractFromOutput | test_excludes_pipeline_stages_jsonl_from_detection | pipeline_stages.jsonl を検出対象から除外 |
| test_phase_orchestrator.py | TestLoadExtractItemsFromOutput | test_loads_processing_items_from_jsonl | JSONL から ProcessingItem を復元 |
| test_phase_orchestrator.py | TestLoadExtractItemsFromOutput | test_loads_items_from_multiple_data_dump_files | 複数 data-dump-*.jsonl から読み込み |
| test_phase_orchestrator.py | TestLoadExtractItemsFromOutput | test_skips_corrupted_json_records | 破損 JSON レコードをスキップ |
| test_phase_orchestrator.py | TestLoadExtractItemsFromOutput | test_excludes_steps_jsonl_from_loading | steps.jsonl を読み込み対象から除外 |
| test_phase_orchestrator.py | TestLoadExtractItemsFromOutput | test_returns_empty_iterator_when_no_files | data-dump 非存在時に空 iterator 返す |
| test_phase_orchestrator.py | TestLoadExtractItemsFromOutput | test_loads_items_in_sorted_file_order | ファイル名ソート順で読み込み |

## テストカテゴリ

### 1. ABC 抽象クラステスト (5 tests)
- `TestBasePhaseOrchestratorAbstract`
- BasePhaseOrchestrator が正しく ABC として定義され、必須の抽象メソッドを要求することを確認

### 2. Template Method テスト (3 tests)
- `TestBasePhaseOrchestratorRunOrder`
- run() メソッドが Extract -> Transform -> Load の順で hooks を呼び出すことを確認
- PhaseResult を返すことを確認
- アイテムがステージ間で受け渡されることを確認

### 3. Resume 検出テスト (6 tests)
- `TestShouldLoadExtractFromOutput`
- _should_load_extract_from_output() が data-dump-*.jsonl の存在を正しく検出することを確認
- steps.jsonl, error_details.jsonl, pipeline_stages.jsonl を除外することを確認

### 4. JSONL 読み込みテスト (6 tests)
- `TestLoadExtractItemsFromOutput`
- _load_extract_items_from_output() が JSONL から ProcessingItem を正しく復元することを確認
- 破損レコードのスキップ、複数ファイル読み込み、ソート順を確認

## 実装ヒント

### 1. `src/etl/core/phase_orchestrator.py` を新規作成

```python
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from src.etl.core.models import ProcessingItem
from src.etl.core.phase import Phase
from src.etl.core.types import PhaseType


class BasePhaseOrchestrator(ABC):
    """Phase 実行の共通基底クラス。Template Method パターンで run() を実装。"""

    @property
    @abstractmethod
    def phase_type(self) -> PhaseType:
        """Phase の種類（IMPORT, ORGANIZE）"""
        ...

    @abstractmethod
    def _run_extract_stage(self, ctx, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
        """Extract stage 実行（各 Phase が実装）"""
        ...

    @abstractmethod
    def _run_transform_stage(self, ctx, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
        """Transform stage 実行（各 Phase が実装）"""
        ...

    @abstractmethod
    def _run_load_stage(self, ctx, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
        """Load stage 実行（各 Phase が実装）"""
        ...

    def _should_load_extract_from_output(self, phase_data: Phase) -> bool:
        """Extract output の存在確認（data-dump-*.jsonl）"""
        extract_output = phase_data.base_path / "extract" / "output"
        if not extract_output.exists():
            return False
        # glob for data-dump-*.jsonl, exclude steps.jsonl etc.
        data_dump_files = list(extract_output.glob("data-dump-*.jsonl"))
        return len(data_dump_files) > 0

    def _load_extract_items_from_output(self, phase_data: Phase) -> Iterator[ProcessingItem]:
        """JSONL から ProcessingItem を復元"""
        # glob data-dump-*.jsonl in sorted order
        # parse each line as JSON
        # skip corrupted records
        # yield ProcessingItem.from_dict()
        ...

    def run(self, phase_data: Phase, debug_mode: bool = False, ...) -> PhaseResult:
        """Template Method - FW が制御フロー管理"""
        # 1. Check if should load from extract output (Resume mode)
        # 2. Run Extract stage (or load from output)
        # 3. Run Transform stage
        # 4. Run Load stage
        # 5. Return PhaseResult
        ...
```

### 2. 固定ファイル名パターン

Phase 2 で実装済み: `data-dump-{番号4桁}.jsonl`
- `data-dump-0001.jsonl`
- `data-dump-0002.jsonl`
- ...

### 3. 除外ファイル

以下のファイルは Resume 復元対象から除外:
- `steps.jsonl`
- `error_details.jsonl`
- `pipeline_stages.jsonl`

### 4. 破損 JSON レコードの処理

`json.JSONDecodeError` をキャッチしてスキップ、処理を継続:

```python
try:
    record = json.loads(line)
    yield ProcessingItem.from_dict(record)
except json.JSONDecodeError:
    logging.warning(f"Skipping corrupted JSON record")
    continue
```

## FAIL 出力例

```
EEEEEEEEEEEEEEEEEEEE
======================================================================
ERROR: test_base_phase_orchestrator_is_abstract (src.etl.tests.test_phase_orchestrator.TestBasePhaseOrchestratorAbstract.test_base_phase_orchestrator_is_abstract)
BasePhaseOrchestrator cannot be instantiated directly.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_phase_orchestrator.py", line 38, in test_base_phase_orchestrator_is_abstract
    from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
ModuleNotFoundError: No module named 'src.etl.core.phase_orchestrator'

======================================================================
...
----------------------------------------------------------------------
Ran 20 tests in 0.002s

FAILED (errors=20)
```

## 次ステップ

phase-executor が「実装 (GREEN)」を実行:
1. T025: RED tests 読み込み
2. T026-T031: BasePhaseOrchestrator 実装
3. T032: `make test` PASS 確認
