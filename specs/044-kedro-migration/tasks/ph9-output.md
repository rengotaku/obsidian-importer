# Phase 9 Output

## 作業概要
- Phase 9 - US5 部分実行・DAG 可視化 の実装完了
- FAIL テスト 5 件を PASS させた
- Transform パイプラインのノード名から `_node` サフィックスを除去
- kedro-viz をインストールし、DAG 可視化機能を有効化

## 修正ファイル一覧

### 修正
- `src/obsidian_etl/pipelines/transform/pipeline.py` - ノード名修正
  - `extract_knowledge_node` → `extract_knowledge`
  - `generate_metadata_node` → `generate_metadata`
  - `format_markdown_node` → `format_markdown`

- `tests/test_pipeline_registry.py` - 期待ノード名修正
  - `expected_transform_nodes` リストを新ノード名に更新

### パッケージインストール
- `kedro-viz==12.3.0` - DAG 可視化ツール
  - 依存関係: fastapi, ipython, plotly, uvicorn, watchfiles, werkzeug 等
  - CLI コマンド: `kedro viz run` (DAG 可視化サーバー起動)
  - CLI コマンド: `kedro viz build` (静的 HTML ビルド)

## テスト結果

### Phase 9 テスト (tests/test_integration.py)

```
python -m unittest tests.test_integration
.....................
----------------------------------------------------------------------
Ran 22 tests in 0.469s

OK
```

全 22 テストメソッドが PASS:
- TestPipelineNodeNames: 4 テスト (import_claude, import_openai, import_github, uniqueness)
- TestPartialRunFromTo: 5 テスト (部分実行、from/to 指定、エラーハンドリング)
- TestE2EClaudeImport: 1 テスト (E2E 統合テスト)
- TestE2EOpenAIImport: 1 テスト (E2E 統合テスト)
- TestE2EGitHubImport: 1 テスト (E2E 統合テスト)
- TestResumeAfterFailure: 1 テスト (Resume テスト)
- TestIdempotentExtractClaude: 3 テスト (冪等性テスト)
- TestIdempotentTransform: 3 テスト (冪等性テスト)
- TestIdempotentOrganize: 3 テスト (冪等性テスト)

### 全 Kedro テスト

```
python -m unittest tests.pipelines.extract_claude.test_nodes tests.pipelines.extract_openai.test_nodes tests.pipelines.extract_github.test_nodes tests.pipelines.transform.test_nodes tests.pipelines.organize.test_nodes tests.test_hooks tests.test_pipeline_registry tests.test_integration
----------------------------------------------------------------------
Ran 178 tests in 0.505s

OK
```

全 178 Kedro 関連テストが PASS（リグレッションなし）。

## 実装の特徴

### ノード命名規則

全パイプラインで統一:
- ノード名 = 関数名
- `_node` サフィックスなし
- 各パイプライン内でユニーク
- DAG 可視化で読みやすい

### 部分実行機能

Kedro 標準機能により実現:
- `kedro run --from-nodes=extract_knowledge --to-nodes=format_markdown`
- `kedro run --from-nodes=classify_genre`
- `kedro run --to-nodes=parse_claude_json`

### DAG 可視化

kedro-viz により実現:
- `kedro viz run` - ローカルサーバー起動（デフォルト: http://localhost:4141）
- `kedro viz build` - 静的 HTML 生成（`build/` ディレクトリ）
- ノード依存関係、データセット入出力、実行時間等を可視化

### 検証したノード名

| Pipeline | Node Names |
|----------|-----------|
| import_claude | parse_claude_json, extract_knowledge, generate_metadata, format_markdown, classify_genre, normalize_frontmatter, clean_content, determine_vault_path, move_to_vault |
| import_openai | parse_chatgpt_zip, extract_knowledge, generate_metadata, format_markdown, classify_genre, normalize_frontmatter, clean_content, determine_vault_path, move_to_vault |
| import_github | clone_github_repo, parse_jekyll, convert_frontmatter, extract_knowledge, generate_metadata, format_markdown, classify_genre, normalize_frontmatter, clean_content, determine_vault_path, move_to_vault |

## 注意点

### headless 環境での kedro viz

- CLI ヘルプ (`kedro viz --help`) は確認済み
- GUI 起動 (`kedro viz run`) は headless 環境では確認不可
- 本番環境では Web ブラウザで http://localhost:4141 にアクセス可能

### Transform パイプラインの命名ミス

- 初期実装で `_node` サフィックスが誤って追加されていた
- 他パイプライン（Extract, Organize）は最初から正しい命名
- テスト駆動により早期発見・修正

### テストカバレッジ

- ノード名の検証: test_import_*_node_names
- 部分実行: test_partial_run_*
- DAG 構造: テスト内で SequentialRunner により間接的に検証
- パイプライン登録: test_pipeline_registry

## 次 Phase への引き継ぎ

Phase 10 (Polish & Cross-Cutting Concerns) へ:
- 全 User Story (US1-US5) 実装完了
- TDD サイクル (RED → GREEN) 完了
- 旧コード (`src/etl/`) 削除が次タスク
- ドキュメント更新（CLAUDE.md, pyproject.toml）が次タスク
- E2E 実データ検証が次タスク

## 実装のミス・課題

なし。全テスト PASS、ノード命名規則統一完了。
