# Phase 2 RED Tests

## サマリー
- Phase: Phase 2 - US1+US2 新ジャンル追加とキーワードマッピング
- FAIL テスト数: 8
- テストファイル: tests/pipelines/organize/test_nodes.py
- 既存テスト: 6 PASS (regression なし)
- 全体: 394 tests, 8 failures

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/organize/test_nodes.py | test_classify_genre_ai | AI キーワード (ChatGPT, LLM, 生成AI) が 'ai' に分類される |
| tests/pipelines/organize/test_nodes.py | test_classify_genre_devops | DevOps キーワード (Docker, コンテナ, インフラ) が 'devops' に分類される |
| tests/pipelines/organize/test_nodes.py | test_classify_genre_lifestyle | lifestyle キーワード (家電, 電子レンジ) が 'lifestyle' に分類される |
| tests/pipelines/organize/test_nodes.py | test_classify_genre_parenting | parenting キーワード (子育て, 育児, 赤ちゃん) が 'parenting' に分類される |
| tests/pipelines/organize/test_nodes.py | test_classify_genre_travel | travel キーワード (旅行, 観光) が 'travel' に分類される |
| tests/pipelines/organize/test_nodes.py | test_classify_genre_health | health キーワード (健康, フィットネス, 運動) が 'health' に分類される |
| tests/pipelines/organize/test_nodes.py | test_classify_genre_priority_ai_over_engineer | ai + engineer 両方マッチ時に ai が優先される |
| tests/pipelines/organize/test_nodes.py | test_classify_genre_priority_devops_over_engineer | devops + engineer 両方マッチ時に devops が優先される |

## FAIL 原因

全て同じ根本原因: `classify_genre` 関数の優先順位リストがハードコードされている。

```python
# src/obsidian_etl/pipelines/organize/nodes.py:148, 161
for genre_name in ["engineer", "business", "economy", "daily"]:
```

- 新ジャンル (ai, devops, health, parenting, travel, lifestyle) がイテレーション対象に含まれない
- params に `genre_priority` リストがあっても無視される
- 結果: 新ジャンルのキーワードは params に存在しても、マッチングループに入らず 'other' または既存ジャンルに分類される

## 実装ヒント

1. `src/obsidian_etl/pipelines/organize/nodes.py` の `classify_genre` 関数内:
   - ハードコードされた `["engineer", "business", "economy", "daily"]` を `params.get("genre_priority", [...])` に変更
   - 2箇所 (tags マッチングとcontent マッチング) とも変更が必要

2. `conf/base/parameters.yml` に:
   - 6 新ジャンルのキーワードを追加 (ai, devops, health, parenting, travel, lifestyle)
   - `genre_priority` リストを追加

## FAIL 出力例

```
FAIL: test_classify_genre_ai (tests.pipelines.organize.test_nodes.TestClassifyGenre)
AI関連のタグ/コンテンツが 'ai' に分類されること。
AssertionError: 'other' != 'ai'

FAIL: test_classify_genre_priority_ai_over_engineer (tests.pipelines.organize.test_nodes.TestClassifyGenre)
AI と engineer の両方にマッチする場合、ai が優先されること。
AssertionError: 'engineer' != 'ai'

FAIL: test_classify_genre_priority_devops_over_engineer (tests.pipelines.organize.test_nodes.TestClassifyGenre)
DevOps と engineer の両方にマッチする場合、devops が優先されること。
AssertionError: 'engineer' != 'devops'
```

## テスト変更の詳細

### _make_organize_params() の更新
- 6 新ジャンルのキーワードを `genre_keywords` に追加
- `genre_priority` リストを追加: `[ai, devops, engineer, economy, business, health, parenting, travel, lifestyle, daily]`

### 8 新テストメソッド (TestClassifyGenre クラス内)
- `test_classify_genre_ai`: tags=["ChatGPT", "LLM", "生成AI"]
- `test_classify_genre_devops`: tags=["Docker", "コンテナ", "インフラ"]
- `test_classify_genre_lifestyle`: tags=["家電", "電子レンジ"]
- `test_classify_genre_parenting`: tags=["子育て", "育児", "赤ちゃん"]
- `test_classify_genre_travel`: tags=["旅行", "観光"]
- `test_classify_genre_health`: tags=["健康", "フィットネス", "運動"]
- `test_classify_genre_priority_ai_over_engineer`: tags=["Claude", "プログラミング"] -> ai
- `test_classify_genre_priority_devops_over_engineer`: tags=["AWS", "API"] -> devops
