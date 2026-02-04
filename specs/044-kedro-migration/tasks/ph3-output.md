# Phase 3 Output

## 作業概要
- Phase 3 - US1 Transform パイプラインの実装完了
- FAIL テスト 21 件を PASS させた
- LLM 知識抽出、メタデータ生成、Markdown フォーマット処理を実装

## 修正ファイル一覧

### 実装ファイル

- `src/obsidian_etl/pipelines/transform/nodes.py` - Transform ノード実装
  - `extract_knowledge()`: LLM による知識抽出（タイトル、要約、タグ）、英語 summary の日本語翻訳
  - `generate_metadata()`: メタデータ生成（file_id, created, tags, normalized=True）
  - `format_markdown()`: YAML frontmatter + Markdown body 生成、ファイル名サニタイズ

- `src/obsidian_etl/pipelines/transform/pipeline.py` - Transform パイプライン定義
  - 3 つのノードを順序実行: extract_knowledge → generate_metadata → format_markdown
  - 入力: `parsed_items` (PartitionedDataset)
  - 出力: `markdown_notes` (PartitionedDataset)

### テスト結果

```
$ python -m unittest tests.pipelines.transform.test_nodes -v
...
Ran 21 tests in 0.002s

OK
```

全テストが PASS。内訳:
- `TestExtractKnowledge`: 3 テスト (基本抽出、複数アイテム、タグ抽出)
- `TestExtractKnowledgeEnglishSummaryTranslation`: 2 テスト (英語→日本語翻訳、日本語スキップ)
- `TestExtractKnowledgeErrorHandling`: 3 テスト (LLM 失敗、部分失敗、空レスポンス)
- `TestGenerateMetadata`: 4 テスト (メタデータ生成、created_at=None、空 tags、フィールド保持)
- `TestFormatMarkdown`: 4 テスト (frontmatter + body、値一致、summary 含有、tags リスト)
- `TestFormatMarkdownOutputFilename`: 5 テスト (基本、特殊文字、Unicode、長いタイトル、空タイトル)

### リグレッション確認

```
$ python -m unittest tests.pipelines.transform.test_nodes tests.pipelines.extract_claude.test_nodes -v
...
Ran 38 tests in 0.003s

OK
```

Phase 2 (Extract Claude) のテストも全て PASS。リグレッションなし。

## 実装の詳細

### extract_knowledge ノード

- **入力**: `dict[str, Callable]` (PartitionedDataset パターン)
- **処理**:
  1. `knowledge_extractor.extract_knowledge()` で LLM 呼び出し
  2. `is_english_summary()` で英語検出
  3. 英語の場合 `translate_summary()` で日本語翻訳
  4. `generated_metadata` として `title`, `summary`, `summary_content`, `tags` を追加
- **エラーハンドリング**: LLM 失敗時はアイテムを除外してログ出力

### generate_metadata ノード

- **入力**: `generated_metadata` を持つアイテム
- **処理**:
  1. `created_at` (ISO 8601) を `YYYY-MM-DD` に変換（フォールバック: 現在日付）
  2. `metadata` dict 生成: `title`, `created`, `tags`, `source_provider`, `file_id`, `normalized: True`
- **出力**: 元のフィールド + `metadata`

### format_markdown ノード

- **入力**: `metadata` と `generated_metadata` を持つアイテム
- **処理**:
  1. YAML frontmatter 生成（手動フォーマット、tags は 2 スペースインデント）
  2. Body 生成（`## 要約` + `summary_content`）
  3. ファイル名サニタイズ（unsafe 文字削除、255 文字制限）
- **出力**: `dict[filename, item]` - `item["content"]` に Markdown

### YAML frontmatter フォーマット

PyYAML の `yaml.dump()` は tags リストを 0 スペースインデントで出力するため、手動フォーマットを採用:

```yaml
title: Python asyncio の仕組み
created: 2026-01-15
tags:
  - Python
  - asyncio
source_provider: claude
file_id: a1b2c3d4e5f6
normalized: true
```

### ファイル名サニタイズ

- unsafe 文字除去: `/\:*?"<>|`
- 複数スペース→単一スペース
- 255 文字以下に切り詰め
- 空タイトル時は `file_id[:12].md` にフォールバック

## 次 Phase への引き継ぎ

### Phase 4 (US1 Organize) で必要な情報

- **入力データセット**: `markdown_notes` (PartitionedDataset)
- **出力期待値**: Vault 配置済みファイル（ジャンル判定済み）
- **共通 utils**: 既存の utils は Phase 1 で移植済み

### 技術的注意点

- PartitionedDataset パターンは Extract/Transform で確立済み
- LLM 呼び出しは `knowledge_extractor` モジュール経由
- エラーハンドリングはログ出力のみ（Hook は Phase 5 で実装）

## 実装のミス・課題

なし。全テスト PASS。
