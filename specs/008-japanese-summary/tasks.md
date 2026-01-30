# Tasks: Summary 日本語化

**Input**: Design documents from `/specs/008-japanese-summary/`
**Prerequisites**: plan.md, spec.md, research.md

**Tests**: 手動テストのみ（自動テストは要求されていない）

**Organization**: シンプルなプロンプト修正のため、最小限のフェーズ構成

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: なし（既存プロジェクトへの修正のため）

> このフェーズはスキップ。既存の `.claude/scripts/` 構造を使用。

---

## Phase 2: Foundational

**Purpose**: なし（既存インフラを使用）

> このフェーズはスキップ。既存の Stage 3 パイプラインに統合。

---

## Phase 3: User Story 1 - Summary 日本語化 (Priority: P1) 🎯 MVP

**Goal**: 英語の Summary/Conversation Overview セクションを日本語に翻訳する

**Independent Test**: 英語サマリーを含むファイルを `ollama_normalizer.py` で処理し、サマリーが日本語になることを確認

### Implementation for User Story 1

- [x] T001 [US1] `stage3_normalize.txt` に Summary 翻訳ルールを追加 in `.claude/scripts/prompts/stage3_normalize.txt`
- [x] T002 [US1] 英語サマリーファイルで動作確認（手動テスト）

**Checkpoint**: 英語 Summary が日本語に翻訳される

---

## Phase 4: User Story 2 - 既存日本語サマリーの保持 (Priority: P2)

**Goal**: 既に日本語のサマリーは変更されないことを確認

**Independent Test**: 日本語サマリーを含むファイルを処理し、内容が変更されていないことを確認

### Implementation for User Story 2

- [x] T003 [US2] 日本語サマリーファイルで動作確認（手動テスト）

**Checkpoint**: 日本語サマリーは変更されない

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 検証と完了確認

- [ ] T004 複数ファイルでの一括処理テスト（`--all` オプション）（後日実行）
- [ ] T005 処理時間が 20% 以上増加していないことを確認（後日実行）
- [x] T006 plan.md の Verification チェックリストを完了

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup): スキップ
    ↓
Phase 2 (Foundational): スキップ
    ↓
Phase 3 (US1): T001 → T002
    ↓
Phase 4 (US2): T003
    ↓
Phase 5 (Polish): T004 → T005 → T006
```

### User Story Dependencies

- **User Story 1 (P1)**: 独立して実装可能（プロンプト修正のみ）
- **User Story 2 (P2)**: US1 完了後に検証（US1 の変更が US2 に影響しないことを確認）

### Parallel Opportunities

- T004, T005 は並列実行可能（異なる検証項目）

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001: プロンプトに翻訳ルール追加
2. T002: 単一ファイルで動作確認
3. **STOP and VALIDATE**: 英語サマリーが日本語に変換されることを確認

### Full Implementation

1. US1 完了（T001-T002）
2. US2 検証（T003）
3. Polish（T004-T006）

---

## Task Details

### T001: stage3_normalize.txt に Summary 翻訳ルール追加

**ファイル**: `.claude/scripts/prompts/stage3_normalize.txt`

**変更内容**:
```
## 改善すべき点
...
4. **英語の Summary/Conversation Overview** → 日本語に翻訳
   - 「## Summary」→「## 概要」
   - 「**Conversation Overview**」→「**会話の概要**」
   - Summary 内の英文は全て日本語に翻訳
   - この翻訳は「完全な英語文書は翻訳しない」ルールより優先
```

### T002: 英語サマリーファイルで動作確認

**テストファイル**: `エンジニア/60A回路で冬の暖房とサーバーがトリップする原因と対策.md`

**確認項目**:
- [ ] `## Summary` が `## 概要` に変換される
- [ ] `**Conversation Overview**` が `**会話の概要**` に変換される
- [ ] 英文が日本語に翻訳される

---

## Notes

- 全タスク数: 6
- User Story 1: 2 タスク
- User Story 2: 1 タスク
- Polish: 3 タスク
- 並列実行機会: T004/T005
- MVP スコープ: T001-T002（プロンプト修正と動作確認）
