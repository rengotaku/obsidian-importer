# Implementation Plan: Resume モード Extract Output 再利用

**Branch**: `040-resume-extract-reuse` | **Date**: 2026-01-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/040-resume-extract-reuse/spec.md`

## Summary

Resume モードで ETL パイプラインを再実行する際、Extract stage の output（data-dump-*.jsonl）を再利用して重複ログを防止する。BasePhaseOrchestrator（Template Method パターン）を導入し、FW が制御フローを管理することで、各 Phase は具体的な Stage 実行のみを実装する。Extract output は固定ファイル名（data-dump-{番号4桁}.jsonl）で 1000 レコードごとに分割する。

## Technical Context

**Language/Version**: Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`）
**Primary Dependencies**: tenacity 8.x（リトライ）、ollama（LLM API）、PyYAML 6.0+、標準ライブラリ（json, pathlib, dataclasses, abc）
**Storage**: ファイルシステム（JSONL, JSON, Markdown）- セッションフォルダ構造
**Testing**: unittest（Python 標準ライブラリ）- `make test` で実行
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: Single project（CLI ETL パイプライン）
**Performance Goals**: 1000 レコード/ファイルで分割、大規模セッション対応
**Constraints**: 既存の ImportPhase、OrganizePhase との互換性維持
**Scale/Scope**: 数千アイテムの会話インポート、Resume モードでの効率的な再処理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ PASS | 変更は ETL パイプラインのみ、Vault 構造に影響なし |
| II. Obsidian Markdown Compliance | ✅ PASS | 出力形式に変更なし、JSONL は内部データ |
| III. Normalization First | ✅ PASS | 正規化ロジックに影響なし |
| IV. Genre-Based Organization | ✅ PASS | ジャンル分類に影響なし |
| V. Automation with Oversight | ✅ PASS | Resume モードは自動化だが、既存の確認フローを維持 |

**Gate Result**: ✅ ALL PASS - Phase 0 に進む

## Project Structure

### Documentation (this feature)

```text
specs/040-resume-extract-reuse/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - internal refactoring)
├── checklists/          # Quality checklists
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/etl/
├── core/
│   ├── phase_orchestrator.py  # NEW: BasePhaseOrchestrator (Template Method)
│   ├── stage.py               # MODIFY: _write_output_item() 固定ファイル名 + 分割
│   ├── models.py              # 既存: ProcessingItem
│   ├── phase.py               # 既存: Phase dataclass
│   └── session.py             # 既存: SessionManager
├── phases/
│   ├── import_phase.py        # MODIFY: BasePhaseOrchestrator 継承
│   └── organize_phase.py      # MODIFY: BasePhaseOrchestrator 継承
├── stages/
│   └── (既存 - 変更なし)
└── tests/
    ├── test_phase_orchestrator.py  # NEW: BasePhaseOrchestrator テスト
    ├── test_resume_mode.py         # MODIFY: 新規テストケース追加
    └── test_stages.py              # MODIFY: 固定ファイル名テスト追加
```

**Structure Decision**: 既存の src/etl/ 構造を維持し、core/ に新規ファイル phase_orchestrator.py を追加。ImportPhase と OrganizePhase を修正して BasePhaseOrchestrator を継承。

## Complexity Tracking

> No violations - standard FW refactoring pattern
