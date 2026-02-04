# Implementation Plan: Jekyll ブログインポート

**Branch**: `034-jekyll-import` | **Date**: 2026-01-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/034-jekyll-import/spec.md`

## Summary

GitHub リポジトリの Jekyll ブログ（`_posts` ディレクトリ等）を既存の ETL パイプラインでインポートする機能を追加。URL からリポジトリをパースし、`git clone --depth 1` で取得後、Markdown ファイルを Obsidian 形式に変換する。既存の `ClaudeExtractor`/`ChatGPTExtractor` パターンに従い、`GitHubExtractor` を実装。

## Technical Context

**Language/Version**: Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`）
**Primary Dependencies**: tenacity 8.x（既存）、標準ライブラリ（subprocess, pathlib, re, yaml）
**Storage**: ファイルシステム（JSON, JSONL, Markdown）- セッションフォルダ構造
**Testing**: unittest（標準ライブラリ）- `src/etl/tests/`
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: Single（既存 ETL パイプライン拡張）
**Performance Goals**: 500+ ファイルを1回のインポートで処理可能
**Constraints**: git コマンド依存、GitHub パブリックリポジトリのみ
**Scale/Scope**: 500+ Markdown ファイル、Jekyll 形式 frontmatter 対応

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ PASS | インポート先は session フォルダ + @index。Vault 直接配置なし |
| II. Obsidian Markdown Compliance | ✅ PASS | Jekyll frontmatter → Obsidian frontmatter 変換を実装 |
| III. Normalization First | ✅ PASS | `normalized: true` 付与、Jekyll 不要フィールド削除 |
| IV. Genre-Based Organization | ✅ PASS | 振り分けは後続の `organize` フェーズで実施 |
| V. Automation with Oversight | ✅ PASS | `--dry-run`、`--limit` オプションで確認可能 |

**Gate Result**: ✅ PASS - 全原則に適合

## Project Structure

### Documentation (this feature)

```text
specs/034-jekyll-import/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - no external API)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/etl/
├── stages/
│   └── extract/
│       ├── __init__.py           # Add GitHubExtractor export
│       ├── github_extractor.py   # NEW: GitHub/Jekyll extractor
│       └── ...
├── utils/
│   └── github_url.py             # NEW: URL parsing utility
├── cli.py                        # Add --provider github
└── tests/
    ├── test_github_extractor.py  # NEW: Unit tests
    └── test_github_url.py        # NEW: URL parser tests
```

**Structure Decision**: 既存の `src/etl/stages/extract/` パターンに従い、`github_extractor.py` を追加。URL パース機能は `src/etl/utils/github_url.py` に分離。

## Complexity Tracking

> **No violations - standard extension of existing pattern**

| Aspect | Complexity | Justification |
|--------|-----------|---------------|
| New Extractor | Low | 既存 ChatGPTExtractor パターンを踏襲 |
| git clone | Low | subprocess 標準ライブラリ使用 |
| URL Parsing | Low | 正規表現で単純パース |
| Frontmatter 変換 | Low | 既存 KnowledgeTransformer パターン活用 |
