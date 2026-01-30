# Phase 1 Output: Setup Complete

**Date**: 2026-01-30
**Phase**: Setup (Phase 1)
**Status**: ✅ Complete

## Tasks Completed

- [x] T001 Read current prompt templates
- [x] T002 Read current parser functions in ollama.py
- [x] T003 Read current knowledge extractor calls
- [x] T004 Read existing tests
- [x] T005 Generate phase output

## Key Findings

### 1. Current Prompt Templates

#### knowledge_extraction.txt
- **Location**: `/path/to/project/src/etl/prompts/knowledge_extraction.txt`
- **Current format**: JSON with 3 fields
```json
{
  "title": "会話のタイトル（オプショナル、40文字以内）",
  "summary": "会話の要点を1-2文で説明（200文字以内）",
  "summary_content": "構造化されたまとめ（Markdown形式、コード含む）"
}
```
- **Target format**: Markdown with 3 sections
```markdown
# タイトル（40文字以内）

## 要約
1-2文の要約テキスト（200文字以内）

## 内容
構造化されたまとめ（Markdown形式、コード含む）
```

#### summary_translation.txt
- **Location**: `/path/to/project/src/etl/prompts/summary_translation.txt`
- **Current format**: JSON with 1 field
```json
{
  "summary": "翻訳された日本語のサマリー（1-2文）"
}
```
- **Target format**: Minimal markdown
```markdown
## 要約
翻訳された日本語のサマリー（1-2文）
```

### 2. Current Parser Functions (ollama.py)

**Location**: `/path/to/project/src/etl/utils/ollama.py`

**parse_json_response(response: str) → tuple[dict, str | None]**
- Entry point for JSON parsing
- Returns: (parsed dict, error_message or None)
- Line 74-93

**extract_json_from_code_block(response: str) → str | None**
- Extracts JSON from ```json ... ``` or ```...``` code blocks
- Returns: JSON string or None
- Line 59-72

**extract_first_json_object(response: str) → str | None**
- Fallback: bracket balancing to find JSON object
- Handles nested braces
- Line 27-57

**format_parse_error(error: Exception, response: str, context: str = "") → str**
- Error message formatter
- Shows truncated response snippet
- Line 96-105

### 3. Knowledge Extractor Calls

**Location**: `/path/to/project/src/etl/utils/knowledge_extractor.py`

**Import statement (line 23)**:
```python
from src.etl.utils.ollama import call_ollama, parse_json_response
```

**Call site 1: translate_summary method (line 395)**:
```python
data, parse_error = parse_json_response(response)
if parse_error:
    return None, parse_error
return data.get("summary", ""), None
```
- Context: English summary translation
- Uses: summary_translation.txt prompt
- Expects: {"summary": "..."}

**Call site 2: extract method (line 446)**:
```python
data, parse_error = parse_json_response(response)
if parse_error:
    return ExtractionResult(
        success=False,
        error=parse_error,
        raw_response=response,
        user_prompt=user_prompt,
    )
```
- Context: Main knowledge extraction
- Uses: knowledge_extraction.txt prompt
- Expects: {"title": "...", "summary": "...", "summary_content": "..."}

### 4. Test Files Status

**test_ollama.py**:
- **Location**: `/path/to/project/src/etl/tests/test_ollama.py`
- **Status**: ❌ Does not exist
- **Action**: Will be created in Phase 2 TDD workflow

**test_knowledge_extractor.py**:
- **Location**: `/path/to/project/src/etl/tests/test_knowledge_extractor.py`
- **Status**: ❌ Does not exist
- **Action**: Will be created in Phase 2 TDD workflow

## Implementation Strategy

### Parser Signature

New `parse_markdown_response()` will maintain same signature as `parse_json_response()`:

```python
def parse_markdown_response(response: str) -> tuple[dict, str | None]:
    """
    Parse markdown response into structured dict.

    Returns:
        tuple[dict, str | None]: (parsed dict, error_message or None)
    """
    pass
```

### Processing Steps

1. **Preprocess**: Remove ```markdown ... ``` fences if present
2. **Section split**: Detect `#` and `##` headings
3. **Extract fields**:
   - Title from `#` heading
   - Summary from `## 要約` section body
   - Content from `## 内容` section body
4. **Build dict**: {"title": ..., "summary": ..., "summary_content": ...}
5. **Return**: (dict, None) on success, (empty dict, error) on failure

### Call Site Updates

**knowledge_extractor.py changes**:
1. Update import (line 23): `parse_json_response` → `parse_markdown_response`
2. Update call site 1 (line 395): Use new parser
3. Update call site 2 (line 446): Use new parser

**Note**: Same return type means no changes to error handling or dict access code.

## Phase Dependencies

**Phase 2 Prerequisites** (all met ✅):
- Prompt structure understood
- Parser functions analyzed
- Call sites identified
- Test file paths confirmed

**No blocking issues found** - ready to proceed to Phase 2 TDD workflow.

## Next Steps

1. Launch `tdd-generator` agent for Phase 2 RED tests
2. Implement tests for `parse_markdown_response()` (T007-T011)
3. Verify tests FAIL (RED state)
4. Generate ph2-test.md output
5. Proceed to GREEN implementation (T014-T019)
