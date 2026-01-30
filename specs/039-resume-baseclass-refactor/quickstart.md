# Quickstart: Resume機能の基底クラス集約リファクタリング

**Branch**: `039-resume-baseclass-refactor` | **Date**: 2026-01-27

## 概要

このリファクタリングにより、Resume機能が `BaseStage` に集約され、継承クラスの実装が簡素化されます。

## 主な変更点

### 1. ItemStatus.SKIPPED → ItemStatus.FILTERED

```python
# Before
from src.etl.core.status import ItemStatus
if not valid:
    item.status = ItemStatus.SKIPPED

# After
from src.etl.core.status import ItemStatus
if not valid:
    item.status = ItemStatus.FILTERED
```

### 2. run_with_skip() メソッドの廃止

継承クラスで `run_with_skip()` を実装する必要がなくなりました。
`BaseStage.run()` が自動的にResume処理を行います。

```python
# Before: 継承クラスで独自実装が必要だった
class MyTransformer(BaseStage):
    def run_with_skip(self, ctx, items):
        # Resume logic here...
        pass

# After: BaseStageを継承するだけでOK
class MyTransformer(BaseStage):
    @property
    def steps(self) -> list[BaseStep]:
        return [MyStep()]
```

### 3. Resume時の動作変更

| 項目 | Before | After |
|------|--------|-------|
| スキップアイテムのステータス | `SKIPPED` に変更 | 変更なし |
| スキップアイテムのyield | あり | なし（フィルタで除外） |
| ログ記録 | `pipeline_stages.jsonl` に記録 | 記録なし |

## Resume機能の使用方法

### 中断からの再開

```bash
# 前回中断したセッションを再開
make import INPUT=... SESSION=20260127_123456
```

### 進捗表示

Resume開始時に以下のような表示が出ます：

```
Resume mode: 700/1000 items already completed, starting from item 701
```

### 前提条件

- Extract stageが完了していること
- 未完了の場合はエラー終了

```
Error: Extract stage not completed. Cannot resume.
```

## テストの実行

```bash
# 全テスト実行
make test

# Resume関連テストのみ
cd src/etl && python -m unittest tests.test_resume_mode -v
```

## マイグレーションチェックリスト

- [ ] `ItemStatus.SKIPPED` を `ItemStatus.FILTERED` に置換
- [ ] `run_with_skip()` メソッドを削除（継承クラス）
- [ ] テストコードの `SKIPPED` 参照を更新
- [ ] Resume時のアサーションを更新（yield数の変更）
