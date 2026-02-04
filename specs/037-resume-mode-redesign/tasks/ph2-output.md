# Phase 2 Output

## 作業概要
- Phase 2 - Foundational (CompletedItemsCache) の実装完了
- FAIL テスト 14 件を PASS させた
- CompletedItemsCache クラスを実装し、pipeline_stages.jsonl から処理済みアイテムを読み込む機能を実装

## 修正ファイル一覧
- `src/etl/core/models.py` - CompletedItemsCache クラスを追加
  - from_jsonl() classmethod: JSONL ファイルから status="success" アイテムを読み込み
  - is_completed() method: アイテムが処理済みか判定
  - __len__() method: 完了アイテム数を返す

## 実装詳細

### CompletedItemsCache クラス

```python
@dataclass
class CompletedItemsCache:
    """Cache for completed items in Resume mode.

    Reads status="success" items from pipeline_stages.jsonl
    and stores them by stage for skip determination.
    """

    items: set[str]
    stage: StageType

    @classmethod
    def from_jsonl(cls, jsonl_path: Path, stage: StageType) -> "CompletedItemsCache":
        """Load completed items from pipeline_stages.jsonl."""
        # JSONL 読み込み、stage + status フィルタ、エラーハンドリング実装

    def is_completed(self, item_id: str) -> bool:
        """Check if item is completed."""
        return item_id in self.items

    def __len__(self) -> int:
        """Return number of completed items."""
        return len(self.items)
```

### フィルタロジック

1. JSONL ファイルを1行ずつ読み込み
2. JSON パース（失敗時は警告ログを出力してスキップ）
3. stage == StageType.value でフィルタ
4. status == "success" でフィルタ
5. item_id を items セットに追加

### エッジケース対応

- **非存在ファイル**: 空のキャッシュを返す（例外を投げない）
- **空ファイル**: 空のキャッシュを返す
- **破損 JSON 行**: 警告ログを出力してスキップ
- **必須フィールド欠損**: 警告ログを出力してスキップ（item_id, status, stage）
- **空行**: 自動的にスキップ

## テスト結果

全 14 テストが PASS:

| Test Class | Test Count | Status |
|-----------|-----------|--------|
| TestCompletedItemsCacheEmpty | 3 | PASS |
| TestCompletedItemsCacheWithSuccess | 2 | PASS |
| TestCompletedItemsCacheIgnoresFailed | 2 | PASS |
| TestCompletedItemsCacheStageFilter | 3 | PASS |
| TestCompletedItemsCacheCorruptedJsonl | 4 | PASS |

```bash
$ python -m pytest src/etl/tests/test_resume_mode.py -v
============================== test session starts ==============================
collected 14 items

src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheEmpty::test_empty_jsonl_returns_empty_cache PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheEmpty::test_is_completed_returns_false_for_empty_cache PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheEmpty::test_nonexistent_jsonl_returns_empty_cache PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheWithSuccess::test_cache_contains_success_items PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheWithSuccess::test_cache_items_set_contains_correct_ids PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheIgnoresFailed::test_failed_items_not_in_cache PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheIgnoresFailed::test_mixed_statuses_only_includes_success PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheStageFilter::test_stage_filter_combined_with_status_filter PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheStageFilter::test_stage_filter_load_only PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheStageFilter::test_stage_filter_transform_only PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheCorruptedJsonl::test_corrupted_line_skipped_valid_lines_parsed PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheCorruptedJsonl::test_empty_lines_skipped PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheCorruptedJsonl::test_missing_required_fields_skipped PASSED
src/etl/tests/test_resume_mode.py::TestCompletedItemsCacheCorruptedJsonl::test_partially_corrupted_json_skipped PASSED

============================== 14 passed in 0.03s
```

## 次 Phase への引き継ぎ

### Phase 3 で使用するクラス

CompletedItemsCache は以下の場所で使用される:

1. **Transform Stage**: 処理済みアイテムをスキップ
2. **Load Stage**: 処理済みアイテムをスキップ
3. **Extract Stage**: Stage 単位でスキップ（CompletedItemsCache は使用しない）

### 統合ポイント

Phase 3 では以下を実装:

1. StageContext に `completed_cache: CompletedItemsCache | None` フィールドを追加
2. Resume モード時に `pipeline_stages.jsonl` から CompletedItemsCache を生成
3. Transform/Load Stage でアイテム処理前に `cache.is_completed(item_id)` でスキップ判定
4. スキップされたアイテムは pipeline_stages.jsonl に記録しない（FR-007）

### データフロー

```
pipeline_stages.jsonl
    │
    ▼
CompletedItemsCache.from_jsonl()
    │ set[item_id] (status="success" のみ)
    │
    ▼
Transform/Load Stage
    │ if cache and cache.is_completed(item_id): skip
    │ else: process → StageLogRecord
    ▼
Console Output: "5 success, 2 failed, 3 skipped"
```

## 実装のミス・課題

特になし。すべてのテストが PASS し、エッジケースにも対応できている。
