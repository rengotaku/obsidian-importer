# Tasks: Bonobo & Tenacity ETL Migration

**Input**: Design documents from `/specs/025-bonobo-tenacity-migration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Included - using unittest (標準ライブラリ)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

> **Note**: User Story 2 was originally "Bonobo パイプライン" but research.md determined bonobo is NOT adopted.
> Instead, custom ETL framework is implemented.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Project root**: `src/etl/` for new ETL pipeline
- **Tests**: `src/etl/tests/`
- **Legacy**: `src/converter/scripts/` (to be migrated)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for `src/etl/`

- [x] T001 Create `src/etl/` directory structure per plan.md
- [x] T002 Create `src/etl/__init__.py` with version info
- [x] T003 [P] Create `src/etl/core/__init__.py`
- [x] T004 [P] Create `src/etl/phases/__init__.py`
- [x] T005 [P] Create `src/etl/stages/__init__.py`
- [x] T006 [P] Create `src/etl/stages/extract/__init__.py`
- [x] T007 [P] Create `src/etl/stages/transform/__init__.py`
- [x] T008 [P] Create `src/etl/stages/load/__init__.py`
- [x] T009 [P] Create `src/etl/tests/__init__.py`
- [x] T010 Add tenacity to requirements or ensure it's installed: `pip install tenacity`
- [x] T011 Run `make test` to verify existing tests still pass
- [x] T012 Generate phase output: specs/025-bonobo-tenacity-migration/tasks/ph1-output.md

---

## Phase 2: Foundational (Core Models & Enums)

**Purpose**: Core data structures that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T013 Read previous phase output: specs/025-bonobo-tenacity-migration/tasks/ph1-output.md
- [x] T014 [P] Create status enums (SessionStatus, PhaseStatus, StageStatus, StepStatus, ItemStatus) in `src/etl/core/status.py`
- [x] T015 [P] Create PhaseType enum (IMPORT, ORGANIZE) in `src/etl/core/types.py`
- [x] T016 [P] Create StageType enum (EXTRACT, TRANSFORM, LOAD) in `src/etl/core/types.py`
- [x] T017 Create ProcessingItem dataclass in `src/etl/core/models.py`
- [x] T018 Create StepResult dataclass in `src/etl/core/models.py`
- [x] T019 Create RetryConfig dataclass in `src/etl/core/models.py`
- [x] T020 [P] Create unit tests for enums and dataclasses in `src/etl/tests/test_models.py`
- [x] T021 Run `make test` to verify all tests pass
- [x] T022 Generate phase output: specs/025-bonobo-tenacity-migration/tasks/ph2-output.md

**Checkpoint**: Core models ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Tenacity リトライ機能統一 (Priority: P1) 🎯 MVP

**Goal**: LLM API呼び出しのリトライロジックを tenacity に統一

**Independent Test**: Ollama API呼び出しに tenacity を適用し、一時的な接続エラーからの回復を確認

### Tests for User Story 1

- [x] T023 Read previous phase output: specs/025-bonobo-tenacity-migration/tasks/ph2-output.md
- [x] T024 [P] [US1] Create test for RetryConfig in `src/etl/tests/test_retry.py`
- [x] T025 [P] [US1] Create test for with_retry decorator in `src/etl/tests/test_retry.py`
- [x] T026 [P] [US1] Create test for exponential backoff + jitter behavior in `src/etl/tests/test_retry.py`

### Implementation for User Story 1

- [x] T027 [US1] Implement RetryConfig with tenacity settings in `src/etl/core/retry.py`
- [x] T028 [US1] Implement `with_retry` decorator using tenacity in `src/etl/core/retry.py`
- [x] T029 [US1] Add retry logging callbacks (before_log, after_log) in `src/etl/core/retry.py`
- [x] T030 [US1] Add exception-specific retry conditions in `src/etl/core/retry.py`
- [x] T031 Run `make test` to verify all tests pass
- [x] T032 Generate phase output: specs/025-bonobo-tenacity-migration/tasks/ph3-output.md

**Checkpoint**: Tenacity リトライ機能が動作し、単独テスト可能

---

## Phase 4: User Story 4 - セッション管理とステータス追跡 (Priority: P1)

**Goal**: パイプライン処理の経過を Session フォルダに記録、Step 単位でステータス追跡

**Independent Test**: 単一ファイルをパイプラインで処理し、@session フォルダに正しいステータス JSON 出力を確認

### Tests for User Story 4

- [x] T033 Read previous phase output: specs/025-bonobo-tenacity-migration/tasks/ph3-output.md
- [x] T034 [P] [US4] Create test for Session creation in `src/etl/tests/test_session.py`
- [x] T035 [P] [US4] Create test for session_id format (YYYYMMDD_HHMMSS) in `src/etl/tests/test_session.py`
- [x] T036 [P] [US4] Create test for Phase folder creation in `src/etl/tests/test_phase.py`
- [x] T037 [P] [US4] Create test for Stage folder creation in `src/etl/tests/test_phase.py`
- [x] T038 [P] [US4] Create test for phase.json status tracking in `src/etl/tests/test_phase.py`

### Implementation for User Story 4

- [x] T039 [US4] Implement Session dataclass in `src/etl/core/session.py`
- [x] T040 [US4] Implement SessionManager (create, load, save) in `src/etl/core/session.py`
- [x] T041 [US4] Implement session.json serialization in `src/etl/core/session.py`
- [x] T042 [US4] Implement Phase dataclass in `src/etl/core/phase.py`
- [x] T043 [US4] Implement PhaseManager (folder creation, status tracking) in `src/etl/core/phase.py`
- [x] T044 [US4] Implement phase.json serialization with Step-level status in `src/etl/core/phase.py`
- [x] T045 [US4] Implement Stage dataclass in `src/etl/core/stage.py`
- [x] T046 [US4] Implement Stage folder structure (input/, output/) in `src/etl/core/stage.py`
- [x] T047 [US4] Implement Step dataclass and StepTracker in `src/etl/core/step.py`
- [x] T048 [US4] Implement debug mode logging in `src/etl/core/config.py`
  - FR-016: debug=true → 詳細ログを Stage フォルダに出力
  - FR-017: debug=false → JSON ステータスのみ、詳細ログ抑制
- [x] T049 Run `make test` to verify all tests pass
- [x] T050 Generate phase output: specs/025-bonobo-tenacity-migration/tasks/ph4-output.md

**Checkpoint**: Session 管理が動作し、Phase/Stage/Step フォルダ構造と JSON ステータス追跡が機能

---

## Phase 5: User Story 2 - カスタム ETL パイプライン基盤 (Priority: P2)

**Goal**: カスタム ETL フレームワークで llm_import/normalizer パイプラインを再構築

> Note: bonobo は不採用。シンプルな Stage ベース設計でカスタム実装

**Independent Test**: normalizer の Stage A（分類判定）を Stage として実装し、単一ファイルの分類処理を実行

### Tests for User Story 2

- [x] T051 Read previous phase output: specs/025-bonobo-tenacity-migration/tasks/ph4-output.md
- [x] T052 [P] [US2] Create test for Stage base class in `src/etl/tests/test_stages.py`
- [x] T053 [P] [US2] Create test for import Phase orchestration in `src/etl/tests/test_import_phase.py`
- [x] T054 [P] [US2] Create test for organize Phase orchestration in `src/etl/tests/test_organize_phase.py`

### Implementation for User Story 2

- [x] T055 [US2] Implement Stage abstract base class in `src/etl/core/stage.py`
- [x] T056 [US2] Implement ClaudeExtractor stage in `src/etl/stages/extract/claude_extractor.py`
- [x] T057 [US2] Implement FileExtractor stage in `src/etl/stages/extract/file_extractor.py`
- [x] T058 [US2] Implement KnowledgeTransformer stage in `src/etl/stages/transform/knowledge_transformer.py`
- [x] T059 [US2] Implement NormalizerTransformer stage in `src/etl/stages/transform/normalizer_transformer.py`
- [x] T060 [US2] Implement SessionLoader stage in `src/etl/stages/load/session_loader.py`
- [x] T061 [US2] Implement VaultLoader stage in `src/etl/stages/load/vault_loader.py`
- [x] T062 [US2] Implement ImportPhase orchestration in `src/etl/phases/import_phase.py`
- [x] T063 [US2] Implement OrganizePhase orchestration in `src/etl/phases/organize_phase.py`
- [x] T064 Run `make test` to verify all tests pass
- [x] T065 Generate phase output: specs/025-bonobo-tenacity-migration/tasks/ph5-output.md

**Checkpoint**: カスタム ETL パイプラインが動作し、import/organize Phase が実行可能

---

## Phase 6: CLI Implementation

**Purpose**: CLI エントリポイント実装（contracts/cli.md に基づく）

### Tests for CLI

- [x] T066 Read previous phase output: specs/025-bonobo-tenacity-migration/tasks/ph5-output.md
- [x] T067 [P] Create test for CLI argument parsing in `src/etl/tests/test_cli.py`
- [x] T068 [P] Create test for CLI exit codes in `src/etl/tests/test_cli.py`

### Implementation for CLI

- [x] T069 Implement CLI entry point with argparse in `src/etl/cli.py`
- [x] T070 Implement `import` command (--input required) in `src/etl/cli.py`
- [x] T071 Implement `organize` command (--input required) in `src/etl/cli.py`
- [x] T072 Implement `status` command (--session, --all, --json) in `src/etl/cli.py`
- [x] T073 Implement `retry` command (--session, --phase) in `src/etl/cli.py`
- [x] T074 Implement `clean` command (--days, --dry-run, --force) in `src/etl/cli.py`
- [x] T075 Create `src/etl/__main__.py` for `python -m src.etl` execution
- [x] T076 Run `make test` to verify all tests pass
- [x] T077 Generate phase output: specs/025-bonobo-tenacity-migration/tasks/ph6-output.md

**Checkpoint**: CLI が動作し、全コマンドが実行可能

---

## Phase 7: User Story 3 - 移行フェーズの段階的実施 (Priority: P3)

**Goal**: 既存機能を破壊することなく段階的にライブラリを移行

**Independent Test**: 移行後に既存テストが全て通過することを確認

### Implementation for User Story 3

- [x] T078 Read previous phase output: specs/025-bonobo-tenacity-migration/tasks/ph6-output.md
- [x] T079 [US3] Add backward-compatible Makefile targets in `Makefile`
  - `etl-import`, `etl-organize`, `etl-status`, `etl-retry`, `etl-clean`
  - Aliases: `llm-import: etl-import`, `organize: etl-organize`
- [x] T080 [US3] Update CLAUDE.md with new ETL commands and folder structure
- [x] T081 [US3] Verify existing `src/converter/scripts/llm_import/` tests pass with new retry module
- [x] T082 [US3] Verify existing `src/converter/scripts/normalizer/` tests pass
- [x] T083 Run `make test` to verify ALL tests pass (legacy + new)
- [x] T084 Generate phase output: specs/025-bonobo-tenacity-migration/tasks/ph7-output.md

**Checkpoint**: 新旧両方のテストが通過し、移行パスが確立

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T085 Read previous phase output: specs/025-bonobo-tenacity-migration/tasks/ph7-output.md
- [x] T086 [P] Update quickstart.md with actual implementation details
- [x] T087 [P] Add type hints to all public interfaces in `src/etl/`
- [x] T088 Code cleanup and remove unused imports
- [x] T089 [P] Add docstrings to all public classes and functions
- [x] T089a [P] Implement ContentMetrics.delta anomaly detection in `src/etl/core/models.py`
  - delta <= -0.5: 50%以上圧縮 → review_required フラグ
  - delta >= 2.0: 3倍以上増加 → review_required フラグ
- [x] T090 Run quickstart.md validation (execute example commands)
- [x] T091 Run `make test` to verify all tests pass
- [x] T092 Run `make lint` (if available) for code quality
- [x] T093 Generate phase output: specs/025-bonobo-tenacity-migration/tasks/ph8-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (BLOCKS all user stories)
    ↓
    ├── Phase 3: US1 - Tenacity (P1) ──┐
    │                                   │
    └── Phase 4: US4 - Session (P1) ───┼── Can run in parallel
                                       ↓
                              Phase 5: US2 - ETL Pipeline (P2)
                                       ↓
                              Phase 6: CLI
                                       ↓
                              Phase 7: US3 - Migration (P3)
                                       ↓
                              Phase 8: Polish
```

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (Tenacity) | Phase 2 | US4 |
| US4 (Session) | Phase 2 | US1 |
| US2 (ETL) | US1, US4 | - |
| US3 (Migration) | US2, CLI | - |

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003-T009 can run in parallel (different __init__.py files)

**Phase 2 (Foundational)**:
- T014-T016 can run in parallel (different files)
- T020 tests can run in parallel

**Phase 3 (US1) & Phase 4 (US4)**:
- These phases can run in parallel if separate developers

**Within each phase**:
- Tasks marked [P] can run in parallel

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all enum/type tasks together:
Task: "Create status enums in src/etl/core/status.py"
Task: "Create PhaseType enum in src/etl/core/types.py"
Task: "Create StageType enum in src/etl/core/types.py"

# Then models (depend on enums):
Task: "Create ProcessingItem dataclass in src/etl/core/models.py"
Task: "Create StepResult dataclass in src/etl/core/models.py"
Task: "Create RetryConfig dataclass in src/etl/core/models.py"
```

---

## Implementation Strategy

### MVP First (Phase 1-4)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (Tenacity) - **core retry functionality**
4. Complete Phase 4: US4 (Session) - **status tracking**
5. **STOP and VALIDATE**: Test tenacity + session independently
6. MVP is usable for retry-enabled processing with status tracking

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Tenacity) → Retry works → Validate
3. Add US4 (Session) → Status tracking works → Validate
4. Add US2 (ETL) → Full pipeline works → Validate
5. Add CLI → Commands work → Validate
6. Add US3 (Migration) → Legacy compatibility → Validate
7. Polish → Production ready

---

## Summary

| Phase | Tasks | Parallel Tasks | User Story |
|-------|-------|----------------|------------|
| 1. Setup | T001-T012 | 7 | - |
| 2. Foundational | T013-T022 | 4 | - |
| 3. US1 Tenacity | T023-T032 | 3 | US1 (P1) |
| 4. US4 Session | T033-T050 | 5 | US4 (P1) |
| 5. US2 ETL | T051-T065 | 3 | US2 (P2) |
| 6. CLI | T066-T077 | 2 | - |
| 7. US3 Migration | T078-T084 | 0 | US3 (P3) |
| 8. Polish | T085-T093 + T089a | 4 | - |
| **Total** | **94 tasks** | **28 parallel** | |

**MVP Scope**: Phase 1-4 (US1 + US4) = 50 tasks
**Full Implementation**: All 8 phases = 94 tasks
