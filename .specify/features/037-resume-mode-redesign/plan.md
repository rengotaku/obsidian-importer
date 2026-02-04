# Implementation Plan: Resume モードの再設計

**Branch**: `037-resume-mode-redesign` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/037-resume-mode-redesign/spec.md`

## Summary

ETL パイプラインの Resume モードを再設計し、中断した処理を効率的に再開できるようにする。
主要な変更点:
- **ステージ別スキップ戦略**: Extract は Stage 単位、Transform/Load はアイテム単位でスキップ判定
- **DEBUG モード廃止**: 詳細ログ出力を通常動作に昇格
- **責務分離**: フレームワーク層（Stage/Phase）でスキップ判定、具象層（Step）は Resume を意識しない
- **ログ肥大化防止**: スキップしたアイテムは pipeline_stages.jsonl に記録しない

## Technical Context

**Language/Version**: Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`）
**Primary Dependencies**: tenacity 8.x（リトライ）, ollama（LLM API）, 標準ライブラリ（json, pathlib, dataclasses）
**Storage**: ファイルシステム（JSONL ログ、Markdown ファイル、JSON セッションデータ）
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: single（CLI パイプラインツール）
**Performance Goals**: 1000件のログファイル読み込みが1秒以内（SC-003）
**Constraints**: 重複 LLM 呼び出し0%（SC-001）、クラッシュ後の重複処理1件以下（SC-004）
**Scale/Scope**: 通常数千〜数万レコードのログファイル

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | Resume モードは Vault 構造に影響しない |
| II. Obsidian Markdown Compliance | ✅ Pass | 出力 Markdown フォーマットは変更なし |
| III. Normalization First | ✅ Pass | 正規化ロジックは変更なし |
| IV. Genre-Based Organization | ✅ Pass | ジャンル分類ロジックは変更なし |
| V. Automation with Oversight | ✅ Pass | Resume モードは自動処理だが、ログで追跡可能 |

**Gate Result**: ✅ All gates passed

### Post-Design Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | 設計変更なし - Vault 構造に影響しない |
| II. Obsidian Markdown Compliance | ✅ Pass | 出力フォーマット変更なし |
| III. Normalization First | ✅ Pass | 正規化ロジック変更なし |
| IV. Genre-Based Organization | ✅ Pass | ジャンル分類変更なし |
| V. Automation with Oversight | ✅ Pass | ログ出力で処理を追跡可能 |

**Post-Design Gate Result**: ✅ All gates passed

## Project Structure

### Documentation (this feature)

```text
specs/037-resume-mode-redesign/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - CLI tool)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/etl/
├── core/
│   ├── models.py        # ProcessingItem, StageLogRecord, CompletedItemsCache 追加
│   ├── stage.py         # BaseStage.run() にスキップ判定ロジック追加
│   ├── phase.py         # Phase.load_completed_items() 追加
│   ├── session.py       # Session（変更なし）
│   ├── config.py        # debug_mode デフォルト True（CLI --debug フラグ廃止）
│   └── types.py         # PhaseType, StageType（変更なし）
├── phases/
│   ├── import_phase.py  # ImportPhase.run() にスキップ統計追加
│   └── organize_phase.py
├── stages/
│   ├── extract/         # discover_items() のみ、スキップ判定なし
│   ├── transform/       # アイテム単位スキップ（フレームワーク層で処理）
│   └── load/            # アイテム単位スキップ（フレームワーク層で処理）
├── cli/
│   ├── commands/
│   │   ├── import_cmd.py  # --debug フラグ削除
│   │   ├── status_cmd.py  # スキップ数表示追加
│   │   └── retry_cmd.py   # 変更なし
│   └── utils/
│       └── pipeline_stats.py  # スキップ数計算ロジック追加
└── tests/
    ├── test_resume_mode.py    # Resume モード専用テスト（新規）
    └── test_stages.py         # 既存テストの修正
```

**Structure Decision**: Single project structure を使用。既存の `src/etl/` ディレクトリ構造を維持し、フレームワーク層（`core/`）に Resume ロジックを集約。

## Complexity Tracking

> Constitution Check に違反はないため、このセクションは空です。
