# Research: E2E Full Pipeline Validation

**Date**: 2026-02-05
**Feature**: 047-e2e-full-pipeline

## Summary

This document consolidates research findings for extending E2E tests from `format_markdown` to full Organize pipeline completion.

---

## R1: Pipeline Data Flow Analysis

### Question
How does data flow from `format_markdown` to `move_to_vault`?

### Findings

**Current Pipeline DAG**:
```
markdown_notes (PartitionedDataset)
    ↓
classify_genre → classified_items
    ↓
normalize_frontmatter → normalized_items
    ↓
clean_content → cleaned_items
    ↓
determine_vault_path → vault_determined_items
    ↓
move_to_vault → organized_items (writes to Vaults/)
```

**New Pipeline DAG** (after clarification):
```
markdown_notes (PartitionedDataset)
    ↓
classify_genre → classified_items
    ↓
extract_topic (NEW) → topic_extracted_items
    ↓
normalize_frontmatter → normalized_items
    ↓
clean_content → cleaned_items
    ↓
embed_frontmatter_fields (NEW) → organized_notes (no file I/O)
```

### Decision
Replace `determine_vault_path` with `extract_topic`. Replace `move_to_vault` with `embed_frontmatter_fields`.

### Alternatives Considered
1. **Keep determine_vault_path**: Rejected - `vault_path` is no longer needed
2. **Mock file system in tests**: Rejected - spec explicitly wants no Vault writes

---

## R2: Frontmatter Structure Comparison

### Question
What fields are in current golden files vs. what Organize pipeline adds?

### Findings

**Current golden files** (format_markdown output):
```yaml
---
title: キッザニアの仕事体験と給料システム
created: 2025-12-18
tags: []
source_provider: claude
file_id: 389c1d35f44f
normalized: true
---
```

**Target golden files** (after clarification):
```yaml
---
title: キッザニアの仕事体験と給料システム
created: 2025-12-18
tags:
  - キッザニア
  - 職業体験
source_provider: claude
file_id: 389c1d35f44f
normalized: true
summary: キッザニアでは子供たちが様々な職業を体験し...
genre: daily
topic: ""
---
```

### Frontmatter 階層構造

| Level | Field | Example | Required | Empty Allowed |
|-------|-------|---------|----------|---------------|
| 大分類 | `genre` | `engineer` | Yes | No |
| 中分類 | `topic` | `aws` | Yes | Yes |
| 詳細 | `tags` | `["rds", "lambda"]` | Yes | Yes (empty list) |

### Decision
階層構造を採用（genre → topic → tags）。`vault_path` は廃止。

---

## R3: Topic Extraction Rules

### Question
How should `topic` be extracted and normalized?

### Findings (from clarification)

1. **LLM 抽出**: 会話内容から主題を抽出
2. **小文字正規化**: `AWS` → `aws`
3. **スペース保持**: `React Native` → `react native`
4. **空許容**: 抽出できない場合は空文字 `""`

### Topic Examples by Genre

| Genre | Topic Examples |
|-------|----------------|
| `engineer` | `aws`, `kubernetes`, `python`, `react`, `database` |
| `business` | `management`, `communication`, `marketing` |
| `economy` | `stock`, `crypto`, `real estate` |
| `daily` | `cooking`, `travel`, `health` |
| `other` | (any or empty) |

### Decision
新規ノード `extract_topic` を追加。LLM 呼び出し + 小文字正規化。

---

## R4: Required Keys for golden_comparator

### Question
What keys does `calculate_frontmatter_similarity` check?

### Findings (from tests/e2e/golden_comparator.py)

**Key handling**:
- **Key existence** (30% weight): Compares `actual_keys & golden_keys` / `len(golden_keys)`
- **file_id** (40% weight): Exact match required
- **title** (20% weight): difflib.SequenceMatcher
- **tags** (10% weight): Set intersection ratio

**Dynamic behavior**: Function iterates over `golden.keys()`, so new keys (`genre`, `topic`) are automatically included in key existence check.

### Decision
No code change needed in `calculate_frontmatter_similarity`. New keys will be automatically checked via key existence scoring.

### Test Updates Needed
- Update `SAMPLE_GOLDEN` and other test fixtures with `genre`, `topic` fields
- Add tests for empty `topic` scenarios

---

## R5: Removed Nodes

### determine_vault_path

**Reason**: `vault_path` は廃止。代わりに `topic` を使用。

**Before**:
```python
def determine_vault_path(partitioned_input, params):
    # Map genre to vault path
    vault_path = vaults.get(genre, "Vaults/その他/")
    item["vault_path"] = vault_path
```

**After**: Node removed. No `vault_path` field.

### move_to_vault

**Reason**: ファイル I/O を廃止。`embed_frontmatter_fields` に置き換え。

**Before**:
```python
def move_to_vault(partitioned_input, params):
    # Write file to Vaults/ directory
    full_path.write_text(content, encoding="utf-8")
```

**After**: `embed_frontmatter_fields` - no file I/O, embeds fields in frontmatter.

---

## Consolidated Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| File I/O | Remove from pipeline | Spec requirement, simplifies testing |
| `vault_path` | Remove from frontmatter | Replaced by `topic` hierarchy |
| `topic` field | Add to frontmatter | New middle classification level |
| Topic extraction | LLM + lowercase | Flexible, normalized |
| Node changes | `extract_topic` (new), `embed_frontmatter_fields` (new) | Clean separation of concerns |
| Test fixtures | Update with `genre`, `topic` | Required for accurate tests |
