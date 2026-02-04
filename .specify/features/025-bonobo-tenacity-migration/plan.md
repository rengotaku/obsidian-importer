# Implementation Plan: Bonobo & Tenacity ETL Migration

**Branch**: `025-bonobo-tenacity-migration` | **Date**: 2026-01-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/025-bonobo-tenacity-migration/spec.md`

## Summary

既存の LLM インポート・正規化パイプラインを、tenacity（リトライライブラリ）とカスタム ETL フレームワークを使用して再構築する。セッションベースの ETL アーキテクチャ（Session → Phase → Stage → Step）を導入し、処理状態の追跡とデバッグを容易にする。

> **Research 結果**: bonobo は開発停滞（6年以上）・alpha 状態のため **不採用**。カスタム ETL 実装を採用。詳細は [research.md](./research.md) 参照。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: tenacity (8.x), ollama (existing)
**Storage**: JSON ファイル（session.json, phase.json）、Markdown ファイル
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: Single CLI application
**Performance Goals**: コード品質向上、リトライ信頼性向上（並列化は将来検討）
**Constraints**: Ollama API 依存（ローカル LLM）
**Scale/Scope**: 単一ユーザー、ローカル環境のみ

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Vault Independence | ✅ PASS | ETL 出力は Session フォルダ内で完結、Vault への配置は Load Stage で明示的に実行 |
| II. Obsidian Markdown Compliance | ✅ PASS | 出力 Markdown は既存規約を維持 |
| III. Normalization First | ✅ PASS | Transform Stage で正規化処理を実行 |
| IV. Genre-Based Organization | ✅ PASS | organize Phase で既存のジャンル分類ロジックを使用 |
| V. Automation with Oversight | ✅ PASS | debug モードで詳細ログ、phase.json で処理状態追跡 |

**Gate Result**: ✅ PASS - No violations

## Project Structure

### Documentation (this feature)

```text
specs/025-bonobo-tenacity-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI interface specs)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── etl/                           # 新規 ETL パイプライン
│   ├── __init__.py
│   ├── cli.py                     # CLI エントリポイント
│   ├── core/                      # コア機能
│   │   ├── __init__.py
│   │   ├── session.py             # Session 管理
│   │   ├── phase.py               # Phase 管理
│   │   ├── stage.py               # Stage 基底クラス
│   │   ├── step.py                # Step 管理
│   │   ├── retry.py               # tenacity ラッパー
│   │   └── config.py              # 設定
│   ├── phases/                    # Phase 実装
│   │   ├── __init__.py
│   │   ├── import_phase.py        # import Phase
│   │   └── organize_phase.py      # organize Phase
│   ├── stages/                    # Stage 実装
│   │   ├── __init__.py
│   │   ├── extract/               # Extract Stages
│   │   │   ├── __init__.py
│   │   │   ├── claude_extractor.py
│   │   │   └── file_extractor.py
│   │   ├── transform/             # Transform Stages
│   │   │   ├── __init__.py
│   │   │   ├── knowledge_transformer.py
│   │   │   └── normalizer_transformer.py
│   │   └── load/                  # Load Stages
│   │       ├── __init__.py
│   │       ├── session_loader.py
│   │       └── vault_loader.py
│   └── tests/                     # テスト
│       ├── __init__.py
│       ├── test_session.py
│       ├── test_phase.py
│       ├── test_stages.py
│       └── test_retry.py
│
├── converter/                     # レガシー（段階的に移行）
│   └── scripts/
│       ├── llm_import/            # → src/etl/phases/import_phase.py へ移行
│       └── normalizer/            # → src/etl/phases/organize_phase.py へ移行
│
└── rag/                           # 既存 RAG 機能（変更なし）
```

**Structure Decision**: Single project 構造を選択。`src/etl/` に新規実装し、既存 `src/converter/` から段階的に移行。

## Complexity Tracking

> Constitution Check に違反がないため、このセクションは該当なし。

---

## Phase 0: Research (NEEDS CLARIFICATION 解決)

### Research Tasks

1. **bonobo 安定性調査**: 1.0 未満の制限事項、既知のバグ、workaround
2. **tenacity 統合パターン**: bonobo ノード内での最適な使用方法
3. **既存コード分析**: llm_import, normalizer の依存関係マッピング

### Output

→ `research.md` に統合

---

## Phase 1: Design & Contracts

### Output

- `data-model.md`: Session, Phase, Stage, Step のデータ構造
- `contracts/cli.md`: CLI インターフェース仕様
- `quickstart.md`: 開発者向けクイックスタートガイド
