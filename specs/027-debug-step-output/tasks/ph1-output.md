# Phase 1: Setup - Output

**Execution Date**: 2026-01-20
**Status**: Completed
**Tasks Completed**: 5/5

---

## Task T001: Read existing debug output implementation

**File**: `/path/to/project/src/etl/core/stage.py` (lines 566-629)

### Current Debug Output Implementation

**Method**: `_write_debug_output(ctx, item, error=None)`

**Key Features**:
1. **Debug Mode Check**: Returns early if `ctx.debug_mode` is False (line 583-584)
2. **Output Location**: `ctx.output_path / "debug"` (line 587)
3. **File Naming**: `{safe_name}_{stage_type}.json` (line 592)
4. **Format**: JSON with indentation (`json.dump(..., indent=2)`) (line 629)
5. **Content Preview**: Truncates content to 500 chars (lines 606-615)

**Data Fields**:
- timestamp (ISO format)
- item_id
- source_path
- current_step
- status
- metadata (serialized)
- content_preview (500 chars max)
- content_length
- transformed_content_preview (500 chars max)
- transformed_content_length
- error (if present)

**Current Limitations**:
- **Stage-level only**: No per-step debug output
- **Single file per item**: No step-by-step tracking
- **Content preview**: Only shows 500 chars, not full content
- **JSON format**: Uses indented JSON, not JSONL

---

## Task T002: Read KnowledgeTransformer steps structure

**File**: `/path/to/project/src/etl/stages/transform/knowledge_transformer.py`

### Step Structure

**KnowledgeTransformer** has 3 steps (lines 645-649):

1. **ExtractKnowledgeStep** (lines 78-403)
   - name: `"extract_knowledge"`
   - Calls Ollama API via KnowledgeExtractor
   - Supports chunking for large conversations
   - Has `process_with_expansion()` method for 1-to-N expansion

2. **GenerateMetadataStep** (lines 406-475)
   - name: `"generate_metadata"`
   - Generates file_id using `generate_file_id()`
   - Creates metadata for knowledge notes

3. **FormatMarkdownStep** (lines 478-629)
   - name: `"format_markdown"`
   - Converts KnowledgeDocument to Markdown
   - Uses `KnowledgeDocument.to_markdown()`

### Step Processing Pattern

**Custom run() method** (lines 659-790):
- Manually processes ExtractKnowledgeStep first with expansion
- Processes remaining steps (GenerateMetadata, FormatMarkdown) sequentially
- Calls `_write_debug_output()` after each step (lines 721, 736, 742, 749)
- Uses `enumerate()` NOT currently used - steps are accessed via list indexing

**Debug Output Calls** (current):
- Line 721: After ExtractKnowledgeStep failure
- Line 736: After step validation fails
- Line 742: After step.process() succeeds
- Line 749: After step.on_error() fallback

---

## Task T003: Read existing test patterns

**Directory**: `/path/to/project/src/etl/tests/`

**Test Files Found**:
- `test_retry.py` - Retry mechanism tests
- `test_phase.py` - Phase management tests
- `test_knowledge_transformer.py` - KnowledgeTransformer tests
- `test_cli.py` - CLI tests
- `test_stages.py` - BaseStage and Stage tests
- `test_organize_phase.py` - Organize phase tests
- `test_import_phase.py` - Import phase tests
- `test_session_loader.py` - Session loader tests
- `test_session.py` - Session management tests
- `test_models.py` - Data model tests

### Test Patterns Observed

**Pattern 1: Mock-based testing** (test_knowledge_transformer.py):
```python
class TestExtractKnowledgeStepWithMockedOllama(unittest.TestCase):
    def test_extract_knowledge_calls_extractor(self):
        step = ExtractKnowledgeStep()
        mock_document = KnowledgeDocument(...)
        mock_result = ExtractionResult(success=True, document=mock_document, ...)
        # Mock and assert
```

**Pattern 2: Temporary directory testing** (test_stages.py):
```python
def test_stage_run_processes_items(self):
    with TemporaryDirectory() as tmpdir:
        session_path = Path(tmpdir) / "20260119_120000"
        session_path.mkdir()
        phase = Phase(...)
        # Test with real filesystem
```

**Pattern 3: Integration testing**:
- Uses actual Session/Phase/Stage objects
- Creates temporary directories for output
- Verifies file creation and content

**Testing Framework**: Python `unittest` (not pytest)

---

## Task T004: Run baseline tests

**Command**: `make test`

**Status**: Completed

**Results**: 238 tests, 3 failures, 1 error

**Failed Tests**:
1. `ERROR: test_session_loader_with_index_path` (TestSessionLoaderIntegration)
2. `FAIL: test_format_markdown_fallback_for_non_conversation` (TestFormatMarkdownStepOutput)
3. `FAIL: test_session_loader_default_steps` (TestSessionLoaderIntegration)
4. `FAIL: test_session_loader_runs_both_steps` (TestSessionLoaderIntegration)

**Analysis**:
- Baseline failures exist BEFORE our changes
- Failures are in SessionLoader and FormatMarkdown, not debug output
- These are pre-existing issues unrelated to debug step output feature
- Our changes should NOT introduce new failures
- Target: Keep test count at 238 total, 3 failures, 1 error (no regression)

---

## Task T005: Generate phase output

**Status**: Complete (this document)

---

## Summary

### Current Implementation Analysis

**Stage-level debug output exists**:
- Written to `debug/` folder under stage output
- Uses JSON format with indentation
- Truncates content to 500 char preview
- Called manually after each step in KnowledgeTransformer

**Gap for Step-level debug output**:
- No dedicated method for step-level output
- No `step_{NNN}_{step_name}/` directory structure
- No JSONL format (uses indented JSON)
- No full content storage (only preview)

### Required Changes

**Phase 2 (Foundational)**:
1. Add `_write_debug_step_output()` method to BaseStage
2. Implement JSONL compact format
3. Update `_process_item()` to use `enumerate(self.steps)` for indexing
4. Ensure zero performance impact when debug_mode=False

**Phase 3+ (User Stories)**:
1. Integrate step output calls in `_process_item()`
2. Implement directory structure: `debug/step_{NNN}_{step_name}/`
3. Store full content (not preview) in JSONL format
4. Include all required fields per data-model.md

### Test Coverage Required

**From test patterns**:
- Mock-based unit tests for method behavior
- Temporary directory integration tests
- JSONL format validation tests
- Debug mode ON/OFF tests
- Step failure scenario tests

### Key Files to Modify

1. **src/etl/core/stage.py** - Add `_write_debug_step_output()` method
2. **src/etl/tests/test_debug_step_output.py** (NEW) - Test suite for step debug output

---

## Next Steps

**Phase 2: Foundational**
- Read this document (T006)
- Implement `_write_debug_step_output()` in BaseStage (T007-T008)
- Update `_process_item()` to use enumerate (T009)
- Verify no regression with `make test` (T010)
