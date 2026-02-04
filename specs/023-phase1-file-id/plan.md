# Implementation Plan: 全工程での file_id 付与・維持

**Branch**: `023-phase1-file-id` | **Date**: 2026-01-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/023-phase1-file-id/spec.md`

## Summary

LLMインポート処理の Phase 1（パース）時点で file_id を生成し、frontmatter に付与する。pipeline_stages.jsonl にも file_id を記録する。さらに organize 処理で file_id がないファイルには新規生成する。これにより、ファイルのライフサイクル全体を通じてトレーサビリティを確保する。

**原則**: どの工程でも「file_id がなければ生成、あれば維持」

## Technical Context

**Language/Version**: Python 3.11+（既存プロジェクト準拠）
**Primary Dependencies**: 標準ライブラリのみ（hashlib, pathlib, json, re）
**Storage**: ファイルシステム（Markdown + JSON状態ファイル）
**Testing**: unittest（`make test`）
**Target Platform**: Linux/macOS（ローカル開発環境）
**Project Type**: CLI スクリプト
**Performance Goals**: N/A（バッチ処理、リアルタイム性不要）
**Constraints**: 既存の file_id 生成ロジック（022-import-file-id）を再利用
**Scale/Scope**: 数百〜数千ファイルの処理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | file_id は Vault 横断の識別子、Vault 独立性に影響なし |
| II. Obsidian Markdown Compliance | ✅ Pass | frontmatter に `file_id` フィールド追加、YAML 形式準拠 |
| III. Normalization First | ✅ Pass | file_id は正規化処理の一部として付与 |
| IV. Genre-Based Organization | ✅ Pass | ジャンル分類に影響なし |
| V. Automation with Oversight | ✅ Pass | 自動生成だが人間が確認可能（frontmatter で可視） |

**Result**: All gates passed. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/023-phase1-file-id/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
development/scripts/
├── llm_import/
│   ├── common/
│   │   ├── file_id.py           # 既存: generate_file_id()
│   │   ├── session_logger.py    # 変更: log_stage() に file_id 追加
│   │   └── state.py             # 既存: ProcessedEntry.file_id
│   ├── providers/
│   │   └── claude/
│   │       └── parser.py        # 変更: to_markdown() に file_id 追加
│   ├── cli.py                   # 変更: Phase 1 で file_id 生成・設定
│   └── tests/
│       ├── test_file_id.py      # 既存
│       └── test_cli.py          # 追加: Phase 1 file_id テスト
│
└── normalizer/
    ├── processing/
    │   └── single.py            # 確認: file_id 生成/維持ロジック
    └── tests/
        └── test_file_id.py      # 追加: organize file_id テスト
```

**Structure Decision**: 既存の `development/scripts/` 構造を維持。llm_import と normalizer の両方を変更。

## Complexity Tracking

> No violations. Simple feature addition to existing modules.
