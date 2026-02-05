# Data Model: E2E Full Pipeline Validation

**Date**: 2026-02-05
**Feature**: 047-e2e-full-pipeline

---

## Frontmatter 階層構造

```
genre（大分類）
  └── topic（中分類）
        └── tags（詳細タグ）
```

| Level | Field | Example | Description |
|-------|-------|---------|-------------|
| 大分類 | `genre` | `engineer` | Vault トップフォルダ（固定5値） |
| 中分類 | `topic` | `aws` | サブフォルダ（LLM 抽出、空許容） |
| 詳細 | `tags` | `["rds", "lambda"]` | タグリスト（LLM 抽出） |

**フォルダ構造例**:
- `Vaults/エンジニア/aws/RDSのパフォーマンスチューニング.md`
- `Vaults/エンジニア/ファイル.md`（topic 空の場合）

---

## Entity: FinalMarkdownOutput

The final Markdown output after Organize pipeline completion.

### Fields

| Field | Type | Required | Empty Allowed | Source | Description |
|-------|------|----------|---------------|--------|-------------|
| `title` | string | Yes | No | LLM extraction | Japanese title |
| `created` | string | Yes | No | ParsedItem.created_at | ISO date (YYYY-MM-DD) |
| `tags` | list[string] | Yes | Yes (empty list) | LLM extraction | Detail tags |
| `source_provider` | string | Yes | No | ParsedItem | "claude", "openai", "github" |
| `file_id` | string | Yes | No | SHA256 hash | 12-char truncated hash |
| `normalized` | boolean | Yes | No | Always `true` | Normalization flag |
| `summary` | string | Yes | No | LLM extraction | Japanese summary |
| `genre` | string | Yes | No | classify_genre | Genre classification (top folder) |
| `topic` | string | Yes | Yes (empty string) | LLM extraction | Topic classification (subfolder) |

### Genre Values (Fixed)

| Value | Japanese | Description |
|-------|----------|-------------|
| `engineer` | エンジニア | Technical content (programming, infra, etc.) |
| `business` | ビジネス | Business skills, management |
| `economy` | 経済 | Economy, finance, market |
| `daily` | 日常 | Daily life, hobbies |
| `other` | その他 | Uncategorized |

### Topic Rules

| Rule | Description | Example |
|------|-------------|---------|
| LLM 抽出 | 会話内容から主題を抽出 | "AWS Lambda について" → `aws` |
| 小文字正規化 | 大文字を小文字に変換 | `AWS` → `aws` |
| スペース保持 | スペースはそのまま | `React Native` → `react native` |
| 空許容 | 抽出できない場合は空文字 | `""` |

### Validation Rules

1. `title` - 非空文字列
2. `created` - `YYYY-MM-DD` 形式
3. `tags` - リスト型（空リスト可）
4. `source_provider` - `claude` | `openai` | `github`
5. `file_id` - 12文字（SHA256 先頭12文字）
6. `normalized` - `true` 固定
7. `summary` - 非空文字列
8. `genre` - `engineer` | `business` | `economy` | `daily` | `other`
9. `topic` - 文字列（空許容、小文字のみ）

---

## Entity: OrganizedItem (Internal)

Internal representation during Organize pipeline processing.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_id` | string | Yes | Partition key |
| `file_id` | string | Yes | SHA256 hash (full) |
| `content` | string | Yes | Markdown content |
| `genre` | string | Yes | Classified genre |
| `topic` | string | Yes | Extracted topic (empty allowed) |
| `output_filename` | string | Yes | Sanitized filename |
| `metadata` | dict | Optional | Original metadata |

### State Transitions

```
ParsedItem
    ↓ [transform pipeline]
TransformedItem (with generated_metadata)
    ↓ [format_markdown]
MarkdownNote (dict[filename, content])
    ↓ [classify_genre]
ClassifiedItem (+ genre)
    ↓ [extract_topic] (NEW)
TopicExtractedItem (+ topic)
    ↓ [normalize_frontmatter]
NormalizedItem (frontmatter cleaned)
    ↓ [clean_content]
CleanedItem (body cleaned)
    ↓ [embed_frontmatter_fields]
FinalMarkdownOutput (genre/topic in frontmatter)
```

---

## Frontmatter YAML Format

### Example: With Topic

```yaml
---
title: RDSのパフォーマンスチューニング
created: 2025-12-18
tags:
  - rds
  - performance
  - mysql
source_provider: claude
file_id: 389c1d35f44f
normalized: true
summary: Amazon RDS のパフォーマンス最適化について、インデックス設計からパラメータチューニングまで解説。
genre: engineer
topic: aws
---

## 要約

Amazon RDS のパフォーマンス最適化について...
```

### Example: Without Topic (Empty)

```yaml
---
title: キッザニアの仕事体験と給料システム
created: 2025-12-18
tags:
  - キッザニア
  - 職業体験
source_provider: claude
file_id: 8a7b6c5d4e3f
normalized: true
summary: キッザニアでは子供たちが様々な職業を体験し、専用通貨「キッゾ」を給料として受け取れます。
genre: daily
topic: ""
---

## 要約

キッザニアでは子供たちが様々な職業を体験し...
```

### Field Order

Recommended order for consistency:
1. `title`
2. `created`
3. `tags`
4. `source_provider`
5. `file_id`
6. `normalized`
7. `summary`
8. `genre`
9. `topic`

---

## Similarity Scoring (golden_comparator)

### Weights

| Component | Weight | Description |
|-----------|--------|-------------|
| Frontmatter | 0.3 | Key existence + specific field matches |
| Body | 0.7 | difflib.SequenceMatcher ratio |

### Frontmatter Scoring

| Check | Weight | Description |
|-------|--------|-------------|
| Key existence | 0.3 | `len(actual_keys & golden_keys) / len(golden_keys)` |
| file_id | 0.4 | Exact match (1.0 or 0.0) |
| title | 0.2 | difflib.SequenceMatcher ratio |
| tags | 0.1 | Set intersection ratio |

**Note**: `genre` と `topic` は key existence チェックに含まれる（動的）。

### Threshold

- Default: 80% (`--threshold 0.8`)
- Self-comparison: 100% expected

---

## Topic Examples by Genre

| Genre | Topic Examples |
|-------|----------------|
| `engineer` | `aws`, `kubernetes`, `python`, `react`, `database`, `linux` |
| `business` | `management`, `communication`, `marketing`, `strategy` |
| `economy` | `stock`, `crypto`, `real estate`, `macro` |
| `daily` | `cooking`, `travel`, `health`, `hobby` |
| `other` | (any or empty) |
