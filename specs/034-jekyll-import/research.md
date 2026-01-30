# Research: Jekyll ブログインポート

**Feature**: 034-jekyll-import
**Date**: 2026-01-25

## Research Topics

### 1. GitHub URL パース

**Decision**: 正規表現で URL を解析し、owner/repo/branch/path を抽出

**Rationale**:
- URL 形式は固定: `https://github.com/{owner}/{repo}/tree/{branch}/{path}`
- 外部ライブラリ不要、標準ライブラリ `re` で十分
- エッジケース（特殊文字、日本語パス）は URL エンコード済みで受け取る

**Pattern**:
```python
import re

GITHUB_URL_PATTERN = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/tree/(?P<branch>[^/]+)/(?P<path>.+)"
)

def parse_github_url(url: str) -> dict | None:
    match = GITHUB_URL_PATTERN.match(url)
    if not match:
        return None
    return match.groupdict()
```

**Alternatives considered**:
- urllib.parse: URL 分解のみで GitHub 固有の構造解析には不十分
- github3.py ライブラリ: 過剰、認証機能不要

---

### 2. git clone 戦略

**Decision**: `git clone --depth 1` + sparse-checkout で対象パスのみ取得

**Rationale**:
- 501 ファイルの Jekyll ブログでも、履歴不要なら高速
- sparse-checkout で `_posts` のみ取得可能（ディスク節約）
- 一時ディレクトリに clone し、処理後削除

**Implementation**:
```python
import subprocess
import tempfile

def clone_github_repo(owner: str, repo: str, branch: str, target_path: str) -> Path:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_url = f"https://github.com/{owner}/{repo}.git"
        clone_dir = Path(tmpdir) / repo

        # Sparse checkout setup
        subprocess.run([
            "git", "clone", "--depth", "1", "--filter=blob:none",
            "--sparse", "-b", branch, repo_url, str(clone_dir)
        ], check=True)

        subprocess.run([
            "git", "-C", str(clone_dir), "sparse-checkout", "set", target_path
        ], check=True)

        return clone_dir / target_path
```

**Alternatives considered**:
- GitHub API: レート制限（60回/時間）で 500 ファイル処理不可
- Archive ZIP ダウンロード: リポジトリ全体取得が必要
- Full clone: 履歴含め時間・ディスク浪費

---

### 3. Jekyll Frontmatter 変換

**Decision**: PyYAML で YAML パース、フィールド変換ルール適用

**Rationale**:
- Jekyll frontmatter は標準 YAML
- 変換ルールは単純なマッピング
- 不正 YAML はフォールバック（本文として処理）

**Conversion Rules**:

| Source Field | Obsidian Field | Notes |
|-------------|----------------|-------|
| `title` | `title` | そのまま（必須） |
| `date` | `created` | ISO 8601 → YYYY-MM-DD に正規化 |
| `tags` | `tags` | リスト形式に統一 |
| `categories` | `tags` に統合 | マージ |
| `keywords` | `tags` に統合 | マージ |
| 本文中 `#tag` | `tags` に追加 | 正規表現で抽出 |
| `layout` | 削除 | 不要 |
| `permalink` | 削除 | 不要 |
| `excerpt` | 削除 | 不要 |
| `slug` | 削除 | 不要（UUID形式） |
| `lastmod` | 削除 | 不要 |
| `headless` | 削除 | 不要 |
| `draft: true` | スキップ | 下書きは除外 |
| `private: true` | スキップ | 非公開は除外 |
| - | `normalized: true` | 追加 |
| - | `file_id` | SHA256 ハッシュ追加 |

**実際のファイル例** (`2022-11-27-532.md`):
```yaml
---
title: "propsの宣言のvalueの謎の？の意味"
draft: false
tags: ["react"]
private: false
slug: "60eb6716-a436-4885-9b37-d288c3ce2def"
date: "2020-01-20T15:12:41+09:00"
lastmod: "2020-01-20T15:12:41+09:00"
keywords: ["react","ベジプロ","プログ","プログラム"]
---
```
→ ファイル名の `532` は記事ID、タイトルは frontmatter.title から取得

**Implementation**:
```python
import yaml
import re

FRONTMATTER_PATTERN = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)

def parse_jekyll_frontmatter(content: str) -> tuple[dict, str]:
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content

    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}, content

    body = content[match.end():]
    return fm, body

def convert_frontmatter(jekyll_fm: dict, body: str) -> dict:
    obsidian_fm = {}

    # Title
    if "title" in jekyll_fm:
        obsidian_fm["title"] = jekyll_fm["title"]

    # Date -> created
    if "date" in jekyll_fm:
        date_str = str(jekyll_fm["date"])[:10]  # YYYY-MM-DD
        obsidian_fm["created"] = date_str

    # Tags + Categories + Body hashtags -> tags
    tags = []
    if "tags" in jekyll_fm:
        tags.extend(jekyll_fm["tags"] if isinstance(jekyll_fm["tags"], list) else [jekyll_fm["tags"]])
    if "categories" in jekyll_fm:
        cats = jekyll_fm["categories"]
        tags.extend(cats if isinstance(cats, list) else [cats])

    # Extract hashtags from body
    body_tags = extract_hashtags(body)
    tags.extend(body_tags)

    if tags:
        obsidian_fm["tags"] = list(set(tags))  # Dedupe

    # Add normalized flag
    obsidian_fm["normalized"] = True

    return obsidian_fm

# Hashtag extraction pattern
HASHTAG_PATTERN = re.compile(r"(?<!\S)#([a-zA-Z][a-zA-Z0-9_-]*)")

def extract_hashtags(text: str) -> list[str]:
    """本文から #tag 形式のタグを抽出."""
    matches = HASHTAG_PATTERN.findall(text)
    return list(set(matches))
```

**Alternatives considered**:
- 手動パース: YAML エッジケース対応が困難
- frontmatter ライブラリ: PyYAML で十分

---

### 4. 日付抽出戦略

**Decision**: 優先順位に従って複数ソースから日付を抽出

**Priority Order**:
1. frontmatter の `date` フィールド
2. ファイル名の Jekyll 形式（`YYYY-MM-DD-title.md`）
3. タイトルまたは本文から正規表現で抽出
4. フォールバック: 現在日時

**Rationale**:
- Jekyll ファイルは複数の場所に日付情報を持つ可能性
- 正規表現で単純一致が最も堅牢
- 複数パターンに対応（`YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY年MM月DD日`）

**Implementation**:
```python
import re
from datetime import datetime

# 日付パターン（複数形式対応）
DATE_PATTERNS = [
    r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})",      # 2024-09-10
    r"(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})",      # 2024/09/10
    r"(?P<year>\d{4})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日",  # 2024年9月10日
]

def extract_date_from_text(text: str) -> str | None:
    """タイトルまたは本文から日付を抽出."""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            g = match.groupdict()
            return f"{g['year']}-{int(g['month']):02d}-{int(g['day']):02d}"
    return None

def get_date(frontmatter: dict, filename: str, title: str, body: str) -> str:
    """優先順位に従って日付を取得."""
    # 1. frontmatter
    if "date" in frontmatter:
        return str(frontmatter["date"])[:10]

    # 2. ファイル名 (Jekyll形式)
    jekyll_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-", filename)
    if jekyll_match:
        return f"{jekyll_match.group(1)}-{jekyll_match.group(2)}-{jekyll_match.group(3)}"

    # 3. タイトルから抽出
    date = extract_date_from_text(title)
    if date:
        return date

    # 4. 本文から抽出（先頭1000文字のみ検索）
    date = extract_date_from_text(body[:1000])
    if date:
        return date

    # 5. フォールバック: 現在日時
    return datetime.now().strftime("%Y-%m-%d")
```

**Fallback for non-Jekyll filenames**:
- ファイル名（拡張子除く）をタイトルとして使用
- 日付は上記優先順位で抽出

---

### 5. 既存パイプラインへの統合

**Decision**: `ChatGPTExtractor` パターンを踏襲し、`GitHubExtractor` を実装

**Rationale**:
- 既存の BaseStage/BaseStep 構造を活用
- `discover_items()` で URL を受け取り、Steps で処理
- 既存の Transform/Load ステージを再利用

**Steps Design**:

1. **CloneRepoStep**: URL パース → git clone → 一時ディレクトリ
2. **DiscoverMarkdownStep**: 指定パス配下の `.md` ファイルを発見
3. **ParseJekyllStep**: frontmatter パース、ファイル名パース
4. **ConvertFrontmatterStep**: Jekyll → Obsidian 変換

**Integration Points**:
- `cli.py`: `--provider github` 追加
- `ImportPhase`: GitHubExtractor 選択ロジック追加
- 既存 `KnowledgeTransformer`: スキップ（Jekyll は既にメタデータあり）

---

## Summary

| Topic | Decision | Risk |
|-------|----------|------|
| URL パース | 正規表現 | Low - 形式固定 |
| Clone 戦略 | sparse-checkout | Low - 標準 git |
| Frontmatter | PyYAML | Low - 標準 YAML |
| 日付抽出 | 優先順位付き正規表現（frontmatter→ファイル名→タイトル→本文） | Low - 複数フォールバック |
| 統合 | ChatGPTExtractor パターン | Low - 実績あり |

**All NEEDS CLARIFICATION resolved**: なし（Technical Context に未解決項目なし）
