# Tasks: Import Session Log

**Input**: Design documents from `/specs/017-import-session-log/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/session-logger.md, quickstart.md

**Tests**: ユニットテストを含む（既存テストフレームワーク pytest）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

```text
.dev/scripts/
├── normalizer/io/session.py       # 既存: プレフィックス引数追加
├── llm_import/
│   ├── cli.py                     # 変更: セッションログ統合
│   └── common/session_logger.py   # 新規: セッションログラッパー
└── tests/llm_import/
    └── test_session_logger.py     # 新規: ユニットテスト
```

---

## Phase 1: Setup

**Purpose**: 既存コードの確認と新規ファイル作成準備

- [x] T001 Verify normalizer/io/session.py functions are stable in .dev/scripts/normalizer/io/session.py
- [x] T002 [P] Create common/ directory in .dev/scripts/llm_import/common/
- [x] T003 [P] Create tests/llm_import/ directory if not exists in .dev/scripts/tests/llm_import/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 既存 normalizer/io/session.py にプレフィックス機能を追加

**⚠️ CRITICAL**: US1〜US3 すべてがこの変更に依存

- [x] T004 Add `prefix` parameter to `create_new_session()` in .dev/scripts/normalizer/io/session.py
- [x] T005 Update `create_new_session()` to generate `{prefix}_{YYYYMMDD_HHMMSS}` format in .dev/scripts/normalizer/io/session.py
- [x] T006 [P] Add test for `create_new_session(prefix="import")` in .dev/scripts/tests/llm_import/test_session_prefix.py

**Checkpoint**: `normalizer/io/session.py` がプレフィックス付きセッション作成をサポート

---

## Phase 3: User Story 1 - 処理進捗の可視化 (Priority: P1) 🎯 MVP

**Goal**: コンソールにプログレスバーと Phase 別結果を表示し、`execution.log` に同内容を記録

**Independent Test**: 10件以上の会話を処理し、セッションディレクトリ内のログファイルで進捗を確認できる

### Tests for User Story 1

- [x] T007 [P] [US1] Create test_session_logger.py with basic tests in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T008 [P] [US1] Add test for SessionLogger constructor (provider, total_files, prefix) in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T009 [P] [US1] Add test for start_session() creates session directory and files in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T010 [P] [US1] Add test for log() writes to execution.log in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T011 [P] [US1] Add test for log_progress() outputs progress bar format in .dev/scripts/tests/llm_import/test_session_logger.py

### Implementation for User Story 1

- [x] T012 [US1] Create SessionLogger class skeleton in .dev/scripts/llm_import/common/session_logger.py
- [x] T013 [US1] Implement SessionLogger.__init__() with provider, total_files, prefix in .dev/scripts/llm_import/common/session_logger.py
- [x] T014 [US1] Implement SessionLogger.start_session() to create directory and session.json in .dev/scripts/llm_import/common/session_logger.py
- [x] T015 [US1] Implement SessionLogger.log() for dual output (console + file) in .dev/scripts/llm_import/common/session_logger.py
- [x] T016 [US1] Implement SessionLogger.log_progress() with progress bar in .dev/scripts/llm_import/common/session_logger.py
- [x] T017 [US1] Add graceful degradation (try/except) for all I/O operations in .dev/scripts/llm_import/common/session_logger.py
- [x] T018 [US1] Integrate SessionLogger into cmd_process() in .dev/scripts/llm_import/cli.py
- [x] T019 [US1] Add session start message and header to cmd_process() in .dev/scripts/llm_import/cli.py
- [x] T020 [US1] Call log_progress() for each conversation in processing loop in .dev/scripts/llm_import/cli.py

**Checkpoint**: `llm_import` 実行時にプログレスバーが表示され、`execution.log` に同内容が記録される

---

## Phase 4: User Story 2 - ステージ別処理詳細の記録 (Priority: P2)

**Goal**: `pipeline_stages.jsonl` に Phase 1/Phase 2 の処理時間を記録

**Independent Test**: 5件の会話を処理し、`pipeline_stages.jsonl` に各ステージの処理時間が記録されていることを確認

### Tests for User Story 2

- [x] T021 [P] [US2] Add test for log_stage() writes JSONL format in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T022 [P] [US2] Add test for StageRecord contains required fields (timestamp, filename, stage, executed, timing_ms) in .dev/scripts/tests/llm_import/test_session_logger.py

### Implementation for User Story 2

- [x] T023 [US2] Implement SessionLogger.log_stage() in .dev/scripts/llm_import/common/session_logger.py
- [x] T024 [US2] Add timing measurement for Phase 1 in cmd_process() in .dev/scripts/llm_import/cli.py
- [x] T025 [US2] Add timing measurement for Phase 2 in cmd_process() in .dev/scripts/llm_import/cli.py
- [x] T026 [US2] Call log_stage() after each phase completion in .dev/scripts/llm_import/cli.py

**Checkpoint**: `pipeline_stages.jsonl` に Phase 1/Phase 2 の処理時間が JSONL 形式で記録される

---

## Phase 5: User Story 3 - 状態ファイルの分離管理 (Priority: P3)

**Goal**: `processed.json`, `pending.json`, `errors.json` に状態を分離記録し、`results.json` に最終サマリーを出力

**Independent Test**: 一部エラーを含む処理を実行し、各状態ファイルに適切に分類されていることを確認

### Tests for User Story 3

- [x] T027 [P] [US3] Add test for add_processed() updates internal list in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T028 [P] [US3] Add test for add_error() updates internal list in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T029 [P] [US3] Add test for add_pending() updates internal list in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T030 [P] [US3] Add test for finalize() writes all state files in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T031 [P] [US3] Add test for finalize() writes results.json with correct counts in .dev/scripts/tests/llm_import/test_session_logger.py

### Implementation for User Story 3

- [x] T032 [US3] Add internal lists for processed, errors, pending in SessionLogger in .dev/scripts/llm_import/common/session_logger.py
- [x] T033 [US3] Implement SessionLogger.add_processed() in .dev/scripts/llm_import/common/session_logger.py
- [x] T034 [US3] Implement SessionLogger.add_error() in .dev/scripts/llm_import/common/session_logger.py
- [x] T035 [US3] Implement SessionLogger.add_pending() in .dev/scripts/llm_import/common/session_logger.py
- [x] T036 [US3] Implement SessionLogger.finalize() to write state files in .dev/scripts/llm_import/common/session_logger.py
- [x] T037 [US3] Implement rich summary display in finalize() in .dev/scripts/llm_import/common/session_logger.py
- [x] T038 [US3] Call add_processed()/add_error()/add_pending() in processing loop in .dev/scripts/llm_import/cli.py
- [x] T039 [US3] Call finalize() at end of cmd_process() in .dev/scripts/llm_import/cli.py

**Checkpoint**: 処理完了後に `processed.json`, `errors.json`, `pending.json`, `results.json` が正しく出力される

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 統合テスト、エッジケース対応、ドキュメント

- [x] T040 [P] Add integration test: full processing with session logging in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T041 [P] Add edge case test: session directory creation failure in .dev/scripts/tests/llm_import/test_session_logger.py
- [x] T042 Verify --status command still works with new session logging in .dev/scripts/llm_import/cli.py
- [x] T043 Run `make test` to ensure all tests pass
- [ ] T044 Run quickstart.md validation (manual test with sample data)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T004-T006)
- **User Story 2 (Phase 4)**: Depends on US1 core (T012-T017) for SessionLogger class
- **User Story 3 (Phase 5)**: Depends on US1 core (T012-T017) for SessionLogger class
- **Polish (Phase 6)**: Depends on all user stories

### User Story Dependencies

- **User Story 1 (P1)**: 独立実装可能（Foundational 完了後）
- **User Story 2 (P2)**: US1 の SessionLogger クラス基盤を使用するが、独立テスト可能
- **User Story 3 (P3)**: US1 の SessionLogger クラス基盤を使用するが、独立テスト可能

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- SessionLogger メソッド追加 → cli.py 統合 の順

### Parallel Opportunities

- T002, T003: Setup の並列実行可能
- T007-T011: US1 テストの並列実行可能
- T021-T022: US2 テストの並列実行可能
- T027-T031: US3 テストの並列実行可能
- T040, T041: Polish テストの並列実行可能

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: T007 "Create test_session_logger.py with basic tests"
Task: T008 "Add test for SessionLogger constructor"
Task: T009 "Add test for start_session()"
Task: T010 "Add test for log()"
Task: T011 "Add test for log_progress()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T006)
3. Complete Phase 3: User Story 1 (T007-T020)
4. **STOP and VALIDATE**: プログレスバーと execution.log が動作することを確認
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → プレフィックス付きセッション作成が可能
2. User Story 1 → プログレスバー + execution.log（MVP）
3. User Story 2 → pipeline_stages.jsonl 追加（パフォーマンス分析可能）
4. User Story 3 → 状態ファイル分離 + results.json（運用性向上）
5. Each story adds value without breaking previous stories

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[会話処理] → [Phase記録] → [状態更新] → [ファイル出力]
     ↓           ↓            ↓            ↓
   テスト      テスト       テスト       テスト
```

**チェックリスト**:
- [ ] SessionLogger 初期化のテスト (T008)
- [ ] セッションディレクトリ作成のテスト (T009)
- [ ] ログ出力のテスト (T010, T011)
- [ ] ステージ記録のテスト (T021, T022)
- [ ] 状態ファイル書き込みのテスト (T027-T031)
- [ ] 統合テスト (T040)
- [ ] エッジケーステスト (T041)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Graceful degradation: ログ機能エラー時も本処理は継続
- 既存の `.extraction_state.json` は維持（役割が異なる）
- `make test` で全テストを実行
