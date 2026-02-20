# Data Model: Organize パイプラインの Obsidian Vault 直接出力対応

**Date**: 2026-02-20
**Branch**: 059-organize-vault-output

## Entities

### OrganizedFile

ジャンル分類済みの Markdown ファイル。

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| partition_key | str | ファイル識別子 | PartitionedDataset key |
| content | str | Markdown コンテンツ（frontmatter 含む） | ファイル内容 |
| genre | str | ジャンル分類 (ai, devops, engineer, ...) | frontmatter |
| topic | str | トピック (python, aws, ...) | frontmatter |
| file_path | Path | ソースファイルパス | PartitionedDataset |

**Extraction from frontmatter**:

```yaml
---
title: Example
genre: ai
topic: python
---
```

### VaultDestination

出力先情報。

| Field | Type | Description |
|-------|------|-------------|
| vault_name | str | Vault 名 (エンジニア, ビジネス, ...) |
| subfolder | str \| None | サブフォルダ (topic から派生) |
| file_name | str | 出力ファイル名 |
| full_path | Path | 完全なファイルパス |

**Path Construction**:

```
{vault_base_path}/{vault_name}/{subfolder}/{file_name}
```

- `subfolder` が空の場合: `{vault_base_path}/{vault_name}/{file_name}`

### ConflictInfo

競合情報。

| Field | Type | Description |
|-------|------|-------------|
| source_file | Path | ソースファイルパス |
| destination | Path | 出力先パス |
| conflict_type | str | "exists" (現在は1種類のみ) |
| existing_size | int | 既存ファイルのサイズ |
| existing_mtime | datetime | 既存ファイルの更新日時 |

### VaultMapping

genre から Vault 名へのマッピング設定。

| Field | Type | Description |
|-------|------|-------------|
| genre | str | ジャンル名 |
| vault_name | str | 出力先 Vault 名 |

**Default Mapping** (parameters.yml):

```yaml
genre_vault_mapping:
  ai: "エンジニア"
  devops: "エンジニア"
  engineer: "エンジニア"
  business: "ビジネス"
  economy: "経済"
  health: "日常"
  parenting: "日常"
  travel: "日常"
  lifestyle: "日常"
  daily: "日常"
  other: "その他"
```

### CopyResult

コピー結果。

| Field | Type | Description |
|-------|------|-------------|
| source | Path | ソースファイルパス |
| destination | Path \| None | 出力先パス（skip の場合 None） |
| status | str | "copied", "skipped", "overwritten", "incremented", "error" |
| error_message | str \| None | エラーメッセージ |

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ data/07_model_output/organized/*.md (PartitionedDataset)        │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ read_organized_files node                                        │
│ - Parse frontmatter                                              │
│ - Extract genre, topic                                           │
│ - Return: dict[partition_key, OrganizedFile]                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ resolve_vault_destination node                                   │
│ - Apply genre → Vault mapping                                    │
│ - Sanitize topic for folder name                                 │
│ - Return: dict[partition_key, VaultDestination]                  │
└─────────────────────────────────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               │                               │
               ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────────────┐
│ organize_preview         │    │ organize_to_vault                │
│ pipeline                 │    │ pipeline                         │
├──────────────────────────┤    ├──────────────────────────────────┤
│ check_conflicts node     │    │ copy_to_vault node               │
│ - Check existing files   │    │ - Handle conflicts               │
│ - Return: ConflictInfo[] │    │ - Copy files                     │
│                          │    │ - Return: CopyResult[]           │
│ log_preview_summary node │    │                                  │
│ - Log destinations       │    │ log_copy_summary node            │
│ - Log conflicts          │    │ - Log results                    │
│ - Log genre distribution │    │                                  │
└──────────────────────────┘    └──────────────────────────────────┘
```

## Validation Rules

### OrganizedFile

- `genre` は空でも可（"other" として扱う）
- `topic` は空でも可（Vault 直下に配置）
- `content` は必須

### VaultDestination

- `vault_name` は空不可
- `file_name` は空不可
- `full_path` は絶対パス

### Topic Sanitization

```python
def sanitize_topic(topic: str) -> str:
    """Topic をフォルダ名として使用可能な形式に正規化。

    - スラッシュ、バックスラッシュ → アンダースコア
    - 先頭・末尾の空白を除去
    - 空文字の場合はそのまま返す
    """
    if not topic:
        return ""
    sanitized = topic.replace("/", "_").replace("\\", "_")
    return sanitized.strip()
```

## State Transitions

このパイプラインは状態遷移を持たない（ステートレス）。
各実行は独立しており、前回の実行状態に依存しない。
