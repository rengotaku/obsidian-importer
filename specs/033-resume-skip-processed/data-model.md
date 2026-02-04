# Data Model: Resume モードでの処理済みアイテムスキップ機能

**Feature Branch**: `033-resume-skip-processed`
**Created**: 2026-01-24

## 変更概要

Resume モードでのスキップ機能に必要なデータモデル変更を定義する。

## PhaseStats 拡張

### 変更前

```python
@dataclass
class PhaseStats:
    status: str
    success_count: int
    error_count: int
    completed_at: str
    error: str | None = None
```

### 変更後

```python
@dataclass
class PhaseStats:
    status: str
    success_count: int
    error_count: int
    skipped_count: int = 0  # NEW
    completed_at: str
    error: str | None = None
```

### session.json 出力例

```json
{
  "session_id": "20260124_164549",
  "created_at": "2026-01-24T16:45:49.417261",
  "status": "completed",
  "phases": {
    "import": {
      "status": "completed",
      "success_count": 100,
      "error_count": 0,
      "skipped_count": 500,
      "completed_at": "2026-01-24T16:50:12.123456"
    }
  },
  "debug_mode": false
}
```

### 後方互換性

- 古い session.json の読み込み: `skipped_count` がなければ `0` でデフォルト
- `from_dict()` でオプショナルとして処理

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "PhaseStats":
    return cls(
        status=data["status"],
        success_count=data["success_count"],
        error_count=data["error_count"],
        skipped_count=data.get("skipped_count", 0),  # デフォルト 0
        completed_at=data["completed_at"],
        error=data.get("error"),
    )
```

## ProcessingItem.metadata 拡張

### スキップ関連フィールド

| フィールド | 型 | 設定箇所 | 説明 |
|----------|-----|---------|------|
| `knowledge_extracted` | bool | Transform | 知識抽出完了フラグ（既存、読み取り対象に） |
| `knowledge_document` | dict | Transform | 抽出済みドキュメント（既存、読み取り対象に） |
| `skipped_reason` | str | Transform/Load | スキップ理由（新規） |

### skipped_reason 値

| 値 | 意味 | 設定箇所 |
|----|------|---------|
| `already_processed` | Transform で処理済み検出 | `ExtractKnowledgeStep` |
| `file_exists` | Load で出力ファイル存在 | `WriteToSessionStep` |
| `non-conversation data not written` | 会話以外のデータ | `WriteToSessionStep`（既存） |

## steps.jsonl スキップエントリ

### 通常処理エントリ（既存）

```json
{
  "item_id": "abc123",
  "step": "extract_knowledge",
  "status": "completed",
  "timing_ms": 45000,
  "before_chars": 5000,
  "after_chars": 1200
}
```

### スキップエントリ（新規）

```json
{
  "item_id": "abc123",
  "step": "extract_knowledge",
  "status": "skipped",
  "skipped_reason": "already_processed",
  "timing_ms": 2,
  "before_chars": 5000,
  "after_chars": 5000
}
```

## ItemStatus との対応

| ItemStatus | 意味 | skipped_count への寄与 |
|------------|------|----------------------|
| `COMPLETED` | 正常処理完了 | No (success_count) |
| `FAILED` | 処理失敗 | No (error_count) |
| `SKIPPED` | スキップ | **Yes** |
| `PENDING` | 未処理 | No |
| `PROCESSING` | 処理中 | No |

## 型定義サマリー

```python
# src/etl/core/session.py
@dataclass
class PhaseStats:
    status: str
    success_count: int
    error_count: int
    skipped_count: int = 0
    completed_at: str
    error: str | None = None

# src/etl/core/models.py (既存)
@dataclass
class ProcessingItem:
    item_id: str
    content: str | None
    metadata: dict[str, Any]  # skipped_reason を追加
    status: ItemStatus
    # ...
```
