# Phase 3 RED Tests

## Summary
- Phase: Phase 3 - User Story 2: 継承クラスの実装簡素化
- FAIL テスト数: 2
- テストファイル: `src/etl/tests/test_resume_mode.py`

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_resume_mode.py | TestTransformItemSkip.test_run_with_skip_does_not_exist | `KnowledgeTransformer.run_with_skip()` が存在しないこと |
| test_resume_mode.py | TestLoadItemSkip.test_run_with_skip_does_not_exist | `SessionLoader.run_with_skip()` が存在しないこと |

## 変更されたテストメソッド

### TestTransformItemSkip (T022 -> T031)
**Before (削除)**:
- `test_transform_item_skip()` - `transformer.run_with_skip()` を呼び出してスキップ動作を確認

**After (追加)**:
- `test_run_with_skip_does_not_exist()` - `hasattr(transformer, "run_with_skip")` が False であることを確認

### TestLoadItemSkip (T023 -> T032)
**Before (削除)**:
- `test_load_item_skip()` - `loader.run_with_skip()` を呼び出してスキップ動作を確認

**After (追加)**:
- `test_run_with_skip_does_not_exist()` - `hasattr(loader, "run_with_skip")` が False であることを確認

## 実装ヒント

### GREEN phase で削除するメソッド:
1. `src/etl/stages/transform/knowledge_transformer.py` 行 657-702: `run_with_skip()` メソッドを削除
2. `src/etl/stages/load/session_loader.py` 行 342-388: `run_with_skip()` メソッドを削除

### 理由:
Phase 2 で `BaseStage.run()` に Resume ロジックが集約されたため、継承クラスの `run_with_skip()` メソッドは不要になりました。Resume 時のスキップは `BaseStage.run()` のジェネレータフィルタで処理されます。

## FAIL 出力例

```
FAIL: test_run_with_skip_does_not_exist (src.etl.tests.test_resume_mode.TestTransformItemSkip.test_run_with_skip_does_not_exist)
T031: run_with_skip() メソッドが KnowledgeTransformer に存在しないことを確認。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_resume_mode.py", line 772, in test_run_with_skip_does_not_exist
    self.assertFalse(
        hasattr(transformer, "run_with_skip"),
        "run_with_skip() should be removed from KnowledgeTransformer. "
        "Resume logic is now in BaseStage.run().",
    )
AssertionError: True is not false : run_with_skip() should be removed from KnowledgeTransformer. Resume logic is now in BaseStage.run().

======================================================================
FAIL: test_run_with_skip_does_not_exist (src.etl.tests.test_resume_mode.TestLoadItemSkip.test_run_with_skip_does_not_exist)
T032: run_with_skip() メソッドが SessionLoader に存在しないことを確認。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_resume_mode.py", line 799, in test_run_with_skip_does_not_exist
    self.assertFalse(
        hasattr(loader, "run_with_skip"),
        "run_with_skip() should be removed from SessionLoader. "
        "Resume logic is now in BaseStage.run().",
    )
AssertionError: True is not false : run_with_skip() should be removed from SessionLoader. Resume logic is now in BaseStage.run().

----------------------------------------------------------------------
Ran 2 tests in 0.026s

FAILED (failures=2)
```

## 技術的背景

### Phase 2 での変更（既に完了）
`BaseStage.run()` に Resume ロジックが集約されました:

```python
# Resume mode: Filter out already completed items (no yield, no status change)
if ctx.completed_cache:
    items = (item for item in items
             if not ctx.completed_cache.is_completed(item.item_id))
```

これにより、継承クラスは Resume を意識せずに `steps` プロパティのみを実装すれば、Resume 機能が自動で適用されます。

### Phase 3 の目標
継承クラス（`KnowledgeTransformer`, `SessionLoader`）から `run_with_skip()` メソッドを削除し、コードベースを簡素化します。
