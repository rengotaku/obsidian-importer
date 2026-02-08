# Phase 1 Output: Setup

## Completed Tasks

- T001: Read Makefile `test-e2e` target (lines 117-160). Current flow: Ollama check → test data prep → Extract (parse_claude_zip) → verify 3 parsed items → Transform (extract_knowledge) → verify LLM output → cleanup.
- T002: Read `conf/test/catalog.yml`. Test environment uses `data/test/` directory. `markdown_notes` outputs to `data/test/07_model_output/notes/*.md`.
- T003: Read `format_markdown` node (nodes.py:160-224). Builds YAML frontmatter (title, created, tags, source_provider, file_id, normalized) + body (summary + summary_content). Outputs `{sanitized_filename: {**item, "content": markdown_content}}`.
- T004: Read existing transform tests. TestFormatMarkdown covers: frontmatter values, summary inclusion, tags list, output filename patterns.
- T005: Created directory structure: `tests/e2e/__init__.py`, `tests/fixtures/golden/`
- T006: Generated this phase output.

## Key Findings

### Current test-e2e flow (to be modified)
1. Ollama check
2. Test data prep (`data/test/` directories, copy `claude_test.zip`)
3. Extract: `kedro run --env=test --to-nodes=parse_claude_zip`
4. Verify: 3 parsed JSON files
5. Transform: `kedro run --env=test --from-nodes=extract_knowledge --to-nodes=extract_knowledge`
6. Verify: transformed items exist
7. Cleanup

### Target flow (after this feature)
1. Ollama check
2. Test data prep
3. Pipeline: `kedro run --env=test --to-nodes=format_markdown` (one-shot to final output)
4. Golden comparison: `python -m tests.e2e.golden_comparator --actual data/test/07_model_output/notes --golden tests/fixtures/golden --threshold 0.9`
5. Cleanup

### format_markdown output structure
```yaml
---
title: <title>
created: <date>
tags:
  - <tag1>
  - <tag2>
source_provider: <provider>
file_id: <sha256_hash>
normalized: true
---

## 要約

<summary>

<summary_content>
```

### Test fixture
- `tests/fixtures/claude_test.zip` contains 3 conversations
- Expected: 3 Markdown files in `data/test/07_model_output/notes/`
