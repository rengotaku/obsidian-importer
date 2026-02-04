# Tasks: データパイプラインの構造的再設計（Kedro 移行）

**Input**: Design documents from `specs/044-kedro-migration/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | Claude インポート（Extract → Transform → Organize 一気通貫） | P1 | FR-1,2,3,5,7 | シナリオ1 |
| US2 | 冪等 Resume（再実行で完了済みスキップ） | P1 | FR-4 | シナリオ2 |
| US3 | OpenAI (ChatGPT) プロバイダー対応 | P2 | FR-7 | シナリオ1 |
| US4 | GitHub Jekyll プロバイダー対応 | P2 | FR-7 | シナリオ1 |
| US5 | 部分実行・DAG 可視化 | P3 | FR-3,6 | シナリオ3,4 |

## Path Conventions

- **Kedro パッケージ**: `src/obsidian_etl/`
- **設定**: `conf/base/`, `conf/local/`
- **データレイヤー**: `data/01_raw/`, `data/02_intermediate/`, `data/03_primary/`, `data/07_model_output/`
- **テスト**: `tests/`
- **既存コード参照**: `src/etl/`（移植元、read-only）

---

## Phase 1: Setup (Project Initialization) — NO TDD

**Purpose**: Kedro プロジェクト生成、設定ファイル配置、ユーティリティ移植

- [X] T001 Read existing implementation overview in src/etl/ to understand current pipeline structure
- [X] T002 [P] Read existing utils in src/etl/utils/ollama.py, src/etl/utils/knowledge_extractor.py, src/etl/utils/chunker.py, src/etl/utils/file_id.py
- [X] T003 [P] Read existing prompts in src/etl/prompts/knowledge_extraction.txt, src/etl/prompts/summary_translation.txt
- [X] T004 [P] Read existing extract stages in src/etl/stages/extract/ for Claude parser logic
- [X] T005 [P] Read existing transform stages in src/etl/stages/transform/ for LLM processing logic
- [X] T006 [P] Read existing organize stages in src/etl/stages/ for genre classification and vault placement logic
- [X] T007 Run `kedro new --name=obsidian-etl --tools=lint,test --example=n --starter=spaceflights-pandas` in project root to generate Kedro skeleton (adjust starter if needed, or use `--example=n` for blank)
- [X] T008 Install dependencies: `pip install kedro==1.1.1 kedro-datasets tenacity>=8.0 PyYAML>=6.0 requests>=2.28`
- [X] T009 [P] Create conf/base/catalog.yml per specs/044-kedro-migration/contracts/catalog.yml
- [X] T010 [P] Create conf/base/parameters.yml per specs/044-kedro-migration/contracts/parameters.yml
- [X] T011 [P] Create conf/base/logging.yml with standard Kedro logging configuration
- [X] T012 [P] Migrate src/etl/utils/ollama.py → src/obsidian_etl/utils/ollama.py (refactor to Kedro conventions: remove class-level state, pure function interface)
- [X] T013 [P] Migrate src/etl/utils/knowledge_extractor.py → src/obsidian_etl/utils/knowledge_extractor.py (refactor: function-based API, params dict input)
- [X] T014 [P] Migrate src/etl/utils/chunker.py → src/obsidian_etl/utils/chunker.py (refactor: pure function, configurable chunk_size via params)
- [X] T015 [P] Migrate src/etl/utils/file_id.py → src/obsidian_etl/utils/file_id.py (refactor: pure function)
- [X] T016 [P] Copy src/etl/prompts/knowledge_extraction.txt → src/obsidian_etl/utils/prompts/knowledge_extraction.txt
- [X] T017 [P] Copy src/etl/prompts/summary_translation.txt → src/obsidian_etl/utils/prompts/summary_translation.txt
- [X] T018 Create pipeline skeleton directories: src/obsidian_etl/pipelines/{extract_claude,extract_openai,extract_github,transform,organize}/ with __init__.py, nodes.py, pipeline.py
- [X] T019 Create src/obsidian_etl/hooks.py with empty ErrorHandlerHook and LoggingHook classes
- [X] T020 Create src/obsidian_etl/pipeline_registry.py with placeholder register_pipelines()
- [X] T021 Configure src/obsidian_etl/settings.py with Hook registration
- [X] T022 Create data/ directory structure: data/{01_raw/claude,01_raw/openai,01_raw/github,02_intermediate/parsed,03_primary/transformed,07_model_output/notes,07_model_output/organized}/
- [X] T023 Create tests/ directory structure: tests/pipelines/{extract_claude,extract_openai,extract_github,transform,organize}/ with empty test_nodes.py files and tests/conftest.py
- [X] T024 Update Makefile with Kedro targets: `make kedro-run`, `make kedro-test`, `make kedro-viz`
- [X] T025 Verify `kedro info` runs successfully (project recognized)
- [X] T026 Generate phase output: specs/044-kedro-migration/tasks/ph1-output.md

---

## Phase 2: US1 - Claude Extract パイプライン (Priority: P1) MVP-Part1

**Goal**: Claude エクスポート JSON をパースし、ParsedItem（統一中間表現）を生成する Extract パイプライン

**Independent Test**: `python -m unittest tests/pipelines/extract_claude/test_nodes.py` で Claude JSON → ParsedItem 変換が検証できる

### 入力

- [x] T027 Read previous phase output: specs/044-kedro-migration/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T028 [P] [US1] Create test fixture: tests/fixtures/claude_input.json (minimal Claude export with 2-3 conversations)
- [x] T029 [P] [US1] Create test fixture: tests/fixtures/expected_outputs/parsed_claude_item.json (expected ParsedItem output)
- [x] T030 [P] [US1] Implement test_parse_claude_json_basic in tests/pipelines/extract_claude/test_nodes.py (valid JSON → ParsedItem dict)
- [x] T031 [P] [US1] Implement test_parse_claude_json_chunking in tests/pipelines/extract_claude/test_nodes.py (25000+ char conversation → multiple chunks)
- [x] T032 [P] [US1] Implement test_parse_claude_json_skip_short in tests/pipelines/extract_claude/test_nodes.py (messages < 3 → excluded from output)
- [x] T033 [P] [US1] Implement test_parse_claude_json_missing_name in tests/pipelines/extract_claude/test_nodes.py (name=None → fallback to first user message)
- [x] T034 [P] [US1] Implement test_validate_structure in tests/pipelines/extract_claude/test_nodes.py (uuid, chat_messages required)
- [x] T035 [P] [US1] Implement test_validate_content in tests/pipelines/extract_claude/test_nodes.py (empty messages excluded)
- [x] T036 [P] [US1] Implement test_file_id_generation in tests/pipelines/extract_claude/test_nodes.py (SHA256 file_id matches expected)
- [x] T037 Verify `make test` FAIL (RED)
- [x] T038 Generate RED output: specs/044-kedro-migration/red-tests/ph2-test.md

### 実装 (GREEN)

- [x] T039 Read RED tests: specs/044-kedro-migration/red-tests/ph2-test.md
- [x] T040 [P] [US1] Implement parse_claude_json node in src/obsidian_etl/pipelines/extract_claude/nodes.py (JSON parse, structure/content validation, chunking, file_id generation)
- [x] T041 [US1] Define Claude extract pipeline in src/obsidian_etl/pipelines/extract_claude/pipeline.py (raw_claude_conversations → parsed_items)
- [x] T042 Verify `make test` PASS (GREEN)

### 検証

- [x] T043 Verify `make test` passes all tests (no regressions)
- [x] T044 Generate phase output: specs/044-kedro-migration/tasks/ph2-output.md

**Checkpoint**: Claude Extract nodes produce correct ParsedItem output

---

## Phase 3: US1 - Transform パイプライン (Priority: P1) MVP-Part2

**Goal**: ParsedItem に LLM 知識抽出・メタデータ生成・Markdown フォーマットを適用する共通 Transform パイプライン

**Independent Test**: `python -m unittest tests/pipelines/transform/test_nodes.py` で ParsedItem → TransformedItem 変換が検証できる

### 入力

- [x] T045 Read previous phase output: specs/044-kedro-migration/tasks/ph2-output.md

### テスト実装 (RED)

- [x] T046 [P] [US1] Create test fixture: tests/fixtures/expected_outputs/transformed_item.json (expected TransformedItem output)
- [x] T047 [P] [US1] Implement test_extract_knowledge in tests/pipelines/transform/test_nodes.py (ParsedItem → generated_metadata with title, summary, tags; mock Ollama)
- [x] T048 [P] [US1] Implement test_extract_knowledge_english_summary_translation in tests/pipelines/transform/test_nodes.py (English summary → Japanese translation; mock Ollama)
- [x] T049 [P] [US1] Implement test_extract_knowledge_error_handling in tests/pipelines/transform/test_nodes.py (LLM failure → item excluded, logged)
- [x] T050 [P] [US1] Implement test_generate_metadata in tests/pipelines/transform/test_nodes.py (generated_metadata → metadata dict with file_id, created, normalized=True)
- [x] T051 [P] [US1] Implement test_format_markdown in tests/pipelines/transform/test_nodes.py (metadata + content → YAML frontmatter + body)
- [x] T052 [P] [US1] Implement test_format_markdown_output_filename in tests/pipelines/transform/test_nodes.py (title → sanitized filename)
- [x] T053 Verify `make test` FAIL (RED)
- [x] T054 Generate RED output: specs/044-kedro-migration/red-tests/ph3-test.md

### 実装 (GREEN)

- [x] T055 Read RED tests: specs/044-kedro-migration/red-tests/ph3-test.md
- [x] T056 [P] [US1] Implement extract_knowledge node in src/obsidian_etl/pipelines/transform/nodes.py (LLM call with tenacity retry, English→Japanese translation)
- [x] T057 [P] [US1] Implement generate_metadata node in src/obsidian_etl/pipelines/transform/nodes.py (file_id, created, tags, normalized flag)
- [x] T058 [P] [US1] Implement format_markdown node in src/obsidian_etl/pipelines/transform/nodes.py (YAML frontmatter + Markdown body, filename sanitization)
- [x] T059 [US1] Define transform pipeline in src/obsidian_etl/pipelines/transform/pipeline.py (parsed_items → transformed_items → markdown_notes)
- [x] T060 Verify `make test` PASS (GREEN)

### 検証

- [x] T061 Verify `make test` passes all tests (no regressions)
- [x] T062 Generate phase output: specs/044-kedro-migration/tasks/ph3-output.md

**Checkpoint**: Transform pipeline converts ParsedItem → Markdown output correctly

---

## Phase 4: US1 - Organize パイプライン (Priority: P1) MVP-Part3

**Goal**: Markdown ファイルのジャンル判定・正規化・Vault 配置を行う Organize パイプライン

**Independent Test**: `python -m unittest tests/pipelines/organize/test_nodes.py` で Markdown → OrganizedItem 変換と Vault 配置が検証できる

### 入力

- [x] T063 Read previous phase output: specs/044-kedro-migration/tasks/ph3-output.md

### テスト実装 (RED)

- [x] T064 [P] [US1] Implement test_classify_genre in tests/pipelines/organize/test_nodes.py (keyword-based genre detection: engineer, business, economy, daily, other)
- [x] T065 [P] [US1] Implement test_classify_genre_default in tests/pipelines/organize/test_nodes.py (no keyword match → "other")
- [x] T066 [P] [US1] Implement test_normalize_frontmatter in tests/pipelines/organize/test_nodes.py (add/update normalized=True, clean unnecessary fields)
- [x] T067 [P] [US1] Implement test_clean_content in tests/pipelines/organize/test_nodes.py (excess blank lines, formatting cleanup)
- [x] T068 [P] [US1] Implement test_determine_vault_path in tests/pipelines/organize/test_nodes.py (genre → vault path mapping from params)
- [x] T069 [P] [US1] Implement test_move_to_vault in tests/pipelines/organize/test_nodes.py (file written to correct vault path; mock filesystem)
- [x] T070 Verify `make test` FAIL (RED)
- [x] T071 Generate RED output: specs/044-kedro-migration/red-tests/ph4-test.md

### 実装 (GREEN)

- [x] T072 Read RED tests: specs/044-kedro-migration/red-tests/ph4-test.md
- [x] T073 [P] [US1] Implement classify_genre node in src/obsidian_etl/pipelines/organize/nodes.py (keyword matching from params)
- [x] T074 [P] [US1] Implement normalize_frontmatter node in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T075 [P] [US1] Implement clean_content node in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T076 [P] [US1] Implement determine_vault and move_to_vault nodes in src/obsidian_etl/pipelines/organize/nodes.py
- [x] T077 [US1] Define organize pipeline in src/obsidian_etl/pipelines/organize/pipeline.py (markdown_notes → organized_items + Vault 配置)
- [x] T078 Verify `make test` PASS (GREEN)

### 検証

- [x] T079 Verify `make test` passes all tests (no regressions)
- [x] T080 Generate phase output: specs/044-kedro-migration/tasks/ph4-output.md

**Checkpoint**: Organize pipeline classifies and places files into correct Vaults

---

## Phase 5: US1 - E2E 統合・Hook・Pipeline Registry (Priority: P1) MVP-Part4

**Goal**: Claude import → organize 一気通貫実行を完成させる。Hook によるエラーハンドリング、pipeline_registry での登録

**Independent Test**: `kedro run --pipeline=import_claude` で Claude エクスポートデータが Vault まで配置される

### 入力

- [x] T081 Read previous phase output: specs/044-kedro-migration/tasks/ph4-output.md

### テスト実装 (RED)

- [x] T082 [P] [US1] Implement test_error_handler_hook in tests/test_hooks.py (on_node_error logs error, pipeline continues)
- [x] T083 [P] [US1] Implement test_logging_hook in tests/test_hooks.py (before_node_run / after_node_run logs node name and timing)
- [x] T084 [P] [US1] Implement test_pipeline_registry in tests/test_pipeline_registry.py (register_pipelines returns import_claude, __default__)
- [x] T085 [P] [US1] Implement test_e2e_claude_import in tests/test_integration.py (SequentialRunner with test DataCatalog: raw_claude → organized_items; mock Ollama)
- [x] T086 Verify `make test` FAIL (RED)
- [x] T087 Generate RED output: specs/044-kedro-migration/red-tests/ph5-test.md

### 実装 (GREEN)

- [x] T088 Read RED tests: specs/044-kedro-migration/red-tests/ph5-test.md
- [x] T089 [P] [US1] Implement ErrorHandlerHook in src/obsidian_etl/hooks.py (on_node_error: log error detail, record failed item)
- [x] T090 [P] [US1] Implement LoggingHook in src/obsidian_etl/hooks.py (before/after_node_run: log timing)
- [x] T091 [US1] Register import_claude pipeline in src/obsidian_etl/pipeline_registry.py (extract_claude + transform + organize)
- [x] T092 [US1] Wire settings.py: register hooks, configure session settings
- [x] T093 Verify `make test` PASS (GREEN)

### 検証

- [x] T094 Verify `make test` passes all tests (no regressions)
- [x] T095 Generate phase output: specs/044-kedro-migration/tasks/ph5-output.md

**Checkpoint**: `kedro run --pipeline=import_claude` executes full Claude import → organize pipeline. US1 MVP complete.

---

## Phase 6: US2 - 冪等 Resume (Priority: P1)

**Goal**: PartitionedDataset の overwrite=false とノード内スキップロジックにより、再実行時に完了済みアイテムをスキップ

**Independent Test**: 2回目の `kedro run` で既存出力がスキップされ、未処理分のみ再処理される

### 入力

- [x] T096 Read previous phase output: specs/044-kedro-migration/tasks/ph5-output.md

### テスト実装 (RED)

- [x] T097 [P] [US2] Implement test_idempotent_extract in tests/pipelines/extract_claude/test_nodes.py (output partition exists → skip item, no re-parse)
- [x] T098 [P] [US2] Implement test_idempotent_transform in tests/pipelines/transform/test_nodes.py (output partition exists → skip item, no LLM call)
- [x] T099 [P] [US2] Implement test_idempotent_organize in tests/pipelines/organize/test_nodes.py (output partition exists → skip item, no re-classify)
- [x] T100 [P] [US2] Implement test_resume_after_failure in tests/test_integration.py (first run: 3 items, 1 fails; second run: only failed item re-processed)
- [x] T101 Verify `make test` FAIL (RED)
- [x] T102 Generate RED output: specs/044-kedro-migration/red-tests/ph6-test.md

### 実装 (GREEN)

- [x] T103 Read RED tests: specs/044-kedro-migration/red-tests/ph6-test.md
- [x] T104 [US2] Add idempotent skip logic to parse_claude_json node in src/obsidian_etl/pipelines/extract_claude/nodes.py (check output partition existence)
- [x] T105 [US2] Add idempotent skip logic to extract_knowledge node in src/obsidian_etl/pipelines/transform/nodes.py (check output partition existence)
- [x] T106 [US2] Add idempotent skip logic to organize nodes in src/obsidian_etl/pipelines/organize/nodes.py (check output partition existence)
- [x] T107 Verify `make test` PASS (GREEN)

### 検証

- [x] T108 Verify `make test` passes all tests (no regressions)
- [x] T109 Generate phase output: specs/044-kedro-migration/tasks/ph6-output.md

**Checkpoint**: Re-running `kedro run` skips completed items and only processes failures. US2 complete.

---

## Phase 7: US3 - OpenAI (ChatGPT) プロバイダー (Priority: P2)

**Goal**: ChatGPT エクスポート ZIP からの Extract パイプライン追加。Transform/Organize は共有パイプライン再利用

**Independent Test**: `python -m unittest tests/pipelines/extract_openai/test_nodes.py` で ZIP → ParsedItem 変換が検証できる

### 入力

- [x] T110 Read previous phase output: specs/044-kedro-migration/tasks/ph6-output.md
- [x] T111 [US3] Read existing ChatGPT parser in src/etl/stages/extract/ for OpenAI extraction logic

### テスト実装 (RED)

- [x] T112 [P] [US3] Create test fixture: tests/fixtures/openai_input.zip (minimal ChatGPT export with conversations.json) — ZIP はテスト内で動的生成（io.BytesIO + zipfile）
- [x] T113 [P] [US3] Create test fixture: tests/fixtures/expected_outputs/parsed_openai_item.json (expected ParsedItem from ChatGPT)
- [x] T114 [P] [US3] Implement test_parse_chatgpt_zip in tests/pipelines/extract_openai/test_nodes.py (ZIP → conversations.json → ParsedItem dict)
- [x] T115 [P] [US3] Implement test_chatgpt_tree_traversal in tests/pipelines/extract_openai/test_nodes.py (mapping tree → chronological messages)
- [x] T116 [P] [US3] Implement test_chatgpt_multimodal in tests/pipelines/extract_openai/test_nodes.py (image → [Image: id], audio → [Audio: name])
- [x] T117 [P] [US3] Implement test_chatgpt_role_conversion in tests/pipelines/extract_openai/test_nodes.py (user→human, system/tool excluded)
- [x] T118 [P] [US3] Implement test_chatgpt_chunking in tests/pipelines/extract_openai/test_nodes.py (25000+ chars → chunks)
- [x] T119 [P] [US3] Implement test_chatgpt_empty_conversations in tests/pipelines/extract_openai/test_nodes.py (empty conversations.json → warning, no output)
- [x] T120 Verify `make test` FAIL (RED)
- [x] T121 Generate RED output: specs/044-kedro-migration/red-tests/ph7-test.md

### 実装 (GREEN)

- [x] T122 Read RED tests: specs/044-kedro-migration/red-tests/ph7-test.md
- [x] T123 [US3] Implement parse_chatgpt_zip node in src/obsidian_etl/pipelines/extract_openai/nodes.py (ZIP extract, tree traversal, multimodal handling, chunking)
- [x] T124 [US3] Define OpenAI extract pipeline in src/obsidian_etl/pipelines/extract_openai/pipeline.py (raw_openai_conversations → parsed_items)
- [x] T125 [US3] Register import_openai pipeline in src/obsidian_etl/pipeline_registry.py (extract_openai + transform + organize)
- [x] T126 Verify `make test` PASS (GREEN)

### 検証

- [x] T127 Verify `make test` passes all tests (no regressions)
- [x] T128 Generate phase output: specs/044-kedro-migration/tasks/ph7-output.md

**Checkpoint**: `kedro run --pipeline=import_openai` processes ChatGPT exports. US3 complete.

---

## Phase 8: US4 - GitHub Jekyll プロバイダー (Priority: P2)

**Goal**: GitHub Jekyll ブログの git clone → パース → frontmatter 変換 の Extract パイプライン追加

**Independent Test**: `python -m unittest tests/pipelines/extract_github/test_nodes.py` で git clone → ParsedItem 変換が検証できる

### 入力

- [x] T129 Read previous phase output: specs/044-kedro-migration/tasks/ph7-output.md
- [x] T130 [US4] Read existing GitHub parser in src/etl/stages/extract/ for Jekyll extraction logic

### テスト実装 (RED)

- [x] T131 [P] [US4] Create test fixture: tests/fixtures/github_jekyll_post.md (sample Jekyll post with frontmatter)
- [x] T132 [P] [US4] Create test fixture: tests/fixtures/expected_outputs/parsed_github_item.json (expected ParsedItem from Jekyll)
- [x] T133 [P] [US4] Implement test_clone_github_repo in tests/pipelines/extract_github/test_nodes.py (URL → sparse-checkout → local files; mock subprocess)
- [x] T134 [P] [US4] Implement test_parse_jekyll in tests/pipelines/extract_github/test_nodes.py (Markdown + frontmatter → parsed fields)
- [x] T135 [P] [US4] Implement test_parse_jekyll_skip_draft in tests/pipelines/extract_github/test_nodes.py (draft: true → excluded)
- [x] T136 [P] [US4] Implement test_convert_frontmatter in tests/pipelines/extract_github/test_nodes.py (Jekyll frontmatter → Obsidian format: date→created, tags/categories/keywords→tags)
- [x] T137 [P] [US4] Implement test_date_extraction_priority in tests/pipelines/extract_github/test_nodes.py (frontmatter.date → filename → regex → current datetime)
- [x] T138 Verify `make test` FAIL (RED)
- [x] T139 Generate RED output: specs/044-kedro-migration/red-tests/ph8-test.md

### 実装 (GREEN)

- [x] T140 Read RED tests: specs/044-kedro-migration/red-tests/ph8-test.md
- [x] T141 [P] [US4] Implement clone_github_repo node in src/obsidian_etl/pipelines/extract_github/nodes.py (git clone --depth 1 + sparse-checkout)
- [x] T142 [P] [US4] Implement parse_jekyll node in src/obsidian_etl/pipelines/extract_github/nodes.py (frontmatter parse, draft/private filter)
- [x] T143 [P] [US4] Implement convert_frontmatter node in src/obsidian_etl/pipelines/extract_github/nodes.py (Jekyll → Obsidian format conversion)
- [x] T144 [US4] Define GitHub extract pipeline in src/obsidian_etl/pipelines/extract_github/pipeline.py (raw_github_posts → parsed_items)
- [x] T145 [US4] Register import_github pipeline in src/obsidian_etl/pipeline_registry.py (extract_github + transform + organize)
- [x] T146 Verify `make test` PASS (GREEN)

### 検証

- [x] T147 Verify `make test` passes all tests (no regressions)
- [x] T148 Generate phase output: specs/044-kedro-migration/tasks/ph8-output.md

**Checkpoint**: `kedro run --pipeline=import_github` processes Jekyll blogs. US4 complete.

---

## Phase 9: US5 - 部分実行・DAG 可視化 (Priority: P3)

**Goal**: ノード範囲指定による部分実行と DAG 可視化の動作確認

**Independent Test**: `kedro run --from-nodes=extract_knowledge --to-nodes=format_markdown` で Transform のみ実行される

### 入力

- [x] T149 Read previous phase output: specs/044-kedro-migration/tasks/ph8-output.md

### テスト実装 (RED)

- [x] T150 [P] [US5] Implement test_partial_run_from_to in tests/test_integration.py (--from-nodes / --to-nodes で指定ノード範囲のみ実行)
- [x] T151 [P] [US5] Implement test_pipeline_node_names in tests/test_integration.py (全ノード名が期待通りに登録されている)
- [x] T152 Verify `make test` FAIL (RED)
- [x] T153 Generate RED output: specs/044-kedro-migration/red-tests/ph9-test.md

### 実装 (GREEN)

- [x] T154 Read RED tests: specs/044-kedro-migration/red-tests/ph9-test.md
- [x] T155 [US5] Ensure all nodes have unique, meaningful names in pipeline definitions (src/obsidian_etl/pipelines/*/pipeline.py)
- [x] T156 [US5] Install kedro-viz and verify `kedro viz` renders DAG correctly
- [x] T157 Verify `make test` PASS (GREEN)

### 検証

- [x] T158 Verify `make test` passes all tests (no regressions)
- [x] T159 Generate phase output: specs/044-kedro-migration/tasks/ph9-output.md

**Checkpoint**: Partial execution and DAG visualization work correctly. US5 complete.

---

## Phase 10: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: 旧コード削除、ドキュメント更新、最終検証

### 入力

- [ ] T160 Read previous phase output: specs/044-kedro-migration/tasks/ph9-output.md

### 実装

- [ ] T161 [P] Delete src/etl/ (旧 ETL パイプライン全体)
- [ ] T162 [P] Remove old ETL-related Makefile targets (make import, make organize, make retry, make status, make item-trace, make session-clean)
- [ ] T163 [P] Remove old .staging/@session/ references from CLAUDE.md
- [ ] T164 Update CLAUDE.md with new Kedro-based commands and data flow
- [ ] T165 Update pyproject.toml with Kedro dependencies and entry points
- [ ] T166 Run quickstart.md validation: verify all commands in specs/044-kedro-migration/quickstart.md work
- [ ] T167 [P] Verify `kedro run --pipeline=import_claude` end-to-end with real data (manual test)
- [ ] T168 [P] Verify `kedro run --pipeline=import_openai` end-to-end with real data (manual test)
- [ ] T169 [P] Verify `kedro run --pipeline=import_github` end-to-end with real data (manual test)

### 検証

- [ ] T170 Run `make test` to verify all tests pass after cleanup
- [ ] T171 Generate phase output: specs/044-kedro-migration/tasks/ph10-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — メインエージェント直接実行
- **US1 Extract (Phase 2)**: Depends on Phase 1 — TDD フロー
- **US1 Transform (Phase 3)**: Depends on Phase 2 — TDD フロー
- **US1 Organize (Phase 4)**: Depends on Phase 3 — TDD フロー
- **US1 E2E (Phase 5)**: Depends on Phase 4 — TDD フロー
- **US2 Resume (Phase 6)**: Depends on Phase 5 — TDD フロー
- **US3 OpenAI (Phase 7)**: Depends on Phase 6 — TDD フロー (independent from US4)
- **US4 GitHub (Phase 8)**: Depends on Phase 7 — TDD フロー (independent from US3, sequential for simplicity)
- **US5 Partial Exec (Phase 9)**: Depends on Phase 8 — TDD フロー
- **Polish (Phase 10)**: Depends on all phases — phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **入力**: Read previous phase output (context from prior work)
2. **テスト実装 (RED)**: Write tests FIRST → verify `make test` FAIL → generate RED output
3. **実装 (GREEN)**: Read RED tests → implement → verify `make test` PASS
4. **検証**: Confirm no regressions → generate phase output

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-9 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 10 (Polish)**: phase-executor のみ

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。並列実行を保証するものではない。

- Setup タスクの [P]: 異なるファイル・ディレクトリの作成で相互依存なし
- RED テストの [P]: 異なるテストファイルへの書き込みで相互依存なし
- GREEN 実装の [P]: 異なるソースファイルへの書き込みで相互依存なし
- User Story 間: 各 Phase は前 Phase の出力に依存するため [P] 不可

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/044-kedro-migration/
├── tasks.md                      # This file
├── tasks/
│   ├── ph1-output.md             # Phase 1 output (Setup results)
│   ├── ph2-output.md             # Phase 2 output (US1 Extract GREEN)
│   ├── ph3-output.md             # Phase 3 output (US1 Transform GREEN)
│   ├── ph4-output.md             # Phase 4 output (US1 Organize GREEN)
│   ├── ph5-output.md             # Phase 5 output (US1 E2E GREEN)
│   ├── ph6-output.md             # Phase 6 output (US2 Resume GREEN)
│   ├── ph7-output.md             # Phase 7 output (US3 OpenAI GREEN)
│   ├── ph8-output.md             # Phase 8 output (US4 GitHub GREEN)
│   ├── ph9-output.md             # Phase 9 output (US5 Partial Exec GREEN)
│   └── ph10-output.md            # Phase 10 output (Polish)
└── red-tests/
    ├── ph2-test.md               # Phase 2 RED (US1 Extract)
    ├── ph3-test.md               # Phase 3 RED (US1 Transform)
    ├── ph4-test.md               # Phase 4 RED (US1 Organize)
    ├── ph5-test.md               # Phase 5 RED (US1 E2E)
    ├── ph6-test.md               # Phase 6 RED (US2 Resume)
    ├── ph7-test.md               # Phase 7 RED (US3 OpenAI)
    ├── ph8-test.md               # Phase 8 RED (US4 GitHub)
    └── ph9-test.md               # Phase 9 RED (US5 Partial Exec)
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

### MVP First (Phase 1 + Phase 2-5)

1. Complete Phase 1: Setup (Kedro project, utils migration)
2. Complete Phase 2: US1 Extract (Claude JSON → ParsedItem)
3. Complete Phase 3: US1 Transform (LLM knowledge extraction)
4. Complete Phase 4: US1 Organize (Genre classification → Vault)
5. Complete Phase 5: US1 E2E (Pipeline registry, hooks, integration)
6. **STOP and VALIDATE**: `kedro run --pipeline=import_claude` で Claude インポート一気通貫を確認

### Full Delivery

1. Phase 1 → Phase 2 → ... → Phase 10
2. Each phase commits: `feat(044-kedro): phase-N description`

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[Raw JSON/ZIP] → [Parse] → [Validate] → [Chunk] → [LLM Extract] → [Metadata] → [Format MD] → [Classify] → [Vault]
      ↓             ↓          ↓           ↓            ↓              ↓             ↓            ↓           ↓
    テスト        テスト      テスト      テスト        テスト          テスト         テスト       テスト      テスト
```

**チェックリスト**:
- [ ] Extract 入力パースのテスト（各プロバイダー）
- [ ] バリデーションロジックのテスト（構造・コンテンツ・メッセージ数）
- [ ] チャンク分割のテスト（閾値超え・メタデータ保存）
- [ ] LLM 知識抽出のテスト（モック Ollama）
- [ ] メタデータ生成のテスト（file_id, created, tags）
- [ ] Markdown フォーマットのテスト（frontmatter + body）
- [ ] ジャンル判定のテスト（キーワードマッチ）
- [ ] Vault 配置のテスト（パスマッピング）
- [ ] 冪等性のテスト（2回目実行でスキップ）
- [ ] E2E 統合テスト（入力→最終出力）

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD: テスト実装 (RED) → FAIL 確認 → 実装 (GREEN) → PASS 確認
- RED output must be generated BEFORE implementation begins
- Commit after each phase completion
- Stop at any checkpoint to validate story independently
- US1 is split across Phase 2-5 because Claude import spans Extract → Transform → Organize → E2E integration
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
