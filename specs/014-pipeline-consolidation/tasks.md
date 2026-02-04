# Tasks: Normalizer Pipeline統合

**Input**: Design documents from `/specs/014-pipeline-consolidation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: 既存テスト構造（normalizer/tests/）を流用。プロパティ毎チェック形式を維持。

**Organization**: US2(Stage A) → US3(Stage C) → US1(統合) の順で実装。US4(num_ctx)は基盤として先行。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

```text
.claude/scripts/
├── normalizer/
│   ├── models.py
│   ├── pipeline/
│   │   ├── stages.py
│   │   ├── runner.py
│   │   └── prompts.py
│   ├── io/
│   │   └── ollama.py
│   └── tests/
│       └── test_pipeline.py
└── prompts/
    ├── stage_a_classify.txt
    └── stage_c_metadata.txt
```

---

## Phase 1: Foundational (US4 + Models)

**Purpose**: 新ステージの基盤となるモデル定義とOllama設定

**⚠️ CRITICAL**: US2/US3の実装前に完了必須

- [X] T001 [P] [US4] Add `num_ctx: 16384` option to Ollama API calls in .claude/scripts/normalizer/io/ollama.py
- [X] T002 [P] Add StageAResult TypedDict (genre, subfolder, confidence, reason) in .claude/scripts/normalizer/models.py
- [X] T003 [P] Add StageCResult TypedDict (title, tags, summary, related) in .claude/scripts/normalizer/models.py
- [X] T004 [P] Update Frontmatter TypedDict to include summary and related fields in .claude/scripts/normalizer/models.py
- [X] T005 [P] Update NormalizationResult TypedDict (remove is_dust/dust_reason, add reason) in .claude/scripts/normalizer/models.py

**Checkpoint**: 新モデル定義完了、Ollama設定完了 ✅

---

## Phase 2: User Story 2 - Stage A: 分類判定の統合 (Priority: P1)

**Goal**: Dust判定とジャンル分類を1回のLLM呼び出しで同時実行

**Independent Test**: Stage Aのみを実行し、dust判定とジャンル分類が1回の呼び出しで正しく返されることを確認

### Implementation for User Story 2

- [X] T006 [P] [US2] Create stage_a_classify.txt prompt in .claude/scripts/prompts/stage_a_classify.txt
- [X] T007 [US2] Implement stage_a() function in .claude/scripts/normalizer/pipeline/stages.py
- [X] T008 [US2] Add routing logic for dust→@dust, unknown→@review in .claude/scripts/normalizer/io/files.py
- [X] T009 [US2] Add test_stage_a_dust() test case in .claude/scripts/normalizer/tests/test_pipeline.py
- [X] T010 [US2] Add test_stage_a_genre() test case in .claude/scripts/normalizer/tests/test_pipeline.py
- [X] T011 [US2] Add test_stage_a_unknown() test case in .claude/scripts/normalizer/tests/test_pipeline.py

**Checkpoint**: Stage A単体で動作確認可能 ✅

---

## Phase 3: User Story 3 - Stage C: メタデータ+Summary統合 (Priority: P1)

**Goal**: title、tags、summary（max 200文字）、relatedを1回のLLM呼び出しで生成

**Independent Test**: Stage Cのみを実行し、4フィールドが全て正しく生成されることを確認

### Implementation for User Story 3

- [X] T012 [P] [US3] Create stage_c_metadata.txt prompt in .claude/scripts/prompts/stage_c_metadata.txt
- [X] T013 [US3] Implement stage_c() function in .claude/scripts/normalizer/pipeline/stages.py
- [X] T014 [US3] Add summary validation (max 200 chars) in .claude/scripts/normalizer/validators/
- [X] T015 [US3] Add related field validation (internal link format) in .claude/scripts/normalizer/validators/
- [X] T016 [US3] Add test_stage_c_metadata() test case in .claude/scripts/normalizer/tests/test_pipeline.py
- [X] T017 [US3] Add test_stage_c_summary_max_length() test case in .claude/scripts/normalizer/tests/test_pipeline.py
- [X] T018 [US3] Add test_stage_c_related_format() test case in .claude/scripts/normalizer/tests/test_pipeline.py

**Checkpoint**: Stage C単体で動作確認可能 ✅

---

## Phase 4: User Story 1 - パイプライン統合 (Priority: P1)

**Goal**: Stage A → Stage B → Stage C の3段階パイプラインを実装

**Independent Test**: 単一ファイルの正規化処理でLLM呼び出し回数が3回であることを確認

### Implementation for User Story 1

- [X] T019 [US1] Update run_pipeline() to use stage_a/stage_b/stage_c in .claude/scripts/normalizer/pipeline/runner.py
- [X] T020 [US1] Implement dust skip logic (Stage A → @dust, skip B/C) in .claude/scripts/normalizer/pipeline/runner.py
- [X] T021 [US1] Implement unknown routing (Stage A → @review, skip B/C) in .claude/scripts/normalizer/pipeline/runner.py
- [X] T022 [US1] Update post_process() to use new result types in .claude/scripts/normalizer/pipeline/stages.py
- [X] T023 [US1] Update frontmatter generation to include summary/related in .claude/scripts/normalizer/pipeline/stages.py
- [X] T024 [US1] Add test_pipeline_full_flow() integration test in .claude/scripts/normalizer/tests/test_pipeline.py
- [X] T025 [US1] Add test_pipeline_dust_skip() test case in .claude/scripts/normalizer/tests/test_pipeline.py
- [X] T026 [US1] Add test_pipeline_unknown_routing() test case in .claude/scripts/normalizer/tests/test_pipeline.py

**Checkpoint**: 新パイプライン完全動作 ✅

---

## Phase 5: Cleanup & Polish

**Purpose**: 旧コード削除、テスト更新

- [X] T027 [P] Remove stage1_dust() function from .claude/scripts/normalizer/pipeline/stages.py
- [X] T028 [P] Remove stage2_genre() function from .claude/scripts/normalizer/pipeline/stages.py
- [X] T029 [P] Remove stage4_metadata() function from .claude/scripts/normalizer/pipeline/stages.py
- [X] T030 [P] Remove stage5_summary() function from .claude/scripts/normalizer/pipeline/stages.py
- [X] T031 [P] Delete .claude/scripts/prompts/stage1_dust.txt
- [X] T032 [P] Delete .claude/scripts/prompts/stage2_genre.txt
- [X] T033 [P] Delete .claude/scripts/prompts/stage4_metadata.txt
- [X] T034 [P] Delete .claude/scripts/prompts/stage5_summary.txt
- [X] T035 Remove old test cases (TestStage1Dust, TestStage2Genre, etc.) from .claude/scripts/normalizer/tests/test_pipeline.py
- [X] T036 Run full test suite and verify all tests pass (84 passed, 6 skipped)
- [X] T037 Create @review folder if not exists at project root (already exists)

**Checkpoint**: Phase 5 完了 - 旧コード削除、テスト更新完了 ✅

---

## Phase 6: Test Coverage Improvement

**Purpose**: 出力層のテストカバレッジ追加（build_normalized_file バグ発覚により追加）

**Background**: `summary` と `related` が frontmatter に出力されないバグを発見。原因は `build_normalized_file()` のテストが存在しなかったため。

### Test Gap Analysis (Resolved)

```
[Stage C] → [post_process_v2] → [frontmatter dict] → [build_normalized_file] → [YAML] → [File]
    ✅ tested              ✅ tested                   ✅ tested              ✅ tested
```

### Implementation

- [X] T038 [P] Create scripts/normalizer/tests/test_single.py skeleton
- [X] T039 Add TestBuildNormalizedFile class with test_includes_summary_and_related()
- [X] T040 Add test_includes_all_frontmatter_fields() - title, tags, created, summary, related, normalized
- [X] T041 Add test_review_fields_when_low_confidence() - review_confidence, review_reason
- [X] T042 Add test_empty_optional_fields() - summary/related が空の場合の挙動
- [X] T043 [P] Add TestNormalizeMarkdown class with basic normalization tests
- [X] T044 [P] Add TestCleanFilename and TestNormalizeFilename tests
- [X] T045 Run make test and verify all tests pass (110 unit + 6 integration = 116 tests)

**Checkpoint**: 出力層テストカバレッジ追加完了 ✅

---

## Phase 7: Directory Restructure (Completed)

**Purpose**: scripts ディレクトリをプロジェクトルートへ移動

- [X] T046 Move .claude/scripts/ to scripts/
- [X] T047 Update paths in scripts/normalizer/config.py
- [X] T048 Update paths in .claude/commands/og/*.md
- [X] T049 Update .claude/skills/makefile/SKILL.md
- [X] T050 Move Makefile to project root and update paths
- [X] T051 Add development/test section to CLAUDE.md
- [X] T052 Run make test and verify all tests pass

**Checkpoint**: ディレクトリ移動完了 ✅

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies - start immediately
- **Phase 2 (US2)**: Depends on T002 (StageAResult model)
- **Phase 3 (US3)**: Depends on T003, T004 (StageCResult, Frontmatter models)
- **Phase 4 (US1)**: Depends on Phase 2 AND Phase 3 completion
- **Phase 5 (Cleanup)**: Depends on Phase 4 completion and all tests passing
- **Phase 6 (Test Coverage)**: Depends on Phase 5, addresses test gap found during Phase 7
- **Phase 7 (Directory Restructure)**: Completed ✅

### User Story Dependencies

```
US4 (num_ctx) ────┐
                  │
US2 (Stage A) ────┼──→ US1 (Pipeline統合)
                  │
US3 (Stage C) ────┘
```

- **US4**: Foundational - no dependencies
- **US2**: Depends on US4 (num_ctx for API calls) and T002 (model)
- **US3**: Depends on US4 (num_ctx for API calls) and T003/T004 (models)
- **US1**: Depends on US2 AND US3 completion

### Parallel Opportunities

**Phase 1 (all parallel)**:
```
T001 (ollama.py) | T002 (StageAResult) | T003 (StageCResult) | T004 (Frontmatter) | T005 (NormalizationResult)
```

**Phase 2 & 3 (can run in parallel after Phase 1)**:
```
US2: T006 → T007 → T008 → T009/T010/T011

US3: T012 → T013 → T014/T015 → T016/T017/T018
```

**Phase 5 (all deletions parallel)**:
```
T027 | T028 | T029 | T030 | T031 | T032 | T033 | T034
```

---

## Parallel Example: Phase 1

```bash
# Launch all foundational tasks together:
Task: "T001 [P] Add num_ctx: 16384 option to Ollama API calls"
Task: "T002 [P] Add StageAResult TypedDict"
Task: "T003 [P] Add StageCResult TypedDict"
Task: "T004 [P] Update Frontmatter TypedDict"
Task: "T005 [P] Update NormalizationResult TypedDict"
```

---

## Implementation Strategy

### MVP First (Stage A + Stage C → Pipeline)

1. Complete Phase 1: Foundational models
2. Complete Phase 2: Stage A (US2)
3. Complete Phase 3: Stage C (US3)
4. Complete Phase 4: Pipeline integration (US1)
5. **STOP and VALIDATE**: Run `/og:organize` on test files
6. Complete Phase 5: Cleanup

### Incremental Validation

1. After Phase 1 → Run existing tests (should pass)
2. After Phase 2 → Test Stage A independently
3. After Phase 3 → Test Stage C independently
4. After Phase 4 → Test full pipeline
5. After Phase 5 → Full regression test

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Stage B (正規化) は既存のstage3_normalize()を維持（名前変更のみ検討）
- 既存テストのプロパティ毎チェック形式を維持してデグレ検知を担保
- Commit after each phase completion
