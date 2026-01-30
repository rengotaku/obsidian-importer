# Implementation Plan: too_large 判定の LLM コンテキストベース化

**Branch**: `038-too-large-llm-context` | **Date**: 2026-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/038-too-large-llm-context/spec.md`

## Summary

現状の `too_large` 判定は `item.content`（生 JSON 全体、約 2.4 倍過大評価）で行われているが、LLM に渡す実際のコンテキストサイズ（メッセージ `text` 合計 + ヘッダー + ラベル）に基づいて判定するように変更する。これにより、本来処理可能なアイテムが誤ってスキップされる問題を解決する。

## Technical Context

**Language/Version**: Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`）
**Primary Dependencies**: tenacity 8.x（リトライ）, ollama（LLM API）, 標準ライブラリ（json, dataclasses）
**Storage**: ファイルシステム（JSONL ログ、Markdown ファイル、JSON セッションデータ）
**Testing**: unittest（Python 標準ライブラリ）、`make test` で実行
**Target Platform**: Linux（ローカル開発環境）
**Project Type**: single（ETL パイプライン）
**Performance Goals**: 判定ロジック変更による処理時間増加 5% 以内
**Constraints**: 既存のユニットテストとの互換性維持
**Scale/Scope**: 424 アイテム/セッション程度

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 適用 | 状態 |
|------|------|------|
| I. Vault Independence | N/A - 内部処理変更 | ✅ Pass |
| II. Obsidian Markdown Compliance | N/A - 入力処理変更 | ✅ Pass |
| III. Normalization First | N/A - 正規化処理の前段階 | ✅ Pass |
| IV. Genre-Based Organization | N/A - ジャンル判定に影響なし | ✅ Pass |
| V. Automation with Oversight | 自動判定の精度向上 | ✅ Pass |

**Gate Result**: ✅ All Pass - 内部処理の改善であり、憲法違反なし

## Project Structure

### Documentation (this feature)

```text
specs/038-too-large-llm-context/
├── spec.md              # 仕様書
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (N/A - 新規エンティティなし)
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/etl/
├── core/
│   └── models.py          # ProcessingItem（既存）
├── stages/
│   └── transform/
│       └── knowledge_transformer.py  # ExtractKnowledgeStep.process() 修正対象
├── utils/
│   └── knowledge_extractor.py        # KnowledgeExtractor._build_user_message() 参照
└── tests/
    ├── test_knowledge_transformer.py # テスト追加
    └── test_too_large_context.py     # 新規テストファイル（オプション）
```

**Structure Decision**: 既存の `src/etl/` 構造を維持。主要変更は `knowledge_transformer.py` の `ExtractKnowledgeStep.process()` メソッド内の判定ロジック。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

該当なし - 憲法違反なし
