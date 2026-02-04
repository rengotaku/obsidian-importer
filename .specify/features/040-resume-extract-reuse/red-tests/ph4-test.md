# Phase 4 RED Tests

## サマリー
- Phase: Phase 4 - User Story 2 続き - ImportPhase と OrganizePhase の継承変更
- FAIL テスト数: 10
- PASS テスト数: 2 (phase_type property は既存実装で PASS)
- テストファイル: `src/etl/tests/test_phase_orchestrator.py`

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_phase_orchestrator.py | test_import_phase_inherits_base_phase_orchestrator | ImportPhase が BasePhaseOrchestrator を継承すること |
| test_phase_orchestrator.py | test_import_phase_has_run_extract_stage_method | ImportPhase が _run_extract_stage() フックを実装すること |
| test_phase_orchestrator.py | test_import_phase_has_run_transform_stage_method | ImportPhase が _run_transform_stage() フックを実装すること |
| test_phase_orchestrator.py | test_import_phase_has_run_load_stage_method | ImportPhase が _run_load_stage() フックを実装すること |
| test_phase_orchestrator.py | test_import_phase_run_delegates_to_base_orchestrator | ImportPhase.run() が BasePhaseOrchestrator.run() に委譲すること |
| test_phase_orchestrator.py | test_organize_phase_inherits_base_phase_orchestrator | OrganizePhase が BasePhaseOrchestrator を継承すること |
| test_phase_orchestrator.py | test_organize_phase_has_run_extract_stage_method | OrganizePhase が _run_extract_stage() フックを実装すること |
| test_phase_orchestrator.py | test_organize_phase_has_run_transform_stage_method | OrganizePhase が _run_transform_stage() フックを実装すること |
| test_phase_orchestrator.py | test_organize_phase_has_run_load_stage_method | OrganizePhase が _run_load_stage() フックを実装すること |
| test_phase_orchestrator.py | test_organize_phase_run_delegates_to_base_orchestrator | OrganizePhase.run() が BasePhaseOrchestrator.run() に委譲すること |

## PASS テスト一覧

| テストファイル | テストメソッド | 備考 |
|---------------|---------------|------|
| test_phase_orchestrator.py | test_import_phase_has_phase_type_property | 既存実装で PhaseType.IMPORT を返している |
| test_phase_orchestrator.py | test_organize_phase_has_phase_type_property | 既存実装で PhaseType.ORGANIZE を返している |

## 実装ヒント

### ImportPhase (`src/etl/phases/import_phase.py`)

1. `BasePhaseOrchestrator` を継承に追加:
   ```python
   from src.etl.core.phase_orchestrator import BasePhaseOrchestrator

   class ImportPhase(BasePhaseOrchestrator):
       ...
   ```

2. フックメソッド実装:
   ```python
   def _run_extract_stage(self, ctx, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
       # 既存の create_extract_stage() と run() ロジックを移行
       extract_stage = self.create_extract_stage()
       return extract_stage.run(ctx, items)

   def _run_transform_stage(self, ctx, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
       transform_stage = self.create_transform_stage()
       return transform_stage.run(ctx, items)

   def _run_load_stage(self, ctx, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
       load_stage = self.create_load_stage()
       return load_stage.run(ctx, items)
   ```

3. 既存の `run()` メソッドを削除（BasePhaseOrchestrator.run() を使用）

### OrganizePhase (`src/etl/phases/organize_phase.py`)

同様に:
1. `BasePhaseOrchestrator` を継承に追加
2. フックメソッド実装
3. 既存の `run()` メソッドを削除

### 注意点

- `phase_type` プロパティは既存実装を維持（テスト PASS）
- `create_extract_stage()`, `create_transform_stage()`, `create_load_stage()` は残す（フックから呼び出す）
- CompletedItemsCache のビルドロジックは BasePhaseOrchestrator.run() に移行する必要がある
- Resume モード進捗表示ロジックも BasePhaseOrchestrator.run() に移行

## FAIL 出力例

```
FAIL: test_import_phase_inherits_base_phase_orchestrator (src.etl.tests.test_phase_orchestrator.TestImportPhaseInheritance)
----------------------------------------------------------------------
AssertionError: False is not true : ImportPhase must inherit from BasePhaseOrchestrator

FAIL: test_import_phase_has_run_extract_stage_method (src.etl.tests.test_phase_orchestrator.TestImportPhaseInheritance)
----------------------------------------------------------------------
AssertionError: False is not true

FAIL: test_organize_phase_inherits_base_phase_orchestrator (src.etl.tests.test_phase_orchestrator.TestOrganizePhaseInheritance)
----------------------------------------------------------------------
AssertionError: False is not true : OrganizePhase must inherit from BasePhaseOrchestrator
```

## テスト実行コマンド

```bash
# Phase 4 テストのみ実行
python -m unittest src.etl.tests.test_phase_orchestrator.TestImportPhaseInheritance src.etl.tests.test_phase_orchestrator.TestOrganizePhaseInheritance -v

# 全テスト実行
make test
```
