# Data Model: Filename Normalize

**Date**: 2026-01-10
**Branch**: `002-filename-normalize`

## Entities

### SourceFile

元ファイル（@index内のファイル）の表現。

| Field | Type | Description |
|-------|------|-------------|
| path | Path | ファイルの絶対パス |
| original_filename | str | 元のファイル名（拡張子含む） |
| content | str | ファイル内容（frontmatter除く、最大4000文字） |
| extracted_date | str | ファイル名から抽出した日付（YYYY-MM-DD形式）、なければ空文字 |

### NormalizedFile

正規化後のファイルの表現。

| Field | Type | Description |
|-------|------|-------------|
| destination_path | Path | 移動先の絶対パス |
| filename | str | 正規化後のファイル名（拡張子含む） |
| frontmatter | Frontmatter | YAML frontmatter データ |
| content | str | 整形済み本文 |

### Frontmatter

ファイルの YAML frontmatter データ。

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| title | str | ファイルのタイトル（**ファイル名と一致**） | Yes |
| tags | list[str] | タグリスト（3-5個） | Yes |
| created | str | 作成日（YYYY-MM-DD形式） | No |
| normalized | bool | 正規化済みフラグ（常に `true`） | Yes |

### FilenameTransformation

ファイル名変換の処理パイプライン。

```
[SourceFile.original_filename]
    ↓
[extract_date_from_filename()] → extracted_date
    ↓
[Ollama API] → frontmatter.title
    ↓
[normalize_filename(frontmatter.title)] → NormalizedFile.filename
    ↓
[get_destination_path()] → NormalizedFile.destination_path
```

## Transformation Rules

### Date Extraction

| Pattern | Example | Extracted |
|---------|---------|-----------|
| `YYYY-MM-DD-*` | `2022-10-17-Title.md` | `2022-10-17` |
| `YYYY_MM_DD_*` | `2022_10_17_Title.md` | `2022-10-17` |
| `YYYY-M-D-*` | `2022-10-7-Title.md` | `2022-10-7` |
| No date | `Title.md` | `""` |

### Filename Normalization

| Rule | Before | After |
|------|--------|-------|
| Ollama生成タイトル使用 | `Pull-a-docker-image.md` | `Docker imageをECRからPullする方法.md` |
| 禁止文字置換 | `Title: Subtitle.md` | `Title_ Subtitle.md` |
| 長さ制限 | `Very long title...（200文字超）` | `Very long title...（単語境界で切り詰め）` |
| フォールバック | （Ollamaが空を返した場合） | 元ファイル名から日付除去 |

### Illegal Characters

ファイルシステム禁止文字（すべてアンダースコアに置換）:

```
< > : " / \ | ? *
```

### Duplicate Handling

| 状況 | 結果 |
|------|------|
| ファイルが存在しない | `Title.md` |
| `Title.md` が存在 | `Title_1.md` |
| `Title.md` と `Title_1.md` が存在 | `Title_2.md` |

## State Transitions

```
[SourceFile in @index/]
    ↓ normalize_file()
[NormalizationResult]
    ↓ process_single_file()
[NormalizedFile in {Vault}/]
    ↓
[SourceFile deleted]
```

## Validation Rules

### Frontmatter Validation

- `title`: 非空、200文字以内
- `tags`: 1-5個のリスト
- `created`: `YYYY-MM-DD` 形式または空
- `normalized`: `true`

### Filename Validation

- 非空
- 禁止文字なし
- 200文字以内
- `.md` 拡張子

## Relationships

```
SourceFile --[transforms to]--> NormalizedFile
NormalizedFile --[contains]--> Frontmatter
NormalizedFile.filename --[equals]--> Frontmatter.title + ".md"
```
