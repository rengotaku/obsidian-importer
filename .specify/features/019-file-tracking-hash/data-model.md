# Data Model: ファイル追跡ハッシュID

**Date**: 2026-01-17
**Branch**: `019-file-tracking-hash`

## Entity Changes

### ProcessingResult（既存型の拡張）

```python
class ProcessingResult(TypedDict):
    """単一ファイル処理結果"""
    # 既存フィールド
    success: bool
    file: str
    genre: GenreType | None
    confidence: ConfidenceLevel
    destination: str | None
    error: str | None
    timestamp: str
    original_chars: int | None
    normalized_chars: int | None
    char_diff: int | None
    improvements_made: list[str] | None
    is_complete_english_doc: bool | None
    is_review: bool
    review_reason: str | None

    # 新規フィールド
    file_id: str | None  # ハッシュベースの一意識別子（12文字）
```

## JSON Schema Changes

### processed.json エントリ

**Before**:
```json
{
  "file": "test.md",
  "status": "success",
  "destination": "Vaults/エンジニア/test.md",
  "timestamp": "2026-01-17T10:30:00"
}
```

**After**:
```json
{
  "file": "test.md",
  "file_id": "abc123def456",
  "status": "success",
  "destination": "Vaults/エンジニア/test.md",
  "timestamp": "2026-01-17T10:30:00"
}
```

### errors.json エントリ

**Before**:
```json
{
  "file": "broken.md",
  "error": "LLM parse error",
  "timestamp": "2026-01-17T10:35:00"
}
```

**After**:
```json
{
  "file": "broken.md",
  "file_id": "xyz789abc012",
  "error": "LLM parse error",
  "timestamp": "2026-01-17T10:35:00"
}
```

## Validation Rules

| フィールド | ルール |
|-----------|--------|
| `file_id` | 12文字の16進数文字列（`[0-9a-f]{12}`） |
| `file_id` | None許容（後方互換性） |

## State Transitions

```
[ファイル検出] → [コンテンツ読み込み] → [ハッシュID生成] → [処理実行] → [ログ記録]
                                           ↓
                                    file_id = sha256(content + path)[:12]
```

## Relationships

```
ProcessingResult
    └── file_id (generated from content + initial_path)
         │
         ├── processed.json[].file_id
         └── errors.json[].file_id
```

## Migration Notes

- 既存の `processed.json` / `errors.json` には `file_id` がない
- 後方互換性のため `file_id` は `str | None` 型
- 古いログを読む際は `file_id` が存在しない場合を考慮
