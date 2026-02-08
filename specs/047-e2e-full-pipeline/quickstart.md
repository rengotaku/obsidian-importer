# Quickstart: E2E Full Pipeline Validation

**Date**: 2026-02-05
**Feature**: 047-e2e-full-pipeline

---

## Prerequisites

- Python 3.11+
- Ollama running locally (`http://localhost:11434`)
- Virtual environment activated (`.venv/bin/activate`)

---

## Implementation Order

### Phase 1: Pipeline Modification

#### Step 1.1: Add extract_topic node

**File**: `src/obsidian_etl/pipelines/organize/nodes.py`

```python
def extract_topic(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, dict]:
    """Extract topic from content using LLM.

    Args:
        partitioned_input: classified_items
        params: organize params (ollama settings)

    Returns:
        Items with "topic" field added (lowercase, empty allowed)
    """
    result = {}

    for key, load_func in partitioned_input.items():
        item = load_func()
        content = item.get("content", "")

        # Extract topic via LLM
        topic = _extract_topic_via_llm(content, params)

        # Normalize: lowercase only
        topic = topic.lower() if topic else ""

        item["topic"] = topic
        result[key] = item

    return result
```

#### Step 1.2: Add embed_frontmatter_fields node

**File**: `src/obsidian_etl/pipelines/organize/nodes.py`

```python
def embed_frontmatter_fields(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, str]:
    """Embed genre, topic, summary into frontmatter content.

    No file I/O - replaces move_to_vault.
    """
    result = {}

    for key, load_func in partitioned_input.items():
        item = load_func()
        content = item.get("content", "")
        genre = item.get("genre", "other")
        topic = item.get("topic", "")

        # Extract summary
        summary = _get_summary(item)

        # Embed fields in frontmatter
        updated_content = _embed_fields_in_frontmatter(content, genre, topic, summary)

        # Use output_filename as key
        output_filename = item.get("output_filename", key)
        result[output_filename] = updated_content

    return result
```

#### Step 1.3: Update organize/pipeline.py

**File**: `src/obsidian_etl/pipelines/organize/pipeline.py`

```python
from .nodes import (
    classify_genre,
    extract_topic,  # NEW
    normalize_frontmatter,
    clean_content,
    embed_frontmatter_fields,  # NEW
)

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=classify_genre,
                inputs=["markdown_notes", "params:organize", "existing_classified_items"],
                outputs="classified_items",
                name="classify_genre",
            ),
            node(
                func=extract_topic,  # NEW
                inputs=["classified_items", "params:organize"],
                outputs="topic_extracted_items",
                name="extract_topic",
            ),
            node(
                func=normalize_frontmatter,
                inputs=["topic_extracted_items", "params:organize"],
                outputs="normalized_items",
                name="normalize_frontmatter",
            ),
            node(
                func=clean_content,
                inputs="normalized_items",
                outputs="cleaned_items",
                name="clean_content",
            ),
            node(
                func=embed_frontmatter_fields,  # NEW
                inputs=["cleaned_items", "params:organize"],
                outputs="organized_notes",
                name="embed_frontmatter_fields",
            ),
        ]
    )
```

#### Step 1.4: Update DataCatalog

**File**: `conf/base/catalog.yml` or `conf/test/catalog.yml`

```yaml
topic_extracted_items:
  type: PartitionedDataset
  path: data/03_primary/topic_extracted
  dataset:
    type: json.JSONDataset

organized_notes:
  type: PartitionedDataset
  path: data/07_model_output/organized
  dataset:
    type: text.TextDataset
    save_args:
      encoding: utf-8
  filename_suffix: ".md"
```

---

### Phase 2: Makefile Updates

#### Step 2.1: Update test-e2e

**File**: `Makefile`

Remove `--to-nodes=format_markdown`:
```makefile
test-e2e:
    # ... existing setup ...
    @cd $(BASE_DIR) && $(PYTHON) -m kedro run --env=test
    # ... update output dir ...
    @cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m tests.e2e.golden_comparator \
        --actual $(TEST_DATA_DIR)/07_model_output/organized \
        --golden tests/fixtures/golden \
        --threshold 0.8
```

#### Step 2.2: Update test-e2e-update-golden

Same changes:
```makefile
test-e2e-update-golden:
    # ... existing setup ...
    @cd $(BASE_DIR) && $(PYTHON) -m kedro run --env=test
    # ...
    @cp $(TEST_DATA_DIR)/07_model_output/organized/*.md tests/fixtures/golden/
```

---

### Phase 3: Test Updates

#### Step 3.1: Add test_extract_topic tests

**File**: `tests/pipelines/organize/test_nodes.py`

```python
def test_extract_topic_normalizes_to_lowercase(self):
    """topic が小文字に正規化される"""
    # LLM が "AWS" を返した場合、"aws" に正規化
    ...

def test_extract_topic_preserves_spaces(self):
    """topic のスペースが保持される"""
    # "React Native" → "react native"
    ...

def test_extract_topic_empty_on_failure(self):
    """抽出失敗時は空文字"""
    ...
```

#### Step 3.2: Add test_embed_frontmatter_fields tests

**File**: `tests/pipelines/organize/test_nodes.py`

```python
def test_embed_frontmatter_fields_adds_genre(self):
    """genre が frontmatter に追加される"""
    ...

def test_embed_frontmatter_fields_adds_topic(self):
    """topic が frontmatter に追加される"""
    ...

def test_embed_frontmatter_fields_adds_empty_topic(self):
    """空の topic が frontmatter に追加される"""
    ...

def test_embed_frontmatter_fields_adds_summary(self):
    """summary が frontmatter に追加される"""
    ...

def test_embed_frontmatter_fields_no_file_write(self):
    """ファイルシステムへの書き込みが発生しない"""
    ...
```

#### Step 3.3: Update test_golden_comparator.py

**File**: `tests/e2e/test_golden_comparator.py`

Update `SAMPLE_GOLDEN` with new fields:
```python
SAMPLE_GOLDEN = """\
---
title: Python asyncio discussion
created: 2026-01-15
tags:
  - python
  - asyncio
source_provider: claude
file_id: a1b2c3d4e5f6
normalized: true
summary: asyncio is a library for writing concurrent code using async/await syntax.
genre: engineer
topic: python
---

## 要約
...
"""
```

---

### Phase 4: Golden File Regeneration

#### Step 4.1: Regenerate golden files

```bash
make test-e2e-update-golden
```

#### Step 4.2: Verify structure

Check that new golden files contain:
- `genre` field
- `topic` field (may be empty)
- `summary` field in frontmatter

```bash
head -20 tests/fixtures/golden/*.md
```

#### Step 4.3: Commit golden files

```bash
git add tests/fixtures/golden/
git commit -m "chore: update golden files with genre/topic frontmatter"
```

---

### Phase 5: Verification

#### Step 5.1: Run unit tests

```bash
make test
```

All existing tests should pass.

#### Step 5.2: Run E2E test

```bash
make test-e2e
```

Should report 100% similarity for self-comparison.

#### Step 5.3: Verify no Vault writes

```bash
ls -la Vaults/
# Should be unchanged from before kedro run
```

---

## Troubleshooting

### E2E test fails with "Golden files not found"

Run `make test-e2e-update-golden` first.

### Similarity below 80%

1. Check LLM output variability
2. Verify frontmatter structure matches
3. Run with lower threshold for debugging: `--threshold 0.5`

### Topic extraction always empty

1. Check Ollama is running
2. Verify LLM prompt in `extract_topic`
3. Check content has extractable topic

### Organize tests fail

1. Check `extract_topic` implementation
2. Check `embed_frontmatter_fields` implementation
3. Verify frontmatter parsing handles all edge cases

---

## Success Criteria Checklist

- [ ] `make test` passes (all unit tests)
- [ ] `make test-e2e` passes (80% threshold)
- [ ] Golden files contain `genre`, `topic`, `summary`
- [ ] No files written to `Vaults/` directory during pipeline run
- [ ] `move_to_vault` file I/O removed
- [ ] `determine_vault_path` replaced with `extract_topic`
