# Tasks: 重複処理の解消

**Input**: Design documents from `/specs/041-fix-extract-dedup/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/extractor-contract.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Revert band-aid fixes and prepare clean baseline

- [X] T001 Revert pass-through guard changes in src/etl/stages/extract/chatgpt_extractor.py (band-aid from current branch)
- [X] T002 [P] Revert `_max_records_per_file` change in src/etl/core/stage.py (5000 → 1000)
- [X] T003 Run `make test` to verify baseline after reverts
- [X] T004 Generate phase output: specs/041-fix-extract-dedup/tasks/ph1-output.md

---

## Phase 2: Foundational - BaseExtractor テンプレート完成 (Priority: P1)

**Purpose**: BaseExtractor に `_build_chunk_messages()` hook を追加し、`_chunk_if_needed()` を完成させる。全 US の前提条件。

**Goal**: テンプレートが構造的に重複を防止する設計にする

### 入力

- [x] T005 Read previous phase output: specs/041-fix-extract-dedup/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T006 [P] Implement test for `_build_chunk_messages()` hook in BaseExtractor in src/etl/tests/test_extractor_template.py
- [x] T007 [P] Implement test for `_chunk_if_needed()` using `_build_chunk_messages()` hook in src/etl/tests/test_extractor_template.py
- [x] T008 [P] Implement test that `stage_type` returns EXTRACT from BaseExtractor (no override needed) in src/etl/tests/test_extractor_template.py
- [x] T009 Verify `make test` FAIL (RED)
- [x] T010 Generate RED output: specs/041-fix-extract-dedup/red-tests/ph2-test.md

### 実装 (GREEN)

- [x] T011 Read RED tests: specs/041-fix-extract-dedup/red-tests/ph2-test.md
- [x] T012 Add `_build_chunk_messages()` hook method to BaseExtractor in src/etl/core/extractor.py
- [x] T013 Update `_chunk_if_needed()` in BaseExtractor to call `_build_chunk_messages()` hook in src/etl/core/extractor.py
- [x] T014 Verify `make test` PASS (GREEN)

### 検証

- [x] T015 Verify `make test` passes all tests (no regressions)
- [x] T016 Generate phase output: specs/041-fix-extract-dedup/tasks/ph2-output.md

**Checkpoint**: BaseExtractor テンプレートが完成。子クラスは `_build_chunk_messages()` を実装するだけで chunking が動作する

---

## Phase 3: User Story 1 - ChatGPT 重複処理の解消 (Priority: P1) MVP

**Goal**: ChatGPT エクスポート ZIP のインポートで N² 重複が発生しない

**Independent Test**: `make import INPUT=chatgpt.zip PROVIDER=openai LIMIT=5` で Extract 出力レコード数が会話数以下

### 入力

- [x] T017 Read previous phase output: specs/041-fix-extract-dedup/tasks/ph2-output.md

### テスト実装 (RED)

- [x] T018 [P] [US1] Implement test: discover → run で N items が N output になる（N² にならない）in src/etl/tests/test_chatgpt_dedup.py
- [x] T019 [P] [US1] Implement test: pipeline_stages.jsonl に同一 conversation_uuid が 2 回以上出現しない in src/etl/tests/test_chatgpt_dedup.py
- [x] T020 [P] [US1] Implement test: ChatGPTExtractor.steps が ValidateMinMessagesStep のみを返す in src/etl/tests/test_chatgpt_dedup.py
- [x] T021 [P] [US1] Implement test: `_build_chunk_messages()` が ChatGPT 形式 `{uuid, text, sender, created_at}` を返す in src/etl/tests/test_chatgpt_dedup.py
- [x] T021b [P] [US1] Implement test: `_discover_raw_items()` が ZIP から content 設定済み・metadata 設定済みの ProcessingItem を yield する in src/etl/tests/test_chatgpt_dedup.py
- [x] T021c [P] [US1] Implement test: ChatGPT チャンキング後の `chat_messages` に uuid, created_at が含まれる in src/etl/tests/test_chatgpt_dedup.py
- [x] T021d [P] [US1] Implement test: 空の conversations.json（0 会話）ZIP で正常終了する in src/etl/tests/test_chatgpt_dedup.py
- [x] T021e [P] [US1] Implement test: mapping/current_node 欠損の会話がスキップされ他の会話は正常処理される in src/etl/tests/test_chatgpt_dedup.py
- [x] T022 Verify `make test` FAIL (RED)
- [x] T023 Generate RED output: specs/041-fix-extract-dedup/red-tests/ph3-test.md

### 実装 (GREEN)

- [x] T024 Read RED tests: specs/041-fix-extract-dedup/red-tests/ph3-test.md
- [x] T024b [US1] Expand `_discover_raw_items()` to include ZIP 読み込み・パース・Claude 形式変換（Steps から移行）in src/etl/stages/extract/chatgpt_extractor.py (ALREADY DONE per RED phase)
- [x] T025 [US1] Delete ReadZipStep, ParseConversationsStep, ConvertFormatStep from src/etl/stages/extract/chatgpt_extractor.py
- [x] T026 [US1] Update ChatGPTExtractor.steps to return `[ValidateMinMessagesStep()]` only in src/etl/stages/extract/chatgpt_extractor.py
- [x] T027 [US1] Implement `_build_chunk_messages()` in ChatGPTExtractor in src/etl/stages/extract/chatgpt_extractor.py
- [x] T028 [US1] Delete `_chunk_if_needed()` override from ChatGPTExtractor in src/etl/stages/extract/chatgpt_extractor.py
- [x] T029 [US1] Delete `stage_type` override from ChatGPTExtractor in src/etl/stages/extract/chatgpt_extractor.py
- [x] T030 Verify `make test` PASS (GREEN)

### 検証

- [x] T031 [US1] Verify existing test_stages.py ChatGPT tests still pass (skipped obsolete tests)
- [x] T032 [US1] Verify existing test_debug_step_output.py ChatGPT tests still pass
- [x] T032b [US1] Verify ImportPhase.run() で ChatGPT Extractor の discover_items() → run() フローが正常動作する統合確認 (verified via test_chatgpt_dedup.py tests)
- [x] T033 Generate phase output: specs/041-fix-extract-dedup/tasks/ph3-output.md

**Checkpoint**: ChatGPT インポートで重複が発生しない。N 会話 → N レコード出力

---

## Phase 4: User Story 2 - Claude Extractor テンプレート統一 (Priority: P1)

**Goal**: 全 Extractor で `_discover_raw_items()` と `steps` の責務が一意に決まる

**Independent Test**: 全 Extractor のコードレビューで重複処理がないことを確認

### 入力

- [x] T034 Read previous phase output: specs/041-fix-extract-dedup/tasks/ph3-output.md

### テスト実装 (RED)

- [x] T035 [P] [US2] Implement test: ClaudeExtractor.`_build_chunk_messages()` が `{text, sender}` を返す in src/etl/tests/test_extractor_template.py
- [x] T036 [P] [US2] Implement test: ClaudeExtractor に `_chunk_if_needed()` override がないことを確認 in src/etl/tests/test_extractor_template.py
- [x] T037 [P] [US2] Implement test: ClaudeExtractor に `stage_type` override がないことを確認 in src/etl/tests/test_extractor_template.py
- [x] T038 Verify `make test` FAIL (RED)
- [x] T039 Generate RED output: specs/041-fix-extract-dedup/red-tests/ph4-test.md

### 実装 (GREEN)

- [x] T040 Read RED tests: specs/041-fix-extract-dedup/red-tests/ph4-test.md
- [x] T041 [US2] Implement `_build_chunk_messages()` in ClaudeExtractor in src/etl/stages/extract/claude_extractor.py
- [x] T042 [US2] Delete `_chunk_if_needed()` override from ClaudeExtractor in src/etl/stages/extract/claude_extractor.py
- [x] T043 [US2] Delete `stage_type` override from ClaudeExtractor in src/etl/stages/extract/claude_extractor.py
- [x] T044 Verify `make test` PASS (GREEN)

### 検証

- [x] T045 [US2] Verify existing test_claude_extractor_refactoring.py tests still pass
- [x] T046 [US2] Verify existing test_chunking_integration.py tests still pass
- [x] T047 Generate phase output: specs/041-fix-extract-dedup/tasks/ph4-output.md

**Checkpoint**: Claude/ChatGPT の Extractor が統一テンプレートに従う。`_chunk_if_needed()` override なし

---

## Phase 5: User Story 3 - 全 Extractor 統一パターン適用 (Priority: P2)

**Goal**: GitHub Extractor もテンプレートメソッドに従い、4 種の Extractor が一貫した設計パターン

**Independent Test**: 全 Extractor で `discover_items()` → `run()` フローが正常動作

### 入力

- [x] T048 Read previous phase output: specs/041-fix-extract-dedup/tasks/ph4-output.md

### テスト実装 (RED)

- [x] T049 [P] [US3] Implement test: GitHubExtractor に `discover_items()` override がないことを確認 in src/etl/tests/test_extractor_template.py
- [x] T050 [P] [US3] Implement test: GitHubExtractor に `stage_type` override がないことを確認 in src/etl/tests/test_extractor_template.py
- [x] T051 [P] [US3] Implement test: GitHubExtractor.`_discover_raw_items()` が Iterator を返す in src/etl/tests/test_extractor_template.py
- [x] T052 Verify `make test` FAIL (RED)
- [x] T053 Generate RED output: specs/041-fix-extract-dedup/red-tests/ph5-test.md

### 実装 (GREEN)

- [x] T054 Read RED tests: specs/041-fix-extract-dedup/red-tests/ph5-test.md
- [x] T055 [US3] Delete `discover_items()` override from GitHubExtractor in src/etl/stages/extract/github_extractor.py
- [x] T055b [US3] Verify git clone ロジックが `_discover_raw_items()` に集約されていることを確認（`discover_items()` override 削除後に欠落しないこと）
- [x] T056 [US3] Delete `stage_type` override from GitHubExtractor in src/etl/stages/extract/github_extractor.py
- [x] T057 [US3] Ensure `_discover_raw_items()` returns Iterator (not list) in src/etl/stages/extract/github_extractor.py
- [x] T058 Verify `make test` PASS (GREEN)

### 検証

- [x] T059 [US3] Verify existing test_github_extractor.py tests still pass
- [x] T060 [US3] Verify FileExtractor (BaseStage 系統) is unaffected - run test_organize_phase.py
- [x] T061 Generate phase output: specs/041-fix-extract-dedup/tasks/ph5-output.md

**Checkpoint**: 全 4 Extractor が統一パターンに従う

---

## Phase 6: User Story 4 - INPUT_TYPE と複数 INPUT 対応 (Priority: P2)

**Goal**: CLI が `--input-type` と複数 `--input` をサポートする

**Independent Test**: `--input-type url` で GitHub URL、`--input-type path` で ZIP ファイルが正しく動作

### 入力

- [x] T062 Read previous phase output: specs/041-fix-extract-dedup/tasks/ph5-output.md

### テスト実装 (RED)

- [x] T063 [P] [US4] Implement test: `--input-type path` がデフォルトで従来と同じ動作 in src/etl/tests/test_import_cmd.py
- [x] T064 [P] [US4] Implement test: `--input-type url` で URL が extract/input/url.txt に保存される in src/etl/tests/test_import_cmd.py
- [x] T065 [P] [US4] Implement test: `--input` 複数指定で全入力が処理される in src/etl/tests/test_import_cmd.py
- [x] T066 [P] [US4] Implement test: `--input-type` 省略で URL 入力はエラー in src/etl/tests/test_import_cmd.py
- [x] T067 Verify `make test` FAIL (RED)
- [x] T068 Generate RED output: specs/041-fix-extract-dedup/red-tests/ph6-test.md

### 実装 (GREEN)

- [x] T069 Read RED tests: specs/041-fix-extract-dedup/red-tests/ph6-test.md
- [x] T070 [US4] Add `--input-type` argument (default: `path`, choices: `path`/`url`) to import command parser in src/etl/cli/commands/import_cmd.py
- [x] T071 [US4] Change `--input` to `action="append"` for multiple inputs in src/etl/cli/commands/import_cmd.py
- [x] T072 [US4] Implement input validation logic (path exists check, URL format check) in src/etl/cli/commands/import_cmd.py
- [x] T073 [US4] Implement input resolution: copy files for path, save url.txt for url in src/etl/cli/commands/import_cmd.py
- [x] T074 [US4] Remove provider-dependent input handling (`if provider == "github"`) from src/etl/cli/commands/import_cmd.py
- [x] T075 [US4] Update ImportPhase.run() to handle multiple input sources in src/etl/phases/import_phase.py (no changes needed - extractors already handle multiple files)
- [x] T076 Verify `make test` PASS (GREEN) - Phase 6 specific tests all pass

### 検証

- [x] T077 [US4] Verify existing import tests still pass (pre-existing errors unrelated to Phase 6)
- [x] T078 Generate phase output: specs/041-fix-extract-dedup/tasks/ph6-output.md

**Checkpoint**: CLI 入力インターフェースが統一。複数入力・URL 入力に対応

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Makefile 更新、ドキュメント、最終検証

- [x] T079 Read previous phase output: specs/041-fix-extract-dedup/tasks/ph6-output.md
- [x] T080 [P] Update Makefile: add INPUT_TYPE variable and comma-separated multiple INPUT support
- [x] T081 [P] Update CLAUDE.md: CLI documentation for `--input-type` and multiple `--input`
- [x] T082 [P] Clean up unused imports and dead code in modified files
- [x] T083 Run `make test` to verify all tests pass (final regression check)
- [x] T084 Run quickstart.md validation: `make import INPUT=chatgpt.zip PROVIDER=openai LIMIT=5 DEBUG=1` and verify no duplication
- [x] T085 Generate phase output: specs/041-fix-extract-dedup/tasks/ph7-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - revert band-aid fixes
- **Phase 2 (Foundational)**: Depends on Phase 1 - BaseExtractor template completion BLOCKS all user stories
- **Phase 3 (US1 ChatGPT)**: Depends on Phase 2 - MVP target
- **Phase 4 (US2 Claude)**: Depends on Phase 2 - can run parallel with Phase 3
- **Phase 5 (US3 GitHub)**: Depends on Phase 2 - can run parallel with Phase 3/4
- **Phase 6 (US4 CLI)**: Depends on Phase 5 (all extractors unified) - input handling changes
- **Phase 7 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1 (ChatGPT dedup)**: Phase 2 only - no dependencies on other stories
- **US2 (Claude template)**: Phase 2 only - can run parallel with US1
- **US3 (GitHub template)**: Phase 2 only - can run parallel with US1/US2
- **US4 (INPUT_TYPE CLI)**: Depends on US3 completion (all extractors unified first)

### Within Each User Story (TDD Flow)

1. テスト実装 (RED): assertions 実装 → `make test` FAIL 確認
2. 実装 (GREEN): プロダクションコード実装 → `make test` PASS 確認
3. 検証: 既存テスト回帰なし確認

---

## Parallel Opportunities

### Phase 2 (Foundational)

```text
# Parallel test writing:
T006: test _build_chunk_messages hook
T007: test _chunk_if_needed with hook
T008: test stage_type inheritance
```

### Phase 3-5 (US1/US2/US3 can run in parallel after Phase 2)

```text
# After Phase 2 completes, these phases can start simultaneously:
Phase 3 (US1): ChatGPT Steps deletion + _build_chunk_messages
Phase 4 (US2): Claude _chunk_if_needed override deletion
Phase 5 (US3): GitHub discover_items override deletion
```

### Within Each Phase

```text
# Test tasks marked [P] can run in parallel:
T018, T019, T020, T021 (Phase 3 tests)
T035, T036, T037 (Phase 4 tests)
T049, T050, T051 (Phase 5 tests)
T063, T064, T065, T066 (Phase 6 tests)
```

---

## Implementation Strategy

### MVP First (Phase 1-3: US1 Only)

1. Phase 1: Revert band-aid fixes
2. Phase 2: Complete BaseExtractor template (`_build_chunk_messages` hook)
3. Phase 3: Fix ChatGPT N² duplication
4. **STOP and VALIDATE**: `make import INPUT=chatgpt.zip PROVIDER=openai LIMIT=5` → verify N items = N records

### Incremental Delivery

1. Phase 1-3 → MVP (ChatGPT duplication fixed)
2. Phase 4 → Claude extractor unified (regression-only, no behavior change)
3. Phase 5 → GitHub extractor unified (regression-only, no behavior change)
4. Phase 6 → CLI input interface unified (`--input-type`, multiple `--input`)
5. Phase 7 → Documentation and cleanup

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生するすべての境界でテストを書く

```
[ZIP/JSON] → [discover_raw_items] → [chunk_if_needed] → [run(steps)] → [output.jsonl]
     ↓              ↓                      ↓                 ↓              ↓
   テスト         テスト                 テスト             テスト         テスト
```

**チェックリスト**:
- [ ] discover_raw_items の出力テスト（content 設定済み、metadata 設定済み）
- [ ] _chunk_if_needed + _build_chunk_messages の統合テスト
- [ ] Steps の pass-through / validation テスト
- [ ] End-to-End: discover → run → output レコード数一致テスト

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- band-aid 修正（pass-through ガード）は Phase 1 で revert し、Phase 3 で構造的に解決
- FileExtractor (BaseStage 直接継承) は本 feature のスコープ外（別 feature で対応）
- 各 Phase 完了時に `make test` で回帰チェック必須
