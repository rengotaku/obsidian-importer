# Quickstart: LLMインポートでのfile_id付与

**Date**: 2026-01-18
**Feature**: 022-import-file-id

## 概要

LLM インポート処理（`make llm-import`）で生成されるナレッジファイルに、ファイル追跡用の file_id が自動付与されるようになります。

## 使用方法

### 通常のインポート

```bash
# インポート実行（変更なし）
make llm-import LIMIT=5

# 生成されたファイルを確認
cat .staging/@index/Knowledge_xxx.md
```

### 出力例

```yaml
---
title: Pythonのデコレータパターン
summary: デコレータの実装方法と活用例
created: 2026-01-18
source_provider: claude
source_conversation: abc123
file_id: a1b2c3d4e5f6  # ← 新規追加
normalized: true
---
```

### state.json での確認

```bash
cat .staging/@llm_exports/claude/.extraction_state.json | jq '.processed_conversations | to_entries[0].value'
```

```json
{
  "id": "abc123",
  "provider": "claude",
  "output_file": ".staging/@index/Knowledge_xxx.md",
  "status": "success",
  "file_id": "a1b2c3d4e5f6"
}
```

## file_id の特性

| 特性 | 説明 |
|------|------|
| **一意性** | 各ファイルに固有の12文字ID |
| **決定論的** | 同じ入力からは同じIDが生成される |
| **追跡性** | ファイル移動後も同一ファイルを特定可能 |

## 後方互換性

- 既存の state.json は引き続き動作します
- file_id がない古いエントリも正常に読み込まれます
- リトライ処理も既存のまま動作します

## テスト

```bash
# 全テスト実行
make test

# file_id 関連テストのみ
cd development && python -m unittest llm_import.tests.test_file_id -v
```
