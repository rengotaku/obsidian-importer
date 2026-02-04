# Phase 3 RED Tests

## Summary
- Phase: Phase 3 - User Story 1: ChatGPT deduplication fix (N^2 -> N)
- FAIL test count: 5
- PASS test count: 11 (validate existing _discover_raw_items behavior)
- Test file: src/etl/tests/test_chatgpt_dedup.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| test_chatgpt_dedup.py | test_steps_returns_only_validate_min_messages | `ChatGPTExtractor.steps` returns exactly 1 step: `ValidateMinMessagesStep` |
| test_chatgpt_dedup.py | test_steps_do_not_include_read_zip | `ReadZipStep` not in steps (moved to `_discover_raw_items`) |
| test_chatgpt_dedup.py | test_steps_do_not_include_parse_conversations | `ParseConversationsStep` not in steps (moved to `_discover_raw_items`) |
| test_chatgpt_dedup.py | test_steps_do_not_include_convert_format | `ConvertFormatStep` not in steps (moved to `_discover_raw_items`) |
| test_chatgpt_dedup.py | test_build_chunk_messages_returns_chatgpt_format | `_build_chunk_messages()` returns `{uuid, text, sender, created_at}` (not None) |

## PASS Test List (existing behavior already works)

| Test File | Test Method | Validates |
|-----------|-------------|-----------|
| test_chatgpt_dedup.py | test_discover_run_n_items_n_output | 3 conversations -> 3 discovered items |
| test_chatgpt_dedup.py | test_discover_run_single_conversation_no_duplication | 1 conversation -> 1 item |
| test_chatgpt_dedup.py | test_no_duplicate_conversation_uuid_in_discovered_items | All UUIDs unique |
| test_chatgpt_dedup.py | test_discover_raw_items_yields_content_set_items | content set with Claude format |
| test_chatgpt_dedup.py | test_discover_raw_items_sets_metadata | Required metadata fields present |
| test_chatgpt_dedup.py | test_discover_raw_items_from_directory | Accepts directory path |
| test_chatgpt_dedup.py | test_chunked_messages_have_uuid_and_created_at | Chunked messages have uuid/created_at |
| test_chatgpt_dedup.py | test_empty_conversations_json_no_exception | Empty ZIP graceful completion |
| test_chatgpt_dedup.py | test_empty_conversations_json_discover_raw_items | Empty ZIP yields nothing |
| test_chatgpt_dedup.py | test_missing_mapping_skipped_others_processed | Malformed conv skipped |
| test_chatgpt_dedup.py | test_missing_current_node_skipped | No current_node skipped |

## Why Tests FAIL

### T020 (Steps validation) - 4 tests FAIL
Currently `ChatGPTExtractor.steps` returns 4 steps:
```python
[ReadZipStep(), ParseConversationsStep(), ConvertFormatStep(), ValidateMinMessagesStep()]
```
After GREEN, it should return only:
```python
[ValidateMinMessagesStep()]
```
The redundant steps (ReadZip, ParseConversations, ConvertFormat) must be deleted because `_discover_raw_items()` already handles ZIP reading, parsing, and format conversion.

### T021 (_build_chunk_messages) - 1 test FAIL
`ChatGPTExtractor` does not override `_build_chunk_messages()`, so it inherits BaseExtractor's default which returns `None`. After GREEN, it must return:
```python
[{"uuid": "", "text": msg.content, "sender": msg.role, "created_at": conv_dict.get("created_at", "")}]
```

## Implementation Hints

- `src/etl/stages/extract/chatgpt_extractor.py`:
  - Delete `ReadZipStep`, `ParseConversationsStep`, `ConvertFormatStep` classes
  - Update `ChatGPTExtractor.steps` to return `[ValidateMinMessagesStep()]`
  - Add `_build_chunk_messages(self, chunk, conversation_dict) -> list[dict]` override
  - Delete `_chunk_if_needed()` override (BaseExtractor template handles it)
  - Delete `stage_type` override (BaseExtractor returns EXTRACT)

## FAIL Output

```
FAILED test_steps_returns_only_validate_min_messages
  AssertionError: Expected 1 step, got 4: ['ReadZipStep', 'ParseConversationsStep', 'ConvertFormatStep', 'ValidateMinMessagesStep']

FAILED test_steps_do_not_include_read_zip
  AssertionError: 'ReadZipStep' unexpectedly found in ['ReadZipStep', 'ParseConversationsStep', 'ConvertFormatStep', 'ValidateMinMessagesStep']

FAILED test_steps_do_not_include_parse_conversations
  AssertionError: 'ParseConversationsStep' unexpectedly found in [...]

FAILED test_steps_do_not_include_convert_format
  AssertionError: 'ConvertFormatStep' unexpectedly found in [...]

FAILED test_build_chunk_messages_returns_chatgpt_format
  AssertionError: unexpectedly None : _build_chunk_messages() should not return None for ChatGPT
```
