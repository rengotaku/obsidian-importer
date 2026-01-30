# Implementation Plan: Resume機能の基底クラス集約リファクタリング

**Branch**: `039-resume-baseclass-refactor` | **Date**: 2026-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/039-resume-baseclass-refactor/spec.md`

## Summary

ETLパイプラインのResume機能を `BaseStage` に集約し、継承クラスが Resume を意識しない設計に再構築する。
`ItemStatus.SKIPPED` を `ItemStatus.FILTERED` に名称変更し、Resume時のスキップとバリデーション失敗を明確に区別する。

## Technical Context

**Language/Version**: Python 3.11+ (pyproject.toml: `requires-python = ">=3.11"`)
**Primary Dependencies**: tenacity 8.x（リトライ）, ollama（LLM API）, 標準ライブラリ（json, dataclasses）
**Storage**: ファイルシステム（JSON, JSONL, Markdown）
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux (local development)
**Project Type**: single
**Performance Goals**: Resume時のLLM呼び出し削減（処理済みアイテムのスキップ）
**Constraints**: 既存のETLアーキテクチャを維持、後方互換性は不要（内部リファクタリング）
**Scale/Scope**: ETLパイプライン内部、16ファイルの変更

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 適用 | 評価 |
|------|------|------|
| I. Vault Independence | N/A | ETLコード変更、Vault構造に影響なし |
| II. Obsidian Markdown Compliance | N/A | Markdownファイル生成ロジックに変更なし |
| III. Normalization First | N/A | 正規化プロセスに影響なし |
| IV. Genre-Based Organization | N/A | ジャンル分類ロジックに影響なし |
| V. Automation with Oversight | ✅ Pass | 自動処理の動作変更だが、ユーザー確認フローは維持 |

**結果**: すべてのGate通過。本リファクタリングはETLパイプラインの内部コードであり、Constitution違反なし。

## Project Structure

### Documentation (this feature)

```text
specs/039-resume-baseclass-refactor/
├── spec.md              # 仕様書
├── plan.md              # このファイル
├── research.md          # Phase 0 研究結果
├── data-model.md        # Phase 1 データモデル
├── quickstart.md        # Phase 1 開発者ガイド
└── tasks.md             # Phase 2 タスク一覧（/speckit.tasks で生成）
```

### Source Code (repository root)

```text
src/etl/
├── core/
│   ├── status.py        # ItemStatus enum 変更
│   ├── stage.py         # BaseStage.run() Resume集約
│   ├── models.py        # StageLogRecord status値変更
│   └── step.py          # SKIPPED参照変更
├── stages/
│   ├── extract/
│   │   └── chatgpt_extractor.py  # SKIPPED参照変更
│   ├── transform/
│   │   └── knowledge_transformer.py  # run_with_skip()削除, SKIPPED変更
│   └── load/
│       └── session_loader.py  # run_with_skip()削除, SKIPPED変更
├── phases/
│   ├── import_phase.py   # Resume前提条件チェック追加, SKIPPED変更
│   └── organize_phase.py # SKIPPED参照変更
└── tests/
    ├── test_resume_mode.py  # テスト修正
    ├── test_knowledge_transformer.py
    ├── test_stages.py
    ├── test_import_phase.py
    ├── test_chatgpt_transform_integration.py
    ├── test_too_large_context.py
    └── test_models.py
```

**Structure Decision**: 既存の `src/etl/` 構造を維持。変更は既存ファイルの修正のみ。

## Complexity Tracking

> 本リファクタリングはConstitution違反がないため、記載不要。

## Phase Summary

### Phase 1: ItemStatus.SKIPPED → FILTERED 名称変更

- `src/etl/core/status.py` のEnum変更
- 全16ファイルの参照更新
- テストコードの更新

### Phase 2: BaseStage.run() Resume集約

- Resume時のスキップロジック簡素化
- yield from skipped_items 削除
- ステータス変更なし、フィルタのみ

### Phase 3: run_with_skip() 削除

- `KnowledgeTransformer.run_with_skip()` 削除
- `SessionLoader.run_with_skip()` 削除
- 関連テストの削除または修正

### Phase 4: Resume前提条件チェックと進捗表示

- Extract完了チェック追加
- 進捗表示実装（Resume mode: n/N items already completed）

### Phase 5: テスト検証とドキュメント更新

- 全テスト通過確認
- CLAUDE.md への Active Technologies 更新
