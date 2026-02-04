# Implementation Tasks: RAG Migration

**Feature**: 001-rag-migration-plan | **Generated**: 2026-01-18
**Input**: Design documents from `/specs/001-rag-migration-plan/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/

**Organization**: Tasks are grouped by phase with explicit input/output for traceability.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `src/rag/`
- **Tests**: `tests/rag/`
- **Data**: `data/qdrant/`
- **Phase Output**: `specs/001-rag-migration-plan/tasks/`

---

## Task Overview

| Phase | Focus | Tasks | Est. Effort |
|-------|-------|-------|-------------|
| 1 | Foundation | Project structure, config, exceptions | Small |
| 2 | Ollama Client | Remote embedding, local LLM integration | Medium |
| 3 | Qdrant Store | Document store setup, collection management | Medium |
| 4 | Indexing Pipeline | Document scanning, chunking, embedding | Large |
| 5 | Query Pipeline | Search, Q&A pipelines | Large |
| 6 | CLI | Command interface, Makefile targets | Medium |
| 7 | Integration | E2E tests, performance validation | Medium |

---

## Phase 1: Foundation

**Purpose**: プロジェクト構造の作成と基盤モジュールの実装

**Independent Test**: `python -c "from src.rag import __version__; print(__version__)"` で version が出力される

- [X] T001 Read previous phase output: N/A (first phase)
- [X] T002 [P] [Internal] Create `src/rag/__init__.py` with version info (`__version__ = "0.1.0"`)
- [X] T003 [P] [Internal] Create `src/rag/clients/__init__.py`
- [X] T004 [P] [Internal] Create `src/rag/stores/__init__.py`
- [X] T005 [P] [Internal] Create `src/rag/pipelines/__init__.py`
- [X] T006 [P] [Internal] Create `tests/rag/__init__.py`
- [X] T007 [P] [Internal] Create `data/qdrant/.gitkeep`
- [X] T008 [Internal] Create `src/rag/config.py` with `OllamaConfig` and `RAGConfig` dataclasses
- [X] T009 [Internal] Create `tests/rag/test_config.py` with unit tests
- [X] T010 [Internal] Create `src/rag/exceptions.py` with exception hierarchy
- [X] T011 Run `make test` or `python -m unittest discover tests/rag` to verify tests pass
- [X] T012 Generate phase output: `specs/001-rag-migration-plan/tasks/ph1-output.md`

**Checkpoint**: Foundation モジュールが import 可能、テスト通過

---

## Phase 2: Ollama Client

**Purpose**: リモート Embedding サーバーとローカル LLM への接続機能

**Goal**: Ollama API を使用した embedding 取得と LLM 応答生成

**Independent Test**: `check_connection("http://ollama-server.local:11434")` が `(True, None)` を返す

- [X] T013 Read previous phase output: `specs/001-rag-migration-plan/tasks/ph1-output.md`
- [X] T014 [US1] Implement `check_connection()` in `src/rag/clients/ollama.py`
- [X] T015 [US1] Add tests for `check_connection()` in `tests/rag/test_ollama_client.py`
- [X] T016 [US1] Implement `get_embedding()` in `src/rag/clients/ollama.py`
- [X] T017 [US1] Add tests for `get_embedding()` in `tests/rag/test_ollama_client.py`
- [X] T018 [US2] Implement `generate_response()` in `src/rag/clients/ollama.py`
- [X] T019 [US2] Add tests for `generate_response()` in `tests/rag/test_ollama_client.py`
- [X] T020 Run `make test` to verify all tests pass
- [X] T021 Generate phase output: `specs/001-rag-migration-plan/tasks/ph2-output.md`

**Checkpoint**: Ollama クライアントが embedding 取得・LLM 生成可能

---

## Phase 3: Qdrant Store

**Purpose**: ベクトルストアのセットアップとコレクション管理

**Goal**: Qdrant DocumentStore のファクトリと統計機能

**Independent Test**: `get_document_store()` が `QdrantDocumentStore` インスタンスを返す

- [X] T022 Read previous phase output: `specs/001-rag-migration-plan/tasks/ph2-output.md`
- [X] T023 [US1] Implement `get_document_store()` in `src/rag/stores/qdrant.py`
- [X] T024 [US1] Add tests for `get_document_store()` in `tests/rag/test_qdrant_store.py`
- [X] T025 [US3] Implement `get_collection_stats()` in `src/rag/stores/qdrant.py`
- [X] T026 [US3] Add tests for `get_collection_stats()` in `tests/rag/test_qdrant_store.py`
- [X] T027 Run `make test` to verify all tests pass
- [X] T028 Generate phase output: `specs/001-rag-migration-plan/tasks/ph3-output.md`

**Checkpoint**: Qdrant store がローカル永続化で動作

---

## Phase 4: Indexing Pipeline

**Purpose**: Vault ドキュメントのスキャン・チャンキング・インデックス作成

**Goal**: Haystack Pipeline を使用したインデックス作成機能

**Independent Test**: `index_vault(pipeline, vault_path, "エンジニア")` が `IndexingResult` を返す

- [X] T029 Read previous phase output: `specs/001-rag-migration-plan/tasks/ph3-output.md`
- [X] T030 [P] [US1] Implement `scan_vault()` in `src/rag/pipelines/indexing.py` (frontmatter parse, normalized filter)
- [X] T031 [P] [US1] Add tests for `scan_vault()` in `tests/rag/test_indexing.py`
- [X] T032 [US1] Implement chunking logic (512 tokens, 50 overlap) in `src/rag/pipelines/indexing.py`
- [X] T033 [US1] Add tests for chunking in `tests/rag/test_indexing.py`
- [X] T034 [US1] Implement `create_indexing_pipeline()` in `src/rag/pipelines/indexing.py`
- [X] T035 [US1] Add tests for `create_indexing_pipeline()` in `tests/rag/test_indexing.py`
- [X] T036 [US3] Implement `index_vault()` in `src/rag/pipelines/indexing.py`
- [X] T037 [US3] Add tests for `index_vault()` including dry_run in `tests/rag/test_indexing.py`
- [X] T038 Run `make test` to verify all tests pass
- [X] T039 Generate phase output: `specs/001-rag-migration-plan/tasks/ph4-output.md`

**Checkpoint**: Vault インデックス作成が動作、dry_run モードで検証可能

---

## Phase 5: Query Pipeline

**Purpose**: セマンティック検索と Q&A パイプラインの実装

**Goal**: 検索と質問応答の両方の機能を提供

**Independent Test**: `search(pipeline, "Kubernetes")` が `SearchResponse` を返す

- [X] T040 Read previous phase output: `specs/001-rag-migration-plan/tasks/ph4-output.md`
- [X] T041 [US1] Implement `create_search_pipeline()` in `src/rag/pipelines/query.py`
- [X] T042 [US1] Add tests for `create_search_pipeline()` in `tests/rag/test_query.py`
- [X] T043 [US1] Implement `search()` with filters in `src/rag/pipelines/query.py`
- [X] T044 [US1] Add tests for `search()` in `tests/rag/test_query.py`
- [X] T045 [US2] Implement `create_qa_pipeline()` in `src/rag/pipelines/query.py`
- [X] T046 [US2] Add tests for `create_qa_pipeline()` in `tests/rag/test_query.py`
- [X] T047 [US2] Implement `ask()` with source citations in `src/rag/pipelines/query.py`
- [X] T048 [US2] Add tests for `ask()` in `tests/rag/test_query.py`
- [X] T049 Run `make test` to verify all tests pass
- [X] T050 Generate phase output: `specs/001-rag-migration-plan/tasks/ph5-output.md`

**Checkpoint**: 検索と Q&A パイプラインが動作

---

## Phase 6: CLI

**Purpose**: コマンドラインインターフェースと Makefile ターゲット

**Goal**: ユーザーが CLI 経由で全機能を利用可能

**Independent Test**: `python -m src.rag.cli --help` でヘルプが表示される

- [X] T051 Read previous phase output: `specs/001-rag-migration-plan/tasks/ph5-output.md`
- [X] T052 [US1] Implement CLI argument parser with subcommands in `src/rag/cli.py`
- [X] T053 [US3] Implement `cmd_index()` in `src/rag/cli.py`
- [X] T054 [US1] Implement `cmd_search()` in `src/rag/cli.py`
- [X] T055 [US2] Implement `cmd_ask()` in `src/rag/cli.py`
- [X] T056 [US3] Implement `cmd_status()` in `src/rag/cli.py`
- [X] T057 [P] [US1] Add `rag-index` target to `Makefile`
- [X] T058 [P] [US1] Add `rag-search` target to `Makefile`
- [X] T059 [P] [US2] Add `rag-ask` target to `Makefile`
- [X] T060 [P] [US3] Add `rag-status` target to `Makefile`
- [X] T061 Run CLI commands manually to verify functionality
- [X] T062 Generate phase output: `specs/001-rag-migration-plan/tasks/ph6-output.md`

**Checkpoint**: CLI コマンドが全て動作、Makefile ターゲット利用可能

---

## Phase 7: Integration & Validation

**Purpose**: E2E テストとパフォーマンス検証

**Goal**: 全機能の統合テストと Success Criteria の検証

**Independent Test**: `make test` で全テストが通過

- [X] T063 Read previous phase output: `specs/001-rag-migration-plan/tasks/ph6-output.md`
- [X] T064 [US3] Create E2E indexing test in `tests/rag/test_e2e_indexing.py`
- [X] T065 [US1] Create E2E search test in `tests/rag/test_e2e_search.py`
- [X] T066 [US2] Create E2E Q&A test in `tests/rag/test_e2e_qa.py`
- [X] T067 [Internal] Create performance validation test in `tests/rag/test_performance.py`
- [X] T068 [Internal] Validate SC-001: Search < 3s for 1000 docs
- [X] T069 [Internal] Validate SC-004: Index creation < 10min for 1000 docs
- [X] T070 [Internal] Validate SC-006: Memory usage < 8GB
- [X] T071 [Internal] Validate Edge Case: Mixed ja/en document search
- [X] T072 [Internal] Validate Edge Case: Search during indexing
- [X] T073 Run `make test` to verify all tests pass
- [X] T074 Generate phase output: `specs/001-rag-migration-plan/tasks/ph7-output.md`

**Checkpoint**: 全テスト通過、Success Criteria 達成

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundation)**: No dependencies - can start immediately
- **Phase 2 (Ollama Client)**: Depends on Phase 1 completion
- **Phase 3 (Qdrant Store)**: Depends on Phase 1 completion (can run in parallel with Phase 2)
- **Phase 4 (Indexing)**: Depends on Phase 2 and Phase 3 completion
- **Phase 5 (Query)**: Depends on Phase 2 and Phase 3 completion (can run in parallel with Phase 4)
- **Phase 6 (CLI)**: Depends on Phase 4 and Phase 5 completion
- **Phase 7 (Integration)**: Depends on Phase 6 completion

### User Story Dependencies

- **US1 (Search)**: Core functionality, no dependencies
- **US2 (Q&A)**: Depends on US1 search capability
- **US3 (Index Update)**: Independent of US2

### Parallel Opportunities

- T002-T007 can run in parallel (different files)
- T030, T031 can run in parallel (implementation and test)
- T057-T060 can run in parallel (different Makefile targets)

---

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 12 | Foundation (Phase 1) |
| P1 | 38 | Core functionality (search, index) |
| P2 | 12 | Q&A features |
| P3 | 12 | Status/stats, integration |

**Total Tasks**: 74
**Critical Path**: Phase 1 → Phase 2/3 → Phase 4/5 → Phase 6 → Phase 7

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each phase should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate phase independently
- Phase output files document decisions, issues, and handoff information
