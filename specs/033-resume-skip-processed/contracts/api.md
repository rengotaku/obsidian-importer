# API Contracts: Resume モードでの処理済みアイテムスキップ機能

**Feature Branch**: `033-resume-skip-processed`
**Created**: 2026-01-24

## CLI Interface

### import コマンド

```bash
# 新規セッション（既存動作）
python -m src.etl import --input PATH [--provider claude|openai] [--debug] [--limit N]

# Resume モード（変更あり）
python -m src.etl import --input PATH --session SESSION_ID [--provider claude|openai] [--debug]
```

#### Resume モードの動作変更

| 項目 | 変更前 | 変更後 |
|------|--------|--------|
| 入力ファイルコピー | 毎回実行 | スキップ（既存ファイルを使用） |
| 処理済みアイテム | 再処理 | スキップ |
| コンソール出力 | `(N success, M failed)` | `(N success, M failed, K skipped)` |

### status コマンド

```bash
python -m src.etl status --session SESSION_ID
```

#### 出力例（変更後）

```
Session: 20260124_164549
Status: completed
Debug: false

Phases:
  import:
    Status: completed
    Success: 100
    Failed: 0
    Skipped: 500
    Completed: 2026-01-24T16:50:12.123456
```

## Internal API

### ExtractKnowledgeStep.process()

```python
def process(self, item: ProcessingItem) -> ProcessingItem:
    """Extract knowledge from conversation.

    Resume behavior:
    - If item.metadata["knowledge_extracted"] is True AND
      item.metadata["knowledge_document"] exists:
      → Set item.status = ItemStatus.SKIPPED
      → Set item.metadata["skipped_reason"] = "already_processed"
      → Return item immediately (no LLM call)

    Args:
        item: ProcessingItem with conversation content.

    Returns:
        ProcessingItem with extracted knowledge OR skipped status.
    """
```

### WriteToSessionStep.process()

```python
def process(self, item: ProcessingItem) -> ProcessingItem:
    """Write content to session output.

    Resume behavior:
    - If item.status == ItemStatus.SKIPPED:
      → Preserve skip metadata
      → Return item without writing file

    Args:
        item: ProcessingItem from Transform stage.

    Returns:
        ProcessingItem with output_path OR skipped status.
    """
```

### PhaseStats

```python
@dataclass
class PhaseStats:
    """Statistics for a completed phase.

    Attributes:
        status: Phase completion status.
        success_count: Number of items successfully processed.
        error_count: Number of items that failed.
        skipped_count: Number of items skipped (NEW).
        completed_at: ISO format completion timestamp.
        error: Error message if phase crashed (optional).
    """
    status: str
    success_count: int
    error_count: int
    skipped_count: int = 0
    completed_at: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON output."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PhaseStats":
        """Deserialize from dictionary.

        Note: skipped_count defaults to 0 for backward compatibility.
        """
```

### ImportPhase.run()

```python
def run(
    self,
    phase_data: Phase,
    debug_mode: bool = False,
    limit: int | None = None,
) -> PhaseResult:
    """Execute the Import phase.

    Resume behavior:
    - Counts ItemStatus.SKIPPED items separately
    - Returns skipped_count in result (via PhaseStats)

    Returns:
        PhaseResult with items_processed, items_failed, items_skipped.
    """
```

## Error Handling

### Resume セッションが存在しない場合

```bash
$ python -m src.etl import --input /path --session nonexistent
[Error] Session not found: nonexistent
# Exit code: 2 (INPUT_NOT_FOUND)
```

### 入力ファイルがない場合（Resume）

```bash
$ python -m src.etl import --input /path --session 20260124_123456
[Error] No input files found in session: 20260124_123456
# Exit code: 2 (INPUT_NOT_FOUND)
```

## Exit Codes

| Code | 意味 | Resume での追加条件 |
|------|------|-------------------|
| 0 | SUCCESS | 全件スキップも成功 |
| 1 | GENERAL_ERROR | - |
| 2 | INPUT_NOT_FOUND | セッションが存在しない |
| 3 | OLLAMA_ERROR | - |
| 4 | PARTIAL_SUCCESS | 一部失敗（スキップは成功扱い） |
| 5 | ALL_FAILED | - |

## Backward Compatibility Contract

1. **新規セッション**: 動作変更なし
2. **古い session.json**: `skipped_count=0` でデフォルト読み込み
3. **debug モード**: スキップも `steps.jsonl` に記録
4. **出力ファイル形式**: 変更なし（Markdown, frontmatter）
