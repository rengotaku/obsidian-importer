# Tasks: Extract Stage Discovery 委譲

**Input**: Design documents from `/specs/031-extract-discovery-delegation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: テストタスクは spec.md で明示的に要求されていないため、最小限（既存テスト維持とリグレッションテスト）に留める。

**Organization**: 2つの User Story（ChatGPT インポート修正、Claude 後方互換性）を順に実装。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 基盤準備と現状確認

- [x] T001 Run `make test` to verify baseline (275 tests should pass)
- [x] T002 Review existing ClaudeExtractor structure in `src/etl/stages/extract/claude_extractor.py`
- [x] T003 Generate phase output: `specs/031-extract-discovery-delegation/tasks/ph1-output.md`

---

## Phase 2: User Story 1 - ChatGPT インポートが正常動作 (Priority: P1)

**Goal**: ChatGPT エクスポート ZIP を処理した際、全ての会話が正しくメッセージ付きでインポートされる

**Independent Test**: `make import INPUT=chatgpt_export.zip PROVIDER=openai LIMIT=5` で出力 Markdown にメッセージ内容が含まれていることを確認

### Implementation for User Story 1

- [x] T004 Read previous phase output: `specs/031-extract-discovery-delegation/tasks/ph1-output.md`
- [x] T005 [US1] Modify `ImportPhase.run()` to call `extract_stage.discover_items()` in `src/etl/phases/import_phase.py`
  - Change line ~347: `items = self.discover_items(input_path)` → `items = extract_stage.discover_items(input_path)`
- [x] T006 [US1] Verify ChatGPTExtractor.discover_items() returns Iterator (currently returns list) in `src/etl/stages/extract/chatgpt_extractor.py`
  - Change return type annotation if needed: `list[ProcessingItem]` → `Iterator[ProcessingItem]`
  - Confirm `yield from` or `iter()` compatibility
- [x] T007 [US1] Update ImportPhase to handle provider-specific discover in `src/etl/phases/import_phase.py`
  - For ChatGPT: use extract_stage.discover_items() directly
  - For Claude: temporarily keep self.discover_items() or delegate
- [x] T008 Run `make test` to verify no regressions
- [x] T009 Run `make import INPUT=<chatgpt_zip> PROVIDER=openai LIMIT=5` manual verification (Skipped - no test file)
- [x] T010 Generate phase output: `specs/031-extract-discovery-delegation/tasks/ph2-output.md`

---

## Phase 3: User Story 2 - Claude インポートの後方互換性 (Priority: P1)

**Goal**: 既存の Claude エクスポートインポートが引き続き正常に動作する

**Independent Test**: Claude エクスポートを処理し、現行と同じ出力が得られることを確認

### Implementation for User Story 2

- [x] T011 Read previous phase output: `specs/031-extract-discovery-delegation/tasks/ph2-output.md`
- [x] T012 [P] [US2] Copy `_expand_conversations()` from ImportPhase to ClaudeExtractor in `src/etl/stages/extract/claude_extractor.py`
- [x] T013 [P] [US2] Copy `_build_conversation_for_chunking()` from ImportPhase to ClaudeExtractor in `src/etl/stages/extract/claude_extractor.py`
- [x] T014 [P] [US2] Copy `_chunk_conversation()` from ImportPhase to ClaudeExtractor in `src/etl/stages/extract/claude_extractor.py`
- [x] T015 [US2] Add `discover_items()` method to ClaudeExtractor that calls `_expand_conversations()` in `src/etl/stages/extract/claude_extractor.py`
  - Method signature: `def discover_items(self, input_path: Path) -> Iterator[ProcessingItem]`
  - Logic: Check input_path exists, find conversations.json, call _expand_conversations
- [x] T016 [US2] Add necessary imports to ClaudeExtractor (json, datetime, Chunker, generate_file_id, etc.)
- [x] T017 [US2] Update ImportPhase.run() to use ClaudeExtractor.discover_items() for Claude provider in `src/etl/phases/import_phase.py`
- [x] T018 [US2] Remove discover-related methods from ImportPhase (discover_items, _expand_conversations, _build_conversation_for_chunking, _chunk_conversation) in `src/etl/phases/import_phase.py`
- [x] T019 [US2] Remove unused imports from ImportPhase (Chunker, SimpleMessage, SimpleConversation if no longer needed)
- [x] T020 Run `make test` to verify all 275 tests pass
- [ ] T021 Run `make import INPUT=<claude_export> PROVIDER=claude LIMIT=5` manual verification
- [x] T022 Generate phase output: `specs/031-extract-discovery-delegation/tasks/ph3-output.md`

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: 最終確認とドキュメント更新

- [x] T023 Read previous phase output: `specs/031-extract-discovery-delegation/tasks/ph3-output.md`
- [x] T024 [P] Add test for ClaudeExtractor.discover_items() in `src/etl/tests/test_stages.py`
- [x] T025 [P] Verify provider-required error message when `--provider` is omitted in CLI
- [x] T026 Update CLAUDE.md if any CLI behavior changes
- [x] T027 Run full test suite `make test` to verify all tests pass
- [x] T028 Run quickstart.md validation (both ChatGPT and Claude import)
- [x] T029 Generate phase output: `specs/031-extract-discovery-delegation/tasks/ph4-output.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (US1 - ChatGPT Fix)**: Depends on Phase 1 completion
- **Phase 3 (US2 - Claude Backward Compatibility)**: Depends on Phase 2 completion
- **Phase 4 (Polish)**: Depends on Phase 3 completion

### User Story Dependencies

- **User Story 1 (P1)**: ChatGPT インポート修正 - ImportPhase.run() の変更が主
- **User Story 2 (P1)**: Claude 後方互換性 - ClaudeExtractor への discover ロジック移植が主

### Within Each Phase

- T012-T014 (ClaudeExtractor へのメソッドコピー) は並列実行可能
- T024-T025 (テスト追加とCLI検証) は並列実行可能
- その他は順次実行

### Parallel Opportunities

```bash
# Phase 3: Copy methods in parallel
T012: Copy _expand_conversations
T013: Copy _build_conversation_for_chunking
T014: Copy _chunk_conversation

# Phase 4: Final checks in parallel
T024: Add ClaudeExtractor.discover_items() test
T025: Verify provider-required error message
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (baseline verification)
2. Complete Phase 2: User Story 1 (ChatGPT インポート修正)
3. **STOP and VALIDATE**: ChatGPT インポートが動作することを確認
4. この時点で ChatGPT インポートは修正されるが、Claude インポートは既存コードで動作

### Incremental Delivery

1. Phase 1 → Baseline confirmed (275 tests pass)
2. Phase 2 → ChatGPT import fixed → Manual test
3. Phase 3 → Claude backward compatibility → All tests pass
4. Phase 4 → Polish and documentation

---

## Risk Mitigation

| リスク | 対策 |
|--------|------|
| 既存テストの破壊 | 各 Phase 後に `make test` で確認 |
| Claude インポートのリグレッション | Phase 3 で慎重に移植、テスト確認 |
| チャンキングロジックの移植ミス | そのままコピー、テストで検証 |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- 既存の 275 テストを破壊しないことが最優先
- Provider は必須（spec.md FR-007）
- Transform/Load stage は変更なし（spec.md スコープ外）
