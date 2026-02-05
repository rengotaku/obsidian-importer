# Phase 1 Output - Setup

## 作業概要

Phase 1 Setup: 既存コードの理解と変更箇所の特定を完了。

## 読み込んだファイル

| ファイル | 行数 | 主要な内容 |
|----------|------|-----------|
| `src/obsidian_etl/pipelines/organize/nodes.py` | 336 | classify_genre, normalize_frontmatter, clean_content, determine_vault_path, move_to_vault |
| `src/obsidian_etl/pipelines/organize/pipeline.py` | 71 | Pipeline: classify → normalize → clean → determine → move |
| `tests/pipelines/organize/test_nodes.py` | 823 | 6 TestClass, ~30 テストメソッド |
| `tests/e2e/golden_comparator.py` | 321 | split_frontmatter_and_body, calculate_*_similarity, compare_directories |
| `tests/e2e/test_golden_comparator.py` | 507 | ~40 テストメソッド |
| `tests/fixtures/golden/` | 3 files | キッザニア, 岩盤浴, BGM配信サーバー |
| `Makefile` (E2E targets) | ~80 lines | test-e2e, test-e2e-update-golden |
| `conf/base/catalog.yml` | 176 | PartitionedDataset definitions |

## 変更箇所の特定

### 1. Pipeline 変更 (nodes.py + pipeline.py)

**削除対象ノード:**
- `determine_vault_path` (L240-273): genre → vault_path マッピング → **削除**
- `move_to_vault` (L276-335): ファイル書き込み → **削除**

**新規ノード:**
- `extract_topic`: LLM で topic 抽出 + 小文字正規化
- `embed_frontmatter_fields`: genre, topic, summary を frontmatter に埋め込み（ファイル I/O なし）

**Pipeline 変更:**
```
現在: classify → normalize → clean → determine_vault_path → move_to_vault
変更: classify → extract_topic (NEW) → normalize → clean → embed_frontmatter_fields (NEW)
```

### 2. Makefile 変更

**test-e2e:**
- L142: `--to-nodes=format_markdown` → **削除**
- L148: `--actual $(TEST_DATA_DIR)/07_model_output/notes` → `--actual $(TEST_DATA_DIR)/07_model_output/organized`

**test-e2e-update-golden:**
- L183: `--to-nodes=format_markdown` → **削除**
- L188: `notes/*.md` → `organized/*.md`

### 3. Catalog 変更 (conf/base/catalog.yml)

**追加:**
```yaml
topic_extracted_items:
  type: partitions.PartitionedDataset
  path: data/07_model_output/topic_extracted
  dataset:
    type: json.JSONDataset
  filename_suffix: ".json"

organized_notes:
  type: partitions.PartitionedDataset
  path: data/07_model_output/organized
  dataset:
    type: text.TextDataset
  filename_suffix: ".md"
```

**削除候補:**
- `vault_determined_items` (L155-164): determine_vault_path 出力 → 不要に

### 4. Golden Files 変更

現在の frontmatter:
```yaml
title: ...
created: YYYY-MM-DD
tags: []
source_provider: claude
file_id: xxx
normalized: true
```

目標の frontmatter:
```yaml
title: ...
created: YYYY-MM-DD
tags: [...]
source_provider: claude
file_id: xxx
normalized: true
summary: ...
genre: engineer|business|economy|daily|other
topic: ...  # 小文字、空許容
```

### 5. テスト変更

**tests/pipelines/organize/test_nodes.py:**
- 削除: `TestDetermineVaultPath` (6 tests)
- 削除: `TestMoveToVault` (6 tests)
- 追加: `TestExtractTopic` (~4 tests)
- 追加: `TestEmbedFrontmatterFields` (~5 tests)

**tests/e2e/test_golden_comparator.py:**
- `SAMPLE_GOLDEN` に `genre`, `topic` 追加
- 新規テスト: frontmatter に genre/topic がある場合の類似度計算

## 注意点

1. **golden_comparator は動的**: key existence チェックは `golden.keys()` をループするため、`genre`, `topic` を追加しても自動で含まれる。明示的なコード変更は不要の可能性あり。

2. **既存テストの影響**: `determine_vault_path` と `move_to_vault` のテスト削除が必要（Phase 6 で対応）

3. **LLM 呼び出し**: `extract_topic` は Ollama を使用。既存の `classify_genre` と同様のパターンで実装可能。

## 次ステップ

Phase 2: User Story 4 - パイプライン変更 (TDD: RED → GREEN)
- tdd-generator: テスト実装 (RED)
- phase-executor: 実装 (GREEN) + 検証
