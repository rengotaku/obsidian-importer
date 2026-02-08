# Tasks: 出力ファイル品質改善

**Input**: Design documents from `/specs/049-output-quality-improve/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenarios |
|----|-------|----------|----|-----------|
| US1 | 空コンテンツファイルの除外 | P1 | FR-001, FR-002 | 3 |
| US2 | タイトルサニタイズ | P1 | FR-003, FR-004, FR-005, FR-006 | 4 |
| US3 | プレースホルダータイトルの防止 | P2 | FR-007 | 2 |
| US4 | トピック粒度の適正化 | P2 | FR-008 | 2 |
| US5 | summary/content 逆転の検出 | P3 | FR-009 | 2 |

## Path Conventions

- **Source**: `src/obsidian_etl/` (Kedro パイプライン)
- **Tests**: `tests/pipelines/` (unittest)
- **Prompts**: `src/obsidian_etl/utils/prompts/`
- **Specs**: `specs/049-output-quality-improve/`

---

## Phase 1: Setup — NO TDD

**Purpose**: Existing code review, test baseline confirmation

- [X] T001 Read current implementation in src/obsidian_etl/pipelines/transform/nodes.py
- [X] T002 [P] Read current implementation in src/obsidian_etl/pipelines/organize/nodes.py
- [X] T003 [P] Read existing tests in tests/pipelines/transform/test_nodes.py
- [X] T004 [P] Read existing tests in tests/pipelines/organize/test_nodes.py
- [X] T005 [P] Read prompt template in src/obsidian_etl/utils/prompts/knowledge_extraction.txt
- [X] T006 Run `make test` to confirm baseline passes
- [X] T007 Generate phase output: specs/049-output-quality-improve/tasks/ph1-output.md

---

## Phase 2: User Story 1 - 空コンテンツファイルの除外 (Priority: P1) MVP

**Goal**: LLM が summary_content を空で返した場合、そのアイテムを出力から除外する

**Independent Test**: `kedro run` 実行後、`data/07_model_output/organized/` に本文が空のファイルが存在しないことを確認

### 入力

- [x] T008 Read previous phase output: specs/049-output-quality-improve/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T009 [P] [US1] Add test_extract_knowledge_skips_empty_content in tests/pipelines/transform/test_nodes.py
- [x] T010 [P] [US1] Add test_extract_knowledge_skips_whitespace_only_content in tests/pipelines/transform/test_nodes.py
- [x] T011 [P] [US1] Add test_extract_knowledge_logs_skip_count in tests/pipelines/transform/test_nodes.py
- [x] T012 Verify `make test` FAIL (RED)
- [x] T013 Generate RED output: specs/049-output-quality-improve/red-tests/ph2-test.md

### 実装 (GREEN)

- [X] T014 Read RED tests: specs/049-output-quality-improve/red-tests/ph2-test.md
- [X] T015 [US1] Add empty content check in extract_knowledge function at src/obsidian_etl/pipelines/transform/nodes.py:113-116
- [X] T016 [US1] Add skipped_empty counter and log message in extract_knowledge
- [X] T017 [US1] Update summary log to include skipped_empty count
- [X] T018 Verify `make test` PASS (GREEN)

### 検証

- [ ] T019 Verify `make test` passes all tests (no regressions)
- [ ] T020 Generate phase output: specs/049-output-quality-improve/tasks/ph2-output.md

**Checkpoint**: User Story 1 should be fully functional - empty content items are excluded

---

## Phase 3: User Story 2 - タイトルサニタイズ (Priority: P1)

**Goal**: タイトルから絵文字、ブラケット、ファイルパス記号を除去する

**Independent Test**: 出力ファイル名に絵文字、`[]`, `()`, `~`, `%` が含まれないことを確認

### 入力

- [x] T021 Read previous phase output: specs/049-output-quality-improve/tasks/ph2-output.md

### テスト実装 (RED)

- [x] T022 [P] [US2] Add test_sanitize_filename_removes_emoji in tests/pipelines/transform/test_nodes.py
- [x] T023 [P] [US2] Add test_sanitize_filename_removes_brackets in tests/pipelines/transform/test_nodes.py
- [x] T024 [P] [US2] Add test_sanitize_filename_removes_tilde_percent in tests/pipelines/transform/test_nodes.py
- [x] T025 [P] [US2] Add test_sanitize_filename_fallback_to_file_id in tests/pipelines/transform/test_nodes.py
- [x] T026 Verify `make test` FAIL (RED)
- [x] T027 Generate RED output: specs/049-output-quality-improve/red-tests/ph3-test.md

### 実装 (GREEN)

- [X] T028 Read RED tests: specs/049-output-quality-improve/red-tests/ph3-test.md
- [X] T029 [US2] Add EMOJI_PATTERN constant at module level in src/obsidian_etl/pipelines/transform/nodes.py
- [X] T030 [US2] Extend _sanitize_filename to remove emojis using EMOJI_PATTERN
- [X] T031 [US2] Extend _sanitize_filename unsafe_chars to include []()~%
- [X] T032 Verify `make test` PASS (GREEN)

### 検証

- [ ] T033 Verify `make test` passes all tests (including US1)
- [ ] T034 Generate phase output: specs/049-output-quality-improve/tasks/ph3-output.md

**Checkpoint**: User Stories 1 AND 2 should both work - empty content excluded AND titles sanitized

---

## Phase 4: User Story 3 - プレースホルダータイトルの防止 (Priority: P2)

**Goal**: LLM がプロンプト例文のプレースホルダーをタイトルとして採用しないようにする

**Independent Test**: 既知の問題会話を再処理し、プレースホルダータイトルが生成されないことを確認

### 入力

- [x] T035 Read previous phase output: specs/049-output-quality-improve/tasks/ph3-output.md

### 実装（プロンプト改善のみ、TDD 対象外）

- [x] T036 [US3] Add placeholder prohibition rules to src/obsidian_etl/utils/prompts/knowledge_extraction.txt
- [x] T037 [US3] Add specific examples of prohibited placeholders: (省略), [トピック名], ...

### 検証

- [x] T038 Verify `make test` passes all tests (no regressions from prompt change)
- [x] T039 Generate phase output: specs/049-output-quality-improve/tasks/ph4-output.md

**Checkpoint**: プロンプトが改善され、プレースホルダーが禁止された

---

## Phase 5: User Story 4 - トピック粒度の適正化 (Priority: P2)

**Goal**: トピック抽出が適切な抽象度（カテゴリレベル）で行われるようにする

**Independent Test**: 離乳食関連の会話を処理し、トピックが `離乳食` レベルの抽象度で分類される

### 入力

- [X] T040 Read previous phase output: specs/049-output-quality-improve/tasks/ph4-output.md

### 実装（プロンプト改善のみ、TDD 対象外）

- [X] T041 [US4] Update _extract_topic_via_llm prompt in src/obsidian_etl/pipelines/organize/nodes.py:238-244
- [X] T042 [US4] Add abstraction level instructions with examples (バナナプリン → 離乳食)

### 検証

- [X] T043 Verify `make test` passes all tests (no regressions)
- [X] T044 Generate phase output: specs/049-output-quality-improve/tasks/ph5-output.md

**Checkpoint**: トピック抽出プロンプトが改善され、カテゴリレベルで抽出される

---

## Phase 6: User Story 5 - summary/content 逆転の検出 (Priority: P3)

**Goal**: summary が 500 文字を超える場合に警告ログを出力する

**Independent Test**: summary が 500 文字を超えるアイテムに対して警告ログが出力される

### 入力

- [x] T045 Read previous phase output: specs/049-output-quality-improve/tasks/ph5-output.md

### テスト実装 (RED)

- [x] T046 [P] [US5] Add test_extract_knowledge_warns_long_summary in tests/pipelines/transform/test_nodes.py
- [x] T047 [P] [US5] Add test_extract_knowledge_no_warning_for_short_summary in tests/pipelines/transform/test_nodes.py
- [x] T048 Verify `make test` FAIL (RED)
- [x] T049 Generate RED output: specs/049-output-quality-improve/red-tests/ph6-test.md

### 実装 (GREEN)

- [X] T050 Read RED tests: specs/049-output-quality-improve/red-tests/ph6-test.md
- [X] T051 [US5] Add summary length check after LLM extraction in src/obsidian_etl/pipelines/transform/nodes.py
- [X] T052 [US5] Add warning log when summary exceeds 500 characters
- [X] T053 Verify `make test` PASS (GREEN)

### 検証

- [ ] T054 Verify `make test` passes all tests (all US complete)
- [ ] T055 Generate phase output: specs/049-output-quality-improve/tasks/ph6-output.md

**Checkpoint**: 全 User Stories (US1-US5) が実装完了

---

## Phase 7: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: E2E テスト、ゴールデンファイル更新、最終検証

### 入力

- [X] T056 Read previous phase output: specs/049-output-quality-improve/tasks/ph6-output.md

### 実装

- [X] T057 Run E2E test with `make test-e2e`
- [X] T058 Update golden files if needed with `make test-e2e-update-golden`
- [X] T059 Verify backward compatibility (FR-010) - no existing functionality broken

### 検証

- [X] T060 Run `make test` to verify all tests pass
- [X] T061 Run `make coverage` to verify coverage ≥80%
- [X] T062 Generate phase output: specs/049-output-quality-improve/tasks/ph7-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - メインエージェント直接実行
- **US1 (Phase 2)**: TDD フロー (tdd-generator → phase-executor)
- **US2 (Phase 3)**: Depends on Phase 2 output - TDD フロー
- **US3 (Phase 4)**: Depends on Phase 3 output - phase-executor のみ（プロンプト改善）
- **US4 (Phase 5)**: Depends on Phase 4 output - phase-executor のみ（プロンプト改善）
- **US5 (Phase 6)**: Depends on Phase 5 output - TDD フロー
- **Polish (Phase 7)**: Depends on all user stories - phase-executor のみ

### Agent Delegation

| Phase | Agent | 内容 |
|-------|-------|------|
| Phase 1 | メインエージェント | Setup（既存コード確認） |
| Phase 2 | tdd-generator → phase-executor | US1 (TDD) |
| Phase 3 | tdd-generator → phase-executor | US2 (TDD) |
| Phase 4 | phase-executor | US3 (プロンプト改善のみ) |
| Phase 5 | phase-executor | US4 (プロンプト改善のみ) |
| Phase 6 | tdd-generator → phase-executor | US5 (TDD) |
| Phase 7 | phase-executor | Polish |

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。

- Setup タスクの [P]: 異なるファイルの読み込みで相互依存なし
- RED テストの [P]: 異なるテストメソッドへの追加で相互依存なし
- GREEN 実装の [P]: 同一ファイルでも独立した機能追加で相互依存なし

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/049-output-quality-improve/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US1 GREEN results)
│   ├── ph3-output.md           # Phase 3 output (US2 GREEN results)
│   ├── ph4-output.md           # Phase 4 output (US3 results)
│   ├── ph5-output.md           # Phase 5 output (US4 results)
│   ├── ph6-output.md           # Phase 6 output (US5 GREEN results)
│   └── ph7-output.md           # Phase 7 output (Final)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED test results (US1)
    ├── ph3-test.md             # Phase 3 RED test results (US2)
    └── ph6-test.md             # Phase 6 RED test results (US5)
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (既存コード確認)
2. Complete Phase 2: User Story 1 (空コンテンツ除外)
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. MVP 完了 - 最も重要な品質問題が解決

### Full Delivery

1. Phase 1 → Phase 2 (US1) → Phase 3 (US2) → Phase 4 (US3) → Phase 5 (US4) → Phase 6 (US5) → Phase 7 (Polish)
2. Each phase commits: `feat(049): US{N} - {description}`

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[LLM抽出] → [空チェック] → [サニタイズ] → [Markdown生成] → [ファイル出力]
    ↓          ↓            ↓              ↓               ↓
  テスト     テスト       テスト         テスト          E2Eテスト
```

**チェックリスト**:
- [x] LLM 抽出部分のテスト（既存）
- [ ] 空コンテンツチェックのテスト（US1）
- [ ] タイトルサニタイズのテスト（US2）
- [ ] summary 長さ警告のテスト（US5）
- [x] E2E テスト（既存）

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- US3, US4 はプロンプト改善のみで TDD 対象外
- 各 Phase 終了時に `make test` で全テスト通過を確認
- E2E テスト (`make test-e2e`) は Phase 7 で実行
