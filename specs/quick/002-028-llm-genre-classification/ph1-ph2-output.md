# Phase 1 & Phase 2 Output: LLM Genre Classification

## 作業概要
- Phase 1 (Implementation) と Phase 2 (Pipeline Update & Cleanup) の実装完了
- Keyword-based genre classification → LLM-based classification への移行
- 2つのノード (`classify_genre`, `extract_topic`) を1つ (`extract_topic_and_genre`) に統合

## 修正ファイル一覧

### 実装ファイル
1. **`src/obsidian_etl/pipelines/organize/nodes.py`** - 主要な変更
   - **追加**: `extract_topic_and_genre()` 関数 - LLM で topic + genre を同時抽出
   - **追加**: `_extract_topic_and_genre_via_llm()` ヘルパー関数 - JSON レスポンス処理
   - **削除**: `classify_genre()` 関数 - keyword-based 分類（旧実装）
   - **削除**: `extract_topic()` 関数 - topic 専用抽出（旧実装）
   - **保持**: `_extract_topic_via_llm()` - 将来の参照用に保持
   - **更新**: モジュール docstring - 新しいノード構成を反映

2. **`src/obsidian_etl/pipelines/organize/pipeline.py`** - パイプライン定義
   - **変更前**: `classify_genre` → `extract_topic` → `normalize` → `clean` → `embed`
   - **変更後**: `extract_topic_and_genre` → `normalize` → `clean` → `embed`
   - **削除**: `classify_genre`, `extract_topic` ノード
   - **追加**: `extract_topic_and_genre` ノード
   - **更新**: モジュール docstring

3. **`conf/base/parameters.yml`** - Ollama 設定
   - **追加**: `ollama.functions.extract_topic_and_genre` セクション
     ```yaml
     extract_topic_and_genre:
       num_predict: 128
       timeout: 30
     ```

### テストファイル（部分更新）
4. **`tests/test_integration.py`** - 統合テスト
   - **更新**: `test_import_claude_node_names` - ノード名期待値を更新
   - **更新**: `test_import_openai_node_names` - ノード名期待値を更新
   - **更新**: `test_import_github_node_names` - ノード名期待値を更新

5. **`tests/test_pipeline_registry.py`** - パイプライン登録テスト
   - **更新**: `test_import_claude_contains_organize_nodes` - ノード名期待値を更新

## 実装の詳細

### `extract_topic_and_genre()` の仕様
- **入力**: `partitioned_input` (dict of callables), `params` (Ollama 設定)
- **出力**: dict[str, dict] - 各アイテムに `topic` と `genre` フィールド追加
- **処理フロー**:
  1. Markdown frontmatter をパース
  2. 本文（body）を抽出（frontmatter 除外）
  3. LLM API 呼び出し（`_extract_topic_and_genre_via_llm`）
  4. JSON レスポンスをパース
  5. `topic` を lowercase に正規化
  6. `genre` をバリデーション（11カテゴリのいずれか）

### LLM プロンプト設計
- **System prompt**: ジャンル定義（11カテゴリ）+ 出力フォーマット（JSON）を明示
- **User message**: 本文の最初 1000文字を入力
- **期待レスポンス**: `{"topic": "主題", "genre": "ジャンル"}`
- **フォールバック**: JSON パースエラー時は `("", "other")` を返す

### ジャンル定義（11カテゴリ）
- `ai`, `devops`, `engineer`, `economy`, `business`, `health`, `parenting`, `travel`, `lifestyle`, `daily`, `other`

## 注意点

### テスト失敗（Phase 3 で解決予定）
**現状**: 6件のテストが失敗している
- **原因**: `tests/pipelines/organize/test_nodes.py` が旧関数 (`classify_genre`, `extract_topic`) をインポート・使用
- **影響範囲**:
  - `TestClassifyGenre` クラス（約30テスト） - keyword-based 分類のテスト
  - `TestExtractTopic` クラス（約5テスト） - topic 専用抽出のテスト
  - `TestIdempotentOrganize` クラス（約5テスト） - idempotent 処理のテスト

**対応方針**（Phase 3）:
1. `tests/pipelines/organize/test_nodes.py` を全面書き換え
   - `classify_genre` → `extract_topic_and_genre` の mock テストに置き換え
   - `extract_topic` テストを削除（統合されたため）
   - `TestIdempotentOrganize` を削除（LLM は毎回実行のため不要）
2. LLM mock 戦略:
   - `_extract_topic_and_genre_via_llm` を patch
   - JSON レスポンス形式をテスト
   - エラーハンドリング（JSON パース失敗、不正なジャンル）をテスト

### 破壊的変更
- **Idempotent 機能削除**: `classify_genre` の `existing_output` パラメータを削除
  - **理由**: LLM は毎回実行するため、既存出力のスキップ機能は不要
  - **影響**: `existing_classified_items` データセットは不要になる
- **ノード数削減**: 2ノード → 1ノード（パイプライン簡素化）
  - **メリット**: LLM 呼び出し1回で済む（効率化）
  - **デメリット**: genre と topic を別々に取得できない（統合されている）

### データフロー変更
**変更前**:
```
markdown_notes → classify_genre → classified_items
              → extract_topic → topic_extracted_items
              → normalize → ...
```

**変更後**:
```
markdown_notes → extract_topic_and_genre → classified_items
              → normalize → ...
```

## 次 Phase への引き継ぎ

### Phase 3: Test Updates（未実施）
- `tests/pipelines/organize/test_nodes.py` の全面書き換えが必要
- 作業規模: 約100テストケースの削除・書き換え
- 推定時間: 2-3時間

### E2E テストの動作確認
- ゴールデンファイル比較テストは既存のまま動作するはず
- LLM の出力が安定していれば、genre/topic の内容が変わる可能性あり
- **推奨**: Phase 3 完了後に `make test-e2e` で確認

## 実装のミス・課題

### 1. LLM レスポンスの安定性
- **問題**: LLM が常に有効な JSON を返す保証はない
- **対策**: JSON パースエラー時のフォールバック実装済み (`("", "other")`)
- **懸念**: フォールバックが頻繁に発生する可能性

### 2. プロンプトの日本語依存
- **問題**: プロンプトが日本語のみ（英語コンテンツで性能低下の可能性）
- **対策**: 現時点では日本語コンテンツを想定しているため問題なし
- **改善案**: 将来的に多言語対応が必要な場合は、プロンプトを英語化

### 3. `_extract_topic_via_llm` の保持
- **理由**: Plan で「残す」と指定されている
- **用途不明**: 実際には使用されていない（デッドコード化）
- **推奨**: 今後削除するか、用途を明確にする

### 4. パラメータ設定の重複
- **問題**: `extract_topic` と `extract_topic_and_genre` で設定が分かれている
- **影響**: `extract_topic` の設定は不要（使用されていない）
- **推奨**: Phase 3 で `extract_topic` の設定を削除

## 成果物の確認

### 実装完了
- [x] `extract_topic_and_genre` 関数実装
- [x] `_extract_topic_and_genre_via_llm` ヘルパー実装
- [x] `ollama.functions.extract_topic_and_genre` 設定追加
- [x] パイプライン定義更新
- [x] 旧関数削除 (`classify_genre`, `extract_topic`)
- [x] 統合テストのノード名期待値更新

### 未完了（Phase 3）
- [ ] `tests/pipelines/organize/test_nodes.py` の書き換え
- [ ] テスト PASS 確認 (`make test`)
- [ ] カバレッジ確認 (`make coverage`)
- [ ] E2E テスト動作確認 (`make test-e2e`)

## 推奨事項

### Phase 3 実施前の検討
1. **LLM mock 戦略の決定**:
   - `_extract_topic_and_genre_via_llm` を patch する方法
   - JSON レスポンス形式のテストケース設計
   - エラーハンドリングのテスト網羅性

2. **既存テストの削除vs書き換え**:
   - `TestClassifyGenre` は全削除して新規作成が効率的
   - `TestIdempotentOrganize` は削除（機能自体が不要）
   - `TestExtractTopic` は削除（統合されたため）

3. **ゴールデンファイルの再生成**:
   - LLM の出力が変わる可能性がある
   - Phase 3 完了後にゴールデンファイルを再生成することを推奨

### パフォーマンス最適化
- **並列化**: 複数アイテムの LLM 呼び出しを並列実行（将来の改善）
- **キャッシュ**: 同一コンテンツの再分類を避けるため、キャッシュ機構を検討

### ドキュメント更新
- `CLAUDE.md` のジャンル分類ルール更新（keyword-based → LLM-based）
- README の機能説明更新
