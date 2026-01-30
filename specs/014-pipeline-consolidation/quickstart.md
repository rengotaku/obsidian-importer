# Quickstart: Normalizer Pipeline統合

**Feature**: 014-pipeline-consolidation
**Date**: 2026-01-15

## Prerequisites

- Python 3.11+
- Ollama with `gpt-oss:20b` model
- 既存の`.claude/scripts/normalizer/`パッケージ

## Changes Overview

### Before (5 LLM calls)
```
pre_process → stage1_dust → stage2_genre → stage3_normalize → stage4_metadata → stage5_summary → post_process
```

### After (3 LLM calls)
```
pre_process → stage_a (分類) → stage_b (正規化) → stage_c (メタデータ) → post_process
```

## File Changes

### Modified Files

| File | Changes |
|------|---------|
| `normalizer/models.py` | StageAResult, StageCResult追加、Frontmatterにsummary/related追加 |
| `normalizer/pipeline/stages.py` | stage_a(), stage_c()追加、旧stage1-5削除 |
| `normalizer/pipeline/runner.py` | 新パイプライン実行ロジック |
| `normalizer/io/ollama.py` | `num_ctx: 16384`オプション追加 |
| `normalizer/tests/test_pipeline.py` | Stage A/B/C テスト追加 |

### New Files

| File | Purpose |
|------|---------|
| `prompts/stage_a_classify.txt` | Dust判定+ジャンル分類統合プロンプト |
| `prompts/stage_c_metadata.txt` | メタデータ+Summary統合プロンプト |

### Deleted Files

| File | Reason |
|------|--------|
| `prompts/stage1_dust.txt` | Stage Aに統合 |
| `prompts/stage2_genre.txt` | Stage Aに統合 |
| `prompts/stage4_metadata.txt` | Stage Cに統合 |
| `prompts/stage5_summary.txt` | Stage Cに統合 |

## Testing

```bash
# 既存テスト実行
cd .claude/scripts
python -m pytest normalizer/tests/ -v

# 特定ステージのテスト
python -m pytest normalizer/tests/test_pipeline.py::test_stage_a -v
python -m pytest normalizer/tests/test_pipeline.py::test_stage_c -v
```

## Frontmatter Output Example

```yaml
---
title: "EFSとEBSの違い"
tags:
  - aws
  - storage
  - efs
created: 2025-01-15
summary: "AWSのストレージサービスEFSとEBSの違いを解説。EFSは共有ファイルシステム、EBSはブロックストレージ。"
related:
  - "[[S3]]"
  - "[[EC2]]"
normalized: true
---
```

## Migration Notes

1. 既存の処理済みファイルには影響なし
2. 未処理ファイル（@index/）は新パイプラインで処理
3. `@review/`フォルダを新規作成（`unknown`判定用）
