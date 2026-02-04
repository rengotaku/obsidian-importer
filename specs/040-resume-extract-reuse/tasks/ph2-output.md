# Phase 2 Output

## 作業概要
- User Story 3: Extract Output 固定ファイル名とレコード分割の実装完了
- FAIL テスト 7 件を PASS させた
- Extract/Transform stage の output が固定ファイル名パターン（data-dump-{番号4桁}.jsonl）で 1000 レコードごとに分割されるようになった

## 修正ファイル一覧
- `src/etl/core/stage.py` - BaseStage に出力ファイル追跡機能を追加
  - `__init__()` に `_output_file_index`, `_output_record_count`, `_max_records_per_file` 属性を追加
  - `_write_output_item()` を固定ファイル名パターン `data-dump-{番号4桁}.jsonl` に変更
  - レコード分割ロジック実装（1000 レコード超過で次ファイルに切り替え）
  - `_write_debug_step_output()` と `_write_debug_output()` にフォルダ作成処理を追加
  - ResumableStage の `__init__()` に `super().__init__()` 追加

- `src/etl/stages/transform/knowledge_transformer.py` - KnowledgeTransformer の `__init__()` に `super().__init__()` 追加
- `src/etl/stages/transform/normalizer_transformer.py` - NormalizerTransformer の `__init__()` に `super().__init__()` 追加
- `src/etl/stages/load/session_loader.py` - SessionLoader の `__init__()` に `super().__init__()` 追加
- `src/etl/stages/load/vault_loader.py` - VaultLoader の `__init__()` に `super().__init__()` 追加

## テスト結果
- Phase 2 テスト: 7/7 PASS
  - `test_fixed_filename_pattern_data_dump_0001` ✅
  - `test_record_splitting_at_1000_records` ✅
  - `test_file_index_increments_correctly` ✅
  - `test_transform_stage_also_uses_fixed_filename` ✅
  - `test_stage_has_output_file_index_attribute` ✅
  - `test_stage_has_output_record_count_attribute` ✅
  - `test_stage_has_max_records_per_file_attribute` ✅

- 全体テスト（test_stages.py）: 62/62 PASS

## 注意点
- **次 Phase（Phase 3）への引き継ぎ**:
  - Extract output は固定ファイル名パターン `data-dump-0001.jsonl`, `data-dump-0002.jsonl` で分割出力される
  - BasePhaseOrchestrator 実装時、この固定パターンを利用して Resume 時に JSONL を読み込む
  - Resume 読み込み時は `glob("data-dump-*.jsonl")` で検索する
  - `steps.jsonl`, `error_details.jsonl`, `pipeline_stages.jsonl` は除外する必要がある

- **BaseStage 継承クラスへの影響**:
  - すべての BaseStage サブクラスで `super().__init__()` 呼び出しが必須
  - BaseExtractor は既に対応済み（`src/etl/core/extractor.py:34`）
  - FileExtractor も対応済み（`src/etl/stages/extract/file_extractor.py`）
  - 新規作成する Stage クラスは必ず `super().__init__()` を呼び出すこと

## 実装のミス・課題
- なし。すべてのテストが GREEN で、既存機能への影響もなし

## 実装の詳細

### 1. BaseStage.__init__() の追加
```python
def __init__(self):
    """Initialize BaseStage with output file tracking attributes."""
    self._output_file_index: int = 1  # 1-indexed (data-dump-0001.jsonl)
    self._output_record_count: int = 0  # Current file record count
    self._max_records_per_file: int = 1000  # Records per file (default: 1000)
```

### 2. _write_output_item() の変更
```python
# US3: Use fixed filename pattern data-dump-{番号4桁}.jsonl
output_file = ctx.output_path / f"data-dump-{self._output_file_index:04d}.jsonl"

# Serialize and write item
# ...

# US3: Increment record count and split if necessary
self._output_record_count += 1

# US3: Split to next file after reaching max records per file
if self._output_record_count >= self._max_records_per_file:
    self._output_file_index += 1
    self._output_record_count = 0
```

### 3. フォルダ作成処理の追加
`_write_debug_step_output()` と `_write_debug_output()` の両方に以下を追加:
```python
# Ensure stage folder exists before writing
stage_folder.mkdir(parents=True, exist_ok=True)
```

これにより、テストで `stage_data.ensure_folders()` が呼ばれない場合でも、自動的にフォルダが作成されるようになった。

## 次 Phase のタスク
Phase 3 (User Story 2) では、BasePhaseOrchestrator クラスを作成し、Template Method パターンで Resume ロジックを FW レベルで管理する。

- BasePhaseOrchestrator.run() が Extract output（data-dump-*.jsonl）の存在を確認
- 存在する場合、JSONL から ProcessingItem を復元
- 存在しない場合、通常通り input フォルダから処理
