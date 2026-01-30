# Implementation Plan: LLM Multi-Stage Processing

**Branch**: `007-llm-multi-stage` | **Date**: 2026-01-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-llm-multi-stage/spec.md`

## Summary

現在の `ollama_normalizer.py` は1回のLLM呼び出しで全処理を行い、38%のエラー率を発生させている。本機能は処理を「Pre-processing → 4段階のLLM処理 → Post-processing」に分割し、各段階で独立したシンプルなプロンプトを使用することでエラー率を10%以下に削減する。時間がかかっても精度を重視する設計。

## Technical Context

**Language/Version**: Python 3.11+（標準ライブラリ中心）
**Primary Dependencies**: なし（標準ライブラリの json, re, urllib, pathlib を使用）
**Storage**: ファイルシステム（Obsidian Vault）
**Testing**: pytest（既存テスト基盤あり: `.claude/scripts/tests/`）
**Target Platform**: Linux（ローカル環境）
**Project Type**: single（CLIツール）
**Performance Goals**: 処理時間より精度優先（4回のLLM呼び出し許容）
**Constraints**: Ollama API（ローカルLLM）を使用、ネットワーク依存なし
**Scale/Scope**: 1回の実行で100ファイル程度を処理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | 各Vaultへの振り分けロジックは変更なし |
| II. Obsidian Markdown Compliance | ✅ Pass | frontmatter形式、リンク形式は維持 |
| III. Normalization First | ✅ Pass | 正規化処理の改善が目的 |
| IV. Genre-Based Organization | ✅ Pass | 6ジャンル分類を維持 |
| V. Automation with Oversight | ✅ Pass | 大量処理時の確認機能を維持 |

**Gate Result**: ✅ PASS - No violations

## Project Structure

### Documentation (this feature)

```text
specs/007-llm-multi-stage/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (stage prompts)
├── checklists/          # Quality checklists
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
.claude/scripts/
├── ollama_normalizer.py      # Main script (to be modified)
├── markdown_normalizer.py    # Existing dependency
├── prompts/
│   ├── normalizer_v2.txt     # Current monolithic prompt
│   ├── stage1_dust.txt       # NEW: Stage 1 prompt
│   ├── stage2_genre.txt      # NEW: Stage 2 prompt
│   ├── stage3_normalize.txt  # NEW: Stage 3 prompt
│   └── stage4_metadata.txt   # NEW: Stage 4 prompt
├── data/
│   └── tag_dictionary.json   # Existing tag dictionary
└── tests/
    ├── test_ollama_normalizer.py
    └── fixtures/             # Test fixtures
```

**Structure Decision**: Single project structure. 既存の `.claude/scripts/` ディレクトリ内で開発。新規プロンプトファイルを `prompts/` に追加。

## Complexity Tracking

> No violations to justify.

N/A - All Constitution checks passed.
