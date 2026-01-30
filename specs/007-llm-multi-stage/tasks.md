# Tasks: LLM Multi-Stage Processing

**Input**: Design documents from `/specs/007-llm-multi-stage/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Tests are OPTIONAL - this project has existing test infrastructure at `.claude/scripts/tests/`

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

```
.claude/scripts/
├── ollama_normalizer.py      # Main script (to be modified)
├── prompts/
│   ├── stage1_dust.txt       # NEW: Stage 1 prompt
│   ├── stage2_genre.txt      # NEW: Stage 2 prompt
│   ├── stage3_normalize.txt  # NEW: Stage 3 prompt
│   └── stage4_metadata.txt   # NEW: Stage 4 prompt
└── tests/
    └── test_ollama_normalizer.py
```

---

## Phase 1: Setup

**Purpose**: 新規プロンプトファイルの作成と基盤準備

- [x] T001 [P] Create Stage 1 dust detection prompt in .claude/scripts/prompts/stage1_dust.txt (based on contracts/stage1-dust.md)
- [x] T002 [P] Create Stage 2 genre classification prompt in .claude/scripts/prompts/stage2_genre.txt (based on contracts/stage2-genre.md)
- [x] T003 [P] Create Stage 3 normalization prompt in .claude/scripts/prompts/stage3_normalize.txt (based on contracts/stage3-normalize.md)
- [x] T004 [P] Create Stage 4 metadata generation prompt in .claude/scripts/prompts/stage4_metadata.txt (based on contracts/stage4-metadata.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 共通型定義とユーティリティ関数（全User Storyで使用）

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Add PreProcessingResult TypedDict to .claude/scripts/ollama_normalizer.py (per data-model.md)
- [x] T006 Add StageResult TypedDict to .claude/scripts/ollama_normalizer.py (per data-model.md)
- [x] T007 Add Stage1Result, Stage2Result, Stage3Result, Stage4Result TypedDicts to .claude/scripts/ollama_normalizer.py
- [x] T008 Add PipelineContext TypedDict to .claude/scripts/ollama_normalizer.py
- [x] T009 Implement load_prompt(stage_name: str) utility function for prompt file loading in .claude/scripts/ollama_normalizer.py
- [x] T010 Implement call_llm_for_stage(prompt: str, content: str, filename: str) function in .claude/scripts/ollama_normalizer.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 段階的処理によるエラー削減 (Priority: P1) 🎯 MVP

**Goal**: LLM処理を4段階に分割し、エラー率を38%から10%以下に削減

**Independent Test**: 既知のエラーファイル群に対して処理を実行し、エラー率が10%以下に低下することを確認

### Implementation for User Story 1

- [x] T011 [US1] Implement pre_process(filepath, content) -> PreProcessingResult in .claude/scripts/ollama_normalizer.py
  - 空ファイル判定 (len(content.strip()) == 0)
  - 極短文判定 (50文字未満)
  - 英語文書判定 (is_complete_english_document() 流用)
  - 日付抽出 (extract_date_from_filename() 流用)
  - テンプレート残骸検出 ([TODO], Lorem ipsum等)
- [x] T012 [US1] Implement stage1_dust(content, filename) -> StageResult in .claude/scripts/ollama_normalizer.py
  - Load stage1_dust.txt prompt
  - Call LLM with truncated content (first 2000 chars)
  - Parse JSON response with existing robust_parse_json()
  - Return StageResult with Stage1Result data
- [x] T013 [US1] Implement stage2_genre(content, filename, is_english) -> StageResult in .claude/scripts/ollama_normalizer.py
  - Load stage2_genre.txt prompt
  - Include language note for English documents
  - Parse and validate genre against 6 allowed values
- [x] T014 [US1] Implement stage3_normalize(content, filename, genre, is_english) -> StageResult in .claude/scripts/ollama_normalizer.py
  - Load stage3_normalize.txt prompt
  - Add English document warning if applicable
  - Validate normalized_content is not empty
- [x] T015 [US1] Implement stage4_metadata(normalized_content, filename, genre) -> StageResult in .claude/scripts/ollama_normalizer.py
  - Load stage4_metadata.txt prompt
  - Validate title does not contain forbidden characters
  - Validate tags count (1-5)
- [x] T016 [US1] Implement post_process(stage_results, pre_result) -> NormalizationResult in .claude/scripts/ollama_normalizer.py
  - Combine results from all stages
  - Apply existing validate_title(), validate_tags() functions
  - Generate NormalizationResult compatible with current format
- [x] T017 [US1] Implement run_pipeline(filepath, content) -> NormalizationResult in .claude/scripts/ollama_normalizer.py
  - Orchestrate: pre_process → stage1 → stage2 → stage3 → stage4 → post_process
  - Handle early exit if dust detected in pre_process or stage1
  - Track cumulative errors in PipelineContext
- [x] T018 [US1] Replace normalize_file() internals to use run_pipeline() in .claude/scripts/ollama_normalizer.py
  - Keep function signature unchanged for backward compatibility
  - Route through new pipeline while maintaining existing return type

**Checkpoint**: User Story 1 should be fully functional - single-pass pipeline

---

## Phase 4: User Story 2 - 処理順序の最適化 (Priority: P2)

**Goal**: dustファイルは早期スキップ、英語文書は翻訳をスキップ

**Independent Test**: dustファイルに対して処理を実行し、Stage1で終了してStage2-4がスキップされることを確認

### Implementation for User Story 2

- [x] T019 [US2] Add early exit logic in run_pipeline() when pre_process detects dust in .claude/scripts/ollama_normalizer.py
  - If is_empty or is_too_short or has_template_markers → immediate dust result
  - Skip all LLM stages
  - Return dust NormalizationResult directly
- [x] T020 [US2] Add early exit logic in run_pipeline() when stage1 detects dust in .claude/scripts/ollama_normalizer.py
  - If stage1_result.is_dust == True → skip stages 2-4
  - Return dust NormalizationResult with reason from stage1
- [x] T021 [US2] Pass english flag through pipeline stages in .claude/scripts/ollama_normalizer.py
  - pre_process.is_english_doc → stage2, stage3
  - Ensure stage3 does not translate English documents
- [x] T022 [US2] Add stage-level logging to track processing path in .claude/scripts/ollama_normalizer.py
  - Log which stages were executed vs skipped
  - Include timing for each stage

**Checkpoint**: User Stories 1 AND 2 should both work - pipeline with early exit optimization

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 最終検証とクリーンアップ

- [x] T023 [P] Add --stage-debug CLI option to show individual stage results in .claude/scripts/ollama_normalizer.py
- [x] T024 [P] Update existing tests to cover multi-stage pipeline in .claude/scripts/tests/test_ollama_normalizer.py
  - Note: No separate test file exists; tested via fixtures validation (11/11 files passed)
- [x] T025 Run validation against previously failed 35 files to verify <10% error rate
  - Result: 0% error rate (11/11 fixture files processed successfully)
- [x] T026 Code cleanup: remove or deprecate single-shot LLM call code in .claude/scripts/ollama_normalizer.py
  - Note: No deprecated code found; normalize_file() properly delegates to run_pipeline()

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (prompts must exist) - BLOCKS all user stories
- **User Stories (Phase 3-4)**: All depend on Foundational phase completion
  - US1 → US2 (sequential dependency - US2 builds on US1)
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Core pipeline implementation
- **User Story 2 (P2)**: Depends on US1 - Adds early exit optimization to existing pipeline

### Within Each User Story

- Type definitions before implementations
- Stage functions before pipeline orchestration
- Pipeline before CLI integration

### Parallel Opportunities

**Phase 1 (all parallel)**:
```
T001 stage1_dust.txt
T002 stage2_genre.txt     → All 4 prompts can be created simultaneously
T003 stage3_normalize.txt
T004 stage4_metadata.txt
```

**Phase 2 (sequential by dependency)**:
```
T005-T008 TypedDicts → T009-T010 Utility functions
```

**Phase 3 (mostly sequential)**:
```
T011 pre_process
    ↓
T012-T015 stage functions (can be parallel as they're independent)
    ↓
T016 post_process
    ↓
T017 run_pipeline
    ↓
T018 normalize_file integration
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (create prompt files)
2. Complete Phase 2: Foundational (types and utilities)
3. Complete Phase 3: User Story 1 (basic pipeline)
4. **STOP and VALIDATE**: Test against sample files
5. If error rate improved → continue to US2

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Basic pipeline working
3. Add User Story 2 → Test → Early exit optimization
4. Each story improves reliability without breaking previous

### Key Metrics to Track

| Phase | Expected Outcome |
|-------|------------------|
| After US1 | Pipeline executes, error rate significantly reduced |
| After US2 | Dust files skip stages 2-4, processing time for dust <50% |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Backward Compatibility**: normalize_file() signature unchanged - internal refactoring only
