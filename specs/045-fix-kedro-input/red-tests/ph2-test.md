# Phase 2 RED Tests

## Summary
- Phase: Phase 2 - Claude/OpenAI ZIP Import (US2)
- FAIL test count: 23 (all ImportError: `parse_claude_zip` does not exist)
- PASS test count: 17 (BinaryDataset: 10, OpenAI fixture: 7 -- pre-existing implementations)
- Test files:
  - `tests/test_datasets.py` (new, 10 tests, PASS)
  - `tests/pipelines/extract_claude/test_nodes.py` (modified, +23 tests, ERROR)
  - `tests/pipelines/extract_openai/test_nodes.py` (modified, +7 tests, PASS)

## FAIL test list

| Test file | Test method | Expected behavior |
|-----------|------------|-------------------|
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipBasic.test_parse_claude_zip_returns_dict | parse_claude_zip が dict を返す |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipBasic.test_parse_claude_zip_item_count | 2 会話から 2 ParsedItem |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipBasic.test_parse_claude_zip_parsed_item_structure | 必須フィールド全て存在 |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipBasic.test_parse_claude_zip_conversation_name | タイトルが正しく設定 |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipBasic.test_parse_claude_zip_message_format | {role, content} 形式 |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipBasic.test_parse_claude_zip_content_format | Human:/Assistant: フォーマット |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipBasic.test_parse_claude_zip_file_id_is_valid_hex | 12桁 hex file_id |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipBasic.test_parse_claude_zip_source_provider | source_provider == "claude" |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipFixture.test_parse_claude_zip_output_count | claude_test.zip -> 3 items |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipFixture.test_parse_claude_zip_all_have_required_fields | 全 items に必須フィールド |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipFixture.test_parse_claude_zip_all_source_provider_claude | 全 items provider=claude |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipFixture.test_parse_claude_zip_all_have_4_messages | 各会話 4 メッセージ |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipFixture.test_parse_claude_zip_content_not_empty | content が空でない |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipFixture.test_parse_claude_zip_not_chunked | is_chunked=False |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipInvalid.test_parse_claude_zip_invalid_bytes | 壊れた ZIP -> 空 dict |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipInvalid.test_parse_claude_zip_truncated_zip | 途中切れ ZIP -> 空 dict |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipInvalid.test_parse_claude_zip_empty_bytes | 空 bytes -> 空 dict |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipNoConversations.test_parse_claude_zip_no_conversations_json | conversations.json 欠損 -> 空 dict |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipNoConversations.test_parse_claude_zip_empty_conversations_json | 空 conversations.json -> 空 dict |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipNoConversations.test_parse_claude_zip_empty_partitioned_input | 空入力 -> 空 dict |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipExistingOutput.test_existing_output_param_accepted | existing_output パラメータ受付 |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipExistingOutput.test_no_existing_output_default | existing_output なしで動作 |
| tests/pipelines/extract_claude/test_nodes.py | TestParseClaudeZipMultipleZips.test_multiple_zips_combined | 複数 ZIP の会話を統合 |

## Implementation hints

- `src/obsidian_etl/pipelines/extract_claude/nodes.py` に `parse_claude_zip(partitioned_input: dict[str, Callable], existing_output: dict | None = None) -> dict[str, dict]` を実装
- 内部フロー: partitioned_input をイテレート -> load_func() で ZIP bytes 取得 -> zipfile で conversations.json 抽出 -> JSON パース -> 既存 parse_claude_json のパースロジックを適用
- エラーハンドリング: 壊れた ZIP / conversations.json 欠損 -> 警告ログ出力して空 dict 返却（他の ZIP の処理は継続）
- OpenAI の `parse_chatgpt_zip` が参照実装として利用可能

## FAIL output example

```
ERROR: test_parse_claude_zip_returns_dict (tests.pipelines.extract_claude.test_nodes.TestParseClaudeZipBasic.test_parse_claude_zip_returns_dict)
content がフォーマット済み会話テキストであること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/extract_claude/test_nodes.py", line 988, in setUp
    from obsidian_etl.pipelines.extract_claude.nodes import parse_claude_zip
ImportError: cannot import name 'parse_claude_zip' from 'obsidian_etl.pipelines.extract_claude.nodes'
```

## Notes

- BinaryDataset tests (10 tests) PASS because BinaryDataset was implemented in Phase 1
- OpenAI fixture tests (7 tests) PASS because parse_chatgpt_zip already exists and works with ZIP fixtures
- OpenAI fixture count was adjusted from 3 to 2: the first conversation in openai_test.zip has < 3 valid messages and is correctly skipped
- Existing Claude tests (21 tests with parse_claude_json) continue to PASS -- no regressions
- RAG test failures (pre-existing, unrelated to this feature) are excluded from analysis
