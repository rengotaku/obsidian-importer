# Quickstart: Filename Normalize

**Date**: 2026-01-10
**Branch**: `002-filename-normalize`

## Overview

この機能は `/og:organize` コマンドの出力ファイル名を改善します：

- **Before**: `2022-10-7-Pull-a-docker-image-from-ECR_1.md`
- **After**: `Docker imageをECRからPullする方法.md`

## Prerequisites

- Ollama が稼働中であること
- `gpt-oss:20b` モデルが利用可能であること

```bash
curl -s http://localhost:11434/api/tags | head -1
```

## Quick Test

### 1. テストファイルを作成

```bash
cat > "@index/2022-10-7-Test-Filename-Normalize.md" << 'EOF'
---
title: Test
---

# Test Article

This is a test article about Docker and ECR.
EOF
```

### 2. プレビュー実行

```bash
python3 .claude/scripts/ollama_normalizer.py --preview "@index/2022-10-7-Test-Filename-Normalize.md"
```

**期待される出力**:
```
✅ ファイル整理完了
  📄 元ファイル: @index/2022-10-7-Test-Filename-Normalize.md
  📂 移動先: エンジニア/Docker ECR テスト.md  # 日付なし、スペース区切り
  🏷️ ジャンル: エンジニア (confidence: 0.85)
  👁️ プレビューモード（移動なし）
```

### 3. 実際に処理

```bash
python3 .claude/scripts/ollama_normalizer.py "@index/2022-10-7-Test-Filename-Normalize.md"
```

### 4. 結果確認

```bash
# ファイル名に日付が含まれていないこと
ls エンジニア/*.md | grep -v "2022"

# frontmatter.title とファイル名が一致すること
head -5 "エンジニア/Docker ECR テスト.md"
```

## Key Changes

| 項目 | Before | After |
|------|--------|-------|
| ファイル名の決定 | 元ファイル名から日付除去 | Ollamaが生成したタイトルを使用 |
| ハイフン | 残る | スペースに変換（Ollamaが適切な形式で生成） |
| frontmatter.title | ファイル名と無関係 | ファイル名と一致 |

## Files Modified

| ファイル | 変更 |
|----------|------|
| `.claude/scripts/ollama_normalizer.py` | `normalize_filename()` 追加、`process_single_file()` 修正 |

## Troubleshooting

### Ollamaが不適切なタイトルを生成する場合

フォールバックとして元ファイル名（日付除去後、ハイフンをスペースに変換）を使用します。

### ファイル名に禁止文字が含まれる場合

自動的にアンダースコアに置換されます。

```
"Title: Subtitle" → "Title_ Subtitle"
```

## Related

- [Spec](./spec.md)
- [Research](./research.md)
- [Data Model](./data-model.md)
