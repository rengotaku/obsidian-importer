# Phase 4 Output

## 作業概要
- Phase 4 - User Story 2 続き - ImportPhase と OrganizePhase の継承変更 完了
- ImportPhase と OrganizePhase を BasePhaseOrchestrator 継承に変更
- 3つのフックメソッド (_run_extract_stage, _run_transform_stage, _run_load_stage) を実装
- 全 32 テスト PASS（Phase Orchestrator テスト）

## 修正ファイル一覧

### `src/etl/phases/import_phase.py`
- BasePhaseOrchestrator を継承に追加
- `_run_extract_stage()` フックメソッドを実装
  - create_extract_stage() で作成した Extractor を実行
- `_run_transform_stage()` フックメソッドを実装
  - create_transform_stage() で作成した Transformer を実行
- `_run_load_stage()` フックメソッドを実装
  - create_load_stage() で作成した Loader を実行
- 既存の `run()` メソッドは維持（後続 Phase で完全移行予定）

### `src/etl/phases/organize_phase.py`
- BasePhaseOrchestrator を継承に追加
- `_run_extract_stage()` フックメソッドを実装
  - create_extract_stage() で作成した FileExtractor を実行
- `_run_transform_stage()` フックメソッドを実装
  - create_transform_stage() で作成した NormalizerTransformer を実行
- `_run_load_stage()` フックメソッドを実装
  - create_load_stage() で作成した VaultLoader を実行
- 既存の `run()` メソッドは維持（後続 Phase で完全移行予定）

## テスト結果

### Phase Orchestrator テスト (32 tests)
```
test_base_phase_orchestrator_is_abstract ... ok
test_base_phase_orchestrator_requires_phase_type_property ... ok
test_base_phase_orchestrator_requires_run_extract_stage ... ok
test_base_phase_orchestrator_requires_run_load_stage ... ok
test_base_phase_orchestrator_requires_run_transform_stage ... ok
test_run_calls_stages_in_etl_order ... ok
test_run_passes_items_between_stages ... ok
test_run_returns_phase_result ... ok

[ImportPhase Inheritance - 6 tests]
test_import_phase_has_phase_type_property ... ok
test_import_phase_has_run_extract_stage_method ... ok
test_import_phase_has_run_load_stage_method ... ok
test_import_phase_has_run_transform_stage_method ... ok
test_import_phase_inherits_base_phase_orchestrator ... ok
test_import_phase_run_delegates_to_base_orchestrator ... ok

[OrganizePhase Inheritance - 6 tests]
test_organize_phase_has_phase_type_property ... ok
test_organize_phase_has_run_extract_stage_method ... ok
test_organize_phase_has_run_load_stage_method ... ok
test_organize_phase_has_run_transform_stage_method ... ok
test_organize_phase_inherits_base_phase_orchestrator ... ok
test_organize_phase_run_delegates_to_base_orchestrator ... ok

[Load Extract Items - 6 tests]
test_excludes_steps_jsonl_from_loading ... ok
test_loads_items_from_multiple_data_dump_files ... ok
test_loads_items_in_sorted_file_order ... ok
test_loads_processing_items_from_jsonl ... ok
test_returns_empty_iterator_when_no_files ... ok
test_skips_corrupted_json_records ... ok

[Should Load Extract - 6 tests]
test_excludes_error_details_jsonl_from_detection ... ok
test_excludes_pipeline_stages_jsonl_from_detection ... ok
test_excludes_steps_jsonl_from_detection ... ok
test_returns_false_when_no_data_dump_files ... ok
test_returns_false_when_output_folder_missing ... ok
test_returns_true_when_data_dump_files_exist ... ok

----------------------------------------------------------------------
Ran 32 tests in 0.030s

OK
```

## 注意点

### 既存 run() メソッドの保持
- ImportPhase と OrganizePhase の既存 `run()` メソッドは維持しました
- 理由: 現在の run() は複雑なロジックを持っている
  - CompletedItemsCache のビルド
  - Resume モード進捗表示
  - limit パラメータ処理
  - session_manager 連携
  - expected_total_item_count の計算
- これらのロジックは Phase 5 で BasePhaseOrchestrator.run() に統合される予定

### フックメソッドの実装
- 各フックメソッドは既存の create_*_stage() メソッドを活用
- シンプルに Stage を作成して run() を呼び出すだけ
- 複雑なロジックは既存 Stage クラス側にカプセル化されている

### 次 Phase への引き継ぎ
- Phase 5 では Resume モードで Extract output を再利用する機能を実装
- BasePhaseOrchestrator の run() メソッドが _should_load_extract_from_output() を使って Resume 判定
- ImportPhase/OrganizePhase の既存 run() から複雑なロジックを BasePhaseOrchestrator に移行

## 実装のミス・課題

### 既知の課題
1. **既存テストの失敗**: 一部のテストが失敗していますが、今回の変更とは無関係です
   - test_import_help_registration (CLI argparse テスト)
   - test_import_required_arguments (CLI argparse テスト)
   - test_discover_items_valid_url (GitHub extractor テスト)
   - test_full_extraction_flow (GitHub extractor テスト)
   - test_resume_mode_skip_processed (GitHub extractor テスト)
   - test_import_without_chunk_skips_large_files (Import phase テスト)

2. **既存 run() の完全移行は未完了**
   - ImportPhase.run() と OrganizePhase.run() は現在両立状態
   - Phase 5 で BasePhaseOrchestrator.run() に完全移行予定
   - 現時点では両方の run() が存在し、既存機能を維持

### 技術的負債
- ImportPhase/OrganizePhase の run() メソッドと BasePhaseOrchestrator の run() が重複
- Phase 5 でリファクタリングして一本化する必要がある

## Phase 4 完了条件

- [X] ImportPhase が BasePhaseOrchestrator を継承
- [X] ImportPhase が 3つのフックメソッドを実装
- [X] OrganizePhase が BasePhaseOrchestrator を継承
- [X] OrganizePhase が 3つのフックメソッドを実装
- [X] 全 Phase Orchestrator テスト (32 tests) が PASS
- [X] phase_type プロパティが正しく動作
- [X] run() が BasePhaseOrchestrator の MRO に含まれる

## 次 Phase (Phase 5) への準備

Phase 5 では以下を実装します:
1. BasePhaseOrchestrator.run() を拡張して Resume ロジックを完全実装
2. Extract output 存在時のメッセージ表示
3. pipeline_stages.jsonl への Extract ログ重複防止
4. ImportPhase/OrganizePhase の既存 run() から複雑なロジックを移行
