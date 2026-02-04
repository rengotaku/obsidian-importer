# Phase 5 Output: US4 - English Summary Translation

## Summary

| Metric | Value |
|--------|-------|
| Phase | Phase 5 - US4 (Translation) |
| Tasks | 10/10 completed |
| Status | Completed |
| Tests | 211 tests passed (ETL Pipeline Tests) |

## Completed Tasks

| # | Task | Status |
|---|------|--------|
| T046 | Read previous phase output | Done |
| T047 | Add test for is_english_summary() detection | Done |
| T048 | Add test for translate_summary() with mocked Ollama | Done |
| T049 | Add test for translation error fallback | Done |
| T050 | Add _translate_if_english() method to ExtractKnowledgeStep | Done |
| T051 | Integrate translation into ExtractKnowledgeStep.process() | Done |
| T052 | Add summary_translated metadata flag to ProcessingItem | Done |
| T053 | Add translation error fallback (use original English) with warning log | Done |
| T054 | Run make test | Done (211 tests passed) |
| T055 | Generate phase output | Done |

## New/Modified Files

### src/etl/stages/transform/knowledge_transformer.py (Modified)

Added translation support to ExtractKnowledgeStep:

1. **_translate_if_english() method** (T050):
   - Detects English summary using `is_english_summary()`
   - Attempts translation via `translate_summary()`
   - Returns (translated_summary, original_summary) tuple
   - On translation error, logs warning and returns (None, original_summary)

2. **process() method integration** (T051):
   - Calls `_translate_if_english()` before extraction
   - Sets translation metadata on ProcessingItem
   - Applies translation to KnowledgeDocument if successful

Key code additions:

```python
def _translate_if_english(
    self, item: ProcessingItem, data: dict
) -> tuple[str | None, str | None]:
    """Translate summary if it's in English.

    T050: Detects English summary and translates to Japanese.

    Args:
        item: ProcessingItem with conversation data.
        data: Parsed conversation JSON.

    Returns:
        Tuple of (translated_summary, original_summary).
        If not English or translation fails, returns (None, original_summary).
    """
    original_summary = data.get("summary")

    if not original_summary:
        return None, None

    # Check if English
    if not self._extractor.is_english_summary(original_summary):
        return None, None

    # Attempt translation
    translated, error = self._extractor.translate_summary(original_summary)

    if error:
        # T053: Translation error - log warning and use original
        logger.warning(
            f"Summary translation failed for {item.item_id}: {error}. "
            "Using original English summary."
        )
        return None, original_summary

    return translated, original_summary
```

### src/etl/tests/test_knowledge_transformer.py (Modified)

Added 10 new test cases for US4:

1. **TestIsEnglishSummaryDetection** (5 tests):
   - `test_detects_english_summary_with_conversation_overview`: Detects "**Conversation Overview**" pattern
   - `test_detects_english_summary_with_high_ascii_ratio`: Detects high ASCII ratio text
   - `test_returns_false_for_japanese_summary`: Japanese text returns False
   - `test_returns_false_for_none_summary`: None returns False
   - `test_returns_false_for_empty_summary`: Empty string returns False

2. **TestTranslateSummaryWithMockedOllama** (3 tests):
   - `test_translate_summary_calls_ollama`: Verifies Ollama is called and returns translated text
   - `test_translate_summary_handles_ollama_error`: Handles connection errors gracefully
   - `test_translate_summary_handles_json_parse_error`: Handles invalid JSON response

3. **TestTranslationErrorFallback** (2 tests):
   - `test_translation_failure_uses_original_english`: On failure, uses original English
   - `test_successful_translation_sets_metadata`: Sets summary_translated and original_summary

## Key Design Decisions

### 1. Translation Metadata Strategy

ProcessingItem metadata includes:
- `summary_translated: bool` - True if translation was applied successfully
- `original_summary: str` - Original English summary (always set if English detected)

### 2. Fallback Behavior (T053)

When translation fails:
1. Log warning with item_id and error message
2. Use original English summary
3. Set `summary_translated = False`
4. Preserve `original_summary` for debugging

### 3. Translation Flow

```
[Parse JSON]
    |
    v
[Check is_english_summary()]
    |
    +-- False --> Skip translation
    |
    +-- True --> [translate_summary()]
                     |
                     +-- Success --> Use translated, set summary_translated=True
                     |
                     +-- Failure --> Log warning, use original, set summary_translated=False
    |
    v
[Continue with extraction]
```

### 4. Integration Point

Translation is applied AFTER extraction, by modifying the `KnowledgeDocument.summary`:
```python
# T051: Apply translation to document if available
if translated_summary is not None and result.document:
    result.document.summary = translated_summary
```

## Test Results

```
Ran 211 tests in 0.227s
OK
```

All existing tests pass. 10 new tests added for translation functionality.
(Note: 3 existing tests were updated to mock `is_english_summary` to return False)

## Translation Detection Criteria

### English Detection Patterns

| Pattern | Example |
|---------|---------|
| `**Conversation Overview**` | Claude's standard summary format |
| `Conversation Overview` | Without bold |
| `Summary:` | Generic summary prefix |
| `Overview:` | Generic overview prefix |
| `The user (asked/requested/wanted/discussed)` | Claude's description pattern |

### ASCII Ratio Threshold

- If > 70% of characters are ASCII, text is considered English
- This handles mixed content cases

## Next Phase Prerequisites

Phase 6 (US5 - @index Output) can now proceed with:

1. `ExtractKnowledgeStep` supports translation
2. Translation metadata (`summary_translated`, `original_summary`) available
3. Test patterns established for mocking translation

## Dependencies for Phase 6

- `SessionLoader.UpdateIndexStep` - Not yet implemented
- `@index` path configuration - Needs to be added to session context
- `file_id` duplicate detection - Needs implementation

## Phase 5 Checkpoint

With Phase 5 complete:

1. **English Detection**: `is_english_summary()` detects English summaries
2. **Translation**: `translate_summary()` translates to Japanese via Ollama
3. **Fallback**: Translation errors use original English with warning log
4. **Metadata**: `summary_translated` and `original_summary` track translation status

The import pipeline can now automatically translate English summaries to Japanese for better Japanese knowledge base integration.
