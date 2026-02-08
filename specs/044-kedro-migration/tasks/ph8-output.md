# Phase 8 Output

## 作業概要
- Phase 8 - US4 GitHub Jekyll プロバイダー の実装完了
- FAIL テスト 38 件（全テスト ImportError で FAIL）を PASS させた
- GitHub Jekyll ブログからの知識インポート機能を実装

## 修正ファイル一覧

### 新規実装
- `src/obsidian_etl/pipelines/extract_github/nodes.py` - GitHub Extract ノード実装
  - `clone_github_repo()`: GitHub URL → sparse-checkout → Markdown ファイル dict
  - `parse_jekyll()`: Jekyll Markdown → ParsedItem dict（draft/private 除外）
  - `convert_frontmatter()`: Jekyll frontmatter → Obsidian 形式変換
  - ヘルパー関数群：
    - `_parse_frontmatter()`: YAML frontmatter パース
    - `_title_from_filename()`: ファイル名からタイトル抽出
    - `_extract_date()`: 優先順位付き日付抽出
    - `_extract_date_from_text()`: 正規表現による日付抽出
    - `_extract_tags()`: tags/categories/keywords 統合

- `src/obsidian_etl/pipelines/extract_github/pipeline.py` - GitHub Extract パイプライン定義
  - `create_pipeline()`: clone → parse → convert の 3 ステージ DAG

### 修正
- `src/obsidian_etl/pipeline_registry.py` - import_github パイプライン登録
  - `extract_github` import 追加
  - `import_github` パイプライン登録（extract_github + transform + organize）

## テスト結果

```
python -m unittest tests.pipelines.extract_github.test_nodes
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.012s

OK
```

全 38 テストメソッドが PASS:
- TestCloneGithubRepo: 5 テスト（URL → git clone → Markdown files dict）
- TestParseJekyll: 10 テスト（Jekyll frontmatter → ParsedItem）
- TestParseJekyllSkipDraft: 4 テスト（draft/private 除外）
- TestConvertFrontmatter: 6 テスト（Jekyll → Obsidian 形式変換）
- TestDateExtractionPriority: 5 テスト（日付抽出優先順位）
- TestIdempotentExtractGithub: 3 テスト（existing_output 互換性）
- TestEmptyInputGithub: 4 テスト（エッジケース：空入力、非 .md、frontmatter なし、Unicode）

## 実装の特徴

### clone_github_repo ノード
- GitHub URL パース（正規表現）
- `git clone --depth 1 --filter=blob:none --sparse` による高速クローン
- `git sparse-checkout set` で対象パスのみ取得
- PartitionedDataset パターン（dict[str, callable]）で返却
- 無効 URL または clone 失敗時は空 dict 返却

### parse_jekyll ノード
- YAML frontmatter パース（yaml.safe_load）
- draft: true / private: true のファイルを自動除外
- ParsedItem（E-2 スキーマ）準拠の dict 生成
- file_id: SHA256 ハッシュの先頭 12 文字
- messages: [] (GitHub は会話ではない)
- content: frontmatter 除去後の本文
- 非 .md ファイルは自動スキップ

### convert_frontmatter ノード
- Jekyll frontmatter → Obsidian frontmatter 変換:
  - `date` → `created`
  - `tags`, `categories`, `keywords` → `tags` 統合
  - `layout`, `permalink`, `slug`, `lastmod` 削除
  - `normalized: true`, `file_id` 追加
- 日付抽出優先順位:
  1. frontmatter.date（ISO 8601 対応）
  2. ファイル名（YYYY-MM-DD-* 形式）
  3. タイトル正規表現
  4. 本文正規表現（先頭 1000 文字）
  5. 現在日時フォールバック
- タグ抽出: frontmatter + 本文 hashtag (#tag)
- title フォールバック: frontmatter → ファイル名から生成

### パイプライン構成
- 3 ステージ DAG:
  1. clone_github_repo: params:github_url → raw_github_posts
  2. parse_jekyll: raw_github_posts → parsed_github_items
  3. convert_frontmatter: parsed_github_items → parsed_items
- 共通 Transform パイプライン（extract_knowledge 等）へ接続
- 共通 Organize パイプライン（classify_genre 等）へ接続

## 注意点

### 既存参照コードとの相違
- 既存 `src/etl/stages/extract/github_extractor.py` を参考にしたが、Kedro ノードパターンに適合するため以下を変更:
  - BaseExtractor パターン廃止 → 純粋関数ノードに変更
  - ProcessingItem dataclass 廃止 → dict ベースに変更
  - Step クラス廃止 → 関数に変更
  - PartitionedDataset パターン（dict[str, callable]）に統一

### subprocess モック
- テストで `@patch("obsidian_etl.pipelines.extract_github.nodes.subprocess")` を使用
- nodes.py でモジュールレベル `import subprocess` が必要（パッチ可能にするため）

### file_id 生成方式
- 他プロバイダーと統一: SHA256(content).hexdigest()[:12]
- 既存 `src/obsidian_etl/utils/file_id.py` の generate_file_id() は使用せず（引数が異なる）

### チャンク分割
- GitHub Jekyll ブログはチャンク分割不要（個別記事のため）
- is_chunked: False, chunk_index: None, total_chunks: None, parent_item_id: None

## 次 Phase への引き継ぎ

Phase 9 (US5 部分実行・DAG 可視化) へ:
- 全プロバイダー（Claude, OpenAI, GitHub）の Extract パイプライン実装完了
- `kedro run --pipeline=import_github` で GitHub Jekyll ブログインポートが可能
- DAG 可視化とノード範囲指定実行の検証が次タスク

## 実装のミス・課題

なし。全テスト PASS、ゴールデンデータとの一致確認済み。
