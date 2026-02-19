# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - US3 既存分類との後方互換性
- テスト数: 4
- 結果: PASS (後方互換性が確認された)
- テストファイル: tests/pipelines/organize/test_nodes.py
- 全テスト数: 398 (394 既存 + 4 新規)

## テスト一覧

| テストファイル | テストメソッド | 期待動作 | 結果 |
|---------------|---------------|---------|------|
| tests/pipelines/organize/test_nodes.py | test_classify_genre_engineer_unchanged | engineer キーワードのみ(プログラミング)で engineer に分類 | PASS |
| tests/pipelines/organize/test_nodes.py | test_classify_genre_business_unchanged | business キーワードのみ(マネジメント)で business に分類 | PASS |
| tests/pipelines/organize/test_nodes.py | test_classify_genre_economy_unchanged | economy キーワードのみ(投資)で economy に分類 | PASS |
| tests/pipelines/organize/test_nodes.py | test_classify_genre_daily_unchanged | daily キーワードのみ(日常)で daily に分類 | PASS |

## テスト設計

各テストは以下の原則に従って設計:

1. **単一ジャンルキーワードのみ使用**: 新しい高優先度ジャンル(ai, devops)と重複しないキーワードを使用
2. **コンテンツとタグの両方を設定**: frontmatter の tags とコンテンツ本文の両方にキーワードを含める
3. **具体的な期待値**: `assertEqual(genre, "engineer")` のように明確なアサーション

### キーワード選択の根拠

| ジャンル | 使用キーワード | 除外した重複キーワード |
|---------|---------------|---------------------|
| engineer | プログラミング | API(devops の AWS と混同しない), DevOps(devops ジャンルと重複) |
| business | マネジメント | 重複なし |
| economy | 投資 | 重複なし |
| daily | 日常 | 重複なし |

## PASS の理由

Phase 2 の実装で:
- 既存4ジャンルのキーワードは変更されていない
- 優先順位変更は **複数ジャンルにマッチする場合のみ** 影響する
- 単一ジャンルのみにマッチするケースでは従来通りの分類結果が維持される

## 実装ヒント (GREEN フェーズ)

テストが既に PASS しているため、GREEN フェーズでは:
1. 追加の実装変更は不要
2. 既存テストの期待値更新も不要
3. 全 398 テストが PASS することの確認のみ

## make test 出力

```
Ran 398 tests in 5.567s

OK
```
