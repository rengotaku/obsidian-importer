# 統合テスト指示書: 022-import-file-id

**Date**: 2026-01-18
**Feature**: LLMインポートでのfile_id付与
**Branch**: `022-import-file-id`

## 機能概要

LLMインポート処理（`make llm-import`）で生成されるナレッジファイルに、12文字の16進数ハッシュID（file_id）を自動付与する機能。

## テスト対象

| コンポーネント | ファイル | 変更内容 |
|---------------|----------|----------|
| file_id生成 | `development/scripts/llm_import/common/file_id.py` | 新規 |
| KnowledgeDocument | `development/scripts/llm_import/common/knowledge_extractor.py` | file_idフィールド追加 |
| ProcessedEntry | `development/scripts/llm_import/common/state.py` | file_idフィールド追加 |
| CLI | `development/scripts/llm_import/cli.py` | file_id生成・設定処理 |

---

## テスト1: ユニットテスト

### 実行コマンド

```bash
cd /path/to/project
make test
```

### 期待結果

```
Ran 156 tests in X.XXXs
OK
```

### 検証ポイント

- [ ] 全156テストがパス
- [ ] file_id関連テストが含まれている（test_file_id.py, test_knowledge_extractor.py, test_cli.py）

---

## テスト2: インポート統合テスト

### 前提条件

- Claudeエクスポートデータが `.staging/@llm_exports/claude/parsed/conversations/` に存在
- Ollamaが起動している（`ollama serve`）

### 実行コマンド

```bash
cd /path/to/project
make llm-import LIMIT=1
```

### 期待結果

1. `.staging/@index/` に新しいMarkdownファイルが生成される
2. 生成ファイルのfrontmatterに `file_id: [12文字16進数]` が含まれる

### 検証コマンド

```bash
# 最新の生成ファイルを確認
ls -lt .staging/@index/*.md | head -1

# frontmatterを確認（file_idが含まれていることを確認）
head -15 .staging/@index/[生成されたファイル名].md
```

### 期待されるfrontmatter形式

```yaml
---
title: [タイトル]
summary: [要約]
created: 2026-01-18
source_provider: claude
source_conversation: [会話ID]
file_id: a1b2c3d4e5f6  # ← 12文字の16進数
normalized: true
---
```

---

## テスト3: state.json記録確認

### 実行コマンド

```bash
# state.jsonの最新エントリを確認
cat .staging/@llm_exports/claude/.extraction_state.json | jq '.processed_conversations | to_entries | last | .value'
```

### 期待結果

```json
{
  "id": "[会話ID]",
  "provider": "claude",
  "input_file": ".staging/@llm_exports/claude/parsed/conversations/[xxx].md",
  "output_file": ".staging/@index/[ファイル名].md",
  "processed_at": "2026-01-18T...",
  "status": "success",
  "skip_reason": null,
  "error_message": null,
  "file_id": "a1b2c3d4e5f6"
}
```

### 検証ポイント

- [ ] `file_id` フィールドが存在
- [ ] 値が12文字の16進数
- [ ] 出力ファイルのfrontmatterと同一のfile_id

---

## テスト4: 決定論性の確認

同じファイルを再処理した場合、同じfile_idが生成されることを確認。

### 手順

1. 現在のstate.jsonをバックアップ
2. 特定の会話をリセット
3. 再度インポート
4. file_idが同一であることを確認

```bash
# バックアップ
cp .staging/@llm_exports/claude/.extraction_state.json /tmp/state_backup.json

# 特定会話のfile_idを記録
CONV_ID="[テスト対象の会話ID]"
OLD_FILE_ID=$(cat .staging/@llm_exports/claude/.extraction_state.json | jq -r ".processed_conversations[\"$CONV_ID\"].file_id")
echo "Old file_id: $OLD_FILE_ID"

# リセット（特定会話を削除）
# ※ 手動でstate.jsonから該当エントリを削除

# 再インポート
make llm-import LIMIT=1

# 新しいfile_idを確認
NEW_FILE_ID=$(cat .staging/@llm_exports/claude/.extraction_state.json | jq -r ".processed_conversations[\"$CONV_ID\"].file_id")
echo "New file_id: $NEW_FILE_ID"

# 比較
[ "$OLD_FILE_ID" = "$NEW_FILE_ID" ] && echo "PASS: 決定論的" || echo "FAIL: file_idが異なる"
```

---

## テスト5: 後方互換性の確認

既存のstate.json（file_idなしのエントリ）が正常に読み込めることを確認。

### 手順

```bash
# Pythonで直接確認
cd /path/to/project/development
python3 -c "
from scripts.llm_import.common.state import StateManager
from pathlib import Path

state_file = Path('../.staging/@llm_exports/claude/.extraction_state.json')
manager = StateManager(state_file)
manager.load()

# 古いエントリ（file_idなし）の確認
for entry in list(manager.state.processed_conversations.values())[:5]:
    print(f'{entry.id}: file_id={entry.file_id}')

print(f'Total entries: {len(manager.state.processed_conversations)}')
print('PASS: 後方互換性OK')
"
```

### 期待結果

- エラーなく読み込み完了
- 古いエントリの `file_id` は `None`
- 新しいエントリの `file_id` は12文字の16進数

---

## テスト6: チャンク分割時のfile_id

大きな会話がチャンク分割された場合、各チャンクに異なるfile_idが付与されることを確認。

### 確認方法

```bash
# チャンク分割された会話を探す
ls .staging/@index/ | grep "_part"

# 各パートのfile_idを確認
for f in .staging/@index/*_part*.md; do
  echo "=== $f ==="
  grep "file_id:" "$f"
done
```

### 期待結果

- 各パートファイルに異なるfile_idが付与されている

---

## チェックリスト

| # | テスト項目 | 結果 |
|---|-----------|------|
| 1 | ユニットテスト 156/156 パス | [ ] |
| 2 | 生成ファイルのfrontmatterにfile_id存在 | [ ] |
| 3 | state.jsonにfile_id記録 | [ ] |
| 4 | 出力ファイルとstate.jsonのfile_idが一致 | [ ] |
| 5 | 決定論的（同一入力→同一file_id） | [ ] |
| 6 | 後方互換性（file_idなしエントリ読み込み可） | [ ] |
| 7 | チャンク分割時に各チャンクで異なるfile_id | [ ] |

---

## トラブルシューティング

### Ollamaが起動していない場合

```bash
ollama serve &
```

### テスト対象データがない場合

```bash
# 未処理の会話があるか確認
make llm-status
```

### file_idが生成されない場合

```bash
# cli.pyのfile_id生成部分を確認
grep -n "generate_file_id" development/scripts/llm_import/cli.py
```
