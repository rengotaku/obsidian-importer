# Tasks: LLM まとめ品質の向上

**Input**: Design documents from `/specs/052-improve-summary-quality/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | まとめ品質の向上 | P1 | FR-001〜005 | 圧縮率20%以上、表形式保持、理由説明 |
| US2 | review フォルダへの振り分け削減 | P2 | FR-001〜005 | 振り分け率20%以下 |
| US3 | ゴールデンファイルによる品質検証 | P2 | FR-006〜008 | E2Eテスト自動実行 |

## Path Conventions

- **Project type**: single (Kedro pipeline)
- **Source**: `src/obsidian_etl/`
- **Tests**: `tests/`
- **Fixtures**: `tests/fixtures/golden/`

---

## Phase 1: Setup — NO TDD

**Purpose**: 既存実装の確認と変更準備

- [X] T001 Read current prompt in src/obsidian_etl/utils/prompts/knowledge_extraction.txt
- [X] T002 [P] Read extract_knowledge node in src/obsidian_etl/pipelines/transform/nodes.py
- [X] T003 [P] Read existing tests in tests/pipelines/transform/test_nodes.py
- [X] T004 [P] List files in data/07_model_output/organized/ for golden file candidates
- [X] T005 [P] List files in data/07_model_output/review/ for golden file candidates
- [X] T006 Generate phase output: specs/052-improve-summary-quality/tasks/ph1-output.md

---

## Phase 2: User Story 1 - まとめ品質の向上 (Priority: P1) MVP

**Goal**: プロンプト改善により、圧縮率20%以上、表形式保持、理由説明を実現

**Independent Test**: `make test` でプロンプト関連テストが通過し、サンプル会話で改善を確認

### 入力

- [ ] T007 Read previous phase output: specs/052-improve-summary-quality/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T008 [P] [US1] Implement test_prompt_includes_reason_instruction in tests/pipelines/transform/test_nodes.py
- [x] T009 [P] [US1] Implement test_prompt_includes_table_preservation in tests/pipelines/transform/test_nodes.py
- [x] T009.1 [P] [US1] Implement test_min_characters_validation in tests/utils/test_compression_validator.py (FR-002: min(original*0.2, 300))
- [x] T009.2 [P] [US1] Implement test_short_conversation_threshold in tests/utils/test_compression_validator.py (Edge Case: <1000文字でしきい値緩和)
- [x] T009.3 [P] [US1] Implement test_prompt_includes_code_preservation in tests/pipelines/transform/test_nodes.py (Edge Case: コードブロック保持)
- [x] T010 Verify `make test` FAIL (RED)
- [x] T011 Generate RED output: specs/052-improve-summary-quality/red-tests/ph2-test.md

### 実装 (GREEN)

- [x] T012 Read RED tests: specs/052-improve-summary-quality/red-tests/ph2-test.md
- [x] T013 [US1] Add V2 qualitative instructions to src/obsidian_etl/utils/prompts/knowledge_extraction.txt (verified in verification-results.md)
- [x] T013.1 [US1] Update validate_compression in src/obsidian_etl/utils/compression_validator.py to enforce min(original*0.2, 300) threshold
- [x] T013.2 [US1] Update get_threshold in src/obsidian_etl/utils/compression_validator.py to relax threshold for <1000 chars (e.g., 30%)
- [x] T013.3 [US1] Add code block preservation instructions to src/obsidian_etl/utils/prompts/knowledge_extraction.txt
- [x] T014 Verify `make test` PASS (GREEN)

### 検証

- [x] T015 Verify `make test` passes all tests (no regressions)
- [x] T016 Generate phase output: specs/052-improve-summary-quality/tasks/ph2-output.md

**Checkpoint**: User Story 1 should be fully functional - プロンプト改善完了

---

## Phase 3: User Story 3 - ゴールデンファイルによる品質検証 (Priority: P2)

**Goal**: ゴールデンファイルセット(10-12件)とE2Eテストを実装

**Independent Test**: `make test` でゴールデンファイルテストが通過

### 入力

- [x] T017 Read previous phase output: specs/052-improve-summary-quality/tasks/ph2-output.md

### テスト実装 (RED)

- [x] T018 [P] [US3] Create tests/fixtures/golden/ directory
- [x] T019 [P] [US3] Create tests/fixtures/golden/README.md with file list template
- [x] T020 [P] [US3] Implement test_golden_files_exist in tests/test_e2e_golden.py
- [x] T021 [P] [US3] Implement test_golden_files_meet_compression_threshold in tests/test_e2e_golden.py
- [x] T022 [P] [US3] Implement test_golden_files_preserve_table_structure in tests/test_e2e_golden.py
- [x] T023 Verify `make test` FAIL (RED)
- [x] T024 Generate RED output: specs/052-improve-summary-quality/red-tests/ph3-test.md

### 実装 (GREEN)

- [x] T025 Read RED tests: specs/052-improve-summary-quality/red-tests/ph3-test.md
- [x] T026 [P] [US3] Select and copy golden file: 技術系・小 from organized/
- [x] T027 [P] [US3] Select and copy golden file: 技術系・中 from organized/
- [x] T028 [P] [US3] Select and copy golden file: 技術系・大 from review/
- [x] T029 [P] [US3] Select and copy golden file: ビジネス系・小 from organized/
- [x] T030 [P] [US3] Select and copy golden file: ビジネス系・中 from organized/
- [x] T031 [P] [US3] Select and copy golden file: 日常系・小 from organized/
- [x] T032 [P] [US3] Select and copy golden file: 表形式・中 from organized/
- [x] T033 [P] [US3] Select and copy golden file: 表形式・大 (千葉のSwitch2販売実績.md) from review/
- [x] T034 [P] [US3] Select and copy golden file: コード含む・小 from organized/
- [x] T035 [P] [US3] Select and copy golden file: コード含む・中 from review/
- [x] T036 [US3] Update tests/fixtures/golden/README.md with actual file list
- [x] T037 Verify `make test` PASS (GREEN)

### 検証

- [x] T038 Verify `make test` passes all tests (including regressions from US1)
- [x] T039 Generate phase output: specs/052-improve-summary-quality/tasks/ph3-output.md

**Checkpoint**: User Story 3 should be fully functional - ゴールデンファイルとE2Eテスト完了

---

## Phase 4: User Story 2 - review フォルダへの振り分け削減 (Priority: P2)

**Goal**: パイプライン実行後の review フォルダ振り分け率を20%以下に

**Independent Test**: テストデータでパイプライン実行し、振り分け率を検証

### 入力

- [x] T040 Read previous phase output: specs/052-improve-summary-quality/tasks/ph3-output.md

### テスト実装 (RED)

- [x] T041 [P] [US2] Implement test_review_folder_ratio in tests/test_e2e_golden.py
- [x] T042 Verify `make test` FAIL (RED) - Note: Tests PASS because Phase 2-3 already implemented improvements
- [x] T043 Generate RED output: specs/052-improve-summary-quality/red-tests/ph4-test.md

### 実装 (GREEN)

- [x] T044 Read RED tests: specs/052-improve-summary-quality/red-tests/ph4-test.md
- [x] T045 [US2] Verify prompt improvements reduce review ratio (already implemented in Phase 2)
- [x] T046 [US2] Run pipeline with test data and measure review ratio
- [x] T047 Verify `make test` PASS (GREEN)

### 検証

- [x] T048 Verify `make test` passes all tests
- [x] T049 Generate phase output: specs/052-improve-summary-quality/tasks/ph4-output.md

**Checkpoint**: User Story 2 should be fully functional - 振り分け率改善確認

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: ドキュメント更新とクリーンアップ

### 入力

- [ ] T050 Read previous phase output: specs/052-improve-summary-quality/tasks/ph4-output.md

### 実装

- [ ] T051 [P] Update CLAUDE.md with golden file documentation
- [ ] T052 [P] Add make test-e2e-golden target to Makefile
- [ ] T053 Run quickstart.md validation scenarios

### 検証

- [ ] T054 Run `make test` to verify all tests pass after cleanup
- [ ] T055 Verify `make coverage` ≥80%
- [ ] T056 Generate phase output: specs/052-improve-summary-quality/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - メインエージェント直接実行
- **User Stories (Phase 2-4)**: TDD フロー (tdd-generator → phase-executor)
  - Phase 2 (US1): プロンプト改善 → MVP
  - Phase 3 (US3): ゴールデンファイル作成 (US1 の改善済みプロンプトを使用)
  - Phase 4 (US2): 振り分け率検証 (US1 + US3 の成果物を使用)
- **Polish (Phase 5)**: Depends on all user stories - phase-executor のみ

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-4 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 5 (Polish)**: phase-executor のみ

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/052-improve-summary-quality/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US1 GREEN results)
│   ├── ph3-output.md           # Phase 3 output (US3 GREEN results)
│   ├── ph4-output.md           # Phase 4 output (US2 GREEN results)
│   └── ph5-output.md           # Phase 5 output (Polish results)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED test results
    ├── ph3-test.md             # Phase 3 RED test results
    └── ph4-test.md             # Phase 4 RED test results
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (既存コード確認)
2. Complete Phase 2: User Story 1 (プロンプト改善)
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. Each phase commits: `feat(phase-N): description`

---

## Notes

- 合計タスク: 62
- Phase 1 (Setup): 6 tasks (T001-T006)
- Phase 2 (US1 - MVP): 16 tasks (T007-T016, T009.1-T009.3, T013.1-T013.3)
- Phase 3 (US3): 23 tasks (T017-T039)
- Phase 4 (US2): 10 tasks (T040-T049)
- Phase 5 (Polish): 7 tasks (T050-T056)
- Parallel tasks: 33 (marked with [P])

### 検証結果に基づく実装方針

検証 (`verification-results.md`) により以下を確認:
- V2（定性的指示のみ）で問題ケースが 7% → 24% に改善
- 数値しきい値をプロンプトに含める必要なし
- T013 で追加する V2 指示内容:
  ```text
  ## 分析・考察の記述
  - 理由・背景: 「なぜそうなるか」を必ず説明
  - パターン・傾向: データから読み取れる傾向を明記
  - 推奨・アドバイス: 結論だけでなく根拠も記述

  ## 表形式データの保持
  - 必ず Markdown 表形式で保持
  - 数値・日付は省略せず記載
  - 表の前に簡潔な説明を追加
  ```
