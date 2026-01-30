# Tasks: Phase 2 簡素化

**Input**: Design documents from `/specs/016-phase2-simplify/`
**Prerequisites**: plan.md, spec.md, research.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)

---

## Phase 1: Setup

**Purpose**: 既存コード確認、変更なし

- [x] T001 既存コード構造の確認（変更不要、既存構造を維持）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: プロンプトファイルと KnowledgeDocument クラスの修正（全 US に必要）

- [x] T002 [P] Create Summary 翻訳用プロンプト in scripts/llm_import/prompts/summary_translation.txt
- [x] T003 [P] Simplify まとめ生成用プロンプト in scripts/llm_import/prompts/knowledge_extraction.txt
- [x] T004 Update KnowledgeDocument class (remove tags, action_items, related_links; add summary) in scripts/llm_import/common/knowledge_extractor.py
- [x] T005 Update to_markdown() method (## 概要 → ## まとめ, remove ## 実践的なアクション, ## 関連) in scripts/llm_import/common/knowledge_extractor.py

**Checkpoint**: プロンプトと データクラスが準備完了 ✅

---

## Phase 3: User Story 1 + 2 - 構造化まとめ & Summary 翻訳 (Priority: P1) 🎯 MVP

**Goal**: 2段階 LLM 処理で Summary 翻訳と構造化まとめを生成

**Independent Test**: 英語 Summary 付き会話を処理し、日本語の `## まとめ` が構造化形式で生成されることを確認

### Implementation

- [x] T006 [US1][US2] Implement translate_summary() method for Step 1 (Summary only → LLM) in scripts/llm_import/common/knowledge_extractor.py
- [x] T007 [US1][US2] Implement extract_knowledge() method for Step 2 (conversation without Summary → LLM) in scripts/llm_import/common/knowledge_extractor.py
- [x] T008 [US1][US2] Update extract() method to orchestrate 2-step LLM flow in scripts/llm_import/common/knowledge_extractor.py
- [x] T009 [US1][US2] Update _build_document() to use new JSON fields (summary, summary_content) in scripts/llm_import/common/knowledge_extractor.py
- [x] T010 [US1][US2] Update _build_user_message() to exclude Summary section when calling Step 2 in scripts/llm_import/common/knowledge_extractor.py

**Checkpoint**: Summary 翻訳と構造化まとめが動作 ✅

---

## Phase 4: User Story 3 - ファイル名の簡素化 (Priority: P2)

**Goal**: 出力ファイル名から日付プレフィックスを除去

**Independent Test**: `2025-12-18_温泉BGMシステム.md` → `温泉BGMシステム.md`

### Implementation

- [x] T011 [US3] Update _generate_filename() to remove date prefix (YYYY-MM-DD_) in scripts/llm_import/cli.py

**Checkpoint**: ファイル名から日付プレフィックスが除去される ✅

---

## Phase 5: User Story 4 - Phase 3 削除 (Priority: P2)

**Goal**: CLI から Phase 3 (normalizer) 呼び出しを削除

**Independent Test**: `--skip-normalize` フラグなしで実行しても normalizer が呼ばれないこと

### Implementation

- [x] T012 [US4] Remove `--skip-normalize` argument definition in scripts/llm_import/cli.py
- [x] T013 [US4] Remove `skip_normalize` variable usage in cmd_process() in scripts/llm_import/cli.py
- [x] T014 [US4] Remove Phase 3 execution block (run_normalizer call) in scripts/llm_import/cli.py
- [x] T015 [US4] Remove run_normalizer() function in scripts/llm_import/cli.py

**Checkpoint**: Phase 2 までで処理が完了、Phase 3 は /og:organize に委譲 ✅

---

## Phase 6: Polish & Verification

**Purpose**: テスト更新と最終検証

- [x] T016 [P] Update MOCK_LLM_RESPONSE (remove title, tags, related_keywords, action_items) in scripts/llm_import/tests/test_knowledge_extractor.py
- [x] T017 [P] Update TestKnowledgeDocument.test_to_markdown() (## 概要 → ## まとめ, remove tags/action/related checks) in scripts/llm_import/tests/test_knowledge_extractor.py
- [x] T018 [P] Add test for 2-step LLM flow (with Summary case) in scripts/llm_import/tests/test_knowledge_extractor.py
- [x] T019 [P] Add test for 1-step LLM flow (without Summary case) in scripts/llm_import/tests/test_knowledge_extractor.py
- [x] T020 Run make test to verify all tests pass
- [ ] T021 Manual validation: Process sample conversation with English Summary
- [ ] T022 Manual validation: Process sample conversation without Summary

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3 (US1+US2)**: Depends on Phase 2 (prompts and KnowledgeDocument ready)
- **Phase 4 (US3)**: Depends on Phase 2, can run parallel to Phase 3
- **Phase 5 (US4)**: Depends on Phase 2, can run parallel to Phase 3/4
- **Phase 6 (Polish)**: Depends on all implementation phases

### User Story Dependencies

- **US1 + US2**: Tightly coupled (same 2-step LLM flow), implement together
- **US3**: Independent, only touches cli.py `_generate_filename()`
- **US4**: Independent, only touches cli.py Phase 3 removal

### Parallel Opportunities

```
Phase 2:
  T002 (summary_translation.txt) ─┬─ parallel
  T003 (knowledge_extraction.txt) ┘

After Phase 2:
  Phase 3 (US1+US2) ─┬─ parallel (different concerns)
  Phase 4 (US3)     ─┤
  Phase 5 (US4)     ─┘

Phase 6:
  T016, T017, T018, T019 ─ parallel (different test cases)
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 2: Foundational (prompts + KnowledgeDocument)
2. Complete Phase 3: US1 + US2 (2-step LLM)
3. **STOP and VALIDATE**: Test with sample conversation
4. Proceed to US3, US4

### Incremental Delivery

1. Phase 2 → Phase 3 → MVP ready (構造化まとめ + Summary 翻訳)
2. Add Phase 4 → ファイル名簡素化
3. Add Phase 5 → Phase 3 削除
4. Phase 6 → テスト・検証

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | T001 | Setup (確認のみ) |
| 2 | T002-T005 | Foundational (プロンプト + データクラス) |
| 3 | T006-T010 | US1+US2: 2段階 LLM |
| 4 | T011 | US3: ファイル名簡素化 |
| 5 | T012-T015 | US4: Phase 3 削除 |
| 6 | T016-T022 | テスト・検証 |

**Total**: 22 tasks
**Parallel opportunities**: T002-T003, T016-T019, Phase 3/4/5 can overlap
