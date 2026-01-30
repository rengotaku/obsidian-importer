# Tasks: 柔軟な入出力比率対応フレームワーク

**Input**: Design documents from `/specs/028-flexible-io-ratios/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/internal-api.md, quickstart.md

**Tests**: Tests are included based on existing test infrastructure and quality requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `src/etl/` (ETL パイプライン)
- **Tests**: `src/etl/tests/` (ユニットテスト)
- **Feature docs**: `specs/028-flexible-io-ratios/tasks/` (Phase 出力)

---

## Phase 1: Setup (基盤準備)

**Purpose**: 変更対象ファイルの確認と依存関係の整理

- [x] T001 Read previous implementation context and verify branch is `028-flexible-io-ratios`
- [x] T002 Verify existing test baseline with `make test` (全テスト通過を確認)
- [x] T003 Run `make test` to verify all tests pass
- [x] T004 Generate phase output: `specs/028-flexible-io-ratios/tasks/ph1-output.md`

---

## Phase 2: Foundational (共通基盤)

**Purpose**: 1:N 展開に必要なデータモデルとユーティリティの準備

**Input**: Read `specs/028-flexible-io-ratios/tasks/ph1-output.md`

- [x] T005 Read previous phase output: `specs/028-flexible-io-ratios/tasks/ph1-output.md`
- [x] T006 [P] Extend ProcessingItem.metadata schema for chunk tracking in `src/etl/core/models.py` (add is_chunked, chunk_index, total_chunks, parent_item_id fields documentation)
- [x] T007 [P] Add chunk metadata constants and validation helper in `src/etl/core/models.py`
- [x] T008 [P] Add test_chunk_metadata_validation in `src/etl/tests/test_models.py`
- [x] T009 Extend StageLogRecord with chunk tracking fields (is_chunked, parent_item_id, chunk_index) in `src/etl/core/models.py`
- [x] T010 [P] Add test_stage_log_record_with_chunk_fields in `src/etl/tests/test_models.py`
- [x] T011 Run `make test` to verify all tests pass
- [x] T012 Generate phase output: `specs/028-flexible-io-ratios/tasks/ph2-output.md`

**Checkpoint**: データモデル拡張完了、テスト全通過

---

## Phase 3: User Story 1 - 標準的な1:1処理 (Priority: P1) 🎯 MVP

**Goal**: 既存の 1:1 処理が維持され、debug ログが正常に出力されることを確認

**Independent Test**: 単一の JSON ファイルを処理し、単一の Markdown ファイルと debug ログが出力される

**Input**: Read `specs/028-flexible-io-ratios/tasks/ph2-output.md`

### Tests for User Story 1

- [x] T013 Read previous phase output: `specs/028-flexible-io-ratios/tasks/ph2-output.md`
- [x] T014 [P] [US1] Add test_1to1_processing_maintains_single_output in `src/etl/tests/test_import_phase.py`
- [x] T015 [P] [US1] Add test_debug_output_for_1to1_processing in `src/etl/tests/test_debug_step_output.py`
- [x] T016 [P] [US1] Add test_pipeline_stages_jsonl_1to1_format in `src/etl/tests/test_stages.py`

### Implementation for User Story 1

- [x] T017 [US1] Verify BaseStage.run() debug output is automatic (no changes needed if FR-008 already met) in `src/etl/core/stage.py`
- [x] T018 [US1] Verify _write_debug_step_output() is called for all items in `src/etl/core/stage.py`
- [x] T019 [US1] Update _write_jsonl_log() to include chunk fields (null for non-chunked) in `src/etl/core/stage.py`
- [x] T020 [US1] Verify existing 1:1 processing flow is unchanged in `src/etl/stages/transform/knowledge_transformer.py`
- [x] T021 Run `make test` to verify all tests pass
- [x] T022 Generate phase output: `specs/028-flexible-io-ratios/tasks/ph3-output.md`

**Checkpoint**: 1:1 処理が正常動作、debug ログ出力確認済み

---

## Phase 4: User Story 2 - 1:N展開処理 (Priority: P1)

**Goal**: 25000 文字超の会話が自動的にチャンク分割され、各チャンクが個別に処理される

**Independent Test**: 30000 文字の会話ファイルを処理し、2 つ以上のチャンク Markdown ファイルが出力される

**Input**: Read `specs/028-flexible-io-ratios/tasks/ph3-output.md`

### Tests for User Story 2

- [x] T023 Read previous phase output: `specs/028-flexible-io-ratios/tasks/ph3-output.md`
- [x] T024 [P] [US2] Add test_discover_items_chunks_large_conversation in `src/etl/tests/test_import_phase.py`
- [x] T025 [P] [US2] Add test_chunk_metadata_propagation in `src/etl/tests/test_import_phase.py`
- [x] T026 [P] [US2] Add test_debug_output_for_chunked_items in `src/etl/tests/test_debug_step_output.py`
- [x] T027 [P] [US2] Add test_pipeline_stages_jsonl_chunked_format in `src/etl/tests/test_stages.py`

### Implementation for User Story 2

- [x] T028 [US2] Extend ImportPhase.discover_items() to call Chunker for large conversations in `src/etl/phases/import_phase.py`
- [x] T029 [US2] Implement _write_chunk_files() to write chunked JSON to extract/input/ in `src/etl/phases/import_phase.py`
- [x] T030 [US2] Set chunk metadata (is_chunked, chunk_index, total_chunks, parent_item_id) on ProcessingItem in `src/etl/phases/import_phase.py`
- [x] T031 [US2] Update _expand_conversations() to integrate with chunking in `src/etl/phases/import_phase.py`
- [x] T032 [US2] Remove run() override from KnowledgeTransformer (use BaseStage.run()) in `src/etl/stages/transform/knowledge_transformer.py`
- [x] T033 [US2] Remove process_with_expansion() from ExtractKnowledgeStep (no longer needed) in `src/etl/stages/transform/knowledge_transformer.py`
- [x] T034 [US2] Update ExtractKnowledgeStep.process() to handle chunk metadata passthrough in `src/etl/stages/transform/knowledge_transformer.py`
- [x] T035 [US2] Update output filename generation to include chunk suffix (_001, _002) in `src/etl/stages/load/session_loader.py`
- [x] T036 Run `make test` to verify all tests pass
- [x] T037 Generate phase output: `specs/028-flexible-io-ratios/tasks/ph4-output.md`

**Checkpoint**: 1:N 展開処理が正常動作、チャンクファイル出力確認済み

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 統合テスト、エッジケース対応、ドキュメント整備

**Input**: Read `specs/028-flexible-io-ratios/tasks/ph4-output.md`

- [x] T038 Read previous phase output: `specs/028-flexible-io-ratios/tasks/ph4-output.md`
- [x] T039 [P] Add integration test: test_end_to_end_mixed_1to1_and_1toN in `src/etl/tests/test_import_phase.py`
- [x] T040 [P] Add edge case test: test_empty_input_no_error in `src/etl/tests/test_import_phase.py`
- [x] T041 [P] Add edge case test: test_single_message_exceeds_threshold in `src/etl/tests/test_import_phase.py`
- [x] T042 [P] Add edge case test: test_partial_chunk_failure in `src/etl/tests/test_import_phase.py`
- [x] T043 Verify SC-005: test_trace_output_to_input_via_parent_item_id in `src/etl/tests/test_stages.py`
- [x] T044 Verify SC-006: Run full test suite and confirm backward compatibility
- [x] T045 Run quickstart.md validation scenarios manually
- [x] T046 Run `make test` to verify all tests pass
- [x] T047 Generate phase output: `specs/028-flexible-io-ratios/tasks/ph5-output.md`

**Checkpoint**: 全機能実装完了、テスト全通過、後方互換性確認済み

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - verify baseline
- **Phase 2 (Foundational)**: Depends on Phase 1 - data model extensions
- **Phase 3 (US1 - 1:1 処理)**: Depends on Phase 2 - verify existing functionality
- **Phase 4 (US2 - 1:N 展開)**: Depends on Phase 3 - implement chunking
- **Phase 5 (Polish)**: Depends on Phase 4 - integration and edge cases

### User Story Dependencies

- **User Story 1 (1:1 処理)**: Can start after Phase 2 - no dependencies on other stories
- **User Story 2 (1:N 展開)**: Can start after Phase 2 - benefits from US1 verification first

### Within Each User Story

- Tests FIRST (T014-T016, T024-T027) - ensure failing tests exist
- Data model/utility changes before Stage changes
- BaseStage/Phase changes before Stage-specific changes
- Verify with `make test` after each implementation group

### Parallel Opportunities

**Phase 2 (Foundational)**:
```bash
# Parallel model extensions
Task: T006 "Extend ProcessingItem.metadata schema"
Task: T007 "Add chunk metadata constants"
Task: T008 "Add test_chunk_metadata_validation"
```

**Phase 3 (US1 Tests)**:
```bash
# All US1 tests can run in parallel
Task: T014 "test_1to1_processing_maintains_single_output"
Task: T015 "test_debug_output_for_1to1_processing"
Task: T016 "test_pipeline_stages_jsonl_1to1_format"
```

**Phase 4 (US2 Tests)**:
```bash
# All US2 tests can run in parallel
Task: T024 "test_discover_items_chunks_large_conversation"
Task: T025 "test_chunk_metadata_propagation"
Task: T026 "test_debug_output_for_chunked_items"
Task: T027 "test_pipeline_stages_jsonl_chunked_format"
```

**Phase 5 (Polish)**:
```bash
# All edge case tests can run in parallel
Task: T039 "test_end_to_end_mixed_1to1_and_1toN"
Task: T040 "test_empty_input_no_error"
Task: T041 "test_single_message_exceeds_threshold"
Task: T042 "test_partial_chunk_failure"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (baseline verification)
2. Complete Phase 2: Foundational (data model extensions)
3. Complete Phase 3: User Story 1 (1:1 processing verified)
4. **STOP and VALIDATE**: Ensure existing functionality preserved
5. Continue to Phase 4 if MVP accepted

### Incremental Delivery

1. Phase 1+2 → Foundation ready
2. Phase 3 → 1:1 processing verified (MVP!)
3. Phase 4 → 1:N expansion working (Full feature)
4. Phase 5 → Edge cases and polish (Production ready)

### Critical Success Factors

- **SC-003**: KnowledgeTransformer.run() オーバーライド削除後もテスト全通過
- **SC-006**: 既存テスト全パス（後方互換性100%）
- **SC-007**: 1:1 と 1:N で同一 debug ログスキーマ

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[conversations.json] → [discover_items] → [chunk split] → [Extract] → [Transform] → [Load]
         ↓                    ↓                ↓              ↓           ↓           ↓
     入力検証          チャンク判定       ファイル分割     metadata     debug log   出力命名
```

**チェックリスト**:
- [x] 入力パース部分のテスト (既存)
- [ ] チャンク判定ロジックのテスト (T024)
- [ ] チャンク分割出力のテスト (T025)
- [ ] debug ログ出力のテスト (T015, T026)
- [ ] 出力ファイル命名のテスト (T035 に含む)
- [ ] End-to-End テスト (T039)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate independently

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 47 |
| Phase 1 (Setup) | 4 |
| Phase 2 (Foundational) | 8 |
| Phase 3 (US1 - 1:1) | 10 |
| Phase 4 (US2 - 1:N) | 15 |
| Phase 5 (Polish) | 10 |
| Parallel Tasks | 20 |
| Test Tasks | 14 |
