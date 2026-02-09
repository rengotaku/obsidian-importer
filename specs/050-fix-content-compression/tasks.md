# Tasks: 出力コンテンツの圧縮率改善

**Input**: Design documents from `/specs/050-fix-content-compression/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | 適切な情報量の保持 | P1 | FR-001,002,003,004 | プロンプト改善でコード・手順を保持 |
| US2 | 圧縮率の品質基準達成 | P1 | FR-005,006,007 | 圧縮率検証 + レビューフォルダ出力 |
| US3 | コード保持の保証 | P2 | FR-002 | US1 のプロンプト改善で対応済み |

## Path Conventions

- **Single project**: `src/obsidian_etl/`, `tests/` at repository root
- Paths shown below assume single project structure

---

## Phase 1: Setup — NO TDD

**Purpose**: Feature ブランチ確認、既存コード確認、テスト通過確認

- [X] T001 Verify current branch is `050-fix-content-compression`
- [X] T002 [P] Read current prompt: src/obsidian_etl/utils/prompts/knowledge_extraction.txt
- [X] T003 [P] Read transform nodes: src/obsidian_etl/pipelines/transform/nodes.py
- [X] T004 [P] Read organize nodes: src/obsidian_etl/pipelines/organize/nodes.py
- [X] T005 [P] Read existing tests: tests/pipelines/transform/test_nodes.py
- [X] T006 Run `make test` to verify all existing tests pass
- [X] T007 Generate phase output: specs/050-fix-content-compression/tasks/ph1-output.md

---

## Phase 2: User Story 1 - 適切な情報量の保持 (Priority: P1) MVP

**Goal**: プロンプトに情報量目安・省略禁止ルールを追加し、LLM の過度な圧縮を防止

**Independent Test**: プロンプトファイルの内容を確認し、必要なセクションが追加されていることを検証

### 入力

- [X] T008 Read previous phase output: specs/050-fix-content-compression/tasks/ph1-output.md

### 実装 (NO TDD - プロンプトファイル変更のみ)

- [X] T009 [US1] Add "情報量の目安" section to src/obsidian_etl/utils/prompts/knowledge_extraction.txt
- [X] T010 [US1] Add "省略禁止" section to src/obsidian_etl/utils/prompts/knowledge_extraction.txt

### 検証

- [X] T011 Verify prompt file contains new sections
- [X] T012 Run `make test` to verify no regressions
- [X] T013 Generate phase output: specs/050-fix-content-compression/tasks/ph2-output.md

**Checkpoint**: プロンプト改善完了、US1 の基盤が整う

---

## Phase 3: User Story 2 - 圧縮率検証共通処理 (Priority: P1)

**Goal**: 圧縮率検証ユーティリティを作成し、全 transform node で共通利用可能にする

**Independent Test**: `compression_validator.py` の単体テストで検証

### 入力

- [X] T014 Read previous phase output: specs/050-fix-content-compression/tasks/ph2-output.md

### テスト実装 (RED)

- [X] T015 [P] [US2] Create test file: tests/utils/test_compression_validator.py
- [X] T016 [P] [US2] Implement test_get_threshold_large in tests/utils/test_compression_validator.py
- [X] T017 [P] [US2] Implement test_get_threshold_medium in tests/utils/test_compression_validator.py
- [X] T018 [P] [US2] Implement test_get_threshold_small in tests/utils/test_compression_validator.py
- [X] T019 [P] [US2] Implement test_validate_compression_valid in tests/utils/test_compression_validator.py
- [X] T020 [P] [US2] Implement test_validate_compression_invalid in tests/utils/test_compression_validator.py
- [X] T021 [P] [US2] Implement test_validate_compression_zero_original in tests/utils/test_compression_validator.py
- [X] T022 Verify `make test` FAIL (RED)
- [X] T023 Generate RED output: specs/050-fix-content-compression/red-tests/ph3-test.md

### 実装 (GREEN)

- [X] T024 Read RED tests: specs/050-fix-content-compression/red-tests/ph3-test.md
- [X] T025 [US2] Create src/obsidian_etl/utils/compression_validator.py with CompressionResult dataclass
- [X] T026 [US2] Implement get_threshold() in src/obsidian_etl/utils/compression_validator.py
- [X] T027 [US2] Implement validate_compression() in src/obsidian_etl/utils/compression_validator.py
- [X] T028 Verify `make test` PASS (GREEN)

### 検証

- [X] T029 Verify `make test` passes all tests (no regressions)
- [X] T030 Generate phase output: specs/050-fix-content-compression/tasks/ph3-output.md

**Checkpoint**: 圧縮率検証ユーティリティが独立して動作

---

## Phase 4: User Story 2 - extract_knowledge 修正 (Priority: P1)

**Goal**: extract_knowledge node に圧縮率検証を組み込み、基準未達アイテムに review_reason を付与

**Independent Test**: 圧縮率が低いアイテムに review_reason が付与されることを検証

### 入力

- [x] T031 Read previous phase output: specs/050-fix-content-compression/tasks/ph3-output.md

### テスト実装 (RED)

- [x] T032 [P] [US2] Add test_extract_knowledge_adds_review_reason in tests/pipelines/transform/test_nodes.py
- [x] T033 [P] [US2] Add test_extract_knowledge_no_review_reason_when_valid in tests/pipelines/transform/test_nodes.py
- [x] T034 Verify `make test` FAIL (RED)
- [x] T035 Generate RED output: specs/050-fix-content-compression/red-tests/ph4-test.md

### 実装 (GREEN)

- [x] T036 Read RED tests: specs/050-fix-content-compression/red-tests/ph4-test.md
- [x] T037 [US2] Import compression_validator in src/obsidian_etl/pipelines/transform/nodes.py
- [x] T038 [US2] Replace existing ratio check with validate_compression() in extract_knowledge
- [x] T039 [US2] Add review_reason to item when is_valid=False (format: "node_name: body_ratio=X% < threshold=Y%")
- [x] T040 [US2] Remove skipped_empty continue for compression failures (process continues)
- [x] T041 Verify `make test` PASS (GREEN)

### 検証

- [x] T042 Verify `make test` passes all tests (no regressions)
- [x] T043 Generate phase output: specs/050-fix-content-compression/tasks/ph4-output.md

**Checkpoint**: extract_knowledge が圧縮率を検証し、review_reason を付与

---

## Phase 5: User Story 2 - レビューフォルダ出力 (Priority: P1)

**Goal**: 基準未達ファイルを review/ フォルダに出力し、frontmatter に review_reason を埋め込む

**Independent Test**: review_reason があるアイテムが review/ に出力されることを検証

### 入力

- [x] T044 Read previous phase output: specs/050-fix-content-compression/tasks/ph4-output.md

### テスト実装 (RED)

- [x] T045 [P] [US2] Add test_format_markdown_review_output in tests/pipelines/transform/test_nodes.py
- [x] T046 [P] [US2] Add test_embed_frontmatter_with_review_reason in tests/pipelines/organize/test_nodes.py
- [x] T047 Verify `make test` FAIL (RED)
- [x] T048 Generate RED output: specs/050-fix-content-compression/red-tests/ph5-test.md

### 実装 (GREEN)

- [x] T049 Read RED tests: specs/050-fix-content-compression/red-tests/ph5-test.md
- [x] T050 [P] [US2] Add review_notes dataset to conf/base/catalog.yml
- [x] T051 [US2] Modify format_markdown to return tuple (normal, review) in src/obsidian_etl/pipelines/transform/nodes.py
- [x] T052 [US2] Update transform pipeline to handle dual output in src/obsidian_etl/pipelines/transform/pipeline.py
- [x] T053 [US2] Modify embed_frontmatter_fields to include review_reason in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T054 Verify `make test` PASS (GREEN)

### 検証

- [x] T055 Verify `make test` passes all tests (no regressions)
- [x] T056 Verify review/ directory structure in data/07_model_output/
- [x] T057 Generate phase output: specs/050-fix-content-compression/tasks/ph5-output.md

**Checkpoint**: レビューフォルダ出力が機能し、frontmatter に review_reason が含まれる

---

## Phase 6: E2E 検証 — NO TDD

**Purpose**: 実際のパイプライン実行で圧縮率改善を検証

### 入力

- [ ] T058 Read previous phase output: specs/050-fix-content-compression/tasks/ph5-output.md

### 実装

- [ ] T059 Run kedro pipeline with test data: `kedro run --pipeline=import_claude --params='{"import.limit": 10}'`
- [ ] T060 Calculate compression ratio for output files
- [ ] T061 Verify review/ folder contains expected files (if any)
- [ ] T062 Verify review files have review_reason in frontmatter

### 検証

- [ ] T063 Verify `make test` passes all tests
- [ ] T064 Verify Body% improvement (target: average >50%)
- [ ] T065 Generate phase output: specs/050-fix-content-compression/tasks/ph6-output.md

**Checkpoint**: E2E で圧縮率改善を確認

---

## Phase 7: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: ドキュメント更新、コードレビュー、最終確認

### 入力

- [ ] T066 Read previous phase output: specs/050-fix-content-compression/tasks/ph6-output.md

### 実装

- [ ] T067 [P] Update CLAUDE.md with new feature documentation
- [ ] T068 [P] Remove any debug code or TODO comments
- [ ] T069 Run code review using code-reviewer agent

### 検証

- [ ] T070 Run `make test` to verify all tests pass after cleanup
- [ ] T071 Run `make lint` to verify code quality
- [ ] T072 Generate phase output: specs/050-fix-content-compression/tasks/ph7-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - メインエージェント直接実行
- **Phase 2 (US1 プロンプト改善)**: Depends on Phase 1 - メインエージェント直接実行 (NO TDD)
- **Phase 3 (US2 圧縮率検証)**: Depends on Phase 2 - TDD フロー (tdd-generator → phase-executor)
- **Phase 4 (US2 extract_knowledge)**: Depends on Phase 3 - TDD フロー
- **Phase 5 (US2 レビューフォルダ)**: Depends on Phase 4 - TDD フロー
- **Phase 6 (E2E)**: Depends on Phase 5 - phase-executor のみ
- **Phase 7 (Polish)**: Depends on Phase 6 - phase-executor のみ

### Within Each TDD Phase

1. **入力**: Read previous phase output (context from prior work)
2. **テスト実装 (RED)**: Write tests FIRST → verify `make test` FAIL → generate RED output
3. **実装 (GREEN)**: Read RED tests → implement → verify `make test` PASS
4. **検証**: Confirm no regressions → generate phase output

### Agent Delegation

- **Phase 1-2**: メインエージェント直接実行
- **Phase 3-5**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 6-7**: phase-executor のみ

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/050-fix-content-compression/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US1 プロンプト改善)
│   ├── ph3-output.md           # Phase 3 output (US2 圧縮率検証)
│   ├── ph4-output.md           # Phase 4 output (US2 extract_knowledge)
│   ├── ph5-output.md           # Phase 5 output (US2 レビューフォルダ)
│   ├── ph6-output.md           # Phase 6 output (E2E)
│   └── ph7-output.md           # Phase 7 output (Polish)
└── red-tests/
    ├── ph3-test.md             # Phase 3 RED test results
    ├── ph4-test.md             # Phase 4 RED test results
    └── ph5-test.md             # Phase 5 RED test results
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (既存コード確認)
2. Complete Phase 2: User Story 1 (プロンプト改善)
3. **STOP and VALIDATE**: プロンプト変更のみで LLM 出力を手動確認

### Full Delivery

1. Phase 1 → 2 → 3 → 4 → 5 → 6 → 7
2. Each phase commits: `feat(phase-N): description`

---

## Notes

- US3 (コード保持の保証) は US1 のプロンプト改善でカバーされるため、独立した Phase なし
- 圧縮率検証は既存の `extract_knowledge` のロジックを置き換え（新規追加ではなく修正）
- review/ フォルダは `data/07_model_output/review/` に作成
- 手動復帰処理はスコープ外（ユーザーが `organized/` へ移動）
