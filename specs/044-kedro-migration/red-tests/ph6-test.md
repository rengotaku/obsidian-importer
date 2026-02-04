# Phase 6 RED Tests

## サマリー
- Phase: Phase 6 - US2 冪等 Resume
- FAIL テスト数: 8 (7 ERROR + 1 FAIL)
- PASS テスト数: 3 (後方互換性テスト)
- テストファイル:
  - tests/pipelines/extract_claude/test_nodes.py (TestIdempotentExtract: 4 tests)
  - tests/pipelines/transform/test_nodes.py (TestIdempotentTransform: 3 tests)
  - tests/pipelines/organize/test_nodes.py (TestIdempotentOrganize: 3 tests)
  - tests/test_integration.py (TestResumeAfterFailure: 1 test)

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/extract_claude/test_nodes.py | test_idempotent_extract_skips_existing | existing_output に存在する file_id のアイテムをスキップ |
| tests/pipelines/extract_claude/test_nodes.py | test_idempotent_extract_all_existing_returns_empty | 全アイテムが既存の場合、空 dict を返す |
| tests/pipelines/extract_claude/test_nodes.py | test_idempotent_extract_empty_existing_processes_all | existing_output が空の場合、全アイテムを処理 |
| tests/pipelines/transform/test_nodes.py | test_idempotent_transform_skips_existing | existing_output にあるアイテムは LLM 呼び出しなしでスキップ |
| tests/pipelines/transform/test_nodes.py | test_idempotent_transform_all_existing_no_llm_call | 全アイテムが既存の場合、LLM が一切呼ばれない |
| tests/pipelines/organize/test_nodes.py | test_idempotent_organize_skips_existing | existing_output にあるアイテムはスキップされ、新規のみ分類 |
| tests/pipelines/organize/test_nodes.py | test_idempotent_organize_all_existing_returns_empty | 全アイテムが既に分類済みの場合、空 dict を返す |
| tests/test_integration.py | test_resume_after_failure | 1回目で一部失敗、2回目で失敗分のみ再処理 |

## PASS テスト（後方互換性）

| テストファイル | テストメソッド | 確認内容 |
|---------------|---------------|---------|
| tests/pipelines/extract_claude/test_nodes.py | test_idempotent_extract_no_existing_output_arg | existing_output 引数なしで全アイテム処理 |
| tests/pipelines/transform/test_nodes.py | test_idempotent_transform_no_existing_output_processes_all | existing_output 引数なしで全アイテム LLM 処理 |
| tests/pipelines/organize/test_nodes.py | test_idempotent_organize_no_existing_output_processes_all | existing_output 引数なしで全アイテム分類 |

## 実装ヒント

### parse_claude_json (Extract)
- `src/obsidian_etl/pipelines/extract_claude/nodes.py` の `parse_claude_json` に `existing_output: dict[str, Callable] | None = None` 引数を追加
- ループ内で `file_id` が `existing_output` のキーに存在する場合はスキップ
- `existing_output` が None の場合は従来通り全アイテム処理（後方互換性）

### extract_knowledge (Transform)
- `src/obsidian_etl/pipelines/transform/nodes.py` の `extract_knowledge` に `existing_output: dict[str, Callable] | None = None` 引数を追加
- ループ内で `partition_id` が `existing_output` のキーに存在する場合はスキップ（LLM 呼び出し回避）
- `existing_output` が None の場合は従来通り全アイテム処理（後方互換性）

### classify_genre (Organize)
- `src/obsidian_etl/pipelines/organize/nodes.py` の `classify_genre` に `existing_output: dict[str, Callable] | None = None` 引数を追加
- ループ内で `key` が `existing_output` のキーに存在する場合はスキップ

### E2E Resume テスト
- `PartitionedMemoryDataset` が2回目の `runner.run()` で既存データを保持していることが前提
- ノードが `existing_output` を受け取るように pipeline.py の Node 定義も更新が必要
- catalog に各ノードの出力データセットを `existing_output` として入力に追加する設計が必要

## FAIL 出力例

```
ERROR: test_idempotent_extract_skips_existing (tests.pipelines.extract_claude.test_nodes.TestIdempotentExtract)
TypeError: parse_claude_json() got an unexpected keyword argument 'existing_output'

ERROR: test_idempotent_transform_skips_existing (tests.pipelines.transform.test_nodes.TestIdempotentTransform)
TypeError: extract_knowledge() got an unexpected keyword argument 'existing_output'

ERROR: test_idempotent_organize_skips_existing (tests.pipelines.organize.test_nodes.TestIdempotentOrganize)
TypeError: classify_genre() got an unexpected keyword argument 'existing_output'

FAIL: test_resume_after_failure (tests.test_integration.TestResumeAfterFailure)
AssertionError: 3 != 1 : Second run should only call LLM for the 1 failed item
```

## 既存テストへの影響

既存 72 テストは全て PASS（リグレッションなし）。
