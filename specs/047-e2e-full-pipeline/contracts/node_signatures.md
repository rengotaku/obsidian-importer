# Node Contracts: E2E Full Pipeline Validation

**Date**: 2026-02-05
**Feature**: 047-e2e-full-pipeline

---

## Node: extract_topic (New)

### Purpose

LLM を使用して会話内容から topic（中分類）を抽出し、小文字に正規化する。

### Signature

```python
def extract_topic(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, dict]:
```

### Input

#### `partitioned_input`

- **Type**: `dict[str, Callable]`
- **Source**: `classified_items` PartitionedDataset
- **Item structure**:

```python
{
    "item_id": str,
    "file_id": str,
    "content": str,           # Markdown with frontmatter
    "genre": str,             # Already classified
    "metadata": dict,
    "generated_metadata": dict
}
```

#### `params`

- **Type**: `dict`
- **Source**: `params:organize` from parameters
- **Required keys**:
  - `ollama.model`: LLM model name
  - `ollama.base_url`: Ollama API URL

### Output

- **Type**: `dict[str, dict]`
- **Item structure**: Input item + `"topic"` field added

### Behavior

1. Iterate over `partitioned_input`
2. For each item:
   - Extract body text from content
   - Call LLM to extract topic (e.g., "AWS", "Kubernetes", "Python")
   - Normalize: lowercase only (`AWS` → `aws`)
   - Preserve spaces (`React Native` → `react native`)
   - If extraction fails: set `topic = ""`
3. Return items with `topic` field

### Topic Normalization Rules

| Rule | Before | After |
|------|--------|-------|
| 小文字化 | `AWS` | `aws` |
| 小文字化 | `Kubernetes` | `kubernetes` |
| スペース保持 | `React Native` | `react native` |
| 空許容 | (extraction failed) | `""` |

### Example

**Input**:
```python
{
    "content": "---\ntitle: RDSのパフォーマンス...\n---\n\nAWS RDSについて...",
    "genre": "engineer"
}
```

**LLM Output**: `"AWS"`

**Result**:
```python
{
    "content": "---\ntitle: RDSのパフォーマンス...\n---\n\nAWS RDSについて...",
    "genre": "engineer",
    "topic": "aws"  # Normalized
}
```

---

## Node: embed_frontmatter_fields (New)

### Purpose

`genre`, `topic`, `summary` を frontmatter に埋め込み、最終 Markdown を生成する。ファイル I/O なし。

### Signature

```python
def embed_frontmatter_fields(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, str]:
```

### Input

#### `partitioned_input`

- **Type**: `dict[str, Callable]`
- **Source**: `cleaned_items` PartitionedDataset
- **Item structure**:

```python
{
    "item_id": str,
    "file_id": str,
    "content": str,           # Markdown with frontmatter
    "genre": str,             # "engineer" | "business" | "economy" | "daily" | "other"
    "topic": str,             # LLM extracted, lowercase, empty allowed
    "output_filename": str,
    "metadata": dict,         # May contain "summary"
    "generated_metadata": dict  # May contain "summary"
}
```

#### `params`

- **Type**: `dict`
- **Source**: `params:organize` from parameters
- **Required keys**: None

### Output

- **Type**: `dict[str, str]`
- **Keys**: Sanitized filename (without `.md` extension)
- **Values**: Complete Markdown content with updated frontmatter

### Behavior

1. Iterate over `partitioned_input`
2. For each item:
   - Load item via callable
   - Extract `genre`, `topic`, `summary` from item
   - Parse existing frontmatter from `content`
   - Add/update fields: `genre`, `topic`, `summary`
   - Rebuild Markdown with updated frontmatter
   - Store in result dict with `output_filename` as key
3. Return result dict (no file I/O)

### Example

**Input item content**:
```markdown
---
title: RDSのパフォーマンスチューニング
created: 2025-12-18
tags:
  - rds
  - performance
source_provider: claude
file_id: 389c1d35f44f
normalized: true
---

## 要約

Amazon RDS のパフォーマンス最適化について...
```

**Item dict fields**:
```python
{
    "genre": "engineer",
    "topic": "aws",
    "metadata": {"summary": "Amazon RDS のパフォーマンス最適化について..."}
}
```

**Output content**:
```markdown
---
title: RDSのパフォーマンスチューニング
created: 2025-12-18
tags:
  - rds
  - performance
source_provider: claude
file_id: 389c1d35f44f
normalized: true
summary: Amazon RDS のパフォーマンス最適化について...
genre: engineer
topic: aws
---

## 要約

Amazon RDS のパフォーマンス最適化について...
```

### Example: Empty Topic

**Item dict fields**:
```python
{
    "genre": "daily",
    "topic": "",  # Empty - could not extract
    "metadata": {"summary": "キッザニアでは子供たちが..."}
}
```

**Output frontmatter**:
```yaml
---
...
genre: daily
topic: ""
---
```

---

## Helper: _embed_fields_in_frontmatter

### Signature

```python
def _embed_fields_in_frontmatter(
    content: str,
    genre: str,
    topic: str,
    summary: str,
) -> str:
```

### Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | str | Markdown with YAML frontmatter |
| `genre` | str | Genre classification |
| `topic` | str | Topic (may be empty) |
| `summary` | str | Summary text (may be empty) |

### Output

- **Type**: `str`
- **Content**: Markdown with updated frontmatter

### Behavior

1. Check if content starts with `---\n`
2. Find closing `---` delimiter
3. Parse YAML frontmatter
4. Add fields: `summary`, `genre`, `topic`
5. Preserve existing field order
6. Serialize frontmatter back to YAML
7. Return reconstructed Markdown

### Edge Cases

| Case | Behavior |
|------|----------|
| No frontmatter | Add frontmatter with new fields |
| Empty summary | Add `summary: ""` |
| Empty topic | Add `topic: ""` |
| Invalid YAML | Log warning, return original content |
| Missing closing `---` | Treat as no frontmatter |

---

## Pipeline Node Registration

### organize/pipeline.py

```python
from .nodes import (
    classify_genre,
    extract_topic,  # NEW
    normalize_frontmatter,
    clean_content,
    embed_frontmatter_fields,  # NEW (replaces move_to_vault)
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
                func=embed_frontmatter_fields,  # NEW (replaces move_to_vault)
                inputs=["cleaned_items", "params:organize"],
                outputs="organized_notes",
                name="embed_frontmatter_fields",
            ),
        ]
    )
```

### DataCatalog Entry

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

## Removed Nodes

### determine_vault_path (Removed)

**Reason**: `vault_path` は廃止。代わりに `topic` を使用。

### move_to_vault (Removed)

**Reason**: ファイル I/O を廃止。`embed_frontmatter_fields` に置き換え。

---

## Backward Compatibility

### Changes Summary

| Old | New | Notes |
|-----|-----|-------|
| `determine_vault_path` | `extract_topic` | topic 抽出に変更 |
| `move_to_vault` | `embed_frontmatter_fields` | ファイル I/O 廃止 |
| `vault_path` field | `topic` field | frontmatter フィールド変更 |

### Test Updates Required

1. `tests/pipelines/organize/test_nodes.py`:
   - Remove `test_determine_vault_path_*` tests
   - Remove `test_move_to_vault_*` tests
   - Add `test_extract_topic_*` tests
   - Add `test_embed_frontmatter_fields_*` tests

2. `tests/e2e/test_golden_comparator.py`:
   - Update `SAMPLE_GOLDEN` with `genre`, `topic` fields
   - Add tests for `topic` empty case
