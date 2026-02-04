# Phase 2 RED Tests

## サマリー
- Phase: Phase 2 - User Story 1 + 2 - マークダウンパーサー実装 & プロンプト変更
- FAIL テスト数: 23 メソッド (3 ERROR + 6 FAIL = 9 failures, 残り14は test_ollama.py の ImportError で全滅)
- テストファイル: 2 ファイル

## FAIL テスト一覧

### test_ollama.py (14 tests - 全て ImportError)

| テストクラス | テストメソッド | 期待動作 |
|-------------|---------------|---------|
| TestParseMarkdownResponseStandard | test_standard_three_section_markdown | 3セクションMD -> dict(title, summary, summary_content) |
| TestParseMarkdownResponseStandard | test_title_extracted_from_h1 | # 見出し -> title |
| TestParseMarkdownResponseStandard | test_summary_extracted_from_section | ## 要約 本文 -> summary |
| TestParseMarkdownResponseStandard | test_content_extracted_from_section | ## 内容 本文 -> summary_content |
| TestParseMarkdownResponseStandard | test_multiline_content_preserved | 複数行コンテンツ保持 |
| TestParseMarkdownResponseStandard | test_return_type_is_tuple | tuple[dict, str\|None] 型 |
| TestParseMarkdownResponseStandard | test_all_three_keys_present | 3キー存在確認 |
| TestParseMarkdownResponseStandard | test_unicode_content_preserved | 日英混在コンテンツ保持 |
| TestParseMarkdownResponseEdgeCases | test_code_block_fence_removal | ```markdown フェンス除去 |
| TestParseMarkdownResponseEdgeCases | test_code_block_fence_without_language | ``` フェンス除去 |
| TestParseMarkdownResponseEdgeCases | test_h2_as_title_when_no_h1 | H1なし -> ## をタイトルに |
| TestParseMarkdownResponseEdgeCases | test_h3_as_title_when_no_h1_h2 | ### をタイトルに |
| TestParseMarkdownResponseEdgeCases | test_plain_text_fallback | プレーンテキスト -> summary |
| TestParseMarkdownResponseEdgeCases | test_empty_input_returns_error | 空入力 -> エラー |
| TestParseMarkdownResponseEdgeCases | test_whitespace_only_input_returns_error | 空白のみ -> エラー |
| TestParseMarkdownResponseEdgeCases | test_none_input_returns_error | None -> エラー |
| TestParseMarkdownResponseEdgeCases | test_missing_summary_section_uses_default | ## 要約 なし -> 空文字 |
| TestParseMarkdownResponseEdgeCases | test_missing_content_section_uses_default | ## 内容 なし -> 空文字 |
| TestParseMarkdownResponseEdgeCases | test_missing_title_uses_default | タイトルなし -> 空文字 |
| TestParseMarkdownResponseEdgeCases | test_extra_whitespace_in_heading_stripped | 見出し空白除去 |
| TestParseMarkdownResponseEdgeCases | test_content_with_code_blocks_preserved | 内容内コードブロック保持 |
| TestParseMarkdownResponseSummaryTranslation | test_summary_only_markdown | ## 要約 のみ -> dict |
| TestParseMarkdownResponseSummaryTranslation | test_summary_only_with_multiline | 複数行要約抽出 |
| TestParseMarkdownResponseSummaryTranslation | test_summary_only_title_defaults_empty | 要約のみ -> title 空 |
| TestParseMarkdownResponseSummaryTranslation | test_summary_only_content_defaults_empty | 要約のみ -> content 空 |

### test_knowledge_extractor.py (12 tests - 3 ERROR + 6 FAIL + 3 PASS)

| テストクラス | テストメソッド | 期待動作 | 状態 |
|-------------|---------------|---------|------|
| TestKnowledgeExtractorExtractMarkdown | test_extract_with_markdown_response_returns_success | MD -> ExtractionResult(success=True) | FAIL |
| TestKnowledgeExtractorExtractMarkdown | test_extract_markdown_populates_summary | ## 要約 -> document.summary | FAIL |
| TestKnowledgeExtractorExtractMarkdown | test_extract_markdown_populates_summary_content | ## 内容 -> document.summary_content | FAIL |
| TestKnowledgeExtractorExtractMarkdown | test_extract_uses_parse_markdown_not_json | parse_markdown_response が呼ばれる | ERROR |
| TestKnowledgeExtractorExtractMarkdown | test_extract_markdown_parse_error_returns_failure | パースエラー -> success=False | FAIL |
| TestKnowledgeExtractorExtractMarkdown | test_extract_preserves_conversation_metadata | メタデータ保持 | FAIL |
| TestKnowledgeExtractorTranslateSummaryMarkdown | test_translate_summary_parses_markdown_response | MD翻訳 -> summary抽出 | FAIL |
| TestKnowledgeExtractorTranslateSummaryMarkdown | test_translate_summary_uses_parse_markdown | parse_markdown_response 使用 | ERROR |
| TestKnowledgeExtractorTranslateSummaryMarkdown | test_translate_summary_returns_error_on_parse_failure | パースエラー -> error | PASS |
| TestKnowledgeExtractorTranslateSummaryMarkdown | test_translate_summary_returns_error_on_api_failure | API エラー -> error | PASS |
| TestKnowledgeExtractorTranslateSummaryMarkdown | test_translate_summary_with_multiline_markdown | 複数行MD翻訳 | FAIL |

## 実装ヒント

### parse_markdown_response() (src/etl/utils/ollama.py)

```python
def parse_markdown_response(response: str) -> tuple[dict, str | None]:
    """
    マークダウンレスポンスを構造化 dict に変換。

    処理手順:
    1. 空入力チェック
    2. コードブロックフェンス除去 (```markdown ... ``` or ``` ... ```)
    3. 見出し検出 (#, ##, ###)
    4. セクション分割: title(#), summary(## 要約), content(## 内容)
    5. dict 構築

    Returns:
        tuple[dict, str | None]: (parsed dict, error_message or None)
    """
```

### knowledge_extractor.py の変更

- `from src.etl.utils.ollama import parse_json_response` を `parse_markdown_response` に変更
- `extract()` 内の `parse_json_response(response)` を `parse_markdown_response(response)` に変更
- `translate_summary()` 内の同様の呼び出しも変更
- 戻り値の型が同じ `tuple[dict, str | None]` なのでエラー処理コードは変更不要

## FAIL 出力例

```
ERROR: test_ollama (unittest.loader._FailedTest.test_ollama)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_ollama
  File "/path/to/project/src/etl/tests/test_ollama.py", line 11, in <module>
    from src.etl.utils.ollama import parse_markdown_response
ImportError: cannot import name 'parse_markdown_response' from 'src.etl.utils.ollama'

FAIL: test_extract_with_markdown_response_returns_success
----------------------------------------------------------------------
AssertionError: False is not true
  (parse_json_response cannot parse markdown -> success=False)

FAIL: test_translate_summary_parses_markdown_response
----------------------------------------------------------------------
AssertionError: 'JSON形式の応答がありません' is not None
  (parse_json_response returns error for markdown input)

ERROR: test_extract_uses_parse_markdown_not_json
----------------------------------------------------------------------
AttributeError: src.etl.utils.knowledge_extractor does not have the attribute 'parse_markdown_response'
  (parse_markdown_response is not yet imported in knowledge_extractor.py)
```
