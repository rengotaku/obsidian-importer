# Phase 1 Output: Setup

## 作業概要

Phase 1 では既存実装の確認と変更準備を行った。

## 確認結果

### 1. classify_genre 関数 (src/obsidian_etl/pipelines/organize/nodes.py:57-175)

**現状の問題点**:
- 優先順位がハードコード: `["engineer", "business", "economy", "daily"]`
- 新ジャンル追加には関数修正が必要

**変更箇所**:
```python
# Before (ハードコード)
for genre_name in ["engineer", "business", "economy", "daily"]:

# After (設定から取得)
genre_priority = params.get("genre_priority", ["engineer", "business", "economy", "daily"])
for genre_name in genre_priority:
```

### 2. parameters.yml (conf/base/parameters.yml:61-85)

**現状**:
- 4ジャンルのキーワードのみ定義: engineer, business, economy, daily
- genre_priority リストなし

**追加必要**:
- 6新ジャンルのキーワード: ai, devops, health, parenting, travel, lifestyle
- genre_priority リスト

### 3. テストファイル (tests/pipelines/organize/test_nodes.py)

**現状**:
- `TestClassifyGenre`: 4ジャンルのテスト
- `TestClassifyGenreDefault`: 'other' フォールバックテスト
- `_make_organize_params()`: 4ジャンルのみ定義

**追加必要**:
- 新ジャンルのテスト
- 優先順位テスト
- `_make_organize_params()` の更新

## 修正ファイル一覧

なし（Phase 1 は読み取りのみ）

## テスト結果

```
Ran 386 tests in 8.579s
OK
```

## 注意点

1. **キーワード設計**: research.md に定義済み（日本語・英語両方）
2. **優先順位**: ai → devops → engineer → economy → business → health → parenting → travel → lifestyle → daily → other
3. **後方互換性**: 既存4ジャンルのキーワードは変更しない

## 次の Phase へのインプット

- Phase 2 では TDD フローで新ジャンルを実装
- テストファーストで RED 状態を作成後、実装
