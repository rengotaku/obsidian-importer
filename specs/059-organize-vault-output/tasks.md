# Tasks: Organize パイプラインの Obsidian Vault 直接出力対応

**Input**: Design documents from `/specs/059-organize-vault-output/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## User Story Summary

| ID  | Title                      | Priority | FR              | Scenario                                   |
|-----|----------------------------|----------|-----------------|-------------------------------------------|
| US1 | Preview（出力先確認）       | P1       | FR-001,002,003,005,006 | 出力先一覧・競合・サマリー表示 |
| US2 | Vault へのコピー            | P2       | FR-001,002,004,008 | ファイルコピー（skip デフォルト）|
| US3 | 競合スキップ               | P3       | FR-004,007      | 既存ファイルをスキップ                     |
| US4 | 競合上書き                 | P4       | FR-004,007      | 既存ファイルを上書き                       |
| US5 | 競合別名保存               | P5       | FR-004,007      | file_1.md 形式で保存                       |

## Path Conventions

- **Source**: `src/obsidian_etl/pipelines/vault_output/`
- **Tests**: `tests/unit/pipelines/vault_output/`
- **Config**: `conf/base/parameters.yml`
- **Registry**: `src/obsidian_etl/pipeline_registry.py`

---

## Phase 1: Setup (Shared Infrastructure) — NO TDD

**Purpose**: 既存コード確認、ディレクトリ構造作成、パラメータ追加

- [x] T001 Read existing organize nodes in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T002 [P] Read existing pipeline_registry in src/obsidian_etl/pipeline_registry.py
- [x] T003 [P] Read existing parameters in conf/base/parameters.yml
- [x] T004 Create directory src/obsidian_etl/pipelines/vault_output/
- [x] T005 [P] Create src/obsidian_etl/pipelines/vault_output/__init__.py
- [x] T006 [P] Create tests/unit/pipelines/vault_output/__init__.py
- [x] T007 Add vault_base_path and genre_vault_mapping to conf/base/parameters.yml
- [x] T008 Generate phase output: specs/059-organize-vault-output/tasks/ph1-output.md

---

## Phase 2: User Story 1 - Preview（出力先確認）(Priority: P1) MVP

**Goal**: organized フォルダ内ファイルの出力先 Vault パスと競合情報を表示

**Independent Test**: `kedro run --pipeline=organize_preview` で出力先一覧と競合が表示される

### 入力

- [x] T009 Read previous phase output: specs/059-organize-vault-output/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T010 [P] [US1] Implement test_resolve_vault_destination_ai_to_engineer in tests/unit/pipelines/vault_output/test_nodes.py
- [x] T011 [P] [US1] Implement test_resolve_vault_destination_with_topic_subfolder in tests/unit/pipelines/vault_output/test_nodes.py
- [x] T012 [P] [US1] Implement test_resolve_vault_destination_empty_topic in tests/unit/pipelines/vault_output/test_nodes.py
- [x] T013 [P] [US1] Implement test_sanitize_topic_special_chars in tests/unit/pipelines/vault_output/test_nodes.py
- [x] T014 [P] [US1] Implement test_check_conflicts_detects_existing_file in tests/unit/pipelines/vault_output/test_nodes.py
- [x] T015 [P] [US1] Implement test_check_conflicts_no_conflict in tests/unit/pipelines/vault_output/test_nodes.py
- [x] T016 [P] [US1] Implement test_log_preview_summary_output_format in tests/unit/pipelines/vault_output/test_nodes.py
- [x] T017 Verify `make test` FAIL (RED)
- [x] T018 Generate RED output: specs/059-organize-vault-output/red-tests/ph2-test.md

### 実装 (GREEN)

- [x] T019 Read RED tests: specs/059-organize-vault-output/red-tests/ph2-test.md
- [x] T020 [P] [US1] Implement sanitize_topic() helper in src/obsidian_etl/pipelines/vault_output/nodes.py
- [x] T021 [P] [US1] Implement resolve_vault_destination() node in src/obsidian_etl/pipelines/vault_output/nodes.py
- [x] T022 [P] [US1] Implement check_conflicts() node in src/obsidian_etl/pipelines/vault_output/nodes.py
- [x] T023 [P] [US1] Implement log_preview_summary() node in src/obsidian_etl/pipelines/vault_output/nodes.py
- [x] T024 [US1] Create create_preview_pipeline() in src/obsidian_etl/pipelines/vault_output/pipeline.py
- [x] T025 [US1] Register organize_preview pipeline in src/obsidian_etl/pipeline_registry.py
- [x] T026 Verify `make test` PASS (GREEN)

### 検証

- [x] T027 Verify `make test` passes all tests (no regressions)
- [x] T028 Generate phase output: specs/059-organize-vault-output/tasks/ph2-output.md

**Checkpoint**: `kedro run --pipeline=organize_preview` が動作し、出力先一覧と競合が表示される

---

## Phase 3: User Story 2+3 - Vault へのコピー（skip デフォルト）(Priority: P2)

**Goal**: ファイルを Vault にコピー。競合時はデフォルトでスキップ

**Independent Test**: `kedro run --pipeline=organize_to_vault` でファイルがコピーされる

### 入力

- [ ] T029 Read previous phase output: specs/059-organize-vault-output/tasks/ph2-output.md

### テスト実装 (RED)

- [ ] T030 [P] [US2] Implement test_copy_to_vault_creates_file in tests/unit/pipelines/vault_output/test_nodes.py
- [ ] T031 [P] [US2] Implement test_copy_to_vault_creates_subfolder in tests/unit/pipelines/vault_output/test_nodes.py
- [ ] T032 [P] [US3] Implement test_copy_to_vault_skip_existing in tests/unit/pipelines/vault_output/test_nodes.py
- [ ] T033 [P] [US2] Implement test_log_copy_summary_output_format in tests/unit/pipelines/vault_output/test_nodes.py
- [ ] T034 [P] [US2] Implement test_copy_to_vault_permission_error_skips in tests/unit/pipelines/vault_output/test_nodes.py
- [ ] T035 Verify `make test` FAIL (RED)
- [ ] T036 Generate RED output: specs/059-organize-vault-output/red-tests/ph3-test.md

### 実装 (GREEN)

- [ ] T037 Read RED tests: specs/059-organize-vault-output/red-tests/ph3-test.md
- [ ] T038 [P] [US2] Implement copy_to_vault() node in src/obsidian_etl/pipelines/vault_output/nodes.py
- [ ] T039 [P] [US2] Implement log_copy_summary() node in src/obsidian_etl/pipelines/vault_output/nodes.py
- [ ] T040 [US2] Create create_vault_pipeline() in src/obsidian_etl/pipelines/vault_output/pipeline.py
- [ ] T041 [US2] Register organize_to_vault pipeline in src/obsidian_etl/pipeline_registry.py
- [ ] T042 Verify `make test` PASS (GREEN)

### 検証

- [ ] T043 Verify `make test` passes all tests (no regressions)
- [ ] T044 Generate phase output: specs/059-organize-vault-output/tasks/ph3-output.md

**Checkpoint**: `kedro run --pipeline=organize_to_vault` でファイルがコピーされ、競合時はスキップ

---

## Phase 4: User Story 4 - 競合上書き (Priority: P4)

**Goal**: `--overwrite` オプションで既存ファイルを上書き

**Independent Test**: `--params='{"organize.conflict_handling": "overwrite"}'` で既存ファイルが更新される

### 入力

- [ ] T045 Read previous phase output: specs/059-organize-vault-output/tasks/ph3-output.md

### テスト実装 (RED)

- [ ] T046 [P] [US4] Implement test_copy_to_vault_overwrite_existing in tests/unit/pipelines/vault_output/test_nodes.py
- [ ] T047 [P] [US4] Implement test_handle_conflict_overwrite_mode in tests/unit/pipelines/vault_output/test_nodes.py
- [ ] T048 Verify `make test` FAIL (RED)
- [ ] T049 Generate RED output: specs/059-organize-vault-output/red-tests/ph4-test.md

### 実装 (GREEN)

- [ ] T050 Read RED tests: specs/059-organize-vault-output/red-tests/ph4-test.md
- [ ] T051 [US4] Add overwrite mode to copy_to_vault() in src/obsidian_etl/pipelines/vault_output/nodes.py
- [ ] T052 Verify `make test` PASS (GREEN)

### 検証

- [ ] T053 Verify `make test` passes all tests (no regressions)
- [ ] T054 Generate phase output: specs/059-organize-vault-output/tasks/ph4-output.md

**Checkpoint**: `--overwrite` で既存ファイルが上書きされる

---

## Phase 5: User Story 5 - 競合別名保存 (Priority: P5)

**Goal**: `--increment` オプションで file_1.md 形式で保存

**Independent Test**: `--params='{"organize.conflict_handling": "increment"}'` で別名ファイルが作成される

### 入力

- [ ] T055 Read previous phase output: specs/059-organize-vault-output/tasks/ph4-output.md

### テスト実装 (RED)

- [ ] T056 [P] [US5] Implement test_find_incremented_path_first in tests/unit/pipelines/vault_output/test_nodes.py
- [ ] T057 [P] [US5] Implement test_find_incremented_path_second in tests/unit/pipelines/vault_output/test_nodes.py
- [ ] T058 [P] [US5] Implement test_copy_to_vault_increment_existing in tests/unit/pipelines/vault_output/test_nodes.py
- [ ] T059 Verify `make test` FAIL (RED)
- [ ] T060 Generate RED output: specs/059-organize-vault-output/red-tests/ph5-test.md

### 実装 (GREEN)

- [ ] T061 Read RED tests: specs/059-organize-vault-output/red-tests/ph5-test.md
- [ ] T062 [P] [US5] Implement find_incremented_path() helper in src/obsidian_etl/pipelines/vault_output/nodes.py
- [ ] T063 [US5] Add increment mode to copy_to_vault() in src/obsidian_etl/pipelines/vault_output/nodes.py
- [ ] T064 Verify `make test` PASS (GREEN)

### 検証

- [ ] T065 Verify `make test` passes all tests (no regressions)
- [ ] T066 Generate phase output: specs/059-organize-vault-output/tasks/ph5-output.md

**Checkpoint**: `--increment` で file_1.md 形式の別名ファイルが作成される

---

## Phase 6: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: コードクリーンアップ、ドキュメント検証、最終確認

### 入力

- [ ] T067 Read previous phase output: specs/059-organize-vault-output/tasks/ph5-output.md

### 実装

- [ ] T068 [P] Add docstrings to all public functions in src/obsidian_etl/pipelines/vault_output/nodes.py
- [ ] T069 [P] Verify edge cases: topic with special chars, missing genre, permission errors
- [ ] T070 Run quickstart.md validation (manual test with real data)

### 検証

- [ ] T071 Run `make test` to verify all tests pass
- [ ] T072 Run `make coverage` to verify ≥80% coverage
- [ ] T073 Generate phase output: specs/059-organize-vault-output/tasks/ph6-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - メインエージェント直接実行
- **Phase 2 (US1 Preview)**: Depends on Phase 1 - TDD (tdd-generator → phase-executor)
- **Phase 3 (US2+US3 Copy)**: Depends on Phase 2 - TDD (tdd-generator → phase-executor)
- **Phase 4 (US4 Overwrite)**: Depends on Phase 3 - TDD (tdd-generator → phase-executor)
- **Phase 5 (US5 Increment)**: Depends on Phase 4 - TDD (tdd-generator → phase-executor)
- **Phase 6 (Polish)**: Depends on Phase 5 - phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **入力**: Read previous phase output (context from prior work)
2. **テスト実装 (RED)**: Write tests FIRST → verify `make test` FAIL → generate RED output
3. **実装 (GREEN)**: Read RED tests → implement → verify `make test` PASS
4. **検証**: Confirm no regressions → generate phase output

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-5 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 6 (Polish)**: phase-executor のみ

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。

- Setup タスクの [P]: 異なるファイル・ディレクトリの作成で相互依存なし
- RED テストの [P]: 異なるテストメソッドへの書き込みで相互依存なし
- GREEN 実装の [P]: 異なる関数の実装で相互依存なし

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/059-organize-vault-output/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US1 Preview)
│   ├── ph3-output.md           # Phase 3 output (US2+US3 Copy)
│   ├── ph4-output.md           # Phase 4 output (US4 Overwrite)
│   ├── ph5-output.md           # Phase 5 output (US5 Increment)
│   └── ph6-output.md           # Phase 6 output (Polish)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED tests
    ├── ph3-test.md             # Phase 3 RED tests
    ├── ph4-test.md             # Phase 4 RED tests
    └── ph5-test.md             # Phase 5 RED tests
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: User Story 1 (Preview)
3. **STOP and VALIDATE**: `kedro run --pipeline=organize_preview` で動作確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
2. Each phase commits: `feat(phase-N): description`

### Suggested MVP Scope

- **Phase 1 + Phase 2**: Preview 機能のみで出力先確認が可能
- これだけでユーザーは Vault 構造を事前確認できる

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[organized/*.md] → [frontmatter解析] → [Vault解決] → [競合検出] → [ファイルコピー]
       ↓              ↓                 ↓              ↓              ↓
     入力検証      genre/topic抽出   パスマッピング   既存チェック    書き込み
```

**チェックリスト**:
- [x] frontmatter パース部分のテスト (既存 organize で対応済み)
- [ ] Vault 解決ロジックのテスト (resolve_vault_destination)
- [ ] 競合検出のテスト (check_conflicts)
- [ ] ファイルコピーのテスト (copy_to_vault)
- [ ] End-to-End テスト（パイプライン実行）

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- US3 (skip) is the default behavior, tested together with US2
- Each user story should be independently completable and testable
- TDD: テスト実装 (RED) → FAIL 確認 → 実装 (GREEN) → PASS 確認
- Commit after each phase completion
