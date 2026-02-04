# Implementation Plan: Phase 2 簡素化

**Branch**: `016-phase2-simplify` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/016-phase2-simplify/spec.md`

## Summary

Phase 2（知識抽出）を簡素化し、title/tags/related_keywords 抽出を削除。代わりに Summary の日本語翻訳と構造化された概要生成に集中する。出力ファイル名から日付プレフィックスを除去し、会話タイトルのみを使用。

## Technical Context

**Language/Version**: Python 3.11+ (既存プロジェクト)
**Primary Dependencies**: 標準ライブラリのみ (urllib, json, pathlib, re)
**Storage**: Markdown ファイル (Obsidian Vault)
**Testing**: pytest (既存: `scripts/llm_import/tests/`)
**Target Platform**: Linux/macOS (ローカル実行)
**Project Type**: Single project (scripts/llm_import/)
**Performance Goals**: N/A (バッチ処理)
**Constraints**: Ollama API 依存
**Scale/Scope**: 400+ 会話ファイル処理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Vault Independence** | ✅ Pass | 出力先は `@index/`、Vault 構造に影響なし |
| **II. Obsidian Markdown Compliance** | ✅ Pass | frontmatter 形式維持、`tags` 削除は Phase 3 との分離目的 |
| **III. Normalization First** | ✅ Pass | `normalized: false` で出力、Phase 3 で正規化 |
| **IV. Genre-Based Organization** | ✅ Pass | ジャンル分類は Phase 3 に委譲 |
| **V. Automation with Oversight** | ✅ Pass | 大量処理は既存 CLI の確認機能を使用 |

## Project Structure

### Documentation (this feature)

```text
specs/016-phase2-simplify/
├── plan.md              # This file
├── research.md          # Phase 0 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
scripts/
└── llm_import/
    ├── cli.py                        # 修正: _generate_filename(), Phase 3 削除
    ├── prompts/
    │   ├── summary_translation.txt   # 新規: Summary 翻訳用
    │   └── knowledge_extraction.txt  # 修正: まとめ生成用に簡素化
    ├── common/
    │   └── knowledge_extractor.py    # 修正: 2段階LLM, KnowledgeDocument
    └── tests/
        └── test_knowledge_extractor.py  # 修正: テスト更新
```

**Structure Decision**: 既存構造を維持。プロンプト1ファイル追加、4ファイル修正。

## Complexity Tracking

> No violations. 既存コードの単純化であり、複雑性は減少する。

| Aspect | Before | After |
|--------|--------|-------|
| LLM 抽出項目 | 7項目 | 4項目 (title, tags, related削除) |
| プロンプト行数 | ~100行 | ~60行 (推定) |
| frontmatter 項目 | 6項目 | 5項目 (tags削除, summary追加) |
