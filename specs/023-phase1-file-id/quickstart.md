# Quickstart: 全工程での file_id 付与・維持

**Feature**: 023-phase1-file-id
**Date**: 2026-01-18

## 概要

この機能は、LLMインポート処理の全工程（Phase 1 → Phase 2 → organize）で file_id を付与・維持し、ファイルのトレーサビリティを確保する。

## 検証シナリオ

### Scenario 1: Phase 1 での file_id 生成

**前提条件**:
- Claude エクスポートデータが `.staging/@llm_exports/claude/` に存在
- Ollama が起動中

**手順**:
```bash
make llm-import --phase1-only LIMIT=1
```

**期待結果**:
1. `.staging/@plan/import/{session}/parsed/conversations/*.md` に file_id が含まれる

**検証**:
```bash
# 最新の parsed ファイルを確認
head -15 .staging/@plan/import/*/parsed/conversations/*.md | grep file_id
```

**成功基準**: `file_id: [12文字16進数]` が frontmatter に存在

---

### Scenario 2: Phase 1 → Phase 2 での file_id 継承

**前提条件**:
- Scenario 1 完了（parsed ファイルに file_id あり）

**手順**:
```bash
make llm-import LIMIT=1
```

**期待結果**:
1. `.staging/@index/*.md` の file_id が parsed ファイルと一致

**検証**:
```bash
# parsed と @index の file_id を比較
PARSED_ID=$(grep "file_id:" .staging/@plan/import/*/parsed/conversations/*.md | head -1 | awk '{print $2}')
INDEX_ID=$(grep "file_id:" .staging/@index/*.md | tail -1 | awk '{print $2}')
echo "Parsed: $PARSED_ID, Index: $INDEX_ID"
[ "$PARSED_ID" = "$INDEX_ID" ] && echo "✅ PASS" || echo "❌ FAIL"
```

**成功基準**: 両方の file_id が一致

---

### Scenario 3: pipeline_stages.jsonl への file_id 記録

**前提条件**:
- Scenario 2 完了

**手順**:
```bash
cat .staging/@plan/import/*/pipeline_stages.jsonl | jq -s '.[-2:]'
```

**期待結果**:
```json
[
  {"stage": "phase1", "file_id": "ab7d3d1c62f4", ...},
  {"stage": "phase2", "file_id": "ab7d3d1c62f4", ...}
]
```

**成功基準**: Phase 1 と Phase 2 のエントリに同一の file_id が記録

---

### Scenario 4: organize での file_id 維持

**前提条件**:
- `.staging/@index/` に file_id 付きファイルが存在

**手順**:
```bash
# プレビューモードで確認
python3 scripts/ollama_normalizer.py .staging/@index/test_file.md --preview
```

**期待結果**:
- 出力に元の file_id が維持されている

**検証**:
```bash
# organize 前後で file_id を比較
BEFORE=$(grep "file_id:" .staging/@index/test_file.md | awk '{print $2}')
# organize 実行後
AFTER=$(grep "file_id:" Vaults/*/test_file.md | awk '{print $2}')
[ "$BEFORE" = "$AFTER" ] && echo "✅ PASS" || echo "❌ FAIL"
```

**成功基準**: organize 前後で file_id が一致

---

### Scenario 5: organize での file_id 新規生成

**前提条件**:
- `.staging/@index/` に file_id なしのファイルを手動配置

**手順**:
```bash
# file_id なしのテストファイルを作成
cat > .staging/@index/test_no_fileid.md << 'EOF'
---
title: テストファイル
tags:
  - test
created: 2026-01-18
normalized: false
---

# テスト内容

これは file_id がないテストファイルです。
EOF

# organize 実行
python3 scripts/ollama_normalizer.py .staging/@index/test_no_fileid.md
```

**期待結果**:
- 移動先ファイルに file_id が新規生成されている

**検証**:
```bash
grep "file_id:" Vaults/*/test_no_fileid.md
```

**成功基準**: `file_id: [12文字16進数]` が frontmatter に存在

---

### Scenario 6: 後方互換性確認

**前提条件**:
- 既存の state.json に file_id なしのエントリが存在

**手順**:
```bash
cd development && python3 -c "
from scripts.llm_import.common.state import ProcessedEntry
import json

# file_id なしのエントリを読み込み
old_entry = {
    'id': 'test-uuid',
    'provider': 'claude',
    'input_file': 'test.md',
    'output_file': 'out.md',
    'processed_at': '2026-01-01T00:00:00',
    'status': 'success'
    # file_id フィールドなし
}
entry = ProcessedEntry.from_dict(old_entry)
print(f'file_id: {entry.file_id}')
print('✅ PASS' if entry.file_id is None else '❌ FAIL')
"
```

**成功基準**: `file_id: None` でエラーなく読み込み

---

## クイックテスト

全シナリオを一括で検証:

```bash
make test  # ユニットテスト
```

**成功基準**: 全テストパス

---

## トラブルシューティング

### file_id が生成されない

1. `generate_file_id()` の import を確認
2. 対象ファイルの content と filepath が正しく渡されているか確認

### Phase 1 と Phase 2 で file_id が異なる

1. Phase 2 が parsed ファイルから file_id を読み取っているか確認
2. `extract_frontmatter()` が file_id を正しくパースしているか確認

### organize で file_id が上書きされる

1. `process_single_file()` で既存 file_id を確認しているか
2. `get_or_generate_file_id()` ロジックが正しく実装されているか
