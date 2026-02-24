# Tasks: GitHub Actions Lint CI

**Input**: Design documents from `/specs/061-github-actions-lint/`
**Prerequisites**: plan.md (required), spec.md (required), research.md

**Tests**: This feature is infrastructure/configuration work. Validation is done via `make` commands and CI execution, not traditional TDD.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US3 | ローカルでの lint 実行 | P3 | FR-008,012,013,014 | `make lint` で ruff + pylint 実行 |
| US1 | PR 作成時の自動 lint チェック | P1 | FR-001,004,005,006,015,016 | PR 作成で CI 自動実行 |
| US2 | main push 時の lint チェック | P2 | FR-002 | main push で CI 自動実行 |

**Note**: US3 (Makefile) is implemented first because US1/US2 depend on `make ruff`/`make pylint` targets.

## Path Conventions

- **Config**: `pyproject.toml`, `Makefile` (repository root)
- **CI**: `.github/workflows/lint.yml`
- **Feature docs**: `specs/061-github-actions-lint/`

---

## Phase 1: Setup (Dependencies & Config) — NO TDD

**Purpose**: Add pylint dependency and configuration to pyproject.toml

- [X] T001 Read current pyproject.toml
- [X] T002 [P] Add pylint to dev dependencies with pinned version in pyproject.toml
- [X] T003 [P] Pin ruff version in pyproject.toml (change `>=0.1.0` to `==0.8.6`)
- [X] T004 [P] Add `[tool.pylint.main]` section in pyproject.toml
- [X] T005 [P] Add `[tool.pylint.messages_control]` section in pyproject.toml
- [X] T006 [P] Add `[tool.pylint.format]` section in pyproject.toml
- [X] T007 Run `pip install -e ".[dev]"` to install updated dependencies
- [X] T008 Verify `pylint --version` outputs expected version
- [X] T009 Generate phase output: specs/061-github-actions-lint/tasks/ph1-output.md

---

## Phase 2: User Story 3 - ローカルでの lint 実行 (Priority: P3) — MVP Foundation

**Goal**: Makefile に `ruff`, `pylint`, `lint` ターゲットを作成し、ローカルで lint チェックを実行可能にする

**Independent Test**: `make ruff`, `make pylint`, `make lint` が正常に動作すること

### 入力

- [X] T010 Read previous phase output: specs/061-github-actions-lint/tasks/ph1-output.md
- [X] T011 Read current Makefile

### 実装

- [X] T012 [US3] Create `ruff` target in Makefile (extract from existing `lint`)
- [X] T013 [US3] Create `pylint` target in Makefile
- [X] T014 [US3] Update `lint` target to call `ruff` then `pylint` (fail-fast) in Makefile
- [X] T015 [US3] Update `.PHONY` to include `ruff`, `pylint` in Makefile

### 検証

- [X] T016 Run `make ruff` and verify ruff executes
- [X] T017 Run `make pylint` and verify pylint executes
- [X] T018 Run `make lint` and verify both linters run sequentially
- [X] T019 Generate phase output: specs/061-github-actions-lint/tasks/ph2-output.md

**Checkpoint**: `make lint` should work locally with both ruff and pylint

---

## Phase 3: User Story 1 & 2 - CI Lint チェック (Priority: P1/P2)

**Goal**: GitHub Actions ワークフローを作成し、PR 作成時 (US1) および main push 時 (US2) に lint チェックを自動実行する

**Independent Test**: PR を作成して GitHub Actions が実行され、ruff と pylint の結果が個別に表示されること

### 入力

- [X] T020 Read previous phase output: specs/061-github-actions-lint/tasks/ph2-output.md

### 実装

- [X] T021 Create `.github/workflows/` directory if not exists
- [X] T022 [P] [US1] [US2] Create `.github/workflows/lint.yml` with workflow name and triggers
- [X] T023 [P] [US1] [US2] Add `ruff` job to `.github/workflows/lint.yml`
- [X] T024 [P] [US1] [US2] Add `pylint` job to `.github/workflows/lint.yml`
- [X] T025 [US1] [US2] Configure pip cache in both jobs in `.github/workflows/lint.yml`

### 検証

- [X] T026 Run `make lint` locally to verify no lint errors block PR
- [SKIP] T027 Commit and push changes to feature branch (requires user action)
- [SKIP] T028 Create PR and verify GitHub Actions triggers (requires GitHub interaction)
- [SKIP] T029 Verify ruff job shows separate status in PR (requires GitHub interaction)
- [SKIP] T030 Verify pylint job shows separate status in PR (requires GitHub interaction)
- [X] T031 Generate phase output: specs/061-github-actions-lint/tasks/ph3-output.md

**Checkpoint**: PR should show two separate check statuses (ruff, pylint)

---

## Phase 4: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: Fix any lint errors in existing code and finalize documentation

### 入力

- [X] T032 Read previous phase output: specs/061-github-actions-lint/tasks/ph3-output.md

### 実装

- [X] T033 [P] Fix any ruff errors in src/obsidian_etl/
- [X] T034 [P] Fix any pylint errors in src/obsidian_etl/ (or add to disable list)
- [X] T035 [P] Update CLAUDE.md if needed (add CI-related notes)
- [X] T036 Update Makefile help text to include new targets

### 検証

- [X] T037 Run `make lint` to verify all linters pass
- [X] T038 Run `make test` to verify no regressions
- [SKIP] T039 Verify CI passes on final PR (requires GitHub interaction)
- [X] T040 Generate phase output: specs/061-github-actions-lint/tasks/ph4-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (US3: Makefile) → Phase 3 (US1/US2: CI) → Phase 4 (Polish)
```

- **Phase 1**: No dependencies - pyproject.toml 更新
- **Phase 2 (US3)**: Depends on Phase 1 - Makefile ターゲット作成
- **Phase 3 (US1/US2)**: Depends on Phase 2 - GitHub Actions は Makefile を使用
- **Phase 4**: Depends on all - 最終調整

### User Story Dependencies

```
US3 (Makefile) → US1/US2 (CI)
```

US1 と US2 は同じワークフローファイルで実現されるため、同時に実装。

### [P] マーク（依存関係なし）

- T002-T006: pyproject.toml の異なるセクションへの追加
- T012-T015: Makefile の異なるターゲット定義
- T022-T024: lint.yml の異なるセクション定義
- T033-T036: 異なるファイルへの変更

---

## Phase Output Artifacts

### Directory Structure

```
specs/061-github-actions-lint/
├── tasks.md                    # This file
└── tasks/
    ├── ph1-output.md           # Phase 1 output (Setup results)
    ├── ph2-output.md           # Phase 2 output (US3: Makefile)
    ├── ph3-output.md           # Phase 3 output (US1/US2: CI)
    └── ph4-output.md           # Phase 4 output (Polish)
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (pyproject.toml)
2. Complete Phase 2: User Story 3 (Makefile targets)
3. **STOP and VALIDATE**: `make lint` でローカル実行を確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4
2. Each phase commits: `feat(phase-N): description`

### Suggested Commits

- Phase 1: `chore: add pylint dependency and configuration`
- Phase 2: `feat: add ruff and pylint Makefile targets`
- Phase 3: `ci: add GitHub Actions lint workflow`
- Phase 4: `fix: resolve lint errors and update documentation`

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- This feature is infrastructure/config work - no traditional TDD
- Validation is via `make` commands and CI execution
- US3 must be completed before US1/US2 (Makefile is prerequisite for CI)
- US1 and US2 share the same workflow file, implemented together
