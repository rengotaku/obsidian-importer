# Tasks: Ollama パラメーター関数別設定

**Input**: Design documents from `/specs/051-ollama-params-config/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/parameters.yml

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | 関数別パラメーター設定 | P1 | FR-001, FR-002, FR-005 | 各関数が対応するパラメーターを使用 |
| US2 | デフォルト値の適用 | P2 | FR-003 | 未指定パラメーターにデフォルト値適用 |
| US3 | extract_topic の統一実装 | P3 | FR-004 | call_ollama 経由でAPI呼び出し |

## Path Conventions

- **Source**: `src/obsidian_etl/`
- **Tests**: `tests/`
- **Config**: `conf/base/parameters.yml`
- Paths shown below follow single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure) — NO TDD

**Purpose**: Project initialization, existing code review, and change preparation

- [X] T001 Read current implementation in src/obsidian_etl/utils/ollama.py
- [X] T002 [P] Read current implementation in src/obsidian_etl/utils/knowledge_extractor.py
- [X] T003 [P] Read current implementation in src/obsidian_etl/pipelines/organize/nodes.py (_extract_topic_via_llm)
- [X] T004 [P] Read current config in conf/base/parameters.yml
- [X] T005 [P] Read existing tests in tests/pipelines/transform/test_nodes.py
- [X] T006 [P] Read existing tests in tests/pipelines/organize/test_nodes.py
- [X] T007 Update conf/base/parameters.yml with new ollama structure (defaults + functions)
- [X] T008 Run `make test` to verify existing tests still pass
- [X] T009 Generate phase output: specs/051-ollama-params-config/tasks/ph1-output.md

---

## Phase 2: User Story 1 - 関数別パラメーター設定 (Priority: P1) MVP

**Goal**: LLM呼び出し関数ごとに異なるパラメーター（モデル、タイムアウト、出力トークン数など）を設定可能にする

**Independent Test**: `parameters.yml` に関数別設定を記述し、`get_ollama_config()` で正しいパラメーターが返されることを確認

### 入力

- [x] T010 Read previous phase output: specs/051-ollama-params-config/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T011 [P] [US1] Create test file tests/utils/test_ollama_config.py with test class
- [x] T012 [P] [US1] Implement test_get_config_extract_knowledge in tests/utils/test_ollama_config.py
- [x] T013 [P] [US1] Implement test_get_config_translate_summary in tests/utils/test_ollama_config.py
- [x] T014 [P] [US1] Implement test_get_config_extract_topic in tests/utils/test_ollama_config.py
- [x] T015 [P] [US1] Implement test_function_override_priority in tests/utils/test_ollama_config.py (function overrides defaults)
- [x] T016 Verify `make test` FAIL (RED) - new tests should fail
- [x] T017 Generate RED output: specs/051-ollama-params-config/red-tests/ph2-test.md

### 実装 (GREEN)

- [x] T018 Read RED tests: specs/051-ollama-params-config/red-tests/ph2-test.md
- [x] T019 [US1] Create src/obsidian_etl/utils/ollama_config.py with OllamaConfig dataclass
- [x] T020 [US1] Implement get_ollama_config() function in src/obsidian_etl/utils/ollama_config.py
- [x] T021 [US1] Add VALID_FUNCTION_NAMES constant and validation logic in src/obsidian_etl/utils/ollama_config.py
- [x] T022 Verify `make test` PASS (GREEN)

### 検証

- [x] T023 Verify `make test` passes all tests (no regressions)
- [x] T024 Generate phase output: specs/051-ollama-params-config/tasks/ph2-output.md

**Checkpoint**: User Story 1 should be fully functional - get_ollama_config() returns correct config for each function

---

## Phase 3: User Story 2 - デフォルト値の適用 (Priority: P2)

**Goal**: 未指定のパラメーターにはデフォルト値が適用される

**Independent Test**: `parameters.yml` で一部パラメーターのみ設定し、未指定項目にデフォルト値が適用されることを確認

### 入力

- [x] T025 Read previous phase output: specs/051-ollama-params-config/tasks/ph2-output.md

### テスト実装 (RED)

- [x] T026 [P] [US2] Implement test_hardcoded_defaults_applied in tests/utils/test_ollama_config.py
- [x] T027 [P] [US2] Implement test_partial_defaults_merge in tests/utils/test_ollama_config.py
- [x] T028 [P] [US2] Implement test_partial_function_override in tests/utils/test_ollama_config.py
- [x] T029 [P] [US2] Implement test_timeout_validation in tests/utils/test_ollama_config.py (1-600s range)
- [x] T030 [P] [US2] Implement test_temperature_validation in tests/utils/test_ollama_config.py (0.0-2.0 range)
- [x] T031 Verify `make test` FAIL (RED)
- [x] T032 Generate RED output: specs/051-ollama-params-config/red-tests/ph3-test.md

### 実装 (GREEN)

- [x] T033 Read RED tests: specs/051-ollama-params-config/red-tests/ph3-test.md
- [x] T034 [US2] Add HARDCODED_DEFAULTS constant in src/obsidian_etl/utils/ollama_config.py
- [x] T035 [US2] Add validation logic for timeout range (1-600) in get_ollama_config()
- [x] T036 [US2] Add validation logic for temperature range (0.0-2.0) in get_ollama_config()
- [x] T037 [US2] Add legacy params fallback (import.ollama, organize.ollama) in get_ollama_config()
- [x] T038 Verify `make test` PASS (GREEN)

### 検証

- [x] T039 Verify `make test` passes all tests (including regressions from US1)
- [x] T040 Generate phase output: specs/051-ollama-params-config/tasks/ph3-output.md

**Checkpoint**: User Stories 1 AND 2 should both work - partial config with defaults applied

---

## Phase 4: User Story 3 - extract_topic の統一実装 (Priority: P3)

**Goal**: `extract_topic` 関数が `call_ollama` を使用してLLM呼び出しを行う

**Independent Test**: `extract_topic` が `call_ollama` 経由でAPIを呼び出し、パラメーターが適用されることを確認

### 入力

- [ ] T041 Read previous phase output: specs/051-ollama-params-config/tasks/ph3-output.md

### テスト実装 (RED)

- [ ] T042 [P] [US3] Add test_extract_topic_uses_call_ollama in tests/pipelines/organize/test_nodes.py
- [ ] T043 [P] [US3] Add test_extract_topic_uses_config_params in tests/pipelines/organize/test_nodes.py
- [ ] T044 [P] [US3] Add test_extract_topic_with_num_predict_limit in tests/pipelines/organize/test_nodes.py
- [ ] T045 Verify `make test` FAIL (RED)
- [ ] T046 Generate RED output: specs/051-ollama-params-config/red-tests/ph4-test.md

### 実装 (GREEN)

- [ ] T047 Read RED tests: specs/051-ollama-params-config/red-tests/ph4-test.md
- [ ] T048 [US3] Import get_ollama_config and call_ollama in src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T049 [US3] Refactor _extract_topic_via_llm to use call_ollama in src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T050 [US3] Update extract_topic to pass params with new ollama structure
- [ ] T051 Verify `make test` PASS (GREEN)

### 検証

- [ ] T052 Verify `make test` passes all tests (all user stories working)
- [ ] T053 Generate phase output: specs/051-ollama-params-config/tasks/ph4-output.md

**Checkpoint**: All 3 user stories complete - extract_topic uses call_ollama with configured params

---

## Phase 5: Integration - 既存関数への適用 (Foundational)

**Goal**: `extract_knowledge` と `translate_summary` が新しいパラメーター取得方式を使用

**Independent Test**: パイプライン実行時に各関数が `get_ollama_config` 経由でパラメーターを取得

### 入力

- [ ] T054 Read previous phase output: specs/051-ollama-params-config/tasks/ph4-output.md

### テスト実装 (RED)

- [ ] T055 [P] Add test_extract_knowledge_uses_get_ollama_config in tests/pipelines/transform/test_nodes.py
- [ ] T056 [P] Add test_translate_summary_uses_get_ollama_config in tests/pipelines/transform/test_nodes.py
- [ ] T057 Verify `make test` FAIL (RED)
- [ ] T058 Generate RED output: specs/051-ollama-params-config/red-tests/ph5-test.md

### 実装 (GREEN)

- [ ] T059 Read RED tests: specs/051-ollama-params-config/red-tests/ph5-test.md
- [ ] T060 [P] Import get_ollama_config in src/obsidian_etl/utils/knowledge_extractor.py
- [ ] T061 [P] Update extract_knowledge() to use get_ollama_config in src/obsidian_etl/utils/knowledge_extractor.py
- [ ] T062 [P] Update translate_summary() to use get_ollama_config in src/obsidian_etl/utils/knowledge_extractor.py
- [ ] T063 Verify `make test` PASS (GREEN)

### 検証

- [ ] T064 Verify `make test` passes all tests
- [ ] T065 Generate phase output: specs/051-ollama-params-config/tasks/ph5-output.md

**Checkpoint**: All LLM functions use unified parameter retrieval

---

## Phase 6: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: Cleanup, documentation, and final validation

### 入力

- [ ] T066 Read previous phase output: specs/051-ollama-params-config/tasks/ph5-output.md

### 実装

- [ ] T067 [P] Remove deprecated import.ollama and organize.ollama from parameters.yml (if safe)
- [ ] T068 [P] Add docstring to get_ollama_config() explaining merge logic
- [ ] T069 [P] Remove requests import from organize/nodes.py if no longer needed
- [ ] T070 Run quickstart.md validation - verify example configurations work

### 検証

- [ ] T071 Run `make test` to verify all tests pass after cleanup
- [ ] T072 Run `make check` for Python syntax validation
- [ ] T073 Generate phase output: specs/051-ollama-params-config/tasks/ph6-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - メインエージェント直接実行
- **User Stories (Phase 2-4)**: TDD フロー (tdd-generator → phase-executor)
  - US1 (Phase 2) → US2 (Phase 3) → US3 (Phase 4) in priority order
- **Integration (Phase 5)**: Depends on US1+US2 for get_ollama_config()
- **Polish (Phase 6)**: Depends on all phases - phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **入力**: Read previous phase output (context from prior work)
2. **テスト実装 (RED)**: Write tests FIRST → verify `make test` FAIL → generate RED output
3. **実装 (GREEN)**: Read RED tests → implement → verify `make test` PASS
4. **検証**: Confirm no regressions → generate phase output

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-5 (User Stories + Integration)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 6 (Polish)**: phase-executor のみ

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。

- Setup タスクの [P]: 異なるファイルの読み取りで相互依存なし
- RED テストの [P]: 異なるテストメソッドで相互依存なし
- GREEN 実装の [P]: 異なるソースファイルへの書き込みで相互依存なし

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/051-ollama-params-config/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US1 GREEN results)
│   ├── ph3-output.md           # Phase 3 output (US2 GREEN results)
│   ├── ph4-output.md           # Phase 4 output (US3 GREEN results)
│   ├── ph5-output.md           # Phase 5 output (Integration results)
│   └── ph6-output.md           # Phase 6 output (Polish results)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED test results
    ├── ph3-test.md             # Phase 3 RED test results
    ├── ph4-test.md             # Phase 4 RED test results
    └── ph5-test.md             # Phase 5 RED test results
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (existing code review, parameters.yml update)
2. Complete Phase 2: User Story 1 (RED → GREEN → 検証)
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. Verify: `get_ollama_config("extract_knowledge", params)` returns correct config

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
2. Each phase commits: `feat(051): <description>`

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[params dict] → [get_ollama_config] → [OllamaConfig] → [call_ollama]
      ↓              ↓                    ↓               ↓
    テスト         テスト               テスト          テスト
```

**チェックリスト**:
- [ ] パラメーター取得のテスト (get_ollama_config)
- [ ] デフォルト値マージのテスト
- [ ] バリデーション（範囲外値）のテスト
- [ ] 各関数での統合テスト

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD: テスト実装 (RED) → FAIL 確認 → 実装 (GREEN) → PASS 確認
- RED output must be generated BEFORE implementation begins
- Commit after each phase completion
- Stop at any checkpoint to validate story independently
- **後方互換性**: 既存の `import.ollama` 構造も引き続きサポート
