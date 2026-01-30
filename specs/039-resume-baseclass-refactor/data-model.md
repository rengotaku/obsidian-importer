# Data Model: Resume機能の基底クラス集約リファクタリング

**Branch**: `039-resume-baseclass-refactor` | **Date**: 2026-01-27

## エンティティ変更

### ItemStatus (Enum) - 変更

**ファイル**: `src/etl/core/status.py`

| 変更前 | 変更後 | 説明 |
|--------|--------|------|
| `SKIPPED = "skipped"` | `FILTERED = "filtered"` | バリデーション失敗等で処理対象外となったアイテム |

```python
class ItemStatus(Enum):
    """Processing item status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    FILTERED = "filtered"  # 変更: SKIPPED → FILTERED
```

### StageLogRecord - 変更

**ファイル**: `src/etl/core/models.py`

`status` フィールドの有効値に `"filtered"` を追加（`"skipped"` を置換）。

---

## クラス変更

### BaseStage - 変更

**ファイル**: `src/etl/core/stage.py`

#### run() メソッドの変更

**削除**: Resume時のスキップアイテムyield処理

```python
# 削除対象（301-315行目付近）
if ctx.completed_cache:
    skipped_items: list[ProcessingItem] = []
    items_to_process: list[ProcessingItem] = []
    for item in items:
        if ctx.completed_cache.is_completed(item.item_id):
            item.status = ItemStatus.SKIPPED  # ← 削除
            item.metadata["skipped_reason"] = "resume_mode"  # ← 削除
            skipped_items.append(item)  # ← 削除
        else:
            items_to_process.append(item)
    yield from skipped_items  # ← 削除
    items = iter(items_to_process)
```

**追加**: シンプルなフィルタリング

```python
# Resume mode: Filter out already completed items
if ctx.completed_cache:
    items = (item for item in items if not ctx.completed_cache.is_completed(item.item_id))
```

### KnowledgeTransformer - 変更

**ファイル**: `src/etl/stages/transform/knowledge_transformer.py`

**削除**: `run_with_skip()` メソッド (656-702行目)

### SessionLoader - 変更

**ファイル**: `src/etl/stages/load/session_loader.py`

**削除**: `run_with_skip()` メソッド (341-388行目)

---

## 関係図

```
┌─────────────────────────────────────────────────────────────────┐
│                          ImportPhase                             │
│                                                                  │
│  ┌─────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │   Extract   │ → │    Transform     │ → │      Load        │  │
│  │   Stage     │   │     Stage        │   │     Stage        │  │
│  └─────────────┘   └──────────────────┘   └──────────────────┘  │
│                                                                  │
│  Resume時: completed_cache で処理済みアイテムをフィルタ         │
│  （BaseStage.run() で一元管理）                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│    ItemStatus       │
├─────────────────────┤
│ PENDING             │
│ PROCESSING          │
│ COMPLETED           │
│ FAILED              │
│ FILTERED (変更)     │  ← validate_input失敗時等
└─────────────────────┘

┌─────────────────────────────────────┐
│       CompletedItemsCache           │
├─────────────────────────────────────┤
│ items: set[str]                     │  ← pipeline_stages.jsonl から読み込み
│ stage: StageType                    │
├─────────────────────────────────────┤
│ is_completed(item_id) → bool        │  ← Resume時のスキップ判定に使用
└─────────────────────────────────────┘
```

---

## 状態遷移図

### ProcessingItem.status

```
                    ┌─────────────┐
                    │   PENDING   │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  PROCESSING  │ │   FILTERED   │ │   (Resume)   │
    └──────┬───────┘ └──────────────┘ │  除外のみ    │
           │          validate_input  │ ステータス   │
           │          失敗時          │ 変更なし     │
    ┌──────┴──────┐                   └──────────────┘
    │             │
    ▼             ▼
┌──────────┐ ┌──────────┐
│COMPLETED │ │  FAILED  │
└──────────┘ └──────────┘
```

---

## バリデーションルール

### Resume前提条件

| 条件 | チェック方法 | エラー時の動作 |
|------|--------------|----------------|
| session.json存在 | `Path.exists()` | エラー終了 |
| expected_total_item_count設定 | `session.phases.get("import")` | エラー終了 |
| extract/output/にファイル存在 | `any(extract_output.iterdir())` | エラー終了 |

### ItemStatus.FILTERED の設定条件

- `step.validate_input(item)` が `False` を返した場合
- 継承Stepで明示的に処理対象外と判断した場合
