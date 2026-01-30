# Phase 6 Output: US5 - @index Output

## Summary

| Metric | Value |
|--------|-------|
| Phase | Phase 6 - US5 (@index Output) |
| Tasks | 9/9 completed |
| Status | Completed |
| Tests | 225 tests passed (ETL Pipeline Tests) |

## Completed Tasks

| # | Task | Status |
|---|------|--------|
| T056 | Read previous phase output | Done |
| T057 | Add test for UpdateIndexStep file copy | Done |
| T058 | Add test for file_id duplicate detection | Done |
| T059 | Implement UpdateIndexStep.process() to copy files to @index | Done |
| T060 | Add _find_existing_by_file_id() method | Done |
| T061 | Add overwrite logic for same/different file_id | Done |
| T062 | Configure @index path from session context | Done |
| T063 | Run make test | Done (225 tests passed) |
| T064 | Generate phase output | Done |

## New/Modified Files

### src/etl/stages/load/session_loader.py (Modified)

Added @index output support to UpdateIndexStep:

1. **UpdateIndexStep.__init__()** (T062):
   - Accepts optional `index_path` parameter
   - If None, skip @index copy (backward compatible)

2. **UpdateIndexStep.process()** (T059, T061):
   - Copies processed file to @index directory
   - Detects duplicates via file_id
   - Overwrites if same file_id exists with different filename
   - Creates new file if no matching file_id

3. **UpdateIndexStep._find_existing_by_file_id()** (T060):
   - Scans @index directory for .md files
   - Extracts file_id from YAML frontmatter using regex
   - Returns Path to existing file or None

4. **SessionLoader.__init__()** (T062):
   - Accepts optional `index_path` parameter
   - Passes to UpdateIndexStep

Key code additions:

```python
class UpdateIndexStep(BaseStep):
    """Update @index directory with processed item (US5)."""

    _FILE_ID_PATTERN = re.compile(r"^file_id:\s*(\S+)", re.MULTILINE)

    def __init__(self, index_path: Path | None = None):
        self._index_path = index_path

    def process(self, item: ProcessingItem) -> ProcessingItem:
        item.metadata["indexed"] = True

        if self._index_path is None or item.output_path is None:
            return item

        self._index_path.mkdir(parents=True, exist_ok=True)
        file_id = item.metadata.get("file_id")

        existing_file = None
        if file_id:
            existing_file = self._find_existing_by_file_id(file_id)

        target_path = self._index_path / item.output_path.name

        if existing_file and existing_file != target_path:
            existing_file.unlink()
            item.metadata["index_overwritten"] = True
            item.metadata["index_overwritten_file"] = existing_file.name

        shutil.copy2(item.output_path, target_path)
        item.metadata["index_path"] = str(target_path)

        return item

    def _find_existing_by_file_id(self, file_id: str) -> Path | None:
        # Scan @index for matching file_id in frontmatter
        ...
```

### src/etl/tests/test_session_loader.py (New)

Created new test file with 14 test cases:

1. **TestWriteToSessionStep** (3 tests):
   - `test_writes_transformed_content_to_file`: Verifies file writing
   - `test_sanitizes_filename`: Verifies special character handling
   - `test_uses_item_id_for_untitled_conversation`: Verifies UUID fallback

2. **TestUpdateIndexStepFileCopy** (4 tests):
   - `test_copies_file_to_index_directory`: Basic copy functionality
   - `test_creates_index_directory_if_not_exists`: Auto-creates directory
   - `test_skips_copy_when_no_output_path`: Graceful skip
   - `test_skips_copy_when_no_index_path_configured`: Backward compatibility

3. **TestUpdateIndexStepDuplicateDetection** (4 tests):
   - `test_overwrites_existing_file_with_same_file_id`: Overwrite logic
   - `test_creates_new_file_for_different_file_id`: New file logic
   - `test_detects_file_id_in_frontmatter`: Frontmatter parsing
   - `test_handles_malformed_frontmatter`: Error handling

4. **TestSessionLoaderIntegration** (3 tests):
   - `test_session_loader_default_steps`: Default steps verification
   - `test_session_loader_with_index_path`: Configuration verification
   - `test_session_loader_runs_both_steps`: End-to-end test

## Key Design Decisions

### 1. Duplicate Detection Strategy

Uses regex-based file_id extraction from YAML frontmatter:
- Pattern: `^file_id:\s*(\S+)` (multiline mode)
- Pros: Fast, no YAML parsing library dependency
- Cons: May match invalid YAML (acceptable for our use case)

### 2. Overwrite Behavior (T061)

| Scenario | Action |
|----------|--------|
| Same file_id, same filename | Overwrite in place |
| Same file_id, different filename | Delete old, copy new |
| Different file_id | Create new file |
| No file_id | Create new file |

### 3. Backward Compatibility (T062)

- `index_path=None` skips @index copy
- Default SessionLoader behavior unchanged
- ImportPhase can optionally pass index_path

### 4. Metadata Tracking

ProcessingItem metadata after UpdateIndexStep:
```python
{
    "indexed": True,
    "index_path": "/path/to/@index/file.md",  # If copied
    "index_overwritten": True,  # If duplicate replaced
    "index_overwritten_file": "old_name.md",  # Original filename
}
```

## Test Results

```
Ran 225 tests in 0.246s
OK
```

All tests pass, including 14 new tests for SessionLoader.

## Duplicate Detection Flow

```
[WriteToSessionStep]
    |
    v
[UpdateIndexStep.process()]
    |
    +-- No index_path? --> Skip, return
    |
    +-- No output_path? --> Skip, return
    |
    +-- Get file_id from metadata
    |
    +-- _find_existing_by_file_id(file_id)
    |       |
    |       +-- Scan @index/*.md
    |       |
    |       +-- Extract frontmatter
    |       |
    |       +-- Match file_id pattern
    |       |
    |       +-- Return Path or None
    |
    +-- existing_file != target_path?
    |       |
    |       +-- Yes: Delete existing, mark overwritten
    |       |
    |       +-- No: Continue
    |
    +-- Copy to @index
    |
    v
[Return item with metadata]
```

## Integration with ImportPhase

To enable @index output, update ImportPhase.run():

```python
# In ImportPhase.run()
load_stage = SessionLoader(
    output_path=load_data.output_path,
    index_path=Path(".staging/@index")  # Configure from session
)
```

## Next Phase Prerequisites

Phase 7 (US6 - Error Detail Output) can now proceed with:

1. `UpdateIndexStep` complete and tested
2. File copy and duplicate detection working
3. Test patterns established for file operations

## Dependencies for Phase 7

- BaseStage._handle_error() - Needs error detail writing
- errors/ folder creation - Needs implementation
- ErrorDetail data capture - LLM prompt/output

## Phase 6 Checkpoint

With Phase 6 complete:

1. **File Copy**: Processed files copied to @index
2. **Duplicate Detection**: file_id based overwrite logic
3. **Backward Compatible**: Optional index_path configuration
4. **Metadata Tracking**: index_path, overwritten status recorded

The import pipeline can now output files to both session/output and @index directories, with automatic duplicate detection based on file_id.
