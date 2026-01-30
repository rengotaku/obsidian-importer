# Data Model: 柔軟な入出力比率対応フレームワーク

**Date**: 2026-01-20
**Feature**: 028-flexible-io-ratios

## Entities

### ProcessingItem (既存・拡張)

パイプラインを流れる処理単位。1:N 展開に対応するためメタデータを拡張。

```python
@dataclass
class ProcessingItem:
    """Processing item that flows through the pipeline."""

    item_id: str
    """Unique identifier (file path or UUID)."""

    source_path: Path
    """Original source file path."""

    current_step: str
    """Name of the current processing step."""

    status: ItemStatus
    """Current processing status."""

    metadata: dict[str, Any]
    """Arbitrary metadata for the item."""

    content: str | None = None
    """Raw content after extraction."""

    transformed_content: str | None = None
    """Content after transformation."""

    output_path: Path | None = None
    """Destination path after loading."""

    error: str | None = None
    """Error message if processing failed."""
```

**Metadata Schema for Chunked Items**:

| Field | Type | Description |
|-------|------|-------------|
| `is_chunked` | bool | チャンク分割されたアイテムか |
| `chunk_index` | int | チャンク番号 (0-indexed) |
| `total_chunks` | int | 総チャンク数 |
| `parent_item_id` | str | 元のアイテムID |
| `chunk_filename` | str | チャンクファイル名 |

**Validation Rules**:
- `is_chunked=True` の場合、`chunk_index`, `total_chunks`, `parent_item_id` は必須
- `chunk_index` は 0 以上 `total_chunks` 未満
- `parent_item_id` は元の会話UUID

### StepDebugRecord (既存・統一スキーマ)

Step 毎の debug 出力レコード。1:1 と 1:N で同一スキーマ。

```python
@dataclass
class StepDebugRecord:
    """Step-level debug output record."""

    timestamp: str
    """ISO8601 format timestamp."""

    item_id: str
    """Item identifier."""

    source_path: str
    """Source file path."""

    current_step: str
    """Step name."""

    step_index: int
    """1-based step index."""

    status: str
    """Processing status (pending, completed, failed, skipped)."""

    metadata: dict[str, Any]
    """Item metadata snapshot."""

    content: str | None = None
    """Full content (debug mode only)."""

    transformed_content: str | None = None
    """Transformed content (debug mode only)."""

    error: str | None = None
    """Error message if failed."""
```

**Output Format**: JSONL (1行1JSON)

**Output Path**: `output/debug/step_{番号:03d}_{step名}/{item_id}.jsonl`

### StageLogRecord (既存・拡張)

pipeline_stages.jsonl の1レコード。親子関係フィールドを追加。

```python
@dataclass
class StageLogRecord:
    """Log record for Stage processing in JSONL format."""

    timestamp: str
    session_id: str
    filename: str
    stage: str
    step: str
    timing_ms: int
    status: str

    # Optional fields
    file_id: str | None = None
    skipped_reason: str | None = None
    before_chars: int | None = None
    after_chars: int | None = None
    diff_ratio: float | None = None

    # New: Chunk tracking (FR-007)
    is_chunked: bool | None = None
    parent_item_id: str | None = None
    chunk_index: int | None = None
```

## Relationships

```
conversations.json (1) ----[discover_items]----> ProcessingItem (N)
                                                      |
                                                      | metadata.parent_item_id
                                                      |
                                                      v
                                                 Parent UUID
```

**Traceability**:
- `StageLogRecord.parent_item_id` → 元の会話を特定
- `ProcessingItem.metadata.chunk_index` → チャンク番号を特定
- `file_id` → 重複検出（既存機能維持）

## State Transitions

### ProcessingItem Status

```
PENDING ─┬─> COMPLETED (全Step成功)
         │
         ├─> SKIPPED (validate_input失敗)
         │
         └─> FAILED (Step処理エラー)
```

### Chunk Processing Flow

```
discover_items()
    │
    ├─ should_chunk(conv) == False
    │       └─> ProcessingItem(is_chunked=False)
    │
    └─ should_chunk(conv) == True
            └─> Chunker.split(conv)
                    └─> ProcessingItem[] (is_chunked=True, chunk_index=0..N-1)
```

## File Naming Convention

| Pattern | Example | Description |
|---------|---------|-------------|
| 通常ファイル | `abc123.json` | UUID そのまま |
| チャンクファイル | `abc123_001.json` | UUID + 3桁連番 |
| 出力Markdown | `タイトル.md` | 抽出されたタイトル |
| チャンク出力 | `タイトル_001.md` | タイトル + 3桁連番 |
