# Implementation Plan: LLMインポートでのfile_id付与

**Branch**: `022-import-file-id` | **Date**: 2026-01-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/022-import-file-id/spec.md`

## Summary

LLM インポート処理（llm_import）で生成されるナレッジファイルに file_id を付与する。既存の normalizer の `generate_file_id()` ロジックを共通化し、KnowledgeDocument と ProcessedEntry に file_id フィールドを追加。frontmatter と state.json の両方に記録することで、インポート時点からファイル追跡を可能にする。

## Technical Context

**Language/Version**: Python 3.11+（既存プロジェクト準拠）
**Primary Dependencies**: 標準ライブラリのみ（hashlib, pathlib, dataclasses）
**Storage**: ファイルシステム（Markdown + JSON状態ファイル）
**Testing**: unittest（`make test` で実行）
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: single
**Performance Goals**: 既存処理に影響なし（ハッシュ計算は O(n) でコンテンツサイズに比例、無視できるレベル）
**Constraints**: 決定論的なID生成（同一入力→同一出力）
**Scale/Scope**: 既存 llm_import コードベースへの限定的変更（3-4ファイル）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check (Phase 0前)

| 原則 | 状態 | 評価 |
|------|------|------|
| I. Vault Independence | ✅ | llm_import は @index 出力、Vault 直接変更なし |
| II. Obsidian Markdown Compliance | ✅ | frontmatter に file_id 追加（YAML形式準拠） |
| III. Normalization First | ✅ | `normalized: true` 維持、file_id は追跡用追加フィールド |
| IV. Genre-Based Organization | N/A | ジャンル分類ロジックに影響なし |
| V. Automation with Oversight | ✅ | 既存フロー踏襲、確認プロセス不変 |

**Gate Result**: ✅ PASS

### Post-Design Check (Phase 1後)

| 原則 | 状態 | 評価 |
|------|------|------|
| I. Vault Independence | ✅ | 変更なし |
| II. Obsidian Markdown Compliance | ✅ | file_id フィールドは YAML スカラー値として出力 |
| III. Normalization First | ✅ | data-model で file_id を Optional として定義、後方互換維持 |
| IV. Genre-Based Organization | N/A | 変更なし |
| V. Automation with Oversight | ✅ | state.json への自動記録、人間が確認可能 |

**Gate Result**: ✅ PASS（設計後も違反なし）

## Project Structure

### Documentation (this feature)

```text
specs/022-import-file-id/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
development/scripts/llm_import/
├── common/
│   ├── knowledge_extractor.py  # KnowledgeDocument (変更対象)
│   ├── state.py                # ProcessedEntry, StateManager (変更対象)
│   └── file_id.py              # 新規: generate_file_id() 共通モジュール
├── tests/
│   ├── test_knowledge_extractor.py  # (変更対象)
│   └── test_file_id.py              # 新規: file_id生成テスト
└── cli.py                      # (軽微な変更: file_id渡し)
```

**Structure Decision**: 既存の llm_import 構造に `file_id.py` を追加し、normalizer との共通化を図る。

## Complexity Tracking

> 違反なし - このセクションは不要
