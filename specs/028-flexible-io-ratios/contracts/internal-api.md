# Internal API Contracts: 柔軟な入出力比率対応フレームワーク

**Date**: 2026-01-20
**Feature**: 028-flexible-io-ratios

## Overview

このドキュメントは ETL フレームワーク内部の API コントラクトを定義する。外部 API は存在しない（ローカル CLI ツール）。

## BaseStep Interface

### process() - 既存（1:1 処理）

```python
@abstractmethod
def process(self, item: ProcessingItem) -> ProcessingItem:
    """Process a single item.

    Args:
        item: Item to process.

    Returns:
        Processed item (may be the same instance, modified).

    Raises:
        Exception: If processing fails.
    """
    ...
```

**Contract**:
- Input: 1 ProcessingItem
- Output: 1 ProcessingItem
- 副作用: なし（item の content/metadata を変更のみ）

### validate_input() - 既存

```python
def validate_input(self, item: ProcessingItem) -> bool:
    """Validate input before processing.

    Args:
        item: Item to validate.

    Returns:
        True if valid, False to skip this item.
    """
    return True
```

**Contract**:
- False を返すと item.status = SKIPPED となる
- 例外を投げてはならない

### on_error() - 既存

```python
def on_error(
    self, item: ProcessingItem, error: Exception
) -> ProcessingItem | None:
    """Handle processing error.

    Args:
        item: Item that caused the error.
        error: Exception that occurred.

    Returns:
        Fallback item to continue with, or None to mark as failed.
    """
    return None
```

**Contract**:
- None を返すと item.status = FAILED となる
- ProcessingItem を返すと処理を継続

## BaseStage Interface

### run() - 拡張禁止

```python
def run(
    self,
    ctx: StageContext,
    items: Iterator[ProcessingItem],
) -> Iterator[ProcessingItem]:
    """Execute the stage on items.

    IMPORTANT: Subclasses MUST NOT override this method (FR-006).

    Args:
        ctx: Stage context with paths and configuration.
        items: Input items to process.

    Yields:
        Processed items.
    """
```

**Contract**:
- 継承クラスはオーバーライド禁止（FR-006）
- debug ログ出力は自動（FR-008）
- 1:1 処理のみ（1:N は Phase レベルで処理）

### steps property - 必須

```python
@property
@abstractmethod
def steps(self) -> list[BaseStep]:
    """List of steps to execute.

    Returns:
        Ordered list of steps for this stage.
    """
    ...
```

**Contract**:
- 継承クラスは steps を定義する
- 空リストは許可（パススルー Stage）

## Phase Interface

### discover_items() - 拡張（1:N 対応）

```python
def discover_items(self) -> Iterator[ProcessingItem]:
    """Discover items to process.

    For chunked conversations (>25000 chars):
    1. Split into chunks using Chunker
    2. Write chunk files to extract/input/
    3. Yield ProcessingItem for each chunk

    Yields:
        ProcessingItem instances with chunk metadata if applicable.
    """
```

**Contract**:
- 25000 文字超の会話は自動チャンク分割
- チャンクアイテムには metadata に chunk 情報を設定
- チャンクファイルは extract/input/ に書き出し

## Debug Output Contract

### Step-level Debug (FR-004)

**Output Path**: `{stage_output}/debug/step_{index:03d}_{name}/{item_id}.jsonl`

**Schema**:
```json
{
  "timestamp": "2026-01-20T12:00:00Z",
  "item_id": "abc123",
  "source_path": "/path/to/file.json",
  "current_step": "extract_knowledge",
  "step_index": 1,
  "status": "completed",
  "metadata": { ... },
  "content": "...",
  "transformed_content": "..."
}
```

**Contract**:
- 1:1 と 1:N で同一スキーマ（FR-003）
- BaseStage が自動出力（FR-008）
- 継承クラスはカスタマイズ不可（FR-009）

### pipeline_stages.jsonl (FR-005)

**Output Path**: `{phase_path}/pipeline_stages.jsonl`

**Schema**:
```json
{
  "timestamp": "2026-01-20T12:00:00Z",
  "session_id": "20260120_120000",
  "filename": "conv_abc123_001.json",
  "stage": "transform",
  "step": "extract_knowledge",
  "timing_ms": 1500,
  "status": "success",
  "file_id": "sha256hash",
  "is_chunked": true,
  "parent_item_id": "abc123",
  "chunk_index": 0
}
```

**Contract**:
- チャンクアイテムは `is_chunked`, `parent_item_id`, `chunk_index` を含む
- 通常アイテムはこれらのフィールドを含まない（または null）
