# Phase 3 Output

## 作業概要
- User Story 3 (GitHub Jekyll ブログのインポート) の実装完了
- FAIL テスト 5 件を PASS させた（GitHub パイプライン関連）
- 既存テスト（254個、RAG以外）も全て PASS を維持（レグレッションなし）

## 修正ファイル一覧
- `conf/base/catalog.yml` - raw_github_posts エントリを削除
  - clone_github_repo は dict[str, Callable] をメモリで返すため、MemoryDataset（Kedro 自動生成）を使用
  - カタログに PartitionedDataset として定義すると型不一致が発生するため削除
- `conf/base/parameters.yml` - github_url と github_clone_dir をフラットキーとして追加
  - 明示的なパラメータ参照（params:github_url, params:github_clone_dir）を可能にする
  - params:parameters アンチパターンを回避
- `src/obsidian_etl/pipelines/extract_github/pipeline.py` - clone_github_repo ノードの入力を変更
  - Before: inputs=["params:github_url", "params:parameters"]
  - After: inputs=["params:github_url", "params:github_clone_dir"]
- `src/obsidian_etl/pipelines/extract_github/nodes.py` - clone_github_repo 関数シグネチャを変更
  - Before: def clone_github_repo(url: str, params: dict) -> dict[str, callable]
  - After: def clone_github_repo(url: str, github_clone_dir: str) -> dict[str, callable]
  - 空文字列の場合は tempfile.mkdtemp() を使用（システム一時ディレクトリ）
- `tests/pipelines/extract_github/test_nodes.py` - 既存テストを新しいシグネチャに更新
  - clone_github_repo(url, {"github_clone_dir": tmpdir}) → clone_github_repo(url, tmpdir)
  - clone_github_repo(url, {}) → clone_github_repo(url, "")

## 注意点
- GitHub パイプラインの raw_github_posts と parsed_github_items はともに MemoryDataset で接続
  - カタログ定義は不要（Kedro が自動的に MemoryDataset を作成）
- github_url と github_clone_dir はトップレベルのフラットキーとして定義
  - import.github_url のようなネスト構造ではなく、github_url として直接アクセス可能
- clone_github_repo の第2引数が params dict から github_clone_dir string に変更
  - 既存のユニットテストも全て更新済み

## テスト結果
- 全テスト数: 279
- PASS: 254 (RAG 以外すべて)
- FAIL: 3 (RAG のみ、既知の失敗、本フィーチャーとは無関係)
- ERROR: 22 (RAG のみ、既知の失敗、本フィーチャーとは無関係)
- Phase 3 で修正した 5 テスト: 全て PASS
  - test_raw_github_posts_not_in_catalog
  - test_github_pipeline_no_catalog_dependency_for_intermediate
  - test_github_url_in_parameters_yml
  - test_github_clone_dir_in_parameters_yml
  - test_pipeline_clone_node_does_not_use_params_parameters
- 既存の GitHub extract テスト (49 テスト): 全て PASS
- 既存のパイプラインテスト (186 テスト): 全て PASS
- 統合テスト (10 テスト): 全て PASS

## 次 Phase への引き継ぎ
- US3 (GitHub Jekyll ブログのインポート) は完了
- US1 (dispatch 型パイプライン) の実装が次 Phase (Phase 4)
- pipeline_registry.py を dispatch 型に変更し、import.provider で振り分ける設計を実装
- 統合テストを ZIP 入力対応に更新

## 実装のミス・課題
- なし。全ての RED テストが GREEN になり、既存テストも全て維持された。
