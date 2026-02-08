# Phase 3 RED Tests

## Summary
- Phase: Phase 3 - GitHub Jekyll ブログのインポート (US3)
- FAIL テスト数: 5
- テストファイル: `tests/pipelines/extract_github/test_nodes.py`

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/extract_github/test_nodes.py | TestGitHubMemoryDatasetFlow.test_raw_github_posts_not_in_catalog | raw_github_posts がカタログに定義されていないこと |
| tests/pipelines/extract_github/test_nodes.py | TestGitHubMemoryDatasetFlow.test_github_pipeline_no_catalog_dependency_for_intermediate | 中間データセットがカタログに依存しないこと |
| tests/pipelines/extract_github/test_nodes.py | TestGitHubUrlParameter.test_github_url_in_parameters_yml | parameters.yml に github_url がフラットキーとして存在すること |
| tests/pipelines/extract_github/test_nodes.py | TestGitHubUrlParameter.test_github_clone_dir_in_parameters_yml | parameters.yml に github_clone_dir がフラットキーとして存在すること |
| tests/pipelines/extract_github/test_nodes.py | TestGitHubUrlParameter.test_pipeline_clone_node_does_not_use_params_parameters | clone_github_repo が params:parameters を使わないこと |

## PASS テスト (既存テスト維持)

| テストメソッド | 状態 |
|---------------|------|
| TestGitHubMemoryDatasetFlow.test_github_pipeline_outputs_raw_github_posts_as_memory | PASS (パイプライン構造テスト、既に接続あり) |
| TestGitHubUrlParameter.test_pipeline_uses_params_github_url_input | PASS (現在の pipeline.py で既に params:github_url が入力に含まれている) |
| 既存 39 テスト (TestCloneGithubRepo, TestParseJekyll, etc.) | 全て PASS |

## 実装ヒント

1. `conf/base/catalog.yml` から `raw_github_posts` エントリを削除
   - clone_github_repo は dict[str, Callable] を返すため、MemoryDataset（Kedro 自動生成）で十分
2. `conf/base/parameters.yml` にフラットキーを追加:
   ```yaml
   github_url: ""
   github_clone_dir: ""
   ```
3. `src/obsidian_etl/pipelines/extract_github/pipeline.py` の clone_github_repo ノード入力から `params:parameters` を除去し、`params:github_clone_dir` に変更

## FAIL 出力例

```
FAIL: test_raw_github_posts_not_in_catalog (tests.pipelines.extract_github.test_nodes.TestGitHubMemoryDatasetFlow)
AssertionError: 'raw_github_posts' unexpectedly found in catalog.yml.
raw_github_posts should NOT be in catalog.yml. clone_github_repo returns dict[str, Callable] in memory,
so it should use MemoryDataset (auto-created by Kedro).

FAIL: test_github_url_in_parameters_yml (tests.pipelines.extract_github.test_nodes.TestGitHubUrlParameter)
AssertionError: 'github_url' not found in {'import': {...}, 'organize': {...}}
parameters.yml should have 'github_url' as a flat key (not nested under 'import').

FAIL: test_github_clone_dir_in_parameters_yml (tests.pipelines.extract_github.test_nodes.TestGitHubUrlParameter)
AssertionError: 'github_clone_dir' not found in {'import': {...}, 'organize': {...}}
parameters.yml should have 'github_clone_dir' as a flat key.

FAIL: test_pipeline_clone_node_does_not_use_params_parameters (tests.pipelines.extract_github.test_nodes.TestGitHubUrlParameter)
AssertionError: 'params:parameters' unexpectedly found in {'params:parameters', 'params:github_url'}
clone_github_repo should NOT use 'params:parameters'. Use explicit params:github_url and params:github_clone_dir instead.
```

## テスト全体結果

```
Ran 279 tests in 0.691s
FAILED (failures=8, errors=22)

内訳:
- 新規 Phase 3 FAIL: 5 (上記テーブル)
- 既存 RAG FAIL: 3 (pre-existing, 無関係)
- 既存 RAG ERROR: 22 (pre-existing, 無関係)
- PASS: 249 (既存 247 + 新規 2)
```
