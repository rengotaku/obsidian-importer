# Implementation Plan: ChatGPTExtractor Steps分離リファクタリング

**Branch**: `032-extract-step-refactor` | **Date**: 2026-01-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/032-extract-step-refactor/spec.md`

## Summary

ChatGPTExtractor の `discover_items()` メソッドを軽量化し、実際の処理を Step クラスに分離。BaseStage フレームワークに汎用的な 1:N 展開 Step モデルを追加し、Extract/Transform 両 Stage で利用可能な設計とする。これにより全 Stage で一貫した `steps.jsonl` 出力を実現。また、session.json の `phases` フィールドを拡張し、各フェーズ完了時の item 数（success_count, error_count）を記録。

## Technical Context

**Language/Version**: Python 3.11+ (pyproject.toml: requires-python = ">=3.11")
**Primary Dependencies**: tenacity 8.x, ollama (既存), 標準ライブラリ (json, pathlib, dataclasses, zipfile)
**Storage**: ファイルシステム (JSON, JSONL, Markdown)
**Testing**: unittest (標準ライブラリ)
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: single (ETL パイプライン)
**Performance Goals**: 既存と同等のスループット維持
**Constraints**: 既存出力との 100% 互換性、後方互換性維持
**Scale/Scope**: 数百〜数千会話/ZIP ファイル処理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | N/A | Vault 構造に影響なし |
| II. Obsidian Markdown Compliance | ✅ PASS | 出力 Markdown フォーマットは変更なし |
| III. Normalization First | N/A | 正規化ロジックに影響なし |
| IV. Genre-Based Organization | N/A | ジャンル分類に影響なし |
| V. Automation with Oversight | ✅ PASS | 既存の確認フローを維持 |

**Gate Result**: ✅ PASS - 憲法違反なし

### Post-Design Re-evaluation (Phase 1 完了後)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | N/A | 設計により変更なし |
| II. Obsidian Markdown Compliance | ✅ PASS | 出力互換性 100% 維持（SC-003） |
| III. Normalization First | N/A | frontmatter 処理は Transform Stage で変更なし |
| IV. Genre-Based Organization | N/A | ジャンル判定ロジックに影響なし |
| V. Automation with Oversight | ✅ PASS | DEBUG モードで steps.jsonl による可視化向上 |

**Post-Design Gate Result**: ✅ PASS - 設計は憲法に準拠

## Project Structure

### Documentation (this feature)

```text
specs/032-extract-step-refactor/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - internal refactoring)
├── checklists/
│   └── requirements.md  # Requirements checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/etl/
├── core/
│   ├── stage.py         # BaseStage, BaseStep (修正対象)
│   ├── step.py          # Step, StepTracker
│   ├── models.py        # ProcessingItem (修正対象)
│   ├── session.py       # Session, PhaseStats (修正対象)
│   └── ...
├── stages/
│   └── extract/
│       └── chatgpt_extractor.py  # ChatGPTExtractor (修正対象)
└── tests/
    ├── test_stages.py
    ├── test_chatgpt_transform_integration.py
    └── ... (新規テスト追加)
```

**Structure Decision**: 既存の `src/etl/` 構造を維持。`core/stage.py` に 1:N 展開機能を追加し、`stages/extract/chatgpt_extractor.py` を Step ベースに書き換え。`core/session.py` に PhaseStats を追加し、session.json のフェーズ統計出力を実現。

**Debug Output**: DEBUG モード時、各 Stage の最終ステップ完了後に `{stage.output_path}/debug/{source_path.stem}_{stage_type}.jsonl` へ追記式で出力。`item_id` と `content`（フル、トランケートなし）のみを含むシンプルな JSONL フォーマット。中間ステップは出力せず、Stage 単位の最終結果のみを記録。

## Complexity Tracking

> 本リファクタリングは既存パターンの拡張であり、違反なし。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (なし) | - | - |
