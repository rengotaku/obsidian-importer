# Tasks: 002-028 LLM Genre Classification

## Phase 1: Implementation

- [x] T001: Create `extract_topic_and_genre` function in `nodes.py`
  - LLM 1回の呼び出しで topic と genre を JSON で取得
  - プロンプトにジャンル定義（11カテゴリ）を埋め込む
  - JSON 解析 + フォールバック
  - ファイル: `src/obsidian_etl/pipelines/organize/nodes.py`

- [x] T002: Add ollama configuration in `parameters.yml`
  - `ollama.functions.extract_topic_and_genre` セクション追加
  - `num_predict: 128`, `timeout: 30` 設定
  - ファイル: `conf/base/parameters.yml`

## Phase 2: Pipeline Update & Cleanup

- [x] T003: Update `pipeline.py` node definitions
  - `classify_genre` ノードを `extract_topic_and_genre` に置換
  - `extract_topic` ノード削除
  - ファイル: `src/obsidian_etl/pipelines/organize/pipeline.py`

- [x] T004: Remove old functions from `nodes.py`
  - `classify_genre` 関数削除
  - `extract_topic` 関数削除
  - `_extract_topic_via_llm` は保持（将来の参照用）
  - ファイル: `src/obsidian_etl/pipelines/organize/nodes.py`

## Phase 3: Parameter Cleanup

- [x] T005: Remove `genre_keywords` from `conf/base/parameters.yml`
  - `genre_keywords` セクション削除（88-157行）
  - `genre_priority` も削除

- [x] T006: Remove `genre_keywords` from `conf/base/parameters_organize.local.yml.example`
  - `genre_keywords` と `genre_priority` を削除

## Phase 4: Test Updates

- [x] T007: Update `tests/pipelines/organize/test_nodes.py`
  - 旧テストクラス削除: `TestClassifyGenre`, `TestExtractTopic`, `TestIdempotentOrganize`
  - 新規テストクラス作成: `TestExtractTopicAndGenre`
  - LLM mock を使用（`_extract_topic_and_genre_via_llm` をモック）
  - Ollama config テストクラス更新: `TestExtractTopicAndGenreUsesOllamaConfig`

- [x] T008: Run all tests and verify
  - `make test` ですべてのテストが PASS することを確認
  - `make coverage` でカバレッジ ≥80% を確認
  - 結果: 370 tests OK, coverage 80%

## Notes

### 既知の問題
- **Test failures**: 古いノード名を参照しているテストが失敗（Phase 3 で解決予定）
  - `tests/test_integration.py`: ノード名期待値は更新済み
  - `tests/test_pipeline_registry.py`: ノード名期待値は更新済み
  - `tests/pipelines/organize/test_nodes.py`: 大規模なテスト書き換えが必要

### 実装の変更点
- **Keyword-based → LLM-based**: ジャンル分類がキーワードマッチングから LLM 推論に変更
- **Single API call**: topic と genre を1回の LLM 呼び出しで取得（効率化）
- **JSON response**: LLM レスポンスを JSON でパース（構造化出力）
- **Idempotent 削除**: LLM は毎回実行するため、既存出力のスキップ機能は不要

### 次の作業
Phase 3 のテスト更新を実行する前に、LLM mock 戦略を確認する必要がある:
1. `extract_topic_and_genre` の unit test を作成
2. 既存の `TestClassifyGenre` を LLM mock ベースに書き換え
3. Idempotent テストを削除
4. `make test` で全テスト PASS を確認
