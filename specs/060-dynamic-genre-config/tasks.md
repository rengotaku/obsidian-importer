# Tasks: ジャンル定義の動的設定

**Input**: Design documents from `/specs/060-dynamic-genre-config/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | ジャンル定義の設定変更 | P1 | FR-001,002,005 | パラメータでジャンル追加・変更 |
| US2 | Vault マッピングと統合管理 | P1 | FR-003,004 | 設定の一元管理 |
| US3 | other 分類の改善サイクル | P1 | FR-006,007,008 | 新ジャンル自動提案 |
| US4 | バリデーションとエラーハンドリング | P2 | FR-003,004 | 設定エラー検出 |

## Path Conventions

- **Source**: `src/obsidian_etl/pipelines/organize/`
- **Config**: `conf/base/`, `conf/local/`
- **Tests**: `tests/pipelines/organize/`
- **Output**: `data/07_model_output/`

---

## Phase 1: Setup (Shared Infrastructure) — NO TDD

**Purpose**: 既存コード確認、設定ファイル更新

- [X] T001 Read current implementation in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T002 [P] Read existing tests in tests/pipelines/organize/test_nodes.py
- [X] T003 [P] Read current config format in conf/base/parameters_organize.local.yml.example
- [X] T004 Update config to new format (vault + description) in conf/base/parameters_organize.local.yml.example
- [X] T005 [P] Update local config to new format in conf/local/parameters_organize.yml
- [X] T006 Generate phase output: specs/060-dynamic-genre-config/tasks/ph1-output.md

---

## Phase 2: User Story 1+2 - ジャンル定義の動的設定 (Priority: P1) MVP

**Goal**: パラメータファイルからジャンル定義を読み込み、LLM プロンプトを動的生成する

**Independent Test**: 新ジャンルを設定に追加し、パイプライン実行で LLM がそのジャンルを使用することを確認

### 入力

- [X] T007 Read previous phase output: specs/060-dynamic-genre-config/tasks/ph1-output.md

### テスト実装 (RED)

- [X] T008 [P] [US1] Implement test_build_genre_prompt in tests/pipelines/organize/test_nodes.py
- [X] T009 [P] [US1] Implement test_parse_genre_config_new_format in tests/pipelines/organize/test_nodes.py
- [X] T010 [P] [US2] Implement test_valid_genres_from_config in tests/pipelines/organize/test_nodes.py
- [X] T011 [P] [US2] Implement test_genre_fallback_to_other in tests/pipelines/organize/test_nodes.py
- [X] T012 Verify `make test` FAIL (RED)
- [X] T013 Generate RED output: specs/060-dynamic-genre-config/red-tests/ph2-test.md

### 実装 (GREEN)

- [X] T014 Read RED tests: specs/060-dynamic-genre-config/red-tests/ph2-test.md
- [X] T015 [P] [US1] Implement _build_genre_prompt() in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T016 [P] [US1] Implement _parse_genre_config() in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T017 [US1] Update _extract_topic_and_genre_via_llm() to use dynamic prompt in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T018 [US2] Update valid_genres validation to use config keys in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T019 Verify `make test` PASS (GREEN)

### 検証

- [X] T020 Verify `make test` passes all tests (no regressions)
- [X] T021 Generate phase output: specs/060-dynamic-genre-config/tasks/ph2-output.md

**Checkpoint**: US1+US2 should be fully functional - パラメータでジャンル追加・変更が動作

---

## Phase 3: User Story 3 - other 分類の改善サイクル (Priority: P1)

**Goal**: other が5件以上の場合に新ジャンル候補を自動提案

**Independent Test**: other 分類が5件以上ある状態で make run を実行し、genre_suggestions.md が生成されることを確認

### 入力

- [X] T022 Read previous phase output: specs/060-dynamic-genre-config/tasks/ph2-output.md

### テスト実装 (RED)

- [X] T023 [P] [US3] Implement test_analyze_other_genres_trigger in tests/pipelines/organize/test_nodes.py
- [X] T024 [P] [US3] Implement test_analyze_other_genres_below_threshold in tests/pipelines/organize/test_nodes.py
- [X] T025 [P] [US3] Implement test_generate_genre_suggestions_md in tests/pipelines/organize/test_nodes.py
- [X] T026 [P] [US3] Implement test_suggest_genre_with_llm in tests/pipelines/organize/test_nodes.py
- [X] T027 Verify `make test` FAIL (RED)
- [X] T028 Generate RED output: specs/060-dynamic-genre-config/red-tests/ph3-test.md

### 実装 (GREEN)

- [X] T029 Read RED tests: specs/060-dynamic-genre-config/red-tests/ph3-test.md
- [X] T030 [P] [US3] Implement _suggest_new_genres_via_llm() in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T031 [P] [US3] Implement _generate_suggestions_markdown() in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T032 [US3] Implement analyze_other_genres() node in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T033 [US3] Add analyze_other_genres node to pipeline in src/obsidian_etl/pipelines/organize/pipeline.py
- [X] T034 Verify `make test` PASS (GREEN)

### 検証

- [X] T035 Verify `make test` passes all tests (including US1, US2)
- [X] T036 Generate phase output: specs/060-dynamic-genre-config/tasks/ph3-output.md

**Checkpoint**: US3 should be fully functional - other 5件以上で提案が出力される

---

## Phase 4: User Story 4 - バリデーションとエラーハンドリング (Priority: P2)

**Goal**: 設定エラー時に明確なメッセージを出力

**Independent Test**: 不正な設定でパイプラインを実行し、適切なエラー/警告が表示されることを確認

### 入力

- [X] T037 Read previous phase output: specs/060-dynamic-genre-config/tasks/ph3-output.md

### テスト実装 (RED)

- [X] T038 [P] [US4] Implement test_missing_description_warning in tests/pipelines/organize/test_nodes.py
- [X] T039 [P] [US4] Implement test_missing_vault_error in tests/pipelines/organize/test_nodes.py
- [X] T040 [P] [US4] Implement test_empty_genre_mapping_fallback in tests/pipelines/organize/test_nodes.py
- [X] T041 Verify `make test` FAIL (RED)
- [X] T042 Generate RED output: specs/060-dynamic-genre-config/red-tests/ph4-test.md

### 実装 (GREEN)

- [ ] T043 Read RED tests: specs/060-dynamic-genre-config/red-tests/ph4-test.md
- [ ] T044 [US4] Add validation logic to _parse_genre_config() in src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T045 [US4] Add warning/error logging for invalid config in src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T046 Verify `make test` PASS (GREEN)

### 検証

- [ ] T047 Verify `make test` passes all tests (including US1, US2, US3)
- [ ] T048 Generate phase output: specs/060-dynamic-genre-config/tasks/ph4-output.md

**Checkpoint**: US4 should be fully functional - 設定エラーが適切に検出される

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: クリーンアップと最終検証

### 入力

- [ ] T049 Read previous phase output: specs/060-dynamic-genre-config/tasks/ph4-output.md

### 実装

- [ ] T050 [P] Remove hardcoded genre definitions from nodes.py
- [ ] T051 [P] Remove hardcoded valid_genres set from nodes.py
- [ ] T052 [P] Update docstrings for modified functions in nodes.py
- [ ] T053 Run `make lint` and fix any issues

### 検証

- [ ] T054 Run `make test` to verify all tests pass after cleanup
- [ ] T055 Run `make coverage` to verify ≥80% coverage
- [ ] T056 Generate phase output: specs/060-dynamic-genre-config/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - メインエージェント直接実行
- **US1+US2 (Phase 2)**: TDD フロー (tdd-generator → phase-executor)
- **US3 (Phase 3)**: Depends on Phase 2 - TDD フロー
- **US4 (Phase 4)**: Depends on Phase 3 - TDD フロー
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

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/060-dynamic-genre-config/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US1+US2 GREEN results)
│   ├── ph3-output.md           # Phase 3 output (US3 GREEN results)
│   ├── ph4-output.md           # Phase 4 output (US4 GREEN results)
│   └── ph5-output.md           # Phase 5 output (Polish results)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED test results
    ├── ph3-test.md             # Phase 3 RED test results
    └── ph4-test.md             # Phase 4 RED test results
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (設定ファイル更新)
2. Complete Phase 2: US1+US2 (RED → GREEN → 検証)
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. Verify: 新ジャンルを追加して分類されることを手動確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. Each phase commits: `feat(060): phase-N description`

---

## Notes

- US1 と US2 は密接に関連するため Phase 2 で同時実装
- US3 (other 分析) は独立した機能だが、US1+US2 の設定読み込みに依存
- US4 (バリデーション) は他の機能を壊さないよう最後に実装
- [P] tasks = no dependencies, execution order free
