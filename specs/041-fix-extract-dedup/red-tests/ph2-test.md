# Phase 2 RED Tests

## Summary
- Phase: Phase 2 - Foundational - BaseExtractor template completion
- FAIL test count: 3 (2 FAIL + 1 ERROR)
- PASS test count: 5 (existing functionality)
- Test file: `src/etl/tests/test_extractor_template.py`

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| test_extractor_template.py | test_base_extractor_has_build_chunk_messages_method | BaseExtractor should have `_build_chunk_messages()` method |
| test_extractor_template.py | test_build_chunk_messages_returns_none_by_default | `_build_chunk_messages()` should return None by default |
| test_extractor_template.py | test_chunk_if_needed_calls_build_chunk_messages | `_chunk_if_needed()` should call `_build_chunk_messages()` hook and use returned messages |

## PASS Test List (Existing Functionality)

| Test File | Test Method | Behavior |
|-----------|-------------|----------|
| test_extractor_template.py | test_child_class_can_override_build_chunk_messages | Child class defines own `_build_chunk_messages()` |
| test_extractor_template.py | test_chunk_if_needed_preserves_content_when_hook_returns_none | No chunking when `_build_conversation_for_chunking()` returns None |
| test_extractor_template.py | test_base_extractor_stage_type_is_extract | `stage_type` returns `StageType.EXTRACT` |
| test_extractor_template.py | test_child_extractor_inherits_stage_type | Child inherits `stage_type` from BaseExtractor |
| test_extractor_template.py | test_stage_type_not_overridden_in_child | `stage_type` defined on BaseExtractor class |

## Implementation Hints

- Add `_build_chunk_messages(self, chunk, conversation_dict: dict) -> list[dict] | None` to `BaseExtractor` in `src/etl/core/extractor.py`
- Default implementation returns `None`
- Update `_chunk_if_needed()` in `BaseExtractor` to call `self._build_chunk_messages(chunk_obj, chunk_conv)` after creating `chunk_conv = dict(conv)` and set `chunk_conv["chat_messages"] = messages` if not None
- Update chunk content with `json.dumps(chunk_conv, ensure_ascii=False)` after hook application

## FAIL Output

```
FAIL: test_base_extractor_has_build_chunk_messages_method (src.etl.tests.test_extractor_template.TestBuildChunkMessagesHook)
AssertionError: False is not true : BaseExtractor should have _build_chunk_messages method

ERROR: test_build_chunk_messages_returns_none_by_default (src.etl.tests.test_extractor_template.TestBuildChunkMessagesHook)
AttributeError: 'ConcreteExtractor' object has no attribute '_build_chunk_messages'

FAIL: test_chunk_if_needed_calls_build_chunk_messages (src.etl.tests.test_extractor_template.TestChunkIfNeededWithHook)
AssertionError: 'custom_field' not found in {'text': 'xxx...', 'sender': 'human'} : chat_messages should be built by _build_chunk_messages() hook
```
