# Phase 1 Output: Setup

**Date**: 2026-02-22
**Branch**: `060-dynamic-genre-config`

## Completed Tasks

- [X] T001 Read current implementation in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T002 Read existing tests in tests/pipelines/organize/test_nodes.py
- [X] T003 Read current config format in conf/base/parameters_organize.local.yml.example
- [X] T004 Update config to new format (vault + description) in conf/base/parameters_organize.local.yml.example
- [X] T005 Update local config to new format in conf/local/parameters_organize.yml
- [X] T006 Generate phase output

## Summary

### 既存実装の理解

**nodes.py** (`_extract_topic_and_genre_via_llm`):
- Lines 135-235
- ハードコードされた `system_prompt` にジャンル定義を含む
- `valid_genres` セットがハードコード (11ジャンル)
- JSON形式でLLMからtopic/genreを抽出

**test_nodes.py**:
- `_make_organize_params()` ヘルパーで `genre_keywords` を定義
- `TestExtractTopicAndGenre`: LLM統合テスト (モック使用)
- `TestLogGenreDistribution`: ジャンル分布ログテスト

**既存テストパターン**:
- `_make_partitioned_input()` でPartitionedDataset形式を模倣
- `unittest.mock.patch` でLLM呼び出しをモック

### 設定ファイル更新

**旧形式** (フラット):
```yaml
genre_vault_mapping:
  ai: "エンジニア"
  devops: "エンジニア"
```

**新形式** (ネスト: vault + description):
```yaml
genre_vault_mapping:
  ai:
    vault: "エンジニア"
    description: "AI/機械学習/LLM/生成AI/Claude/ChatGPT"
  devops:
    vault: "エンジニア"
    description: "インフラ/CI/CD/クラウド/Docker/Kubernetes/AWS"
```

### Phase 2 への引継ぎ事項

1. **実装対象**: `_extract_topic_and_genre_via_llm()` のプロンプト動的生成
2. **テスト対象**: 新形式の設定読み込み、プロンプト生成
3. **ハードコード削除対象**:
   - `system_prompt` 内のジャンル定義
   - `valid_genres` セット

### 変更ファイル一覧

| ファイル | 変更内容 |
|----------|----------|
| `conf/base/parameters_organize.local.yml.example` | 新形式に更新 |
| `conf/local/parameters_organize.yml` | 新形式に更新 |

### 次フェーズの準備

Phase 2 (US1+US2) は TDD フローで実行:
1. tdd-generator → テスト実装 (RED)
2. phase-executor → 実装 (GREEN) + 検証
