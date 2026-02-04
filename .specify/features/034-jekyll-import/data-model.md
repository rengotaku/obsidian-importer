# Data Model: Jekyll ブログインポート

**Feature**: 034-jekyll-import
**Date**: 2026-01-25

## Entities

### GitHubRepoInfo

GitHub URL から抽出されたリポジトリ情報。

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| owner | str | リポジトリオーナー | 非空、英数字・ハイフン・アンダースコア |
| repo | str | リポジトリ名 | 非空、英数字・ハイフン・アンダースコア・ドット |
| branch | str | ブランチ名 | 非空、デフォルト `master` または `main` |
| path | str | 対象ディレクトリパス | 非空、例: `_posts` |

**Derived Properties**:
- `clone_url`: `https://github.com/{owner}/{repo}.git`
- `full_path`: `{repo}/{path}`

---

### JekyllPost

ブログ記事のパース結果。

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| filename | str | 元ファイル名 | `.md` 拡張子、例: `2022-11-27-532.md` |
| filepath | Path | フルパス | 存在するファイル |
| raw_content | str | ファイル全体の内容 | 非空 |
| frontmatter | dict | パース済み YAML frontmatter | 辞書、title 推奨 |
| body | str | frontmatter 以降の本文 | 空可 |

**重要**: ファイル名の末尾（例: `532`）は記事IDであり、タイトルではない。タイトルは必ず `frontmatter.title` から取得する。

**State Transitions**:
```
discovered → parsed → converted → loaded
```

---

### ObsidianNote

変換後の Obsidian ノート。

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| title | str | ノートタイトル | Yes |
| created | str | 作成日 (YYYY-MM-DD) | Yes |
| tags | list[str] | タグリスト | No (default: []) |
| normalized | bool | 正規化フラグ | Yes (always True) |
| file_id | str | SHA256 ハッシュ | Yes |
| body | str | 本文 Markdown | Yes |

**Frontmatter Template**:
```yaml
---
title: "{title}"
created: "{created}"
tags: {tags}
normalized: true
file_id: "{file_id}"
---
```

---

## Relationships

```
GitHubRepoInfo (1) ─────contains────→ (N) JekyllPost
                                            │
                                            │ converts to
                                            ▼
                                     ObsidianNote
```

---

## Validation Rules

### GitHubRepoInfo Validation

| Rule | Condition | Error Message |
|------|-----------|---------------|
| URL Format | URL matches `https://github.com/.../tree/...` | "Invalid GitHub URL format" |
| Owner Valid | `^[a-zA-Z0-9_-]+$` | "Invalid repository owner" |
| Repo Valid | `^[a-zA-Z0-9._-]+$` | "Invalid repository name" |
| Path Non-empty | `len(path) > 0` | "Target path is required" |

### JekyllPost Validation

| Rule | Condition | Error Message |
|------|-----------|---------------|
| File Extension | filename.endswith('.md') | "Not a Markdown file" |
| Not Draft | frontmatter.get('draft') != True | "Draft post skipped" |
| Has Content | len(raw_content) > 0 | "Empty file" |

### ObsidianNote Validation

| Rule | Condition | Error Message |
|------|-----------|---------------|
| Title Present | len(title) > 0 | "Title is required" |
| Date Format | matches YYYY-MM-DD | "Invalid date format" |
| File ID | len(file_id) == 64 | "Invalid file_id hash" |

---

## Field Mapping (Jekyll → Obsidian)

| Source | Target | Transformation |
|--------|--------|----------------|
| `frontmatter.title` | `title` | そのまま、なければファイル名から |
| (see below) | `created` | 優先順位に従って抽出 |
| `frontmatter.tags` | `tags` | リスト化 |
| `frontmatter.categories` | `tags` に追加 | マージ |
| 本文中 `#tag` | `tags` に追加 | 正規表現で抽出・重複排除 |
| - | `normalized` | 常に `true` |
| raw_content hash | `file_id` | SHA256 |
| `body` | body | そのまま |

### 日付抽出優先順位 (`created` フィールド)

| Priority | Source | Example |
|----------|--------|---------|
| 1 | `frontmatter.date` | `date: 2024-09-10` |
| 2 | ファイル名 (Jekyll形式) | `2024-09-10-title.md` |
| 3 | タイトルから正規表現抽出 | `2024年9月10日のメモ` |
| 4 | 本文から正規表現抽出 | 本文先頭1000文字を検索 |
| 5 | フォールバック | 現在日時 |

**対応日付形式**:
- `YYYY-MM-DD` (例: 2024-09-10)
- `YYYY/MM/DD` (例: 2024/09/10)
- `YYYY年MM月DD日` (例: 2024年9月10日)

### タグ抽出ソース

| Priority | Source | Example |
|----------|--------|---------|
| 1 | `frontmatter.tags` | `tags: ["react"]` |
| 2 | `frontmatter.categories` | `categories: [devops]` |
| 3 | `frontmatter.keywords` | `keywords: ["react","プログラム"]` |
| 4 | 本文中 `#tag` | `#kubernetes #helm` |

**ハッシュタグ抽出ルール**:
- パターン: `#` + 英字で始まる英数字・ハイフン・アンダースコア
- 例: `#aws`, `#my-tag`, `#tag_name`
- 除外: `#123`（数字のみ）、`##heading`（見出し）

**Removed Fields** (Source → Obsidian):
- `layout` - テーマ用
- `permalink` - URL用
- `excerpt` - 抜粋
- `slug` - UUID形式のID
- `lastmod` - 最終更新日
- `headless` - Hugo用
- `draft` - 下書きフラグ（true ならスキップ）
- `private` - 非公開フラグ（true ならスキップ）

**Merged into tags**:
- `keywords` - タグに統合
