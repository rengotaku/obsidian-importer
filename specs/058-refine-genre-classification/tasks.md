# Tasks: ETL ジャンル分類の細分化

**Input**: Design documents from `/specs/058-refine-genre-classification/`
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
| US1 | ジャンル分類の精度向上 | P1 | FR-001,003,004 | 「その他」30%以下 |
| US2 | 新ジャンルへの適切なマッピング | P1 | FR-002,005 | 各新ジャンルの分類テスト |
| US3 | 既存分類との後方互換性 | P2 | FR-006 | 既存テスト全パス |

**Note**: US1 と US2 は密結合（ジャンル追加にはキーワード定義が必須）のため、Phase 2 で統合実装。

## Path Conventions

- **Source**: `src/obsidian_etl/pipelines/organize/nodes.py`
- **Config**: `conf/base/parameters.yml`
- **Tests**: `tests/test_organize_files.py`
- **Docs**: `CLAUDE.md`

---

## Phase 1: Setup — NO TDD

**Purpose**: 既存実装の確認と変更準備

- [X] T001 Read current classify_genre implementation in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T002 [P] Read existing genre keywords in conf/base/parameters.yml
- [X] T003 [P] Read existing tests in tests/pipelines/organize/test_nodes.py
- [X] T004 Run `make test` to confirm current test suite passes
- [X] T005 Generate phase output: specs/058-refine-genre-classification/tasks/ph1-output.md

---

## Phase 2: US1+US2 - 新ジャンル追加とキーワードマッピング (Priority: P1) MVP

**Goal**: 6つの新ジャンル（ai, devops, lifestyle, parenting, travel, health）を追加し、適切なキーワードをマッピング

**Independent Test**: `kedro run` 後、`organized/` 配下に新ジャンルフォルダが作成され、「その他」が30%以下になる

### 入力

- [x] T006 Read previous phase output: specs/058-refine-genre-classification/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T007 [P] [US1] Implement test_classify_genre_ai for AI keywords in tests/test_organize_files.py
- [x] T008 [P] [US1] Implement test_classify_genre_devops for DevOps keywords in tests/test_organize_files.py
- [x] T009 [P] [US2] Implement test_classify_genre_lifestyle for lifestyle keywords in tests/test_organize_files.py
- [x] T010 [P] [US2] Implement test_classify_genre_parenting for parenting keywords in tests/test_organize_files.py
- [x] T011 [P] [US2] Implement test_classify_genre_travel for travel keywords in tests/test_organize_files.py
- [x] T012 [P] [US2] Implement test_classify_genre_health for health keywords in tests/test_organize_files.py
- [x] T013 [P] [US1] Implement test_classify_genre_priority_ai_over_engineer for priority order in tests/test_organize_files.py
- [x] T014 [P] [US1] Implement test_classify_genre_priority_devops_over_engineer for priority order in tests/test_organize_files.py
- [x] T015 Verify `make test` FAIL (RED)
- [x] T016 Generate RED output: specs/058-refine-genre-classification/red-tests/ph2-test.md

### 実装 (GREEN)

- [x] T017 Read RED tests: specs/058-refine-genre-classification/red-tests/ph2-test.md
- [x] T018 [P] [US2] Add new genre keywords (ai, devops, health, parenting, travel, lifestyle) in conf/base/parameters.yml
- [x] T019 [P] [US1] Add genre_priority list in conf/base/parameters.yml
- [x] T020 [US1] Update classify_genre to use genre_priority from params in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T021 Verify `make test` PASS (GREEN)

### 検証

- [x] T022 Verify `make test` passes all tests (no regressions)
- [x] T023 Generate phase output: specs/058-refine-genre-classification/tasks/ph2-output.md

**Checkpoint**: 新ジャンル分類が動作し、優先順位が設定から読み込まれる

---

## Phase 3: US3 - 既存分類との後方互換性 (Priority: P2)

**Goal**: 既存4ジャンル（engineer, business, economy, daily）の分類が維持される

**Independent Test**: 既存キーワードを含むテストファイルが従来通りのジャンルに分類される

### 入力

- [ ] T024 Read previous phase output: specs/058-refine-genre-classification/tasks/ph2-output.md

### テスト実装 (RED)

- [ ] T025 [P] [US3] Implement test_classify_genre_engineer_unchanged for engineer keywords in tests/test_organize_files.py
- [ ] T026 [P] [US3] Implement test_classify_genre_business_unchanged for business keywords in tests/test_organize_files.py
- [ ] T027 [P] [US3] Implement test_classify_genre_economy_unchanged for economy keywords in tests/test_organize_files.py
- [ ] T028 [P] [US3] Implement test_classify_genre_daily_unchanged for daily keywords in tests/test_organize_files.py
- [ ] T029 Verify `make test` FAIL (RED) - 既存テストの期待値更新が必要な場合
- [ ] T030 Generate RED output: specs/058-refine-genre-classification/red-tests/ph3-test.md

### 実装 (GREEN)

- [ ] T031 Read RED tests: specs/058-refine-genre-classification/red-tests/ph3-test.md
- [ ] T032 [US3] Verify existing genre keywords are preserved in conf/base/parameters.yml
- [ ] T033 [US3] Update any existing tests that fail due to priority order changes in tests/test_organize_files.py
- [ ] T034 Verify `make test` PASS (GREEN)

### 検証

- [ ] T035 Verify `make test` passes all tests (including US1, US2 tests)
- [ ] T036 Generate phase output: specs/058-refine-genre-classification/tasks/ph3-output.md

**Checkpoint**: 既存4ジャンルの分類が維持され、全テストがパス

---

## Phase 4: FR-008 - ジャンル分布ログ出力 (TDD)

**Goal**: パイプライン完了時にジャンル分布（件数・割合）をログ出力

**Independent Test**: パイプライン実行後のログにジャンル分布が表示される

### 入力

- [ ] T037 Read previous phase output: specs/058-refine-genre-classification/tasks/ph3-output.md

### テスト実装 (RED)

- [ ] T038 [P] Implement test_log_genre_distribution for genre stats logging in tests/test_organize_files.py
- [ ] T039 Verify `make test` FAIL (RED)
- [ ] T040 Generate RED output: specs/058-refine-genre-classification/red-tests/ph4-test.md

### 実装 (GREEN)

- [ ] T041 Read RED tests: specs/058-refine-genre-classification/red-tests/ph4-test.md
- [ ] T042 Add log_genre_distribution function in src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T043 Integrate log_genre_distribution into classify_genre return flow in src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T044 Verify `make test` PASS (GREEN)

### 検証

- [ ] T045 Verify `make test` passes all tests
- [ ] T046 Generate phase output: specs/058-refine-genre-classification/tasks/ph4-output.md

**Checkpoint**: ログにジャンル分布が出力される

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: ドキュメント更新、最終検証

### 入力

- [ ] T047 Read previous phase output: specs/058-refine-genre-classification/tasks/ph4-output.md

### 実装

- [ ] T048 [P] Update CLAUDE.md ジャンル説明 section with new genres
- [ ] T049 [P] Run quickstart.md validation steps
- [ ] T050 Code cleanup and remove any debug statements

### 検証

- [ ] T051 Run `make test` to verify all tests pass after cleanup
- [ ] T052 Run `make lint` to verify code quality
- [ ] T053 Generate phase output: specs/058-refine-genre-classification/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - メインエージェント直接実行
- **Phase 2 (US1+US2)**: Depends on Phase 1 - tdd-generator → phase-executor
- **Phase 3 (US3)**: Depends on Phase 2 - tdd-generator → phase-executor
- **Phase 4 (FR-008)**: Depends on Phase 3 - tdd-generator → phase-executor
- **Phase 5 (Polish)**: Depends on Phase 4 - phase-executor のみ

### Within Each TDD Phase

1. **入力**: Read previous phase output
2. **テスト実装 (RED)**: Write tests → `make test` FAIL → generate RED output
3. **実装 (GREEN)**: Read RED tests → implement → `make test` PASS
4. **検証**: Confirm no regressions → generate phase output

### Agent Delegation

| Phase | Agent | Description |
|-------|-------|-------------|
| Phase 1 | メインエージェント | Setup (既存コード確認) |
| Phase 2 | tdd-generator → phase-executor | US1+US2 (新ジャンル追加) |
| Phase 3 | tdd-generator → phase-executor | US3 (後方互換性) |
| Phase 4 | tdd-generator → phase-executor | FR-008 (ログ出力) |
| Phase 5 | phase-executor | Polish (ドキュメント) |

### [P] マーク（依存関係なし）

- T001-T003: 異なるファイルの読み取りで相互依存なし
- T007-T014: 異なるテストメソッドの作成で相互依存なし
- T018-T019: 異なる設定セクションへの書き込みで相互依存なし
- T025-T028: 異なるテストメソッドの作成で相互依存なし
- T048-T050: 異なるファイルへの書き込みで相互依存なし

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/058-refine-genre-classification/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup)
│   ├── ph2-output.md           # Phase 2 output (US1+US2 GREEN)
│   ├── ph3-output.md           # Phase 3 output (US3 GREEN)
│   ├── ph4-output.md           # Phase 4 output (FR-008 GREEN)
│   └── ph5-output.md           # Phase 5 output (Polish)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED test results
    ├── ph3-test.md             # Phase 3 RED test results
    └── ph4-test.md             # Phase 4 RED test results
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (既存コード確認)
2. Complete Phase 2: US1+US2 (新ジャンル追加) - RED → GREEN → 検証
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. Manual verification: `kedro run` で新ジャンルフォルダ作成を確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. Each phase commits: `feat(phase-N): description`

---

## Test Coverage Rules

**チェックリスト**:
- [ ] 新ジャンル分類テスト（ai, devops, health, parenting, travel, lifestyle）
- [ ] 優先順位テスト（ai > engineer, devops > engineer）
- [ ] 既存ジャンル維持テスト（engineer, business, economy, daily）
- [ ] ログ出力テスト（ジャンル分布）

---

## Notes

- 新ジャンル6種: ai, devops, lifestyle, parenting, travel, health
- 優先順位: ai → devops → engineer → economy → business → health → parenting → travel → lifestyle → daily → other
- キーワードは日本語・英語両方を定義（research.md 参照）
- 既存 classify_genre 関数を拡張（新関数作成ではなく）
