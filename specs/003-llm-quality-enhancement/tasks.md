# Tasks: ローカルLLM品質向上

**Input**: Design documents from `/specs/003-llm-quality-enhancement/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli.md ✅, quickstart.md ✅

**Tests**: Optional (テスト実装は明示的に要求された場合のみ)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)

## Path Conventions

- **Scripts**: `.claude/scripts/`
- **Prompts**: `.claude/scripts/prompts/`
- **Data**: `.claude/scripts/data/`
- **Tests**: `.claude/scripts/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: プロジェクト構造の作成と基本設定

- [ ] T001 Create directory structure: `.claude/scripts/prompts/examples/`, `.claude/scripts/data/`, `.claude/scripts/tests/fixtures/`
- [ ] T002 [P] Create `@review/` folder for low-confidence files at repository root
- [ ] T003 [P] Verify Ollama service and gpt-oss:20b model availability

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 全User Storyで共有される基盤コンポーネント

**⚠️ CRITICAL**: User Story実装前に完了必須

- [ ] T004 Create improved system prompt template in `.claude/scripts/prompts/normalizer_v2.txt` with Few-shot examples (3-5 examples for title, tags, content improvement)
- [ ] T005 [P] Create Few-shot example files in `.claude/scripts/prompts/examples/` (3-5 input/output pairs)
- [ ] T006 Implement tag extraction module in `.claude/scripts/tag_extractor.py` (FR-004: extract tags from existing Vaults, categorize by language/infrastructure/tools/concepts/lifestyle)
- [ ] T007 Implement Markdown post-processing module in `.claude/scripts/markdown_normalizer.py` (FR-005: heading level adjustment, blank line compression, bullet unification)
- [ ] T008 [P] Implement English document detection logic (research.md criteria: length 500+, English ratio 80%+, heading count 2+, weighted score >= 0.7)

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - タイトル品質の改善 (Priority: P1) 🎯 MVP

**Goal**: 生成されるタイトルがClaude Opusレベルの品質になる

**Independent Test**: 10件のサンプルファイルを処理し、タイトル品質をClaude Opus比較で評価

### Implementation for User Story 1

- [ ] T009 [US1] Update prompt template with title-focused Few-shot examples in `.claude/scripts/prompts/normalizer_v2.txt` (good/bad title pairs, filename restrictions)
- [ ] T010 [US1] Modify `ollama_normalizer.py` to load and use new prompt template from `.claude/scripts/prompts/normalizer_v2.txt`
- [ ] T011 [US1] Add filename validation in `ollama_normalizer.py` (FR-002: remove filesystem-forbidden characters)
- [ ] T012 [US1] Add title quality logging in `ollama_normalizer.py` (log generated title vs original filename)

**Checkpoint**: Title generation should produce high-quality, descriptive titles for any input file

---

## Phase 4: User Story 2 - メタタグ品質向上 (Priority: P2)

**Goal**: 生成されるタグが一貫性あり、検索・フィルタリングに有用

**Independent Test**: 20件のファイルを処理し、タグ一貫性と網羅性を評価

### Implementation for User Story 2

- [ ] T013 [US2] Integrate tag_extractor.py output into prompt injection in `ollama_normalizer.py` (FR-004: load tag_dictionary.json, inject into prompt)
- [ ] T014 [US2] Update prompt template with tag-focused examples in `.claude/scripts/prompts/normalizer_v2.txt` (demonstrate 3-5 tags, existing vocabulary usage)
- [ ] T015 [US2] Add tag validation in `ollama_normalizer.py` (FR-003: enforce 3-5 tags per file, validate against dictionary)
- [ ] T016 [US2] Add tag consistency logging in `ollama_normalizer.py` (log tag match rate with dictionary)

**Checkpoint**: Tags should be consistent with existing vocabulary and appropriately cover file topics

---

## Phase 5: User Story 3 - Markdownフォーマット正規化 (Priority: P3)

**Goal**: 出力MarkdownがObsidian規約に従い一貫したフォーマット

**Independent Test**: フォーマット処理のみテストし、見出しレベル・空行・箇条書きの一貫性を検証

### Implementation for User Story 3

- [ ] T017 [US3] Integrate markdown_normalizer.py into ollama_normalizer.py post-processing pipeline (FR-005, FR-008)
- [ ] T018 [US3] Add frontmatter preservation in `markdown_normalizer.py` (protect YAML block during normalization)
- [ ] T019 [US3] Add format validation check in `ollama_normalizer.py` (verify output passes all normalization rules)
- [ ] T020 [US3] Add `--diff` option support in `ollama_normalizer.py` (FR-007: show before/after comparison)

**Checkpoint**: All output files should pass Markdown format validation with consistent heading/bullet/whitespace

---

## Phase 6: User Story 4 - コンテンツ精査・改善 (Priority: P2)

**Goal**: 冗長表現の簡潔化、不完全文の補完、断片的英語メモの日本語化

**Independent Test**: 冗長文書、不完全メモ、英語混じり文書を処理し改善確認

### Implementation for User Story 4

- [ ] T021 [US4] Update prompt template with content improvement examples in `.claude/scripts/prompts/normalizer_v2.txt` (verbose→concise, incomplete→complete, code preservation)
- [ ] T022 [US4] Integrate English document detection into `ollama_normalizer.py` (FR-011, FR-012: skip translation for complete English docs)
- [ ] T023 [US4] Add improvements_made tracking in `ollama_normalizer.py` (data-model.md: log what was improved)
- [ ] T024 [US4] Update output format to show improvements in `ollama_normalizer.py` (CLI output: list improvements made)

**Checkpoint**: Content should be concise, complete, and in natural Japanese (unless complete English doc)

---

## Phase 7: Low-Confidence Handling (@review)

**Purpose**: 確信度が低いファイルの適切な処理

- [ ] T025 Implement confidence threshold check in `ollama_normalizer.py` (FR-013: threshold 0.7)
- [ ] T026 Implement @review folder output in `ollama_normalizer.py` (FR-013, FR-014: output to @review/ with confidence and reason in frontmatter)
- [ ] T027 Add review_confidence and review_reason to frontmatter output (data-model.md: Frontmatter extension)
- [ ] T028 Update batch processing stats to include review count in `ollama_normalizer.py` (CLI stats: success/dust/review/error)

**Checkpoint**: Low-confidence files should be routed to @review/ with metadata for human review

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 品質向上、ドキュメント更新

- [ ] T029 [P] Add quality metrics output in `ollama_normalizer.py` (FR-006: title match rate, tag consistency, format compliance)
- [ ] T030 [P] Create test fixtures in `.claude/scripts/tests/fixtures/` (sample files for each scenario)
- [ ] T031 Update `--status` command to show review folder stats in `ollama_normalizer.py`
- [ ] T032 [P] Add `--json` output format for all operations in `ollama_normalizer.py` (contracts/cli.md schemas)
- [ ] T033 Run quickstart.md validation workflow (end-to-end test with sample files)
- [ ] T034 Performance validation: ensure processing time < 30 seconds per file (SC-004)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Title) → US2 (Tags) → US4 (Content) can be sequential or parallel
  - US3 (Format) can be parallel with US2/US4
- **Low-Confidence (Phase 7)**: Depends on core implementation (Phase 3+)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|-----------|-------------------|
| US1 (Title) | Foundational | - |
| US2 (Tags) | Foundational, US1 (prompt integration) | US3 |
| US3 (Format) | Foundational | US2, US4 |
| US4 (Content) | Foundational | US3 |

### Within Each User Story

- Prompt template updates before integration
- Core implementation before validation
- Validation before logging/metrics

### Parallel Opportunities

- T002, T003: Setup tasks
- T005, T008: Foundational tasks
- T029, T030, T032: Polish tasks

---

## Parallel Example: Foundational Phase

```bash
# Launch parallel foundational tasks:
Task: "T005 [P] Create Few-shot example files"
Task: "T008 [P] Implement English document detection logic"

# Then sequential:
Task: "T004 Create improved system prompt template" (depends on T005)
Task: "T006 Implement tag extraction module"
Task: "T007 Implement Markdown post-processing module"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T008)
3. Complete Phase 3: User Story 1 (T009-T012)
4. **STOP and VALIDATE**: Test title quality with 10 sample files
5. Compare with Claude Opus output

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Title) → Test independently → **MVP!**
3. Add US2 (Tags) → Test tag consistency
4. Add US3 (Format) → Test format compliance
5. Add US4 (Content) → Test content improvement
6. Add Low-Confidence handling → Test @review workflow
7. Polish → Quality metrics and documentation

### Single Developer Strategy

1. Phase 1-2: Setup + Foundational (T001-T008)
2. Phase 3: US1 Title (T009-T012) → Validate
3. Phase 4: US2 Tags (T013-T016) → Validate
4. Phase 5: US3 Format (T017-T020) → Validate
5. Phase 6: US4 Content (T021-T024) → Validate
6. Phase 7: Low-Confidence (T025-T028) → Validate
7. Phase 8: Polish (T029-T034) → Final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Existing `ollama_normalizer.py` is the primary modification target
- New modules: `tag_extractor.py`, `markdown_normalizer.py`
- Standard library only (no external dependencies)
- Commit after each task or logical group
