# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - User Story 3 (other 分類の改善サイクル)
- FAIL テスト数: 11
- テストファイル: tests/pipelines/organize/test_nodes.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/organize/test_nodes.py | test_analyze_other_genres_trigger | other 5件以上で analyze_other_genres がトリガーされ提案を返す |
| tests/pipelines/organize/test_nodes.py | test_analyze_other_genres_below_threshold | other 4件以下で提案なしメッセージを返す |
| tests/pipelines/organize/test_nodes.py | test_analyze_other_genres_zero_other | other 0件で提案なしメッセージを返す |
| tests/pipelines/organize/test_nodes.py | test_analyze_other_genres_exactly_five | other ちょうど5件でトリガーされる |
| tests/pipelines/organize/test_nodes.py | test_generate_genre_suggestions_md_format | Markdown 形式の提案レポートを正しく生成 |
| tests/pipelines/organize/test_nodes.py | test_generate_genre_suggestions_md_yaml_example | YAML 設定例を含む |
| tests/pipelines/organize/test_nodes.py | test_generate_genre_suggestions_md_empty_suggestions | 空の提案で提案なしメッセージ |
| tests/pipelines/organize/test_nodes.py | test_generate_genre_suggestions_md_sample_titles_max_five | sample_titles 5件表示 |
| tests/pipelines/organize/test_nodes.py | test_suggest_genre_with_llm_returns_suggestions | LLM が GenreSuggestion リストを返す |
| tests/pipelines/organize/test_nodes.py | test_suggest_genre_with_llm_error_returns_empty | LLM エラー時に空リストを返す |
| tests/pipelines/organize/test_nodes.py | test_suggest_genre_with_llm_invalid_json_returns_empty | 不正 JSON で空リストを返す |

## 実装ヒント

- `src/obsidian_etl/pipelines/organize/nodes.py` に以下を実装:
  - `analyze_other_genres(partitioned_input: dict[str, Callable], params: dict) -> str` - other 分析ノード
  - `_suggest_new_genres_via_llm(other_items: list[dict], params: dict) -> list[dict]` - LLM による新ジャンル提案
  - `_generate_suggestions_markdown(suggestions: list[dict], other_count: int) -> str` - Markdown レポート生成
- `analyze_other_genres` は partitioned_input から other 分類アイテムを抽出し、5件以上なら LLM に提案を依頼
- `_generate_suggestions_markdown` は data-model.md の genre_suggestions.md フォーマットに準拠
- GenreSuggestion 構造: `{"suggested_genre", "suggested_description", "sample_titles", "content_count"}`

## FAIL 出力例
```
FAIL: test_analyze_other_genres_trigger (tests.pipelines.organize.test_nodes.TestAnalyzeOtherGenres)
analyze_other_genres is not yet implemented (RED)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/pipelines/organize/test_nodes.py", line 1355, in setUp
    self.fail("analyze_other_genres is not yet implemented (RED)")
AssertionError: analyze_other_genres is not yet implemented (RED)
```

## テスト実行結果
```
Ran 54 tests in 0.007s
FAILED (failures=11)
```

- 既存テスト 43 件: 全て PASS (回帰なし)
- 新規テスト 11 件: 全て FAIL (RED)
