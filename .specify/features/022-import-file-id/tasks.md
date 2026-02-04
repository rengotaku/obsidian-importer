# Tasks: LLMインポートでのfile_id付与

**Input**: Design documents from `/specs/022-import-file-id/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: テストは明示的に要求されているため（plan.md: `tests/test_file_id.py` 新規作成）、テストタスクを含める。

**Organization**: ユーザーストーリー単位でタスクを整理し、独立したテストと実装を可能にする。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: 所属するユーザーストーリー（US1, US2）
- 各タスクに正確なファイルパスを記載

## Path Conventions

- **Source**: `development/scripts/llm_import/`
- **Tests**: `development/scripts/llm_import/tests/`

---

## Phase 1: Setup (共通基盤)

**Purpose**: file_id 生成ロジックの共通モジュール作成

- [x] T001 Read previous phase output: N/A (initial phase)
- [x] T002 [P] Create `development/scripts/llm_import/common/file_id.py` with `generate_file_id()` function
- [x] T003 [P] Create `development/scripts/llm_import/tests/test_file_id.py` with unit tests for file_id generation
- [x] T004 Run `make test` to verify all tests pass
- [x] T005 Generate phase output: `specs/022-import-file-id/tasks/ph1-output.md`

---

## Phase 2: User Story 1 - インポート時のfile_id自動付与 (Priority: P1) 🎯 MVP

**Goal**: インポート処理で生成されるナレッジファイルのfrontmatterにfile_idを自動付与

**Independent Test**: `make llm-import LIMIT=1` で生成されたファイルの frontmatter に `file_id: [12文字]` が含まれることを確認

### Tests for User Story 1

- [x] T006 Read previous phase output: `specs/022-import-file-id/tasks/ph1-output.md`
- [x] T007 [P] [US1] Add test for KnowledgeDocument.file_id field in `development/scripts/llm_import/tests/test_knowledge_extractor.py`
- [x] T008 [P] [US1] Add test for KnowledgeDocument.to_markdown() outputting file_id in frontmatter in `development/scripts/llm_import/tests/test_knowledge_extractor.py`

### Implementation for User Story 1

- [x] T009 [US1] Add `file_id: str = ""` field to KnowledgeDocument dataclass in `development/scripts/llm_import/common/knowledge_extractor.py`
- [x] T010 [US1] Modify `KnowledgeDocument.to_markdown()` to include file_id in frontmatter in `development/scripts/llm_import/common/knowledge_extractor.py`
- [x] T011 [US1] Modify `cli.py` to generate file_id before writing file and set it on KnowledgeDocument in `development/scripts/llm_import/cli.py`
- [x] T012 [US1] Update chunk processing in cli.py to generate unique file_id for each chunk in `development/scripts/llm_import/cli.py`
- [x] T013 Run `make test` to verify all tests pass
- [x] T014 Generate phase output: `specs/022-import-file-id/tasks/ph2-output.md`

**Checkpoint**: frontmatter に file_id が出力されることを確認

---

## Phase 3: User Story 2 - state.jsonでのfile_id記録 (Priority: P2)

**Goal**: state.json の processed エントリに file_id を記録し、リトライやエラー追跡でファイル特定を可能に

**Independent Test**: インポート後に state.json を確認し、processed エントリに file_id が含まれることを確認

### Tests for User Story 2

- [x] T015 Read previous phase output: `specs/022-import-file-id/tasks/ph2-output.md`
- [x] T016 [P] [US2] Add test for ProcessedEntry.file_id field in `development/scripts/llm_import/tests/test_cli.py`
- [x] T017 [P] [US2] Add test for ProcessedEntry.to_dict() including file_id in `development/scripts/llm_import/tests/test_cli.py`
- [x] T018 [P] [US2] Add test for ProcessedEntry.from_dict() handling file_id (present and missing) in `development/scripts/llm_import/tests/test_cli.py`

### Implementation for User Story 2

- [x] T019 [US2] Add `file_id: str | None = None` field to ProcessedEntry dataclass in `development/scripts/llm_import/common/state.py`
- [x] T020 [US2] Modify `ProcessedEntry.to_dict()` to include file_id in `development/scripts/llm_import/common/state.py`
- [x] T021 [US2] Modify `ProcessedEntry.from_dict()` to handle file_id (with backward compatibility for missing key) in `development/scripts/llm_import/common/state.py`
- [x] T022 [US2] Pass file_id when creating ProcessedEntry in cli.py in `development/scripts/llm_import/cli.py`
- [x] T023 Run `make test` to verify all tests pass
- [x] T024 Generate phase output: `specs/022-import-file-id/tasks/ph3-output.md`

**Checkpoint**: state.json に file_id が記録されることを確認

---

## Phase 4: Polish & 検証

**Purpose**: 最終検証とドキュメント整合性確認

- [x] T025 Read previous phase output: `specs/022-import-file-id/tasks/ph3-output.md`
- [x] T026 [P] Run integration test: `make llm-import LIMIT=1` and verify file_id in both output file and state.json
- [x] T027 [P] Verify backward compatibility: existing state.json without file_id still loads correctly
- [x] T028 Run quickstart.md validation scenarios
- [x] T029 Run `make test` to verify final state
- [x] T030 Generate phase output: `specs/022-import-file-id/tasks/ph4-output.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし - 即座に開始可能
- **Phase 2 (US1)**: Phase 1 の完了に依存
- **Phase 3 (US2)**: Phase 2 の完了に依存（ProcessedEntry は file_id 生成後に設定するため）
- **Phase 4 (Polish)**: Phase 3 の完了に依存

### User Story Dependencies

- **US1 (P1)**: file_id 生成モジュール（Phase 1）の完了後に開始可能
- **US2 (P2)**: US1 の file_id 生成ロジックを使用するため、US1 完了後に開始

### Within Each Phase

- テストを先に書いて FAIL を確認
- 実装を行い PASS を確認
- `make test` で全体の整合性を確認

### Parallel Opportunities

**Phase 1**:
- T002 と T003 は並列実行可能（異なるファイル）

**Phase 2**:
- T007 と T008 は並列実行可能（同一テストファイルだが異なるテストケース）

**Phase 3**:
- T016, T017, T018 は並列実行可能（同一テストファイルだが異なるテストケース）

**Phase 4**:
- T026 と T027 は並列実行可能（異なる検証内容）

---

## Parallel Example: Phase 1

```bash
# file_id.py と test_file_id.py を同時作成
Task: "Create file_id.py" (T002)
Task: "Create test_file_id.py" (T003)
```

---

## Implementation Strategy

### MVP First (Phase 1-2)

1. Phase 1: file_id 生成モジュール作成
2. Phase 2: KnowledgeDocument への file_id 付与 (US1)
3. **STOP and VALIDATE**: `make llm-import LIMIT=1` で frontmatter に file_id があることを確認
4. MVP 完了（最小限の価値提供）

### Full Implementation (Phase 3-4)

1. Phase 3: state.json への file_id 記録 (US2)
2. Phase 4: 最終検証
3. 完全な機能として完成

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[file_id生成] → [KnowledgeDocument] → [to_markdown()] → [ファイル書込]
      ↓              ↓                    ↓                 ↓
   テスト         テスト               テスト            統合テスト

[file_id] → [ProcessedEntry] → [to_dict()] → [state.json]
    ↓             ↓                ↓              ↓
  テスト       テスト            テスト       統合テスト
```

---

## Notes

- [P] tasks = 異なるファイル、依存関係なし
- [Story] ラベルはユーザーストーリーへのトレーサビリティ
- 各ユーザーストーリーは独立して完了・テスト可能
- コミットは各タスクまたは論理的グループごと
- チェックポイントでストーリーを独立して検証可能
