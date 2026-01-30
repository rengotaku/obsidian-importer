# Quickstart: Resume モードでの処理済みアイテムスキップ機能

**Feature Branch**: `033-resume-skip-processed`
**Created**: 2026-01-24

## 概要

Resume モード（`--session` オプション）で既存の処理済みアイテムをスキップし、インポート時間を大幅に削減する機能。

## 実装手順

### Step 1: PhaseStats に skipped_count 追加

**ファイル**: `src/etl/core/session.py`

```python
@dataclass
class PhaseStats:
    status: str
    success_count: int
    error_count: int
    skipped_count: int = 0  # NEW: スキップ数
    completed_at: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "status": self.status,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "skipped_count": self.skipped_count,  # NEW
            "completed_at": self.completed_at,
        }
        if self.error is not None:
            result["error"] = self.error
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PhaseStats":
        return cls(
            status=data["status"],
            success_count=data["success_count"],
            error_count=data["error_count"],
            skipped_count=data.get("skipped_count", 0),  # 後方互換
            completed_at=data["completed_at"],
            error=data.get("error"),
        )
```

### Step 2: ExtractKnowledgeStep に処理済みスキップ追加

**ファイル**: `src/etl/stages/transform/knowledge_transformer.py`

```python
def process(self, item: ProcessingItem) -> ProcessingItem:
    """Extract knowledge from conversation using Ollama."""

    # [NEW] Resume スキップ: 処理済みチェック
    if self._is_already_processed(item):
        item.status = ItemStatus.SKIPPED
        item.metadata["skipped_reason"] = "already_processed"
        item.transformed_content = item.content  # 既存コンテンツを維持
        return item

    # ... 既存の処理ロジック

def _is_already_processed(self, item: ProcessingItem) -> bool:
    """Check if item was already processed in a previous run.

    Returns True if:
    - knowledge_extracted is True
    - knowledge_document exists and is not None
    """
    if item.metadata.get("knowledge_extracted") is not True:
        return False
    if item.metadata.get("knowledge_document") is None:
        return False
    return True
```

### Step 3: cli.py で Resume 時の入力コピースキップ

**ファイル**: `src/etl/cli.py`

```python
# 変更前（L285-306 付近）
# Copy input files to extract/input
extract_input = phase_data.stages[StageType.EXTRACT].input_path

if source_path.is_file() and source_path.suffix.lower() == ".zip":
    shutil.copy(source_path, extract_input)
else:
    # ... コピー処理

# 変更後
# Resume 時は入力ファイルコピーをスキップ
if not session_id:  # 新規セッションのみコピー
    extract_input = phase_data.stages[StageType.EXTRACT].input_path

    if source_path.is_file() and source_path.suffix.lower() == ".zip":
        shutil.copy(source_path, extract_input)
    else:
        # ... 既存のコピー処理
else:
    # Resume: 既存の入力ファイルを使用
    extract_input = phase_data.stages[StageType.EXTRACT].input_path
    if not any(extract_input.iterdir()):
        print(f"[Error] No input files found in session: {session_id}", file=sys.stderr)
        return ExitCode.INPUT_NOT_FOUND
```

### Step 4: ImportPhase で skipped_count 集計

**ファイル**: `src/etl/phases/import_phase.py`

```python
def run(self, phase_data: Phase, debug_mode: bool = False, limit: int | None = None) -> PhaseResult:
    # ... 既存の stage 実行

    # Consume iterator and count results
    items_processed = 0
    items_failed = 0
    items_skipped = 0  # NEW

    for item in loaded:
        if item.status == ItemStatus.COMPLETED:
            items_processed += 1
        elif item.status == ItemStatus.FAILED:
            items_failed += 1
        elif item.status == ItemStatus.SKIPPED:  # NEW
            items_skipped += 1
        else:
            items_processed += 1

    # ... PhaseResult 作成（skipped_count を含める）
```

### Step 5: コンソール出力の更新

**ファイル**: `src/etl/cli.py`

```python
# 変更前
print(f"[Phase] import completed ({result.items_processed} success, {result.items_failed} failed)")

# 変更後
if result.items_skipped > 0:
    print(f"[Phase] import completed ({result.items_processed} success, {result.items_failed} failed, {result.items_skipped} skipped)")
else:
    print(f"[Phase] import completed ({result.items_processed} success, {result.items_failed} failed)")
```

## テスト手順

### 1. 新規セッションで一部処理

```bash
make import INPUT=~/.staging/@llm_exports/claude/ LIMIT=5
# → 5件処理
```

### 2. Resume で続行

```bash
make import INPUT=~/.staging/@llm_exports/claude/ SESSION=<session_id>
# → 処理済み5件はスキップ、残りを処理
```

### 3. 全件処理済みセッションで Resume

```bash
make import INPUT=~/.staging/@llm_exports/claude/ SESSION=<session_id>
# → 全件スキップ、即座に完了
```

## 検証ポイント

| 項目 | 期待値 |
|------|--------|
| スキップ時間 | 10ms 未満/アイテム |
| `session.json` | `skipped_count` が記録される |
| `steps.jsonl` | `status: "skipped"`, `skipped_reason` が記録される |
| コンソール出力 | スキップ数が表示される |
| 入力ファイル | Resume 時に上書きされない |
