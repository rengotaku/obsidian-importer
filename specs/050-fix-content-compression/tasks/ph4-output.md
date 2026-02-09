# Phase 4 Output

## 作業概要
- Phase 4 - extract_knowledge 修正 (User Story 2) の実装完了
- FAIL テスト 1 件を PASS させた (GREEN)
- `extract_knowledge` node に圧縮率検証を統合し、基準未達アイテムに `review_reason` を付与

## 修正ファイル一覧
- `src/obsidian_etl/pipelines/transform/nodes.py` - 既存ファイル修正
  - `compression_validator` モジュールを import
  - 既存の ratio チェックロジック (lines 154-166) を `validate_compression()` 呼び出しに置き換え
  - 基準未達時に `review_reason` フィールドを item に追加（除外しない）
  - `continue` 文を削除し、処理を継続するように変更

## 実装内容

### Before (lines 154-166)
```python
# Check content compression ratio (detect abnormal shrinkage)
original_len = len(item["content"])
output_len = len(summary_content)
if original_len > 0:
    ratio = output_len / original_len * 100
    min_ratio = params.get("transform", {}).get("min_content_ratio", 5.0)
    if ratio < min_ratio:
        logger.warning(
            f"Low content ratio ({ratio:.1f}% < {min_ratio}%) for {partition_id}: "
            f"{original_len} -> {output_len} chars. Item excluded."
        )
        skipped_empty += 1
        continue  # ← 問題: 基準未達でアイテムを除外していた
```

### After (lines 154-174)
```python
# Check content compression ratio using compression_validator
compression_result = validate_compression(
    original_content=item["content"],
    output_content=summary_content,
    body_content=summary_content,  # For extract_knowledge, body = summary_content
    node_name="extract_knowledge",
)

if not compression_result.is_valid:
    # Add review_reason to item (don't exclude)
    review_reason = (
        f"{compression_result.node_name}: "
        f"body_ratio={compression_result.body_ratio:.1%} < "
        f"threshold={compression_result.threshold:.1%}"
    )
    item["review_reason"] = review_reason
    logger.warning(
        f"Low content ratio for {partition_id}: {review_reason}. "
        f"Item marked for review."
    )
    # DO NOT continue - process the item normally
```

## 主要な変更点

1. **圧縮率検証ロジックの置き換え**
   - 旧: 固定しきい値 `min_content_ratio=5.0%` でチェック
   - 新: `compression_validator.get_threshold()` で元サイズに応じた動的しきい値を適用
     - 10,000+ chars: 10%
     - 5,000-9,999 chars: 15%
     - <5,000 chars: 20%

2. **基準未達時の動作変更**
   - 旧: アイテムを除外 (`continue`)
   - 新: `review_reason` フィールドを追加し、処理を継続

3. **review_reason フォーマット**
   - 形式: `"node_name: body_ratio=X.X% < threshold=Y.Y%"`
   - 例: `"extract_knowledge: body_ratio=5.0% < threshold=10.0%"`

## テスト結果
```
test_extract_knowledge_adds_review_reason ... ok
test_extract_knowledge_no_review_reason_when_valid ... ok

----------------------------------------------------------------------
Ran 306 tests in 0.812s

OK (PASS: 306)
```

全テストが PASS (GREEN) を達成。レグレッションなし。

## 注意点
- `review_reason` は item 直下に追加（`generated_metadata` ではない）
- 既存の `skipped_empty` カウンターは圧縮率チェックでは増加しなくなった
- 警告ログは引き続き出力されるが、アイテムは除外されない

## 実装のミス・課題
特になし。

## 次 Phase への引き継ぎ
- Phase 5: レビューフォルダ出力の実装
- `review_reason` を持つアイテムを `data/07_model_output/review/` に出力
- `format_markdown` node を修正し、通常 notes と review notes の2系統出力を実装
- `embed_frontmatter_fields` node を修正し、review_reason を frontmatter に埋め込み
