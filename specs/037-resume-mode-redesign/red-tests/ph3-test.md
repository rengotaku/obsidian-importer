# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - User Story 1 (中断したインポートの再開)
- FAIL テスト数: 8
- テストファイル: `src/etl/tests/test_resume_mode.py`

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_resume_mode.py | TestSkipCompletedItem.test_skip_completed_item | 処理済みアイテムがスキップされる |
| test_resume_mode.py | TestSkipNotLogged.test_skip_not_logged | 空キャッシュでは全アイテム処理 |
| test_resume_mode.py | TestExtractStageSkip.test_extract_stage_skip | Extract 出力があれば Stage 全体スキップ |
| test_resume_mode.py | TestTransformItemSkip.test_transform_item_skip | Transform の処理済みアイテムスキップ |
| test_resume_mode.py | TestLoadItemSkip.test_load_item_skip | Load の処理済みアイテムスキップ |
| test_resume_mode.py | TestResumeAllCompleted.test_resume_all_completed | 全完了時は全スキップ |
| test_resume_mode.py | TestChunkedItemAllSuccessRequired.test_chunked_item_all_success_required | 部分成功チャンクは全再処理 |
| test_resume_mode.py | TestChunkedItemPartialFailureRetry.test_chunked_item_partial_failure_retry | 全成功チャンクはスキップ |

## PASS テスト（既存）

| テストファイル | テストメソッド | 説明 |
|---------------|---------------|------|
| test_resume_mode.py | TestResumePartialCompletion.test_resume_partial_completion | 10件中5件処理済み → 5件スキップ判定 (キャッシュ部分のみ) |

## 実装ヒント

### 1. StageContext に completed_cache 追加

`src/etl/core/stage.py`:
```python
@dataclass
class StageContext:
    phase: "Phase"
    stage: Stage
    debug_mode: bool = False
    limit: int | None = None
    chunk: bool = False
    completed_cache: CompletedItemsCache | None = None  # NEW
```

### 2. ResumableStage クラス（または BaseStage.run() 修正）

`src/etl/core/stage.py`:
```python
class BaseStage(ABC):
    def run(self, ctx: StageContext, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
        # Resume mode: check completed_cache
        if ctx.completed_cache:
            items = self._filter_completed(ctx.completed_cache, items)
        # ... existing logic

    def _filter_completed(self, cache: CompletedItemsCache, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
        for item in items:
            if cache.is_completed(item.item_id):
                # Skip - don't yield, don't log
                continue
            yield item
```

### 3. ChunkedItemsCache クラス

`src/etl/core/models.py`:
```python
@dataclass
class ChunkedItemsCache:
    """Cache for chunked items with parent tracking."""

    items: set[str]  # Successful item_ids
    parent_chunks: dict[str, set[str]]  # parent_item_id -> set of chunk_item_ids
    chunk_success: dict[str, set[str]]  # parent_item_id -> set of successful chunks
    stage: StageType

    @classmethod
    def from_jsonl(cls, jsonl_path: Path, stage: StageType) -> "ChunkedItemsCache":
        """Load with chunk tracking."""
        ...

    def is_completed(self, item_id: str) -> bool:
        """Check if item (or all its chunks) completed."""
        ...

    def is_parent_completed(self, parent_item_id: str) -> bool:
        """Check if all chunks of parent completed."""
        ...
```

### 4. ImportPhase.should_skip_extract_stage()

`src/etl/phases/import_phase.py`:
```python
class ImportPhase:
    def should_skip_extract_stage(self) -> bool:
        """Check if Extract output folder has results."""
        extract_output = self.base_path / "extract" / "output"
        if extract_output.exists():
            return any(extract_output.iterdir())
        return False
```

### 5. Transform/Load Stage の run_with_skip()

`src/etl/stages/transform/knowledge_transformer.py`:
```python
class KnowledgeTransformer(BaseStage):
    def run_with_skip(self, ctx: StageContext, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
        """Run with completed item skipping."""
        if ctx.completed_cache:
            items = self._filter_completed(ctx.completed_cache, items)
        yield from self.run(ctx, items)
```

## FAIL 出力例

```
ERROR: test_skip_completed_item (src.etl.tests.test_resume_mode.TestSkipCompletedItem.test_skip_completed_item)
CompletedItemsCache にあるアイテムはスキップされる。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_resume_mode.py", line 613, in test_skip_completed_item
    from src.etl.core.stage import ResumableStage, StageContext
ImportError: cannot import name 'ResumableStage' from 'src.etl.core.stage'
```

```
ERROR: test_chunked_item_all_success_required (src.etl.tests.test_resume_mode.TestChunkedItemAllSuccessRequired.test_chunked_item_all_success_required)
3チャンクのうち2チャンクのみ成功の場合、全チャンクが再処理対象。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_resume_mode.py", line 998, in test_chunked_item_all_success_required
    from src.etl.core.models import ChunkedItemsCache
ImportError: cannot import name 'ChunkedItemsCache' from 'src.etl.core.models'
```

```
ERROR: test_load_item_skip (src.etl.tests.test_resume_mode.TestLoadItemSkip.test_load_item_skip)
pipeline_stages.jsonl で load success のアイテムはスキップ。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_resume_mode.py", line 881, in test_load_item_skip
    ctx = StageContext(
TypeError: StageContext.__init__() got an unexpected keyword argument 'completed_cache'
```

## 必要な実装（GREEN フェーズ）

| タスク ID | 実装内容 | ファイル |
|----------|---------|---------|
| T029 | StageContext に completed_cache 追加 | `src/etl/core/stage.py` |
| T030 | BaseStage.run() にスキップロジック追加 | `src/etl/core/stage.py` |
| T031 | ImportPhase.should_skip_extract_stage() | `src/etl/phases/import_phase.py` |
| T032 | skip_count トラッキング | `src/etl/core/stage.py` |
| T033 | コンソール出力にスキップ数追加 | `src/etl/cli/commands/import_cmd.py` |
| (new) | ChunkedItemsCache クラス | `src/etl/core/models.py` |
| (new) | run_with_skip() メソッド | Transform/Load Stage |

## チャンク処理の仕様

### 全チャンク成功必須（FR-011 準拠）

- チャンク分割されたアイテムは `parent_item_id` で元の会話を追跡
- 1つでも失敗したチャンクがあれば、**全チャンクを再処理対象**とする
- これにより、チャンク間の一貫性を保証

### データ構造

```jsonl
// pipeline_stages.jsonl のチャンクレコード例
{"item_id":"conv_chunk_0","is_chunked":true,"parent_item_id":"conv_original","chunk_index":0,"status":"success",...}
{"item_id":"conv_chunk_1","is_chunked":true,"parent_item_id":"conv_original","chunk_index":1,"status":"success",...}
{"item_id":"conv_chunk_2","is_chunked":true,"parent_item_id":"conv_original","chunk_index":2,"status":"failed",...}
```

### スキップ判定ロジック

```python
def is_parent_completed(parent_item_id: str) -> bool:
    """parent_item_id に紐づく全チャンクが成功しているか判定。"""
    all_chunks = parent_chunks.get(parent_item_id, set())
    successful_chunks = chunk_success.get(parent_item_id, set())
    return all_chunks == successful_chunks and len(all_chunks) > 0
```
