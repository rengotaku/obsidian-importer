# Tasks: 全工程での file_id 付与・維持

**Input**: Design documents from `/specs/023-phase1-file-id/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `development/scripts/llm_import/` and `development/scripts/normalizer/`
- **Tests**: `development/scripts/llm_import/tests/` and `development/scripts/normalizer/tests/`

---

## Phase 1: Setup

**Purpose**: 準備と既存コード確認

- [x] T001 Read previous phase output: N/A (first phase)
- [x] T002 Verify existing `file_id.py` module in `development/scripts/llm_import/common/file_id.py`
- [x] T003 Run `make test` to verify baseline tests pass
- [x] T004 Generate phase output: `specs/023-phase1-file-id/tasks/ph1-output.md`

---

## Phase 2: User Story 1 - Phase 1 完了時点でのファイル追跡 (Priority: P1)

**Goal**: Phase 1（パース）完了時点で parsed ファイルの frontmatter に `file_id` を含める

**Independent Test**: Phase 1 実行後、parsed ディレクトリのファイルの frontmatter に `file_id: [12文字16進数]` が含まれることを確認

### Implementation for User Story 1

- [x] T005 Read previous phase output: `specs/023-phase1-file-id/tasks/ph1-output.md`
- [x] T006 [P] [US1] Add `file_id` parameter to `ClaudeParser.to_markdown()` in `development/scripts/llm_import/providers/claude/parser.py`
- [x] T007 [P] [US1] Add test for `to_markdown()` with file_id in `development/scripts/llm_import/tests/providers/test_claude_parser.py`
- [x] T008 [US1] Update `cli.py` Phase 1 processing to generate and pass file_id to `to_markdown()` in `development/scripts/llm_import/cli.py`
- [x] T009 [US1] Add test for Phase 1 file_id generation in `development/scripts/llm_import/tests/test_cli.py`
- [x] T010 Run `make test` to verify all tests pass
- [x] T011 Generate phase output: `specs/023-phase1-file-id/tasks/ph2-output.md`

**Checkpoint**: Phase 1 parsed ファイルに file_id が含まれる

---

## Phase 3: User Story 2 - pipeline_stages.jsonl での file_id 記録 (Priority: P2)

**Goal**: 各パイプラインステージの実行ログに file_id を含める

**Independent Test**: インポート実行後、`pipeline_stages.jsonl` の各エントリに `file_id` フィールドが存在することを確認

### Implementation for User Story 2

- [x] T012 Read previous phase output: `specs/023-phase1-file-id/tasks/ph2-output.md`
- [x] T013 [P] [US2] Add optional `file_id` parameter to `log_stage()` in `development/scripts/llm_import/common/session_logger.py`
- [x] T014 [P] [US2] Add test for `log_stage()` with file_id in `development/scripts/llm_import/tests/test_session_logger.py`
- [x] T015 [US2] Update `cli.py` to pass file_id to `log_stage()` for Phase 1 in `development/scripts/llm_import/cli.py`
- [x] T016 [US2] Update `cli.py` to pass file_id to `log_stage()` for Phase 2 in `development/scripts/llm_import/cli.py`
- [x] T017 [US2] Add test for pipeline_stages.jsonl file_id recording in `development/scripts/llm_import/tests/test_cli.py`
- [x] T018 Run `make test` to verify all tests pass
- [x] T019 Generate phase output: `specs/023-phase1-file-id/tasks/ph3-output.md`

**Checkpoint**: pipeline_stages.jsonl に file_id が記録される

---

## Phase 4: User Story 2 Continued - Phase 2 での file_id 継承 (Priority: P2)

**Goal**: Phase 2 実行時に parsed ファイルから file_id を読み取り、出力ファイルに継承する

**Independent Test**: Phase 1 → Phase 2 間で file_id が一致する

### Implementation for Phase 2 Inheritance

- [x] T020 Read previous phase output: `specs/023-phase1-file-id/tasks/ph3-output.md`
- [x] T021 [US2] Update `extract_frontmatter()` or add helper to read file_id from parsed file in `development/scripts/llm_import/common/knowledge_extractor.py`
- [x] T022 [US2] Update `cli.py` Phase 2 processing to inherit file_id from parsed file in `development/scripts/llm_import/cli.py`
- [x] T023 [US2] Add test for Phase 2 file_id inheritance in `development/scripts/llm_import/tests/test_knowledge_extractor.py`
- [x] T024 [US2] Add test for Phase 1 → Phase 2 file_id consistency in `development/scripts/llm_import/tests/test_cli.py`
- [x] T025 Run `make test` to verify all tests pass
- [x] T026 Generate phase output: `specs/023-phase1-file-id/tasks/ph4-output.md`

**Checkpoint**: Phase 1 と Phase 2 で file_id が一致

---

## Phase 5: User Story 3 - Organize 時の file_id 付与・維持 (Priority: P3)

**Goal**: `@index/` から Vaults へファイルを移動する際に file_id が付与・維持される

**Independent Test**: `/og:organize` 実行後、Vaults 内のすべてのファイルの frontmatter に `file_id` が存在することを確認

### Implementation for User Story 3

- [x] T027 Read previous phase output: `specs/023-phase1-file-id/tasks/ph4-output.md`
- [x] T028 [P] [US3] Update `process_single_file()` to check existing file_id in frontmatter in `development/scripts/normalizer/processing/single.py`
- [x] T029 [P] [US3] Implement `get_or_generate_file_id()` helper in `development/scripts/normalizer/processing/single.py`
- [x] T030 [US3] Update `build_normalized_file()` call to use existing or generated file_id in `development/scripts/normalizer/processing/single.py`
- [x] T031 [P] [US3] Add test for file_id preservation in `development/scripts/normalizer/tests/test_single.py`
- [x] T032 [P] [US3] Add test for file_id generation when missing in `development/scripts/normalizer/tests/test_single.py`
- [x] T033 Run `make test` to verify all tests pass
- [x] T034 Generate phase output: `specs/023-phase1-file-id/tasks/ph5-output.md`

**Checkpoint**: organize で file_id が維持/生成される

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 統合テストと品質確認

- [x] T035 Read previous phase output: `specs/023-phase1-file-id/tasks/ph5-output.md`
- [x] T036 [P] Verify backward compatibility with existing state.json (file_id なしエントリ)
- [x] T037 [P] Verify backward compatibility with existing pipeline_stages.jsonl (file_id なしエントリ)
- [x] T038 Run quickstart.md validation scenarios manually
- [x] T039 Run `make test` to verify all tests pass
- [x] T040 Generate phase output: `specs/023-phase1-file-id/tasks/ph6-output.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (US1)**: Depends on Phase 1 completion
- **Phase 3 (US2 - logging)**: Depends on Phase 2 completion
- **Phase 4 (US2 - inheritance)**: Depends on Phase 3 completion
- **Phase 5 (US3)**: Depends on Phase 2 completion (can run in parallel with Phase 3/4)
- **Phase 6 (Polish)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories - Phase 1 file_id generation
- **US2 (P2)**: Depends on US1 for file_id to log/inherit
- **US3 (P3)**: Independent - can run after US1, parallel to US2

### Parallel Opportunities

- T006, T007 can run in parallel (different files)
- T013, T014 can run in parallel (different files)
- T028, T029, T031, T032 can run in parallel (different aspects of US3)
- T036, T037 can run in parallel (backward compatibility checks)

---

## Parallel Example: Phase 5 (User Story 3)

```bash
# Launch parallel tasks for normalizer file_id support:
Task: "Update process_single_file() to check existing file_id" [T028]
Task: "Implement get_or_generate_file_id() helper" [T029]
Task: "Add test for file_id preservation" [T031]
Task: "Add test for file_id generation when missing" [T032]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: User Story 1 (Phase 1 file_id 生成)
3. **STOP and VALIDATE**: parsed ファイルに file_id が含まれることを確認
4. Deploy if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → parsed に file_id 付与 (MVP!)
2. Phase 3 + Phase 4 → pipeline_stages.jsonl と Phase 2 継承
3. Phase 5 → organize での維持/生成
4. Phase 6 → 品質確認

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[Claude Export] → [Phase 1 parse] → [Phase 2 extract] → [Organize]
                        ↓                  ↓                ↓
                   file_id生成         file_id継承       file_id維持/生成
                        ↓                  ↓                ↓
                     テスト             テスト            テスト
```

**チェックリスト**:
- [ ] Phase 1 で file_id が frontmatter に出力されるテスト
- [ ] Phase 2 で file_id が継承されるテスト
- [ ] pipeline_stages.jsonl に file_id が記録されるテスト
- [ ] organize で file_id が維持されるテスト
- [ ] organize で file_id がない場合に生成されるテスト

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
