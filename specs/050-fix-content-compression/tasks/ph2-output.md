# Phase 2 Output: US1 プロンプト改善

**Date**: 2026-02-10
**Status**: COMPLETE

## Tasks Completed

| Task | Description | Status |
|------|-------------|--------|
| T008 | Read previous phase output | ✅ |
| T009 | Add "情報量の目安" section to prompt | ✅ |
| T010 | Add "省略禁止" section to prompt | ✅ |
| T011 | Verify prompt file contains new sections | ✅ |
| T012 | Run `make test` - all 295 tests pass | ✅ |
| T013 | Generate phase output | ✅ |

## Changes Made

### Modified: `src/obsidian_etl/utils/prompts/knowledge_extraction.txt`

Added two new sections before "品質基準":

#### 1. 情報量の目安

```text
## 情報量の目安

元の会話サイズに応じた最小出力量を目安としてください:
- 10,000文字以上の会話 → 最低1,000文字の「内容」セクション
- 5,000〜10,000文字の会話 → 最低750文字の「内容」セクション
- 5,000文字未満の会話 → 最低500文字の「内容」セクション

短い会話でも、コード・手順・設定などの重要情報は**すべて保持**してください。
```

#### 2. 省略禁止

```text
## 省略禁止

以下は**絶対に省略しないでください**:
- コードブロック（完全な形で含める、一部だけを抽出しない）
- 手順・ステップ（すべてのステップを含める）
- 設定ファイルの内容（完全な形で含める）
- コマンド例（オプションを含めて完全に記載）
- エラーメッセージと対処法（具体的に記載）

「詳細は省略」「以下同様」「...（省略）...」などの省略表現は**使用禁止**です。
```

#### 3. 品質基準の追加項目

```text
- **情報保持**: 重要な情報は一切省略しない
```

## Verification

- ✅ "情報量の目安" section exists (grep count: 1)
- ✅ "省略禁止" section exists (grep count: 1)
- ✅ All 295 tests pass (no regressions)

## Next Phase: Phase 3 (US2 圧縮率検証共通処理)

Phase 3 will create `compression_validator.py` with:
- `CompressionResult` dataclass
- `get_threshold()` function with tiered thresholds
- `validate_compression()` function
