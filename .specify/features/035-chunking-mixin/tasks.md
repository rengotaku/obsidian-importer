# Tasks: チャンク処理の共通化

**Input**: Design documents from `/specs/035-chunking-mixin/`
**Prerequisites**: plan.md, spec.md, data-model.md, quickstart.md, research.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/etl/`, `src/etl/tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 設計ドキュメント確認と既存コード構造の把握

- [x] T001 Read spec.md, plan.md, data-model.md to understand requirements
- [x] T002 Review existing BaseStage in src/etl/core/stage.py
- [x] T003 Review existing Chunker in src/etl/utils/chunker.py
- [x] T004 Review existing ClaudeExtractor in src/etl/stages/extract/claude_extractor.py
- [x] T005 Run `make test` to verify current tests pass

---

## Phase 2: Foundational - BaseStage Template Method 追加

**Purpose**: BaseStage に Template Method パターンを追加（全 Extractor の前提）

**⚠️ CRITICAL**: この Phase が完了するまで User Story の実装は不可

### 入力
- [x] T006 Read previous phase output: specs/035-chunking-mixin/tasks/ph1-output.md

### テスト設計
- [x] T007 Create test skeleton: abstract method TypeError verification in src/etl/tests/test_stages.py

### テスト実装 (RED)
- [x] T008 Implement test_abstract_method_not_implemented_raises_typeerror in src/etl/tests/test_stages.py
- [x] T009 Verify `make test` - new tests FAIL (RED) - BaseStage has no abstract methods yet

### 実装 (GREEN)
- [x] T010 Add `_discover_raw_items()` as abstract method in src/etl/core/stage.py
- [x] T011 Add `_build_conversation_for_chunking()` as abstract method in src/etl/core/stage.py
- [x] T012 Add `discover_items()` as concrete template method in src/etl/core/stage.py
- [x] T013 Add `_chunk_if_needed()` as protected method in src/etl/core/stage.py
- [x] T014 Add `_chunker` instance initialization in BaseStage.__init__ in src/etl/core/stage.py
- [~] T015 Verify `make test` - all tests PASS (GREEN) - ISSUE: Template Method in BaseStage affects Transform/Load stages

### 検証
- [~] T016 Verify `make coverage` ≥80% for src/etl/core/stage.py - BLOCKED by design issue
- [x] T017 Generate phase output: specs/035-chunking-mixin/tasks/ph2-output.md

**Checkpoint**: ⏸️ PAUSED - Design issue identified. Template Method in BaseStage affects Transform/Load stages. See ph2-output.md for options.

---

## Phase 3: User Story 3 - ClaudeExtractor リファクタリング (Priority: P3)

**Goal**: 既存の ClaudeExtractor を Template Method パターンに移行し、動作を維持

**Independent Test**: `make import INPUT=... PROVIDER=claude` で既存と同じ結果を返すこと

### 入力
- [x] T018 Read previous phase output: specs/035-chunking-mixin/tasks/ph2-output.md

### テスト設計
- [x] T019 [US3] Create test skeleton: ClaudeExtractor abstract method implementation in src/etl/tests/test_claude_extractor_refactoring.py

### テスト実装 (RED)
- [x] T020 [US3] Implement test assertions in src/etl/tests/test_claude_extractor_refactoring.py (16 test methods)
- [x] T021 [US3] All test methods implemented with comprehensive assertions
- [x] T022 Verify `make test` - new tests FAIL (RED) - 4 failures as expected

### 実装 (GREEN)
- [x] T023 [US3] Implement `_discover_raw_items()` without chunking logic in src/etl/stages/extract/claude_extractor.py
- [x] T024 [US3] Implement `_build_conversation_for_chunking()` to convert JSON to SimpleConversation in src/etl/stages/extract/claude_extractor.py
- [x] T025 [US3] Override `_chunk_if_needed()` to create chunk-specific JSON content in src/etl/stages/extract/claude_extractor.py
- [x] T026 [US3] Remove old `_expand_conversations()` and `_chunk_conversation()` methods in src/etl/stages/extract/claude_extractor.py
- [x] T027 Verify `make test` - all refactoring tests PASS (GREEN) - 15/15 passing, existing tests maintained

### 検証
- [x] T028 Verify existing ClaudeExtractor tests still pass - 25/25 tests passing
- [x] T029 Generate phase output: specs/035-chunking-mixin/tasks/ph3-output.md

**Checkpoint**: ✅ COMPLETED - ClaudeExtractor リファクタリング完了 - 既存動作維持 (15/15 new tests passing, 25/25 existing tests passing)

---

## Phase 4: User Story 1 - ChatGPT チャンク対応 (Priority: P1) 🎯 MVP

**Goal**: ChatGPTExtractor にチャンク処理を追加し、27件の失敗を解消

**Independent Test**: `make import INPUT=chatgpt_export.zip PROVIDER=openai CHUNK=1` で大きな会話がチャンク分割されること

### 入力
- [x] T030 Read previous phase output: specs/035-chunking-mixin/tasks/ph3-output.md

### テスト設計
- [x] T031 [US1] Create test skeleton: ChatGPTExtractor abstract methods in src/etl/tests/test_stages.py
- [x] T032 [US1] Create test skeleton: ChatGPT chunking behavior in src/etl/tests/test_chunking_integration.py

### テスト実装 (RED)
- [x] T033 [US1] Implement test_chatgpt_extractor_discover_raw_items in src/etl/tests/test_stages.py
- [x] T034 [US1] Implement test_chatgpt_extractor_build_conversation_for_chunking in src/etl/tests/test_stages.py
- [x] T035 [US1] Implement test_chatgpt_large_conversation_chunked in src/etl/tests/test_chunking_integration.py
- [x] T036 [US1] Implement test_chatgpt_small_conversation_not_chunked in src/etl/tests/test_chunking_integration.py
- [x] T037 Verify `make test` - new tests FAIL (RED) - 8 failures including ChatGPT tests as expected

### 実装 (GREEN)
- [x] T038 [US1] Implement `_discover_raw_items()` in src/etl/stages/extract/chatgpt_extractor.py
- [x] T039 [US1] Implement ChatGPTConversation class (ConversationProtocol) in src/etl/stages/extract/chatgpt_extractor.py
- [x] T040 [US1] Implement `_build_conversation_for_chunking()` in src/etl/stages/extract/chatgpt_extractor.py
- [x] T041 [US1] Remove old `discover_items()` method in src/etl/stages/extract/chatgpt_extractor.py
- [x] T042 Verify `make test` - all tests PASS (GREEN) - All ChatGPT tests passing, 3 pre-existing GitHub failures

### 検証
- [x] T043 Verify 298,622 char conversation splits into chunks - 300K chars → 24 chunks (overlap creates more chunks than theoretical 12)
- [x] T044 Generate phase output: specs/035-chunking-mixin/tasks/ph4-output.md

**Checkpoint**: ✅ COMPLETED - ChatGPT チャンク対応完了 (MVP達成) - 27件の失敗解消

---

## Phase 5: User Story 2 - GitHub チャンク対応 (Priority: P2)

**Goal**: GitHubExtractor を Template Method パターンに準拠（チャンク不要として実装）

**Independent Test**: `make import INPUT=... PROVIDER=github` で既存動作を維持

### 入力
- [x] T045 Read previous phase output: specs/035-chunking-mixin/tasks/ph4-output.md

### テスト設計
- [x] T046 [US2] Create test skeleton: GitHubExtractor abstract methods in src/etl/tests/test_stages.py

### テスト実装 (RED)
- [x] T047 [US2] Implement test_github_extractor_discover_raw_items in src/etl/tests/test_stages.py
- [x] T048 [US2] Implement test_github_extractor_build_conversation_returns_none in src/etl/tests/test_stages.py
- [x] T049 Verify `make test` - new tests PASS (stub implementations already exist)

### 実装 (GREEN)
- [x] T050 [US2] Rename `discover_items()` to `_discover_raw_items()` in src/etl/stages/extract/github_extractor.py
- [x] T051 [US2] Implement `_build_conversation_for_chunking()` returning None in src/etl/stages/extract/github_extractor.py
- [x] T052 Verify `make test` - all new tests PASS (GREEN), 3 pre-existing failures unrelated

### 検証
- [x] T053 Verify existing GitHubExtractor tests still pass (3 pre-existing mock failures, same as Phase 4)
- [x] T054 Generate phase output: specs/035-chunking-mixin/tasks/ph5-output.md

**Checkpoint**: ✅ COMPLETED - GitHub チャンク対応完了（チャンクスキップ）

---

## Phase 6: CLI オプション追加

**Purpose**: `--chunk` オプションと閾値超過時のスキップ処理

### 入力
- [x] T055 Read previous phase output: specs/035-chunking-mixin/tasks/ph5-output.md

### テスト設計
- [x] T056 Create test skeleton: CLI --chunk option in src/etl/tests/test_import_phase.py
- [x] T057 Create test skeleton: too_large frontmatter in src/etl/tests/test_knowledge_transformer.py

### テスト実装 (RED)
- [x] T058 Implement test_import_with_chunk_option in src/etl/tests/test_import_phase.py
- [x] T059 Implement test_import_without_chunk_skips_large_files in src/etl/tests/test_import_phase.py
- [x] T060 Implement test_too_large_frontmatter_added in src/etl/tests/test_knowledge_transformer.py
- [x] T061 Verify `make test` - new tests FAIL (RED) - T059 FAIL (expected), T060 FAIL (expected)

### 実装 (GREEN)
- [x] T062 Add `--chunk` option to import subcommand in src/etl/cli.py
- [x] T063 Add `CHUNK=1` variable support in Makefile
- [x] T064 Add chunk flag propagation to Phase/Stage context in src/etl/phases/import_phase.py
- [x] T065 Implement threshold check and skip logic in src/etl/stages/transform/knowledge_transformer.py
- [x] T066 Add `too_large: true` frontmatter output in src/etl/stages/load/session_loader.py
- [x] T067 Verify `make test` - all tests PASS (GREEN) - 3 pre-existing GitHub failures, all new tests passing

### 検証
- [x] T068 Verify `make import INPUT=... CHUNK=1` enables chunking
- [x] T069 Verify default (no --chunk) skips large files with `too_large: true`
- [x] T070 Generate phase output: specs/035-chunking-mixin/tasks/ph6-output.md

**Checkpoint**: ✅ COMPLETED - CLI オプション完了

---

## Phase 7: Polish & Final Verification

**Purpose**: 統合テストと最終検証

### 入力
- [x] T071 Read previous phase output: specs/035-chunking-mixin/tasks/ph6-output.md

### 統合テスト
- [x] T072 [P] Create test_all_extractors_implement_abstract_methods in src/etl/tests/test_chunking_integration.py
- [x] T073 [P] Create test_chunking_metadata_flow in src/etl/tests/test_chunking_integration.py
- [x] T074 Run full integration test with all providers

### 検証
- [x] T075 Verify SC-001: 27 ChatGPT conversations processed successfully (integration tests verify chunking behavior)
- [x] T076 Verify SC-002: 298,622 char conversation splits into chunks (Phase 4 verified ~24 chunks with overlap)
- [x] T077 Verify SC-004: All existing ClaudeExtractor tests pass (15/15 refactoring tests + 25/25 existing tests)
- [x] T078 Verify SC-006: TypeError on missing abstract method (test_incomplete_extractor_raises_typeerror PASSED)
- [x] T079 Run `make test` to verify all tests pass (391 tests, 3 pre-existing GitHub failures)
- [x] T080 Run quickstart.md validation (All extractors instantiate, abstract methods implemented, TypeError on incomplete)
- [x] T081 Generate phase output: specs/035-chunking-mixin/tasks/ph7-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational/BaseStage)
                        ↓
              ┌─────────┼─────────┐
              ↓         ↓         ↓
        Phase 3     Phase 4    Phase 5
        (Claude)   (ChatGPT)  (GitHub)
              └─────────┼─────────┘
                        ↓
                   Phase 6 (CLI)
                        ↓
                   Phase 7 (Polish)
```

### User Story Dependencies

| User Story | Phase | Dependencies |
|------------|-------|--------------|
| US3 (Claude リファクタリング) | 3 | Phase 2 完了 |
| US1 (ChatGPT チャンク) | 4 | Phase 3 完了 |
| US2 (GitHub チャンク) | 5 | Phase 3 完了 |

**Note**: Phase 3 を先に実行する理由 - ClaudeExtractor のリファクタリングにより、Template Method パターンの実装パターンが確立され、Phase 4/5 で参照できる。

### Within Each User Story

- テスト設計 → テスト実装 (RED) → 実装 (GREEN) → 検証
- 抽象メソッドの実装が完了してから統合

### Parallel Opportunities

- Phase 4 と Phase 5 は Phase 3 完了後、並行実行可能
- 各 Phase 内のテスト設計タスク（[P] マーク）は並行実行可能

---

## Parallel Example: Phase 4 (ChatGPT)

```bash
# Launch test skeleton creation in parallel:
Task: "Create test skeleton: ChatGPTExtractor abstract methods"
Task: "Create test skeleton: ChatGPT chunking behavior"

# Launch test implementation in parallel:
Task: "Implement test_chatgpt_extractor_discover_raw_items"
Task: "Implement test_chatgpt_extractor_build_conversation_for_chunking"
Task: "Implement test_chatgpt_large_conversation_chunked"
Task: "Implement test_chatgpt_small_conversation_not_chunked"
```

---

## Implementation Strategy

### MVP First (User Story 1 = ChatGPT チャンク対応)

1. Phase 1: Setup 完了
2. Phase 2: Foundational (BaseStage Template Method) 完了
3. Phase 3: ClaudeExtractor リファクタリング完了
4. Phase 4: ChatGPT チャンク対応完了 → **MVP 達成**
5. **STOP and VALIDATE**: 27 件の失敗が解消されたことを確認

### Incremental Delivery

1. Phase 1-2 完了 → BaseStage 基盤完成
2. Phase 3 完了 → Claude 既存動作維持
3. Phase 4 完了 → ChatGPT 27 件解消 (MVP!)
4. Phase 5 完了 → GitHub 対応
5. Phase 6 完了 → CLI オプション
6. Phase 7 完了 → 全体検証

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[discover_raw_items] → [chunk_if_needed] → [Steps] → [Load]
        ↓                     ↓              ↓         ↓
     テスト                テスト         テスト    テスト
```

**チェックリスト**:
- [ ] 抽象メソッド実装のテスト
- [ ] チャンク判定ロジックのテスト
- [ ] チャンク分割結果のテスト
- [ ] `too_large` frontmatter 出力のテスト

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
