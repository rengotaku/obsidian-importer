# Tasks: Frontmatter ファイル振り分けスクリプト

**Input**: Design documents from `/specs/057-frontmatter-file-organizer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID  | Title              | Priority | FR                          | Scenario                           |
|-----|--------------------|---------|-----------------------------|-----------------------------------|
| US1 | 振り分けプレビュー確認 | P1      | FR-002, FR-003              | ジャンル別件数表示、フォルダ存在確認 |
| US2 | ファイル振り分け実行   | P2      | FR-004-010                  | 実際のファイル移動、サマリー表示     |
| US3 | 入出力パス指定        | P3      | FR-006, FR-015              | カスタムパス、Makefile ターゲット   |

## Path Conventions

- **Main script**: `scripts/organize_files.py`
- **Config sample**: `conf/base/genre_mapping.yml.sample`
- **Tests**: `tests/test_organize_files.py`
- **Makefile**: `Makefile` (repository root)

---

## Phase 1: Setup (Shared Infrastructure) — NO TDD

**Purpose**: Project initialization, configuration files, and core module scaffolding

- [X] T001 Create scripts/ directory structure
- [X] T002 [P] Create conf/base/genre_mapping.yml.sample with default mappings
- [X] T003 [P] Add conf/base/genre_mapping.yml to .gitignore
- [X] T004 [P] Create scripts/organize_files.py scaffold with argparse CLI (--dry-run, --input, --output, --config)
- [X] T005 [P] Create tests/test_organize_files.py scaffold with unittest
- [X] T006 Add organize-preview and organize targets to Makefile
- [X] T007 Generate phase output: specs/057-frontmatter-file-organizer/tasks/ph1-output.md

---

## Phase 2: User Story 1 - 振り分けプレビュー確認 (Priority: P1) MVP

**Goal**: ユーザーがファイル移動前に振り分け計画を確認できる

**Independent Test**: `make organize-preview` でジャンル別件数と対象フォルダ存在状況が正しく表示される

### 入力

- [ ] T008 Read previous phase output: specs/057-frontmatter-file-organizer/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T009 [P] [US1] Implement test_load_config_success for config loading in tests/test_organize_files.py
- [x] T010 [P] [US1] Implement test_load_config_not_found for missing config error in tests/test_organize_files.py
- [x] T011 [P] [US1] Implement test_parse_frontmatter for YAML parsing in tests/test_organize_files.py
- [x] T012 [P] [US1] Implement test_parse_frontmatter_invalid for invalid YAML handling in tests/test_organize_files.py
- [x] T013 [P] [US1] Implement test_get_genre_mapping for English→Japanese mapping in tests/test_organize_files.py
- [x] T014 [P] [US1] Implement test_get_genre_mapping_unknown for unknown genre→その他 fallback in tests/test_organize_files.py
- [x] T015 [P] [US1] Implement test_sanitize_topic for special character replacement in tests/test_organize_files.py
- [x] T016 [P] [US1] Implement test_preview_genre_counts for genre count summary in tests/test_organize_files.py
- [x] T017 [P] [US1] Implement test_preview_folder_existence for folder existence check in tests/test_organize_files.py
- [x] T018 [P] [US1] Implement test_preview_empty_input for no files scenario in tests/test_organize_files.py
- [x] T019 Verify `make test` FAIL (RED)
- [x] T020 Generate RED output: specs/057-frontmatter-file-organizer/red-tests/ph2-test.md

### 実装 (GREEN)

- [x] T021 Read RED tests: specs/057-frontmatter-file-organizer/red-tests/ph2-test.md
- [x] T022 [P] [US1] Implement load_config() for YAML config loading in scripts/organize_files.py
- [x] T023 [P] [US1] Implement parse_frontmatter() for Markdown frontmatter extraction in scripts/organize_files.py
- [x] T024 [P] [US1] Implement get_genre_mapping() for English→Japanese mapping with fallback in scripts/organize_files.py
- [x] T025 [P] [US1] Implement sanitize_topic() for special character replacement in scripts/organize_files.py
- [x] T026 [P] [US1] Implement scan_files() to collect all .md files with frontmatter in scripts/organize_files.py
- [x] T027 [US1] Implement generate_preview() for genre counts and folder existence in scripts/organize_files.py
- [x] T028 [US1] Implement preview_mode() CLI handler with formatted output in scripts/organize_files.py
- [x] T029 Verify `make test` PASS (GREEN)

### 検証

- [x] T030 Verify `make test` passes all tests (no regressions)
- [ ] T031 Run `make organize-preview` with test fixtures to validate output
- [x] T032 Generate phase output: specs/057-frontmatter-file-organizer/tasks/ph2-output.md

**Checkpoint**: US1 完了 - プレビューモードが独立して動作することを確認

---

## Phase 3: User Story 2 - ファイル振り分け実行 (Priority: P2)

**Goal**: frontmatter の genre/topic に基づいてファイルを実際に移動する

**Independent Test**: `make organize` でファイルが正しいフォルダ構造に移動される

### 入力

- [ ] T033 Read previous phase output: specs/057-frontmatter-file-organizer/tasks/ph2-output.md

### テスト実装 (RED)

- [x] T034 [P] [US2] Implement test_get_destination_path for target path calculation in tests/test_organize_files.py
- [x] T035 [P] [US2] Implement test_get_destination_unclassified for missing genre/topic in tests/test_organize_files.py
- [x] T036 [P] [US2] Implement test_move_file_success for successful file move in tests/test_organize_files.py
- [x] T037 [P] [US2] Implement test_move_file_creates_directory for auto folder creation in tests/test_organize_files.py
- [x] T038 [P] [US2] Implement test_move_file_skip_existing for duplicate file skip in tests/test_organize_files.py
- [x] T039 [P] [US2] Implement test_organize_files_summary for success/skip/error counts in tests/test_organize_files.py
- [x] T040 Verify `make test` FAIL (RED)
- [x] T041 Generate RED output: specs/057-frontmatter-file-organizer/red-tests/ph3-test.md

### 実装 (GREEN)

- [ ] T042 Read RED tests: specs/057-frontmatter-file-organizer/red-tests/ph3-test.md
- [ ] T043 [P] [US2] Implement get_destination_path() for target path calculation in scripts/organize_files.py
- [ ] T044 [P] [US2] Implement move_file() with directory creation and skip logic in scripts/organize_files.py
- [ ] T045 [US2] Implement organize_files() for batch file processing with summary in scripts/organize_files.py
- [ ] T046 [US2] Implement execute_mode() CLI handler with confirmation prompt in scripts/organize_files.py
- [ ] T047 Verify `make test` PASS (GREEN)

### 検証

- [ ] T048 Verify `make test` passes all tests (including US1 regressions)
- [ ] T049 Run integration test: preview → execute → verify file locations
- [ ] T050 Generate phase output: specs/057-frontmatter-file-organizer/tasks/ph3-output.md

**Checkpoint**: US1 + US2 完了 - プレビュー＆実行が独立して動作することを確認

---

## Phase 4: User Story 3 - 入出力パス指定 (Priority: P3)

**Goal**: カスタム入出力パスを指定して振り分けを実行できる

**Independent Test**: カスタムパス指定で正しいパスが使用される

### 入力

- [ ] T051 Read previous phase output: specs/057-frontmatter-file-organizer/tasks/ph3-output.md

### テスト実装 (RED)

- [ ] T052 [P] [US3] Implement test_cli_default_paths for default path usage in tests/test_organize_files.py
- [ ] T053 [P] [US3] Implement test_cli_custom_input_path for custom input path in tests/test_organize_files.py
- [ ] T054 [P] [US3] Implement test_cli_custom_output_path for custom output path in tests/test_organize_files.py
- [ ] T055 [P] [US3] Implement test_cli_expand_tilde for ~ expansion in tests/test_organize_files.py
- [ ] T056 Verify `make test` FAIL (RED)
- [ ] T057 Generate RED output: specs/057-frontmatter-file-organizer/red-tests/ph4-test.md

### 実装 (GREEN)

- [ ] T058 Read RED tests: specs/057-frontmatter-file-organizer/red-tests/ph4-test.md
- [ ] T059 [US3] Implement resolve_paths() for default/custom path resolution with ~ expansion in scripts/organize_files.py
- [ ] T060 [US3] Update main() to integrate path resolution in scripts/organize_files.py
- [ ] T061 [US3] Update Makefile targets to support INPUT/OUTPUT variables
- [ ] T062 Verify `make test` PASS (GREEN)

### 検証

- [ ] T063 Verify `make test` passes all tests (including US1, US2 regressions)
- [ ] T064 Test `make organize-preview INPUT=/custom/path`
- [ ] T065 Test `make organize OUTPUT=/custom/path`
- [ ] T066 Generate phase output: specs/057-frontmatter-file-organizer/tasks/ph4-output.md

**Checkpoint**: US1 + US2 + US3 完了 - 全ユーザーストーリーが動作することを確認

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: コード品質、ドキュメント、最終検証

### 入力

- [ ] T067 Read previous phase output: specs/057-frontmatter-file-organizer/tasks/ph4-output.md

### 実装

- [ ] T068 [P] Add docstrings to all public functions in scripts/organize_files.py
- [ ] T069 [P] Run `make lint` and fix any ruff warnings
- [ ] T070 [P] Update Makefile help section with new targets
- [ ] T071 Verify quickstart.md scenarios work as documented

### 検証

- [ ] T072 Run `make test` to verify all tests pass after cleanup
- [ ] T073 Run `make coverage` and verify ≥80% coverage
- [ ] T074 Generate phase output: specs/057-frontmatter-file-organizer/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - メインエージェント直接実行
- **User Stories (Phase 2-4)**: TDD フロー (tdd-generator → phase-executor)
  - Phase 2 (US1) → Phase 3 (US2) → Phase 4 (US3)
- **Polish (Phase 5)**: Depends on all user stories - phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **入力**: Read previous phase output (context from prior work)
2. **テスト実装 (RED)**: Write tests FIRST → verify `make test` FAIL → generate RED output
3. **実装 (GREEN)**: Read RED tests → implement → verify `make test` PASS
4. **検証**: Confirm no regressions → generate phase output

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-4 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 5 (Polish)**: phase-executor のみ

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。

- Setup タスクの [P]: 異なるファイル・ディレクトリの作成で相互依存なし
- RED テストの [P]: 異なるテストメソッドで相互依存なし
- GREEN 実装の [P]: 異なる関数実装で相互依存なし

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/057-frontmatter-file-organizer/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US1 GREEN results)
│   ├── ph3-output.md           # Phase 3 output (US2 GREEN results)
│   ├── ph4-output.md           # Phase 4 output (US3 GREEN results)
│   └── ph5-output.md           # Final phase output
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED test results
    ├── ph3-test.md             # Phase 3 RED test results
    └── ph4-test.md             # Phase 4 RED test results
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (scaffolding)
2. Complete Phase 2: User Story 1 - プレビュー機能 (RED → GREEN → 検証)
3. **STOP and VALIDATE**: `make organize-preview` で動作確認
4. MVP delivers: ユーザーは振り分け計画を事前に確認できる

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. Each phase commits: `feat(057): phase-N description`

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[.md ファイル] → [frontmatter パース] → [genre マッピング] → [パス生成] → [ファイル移動]
      ↓              ↓                    ↓                ↓              ↓
   テスト         テスト               テスト            テスト         テスト
```

**チェックリスト**:
- [x] 入力パース部分のテスト (T011-T012)
- [x] 変換ロジックのテスト (T013-T015)
- [x] 出力生成部分のテスト (T034-T035)
- [x] End-to-End テスト (T049)

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD: テスト実装 (RED) → FAIL 確認 → 実装 (GREEN) → PASS 確認
- RED output must be generated BEFORE implementation begins
- Commit after each phase completion
