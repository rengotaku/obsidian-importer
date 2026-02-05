# Phase 3 RED Tests - 検証テスト（RED 省略）

## サマリー

- Phase: Phase 3 - User Story 1 (パイプライン最終出力のゴールデンファイル比較)
- RED 状態: **省略**
- 理由: golden_comparator は動的に key をチェックするため、新しいフィールド追加でもテストは PASS する
- テストファイル: `tests/e2e/test_golden_comparator.py`

## 変更内容

### SAMPLE_GOLDEN 更新

SAMPLE_GOLDEN および関連サンプルに `summary`, `genre`, `topic` フィールドを追加:

```yaml
---
title: Python asyncio discussion
created: 2026-01-15
tags:
  - python
  - asyncio
source_provider: claude
file_id: a1b2c3d4e5f6
normalized: true
summary: Pythonの非同期処理ライブラリasyncioについて、イベントループ、コルーチン、タスクの基礎を解説。
genre: engineer
topic: python
---
```

### 新規テストメソッド

| テストメソッド | 目的 | ステータス |
|---------------|------|-----------|
| `test_frontmatter_similarity_with_genre_topic` | genre, topic が key existence チェックに含まれることを確認 | PASS |
| `test_frontmatter_similarity_with_empty_topic` | 空 topic でも正しく類似度計算されることを確認 | PASS |

### 更新テストメソッド

| テストメソッド | 変更内容 | ステータス |
|---------------|---------|-----------|
| `test_frontmatter_keys_preserved` | expected_keys に `summary`, `genre`, `topic` を追加 | PASS |

### 新規サンプル定数

- `SAMPLE_WITH_EMPTY_TOPIC`: 空 topic のサンプル
- `SAMPLE_GOLDEN_WITH_EMPTY_TOPIC`: 空 topic の golden サンプル

## テスト実行結果

```
$ .venv/bin/python -m unittest tests.e2e.test_golden_comparator -v

test_frontmatter_similarity_with_empty_topic ... ok
test_frontmatter_similarity_with_genre_topic ... ok
test_frontmatter_keys_preserved ... ok
... (他 37 件も全て OK)

----------------------------------------------------------------------
Ran 40 tests in 0.028s

OK
```

## RED 省略の理由

golden_comparator の `calculate_frontmatter_similarity` 関数は動的に key をチェックする設計:

```python
# Key existence (30% weight)
golden_keys = set(golden.keys())
actual_keys = set(actual.keys())
key_match_ratio = len(actual_keys & golden_keys) / len(golden_keys) if golden_keys else 1.0
```

この設計により、SAMPLE_GOLDEN に新しいフィールド（`genre`, `topic`, `summary`）を追加しても：
- 実装変更なしで新フィールドが key existence チェックに自動的に含まれる
- テストは PASS する（RED 状態が発生しない）

## 次ステップ

Phase 3 実装 (GREEN) で以下を実行:
1. Makefile の `test-e2e` ターゲット更新（`--to-nodes=format_markdown` 削除）
2. 出力ディレクトリを `data/07_model_output/organized` に変更
3. `make test` で全テスト PASS 確認
