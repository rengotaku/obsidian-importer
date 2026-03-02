# Phase 5 RED Tests

## サマリー
- Phase: Phase 5 - パーティション処理での file_id 設定
- FAIL テスト数: 7
- テストファイル: tests/pipelines/transform/test_nodes.py, tests/pipelines/organize/test_nodes.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/transform/test_nodes.py | test_set_file_id_called_for_each_partition | 各パーティションに対して set_file_id が呼ばれる |
| tests/pipelines/transform/test_nodes.py | test_set_file_id_called_before_llm | set_file_id が LLM 呼び出しの前に呼ばれる |
| tests/pipelines/transform/test_nodes.py | test_set_file_id_called_even_on_llm_failure | LLM 失敗時でも set_file_id は呼ばれる |
| tests/pipelines/organize/test_nodes.py | test_set_file_id_called_for_each_partition | 各パーティションに対して set_file_id が呼ばれる |
| tests/pipelines/organize/test_nodes.py | test_set_file_id_called_before_llm | set_file_id が LLM 呼び出しの前に呼ばれる |
| tests/pipelines/organize/test_nodes.py | test_set_file_id_uses_metadata_file_id | metadata の file_id が set_file_id に渡される |
| tests/pipelines/organize/test_nodes.py | test_set_file_id_fallback_to_key | file_id がない場合 partition key にフォールバック |

## 実装ヒント

### transform/nodes.py
- `from obsidian_etl.utils.log_context import set_file_id` をインポート
- `extract_knowledge` のパーティションループ (`for partition_id, load_func in to_process:`) の先頭で `set_file_id(partition_id)` を呼び出す

### organize/nodes.py
- `from obsidian_etl.utils.log_context import set_file_id` をインポート
- `extract_topic_and_genre` のパーティションループ (`for key, load_func in partitioned_input.items():`) 内で、`file_id` 取得後に `set_file_id(file_id)` を呼び出す
- file_id は `metadata.get("file_id") or key` で取得（既存ロジック）

## FAIL 出力例
```
ERROR: test_set_file_id_called_for_each_partition (tests.pipelines.transform.test_nodes.TestExtractKnowledgeFileIdContext)
AttributeError: <module 'obsidian_etl.pipelines.transform.nodes'> does not have the attribute 'set_file_id'

ERROR: test_set_file_id_called_for_each_partition (tests.pipelines.organize.test_nodes.TestExtractTopicAndGenreFileIdContext)
AttributeError: <module 'obsidian_etl.pipelines.organize.nodes'> does not have the attribute 'set_file_id'
```
