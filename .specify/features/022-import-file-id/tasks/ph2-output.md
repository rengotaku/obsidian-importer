# Phase 2 Output: User Story 1 - インポート時のfile_id自動付与

## Summary

Phase 2 completed successfully. Implemented file_id field in KnowledgeDocument and automatic file_id generation in cli.py.

## Completed Tasks

| Task | Description | Status |
|------|-------------|--------|
| T006 | Read previous phase output | Done |
| T007 | Add test for KnowledgeDocument.file_id field | Done |
| T008 | Add test for to_markdown() outputting file_id | Done |
| T009 | Add `file_id: str = ""` field to KnowledgeDocument | Done |
| T010 | Modify to_markdown() to include file_id in frontmatter | Done |
| T011 | Modify cli.py to generate file_id before writing | Done |
| T012 | Update chunk processing with unique file_id | Done |
| T013 | Run `make test` | PASS |
| T014 | Generate phase output | Done |

## Artifacts Modified

### 1. `development/scripts/llm_import/common/knowledge_extractor.py`

Added `file_id` field to KnowledgeDocument dataclass:

```python
@dataclass
class KnowledgeDocument:
    # ... existing fields ...
    code_snippets: list[CodeSnippet] = field(default_factory=list)
    file_id: str = ""  # NEW: 12-character hex hash ID
    normalized: bool = False
```

Modified `to_markdown()` to output file_id in frontmatter (only if non-empty):

```python
def to_markdown(self) -> str:
    # Frontmatter
    lines.append("---")
    # ... other fields ...
    lines.append(f"source_conversation: {self.source_conversation}")
    if self.file_id:
        lines.append(f"file_id: {self.file_id}")
    lines.append(f"normalized: {str(self.normalized).lower()}")
    lines.append("---")
```

### 2. `development/scripts/llm_import/cli.py`

Added import:

```python
from scripts.llm_import.common.file_id import generate_file_id
```

Added file_id generation for normal processing (T011):

```python
# Phase 2 output
document = result.document
output_filename = sanitize_filename(document.title) + ".md"
output_path = output_dir / output_filename

# Generate file_id before writing
content_for_hash = document.to_markdown()
relative_path = output_path.relative_to(output_dir.parent.parent)
document.file_id = generate_file_id(content_for_hash, relative_path)

after_content = document.to_markdown()
```

Added file_id generation for chunk processing (T012):

```python
for filename, result in chunk_results:
    if result.success:
        document = result.document
        output_filename = sanitize_filename(filename[:-3]) + ".md"
        output_path = output_dir / output_filename

        # Generate unique file_id for each chunk
        content_for_hash = document.to_markdown()
        relative_path = output_path.relative_to(output_dir.parent.parent)
        document.file_id = generate_file_id(content_for_hash, relative_path)

        after_content = document.to_markdown()
        output_path.write_text(after_content, encoding="utf-8")
```

### 3. `development/scripts/llm_import/tests/test_knowledge_extractor.py`

Added new test class `TestKnowledgeDocumentFileId` with 5 tests:

- `test_file_id_field_default_empty`: Verifies default value is empty string
- `test_file_id_field_can_be_set`: Verifies field can be set to a value
- `test_to_markdown_includes_file_id_in_frontmatter`: Verifies file_id appears in frontmatter
- `test_to_markdown_file_id_position_before_normalized`: Verifies file_id comes before normalized
- `test_to_markdown_empty_file_id_not_output`: Verifies empty file_id is not output

## Test Results

```
test_file_id_field_default_empty ... ok
test_file_id_field_can_be_set ... ok
test_to_markdown_includes_file_id_in_frontmatter ... ok
test_to_markdown_file_id_position_before_normalized ... ok
test_to_markdown_empty_file_id_not_output ... ok
```

All tests passed.

## Output Format

Generated Markdown files now include file_id in frontmatter:

```yaml
---
title: ナレッジタイトル
summary: 1行要約
created: 2026-01-18
source_provider: claude
source_conversation: abc123
file_id: a1b2c3d4e5f6
normalized: false
---
```

## Notes for Phase 3

Phase 3 can now use the generated file_id in ProcessedEntry (state.json):

- file_id is available on KnowledgeDocument after cli.py sets it
- Pass file_id when creating ProcessedEntry in state.add_entry()
- Add file_id field to ProcessedEntry dataclass

## Verification

To verify file_id generation works:

```bash
make llm-import LIMIT=1
# Check generated file in .staging/@index/
grep "file_id:" .staging/@index/*.md
```
