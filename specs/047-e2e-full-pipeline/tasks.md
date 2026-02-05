# Tasks: E2E Full Pipeline Validation

**Input**: Design documents from `/specs/047-e2e-full-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US4 | パイプライン変更: Vault 書き込み廃止 | P1 | FR-007,008,009,010 | Organize パイプラインのファイル I/O 廃止 |
| US1 | パイプライン最終出力のゴールデンファイル比較 | P1 | FR-001,003,004,005,006 | E2E テストでフルパイプライン検証 |
| US2 | 最終出力のゴールデンファイル生成・更新 | P1 | FR-002 | ゴールデンファイル再生成 |
| US3 | ゴールデンファイルの frontmatter 完全検証 | P2 | FR-003,004 | frontmatter フィールド検証 |

**Note**: US4 (パイプライン変更) は US1/US2 の前提となるため、最初に実装する。

## Path Conventions

- **Source**: `src/obsidian_etl/` - Kedro パイプライン実装
- **Tests**: `tests/` - ユニットテスト（unittest）
- **E2E**: `tests/e2e/` - E2E テスト（golden_comparator）
- **Fixtures**: `tests/fixtures/` - テストフィクスチャ

---

## Phase 1: Setup (Shared Infrastructure) — NO TDD

**Purpose**: 既存コードの理解と変更箇所の特定

- [x] T001 Read current organize pipeline in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T002 [P] Read current organize pipeline registration in src/obsidian_etl/pipelines/organize/pipeline.py
- [x] T003 [P] Read existing organize tests in tests/pipelines/organize/test_nodes.py
- [x] T004 [P] Read golden_comparator in tests/e2e/golden_comparator.py
- [x] T005 [P] Read existing E2E tests in tests/e2e/test_golden_comparator.py
- [x] T006 [P] Read current golden files in tests/fixtures/golden/
- [x] T007 [P] Read Makefile E2E targets (test-e2e, test-e2e-update-golden)
- [x] T008 [P] Read DataCatalog config in conf/base/catalog.yml
- [x] T009 Generate phase output: specs/047-e2e-full-pipeline/tasks/ph1-output.md

---

## Phase 2: User Story 4 - パイプライン変更: Vault 書き込み廃止 (Priority: P1) MVP

**Goal**: Organize パイプラインから Vault へのファイル書き込みを廃止し、振り分け情報を frontmatter に埋め込む

**Independent Test**: `kedro run` 実行後、`Vaults/` にファイルが作成されない & frontmatter に `genre`, `topic` が含まれる

### 入力

- [x] T010 Read previous phase output: specs/047-e2e-full-pipeline/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T011 [P] [US4] Implement test_extract_topic_normalizes_to_lowercase in tests/pipelines/organize/test_nodes.py
- [x] T012 [P] [US4] Implement test_extract_topic_preserves_spaces in tests/pipelines/organize/test_nodes.py
- [x] T013 [P] [US4] Implement test_extract_topic_empty_on_failure in tests/pipelines/organize/test_nodes.py
- [x] T014 [P] [US4] Implement test_embed_frontmatter_fields_adds_genre in tests/pipelines/organize/test_nodes.py
- [x] T015 [P] [US4] Implement test_embed_frontmatter_fields_adds_topic in tests/pipelines/organize/test_nodes.py
- [x] T016 [P] [US4] Implement test_embed_frontmatter_fields_adds_empty_topic in tests/pipelines/organize/test_nodes.py
- [x] T017 [P] [US4] Implement test_embed_frontmatter_fields_adds_summary in tests/pipelines/organize/test_nodes.py
- [x] T018 [P] [US4] Implement test_embed_frontmatter_fields_no_file_write in tests/pipelines/organize/test_nodes.py
- [x] T019 Verify `make test` FAIL (RED) for new tests
- [x] T020 Generate RED output: specs/047-e2e-full-pipeline/red-tests/ph2-test.md

### 実装 (GREEN)

- [x] T021 Read RED tests: specs/047-e2e-full-pipeline/red-tests/ph2-test.md
- [x] T022 [P] [US4] Implement extract_topic node in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T023 [P] [US4] Implement _extract_topic_via_llm helper in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T024 [P] [US4] Implement embed_frontmatter_fields node in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T025 [P] [US4] Implement _embed_fields_in_frontmatter helper in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T026 [US4] Update create_pipeline with extract_topic and embed_frontmatter_fields in src/obsidian_etl/pipelines/organize/pipeline.py
- [x] T027 [US4] Remove determine_vault_path and move_to_vault from pipeline in src/obsidian_etl/pipelines/organize/pipeline.py
- [x] T028 [P] [US4] Add topic_extracted_items dataset in conf/base/catalog.yml
- [x] T029 [P] [US4] Update organized_notes dataset in conf/base/catalog.yml
- [x] T030 Verify `make test` PASS (GREEN)

### 検証

- [x] T031 Verify `make test` passes all tests (no regressions)
- [x] T032 Verify `kedro run` does not create files in `Vaults/` directory
- [x] T033 Generate phase output: specs/047-e2e-full-pipeline/tasks/ph2-output.md

**Checkpoint**: extract_topic と embed_frontmatter_fields ノードが動作し、Vault 書き込みが廃止される

---

## Phase 3: User Story 1 - パイプライン最終出力のゴールデンファイル比較 (Priority: P1)

**Goal**: `make test-e2e` がフルパイプライン（Organize 含む）の最終出力を検証する

**Independent Test**: `make test-e2e` 実行後、ゴールデンファイル自己比較で 100% の類似度が返る

### 入力

- [x] T034 Read previous phase output: specs/047-e2e-full-pipeline/tasks/ph2-output.md

### テスト実装 (RED)

- [x] T035 [P] [US1] Update SAMPLE_GOLDEN with genre, topic fields in tests/e2e/test_golden_comparator.py
- [x] T036 [P] [US1] Add test_frontmatter_similarity_with_genre_topic in tests/e2e/test_golden_comparator.py
- [x] T037 [P] [US1] Add test_frontmatter_similarity_with_empty_topic in tests/e2e/test_golden_comparator.py
- [x] T038 Verify `make test` FAIL (RED) for updated tests — RED 省略: golden_comparator は動的 key チェックのため PASS
- [x] T039 Generate RED output: specs/047-e2e-full-pipeline/red-tests/ph3-test.md

### 実装 (GREEN)

- [ ] T040 Read RED tests: specs/047-e2e-full-pipeline/red-tests/ph3-test.md
- [ ] T041 [US1] Update test-e2e target to remove --to-nodes=format_markdown in Makefile
- [ ] T042 [US1] Update test-e2e target to use data/07_model_output/organized as actual output in Makefile
- [ ] T043 Verify `make test` PASS (GREEN)

### 検証

- [ ] T044 Verify `make test` passes all tests (including regressions)
- [ ] T045 Generate phase output: specs/047-e2e-full-pipeline/tasks/ph3-output.md

**Checkpoint**: test-e2e ターゲットがフルパイプラインを検証する設定になる

---

## Phase 4: User Story 2 - 最終出力のゴールデンファイル生成・更新 (Priority: P1)

**Goal**: `make test-e2e-update-golden` がフルパイプライン後の最終出力をゴールデンファイルとして保存する

**Independent Test**: `make test-e2e-update-golden` 実行後、ゴールデンファイルに `genre`, `topic`, `summary` が含まれる

### 入力

- [ ] T046 Read previous phase output: specs/047-e2e-full-pipeline/tasks/ph3-output.md

### 実装 (NO TDD - Makefile 更新のみ)

- [ ] T047 [US2] Update test-e2e-update-golden target to remove --to-nodes=format_markdown in Makefile
- [ ] T048 [US2] Update test-e2e-update-golden target to copy from data/07_model_output/organized in Makefile
- [ ] T049 [US2] Run make test-e2e-update-golden to regenerate golden files
- [ ] T050 [US2] Verify regenerated golden files contain genre, topic, summary in frontmatter

### 検証

- [ ] T051 Run `make test-e2e` to verify self-comparison returns 100% similarity
- [ ] T052 Generate phase output: specs/047-e2e-full-pipeline/tasks/ph4-output.md

**Checkpoint**: ゴールデンファイルがフルパイプライン出力を反映

---

## Phase 5: User Story 3 - ゴールデンファイルの frontmatter 完全検証 (Priority: P2)

**Goal**: golden_comparator が Organize 後の frontmatter フィールドを正しく比較する

**Independent Test**: frontmatter に新しいフィールド（genre, topic）が追加されても正しく類似度計算される

### 入力

- [ ] T053 Read previous phase output: specs/047-e2e-full-pipeline/tasks/ph4-output.md

### テスト実装 (RED)

- [ ] T054 [P] [US3] Add test_calculate_frontmatter_similarity_missing_genre in tests/e2e/test_golden_comparator.py
- [ ] T055 [P] [US3] Add test_calculate_frontmatter_similarity_missing_topic in tests/e2e/test_golden_comparator.py
- [ ] T056 [P] [US3] Add test_similarity_with_summary_mismatch in tests/e2e/test_golden_comparator.py
- [ ] T057 Verify `make test` FAIL (RED) for new tests
- [ ] T058 Generate RED output: specs/047-e2e-full-pipeline/red-tests/ph5-test.md

### 実装 (GREEN)

- [ ] T059 Read RED tests: specs/047-e2e-full-pipeline/red-tests/ph5-test.md
- [ ] T060 [US3] Verify golden_comparator correctly handles genre, topic fields (may need no code changes if dynamic)
- [ ] T061 Verify `make test` PASS (GREEN)

### 検証

- [ ] T062 Verify `make test` passes all tests
- [ ] T063 Generate phase output: specs/047-e2e-full-pipeline/tasks/ph5-output.md

**Checkpoint**: frontmatter の新フィールドが正しく比較される

---

## Phase 6: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: 不要コードの削除、ドキュメント更新、最終検証

### 入力

- [ ] T064 Read previous phase output: specs/047-e2e-full-pipeline/tasks/ph5-output.md

### 実装

- [ ] T065 [P] Remove determine_vault_path function from src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T066 [P] Remove move_to_vault function from src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T067 [P] Remove related imports from src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T068 [P] Remove obsolete tests (test_determine_vault_path_*, test_move_to_vault_*) from tests/pipelines/organize/test_nodes.py
- [ ] T069 [P] Remove vault_determined_items dataset from conf/base/catalog.yml if exists
- [ ] T070 Run quickstart.md validation (Success Criteria Checklist)

### 検証

- [ ] T071 Run `make test` to verify all tests pass after cleanup
- [ ] T072 Run `make test-e2e` to verify E2E tests pass
- [ ] T073 Verify `Vaults/` directory unchanged after `kedro run`
- [ ] T074 Generate phase output: specs/047-e2e-full-pipeline/tasks/ph6-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - メインエージェント直接実行
- **User Story 4 (Phase 2)**: Depends on Phase 1 - TDD フロー (tdd-generator → phase-executor)
- **User Story 1 (Phase 3)**: Depends on Phase 2 - TDD フロー
- **User Story 2 (Phase 4)**: Depends on Phase 3 - phase-executor のみ
- **User Story 3 (Phase 5)**: Depends on Phase 4 - TDD フロー
- **Polish (Phase 6)**: Depends on Phase 5 - phase-executor のみ

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

- Setup タスクの [P]: 異なるファイルの読み込みで相互依存なし
- RED テストの [P]: 異なるテストメソッドへの追加で相互依存なし
- GREEN 実装の [P]: 異なる関数/ノードの実装で相互依存なし

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/047-e2e-full-pipeline/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US4 GREEN results)
│   ├── ph3-output.md           # Phase 3 output (US1 GREEN results)
│   ├── ph4-output.md           # Phase 4 output (US2 GREEN results)
│   ├── ph5-output.md           # Phase 5 output (US3 GREEN results)
│   └── ph6-output.md           # Phase 6 output (Polish results)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED test results (US4)
    ├── ph3-test.md             # Phase 3 RED test results (US1)
    └── ph5-test.md             # Phase 5 RED test results (US3)
```

### Phase Output Content

Each `phN-output.md` should contain:
- Summary of what was done
- Files created/modified
- Test results (`make test` output)
- Any decisions or deviations from the plan

### RED Test Output Content

Each `phN-test.md` should contain:
- Test code written
- `make test` output showing FAIL (RED confirmation)
- Number of failing tests and their names

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (existing code review)
2. Complete Phase 2: User Story 4 - パイプライン変更 (RED → GREEN → 検証)
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. `kedro run` で Vault 書き込みがないことを確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
2. Each phase commits: `feat(phase-N): description`

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[classified_items] → [extract_topic] → [normalize_frontmatter] → [clean_content] → [embed_frontmatter_fields] → [organized_notes]
      ↓                    ↓                    ↓                     ↓                      ↓
    テスト               テスト                テスト                テスト                 テスト
```

**チェックリスト**:
- [ ] extract_topic の正規化テスト（小文字化、スペース保持、空許容）
- [ ] embed_frontmatter_fields のフィールド追加テスト（genre, topic, summary）
- [ ] embed_frontmatter_fields のファイル I/O なしテスト
- [ ] golden_comparator の拡張フィールド対応テスト

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- US4 は US1/US2/US3 の前提となるため最初に実装
- TDD: テスト実装 (RED) → FAIL 確認 → 実装 (GREEN) → PASS 確認
- RED output must be generated BEFORE implementation begins
- Commit after each phase completion
- Backward compatibility: 既存テストが PASS し続けることを確認
