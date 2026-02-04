# Tasks: ETL Import パリティ実装

**Input**: Design documents from `/specs/026-etl-import-parity/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: テストは spec.md で Success Criteria として要求されているため含める

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (utils/prompts コピー)

**Purpose**: converter からモジュールをコピーし、src/etl 内で独立した環境を構築

- [X] T001 Create src/etl/utils/ directory and __init__.py
- [X] T002 [P] Copy ollama.py from src/converter/scripts/llm_import/common/ to src/etl/utils/ollama.py
- [X] T003 [P] Copy knowledge_extractor.py from src/converter/scripts/llm_import/common/ to src/etl/utils/knowledge_extractor.py
- [X] T004 [P] Copy chunker.py from src/converter/scripts/llm_import/common/ to src/etl/utils/chunker.py
- [X] T005 [P] Copy file_id.py from src/converter/scripts/llm_import/common/ to src/etl/utils/file_id.py
- [X] T006 [P] Copy error_writer.py from src/converter/scripts/llm_import/common/ to src/etl/utils/error_writer.py
- [X] T007 Create src/etl/prompts/ directory
- [X] T008 [P] Copy knowledge extraction prompt from src/converter/scripts/llm_import/prompts/ to src/etl/prompts/
- [X] T009 [P] Copy summary translation prompt from src/converter/scripts/llm_import/prompts/ to src/etl/prompts/
- [X] T010 Update import paths in copied modules (remove llm_import dependencies)
- [X] T011 Run `make test` to verify existing tests still pass
- [X] T012 Generate phase output: specs/026-etl-import-parity/tasks/ph1-output.md

---

## Phase 2: Foundational (フレームワーク拡張)

**Purpose**: BaseStage に JSONL ログ出力と DEBUG モード出力を追加（US7, US8 の基盤）

**⚠️ CRITICAL**: この Phase が完了しないと、後続の User Story で自動ログ・DEBUG 出力が機能しない

- [X] T013 Read previous phase output: specs/026-etl-import-parity/tasks/ph1-output.md
- [X] T014 Add StageLogRecord dataclass to src/etl/core/models.py
- [X] T015 [P] Add _write_jsonl_log() method to BaseStage in src/etl/core/stage.py
- [X] T016 [P] Add _write_debug_output() method to BaseStage in src/etl/core/stage.py
- [X] T017 Modify BaseStage.run() to call _write_jsonl_log() after each item in src/etl/core/stage.py
- [X] T018 Modify BaseStage._process_item() to call _write_debug_output() in DEBUG mode in src/etl/core/stage.py
- [X] T019 Add pipeline_stages.jsonl path to Phase context in src/etl/core/phase.py
- [X] T020 [P] [US7] Add test for JSONL log output in src/etl/tests/test_stages.py
- [X] T021 [P] [US8] Add test for DEBUG mode output in src/etl/tests/test_stages.py
- [X] T022 Run `make test` to verify all tests pass
- [X] T023 Generate phase output: specs/026-etl-import-parity/tasks/ph2-output.md

**Checkpoint**: フレームワークが JSONL ログと DEBUG 出力を自動生成できる状態

---

## Phase 3: US1 + US2 - Ollama 知識抽出 + file_id (Priority: P1) 🎯 MVP

**Goal**: 会話データから Ollama で知識抽出し、file_id 付きの Markdown を生成

**Independent Test**: 1つの会話 JSON を処理し、要約・タグ・file_id 付き Markdown が出力されることを確認

### Tests for US1 + US2

- [X] T024 Read previous phase output: specs/026-etl-import-parity/tasks/ph2-output.md
- [X] T025 [P] [US1] Add test for ExtractKnowledgeStep with mocked Ollama in src/etl/tests/test_knowledge_transformer.py
- [X] T026 [P] [US2] Add test for GenerateMetadataStep file_id generation in src/etl/tests/test_knowledge_transformer.py
- [X] T027 [P] [US1] Add test for FormatMarkdownStep output format in src/etl/tests/test_knowledge_transformer.py

### Implementation for US1 + US2

- [X] T028 [US1] Replace stub in ExtractKnowledgeStep.process() with KnowledgeExtractor.extract() call in src/etl/stages/transform/knowledge_transformer.py
- [X] T029 [US1] Add Ollama error handling with tenacity retry in ExtractKnowledgeStep in src/etl/stages/transform/knowledge_transformer.py
- [X] T030 [US2] Implement file_id generation in GenerateMetadataStep.process() using generate_file_id() in src/etl/stages/transform/knowledge_transformer.py
- [X] T031 [US1] Update FormatMarkdownStep.process() to use KnowledgeDocument.to_markdown() in src/etl/stages/transform/knowledge_transformer.py
- [X] T032 [US1] Add metadata keys (knowledge_extracted, file_id) to ProcessingItem in ExtractKnowledgeStep
- [X] T033 Run `make test` to verify all tests pass
- [X] T034 Generate phase output: specs/026-etl-import-parity/tasks/ph3-output.md

**Checkpoint**: 基本的な知識抽出と file_id 生成が動作する状態（MVP）

---

## Phase 4: US3 - 大規模会話のチャンク分割 (Priority: P2)

**Goal**: 25000文字以上の会話を複数チャンクに分割して処理

**Independent Test**: 100メッセージ以上の会話を処理し、複数ファイルが出力されることを確認

### Tests for US3

- [X] T035 Read previous phase output: specs/026-etl-import-parity/tasks/ph3-output.md
- [X] T036 [P] [US3] Add test for should_chunk() in src/etl/tests/test_knowledge_transformer.py
- [X] T037 [P] [US3] Add test for chunk splitting with multiple outputs in src/etl/tests/test_knowledge_transformer.py
- [X] T038 [P] [US3] Add test for partial chunk failure handling in src/etl/tests/test_knowledge_transformer.py

### Implementation for US3

- [X] T039 [US3] Add _should_chunk() method to ExtractKnowledgeStep in src/etl/stages/transform/knowledge_transformer.py
- [X] T040 [US3] Add _handle_chunked_conversation() method to ExtractKnowledgeStep in src/etl/stages/transform/knowledge_transformer.py
- [X] T041 [US3] Modify ExtractKnowledgeStep.process() to branch on chunk decision in src/etl/stages/transform/knowledge_transformer.py
- [X] T042 [US3] Add chunk metadata (is_chunked, chunk_index) to ProcessingItem in ExtractKnowledgeStep
- [X] T043 [US3] Handle chunk expansion (1 input → N outputs) in KnowledgeTransformer stage in src/etl/stages/transform/knowledge_transformer.py
- [X] T044 Run `make test` to verify all tests pass
- [X] T045 Generate phase output: specs/026-etl-import-parity/tasks/ph4-output.md

**Checkpoint**: 大規模会話がチャンク分割されて処理される状態

---

## Phase 5: US4 - 英語 Summary の自動翻訳 (Priority: P2)

**Goal**: 英語 Summary を日本語に自動翻訳

**Independent Test**: 英語 Summary 付き会話を処理し、日本語 Summary が出力されることを確認

### Tests for US4

- [X] T046 Read previous phase output: specs/026-etl-import-parity/tasks/ph4-output.md
- [X] T047 [P] [US4] Add test for is_english_summary() detection in src/etl/tests/test_knowledge_transformer.py
- [X] T048 [P] [US4] Add test for translate_summary() with mocked Ollama in src/etl/tests/test_knowledge_transformer.py
- [X] T049 [P] [US4] Add test for translation error fallback in src/etl/tests/test_knowledge_transformer.py

### Implementation for US4

- [X] T050 [US4] Add _translate_if_english() method to ExtractKnowledgeStep in src/etl/stages/transform/knowledge_transformer.py
- [X] T051 [US4] Integrate translation into ExtractKnowledgeStep.process() after extraction in src/etl/stages/transform/knowledge_transformer.py
- [X] T052 [US4] Add summary_translated metadata flag to ProcessingItem
- [X] T053 [US4] Add translation error fallback (use original English) with warning log
- [X] T054 Run `make test` to verify all tests pass
- [X] T055 Generate phase output: specs/026-etl-import-parity/tasks/ph5-output.md

**Checkpoint**: 英語 Summary が日本語に翻訳される状態

---

## Phase 6: US5 - @index への最終出力 (Priority: P2)

**Goal**: session/output と @index 両方にファイルを出力

**Independent Test**: import 完了後、@index フォルダにファイルが存在することを確認

### Tests for US5

- [X] T056 Read previous phase output: specs/026-etl-import-parity/tasks/ph5-output.md
- [X] T057 [P] [US5] Add test for UpdateIndexStep file copy in src/etl/tests/test_session_loader.py
- [X] T058 [P] [US5] Add test for file_id duplicate detection in src/etl/tests/test_session_loader.py

### Implementation for US5

- [X] T059 [US5] Implement UpdateIndexStep.process() to copy files to @index in src/etl/stages/load/session_loader.py
- [X] T060 [US5] Add _find_existing_by_file_id() method to scan @index for duplicates in src/etl/stages/load/session_loader.py
- [X] T061 [US5] Add overwrite logic for same file_id, new file for different file_id in UpdateIndexStep
- [X] T062 [US5] Configure @index path from session context in src/etl/stages/load/session_loader.py
- [X] T063 Run `make test` to verify all tests pass
- [X] T064 Generate phase output: specs/026-etl-import-parity/tasks/ph6-output.md

**Checkpoint**: ファイルが @index にも出力される状態

---

## Phase 7: US6 - エラー詳細ファイル出力 (Priority: P3)

**Goal**: エラー発生時に詳細デバッグ情報を errors/ フォルダに出力

**Independent Test**: 意図的エラーを発生させ、errors/ に詳細ファイルが出力されることを確認

### Tests for US6

- [X] T065 Read previous phase output: specs/026-etl-import-parity/tasks/ph6-output.md
- [X] T066 [P] [US6] Add test for error detail file creation in src/etl/tests/test_session_loader.py
- [X] T067 [P] [US6] Add test for ErrorDetail fields in output file in src/etl/tests/test_session_loader.py

### Implementation for US6

- [X] T068 [US6] Add _write_error_detail() method to BaseStage._handle_error() in src/etl/core/stage.py
- [X] T069 [US6] Create ErrorDetail from ProcessingItem and ExtractionResult in _handle_error()
- [X] T070 [US6] Ensure errors/ folder is created under phase directory
- [X] T071 [US6] Add llm_prompt and llm_output capture in ExtractKnowledgeStep error path
- [X] T072 Run `make test` to verify all tests pass
- [X] T073 Generate phase output: specs/026-etl-import-parity/tasks/ph7-output.md

**Checkpoint**: エラー時に詳細ファイルが出力される状態

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 統合テスト、ドキュメント更新、最終検証

- [X] T074 Read previous phase output: specs/026-etl-import-parity/tasks/ph7-output.md
- [X] T075 [P] Add end-to-end integration test with real Ollama (skip if not available) in src/etl/tests/test_import_phase.py
- [X] T076 [P] Add test for MIN_MESSAGES skip logic in src/etl/tests/test_import_phase.py
- [X] T077 [P] Add test for processed file_id skip logic in src/etl/tests/test_import_phase.py
- [X] T078 Update CLAUDE.md with new ETL capabilities
- [X] T079 Run full test suite with `make test`
- [X] T080 Run manual validation with sample Claude export data
- [X] T081 Generate phase output: specs/026-etl-import-parity/tasks/ph8-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - モジュールコピー
- **Phase 2 (Foundational)**: Depends on Phase 1 - フレームワーク拡張
- **Phase 3 (US1+US2)**: Depends on Phase 2 - MVP 知識抽出
- **Phase 4 (US3)**: Depends on Phase 3 - チャンク分割
- **Phase 5 (US4)**: Depends on Phase 3 - 翻訳（Phase 4 と並列可能）
- **Phase 6 (US5)**: Depends on Phase 3 - @index 出力（Phase 4, 5 と並列可能）
- **Phase 7 (US6)**: Depends on Phase 2 - エラー詳細（Phase 3-6 と並列可能）
- **Phase 8 (Polish)**: Depends on all previous phases

### User Story Dependencies

```
Phase 2 (Framework)
      │
      ▼
Phase 3 (US1+US2: MVP) ─────────────────────┐
      │                                      │
      ├─────────┬─────────┬─────────────────┤
      ▼         ▼         ▼                  ▼
Phase 4     Phase 5     Phase 6          Phase 7
(US3)       (US4)       (US5)            (US6)
Chunking  Translation   @index          Errors
      │         │         │                  │
      └─────────┴─────────┴─────────────────┘
                         │
                         ▼
                    Phase 8 (Polish)
```

### Parallel Opportunities

**Phase 1 (Setup)**:
```
T002, T003, T004, T005, T006  # utils コピー（並列）
T008, T009                     # prompts コピー（並列）
```

**Phase 2 (Foundational)**:
```
T015, T016                     # BaseStage メソッド追加（並列）
T020, T021                     # テスト（並列）
```

**Phase 3 (US1+US2)**:
```
T025, T026, T027               # テスト（並列）
```

**After Phase 3 completion**:
```
Phase 4 (US3), Phase 5 (US4), Phase 6 (US5), Phase 7 (US6)  # 全て並列可能
```

---

## Implementation Strategy

### MVP First (Phase 1-3)

1. Complete Phase 1: Setup（utils/prompts コピー）
2. Complete Phase 2: Foundational（フレームワーク拡張）
3. Complete Phase 3: US1+US2（知識抽出 + file_id）
4. **STOP and VALIDATE**: 基本的な import 処理が動作することを確認
5. Deploy/demo if ready

### Incremental Delivery

1. Phase 1-3 → MVP: 基本知識抽出
2. Phase 4 → 大規模会話対応
3. Phase 5 → 日本語ナレッジベース品質向上
4. Phase 6 → organize Phase との連携
5. Phase 7 → デバッグ・運用性向上
6. Phase 8 → 品質保証

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[JSON入力] → [会話パース] → [Ollama抽出] → [Markdown生成] → [ファイル出力]
     ↓           ↓              ↓              ↓              ↓
   テスト      テスト         テスト         テスト         テスト
```

**チェックリスト**:
- [x] Extract Stage: JSON パース、バリデーション
- [x] Transform Stage: 知識抽出、file_id 生成、Markdown フォーマット
- [x] Load Stage: ファイル出力、@index コピー、エラー出力
- [x] Framework: JSONL ログ、DEBUG 出力

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 81 |
| Phase 1 (Setup) | 12 tasks |
| Phase 2 (Foundational) | 11 tasks |
| Phase 3 (US1+US2 MVP) | 11 tasks |
| Phase 4 (US3 Chunking) | 11 tasks |
| Phase 5 (US4 Translation) | 10 tasks |
| Phase 6 (US5 @index) | 9 tasks |
| Phase 7 (US6 Errors) | 9 tasks |
| Phase 8 (Polish) | 8 tasks |
| Parallel Opportunities | 23 tasks marked [P] |
| MVP Scope | Phase 1-3 (34 tasks) |
