# Tasks: E2Eテスト出力検証

**Input**: Design documents from `/specs/046-e2e-output-validation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID  | Title                                        | Priority | FR          | Scenario                                 |
|-----|----------------------------------------------|----------|-------------|------------------------------------------|
| US1 | E2Eテストで最終出力の正しさを検証する        | P1       | FR-1,2,3,4  | ゴールデンファイルとの類似度90%以上で成功 |
| US2 | ゴールデンファイルの作成・更新               | P2       | FR-5,6,7,8  | make test-e2e-update-golden で生成・更新  |

## Path Conventions

- **Single project**: `tests/e2e/`, `tests/fixtures/golden/` at repository root
- Makefile at repository root

---

## Phase 1: Setup (Shared Infrastructure) — NO TDD

**Purpose**: 既存コードの確認、ディレクトリ構造の準備

- [X] T001 Read current E2E test implementation in Makefile (test-e2e target, lines 117-160)
- [X] T002 [P] Read existing test infrastructure in conf/test/catalog.yml
- [X] T003 [P] Read format_markdown node implementation in src/obsidian_etl/pipelines/transform/nodes.py
- [X] T004 [P] Read existing transform unit tests in tests/pipelines/transform/test_nodes.py
- [X] T005 Create directory structure: tests/e2e/__init__.py, tests/fixtures/golden/
- [X] T006 Generate phase output: specs/046-e2e-output-validation/tasks/ph1-output.md

---

## Phase 2: User Story 1 - E2Eテストで最終出力の正しさを検証する (Priority: P1) MVP

**Goal**: `golden_comparator.py` を作成し、Markdown ファイルをゴールデンファイルと比較して類似度90%以上で成功判定する

**Independent Test**: `python -m tests.e2e.golden_comparator --actual <dir> --golden <dir> --threshold 0.9` で比較結果が返る

### 入力

- [x] T007 Read previous phase output: specs/046-e2e-output-validation/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T008 [P] [US1] Implement test_split_frontmatter_and_body (frontmatter と body の分離) in tests/e2e/test_golden_comparator.py
- [x] T009 [P] [US1] Implement test_frontmatter_similarity (frontmatter 類似度計算: キー存在、file_id 完全一致、title/tags 類似度) in tests/e2e/test_golden_comparator.py
- [x] T010 [P] [US1] Implement test_body_similarity (body テキスト類似度計算: 完全一致→1.0、微差→0.9〜1.0、大差→<0.9) in tests/e2e/test_golden_comparator.py
- [x] T011 [P] [US1] Implement test_total_score (総合スコア計算: frontmatter×0.3 + body×0.7) in tests/e2e/test_golden_comparator.py
- [x] T012 [P] [US1] Implement test_compare_directories (ディレクトリ比較: ファイル数一致、ファイル数不一致エラー、ゴールデン不在エラー) in tests/e2e/test_golden_comparator.py
- [x] T013 [P] [US1] Implement test_comparison_report (失敗時レポート: ファイル名、スコア、missing_keys、diff_summary) in tests/e2e/test_golden_comparator.py
- [x] T014 Verify `make test` FAIL (RED)
- [x] T015 Generate RED output: specs/046-e2e-output-validation/red-tests/ph2-test.md

### 実装 (GREEN)

- [ ] T016 Read RED tests: specs/046-e2e-output-validation/red-tests/ph2-test.md
- [ ] T017 [P] [US1] Implement split_frontmatter_and_body() in tests/e2e/golden_comparator.py
- [ ] T018 [P] [US1] Implement calculate_frontmatter_similarity() in tests/e2e/golden_comparator.py
- [ ] T019 [P] [US1] Implement calculate_body_similarity() using difflib.SequenceMatcher in tests/e2e/golden_comparator.py
- [ ] T020 [US1] Implement calculate_total_score() (frontmatter×0.3 + body×0.7) in tests/e2e/golden_comparator.py
- [ ] T021 [US1] Implement compare_directories() (ファイル列挙、ペアリング、個別比較、レポート生成) in tests/e2e/golden_comparator.py
- [ ] T022 [US1] Implement CLI entry point (__main__ block with argparse: --actual, --golden, --threshold) in tests/e2e/golden_comparator.py
- [ ] T023 Verify `make test` PASS (GREEN)

### 検証

- [ ] T024 Verify `make coverage` ≥80%
- [ ] T025 Generate phase output: specs/046-e2e-output-validation/tasks/ph2-output.md

**Checkpoint**: golden_comparator.py が単体で動作し、2つのディレクトリの Markdown ファイルを比較できる

---

## Phase 3: User Story 2 - ゴールデンファイルの作成・更新 (Priority: P2)

**Goal**: Makefile に `test-e2e-update-golden` と改修版 `test-e2e` ターゲットを追加する

**Independent Test**: `make test-e2e-update-golden` でゴールデンファイルが生成され、`make test-e2e` で比較テストが実行される

### 入力

- [ ] T026 Read previous phase output: specs/046-e2e-output-validation/tasks/ph2-output.md

### テスト実装 (RED)

> Note: Makefile ターゲットのテストは手動検証（E2E）のため、テストスクリプトは書かない。
> ただし、ゴールデンファイル存在チェックのロジックは golden_comparator.py のテストでカバー済み (T012)。

### 実装 (GREEN)

- [ ] T027 [US2] Add `test-e2e-update-golden` target in Makefile: Ollama チェック → テストデータ準備 → パイプライン実行 (--to-nodes=format_markdown) → 出力を tests/fixtures/golden/ にコピー → クリーンアップ
- [ ] T028 [US2] Modify `test-e2e` target in Makefile: 中間チェック (Step 3, Step 4) を削除 → パイプラインを format_markdown まで一括実行 → ゴールデンファイル存在チェック → golden_comparator.py 呼び出し → クリーンアップ
- [ ] T029 [US2] Add `.PHONY: test-e2e-update-golden` declaration in Makefile

### 検証

- [ ] T030 Verify `make test` passes all tests (no regressions)
- [ ] T031 Generate phase output: specs/046-e2e-output-validation/tasks/ph3-output.md

**Checkpoint**: `make test-e2e-update-golden` と `make test-e2e` が動作する

---

## Phase 4: ゴールデンファイル初回生成 & 検証 — NO TDD

**Purpose**: ゴールデンファイルを実際に生成し、E2Eテスト全体の動作を検証する

### 入力

- [ ] T032 Read previous phase output: specs/046-e2e-output-validation/tasks/ph3-output.md

### 実装

- [ ] T033 Run `make test-e2e-update-golden` to generate initial golden files in tests/fixtures/golden/
- [ ] T034 Verify golden files exist: 3 .md files in tests/fixtures/golden/
- [ ] T035 Verify golden file structure: frontmatter (title, created, tags, file_id, normalized) + body (要約 + summary_content)
- [ ] T036 Run `make test-e2e` to verify comparison passes (all files ≥90% similarity)

### 検証

- [ ] T037 Run `make test` to verify all unit tests still pass
- [ ] T038 Generate phase output: specs/046-e2e-output-validation/tasks/ph4-output.md

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: ドキュメント更新、不要コード削除

### 入力

- [ ] T039 Read previous phase output: specs/046-e2e-output-validation/tasks/ph4-output.md

### 実装

- [ ] T040 [P] Update CLAUDE.md: test-e2e-update-golden コマンドの説明を Custom Commands セクションに追加
- [ ] T041 [P] Update Makefile help target: test-e2e-update-golden の説明を追加
- [ ] T042 Code cleanup: 不要なインポートや未使用変数の削除

### 検証

- [ ] T043 Run `make test` to verify all tests pass after cleanup
- [ ] T044 Run `make lint` to verify code quality
- [ ] T045 Generate phase output: specs/046-e2e-output-validation/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - メインエージェント直接実行
- **US1 (Phase 2)**: TDD フロー (tdd-generator → phase-executor)
- **US2 (Phase 3)**: Phase 2 完了後 (golden_comparator.py が必要)
- **ゴールデンファイル生成 (Phase 4)**: Phase 3 完了後 (Makefile ターゲットが必要)
- **Polish (Phase 5)**: Phase 4 完了後 - phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **入力**: Read previous phase output (context from prior work)
2. **テスト実装 (RED)**: Write tests FIRST → verify `make test` FAIL → generate RED output
3. **実装 (GREEN)**: Read RED tests → implement → verify `make test` PASS
4. **検証**: Confirm no regressions → generate phase output

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2 (US1)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 3 (US2)**: phase-executor のみ (Makefile 改修、RED テストなし)
- **Phase 4 (ゴールデン生成)**: phase-executor のみ
- **Phase 5 (Polish)**: phase-executor のみ

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。並列実行を保証するものではない。

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/046-e2e-output-validation/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US1 GREEN results)
│   ├── ph3-output.md           # Phase 3 output (US2 results)
│   ├── ph4-output.md           # Phase 4 output (ゴールデン生成 results)
│   └── ph5-output.md           # Phase 5 output (Polish results)
└── red-tests/
    └── ph2-test.md             # Phase 2 RED test results (FAIL confirmation)
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (既存コード確認)
2. Complete Phase 2: US1 - golden_comparator.py (RED → GREEN → 検証)
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. golden_comparator.py を手動でテスト用ファイルで動作確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. Each phase commits: `feat(phase-N): description`

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[Markdown入力] → [frontmatter/body分離] → [類似度計算] → [閾値判定] → [レポート出力]
      ↓                  ↓                    ↓              ↓            ↓
    テスト              テスト               テスト         テスト        テスト
```

**チェックリスト**:
- [ ] frontmatter/body 分離のテスト (T008)
- [ ] frontmatter 類似度計算のテスト (T009)
- [ ] body 類似度計算のテスト (T010)
- [ ] 総合スコア計算のテスト (T011)
- [ ] ディレクトリ比較のテスト (T012)
- [ ] レポート出力のテスト (T013)

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- Phase 3 (US2) は Makefile のみの改修のため RED テストなし
- Phase 4 は Ollama 起動が前提（手動実行）
- golden_comparator.py は外部依存なし（difflib, yaml は標準ライブラリ）
