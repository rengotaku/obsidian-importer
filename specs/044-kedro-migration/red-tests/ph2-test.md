# Phase 2 RED Tests

## Summary
- Phase: Phase 2 - US1 Claude Extract Pipeline
- FAIL test count: 14 (all fail due to ImportError: parse_claude_json not implemented)
- Test file: tests/pipelines/extract_claude/test_nodes.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| test_nodes.py | test_parse_claude_json_basic | Valid Claude JSON -> ParsedItem dict with correct fields |
| test_nodes.py | test_parse_claude_json_message_format | Messages normalized to {role, content} format |
| test_nodes.py | test_parse_claude_json_content_format | Content contains formatted "Human:" / "Assistant:" text |
| test_nodes.py | test_parse_claude_json_second_conversation | Second conversation parsed correctly |
| test_nodes.py | test_parse_claude_json_chunking | 25000+ char conversation -> multiple chunks with metadata |
| test_nodes.py | test_parse_claude_json_skip_short | Conversations with < 3 messages excluded |
| test_nodes.py | test_parse_claude_json_empty_conversations | Empty list -> empty dict |
| test_nodes.py | test_parse_claude_json_missing_name | name=None -> fallback to first user message |
| test_nodes.py | test_parse_claude_json_name_missing_key | name key absent -> fallback to first user message |
| test_nodes.py | test_validate_structure_missing_uuid | Missing uuid -> conversation excluded |
| test_nodes.py | test_validate_structure_missing_chat_messages | Missing chat_messages -> conversation excluded |
| test_nodes.py | test_validate_structure_both_required_present | Valid structure -> conversation processed |
| test_nodes.py | test_validate_content_empty_messages | All-empty messages -> conversation excluded (content < 10 chars) |
| test_nodes.py | test_validate_content_mixed_empty_messages | Mixed empty/non-empty messages -> empty filtered out |
| test_nodes.py | test_file_id_generation | file_id is 12 hex chars (SHA256 prefix) |
| test_nodes.py | test_file_id_deterministic | Same input -> same file_id |
| test_nodes.py | test_file_id_different_for_different_content | Different input -> different file_id |

## Implementation Hints

- `src/obsidian_etl/pipelines/extract_claude/nodes.py` に `parse_claude_json(conversations: list[dict]) -> dict[str, dict]` を実装
- 入力: Claude export JSON の会話リスト (list[dict])
- 出力: `Dict[str, dict]` (partition_id -> ParsedItem dict)
- ParsedItem の構造は `specs/044-kedro-migration/data-model.md` の E-2 を参照
- チャンク分割には `obsidian_etl.utils.chunker.should_chunk` / `split_messages` を使用
- file_id 生成には `obsidian_etl.utils.file_id.generate_file_id` を使用
- バリデーション: uuid と chat_messages が必須、messages >= 3、content >= 10 chars
- name が None/欠落の場合、最初の human メッセージをフォールバック名として使用
- メッセージ正規化: sender -> role, text -> content
- 空メッセージ (text="") はフィルタリングして除外

## FAIL Output Example
```
ERROR: pipelines.extract_claude.test_nodes (unittest.loader._FailedTest.pipelines.extract_claude.test_nodes)
----------------------------------------------------------------------
ImportError: Failed to import test module: pipelines.extract_claude.test_nodes
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/extract_claude/test_nodes.py", line 21, in <module>
    from obsidian_etl.pipelines.extract_claude.nodes import parse_claude_json
ImportError: cannot import name 'parse_claude_json' from 'obsidian_etl.pipelines.extract_claude.nodes'
```
