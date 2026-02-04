# Tasks: Scripts コードリファクタリング

**Input**: Design documents from `/specs/009-scripts-refactor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

**Tests**: テストは既存の `make test-fixtures` を使用。新規テストタスクは不要。

**Organization**: タスクは依存関係グラフ（research.md）に従い、基盤モジュールから順に移行。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: 関連ユーザーストーリー（US1-US4）
- ファイルパスは `.claude/scripts/` からの相対パス

## Path Conventions

```
.claude/scripts/
├── ollama_normalizer.py          # エントリポイント（リファクタリング後）
├── normalizer/                   # 新規パッケージ
│   ├── __init__.py
│   ├── config.py
│   ├── types.py
│   ├── validators/
│   ├── detection/
│   ├── pipeline/
│   ├── io/
│   ├── state/
│   ├── processing/
│   ├── output/
│   └── cli/
└── Makefile                      # 既存（変更なし）
```

---

## Phase 1: Setup (パッケージ構造作成)

**Purpose**: normalizer パッケージのディレクトリ構造を作成

- [x] T001 Create normalizer package directory structure in .claude/scripts/normalizer/
- [x] T002 [P] Create normalizer/__init__.py with package docstring
- [x] T003 [P] Create normalizer/validators/__init__.py
- [x] T004 [P] Create normalizer/detection/__init__.py
- [x] T005 [P] Create normalizer/pipeline/__init__.py
- [x] T006 [P] Create normalizer/io/__init__.py
- [x] T007 [P] Create normalizer/state/__init__.py
- [x] T008 [P] Create normalizer/processing/__init__.py
- [x] T009 [P] Create normalizer/output/__init__.py
- [x] T010 [P] Create normalizer/cli/__init__.py

**Checkpoint**: パッケージ構造が作成され、`python3 -c "import normalizer"` が成功する

---

## Phase 2: Foundational (基盤モジュール)

**Purpose**: 他の全モジュールが依存する config.py と types.py を作成

**⚠️ CRITICAL**: このフェーズが完了するまで、他のモジュール移行は開始できない

- [x] T011 [US1] Extract constants and paths to normalizer/config.py (L22-143 from ollama_normalizer.py)
- [x] T012 [US1] Extract TypedDict definitions to normalizer/types.py (L633-1385 from ollama_normalizer.py)
- [x] T013 Verify T011-T012 with `python3 -m py_compile normalizer/config.py normalizer/types.py`

**Checkpoint**: config.py と types.py が構文エラーなくインポート可能

---

## Phase 3: User Story 1 - 開発者がコードを修正する (Priority: P1) 🎯 MVP

**Goal**: コードを論理的なモジュールに分割し、特定機能の修正が1モジュール内で完結できるようにする

**Independent Test**: `validators/tags.py` のみを読み込んでタグ検証ロジックが完全に把握できることを確認

### 3.1 Validators モジュール

- [x] T014 [P] [US1] Extract validate_title, log_title_quality to normalizer/validators/title.py (L355-410)
- [x] T015 [P] [US1] Extract tag validation functions to normalizer/validators/tags.py (L426-630)
- [x] T016 [P] [US1] Extract validate_markdown_format, log_format_quality to normalizer/validators/format.py (L411-425)
- [x] T017 [US1] Update normalizer/validators/__init__.py to export public functions

### 3.2 Detection モジュール

- [x] T018 [P] [US1] Extract English detection functions to normalizer/detection/english.py (L283-354)
- [x] T019 [US1] Update normalizer/detection/__init__.py to export public functions

### 3.3 IO モジュール

- [x] T020 [P] [US1] Extract file operations to normalizer/io/files.py (L1500-1600)
- [x] T021 [P] [US1] Extract session management to normalizer/io/session.py (L1601-1750)
- [x] T022 [P] [US1] Extract Ollama API calls and JSON parsing to normalizer/io/ollama.py (L1751-1900)
- [x] T023 [US1] Update normalizer/io/__init__.py to export public functions

### 3.4 State モジュール

- [x] T024 [US1] Extract state management and StateManager singleton to normalizer/state/manager.py (L2200-2400 + global vars)
- [x] T025 [US1] Update normalizer/state/__init__.py to export StateManager and get_state

### 3.5 Pipeline モジュール

- [x] T026 [P] [US1] Extract prompt loading and LLM call functions to normalizer/pipeline/prompts.py (L758-900)
- [x] T027 [P] [US1] Extract stage functions (pre_process, stage1-4, post_process) to normalizer/pipeline/stages.py (L901-1200)
- [x] T028 [US1] Extract run_pipeline and logging to normalizer/pipeline/runner.py (L1201-1330)
- [x] T029 [US1] Update normalizer/pipeline/__init__.py to export run_pipeline

### 3.6 Processing モジュール

- [x] T030 [P] [US1] Extract single file processing to normalizer/processing/single.py (L1901-2100)
- [x] T031 [P] [US1] Extract batch processing to normalizer/processing/batch.py (L2101-2200)
- [x] T032 [US1] Update normalizer/processing/__init__.py to export process_single_file, process_all_files

### 3.7 Output モジュール

- [x] T033 [P] [US1] Extract formatters and utilities to normalizer/output/formatters.py (L2401-2750)
- [x] T034 [P] [US1] Extract diff display to normalizer/output/diff.py (L2601-2700)
- [x] T035 [US1] Update normalizer/output/__init__.py to export public functions

### 3.8 CLI モジュール

- [x] T036 [US1] Extract argument parser to normalizer/cli/parser.py (L2751-2900)
- [x] T037 [US1] Extract command implementations (cmd_status, cmd_metrics, main) to normalizer/cli/commands.py (L2901-3233)
- [x] T038 [US1] Update normalizer/cli/__init__.py to export main

**Checkpoint**: 全モジュールが分割完了、各モジュール500行以下

---

## Phase 4: User Story 2 - 既存機能が正常に動作し続ける (Priority: P1)

**Goal**: リファクタリング後も全既存機能が同一の入出力で動作する

**Independent Test**: `make test-fixtures` で全テストケースがリファクタリング前と同じ結果を返す

- [x] T039 [US2] Update normalizer/__init__.py to export main and public APIs
- [x] T040 [US2] Refactor ollama_normalizer.py to thin entry point (import from normalizer.cli.commands)
- [x] T041 [US2] Verify `python3 ollama_normalizer.py --help` shows same output as before
- [x] T042 [US2] Run `make test-fixtures` and verify all fixtures pass
- [x] T043 [US2] Verify `make preview` works correctly
- [x] T044 [US2] Verify `make status` works correctly

**Checkpoint**: 全既存CLI機能が動作、test-fixturesが全てパス

---

## Phase 5: User Story 3 - AIが効率的にコードを理解する (Priority: P2)

**Goal**: 各モジュールが300-500行以内に収まり、AIが一度の読み込みで機能を完全に把握できる

**Independent Test**: `wc -l normalizer/**/*.py` で全ファイルが500行以下であることを確認

- [x] T045 [US3] Verify all module files are under 500 lines with line count check
- [x] T046 [US3] Verify no circular imports with `python3 -c "from normalizer import main"`
- [x] T047 [US3] Document module responsibilities in normalizer/__init__.py docstring

**Checkpoint**: 全モジュール500行以下、循環依存なし

---

## Phase 6: User Story 4 - エントリポイントの互換性維持 (Priority: P2)

**Goal**: 既存の ollama_normalizer.py が引き続きエントリポイントとして機能し、Makefileを変更せずに使用できる

**Independent Test**: 既存Makefileの全ターゲットが変更なしで動作する

- [x] T048 [US4] Verify ollama_normalizer.py is under 100 lines
- [x] T049 [US4] Verify `python3 -m normalizer --help` works as alternative entry point
- [x] T050 [US4] Add normalizer/__main__.py for `python3 -m normalizer` support
- [x] T051 [US4] Final verification: all Makefile targets work without modification

**Checkpoint**: ollama_normalizer.py が100行以下、全Makefileターゲットが動作

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: クリーンアップと最終確認

- [x] T052 [P] Remove backup files (.backup, .backup-006) from .claude/scripts/
- [x] T053 [P] Run `make check` (py_compile) on all new modules
- [x] T054 Verify lint passes with `make lint` (if ruff available)
- [x] T055 Update quickstart.md with final module structure
- [x] T056 Final comprehensive test: `make test-fixtures` with all fixtures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 即座に開始可能
- **Foundational (Phase 2)**: Phase 1 完了後に開始
- **US1 (Phase 3)**: Phase 2 完了後に開始（モジュール分割のメイン作業）
- **US2 (Phase 4)**: Phase 3 完了後に開始（互換性検証）
- **US3 (Phase 5)**: Phase 4 完了後に開始（行数確認）
- **US4 (Phase 6)**: Phase 4 完了後に開始（エントリポイント確認）
- **Polish (Phase 7)**: Phase 5, 6 完了後に開始

### User Story Dependencies

- **US1 (P1)**: Phase 2（Foundational）完了後に開始可能
- **US2 (P1)**: US1 完了後に開始（分割されたコードの互換性検証）
- **US3 (P2)**: US2 完了後に開始（動作確認後に行数チェック）
- **US4 (P2)**: US2 完了後に開始（動作確認後にエントリポイント確認）

### Within Each Phase

- [P] マークのタスクは並列実行可能
- 同一サブパッケージ内の `__init__.py` 更新は、モジュール作成後に実行
- 各フェーズ終了時にチェックポイント検証を実施

### Parallel Opportunities

- **Phase 1**: T002-T010 は全て並列実行可能
- **Phase 2**: T011, T012 は並列実行可能
- **Phase 3.1-3.8**: 各セクション内の [P] タスクは並列実行可能（ただしセクション間は依存関係あり）
  - 例: validators (T014-T016) は並列、detection (T018) は validators 完了後
  - 例外: io, pipeline, processing, output は validators/detection 完了後に並列開始可能
- **Phase 7**: T052-T054 は並列実行可能

---

## Parallel Example: Phase 3.1 Validators

```bash
# 3つの validator モジュールを同時に作成:
Task: "Extract validate_title to normalizer/validators/title.py"
Task: "Extract tag validation to normalizer/validators/tags.py"
Task: "Extract validate_markdown_format to normalizer/validators/format.py"

# 完了後に __init__.py を更新:
Task: "Update normalizer/validators/__init__.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2 のみ)

1. Phase 1: Setup → パッケージ構造作成
2. Phase 2: Foundational → config.py, types.py
3. Phase 3: US1 → 全モジュール分割
4. Phase 4: US2 → 互換性検証、`make test-fixtures` パス
5. **STOP and VALIDATE**: この時点でMVP完成、実用可能

### Full Implementation

1. MVP完了後
2. Phase 5: US3 → 行数確認、循環依存チェック
3. Phase 6: US4 → エントリポイント最終確認
4. Phase 7: Polish → クリーンアップ

### Incremental Delivery

各フェーズ完了後にコミット:
1. `feat: create normalizer package structure`
2. `feat: add config.py and types.py base modules`
3. `refactor: extract validators, detection, io modules`
4. `refactor: extract state, pipeline, processing modules`
5. `refactor: extract output, cli modules`
6. `refactor: update entry point for compatibility`
7. `chore: cleanup and final verification`

---

## Notes

- [P] タスク = 異なるファイル、依存関係なし
- [Story] ラベル = ユーザーストーリーへのトレーサビリティ
- 各フェーズのチェックポイントで検証を実施
- `make test-fixtures` が最終的な互換性確認手段
- 既存の `markdown_normalizer.py` は変更しない（そのまま維持）

---

## Summary

| Phase | Tasks | Parallel | Purpose |
|-------|-------|----------|---------|
| 1: Setup | 10 | 9 | パッケージ構造 |
| 2: Foundational | 3 | 2 | 基盤モジュール |
| 3: US1 | 25 | 18 | モジュール分割 |
| 4: US2 | 6 | 0 | 互換性検証 |
| 5: US3 | 3 | 0 | 行数確認 |
| 6: US4 | 4 | 0 | エントリポイント |
| 7: Polish | 5 | 3 | クリーンアップ |
| **Total** | **56** | **32** | - |
