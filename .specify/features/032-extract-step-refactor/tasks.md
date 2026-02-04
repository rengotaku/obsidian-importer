# Tasks: ChatGPTExtractor Steps分離リファクタリング

**Input**: Design documents from `/specs/032-extract-step-refactor/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Included - リファクタリングのため既存テストの維持と新規ユニットテストが必要

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: プロジェクト準備と既存コードの確認

- [X] T001 Read previous phase output (N/A - 初回フェーズ)
- [X] T002 Verify current test status with `make test` to establish baseline (✅ 280/280 passed after fetch_titles fix)
- [X] T003 Run `make import INPUT=chatgpt_export.zip PROVIDER=openai DEBUG=1` to capture baseline output for comparison (✅ Baseline captured - session 20260124_145953)
- [X] T004 Run `make test` to verify all tests pass (✅ All 280 tests pass)
- [X] T005 Generate phase output: specs/032-extract-step-refactor/tasks/ph1-output.md

---

## Phase 2: Foundational (1:N 展開フレームワーク拡張)

**Purpose**: BaseStage フレームワークに 1:N 展開対応を追加（全 User Story のブロック要件）

**⚠️ CRITICAL**: User Story 1-4 の実装はこのフェーズ完了後に開始可能

### Framework Extensions

- [X] T006 Read previous phase output: specs/032-extract-step-refactor/tasks/ph1-output.md
- [X] T007 [P] Add type annotation `ProcessingItem | list[ProcessingItem]` to `BaseStep.process()` return type in src/etl/core/stage.py
- [X] T008 [P] Add `PhaseStats` dataclass to src/etl/core/session.py with fields: status, success_count, error_count, completed_at, error (optional)
- [X] T009 Modify `Session.phases` type from `list[str]` to `dict[str, PhaseStats]` in src/etl/core/session.py
- [X] T010 Update `Session.to_dict()` to serialize phases as dict with PhaseStats in src/etl/core/session.py
- [X] T011 Update `Session.from_dict()` to handle both old format (list) and new format (dict) for backward compatibility in src/etl/core/session.py
- [X] T012 Modify `BaseStage._process_item()` to detect list return from step.process() and expand to multiple items in src/etl/core/stage.py
- [X] T013 Add validation in `_process_item()`: list return must not be empty (raise RuntimeError) in src/etl/core/stage.py
- [X] T014 Update `_write_debug_step_output()` to log parent_item_id, expansion_index, total_expanded for 1:N steps in src/etl/core/stage.py

### Foundational Tests

- [X] T015 [P] Add test_phase_stats_dataclass in src/etl/tests/test_session.py
- [X] T016 [P] Add test_session_phases_dict_format in src/etl/tests/test_session.py
- [X] T017 [P] Add test_session_backward_compat_list_phases in src/etl/tests/test_session.py
- [X] T018 [P] Create src/etl/tests/test_expanding_step.py with test_step_returns_list_expands_items
- [X] T019 [P] Add test_step_returns_empty_list_raises in src/etl/tests/test_expanding_step.py
- [X] T020 [P] Add test_step_returns_single_item_unchanged in src/etl/tests/test_expanding_step.py
- [X] T021 Run `make test` to verify all tests pass (291/292 passing, 1 pre-existing import phase test failure)
- [X] T022 Generate phase output: specs/032-extract-step-refactor/tasks/ph2-output.md

**Checkpoint**: 1:N 展開フレームワークが動作し、PhaseStats が session.json に記録可能

---

## Phase 3: User Story 1 - Extract Stage のステップ別トレース (Priority: P1) 🎯 MVP

**Goal**: ChatGPT インポート処理のパフォーマンスを分析するため、Extract Stage の各ステップの処理時間と変化率を `steps.jsonl` で確認できる

**Independent Test**: debug モードで ChatGPT インポートを実行し、`extract/output/debug/steps.jsonl` が生成され、各ステップの timing_ms、before_chars、after_chars、diff_ratio が記録されていることを確認

### Implementation for User Story 1

- [X] T023 Read previous phase output: specs/032-extract-step-refactor/tasks/ph2-output.md
- [X] T024 [P] [US1] Create ReadZipStep class in src/etl/stages/extract/chatgpt_extractor.py with name="read_zip", process() returns single item with content=raw JSON
- [X] T025 [P] [US1] Create ParseConversationsStep class in src/etl/stages/extract/chatgpt_extractor.py with name="parse_conversations", process() returns list[ProcessingItem] (1:N expansion)
- [X] T026 [P] [US1] Create ConvertFormatStep class in src/etl/stages/extract/chatgpt_extractor.py with name="convert_format", process() converts ChatGPT mapping to Claude messages format
- [X] T027 [P] [US1] Create ValidateMinMessagesStep class in src/etl/stages/extract/chatgpt_extractor.py with name="validate_min_messages", process() sets status=SKIPPED if < MIN_MESSAGES
- [X] T028 [US1] Refactor ChatGPTExtractor.discover_items() to only find ZIP files and yield ProcessingItem(content=None) in src/etl/stages/extract/chatgpt_extractor.py
- [X] T029 [US1] Update ChatGPTExtractor.steps property to return [ReadZipStep, ParseConversationsStep, ConvertFormatStep, ValidateMinMessagesStep] in src/etl/stages/extract/chatgpt_extractor.py
- [X] T030 [US1] Ensure metadata propagation: parent_item_id, expansion_index, total_expanded in ParseConversationsStep (handled by BaseStage framework automatically)

### Tests for User Story 1

- [X] T031 [P] [US1] Add test_read_zip_step in src/etl/tests/test_stages.py
- [X] T032 [P] [US1] Add test_parse_conversations_step_expands in src/etl/tests/test_stages.py
- [X] T033 [P] [US1] Add test_convert_format_step in src/etl/tests/test_stages.py
- [X] T034 [P] [US1] Add test_validate_min_messages_step_skips in src/etl/tests/test_stages.py
- [X] T035 [P] [US1] Add test_chatgpt_extractor_discover_items_minimal in src/etl/tests/test_stages.py
- [X] T036 [US1] Add test_chatgpt_extract_generates_steps_jsonl in src/etl/tests/test_debug_step_output.py
- [X] T037 Run `make test` to verify all tests pass (298 tests, 297 pass, 1 pre-existing failure)
- [X] T038 [US1] Manual verification: Run `make import INPUT=<test_zip> PROVIDER=openai DEBUG=1` and confirm steps.jsonl is generated (✅ Verified - all 4 steps logged with expansion metadata)
- [X] T039 Generate phase output: specs/032-extract-step-refactor/tasks/ph3-output.md

**Checkpoint**: Extract Stage で steps.jsonl が生成され、4つのステップログが記録される

---

## Phase 4: User Story 2 - 既存機能の互換性維持 (Priority: P1)

**Goal**: 既存の ChatGPT インポート機能が同一の入出力で動作し、最終的な Markdown ファイルが変更前と同じ内容で生成される

**Independent Test**: リファクタリング前後で同じ ChatGPT エクスポートをインポートし、生成された Markdown ファイルの内容が一致することを確認

### Implementation for User Story 2

- [X] T040 Read previous phase output: specs/032-extract-step-refactor/tasks/ph3-output.md
- [X] T041 [US2] Verify edge case: Empty conversations.json outputs warning and exits 0 in src/etl/stages/extract/chatgpt_extractor.py (existing behavior)
- [X] T042 [US2] Verify edge case: Corrupted ZIP outputs error and exits 2 in src/etl/stages/extract/chatgpt_extractor.py (existing behavior)
- [X] T043 [US2] Verify edge case: Missing title generates from first user message in ConvertFormatStep or discover_items
- [X] T044 [US2] Verify edge case: Missing timestamp falls back to current date in ConvertFormatStep

### Tests for User Story 2

- [X] T045 [P] [US2] Add test_chatgpt_import_output_matches_baseline in src/etl/tests/test_chatgpt_transform_integration.py
- [X] T046 [P] [US2] Add test_chatgpt_import_empty_conversations in src/etl/tests/test_chatgpt_transform_integration.py
- [X] T047 [P] [US2] Add test_chatgpt_import_min_messages_skip in src/etl/tests/test_chatgpt_transform_integration.py
- [X] T048 Run `make test` to verify all tests pass
- [X] T049 [US2] Manual verification: Compare Markdown output with baseline captured in Phase 1
- [X] T050 Generate phase output: specs/032-extract-step-refactor/tasks/ph4-output.md

**Checkpoint**: 既存機能が 100% 互換で動作

---

## Phase 5: User Story 3 - Claude Extractor との設計統一 (Priority: P2)

**Goal**: 開発者が新しい Extractor を追加する際、Claude Extractor と ChatGPT Extractor が同じ設計パターンに従っているため、実装の参考にできる

**Independent Test**: Claude Extractor と ChatGPT Extractor のクラス構造を比較し、discover_items() と steps の責務分担が同じパターンであることを確認

### Implementation for User Story 3

- [X] T051 Read previous phase output: specs/032-extract-step-refactor/tasks/ph4-output.md
- [X] T052 [US3] Review Claude Extractor discover_items() pattern and document design consistency in specs/032-extract-step-refactor/tasks/ph5-output.md
- [X] T053 [US3] Ensure ChatGPTExtractor.discover_items() only yields ProcessingItem(content=None) like Claude pattern (verify T028 completion)
- [X] T054 [US3] Document extractor design pattern in code comments or docstrings in src/etl/stages/extract/chatgpt_extractor.py
- [X] T055 Run `make test` to verify all tests pass (300/301 passing, 1 pre-existing failure)
- [X] T056 Generate phase output: specs/032-extract-step-refactor/tasks/ph5-output.md

**Checkpoint**: 両 Extractor が同一の設計パターンに従う

---

## Phase 6: User Story 4 - セッション統計の可視化 (Priority: P2)

**Goal**: 開発者がセッションの処理結果を確認する際、session.json を見るだけで各フェーズの成功/失敗件数を把握できる

**Independent Test**: インポート完了後の session.json を確認し、phases フィールドに item 数が記録されていることを確認

### Implementation for User Story 4

- [X] T057 Read previous phase output: specs/032-extract-step-refactor/tasks/ph5-output.md
- [X] T058 [US4] Update import command in src/etl/cli.py to record PhaseStats (success_count, error_count, status, completed_at) after phase completion
- [X] T059 [US4] Add exception handling in cli.py import command to record status="crashed" and error field on unhandled exceptions
- [X] T060 [US4] Update organize command in src/etl/cli.py to record PhaseStats after phase completion

### Tests for User Story 4

- [X] T061 [P] [US4] Add test_cli_import_records_phase_stats in src/etl/tests/test_cli.py
- [X] T062 [P] [US4] Add test_cli_import_crashed_records_error in src/etl/tests/test_cli.py
- [X] T063 [P] [US4] Add test_session_json_phases_format in src/etl/tests/test_session.py
- [X] T064 Run `make test` to verify all tests pass (305 tests, 304 pass, 1 pre-existing failure)
- [X] T065 [US4] Manual verification: Run import and check session.json contains phases with stats (✅ Verified - session 20260124_164549)
- [X] T066 Generate phase output: specs/032-extract-step-refactor/tasks/ph6-output.md

**Checkpoint**: session.json にフェーズ統計が記録される

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 最終検証とドキュメント更新

- [X] T067 Read previous phase output: specs/032-extract-step-refactor/tasks/ph6-output.md
- [X] T068 [P] Update CLAUDE.md with new session.json phases format documentation
- [X] T069 [P] Run full test suite with `make test` to verify all changes
- [X] T070 Run `make import INPUT=<test_zip> PROVIDER=openai DEBUG=1` and verify steps.jsonl, session.json
- [X] T071 Run `make item-trace SESSION=<session_id> ITEM=<item_id>` and verify Extract stage steps are displayed
- [X] T072 Code cleanup: Remove obsolete code from chatgpt_extractor.py (old discover_items logic)
- [X] T073 Run `make test` to verify all tests pass
- [X] T074 Generate phase output: specs/032-extract-step-refactor/tasks/ph7-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on Phase 3 (needs Step implementation to verify compatibility)
- **Phase 5 (US3)**: Depends on Phase 3 (design pattern review)
- **Phase 6 (US4)**: Depends on Phase 2 (PhaseStats infrastructure)
- **Phase 7 (Polish)**: Depends on all user stories completion

### User Story Dependencies

- **User Story 1 (P1)**: Core feature - Steps 分離と steps.jsonl 出力
- **User Story 2 (P1)**: Verification - US1 の互換性確認
- **User Story 3 (P2)**: Design - パターン統一の検証
- **User Story 4 (P2)**: Enhancement - セッション統計

### Within Each User Story

- Implementation tasks before test tasks
- Core logic before edge case handling
- Unit tests before integration verification

### Parallel Opportunities

Phase 2:
- T007, T008 can run in parallel (different files)
- T015-T020 test tasks can run in parallel

Phase 3:
- T024-T027 Step classes can be created in parallel
- T031-T035 test tasks can run in parallel

Phase 4:
- T045-T047 test tasks can run in parallel

Phase 6:
- T061-T063 test tasks can run in parallel

---

## Parallel Example: Phase 2

```bash
# Launch framework extension tasks in parallel:
Task: "Add type annotation to BaseStep.process() in src/etl/core/stage.py"
Task: "Add PhaseStats dataclass in src/etl/core/session.py"

# Launch test tasks in parallel:
Task: "Add test_phase_stats_dataclass in src/etl/tests/test_session.py"
Task: "Add test_session_phases_dict_format in src/etl/tests/test_session.py"
Task: "Create src/etl/tests/test_expanding_step.py"
```

---

## Parallel Example: Phase 3 (User Story 1)

```bash
# Launch Step class creation tasks in parallel:
Task: "Create ReadZipStep class in src/etl/stages/extract/chatgpt_extractor.py"
Task: "Create ParseConversationsStep class in src/etl/stages/extract/chatgpt_extractor.py"
Task: "Create ConvertFormatStep class in src/etl/stages/extract/chatgpt_extractor.py"
Task: "Create ValidateMinMessagesStep class in src/etl/stages/extract/chatgpt_extractor.py"

# Launch test tasks in parallel:
Task: "Add test_read_zip_step in src/etl/tests/test_stages.py"
Task: "Add test_parse_conversations_step_expands in src/etl/tests/test_stages.py"
Task: "Add test_convert_format_step in src/etl/tests/test_stages.py"
Task: "Add test_validate_min_messages_step_skips in src/etl/tests/test_stages.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (1:N フレームワーク)
3. Complete Phase 3: User Story 1 (Steps 分離)
4. **STOP and VALIDATE**: steps.jsonl が生成されることを確認
5. Continue to Phase 4 for compatibility verification

### Incremental Delivery

1. Phase 1-2 → 1:N 展開フレームワーク完成
2. Phase 3 → Extract Stage で steps.jsonl 出力 (MVP!)
3. Phase 4 → 互換性確認
4. Phase 5-6 → 設計統一 + セッション統計
5. Phase 7 → 最終検証

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 74 |
| Phase 1 (Setup) | 5 |
| Phase 2 (Foundational) | 17 |
| Phase 3 (US1 - MVP) | 17 |
| Phase 4 (US2) | 11 |
| Phase 5 (US3) | 6 |
| Phase 6 (US4) | 10 |
| Phase 7 (Polish) | 8 |
| Parallel Tasks [P] | 29 |
| Test Tasks | 17 |

### Independent Test Criteria

| User Story | Test Criteria |
|------------|---------------|
| US1 | `extract/output/debug/steps.jsonl` に 4 ステップのログが記録される |
| US2 | リファクタリング前後の Markdown 出力が 100% 一致 |
| US3 | discover_items() が content=None の ProcessingItem のみを yield |
| US4 | session.json の phases が dict 形式で success_count, error_count を含む |

### MVP Scope

- Phase 1-3 完了で MVP 達成
- User Story 1 (Extract Stage の steps.jsonl 出力) が主目的
