# Tasks: @index フォルダ内再帰的Markdown処理

**Input**: Design documents from `/specs/006-index-markdown-process/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Optional - テストは必要に応じて追加

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Target file**: `.claude/scripts/ollama_normalizer.py`
- **Test file**: `.claude/scripts/tests/test_recursive_scan.py`

---

## Phase 1: Setup

**Purpose**: 準備作業と既存コードの確認

- [x] T001 バックアップ作成: `cp .claude/scripts/ollama_normalizer.py .claude/scripts/ollama_normalizer.py.backup-006`
- [x] T002 既存の `list_index_files()` 関数を確認（line 806-820）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: すべてのUser Storyに必要な共通インフラ

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 `should_exclude(path: Path) -> bool` 関数を追加（除外判定ロジック）in `.claude/scripts/ollama_normalizer.py`
- [x] T004 `ScanResult` TypedDict を追加（スキャン結果の型定義）in `.claude/scripts/ollama_normalizer.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - サブフォルダ内Markdown一括処理 (Priority: P1) 🎯 MVP

**Goal**: `@index/` 以下のすべてのサブフォルダを再帰的に探索し、Markdownファイルを検出・処理

**Independent Test**: `@index/subfolder/test.md` を作成し、「整理して」コマンドで処理されることを確認

### Implementation for User Story 1

- [x] T005 [US1] `list_index_files()` 内の `glob("*.md")` を `rglob("*.md")` に変更 in `.claude/scripts/ollama_normalizer.py:812`
- [x] T006 [US1] `list_index_files()` 内で `should_exclude()` フィルタを適用 in `.claude/scripts/ollama_normalizer.py`
- [x] T007 [US1] `status` サブコマンドの統計表示を更新（直下/サブフォルダ別カウント）in `.claude/scripts/ollama_normalizer.py`
- [x] T008 [US1] 手動テスト: 既存の89件サブフォルダファイルが検出されることを確認

**Checkpoint**: User Story 1 完了 - サブフォルダ内ファイルの再帰検出が動作

---

## Phase 4: User Story 2 - 処理対象ファイルのプレビュー表示 (Priority: P2)

**Goal**: 処理前に対象ファイル一覧を表示し、ユーザー確認を可能にする

**Independent Test**: 20件以上のファイルがある場合、確認プロンプトが表示されることを確認

### Implementation for User Story 2

- [x] T009 [US2] 大量ファイル処理時の確認プロンプト追加（閾値: 20件）in `.claude/scripts/ollama_normalizer.py`
- [x] T010 [US2] `--force` オプション追加（確認スキップ）in `.claude/scripts/ollama_normalizer.py` argparse設定
- [x] T011 [US2] プレビュー表示フォーマット実装（ファイル名、パス、階層深度）in `.claude/scripts/ollama_normalizer.py`
- [x] T012 [US2] 手動テスト: 確認プロンプトと `--force` オプションの動作確認

**Checkpoint**: User Story 2 完了 - 大量ファイル処理前の確認フローが動作

---

## Phase 5: User Story 3 - 特定フォルダの除外設定 (Priority: P3)

**Goal**: 隠しファイル/フォルダをデフォルトで除外し、安全な処理を保証

**Independent Test**: `.obsidian/` 内のファイルが処理対象から除外されることを確認

### Implementation for User Story 3

- [x] T013 [US3] `should_exclude()` の除外ログ出力追加（除外されたファイル/フォルダを記録）in `.claude/scripts/ollama_normalizer.py`
- [x] T014 [US3] `status --verbose` で除外されたファイル一覧を表示 in `.claude/scripts/ollama_normalizer.py`
- [x] T015 [US3] 手動テスト: `.obsidian/` 配下のファイルが除外されることを確認

**Checkpoint**: User Story 3 完了 - 除外ロジックが正常に動作

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 仕上げと品質向上

- [x] T016 [P] 処理結果統計の強化（移動先Vault別カウント、エラー件数）in `.claude/scripts/ollama_normalizer.py`
- [x] T017 [P] `--cleanup-empty` オプション追加（空フォルダ削除）in `.claude/scripts/ollama_normalizer.py`
- [x] T018 docstring更新: 変更した関数のドキュメント更新 in `.claude/scripts/ollama_normalizer.py`
- [x] T019 quickstart.md の検証: 記載内容どおりに動作することを確認

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: T003, T004 必須 → T005-T008
- **User Story 2 (P2)**: T005-T006 必須（ファイル検出が動いている前提）→ T009-T012
- **User Story 3 (P3)**: T003 の `should_exclude()` が存在する前提 → T013-T015

### Parallel Opportunities

- T001, T002 は並列可能
- T003, T004 は並列可能（異なる機能）
- T016, T017, T018 は並列可能

---

## Parallel Example: Foundational Phase

```bash
# Launch foundational tasks together:
Task: "should_exclude() 関数を追加 in ollama_normalizer.py"
Task: "ScanResult TypedDict を追加 in ollama_normalizer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T004)
3. Complete Phase 3: User Story 1 (T005-T008)
4. **STOP and VALIDATE**: Test with existing 89 subfolder files
5. 既存の89件ファイルを処理可能な状態

### Incremental Delivery

1. Setup + Foundational → 基盤完成
2. User Story 1 → 再帰検出動作 → **MVP達成**
3. User Story 2 → 確認フロー追加 → 安全性向上
4. User Story 3 → 除外ログ追加 → 可視性向上
5. Polish → 品質向上

---

## Notes

- [P] tasks = different files or independent functions
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- 変更対象ファイルは1つ（`.claude/scripts/ollama_normalizer.py`）
- 新規ファイル作成は最小限（テストファイルのみ、必要に応じて）
