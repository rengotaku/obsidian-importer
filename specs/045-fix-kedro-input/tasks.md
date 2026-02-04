# Tasks: Kedro 入力フロー修正

**Input**: Design documents from `/specs/045-fix-kedro-input/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/catalog.yml, quickstart.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | dispatch 型パイプラインによるインポート実行 | P1 | FR-001, FR-008 | provider 指定で適切な Extract パイプラインに dispatch |
| US2 | Claude/OpenAI ZIP ファイルからのインポート | P1 | FR-002, FR-003, FR-004, FR-006, FR-007, FR-009 | ZIP → パース → Markdown 生成 + 冪等 Resume |
| US3 | GitHub Jekyll ブログのインポート | P3 | FR-005, FR-008 | URL → git clone → Markdown 生成 |

## Path Conventions

- Source: `src/obsidian_etl/`
- Tests: `tests/`
- Config: `conf/base/`
- Fixtures: `tests/fixtures/`

---

## Phase 1: Setup (Shared Infrastructure) — NO TDD

**Purpose**: BinaryDataset 作成、既存コード確認、共通基盤の準備

- [X] T001 Read current implementation: `src/obsidian_etl/pipeline_registry.py`, `conf/base/catalog.yml`, `conf/base/parameters.yml`
- [X] T002 [P] Read existing extract nodes: `src/obsidian_etl/pipelines/extract_claude/nodes.py`, `src/obsidian_etl/pipelines/extract_openai/nodes.py`, `src/obsidian_etl/pipelines/extract_github/nodes.py`
- [X] T003 [P] Read existing extract pipelines: `src/obsidian_etl/pipelines/extract_claude/pipeline.py`, `src/obsidian_etl/pipelines/extract_openai/pipeline.py`, `src/obsidian_etl/pipelines/extract_github/pipeline.py`
- [X] T004 [P] Read existing tests: `tests/pipelines/extract_claude/test_nodes.py`, `tests/pipelines/extract_openai/test_nodes.py`, `tests/pipelines/extract_github/test_nodes.py`, `tests/test_pipeline_registry.py`, `tests/test_integration.py`
- [X] T005 [P] Create datasets package: `src/obsidian_etl/datasets/__init__.py`
- [X] T006 [P] Implement BinaryDataset in `src/obsidian_etl/datasets/binary_dataset.py` (AbstractDataset subclass, ~30 lines: load/save/describe)
- [X] T007 Run `make test` to verify no regressions from new files
- [X] T008 Generate phase output: `specs/045-fix-kedro-input/tasks/ph1-output.md`

---

## Phase 2: User Story 2 - Claude/OpenAI ZIP ファイルからのインポート (Priority: P1) MVP

**Goal**: Claude Extract ノードを ZIP 入力に変更し、Claude/OpenAI 両方のカタログ定義を BinaryDataset に更新する。

**Independent Test**: テスト用 ZIP (`claude_test.zip`, `openai_test.zip`) から Extract ノードが正しくパースできることを `make test` で確認する。

### 入力

- [ ] T009 Read previous phase output: `specs/045-fix-kedro-input/tasks/ph1-output.md`

### テスト実装 (RED)

- [x] T010 [P] [US2] Implement BinaryDataset unit tests in `tests/test_datasets.py` (load ZIP bytes, save, describe)
- [x] T011 [P] [US2] Implement `test_parse_claude_zip` tests in `tests/pipelines/extract_claude/test_nodes.py` (ZIP input → parsed_items with required fields: item_id, source_provider, content, file_id, messages, conversation_name, created_at)
- [x] T012 [P] [US2] Implement `test_parse_claude_zip_output_count` in `tests/pipelines/extract_claude/test_nodes.py` (claude_test.zip → 3 parsed_items)
- [x] T013 [P] [US2] Implement `test_parse_claude_zip_invalid` in `tests/pipelines/extract_claude/test_nodes.py` (broken ZIP → error handling)
- [x] T014 [P] [US2] Implement `test_parse_claude_zip_no_conversations` in `tests/pipelines/extract_claude/test_nodes.py` (ZIP without conversations.json → skip with warning)
- [x] T015 [P] [US2] Update OpenAI extract tests in `tests/pipelines/extract_openai/test_nodes.py` to use `openai_test.zip` fixture and verify BinaryDataset catalog compatibility
- [x] T016 Verify `make test` FAIL (RED)
- [x] T017 Generate RED output: `specs/045-fix-kedro-input/red-tests/ph2-test.md`

### 実装 (GREEN)

- [x] T018 Read RED tests: `specs/045-fix-kedro-input/red-tests/ph2-test.md`
- [x] T019 [US2] Rename `parse_claude_json` → `parse_claude_zip` in `src/obsidian_etl/pipelines/extract_claude/nodes.py` (input: `dict[str, Callable]`, ZIP bytes → conversations.json 抽出 → 既存パースロジック適用)
- [x] T020 [US2] Update Claude pipeline inputs in `src/obsidian_etl/pipelines/extract_claude/pipeline.py` (dataset name: `raw_claude_conversations`, node function: `parse_claude_zip`)
- [x] T021 [US2] Update `conf/base/catalog.yml` — Claude entry: PartitionedDataset + BinaryDataset + `.zip` suffix
- [x] T022 [US2] Update `conf/base/catalog.yml` — OpenAI entry: PartitionedDataset + BinaryDataset + `.zip` suffix
- [x] T023 Verify `make test` PASS (GREEN)

### 検証

- [x] T024 Verify `make test` passes all tests (no regressions, 178+ existing tests)
- [x] T025 Verify `make coverage` ≥80%
- [x] T026 Generate phase output: `specs/045-fix-kedro-input/tasks/ph2-output.md`

**Checkpoint**: Claude/OpenAI Extract ノードが ZIP 入力で正しく動作し、parsed_items が期待どおりに生成される

---

## Phase 3: User Story 3 - GitHub Jekyll ブログのインポート (Priority: P3)

**Goal**: GitHub パイプラインのカタログ接続を修正し、URL パラメータ → git clone → MemoryDataset フローが正しく動作するようにする。

**Independent Test**: `make test` で GitHub Extract テストが全てパスすることを確認する。

### 入力

- [ ] T027 Read previous phase output: `specs/045-fix-kedro-input/tasks/ph2-output.md`

### テスト実装 (RED)

- [x] T028 [P] [US3] Update GitHub extract tests in `tests/pipelines/extract_github/test_nodes.py` to verify MemoryDataset-based data flow (no catalog entry for raw_github_posts)
- [x] T029 [P] [US3] Add test for `github_url` parameter usage in `tests/pipelines/extract_github/test_nodes.py`
- [x] T030 Verify `make test` FAIL (RED)
- [x] T031 Generate RED output: `specs/045-fix-kedro-input/red-tests/ph3-test.md`

### 実装 (GREEN)

- [x] T032 Read RED tests: `specs/045-fix-kedro-input/red-tests/ph3-test.md`
- [x] T033 [US3] Remove `raw_github_posts` entry from `conf/base/catalog.yml` (MemoryDataset auto-created)
- [x] T034 [US3] Update `conf/base/parameters.yml` — add `github_url` and `github_clone_dir` parameters (flat keys, matching existing node signature)
- [x] T035 [US3] Update GitHub pipeline in `src/obsidian_etl/pipelines/extract_github/pipeline.py` — fix catalog connections for MemoryDataset flow
- [x] T036 Verify `make test` PASS (GREEN)

### 検証

- [x] T037 Verify `make test` passes all tests (no regressions)
- [x] T038 Generate phase output: `specs/045-fix-kedro-input/tasks/ph3-output.md`

**Checkpoint**: GitHub パイプラインが URL パラメータ → git clone → MemoryDataset で正しく動作する

---

## Phase 4: User Story 1 - dispatch 型パイプライン + 統合テスト (Priority: P1)

**Goal**: `pipeline_registry.py` を dispatch 型に変更し、`__default__` パイプラインが `import_claude` を使用するようにする。統合テストを ZIP 入力対応に更新する。

**Independent Test**: `kedro run` でデフォルト（Claude）パイプラインが正しく dispatch されることを確認する。

### 入力

- [ ] T039 Read previous phase output: `specs/045-fix-kedro-input/tasks/ph3-output.md`

### テスト実装 (RED)

- [ ] T040 [P] [US1] Update `tests/test_pipeline_registry.py` — test `__default__` pipeline is `import_claude`, test individual pipeline names still work
- [ ] T041 [P] [US1] Update `tests/test_integration.py` — update integration tests to use ZIP input fixtures instead of raw dict injection
- [ ] T042 [P] [US1] Add dispatch error test in `tests/test_pipeline_registry.py` — invalid provider → clear error message
- [ ] T043 Verify `make test` FAIL (RED)
- [ ] T044 Generate RED output: `specs/045-fix-kedro-input/red-tests/ph4-test.md`

### 実装 (GREEN)

- [ ] T045 Read RED tests: `specs/045-fix-kedro-input/red-tests/ph4-test.md`
- [ ] T046 [US1] Update `src/obsidian_etl/pipeline_registry.py` — dispatch 型設計: read `import.provider` from `conf/base/parameters.yml` via OmegaConf, set `__default__` dynamically to matching pipeline, raise clear error for invalid provider
- [ ] T047 Verify `make test` PASS (GREEN)

### 検証

- [ ] T048 Verify `make test` passes all tests (full regression)
- [ ] T049 Verify `make coverage` ≥80%
- [ ] T050 Generate phase output: `specs/045-fix-kedro-input/tasks/ph4-output.md`

**Checkpoint**: `kedro run` が dispatch 型で動作し、全プロバイダーが正しく選択される

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: ドキュメント更新、不要コード削除、最終検証

### 入力

- [ ] T051 Read previous phase output: `specs/045-fix-kedro-input/tasks/ph4-output.md`

### 実装

- [ ] T052 [P] Update `CLAUDE.md` — reflect new catalog structure, ZIP input documentation, dispatch pipeline usage
- [ ] T053 [P] Remove any deprecated code or unused imports from modified files
- [ ] T054 Run quickstart.md validation: verify documented commands match implementation
- [ ] T055 Run `make lint` to verify code quality

### 検証

- [ ] T056 Run `make test` to verify all tests pass after cleanup
- [ ] T057 Generate phase output: `specs/045-fix-kedro-input/tasks/ph5-output.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — メインエージェント直接実行
- **US2 (Phase 2)**: Depends on Phase 1 (BinaryDataset) — TDD フロー (tdd-generator → phase-executor)
- **US3 (Phase 3)**: Depends on Phase 2 (catalog changes) — TDD フロー (tdd-generator → phase-executor)
- **US1 (Phase 4)**: Depends on Phase 2+3 (all extract pipelines fixed) — TDD フロー (tdd-generator → phase-executor)
- **Polish (Phase 5)**: Depends on Phase 4 — phase-executor のみ

### Phase Order Rationale

US2 (Claude/OpenAI ZIP) is implemented before US1 (dispatch) because:
1. US1 (dispatch) depends on all extract pipelines being functional
2. US2 fixes the core input layer (catalog ↔ node signature mismatch)
3. US3 fixes GitHub-specific catalog issues
4. US1 then wires everything together with dispatch + integration tests

### Within Each User Story Phase (TDD Flow)

1. **入力**: Read previous phase output (context from prior work)
2. **テスト実装 (RED)**: Write tests FIRST → verify `make test` FAIL → generate RED output
3. **実装 (GREEN)**: Read RED tests → implement → verify `make test` PASS
4. **検証**: Confirm no regressions → generate phase output

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2 (US2)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 3 (US3)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 4 (US1)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 5 (Polish)**: phase-executor のみ

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。

- Setup タスクの [P]: 異なるファイルの読み込み・作成で相互依存なし
- RED テストの [P]: 異なるテストファイルへの書き込みで相互依存なし
- GREEN 実装の [P]: 異なるソースファイルへの書き込みで相互依存なし
- Phase 間: 各 Phase は前 Phase の出力に依存するため [P] 不可

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/045-fix-kedro-input/
├── tasks.md                        # This file
├── tasks/
│   ├── ph1-output.md               # Phase 1 output (Setup results)
│   ├── ph2-output.md               # Phase 2 output (US2 GREEN results)
│   ├── ph3-output.md               # Phase 3 output (US3 GREEN results)
│   ├── ph4-output.md               # Phase 4 output (US1 GREEN results)
│   └── ph5-output.md               # Phase 5 output (Polish results)
└── red-tests/
    ├── ph2-test.md                  # Phase 2 RED test results (US2)
    ├── ph3-test.md                  # Phase 3 RED test results (US3)
    └── ph4-test.md                  # Phase 4 RED test results (US1)
```

### Phase Output Content

Each `phN-output.md` should contain:
- Summary of what was done
- Files created/modified
- Test results (`make test` output)
- Any decisions or deviations from the plan

### RED Test Output Content

Each `phN-test.md` should contain:
- Test code written
- `make test` output showing FAIL (RED confirmation)
- Number of failing tests and their names

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (BinaryDataset + existing code review)
2. Complete Phase 2: US2 — Claude/OpenAI ZIP (RED → GREEN → 検証)
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. Claude ZIP 入力でのパース動作を手動検証

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. Each phase commits: `feat(phase-N): description`

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[ZIP bytes] → [conversations.json 抽出] → [パース] → [parsed_items] → [Transform]
     ↓                   ↓                    ↓            ↓
   テスト              テスト                テスト        テスト
```

**チェックリスト**:
- [ ] BinaryDataset の load/save テスト
- [ ] ZIP → conversations.json 抽出テスト
- [ ] パースロジック（必須フィールド、件数）テスト
- [ ] エッジケース（破損 ZIP、空 ZIP、conversations.json 欠損）テスト
- [ ] 統合テスト（ZIP 入力 → parsed_items 出力）

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD: テスト実装 (RED) → FAIL 確認 → 実装 (GREEN) → PASS 確認
- RED output must be generated BEFORE implementation begins
- Commit after each phase completion
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
