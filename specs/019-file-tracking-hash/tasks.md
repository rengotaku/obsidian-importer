# Tasks: ファイル追跡ハッシュID

**Input**: Design documents from `/specs/019-file-tracking-hash/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: 既存テストフレームワーク（unittest）を使用。新規テストファイル追加。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Project**: `development/scripts/normalizer/`
- **Tests**: `development/scripts/normalizer/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 既存プロジェクトへの拡張準備

- [ ] T001 Confirm existing project structure and dependencies in development/scripts/normalizer/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 型定義の更新（両User Storyに必要）

**⚠️ CRITICAL**: User Story実装前に完了必須

- [ ] T002 Add `file_id: str | None` field to ProcessingResult in development/scripts/normalizer/models.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - ファイル追跡IDの自動生成 (Priority: P1) 🎯 MVP

**Goal**: ファイル処理時にコンテンツ+初回パスからハッシュIDを自動生成

**Independent Test**: 任意のファイルを処理し、生成されたIDがセッションログに記録されていることを確認

### Implementation for User Story 1

- [ ] T003 [US1] Add `generate_file_id(content: str, filepath: Path) -> str` function in development/scripts/normalizer/processing/single.py
- [ ] T004 [US1] Call `generate_file_id` in `process_single_file` and set `file_id` in result in development/scripts/normalizer/processing/single.py
- [ ] T005 [P] [US1] Add unit test for `generate_file_id` function in development/scripts/normalizer/tests/test_file_id.py

**Checkpoint**: User Story 1 should be fully functional - ハッシュID生成が動作

---

## Phase 4: User Story 2 - 処理履歴のID連携 (Priority: P2)

**Goal**: processed.json/errors.jsonに`file_id`フィールドを含める

**Independent Test**: 処理実行後、`processed.json`内のエントリに`file_id`が含まれていることを確認

### Implementation for User Story 2

- [ ] T006 [US2] Update `update_state` to include `file_id` in processed entries in development/scripts/normalizer/state/manager.py
- [ ] T007 [US2] Update `update_state` to include `file_id` in error entries in development/scripts/normalizer/state/manager.py
- [ ] T008 [P] [US2] Add integration test for file_id in processed.json in development/scripts/normalizer/tests/test_file_id.py

**Checkpoint**: User Stories 1 AND 2 should both work - ログにfile_idが記録される

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 検証と最終確認

- [ ] T009 Run `make test` to verify all tests pass
- [ ] T010 Manual verification: process test file and confirm file_id in processed.json

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - 確認のみ
- **Foundational (Phase 2)**: Depends on Setup - models.py の型定義更新
- **User Story 1 (Phase 3)**: Depends on Foundational - ハッシュID生成実装
- **User Story 2 (Phase 4)**: Depends on Foundational - ログ連携実装（US1と並列可）
- **Polish (Phase 5)**: Depends on all user stories

### User Story Dependencies

- **User Story 1 (P1)**: Foundational完了後に開始可能 - 独立してテスト可能
- **User Story 2 (P2)**: Foundational完了後に開始可能 - US1と並列実行可能

### Within Each User Story

- 実装タスク → テストタスク の順序
- T003 → T004 → T005 (US1)
- T006 → T007 → T008 (US2)

### Parallel Opportunities

- T005 [US1] と T008 [US2] は並列実行可能（異なるテストケース）
- US1 と US2 は Foundational 完了後に並列開始可能

---

## Parallel Example: After Foundational

```bash
# User Story 1 と User Story 2 を並列で開始可能:

# US1 Track:
Task: "Add generate_file_id function in single.py"
Task: "Call generate_file_id in process_single_file"
Task: "Add unit test for generate_file_id"

# US2 Track (can start in parallel):
Task: "Update update_state for processed entries"
Task: "Update update_state for error entries"
Task: "Add integration test for file_id in logs"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (確認)
2. Complete Phase 2: Foundational (models.py 更新)
3. Complete Phase 3: User Story 1 (ハッシュID生成)
4. **STOP and VALIDATE**: `generate_file_id` が正しく動作することを確認
5. User Story 1 完了で MVP 達成

### Full Implementation

1. Setup + Foundational → 基盤完了
2. User Story 1 → ハッシュID生成動作
3. User Story 2 → ログ連携動作
4. Polish → 全テストパス確認

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- 既存コードへの最小限変更（3ファイルのみ）
- 後方互換性維持（file_id は None 許容）
- Commit after each task or logical group
