# Tasks: Vault配下ファイル階層化

**Input**: Design documents from `/specs/013-vault-hierarchy/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: テストタスクは明示的に要求されていないため省略

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `.claude/scripts/` at repository root
- Paths shown below follow plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create hierarchy_logs directory in @index/hierarchy_logs/
- [x] T002 Create hierarchy_organizer.py skeleton in .claude/scripts/hierarchy_organizer.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Implement Vault class (name, path, subfolders discovery) in .claude/scripts/hierarchy_organizer.py
- [x] T004 Implement Subfolder class (name, path, file_count) in .claude/scripts/hierarchy_organizer.py
- [x] T005 [P] Implement MarkdownFile class (metadata extraction from frontmatter) in .claude/scripts/hierarchy_organizer.py
- [x] T006 [P] Implement ClassificationResult dataclass in .claude/scripts/hierarchy_organizer.py
- [x] T007 Implement LLM client (Ollama API call with hierarchy prompt) in .claude/scripts/hierarchy_organizer.py
- [x] T008 Implement dynamic subfolder list injection into LLM prompt in .claude/scripts/hierarchy_organizer.py
- [x] T009 Implement JSON response parser with error handling in .claude/scripts/hierarchy_organizer.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 既存ファイルの階層整理 (Priority: P1) 🎯 MVP

**Goal**: Vaultルート直下のファイルをLLMで分類し、サブフォルダへ移動

**Independent Test**: エンジニアVaultのファイル10件を手動で選択し、適切なサブフォルダへ分類・移動できることを確認

### Implementation for User Story 1

- [x] T010 [US1] Implement scan_vault_root() to list root-level .md files in .claude/scripts/hierarchy_organizer.py
- [x] T011 [US1] Implement classify_file() to call LLM and get subfolder suggestion in .claude/scripts/hierarchy_organizer.py
- [x] T012 [US1] Implement batch classification with progress bar in .claude/scripts/hierarchy_organizer.py
- [x] T013 [US1] Implement MoveOperation class (source, dest, status) in .claude/scripts/hierarchy_organizer.py
- [x] T014 [US1] Implement move_file() with collision handling (_1, _2 suffix) in .claude/scripts/hierarchy_organizer.py
- [x] T015 [US1] Implement MoveLog class and JSON serialization in .claude/scripts/hierarchy_organizer.py
- [x] T016 [US1] Implement execute_moves() to perform actual file operations in .claude/scripts/hierarchy_organizer.py
- [x] T017 [US1] Add CLI argument parsing (VAULT, --execute, --limit, --confidence) in .claude/scripts/hierarchy_organizer.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - @indexからの移動時に階層配置 (Priority: P2)

**Goal**: @indexからVaultへ移動する際にジャンル＋サブフォルダを同時判定

**Independent Test**: @indexにテストファイル3件を配置し、organize実行時にVaultの適切なサブフォルダへ直接配置されることを確認

### Implementation for User Story 2

- [x] T018 [US2] Extend LLM prompt to include genre + subfolder simultaneous classification in .claude/scripts/hierarchy_organizer.py
- [x] T019 [US2] Implement classify_for_organize() that returns genre and subfolder in .claude/scripts/hierarchy_organizer.py
- [x] T020 [US2] Add --from-index mode to process files from @index/ in .claude/scripts/hierarchy_organizer.py
- [x] T021 [US2] Implement move_to_vault_subfolder() combining genre and hierarchy in .claude/scripts/hierarchy_organizer.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 階層構造のプレビューと確認 (Priority: P3)

**Goal**: 移動前にプレビュー表示し、ユーザーが確認・修正可能

**Independent Test**: ドライランモードで10件のファイルの移動先を表示し、ユーザーが確認できることを確認

### Implementation for User Story 3

- [x] T022 [US3] Implement preview_results() to display proposed moves in table format in .claude/scripts/hierarchy_organizer.py
- [x] T023 [US3] Add --output option for CSV/JSON export of preview in .claude/scripts/hierarchy_organizer.py
- [x] T024 [US3] Add --format option (csv/json) for output format selection in .claude/scripts/hierarchy_organizer.py
- [x] T025 [US3] Implement summary statistics (total, to_move, new_folders) in .claude/scripts/hierarchy_organizer.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T026 [P] Add Makefile targets (hierarchy-preview, hierarchy-execute) in Makefile
- [x] T027 [P] Add --new-folders option to control new folder creation in .claude/scripts/hierarchy_organizer.py
- [x] T028 [P] Add --verbose option for detailed logging in .claude/scripts/hierarchy_organizer.py
- [x] T029 Implement --rollback option to undo moves from log file in .claude/scripts/hierarchy_organizer.py
- [x] T030 Add exit codes (0-4) per CLI contract in .claude/scripts/hierarchy_organizer.py
- [x] T031 Run manual validation with 10 files per quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories proceed sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after US1 (extends LLM prompt from US1)
- **User Story 3 (P3)**: Can start after Foundational - Adds preview to existing classification logic

### Within Each User Story

- Models/classes before services
- Services before CLI integration
- Core implementation before options/flags
- Story complete before moving to next priority

### Parallel Opportunities

- T005, T006 can run in parallel (different classes)
- T026, T027, T028 can run in parallel (different files/options)

---

## Parallel Example: Foundational Phase

```bash
# Launch in parallel:
Task: "Implement MarkdownFile class in .claude/scripts/hierarchy_organizer.py"
Task: "Implement ClassificationResult dataclass in .claude/scripts/hierarchy_organizer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T009)
3. Complete Phase 3: User Story 1 (T010-T017)
4. **STOP and VALIDATE**: Test with `python .claude/scripts/hierarchy_organizer.py エンジニア -l 10`
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP完成！**
3. Add User Story 2 → Test independently → @index統合
4. Add User Story 3 → Test independently → プレビュー機能追加
5. Add Polish → 本番運用準備完了

---

## Notes

- [P] tasks = different files/classes, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- 全タスクは単一ファイル hierarchy_organizer.py に実装（既存スクリプトパターンに従う）

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1: Setup | T001-T002 | 2 tasks |
| Phase 2: Foundational | T003-T009 | 7 tasks |
| Phase 3: US1 (P1) MVP | T010-T017 | 8 tasks |
| Phase 4: US2 (P2) | T018-T021 | 4 tasks |
| Phase 5: US3 (P3) | T022-T025 | 4 tasks |
| Phase 6: Polish | T026-T031 | 6 tasks |
| **Total** | | **31 tasks** |
