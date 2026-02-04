# Data Model: @index フォルダ内再帰的Markdown処理

**Feature**: 006-index-markdown-process
**Date**: 2026-01-12

## Entities

### TargetFile

`@index/` 以下で検出された処理対象 Markdown ファイル。

| Field | Type | Description |
|-------|------|-------------|
| path | Path | ファイルの絶対パス |
| relative_path | str | @index/ からの相対パス |
| filename | str | ファイル名（拡張子含む） |
| depth | int | @index/ からの階層深度（直下=0） |

**Derived Properties**:
- `is_in_subfolder`: `depth > 0`

---

### ExclusionRule

除外パターンを定義するルール。

| Field | Type | Description |
|-------|------|-------------|
| pattern | str | 除外パターン（glob形式またはprefix） |
| type | Literal["prefix", "glob", "exact"] | パターンの種類 |
| description | str | ルールの説明 |

**Default Rules**:
```python
DEFAULT_EXCLUSIONS = [
    {"pattern": ".", "type": "prefix", "description": "隠しファイル/フォルダ"},
    {"pattern": ".obsidian", "type": "exact", "description": "Obsidian設定フォルダ"},
]
```

---

### ProcessingResult

各ファイルの処理結果。

| Field | Type | Description |
|-------|------|-------------|
| source_path | Path | 元のファイルパス |
| dest_path | Path | None | 移動先パス（移動した場合） |
| status | Literal["moved", "skipped", "error"] | 処理結果ステータス |
| genre | str | None | 判定されたジャンル |
| error_message | str | None | エラー詳細（エラー時のみ） |

---

### ScanResult

スキャン結果の集約。

| Field | Type | Description |
|-------|------|-------------|
| total_files | int | 検出されたファイル総数 |
| direct_files | int | @index/ 直下のファイル数 |
| subfolder_files | int | サブフォルダ内のファイル数 |
| excluded_count | int | 除外されたファイル数 |
| files | list[TargetFile] | 処理対象ファイルリスト |

---

## State Transitions

### File Processing Flow

```
[Detected] → [Excluded?] → [Processing] → [Moved/Skipped/Error]
     │            │
     │            └── Yes → (not in files list)
     │
     └── No → Continue
```

### Batch Processing States

```
[Scanning] → [Preview] → [Confirmed?] → [Processing] → [Complete]
                              │
                              └── No → [Cancelled]
```

---

## Relationships

```
ScanResult
    └── contains many → TargetFile

ExclusionRule
    └── filters → TargetFile (during scan)

ProcessingResult
    └── references → TargetFile.path
```

---

## Validation Rules

### TargetFile
- `path` must exist and be a file
- `path` must end with `.md`
- `path` must be under `@index/` directory

### ProcessingResult
- If `status == "moved"`, `dest_path` must not be None
- If `status == "error"`, `error_message` must not be None
