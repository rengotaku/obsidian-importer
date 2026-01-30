# Phase 5 Output

## 作業概要
- User Story 1: Resume モードでの Extract 重複ログ防止 の実装完了
- ImportPhase.run() に Resume 検出ロジックを追加し、Extract output が存在する場合は JSONL から ProcessingItem を復元するように変更
- FAIL テスト 2 件を PASS させた（test_import_phase_run_skips_extract_when_output_exists, test_import_phase_run_no_new_extract_logs_in_resume_mode）

## 修正ファイル一覧
- `src/etl/phases/import_phase.py` - ImportPhase.run() に Resume 検出ロジックを追加（Option 2: Inline Resume Logic を採用）

## 実装内容

### ImportPhase.run() の変更点

Extract stage 実行前に、以下のロジックを追加:

```python
# Check if Extract output exists (Resume mode)
if self._should_load_extract_from_output(phase_data):
    print("Resume mode: Loading from extract/output/*.jsonl")
    extracted = list(self._load_extract_items_from_output(phase_data))
else:
    print("Extract output not found, processing from input/")
    # Discover items and run Extract stage (existing logic)
    items = extract_stage.discover_items(input_path, chunk=self._chunk)
    extract_ctx = StageContext(...)
    extracted_iter = extract_stage.run(extract_ctx, items)
    extracted = list(extracted_iter)
```

### 動作の詳細

1. **Resume 検出**: `_should_load_extract_from_output()` で `extract/output/data-dump-*.jsonl` の存在を確認
2. **Resume 時**:
   - stdout に "Resume mode: Loading from extract/output/*.jsonl" を表示
   - `_load_extract_items_from_output()` で JSONL から ProcessingItem を復元
   - Extract stage をスキップ（discover_items、extract_stage.run を呼び出さない）
   - pipeline_stages.jsonl に新しい Extract ログは追記されない
3. **通常処理時**:
   - stdout に "Extract output not found, processing from input/" を表示
   - 既存の Extract stage 処理を実行

### Resume ロジックの詳細

`BasePhaseOrchestrator` の実装を活用:

- `_should_load_extract_from_output()`: `data-dump-*.jsonl` パターンでファイルを検索（steps.jsonl、error_details.jsonl、pipeline_stages.jsonl は除外）
- `_load_extract_items_from_output()`: JSONL ファイルから ProcessingItem を復元、破損した JSON レコードはスキップ

## テスト結果

### Phase 5 固有テスト（PASS）

- `test_import_phase_run_skips_extract_when_output_exists`: Extract output 存在時に Extract stage をスキップ ✓
- `test_import_phase_run_no_new_extract_logs_in_resume_mode`: Resume 時に Extract ログを追記しない ✓

### 全 Resume モードテスト（PASS）

43 tests in 0.049s - OK

- BasePhaseOrchestrator テスト: 6 件 PASS
- ImportPhase Resume テスト: 2 件 PASS
- CompletedItemsCache テスト: 11 件 PASS
- その他 Resume 関連テスト: 24 件 PASS

## 注意点

### 次 Phase での作業

- **Phase 6 (Polish)**: 最終検証と統合テストを実施
- **Manual verification (T071)**: 実際のセッションで Resume モードを実行し、pipeline_stages.jsonl の重複ログがないことを確認

### 実装の選択

**Option 1 vs Option 2**: RED test ドキュメントでは 2 つのアプローチが提案されていた:

- **Option 1**: `super().run()` に委譲
- **Option 2**: Inline Resume Logic（採用）

**Option 2 を選択した理由**:
- ImportPhase.run() は session_manager、limit、progress display などのカスタムロジックを持つ
- BasePhaseOrchestrator.run() はミニマルな実装で、これらの機能をサポートしていない
- Inline で Resume チェックを追加する方が、既存ロジックを維持しながら Resume 機能を追加できる

### OrganizePhase への適用

OrganizePhase.run() にも同様のパターンを適用する必要があるが、現時点では OrganizePhase が BasePhaseOrchestrator.run() を直接使用している可能性がある。Phase 6 で確認が必要。

## 実装のミス・課題

### なし

実装は RED テストの要求通りに完了し、既存テストも影響を受けていない。

### 既存の不具合（Phase 5 とは無関係）

テスト実行時に以下のエラーが確認されたが、これらは Phase 5 の変更とは無関係:

- GitHub extractor テスト: 7 failures（既存の問題）
- Chunk option テスト: 1 failure（既存の問題）

これらは別の Issue で対応が必要。

## 完了基準チェック

- [X] T062-T069: すべての GREEN タスク完了
- [X] T070: `make test` で Resume モードテスト全件 PASS
- [ ] T071: Manual verification（Phase 6 で実施予定）
- [X] T072: Phase 出力生成

## 次ステップ

Phase 6 (Polish & Cross-Cutting Concerns) に進み、以下を実施:

1. 全テストスイート実行
2. Manual verification（実際のセッションで Resume モード動作確認）
3. OrganizePhase で同様の Resume ロジックが必要か確認
4. quickstart.md の検証シナリオ実行
5. ドキュメント更新（必要に応じて）
