# Implementation Plan: 柔軟な入出力比率対応フレームワーク

**Branch**: `028-flexible-io-ratios` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/028-flexible-io-ratios/spec.md`

## Summary

ETLフレームワークの BaseStage を拡張し、1:1（単一入出力）と 1:N（1入力→複数出力）の両方のパターンをサポートする。継承クラスが `run()` をオーバーライドせずに入出力比率を実現でき、debugモード時のログ出力はフレームワーク側で自動的かつ統一的に行われる。

## Technical Context

**Language/Version**: Python 3.13（既存 src/etl 環境）
**Primary Dependencies**: tenacity 8.x（既存）、標準ライブラリ（dataclasses, json, pathlib）
**Storage**: ファイルシステム（JSONL, Markdown）
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: single（ETLパイプライン拡張）
**Performance Goals**: 現行パフォーマンスを維持（1ファイル/秒以上）
**Constraints**: 後方互換性100%、既存テスト全パス
**Scale/Scope**: 1セッションあたり最大1000ファイル程度

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ Pass | フレームワーク変更のみ、Vault 構造に影響なし |
| II. Obsidian Markdown Compliance | ✅ Pass | Markdown 出力形式は変更なし |
| III. Normalization First | ✅ Pass | 正規化ロジックに影響なし |
| IV. Genre-Based Organization | ✅ Pass | ジャンル振り分けロジックに影響なし |
| V. Automation with Oversight | ✅ Pass | 自動処理の確認フローは維持 |

**Gate Result**: ✅ PASS - 全原則に適合

## Project Structure

### Documentation (this feature)

```text
specs/028-flexible-io-ratios/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/etl/
├── core/
│   ├── stage.py         # BaseStage（変更なし、debug出力は既存機能を使用）
│   ├── step.py          # BaseStep（変更なし）
│   ├── models.py        # ProcessingItem metadata拡張、StageLogRecord拡張
│   └── status.py        # 既存（変更なし）
├── phases/
│   └── import_phase.py  # discover_items()でチャンク分割
├── stages/
│   ├── extract/
│   │   └── claude_extractor.py  # 変更なし
│   └── transform/
│       └── knowledge_transformer.py  # run()オーバーライド削除
└── tests/
    ├── test_models.py               # チャンクmetadataテスト追加
    ├── test_import_phase.py         # チャンク分割テスト追加
    ├── test_debug_step_output.py    # 1:1/1:N debugログテスト追加
    └── test_stages.py               # pipeline_stages.jsonlテスト追加
```

**Structure Decision**: 既存の `src/etl/` 構造を維持し、core モジュールの拡張と stages の修正のみ行う。

## Complexity Tracking

> No violations - Constitution Check passed without exceptions.
