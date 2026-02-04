# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - 後方互換性検証 (US3)
- テスト数: 7 (全て PASS)
- テストファイル: src/etl/tests/test_knowledge_extractor.py
- RED 状態: **GREEN** -- Phase 2 実装が既に後方互換性を維持しており、新テストは即座に PASS した

## 状態の説明

Phase 3 の統合テストは、Phase 2 で実装された `parse_markdown_response()` + `KnowledgeDocument.to_markdown()` のフローが従来と同じ出力フォーマットを生成することを検証する。

テスト実装の結果、7 テスト全てが即座に PASS した。これは Phase 2 の実装が正しく後方互換性を維持していることを示す。RED フェーズとしての FAIL は発生しなかったが、これらのテストは回帰テストとして有効であり、今後の変更に対する安全ネットとなる。

## テスト一覧

| テストファイル | テストメソッド | 期待動作 | 結果 |
|---------------|---------------|---------|------|
| test_knowledge_extractor.py | test_to_markdown_has_valid_frontmatter | frontmatter に title/summary/created/source_provider/source_conversation が含まれる | PASS |
| test_knowledge_extractor.py | test_to_markdown_heading_normalization | summary_content 内の ### が #### に正規化される | PASS |
| test_knowledge_extractor.py | test_to_markdown_no_h1_duplication | 本文に H1 見出しが存在しない（frontmatter の title と重複しない） | PASS |
| test_knowledge_extractor.py | test_to_markdown_complete_format | frontmatter + 本文の完全なフォーマットが期待通り | PASS |
| test_knowledge_extractor.py | test_to_markdown_with_code_block_in_content | コードブロックを含む内容が正しく出力される | PASS |
| test_knowledge_extractor.py | test_to_markdown_with_english_summary_translation | 英語サマリー翻訳フロー経由でも出力が正しい | PASS |
| test_knowledge_extractor.py | test_to_markdown_with_unicode_content | Unicode/日本語コンテンツが正しく処理される | PASS |

## テストクラス

`TestMarkdownResponseToMarkdownOutput` -- 7 メソッド

End-to-end フロー検証:
1. Mock LLM がマークダウンレスポンスを返す
2. `KnowledgeExtractor.extract()` が `parse_markdown_response()` で処理
3. `KnowledgeDocument.to_markdown()` が正しい出力フォーマットを生成

## 実装ヒント

Phase 2 実装が既に後方互換のため、Phase 3 の GREEN 実装は不要。テストが回帰テストとして機能する。

もし将来テストが FAIL する場合:
- `src/etl/utils/ollama.py` の `parse_markdown_response()` が返す dict のキー/値を確認
- `src/etl/utils/knowledge_extractor.py` の `_build_document()` が dict から `KnowledgeDocument` を構築する処理を確認
- `KnowledgeDocument.to_markdown()` と `_normalize_summary_headings()` の見出し正規化ロジックを確認

## テスト実行結果

```
test_to_markdown_complete_format ... ok
test_to_markdown_has_valid_frontmatter ... ok
test_to_markdown_heading_normalization ... ok
test_to_markdown_no_h1_duplication ... ok
test_to_markdown_with_code_block_in_content ... ok
test_to_markdown_with_english_summary_translation ... ok
test_to_markdown_with_unicode_content ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.002s

OK
```
