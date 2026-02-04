# Implementation Plan: Transform Stage Debug Step Output

**Branch**: `027-debug-step-output` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/027-debug-step-output/spec.md`

## Summary

Transform stage が debug モード時に各 step の中間出力を JSONL 形式で保存する機能を追加。
既存の `Config.debug_mode` フラグと `BaseStage` の JSONL 出力機能を活用し、step 毎の出力を `transform/debug/step_NNN_<step_name>/` に書き出す。

## Technical Context

**Language/Version**: Python 3.13（既存 ETL パイプライン）
**Primary Dependencies**: tenacity 8.x（既存）、標準ライブラリ（json, pathlib, dataclasses）
**Storage**: ファイルシステム（JSONL 形式）
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: Single project
**Performance Goals**: 既存パイプラインと同等（debug モード OFF 時は影響なし）
**Constraints**: JSONL は 1行1JSON、改行なしのコンパクト形式
**Scale/Scope**: 会話ファイル数百件程度

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 適合状況 | 備考 |
|------|---------|------|
| I. Vault Independence | ✅ 適合 | Vault には直接関与しない（ETL 内部機能） |
| II. Obsidian Markdown Compliance | ✅ 適合 | debug 出力は JSONL 形式（Markdown ではない） |
| III. Normalization First | ✅ 適合 | 正規化処理には影響しない |
| IV. Genre-Based Organization | ✅ 適合 | ジャンル分類には影響しない |
| V. Automation with Oversight | ✅ 適合 | debug 出力は開発者確認用 |

**Gate Status**: ✅ PASS - 全原則に適合

## Project Structure

### Documentation (this feature)

```text
specs/027-debug-step-output/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/etl/
├── core/
│   ├── config.py        # Config.debug_mode（既存）
│   └── stage.py         # BaseStage に debug 出力機能を追加
├── stages/
│   └── transform/
│       └── knowledge_transformer.py  # KnowledgeTransformer に統合
└── tests/
    └── test_debug_step_output.py     # 新規テスト
```

### Debug Output Structure (runtime)

```text
.staging/@session/YYYYMMDD_HHMMSS/
└── import/
    └── transform/
        ├── debug/                          # 🆕 debug 出力
        │   └── step_001_extract_knowledge/ # 現時点では1 step のみ
        │       ├── conversation_001.jsonl
        │       └── conversation_002.jsonl
        └── output/                         # 既存（変更なし）
            └── ...
```

> **Note**: 現在 KnowledgeTransformer は `ExtractKnowledgeStep` の1 step のみ。
> 将来 step が追加された場合、自動的に `step_002_xxx/`, `step_003_xxx/` が作成される。

**Structure Decision**: 既存の `src/etl/` 構造を維持。`core/stage.py` の `BaseStage` クラスに debug step 出力機能を追加し、Transform stage で利用する。

## Complexity Tracking

> **No violations detected.** Constitution Check passed without exceptions.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| なし | - | - |
