# Phase 7 Output: US6 - Error Detail File Output

## Summary

| Metric | Value |
|--------|-------|
| Phase | Phase 7 - US6 (Error Detail Output) |
| Tasks | 9/9 completed |
| Status | Completed |
| Tests | 230 tests passed (ETL Pipeline Tests) |

## Completed Tasks

| # | Task | Status |
|---|------|--------|
| T065 | Read previous phase output | Done |
| T066 | Add test for error detail file creation | Done |
| T067 | Add test for ErrorDetail fields in output file | Done |
| T068 | Add _write_error_detail() method to BaseStage._handle_error() | Done |
| T069 | Create ErrorDetail from ProcessingItem in _handle_error() | Done |
| T070 | Ensure errors/ folder is created under phase directory | Done |
| T071 | Add llm_prompt and llm_output capture in error path | Done |
| T072 | Run make test | Done (230 tests passed) |
| T073 | Generate phase output | Done |

## New/Modified Files

### src/etl/core/stage.py (Modified)

Added error detail file output support to BaseStage:

1. **Import ErrorDetail and write_error_file** (T068):
   - Added import from `..utils.error_writer`

2. **BaseStage._handle_error()** (T068):
   - Now calls `_write_error_detail()` before debug output
   - Maintains backward compatibility with debug mode

3. **BaseStage._write_error_detail()** (T068-T071):
   - Creates ErrorDetail from ProcessingItem metadata
   - Writes to `{phase_dir}/errors/{conversation_id}.md`
   - Captures llm_prompt and llm_raw_response from item metadata
   - Silently ignores write errors to avoid masking original error

4. **BaseStage._classify_error()** (T069):
   - Classifies exception into error types: json_parse, no_json, timeout, connection, retry_exhausted, unknown

Key code additions:

```python
def _handle_error(
    self,
    ctx: StageContext,
    item: ProcessingItem,
    error: Exception,
) -> None:
    """Handle stage-level error.

    T068: Writes error detail file to errors/ folder.
    """
    # T068: Write error detail file
    self._write_error_detail(ctx, item, error)

    if ctx.debug_mode:
        self._write_debug_output(ctx, item, error=error)

def _write_error_detail(
    self,
    ctx: StageContext,
    item: ProcessingItem,
    error: Exception,
) -> None:
    """Write error detail file to errors/ folder."""
    errors_path = ctx.phase.base_path / "errors"
    session_id = ctx.phase.base_path.parent.name

    error_type = self._classify_error(error)
    conversation_id = item.metadata.get("conversation_uuid", item.item_id)
    conversation_title = item.metadata.get("conversation_name", "Untitled")
    llm_prompt = item.metadata.get("llm_prompt", "")
    llm_output = item.metadata.get("llm_raw_response")
    original_content = item.content or item.transformed_content or ""

    error_detail = ErrorDetail(
        session_id=session_id,
        conversation_id=conversation_id,
        conversation_title=conversation_title,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        error_type=error_type,
        error_message=str(error),
        original_content=original_content,
        llm_prompt=llm_prompt,
        stage=item.current_step or self.stage_type.value,
        llm_output=llm_output,
    )

    try:
        write_error_file(error_detail, errors_path)
    except Exception:
        pass  # Silently ignore write errors

def _classify_error(self, error: Exception) -> str:
    """Classify error type from exception."""
    error_msg = str(error).lower()
    error_type_name = type(error).__name__.lower()

    if "json" in error_msg or "json" in error_type_name:
        if "parse" in error_msg or "decode" in error_msg:
            return "json_parse"
        return "no_json"
    elif "timeout" in error_msg or "timeout" in error_type_name:
        return "timeout"
    elif "connection" in error_msg or "connection" in error_type_name:
        return "connection"
    elif "retry" in error_msg:
        return "retry_exhausted"
    else:
        return "unknown"
```

### src/etl/tests/test_session_loader.py (Modified)

Added 7 new test cases for error detail file output:

1. **TestErrorDetailFileCreation** (2 tests, T066):
   - `test_error_detail_file_created_in_errors_folder`: Verifies errors/ folder creation
   - `test_error_file_with_timestamp_in_filename`: Verifies conversation_id filename

2. **TestErrorDetailFields** (5 tests, T067):
   - `test_error_file_contains_all_required_fields`: All ErrorDetail fields present
   - `test_error_file_handles_optional_fields`: Optional fields (None) handled
   - `test_error_file_markdown_structure`: Correct Markdown headers and code blocks

## Key Design Decisions

### 1. Error Type Classification (T069)

Automatic classification based on exception message and type:

| Error Type | Detection Pattern |
|------------|------------------|
| json_parse | "json" + ("parse" or "decode") in message |
| no_json | "json" in message (without parse/decode) |
| timeout | "timeout" in message or type name |
| connection | "connection" in message or type name |
| retry_exhausted | "retry" in message |
| unknown | Default fallback |

### 2. Error File Location (T070)

```
.staging/@session/YYYYMMDD_HHMMSS/
    import/
        errors/                    <- Created by _write_error_detail()
            {conversation_id}.md   <- One file per error
```

### 3. LLM Context Capture (T071)

ExtractKnowledgeStep already captures llm_prompt and llm_raw_response in item.metadata:

```python
# In ExtractKnowledgeStep.process() error path:
item.metadata["llm_prompt"] = result.user_prompt
item.metadata["llm_raw_response"] = result.raw_response
```

BaseStage._write_error_detail() reads these from metadata and includes in ErrorDetail.

### 4. Silent Error Handling

Write errors are silently ignored to avoid masking the original error:

```python
try:
    write_error_file(error_detail, errors_path)
except Exception:
    pass  # Silently ignore write errors
```

## Error Detail File Format

Output format (from error_writer.py):

```markdown
# Error Detail: {conversation_title}

**Session**: {session_id}
**Conversation ID**: {conversation_id}
**Timestamp**: {timestamp}
**Error Type**: {error_type}
**Error Position**: {error_position or N/A}
**Stage**: {stage}

## Error Message

{error_message}

## Original Content

```text
{original_content}
```

## LLM Prompt

```text
{llm_prompt}
```

## LLM Raw Output

```text
{llm_output or (no output)}
```

## Context

{error_context}  <- Only if set
```

## Test Results

```
Ran 230 tests in 0.224s
OK
```

All tests pass, including 7 new tests for error detail output.

## Error Flow Diagram

```
[Step.process()]
    |
    +-- Exception raised
    |
    v
[BaseStage.run()]
    |
    +-- Catches exception
    |
    +-- Calls _handle_error(ctx, item, error)
    |
    v
[BaseStage._handle_error()]
    |
    +-- _write_error_detail(ctx, item, error)
    |       |
    |       +-- _classify_error(error) -> error_type
    |       |
    |       +-- Extract metadata:
    |       |     - conversation_id
    |       |     - conversation_title
    |       |     - llm_prompt (from item.metadata)
    |       |     - llm_raw_response (from item.metadata)
    |       |
    |       +-- Create ErrorDetail dataclass
    |       |
    |       +-- write_error_file(error_detail, errors_path)
    |       |       |
    |       |       +-- Create errors/ folder
    |       |       |
    |       |       +-- Write {conversation_id}.md
    |       |
    |       +-- (Silently catch any write errors)
    |
    +-- If debug_mode:
    |       _write_debug_output(ctx, item, error)
    |
    v
[Continue error handling in run()]
    |
    +-- item.status = ItemStatus.FAILED
    +-- item.error = str(error)
    +-- Write JSONL log
    +-- yield item
```

## Next Phase Prerequisites

Phase 8 (Polish & Cross-Cutting Concerns) can now proceed with:

1. Error detail files automatically created on failure
2. All US1-US6 features implemented and tested
3. Test patterns established for all stages

## Phase 7 Checkpoint

With Phase 7 complete:

1. **Error Detail Files**: Automatically written to errors/ folder
2. **Error Classification**: Automatic error_type from exception
3. **LLM Context**: llm_prompt and llm_output captured in error files
4. **Backward Compatible**: No changes to existing behavior

The import pipeline now outputs detailed debug information for all errors, enabling easy troubleshooting of LLM extraction failures.
