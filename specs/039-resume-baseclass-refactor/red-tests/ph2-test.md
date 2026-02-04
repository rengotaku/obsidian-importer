# Phase 2 RED Tests

## サマリー
- Phase: Phase 2 - User Story 1: 中断からの再開（Resume Mode）
- FAIL テスト数: 2
- テストファイル: `src/etl/tests/test_resume_mode.py`

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/test_resume_mode.py | TestResumeAllCompleted.test_resume_all_completed | Resume時、全アイテム処理済みなら results は空（0件） |
| tests/test_resume_mode.py | TestSkipSuccessRetryFailed.test_skip_success_retry_failed | Resume時、処理済み3件はフィルタされ results は2件のみ |

## 実装ヒント

### 現在の実装（BaseStage.run() 304-316行目）

```python
# Resume mode: Skip already processed items (completed_cache check)
if ctx.completed_cache:
    skipped_items: list[ProcessingItem] = []
    items_to_process: list[ProcessingItem] = []
    for item in items:
        if ctx.completed_cache.is_completed(item.item_id):
            item.status = ItemStatus.FILTERED           # <- 削除
            item.metadata["skipped_reason"] = "resume_mode"  # <- 削除
            skipped_items.append(item)                 # <- 削除
        else:
            items_to_process.append(item)
    yield from skipped_items  # <- 削除
    items = iter(items_to_process)
```

### 期待される実装

```python
# Resume mode: Filter out already completed items (no yield, no status change)
if ctx.completed_cache:
    items = (item for item in items
             if not ctx.completed_cache.is_completed(item.item_id))
```

### 変更点

| 項目 | Before | After |
|------|--------|-------|
| スキップアイテムの yield | あり | なし |
| ステータス変更 | FILTERED に変更 | 変更なし |
| メタデータ追加 | skipped_reason 追加 | 追加なし |
| 処理方式 | リスト作成 + yield | ジェネレータでフィルタのみ |

### ResumableStage.run() も同様に修正が必要

`ResumableStage.run()` (1016-1067行目) も同様のロジックを持つため、同じ修正が必要。

```python
# 現在の実装（削除すべき部分）
if ctx.completed_cache:
    skipped_items: list[ProcessingItem] = []
    items_to_process: list[ProcessingItem] = []

    for item in items:
        if ctx.completed_cache.is_completed(item.item_id):
            # Mark as skipped and collect
            item.status = ItemStatus.FILTERED  # <- 削除
            skipped_items.append(item)
        else:
            items_to_process.append(item)

    # Yield skipped items first (without logging)
    yield from skipped_items  # <- 削除

    # Process non-skipped items
    items = iter(items_to_process)
```

## FAIL 出力例

```
======================================================================
FAIL: test_resume_all_completed (src.etl.tests.test_resume_mode.TestResumeAllCompleted.test_resume_all_completed)
全アイテム処理済みの場合、全てフィルタされ結果は空。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_resume_mode.py", line 1192, in test_resume_all_completed
    self.assertEqual(len(results), 0)
AssertionError: 5 != 0

======================================================================
FAIL: test_skip_success_retry_failed (src.etl.tests.test_resume_mode.TestSkipSuccessRetryFailed.test_skip_success_retry_failed)
3件成功、2件失敗のログ: 成功3件はフィルタされ、失敗2件のみ再処理。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_resume_mode.py", line 1399, in test_skip_success_retry_failed
    self.assertEqual(len(results), 2)
AssertionError: 5 != 2

----------------------------------------------------------------------
Ran 2 tests in 0.002s

FAILED (failures=2)
```

## 修正対象ファイル

1. `src/etl/core/stage.py`
   - `BaseStage.run()` (行 304-316): Resume ロジック簡素化
   - `ResumableStage.run()` (行 1039-1055): 同様に簡素化

## 技術的注意点

- ジェネレータ式を使用することでメモリ効率が向上
- 処理済みアイテムは呼び出し元に一切返さない
- ステータス変更しないため、元のアイテム状態が保持される
- `limit` 適用はフィルタ後に行う（現在の実装と同じ）
