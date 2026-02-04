# Phase 9 RED Tests

## サマリー
- Phase: Phase 9 - US5 部分実行・DAG 可視化
- FAIL テスト数: 5 (FAIL: 3, ERROR: 2)
- テストファイル: tests/test_integration.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/test_integration.py | TestPipelineNodeNames.test_import_claude_node_names | import_claude の全ノード名が期待値と一致する |
| tests/test_integration.py | TestPipelineNodeNames.test_import_openai_node_names | import_openai の全ノード名が期待値と一致する |
| tests/test_integration.py | TestPipelineNodeNames.test_import_github_node_names | import_github の全ノード名が期待値と一致する |
| tests/test_integration.py | TestPartialRunFromTo.test_partial_run_transform_only | from_nodes=extract_knowledge, to_nodes=format_markdown で Transform のみ実行 |
| tests/test_integration.py | TestPartialRunFromTo.test_from_nodes_to_nodes_subset_node_count | 部分パイプラインのノード数が元より少ない（Transform = 3 ノード） |

## PASS テスト（既に正しく動作するもの）

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/test_integration.py | TestPipelineNodeNames.test_all_node_names_are_unique_within_pipeline | 各パイプライン内でノード名が重複しない |
| tests/test_integration.py | TestPartialRunFromTo.test_partial_run_organize_only | from_nodes=classify_genre で Organize のみ実行 |
| tests/test_integration.py | TestPartialRunFromTo.test_partial_run_invalid_node_raises_error | 存在しないノード名で ValueError 発生 |

## 根本原因

Transform パイプライン (`src/obsidian_etl/pipelines/transform/pipeline.py`) のノード名に `_node` サフィックスが付いている:

- `extract_knowledge_node` (期待: `extract_knowledge`)
- `generate_metadata_node` (期待: `generate_metadata`)
- `format_markdown_node` (期待: `format_markdown`)

他パイプライン（Extract, Organize）のノード名は関数名と一致しており問題なし。

## 実装ヒント

- `src/obsidian_etl/pipelines/transform/pipeline.py` のノード名から `_node` サフィックスを除去:
  - `name="extract_knowledge_node"` -> `name="extract_knowledge"`
  - `name="generate_metadata_node"` -> `name="generate_metadata"`
  - `name="format_markdown_node"` -> `name="format_markdown"`
- 変更後、全 5 テストが PASS するはず

## FAIL 出力例

```
FAIL: test_import_claude_node_names (test_integration.TestPipelineNodeNames.test_import_claude_node_names)
import_claude パイプラインのノード名が正しいこと。
----------------------------------------------------------------------
AssertionError: Items in the first set but not the second:
'extract_knowledge_node'
'format_markdown_node'
'generate_metadata_node'
Items in the second set but not the first:
'generate_metadata'
'format_markdown'
'extract_knowledge' : import_claude node names mismatch.
Expected: ['classify_genre', 'clean_content', 'determine_vault_path', 'extract_knowledge', 'format_markdown', 'generate_metadata', 'move_to_vault', 'normalize_frontmatter', 'parse_claude_json']
Actual:   ['classify_genre', 'clean_content', 'determine_vault_path', 'extract_knowledge_node', 'format_markdown_node', 'generate_metadata_node', 'move_to_vault', 'normalize_frontmatter', 'parse_claude_json']
```

```
ERROR: test_partial_run_transform_only (tests.test_integration.TestPartialRunFromTo.test_partial_run_transform_only)
----------------------------------------------------------------------
ValueError: Pipeline does not contain nodes named ['extract_knowledge'].
```
