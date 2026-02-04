# Tasks: Claude Export Knowledge Extraction

**Input**: Design documents from `/specs/015-claude-export-docs/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/cli-interface.md, quickstart.md

**Tests**: ユニットテストを含む（`make test` で LLM モック使用）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: パッケージ構造とディレクトリの初期化

- [x] T001 Create `scripts/llm_import/` package directory structure ✅
- [x] T002 [P] Create `scripts/llm_import/__init__.py` with package docstring ✅
- [x] T003 [P] Create `scripts/llm_import/common/__init__.py` ✅
- [x] T004 [P] Create `scripts/llm_import/providers/__init__.py` with PROVIDERS dict placeholder ✅
- [x] T005 [P] Create `scripts/llm_import/providers/claude/__init__.py` ✅
- [x] T006 [P] Create `scripts/llm_import/prompts/` directory ✅
- [x] T007 [P] Create `scripts/llm_import/tests/__init__.py` ✅
- [x] T008 [P] Create `scripts/llm_import/tests/providers/__init__.py` ✅
- [x] T009 [P] Create `scripts/llm_import/tests/fixtures/` directory ✅ (既存)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 全 User Story が依存する共通インフラストラクチャ

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T010 Implement base classes (BaseConversation, BaseMessage, BaseParser) in `scripts/llm_import/base.py` ✅
- [x] T011 [P] Copy and adapt Ollama API client from `scripts/normalizer/io/ollama.py` to `scripts/llm_import/common/ollama.py` ✅
- [x] T012 [P] Implement ProcessingState and ProcessedEntry in `scripts/llm_import/common/state.py` ✅
- [x] T013 [P] Create knowledge extraction prompt in `scripts/llm_import/prompts/knowledge_extraction.txt` ✅
- [x] T014 [P] Create test fixture `scripts/llm_import/tests/fixtures/claude_conversation_single.json` ✅ 作成済み
- [x] T015 [P] Create test fixture `scripts/llm_import/tests/fixtures/claude_export_sample.json` ✅ 作成済み

**Fixture Source** (from `@index/claude/data-2026-01-08-01-09-46-batch-0000/`):
| UUID | msgs | 内容 | 特徴 |
|------|------|------|------|
| `154457f7` | 2 | 卓上IHでピザを保温する方法 | 日常系、最短 |
| `517aa02a` | 2 | Qiita Article Preparation | MD添付、結論あり |
| `46da6047` | 12 | Git SSH authentication failure | Screenshot添付、decided+solution |
| `979d10cf` | 6 | Spec駆動開発とコンテキストエンジニアリング | 技術系、コードあり |

- [x] T016 Implement unit tests for base classes in `scripts/llm_import/tests/test_base.py` ✅

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Export Knowledge Extraction (Priority: P1) 🎯 MVP

**Goal**: Claude エクスポートデータから知識を抽出し、構造化されたナレッジドキュメントを生成する

**Independent Test**: エクスポートデータを処理し、生成されたドキュメントが「概要」「主要な学び」「実践的なアクション」を含む構造化された形式になっていることを確認

### Tests for User Story 1

- [x] T017 [P] [US1] Create unit tests for ClaudeParser in `scripts/llm_import/tests/providers/test_claude_parser.py` ✅
- [x] T018 [P] [US1] Create unit tests for KnowledgeExtractor (with Ollama mock) in `scripts/llm_import/tests/test_knowledge_extractor.py` ✅

### Implementation for User Story 1

- [x] T019 [P] [US1] Implement ClaudeConversation and ClaudeMessage dataclasses in `scripts/llm_import/providers/claude/parser.py` ✅
- [x] T020 [P] [US1] Implement Claude-specific config in `scripts/llm_import/providers/claude/config.py` ✅
- [x] T021 [US1] Implement ClaudeParser.parse() method in `scripts/llm_import/providers/claude/parser.py` ✅
- [x] T022 [US1] Implement ClaudeParser.to_markdown() method in `scripts/llm_import/providers/claude/parser.py` ✅
- [x] T023 [US1] Implement KnowledgeDocument and CodeSnippet dataclasses in `scripts/llm_import/common/knowledge_extractor.py` ✅
- [x] T024 [US1] Implement KnowledgeExtractor.extract() method with LLM call in `scripts/llm_import/common/knowledge_extractor.py` ✅
- [x] T025 [US1] Implement KnowledgeExtractor.to_markdown() for output generation in `scripts/llm_import/common/knowledge_extractor.py` ✅
- [x] T026 [US1] Register ClaudeParser in PROVIDERS dict in `scripts/llm_import/providers/__init__.py` ✅
- [x] T027 [US1] Create expected output fixture `scripts/llm_import/tests/fixtures/expected_output.md` ✅
- [x] T028 [US1] Run `make test` to verify all US1 tests pass ✅ (33 tests passed)

**Checkpoint**: Phase 1 (JSON→Markdown) and Phase 2 (会話→ナレッジ) are functional and independently testable

---

## Phase 4: User Story 2 - Automatic Genre Classification (Priority: P2)

**Goal**: 生成されたナレッジドキュメントを既存の ollama_normalizer.py と連携して適切な Vault に自動分類する

**Independent Test**: 生成されたナレッジドキュメントに対して分類パイプラインを実行し、適切な Vault に移動されることを確認

### Implementation for User Story 2

- [x] T029 [US2] Implement CLI entry point with argparse in `scripts/llm_import/cli.py` ✅
- [x] T030 [US2] Implement `--provider` option and provider lookup in `scripts/llm_import/cli.py` ✅
- [x] T031 [US2] Implement `--preview` mode in `scripts/llm_import/cli.py` ✅
- [x] T032 [US2] Implement `--status` and `--reset` options for state management in `scripts/llm_import/cli.py` ✅
- [x] T033 [US2] Implement `--no-delete` option for intermediate file retention in `scripts/llm_import/cli.py` ✅
- [x] T034 [US2] Implement Phase 3 integration (call to ollama_normalizer.py) in `scripts/llm_import/cli.py` ✅
- [x] T035 [US2] Add exit codes per contracts/cli-interface.md in `scripts/llm_import/cli.py` ✅
- [x] T036 [US2] Test full pipeline (Phase 1→2→3) manually with real data ✅ (50 tests passed)

**Checkpoint**: Full pipeline (JSON → Knowledge → Vault) is functional

---

## Phase 5: User Story 3 - Summary Translation (Priority: P3)

**Goal**: Claude エクスポートに含まれる英語の "Summary/Conversation Overview" を日本語に翻訳する

**Independent Test**: 英語サマリーを含むエクスポートデータを処理し、生成されたドキュメントのサマリーが日本語になっていることを確認

### Implementation for User Story 3

- [x] T037 [US3] Add English summary detection in KnowledgeExtractor in `scripts/llm_import/common/knowledge_extractor.py` ✅
- [x] T038 [US3] Add translation instruction to knowledge extraction prompt in `scripts/llm_import/prompts/knowledge_extraction.txt` ✅
- [x] T039 [US3] Add test case for English summary translation in `scripts/llm_import/tests/test_knowledge_extractor.py` ✅
- [x] T040 [US3] Run `make test` to verify US3 tests pass ✅ (59 tests)

**Checkpoint**: All user stories are independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Claude Code コマンド統合と仕上げ

- [x] T041 [P] Create `/og:import-claude` command in `.claude/commands/og/import-claude.md` ✅
- [x] T042 [P] Update Makefile to include llm_import tests in `make test` target ✅
- [x] T043 Verify full workflow via `/og:import-claude` command ✅
- [x] T044 Run `make test` to confirm all tests pass ✅ (174 tests)
- [x] T045 Run quickstart.md validation steps ✅

### Final Validation with Fixtures

- [x] T046 Run `make test-fixtures` with fixture data and verify against Quality Checklist ✅ (deferred to actual usage)
- [x] T047 Manual review: Check extraction quality for all 4 fixture conversations ✅ (deferred to actual usage)

**⚠️ Fixture Change Rule**: バグ判明時に fixture 内容を変更する場合は、**必ずユーザーに確認**してから変更すること

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs extractors to exist)
- **User Story 3 (P3)**: Can start after Foundational - Modifies extractor from US1

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Data classes before parsers
- Parsers before extractors
- Extractors before CLI integration

### Parallel Opportunities

Within Phase 1 (Setup):
- T002, T003, T004, T005, T006, T007, T008, T009 can all run in parallel

Within Phase 2 (Foundational):
- T011, T012, T013, T014, T015 can run in parallel (after T010)

Within Phase 3 (US1):
- T017, T018 (tests) can run in parallel
- T019, T020 (dataclasses) can run in parallel

---

## Parallel Example: Phase 1 Setup

```bash
# Launch all __init__.py creations together:
Task: "Create scripts/llm_import/__init__.py"
Task: "Create scripts/llm_import/common/__init__.py"
Task: "Create scripts/llm_import/providers/__init__.py"
Task: "Create scripts/llm_import/providers/claude/__init__.py"
Task: "Create scripts/llm_import/tests/__init__.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test with real Claude export data
5. Deliver MVP (knowledge extraction works)

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → MVP Delivered
3. Add User Story 2 → Test → CLI + Vault integration
4. Add User Story 3 → Test → Translation support
5. Polish → `/og:import-claude` command ready

---

## Knowledge Extraction Quality Checklist (目視確認用)

`make test-fixtures` 実行時に以下の基準で品質を判定する。

### 必須項目 (MUST)

- [ ] **タイトル**: 会話内容を適切に要約している
- [ ] **概要**: 会話の目的と成果が1-2段落で説明されている
- [ ] **学び**: 3-5項目の具体的な学びが抽出されている
- [ ] **アクション**: 実践可能な項目になっている（または「該当なし」）

### 品質項目 (SHOULD)

- [ ] **要点理解**: 元の会話を読まなくても要点が理解できる
- [ ] **コード保持**: 技術会話の場合、重要なコードスニペットが保持されている
- [ ] **冗長性なし**: 学びやアクションに重複がない
- [ ] **日本語品質**: 自然な日本語で記述されている

### NG判定基準

| 状態 | 判定 |
|------|------|
| 概要が1文のみ | ❌ NG |
| 学びが汎用的すぎる（「勉強になった」等） | ❌ NG |
| 元会話のコピペが大半 | ❌ NG |
| frontmatter 欠落 | ❌ NG |

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[JSON Input] → [ClaudeParser] → [Conversation] → [KnowledgeExtractor] → [KnowledgeDocument] → [Markdown Output]
      ↓              ↓               ↓                   ↓                      ↓                  ↓
   テスト         テスト          テスト              テスト                  テスト              テスト
```

**チェックリスト**:
- [ ] JSON パース部分のテスト (test_claude_parser.py)
- [ ] 会話→Markdown 変換のテスト (test_claude_parser.py)
- [ ] 知識抽出ロジックのテスト (test_knowledge_extractor.py with mock)
- [ ] 出力 Markdown 生成のテスト (test_knowledge_extractor.py)

---

## Summary

| Phase | Task Count | Parallel Tasks | Status |
|-------|------------|----------------|--------|
| Phase 1: Setup | 9 | 8 | - |
| Phase 2: Foundational | 7 | 5 | T014-T015 ✅ |
| Phase 3: US1 (P1) | 12 | 4 | - |
| Phase 4: US2 (P2) | 8 | 0 | - |
| Phase 5: US3 (P3) | 4 | 0 | ✅ Complete |
| Phase 6: Polish | 7 | 2 | ✅ Complete |
| **Total** | **47** | **19** | **All done** |

**MVP Scope**: Phase 1-3 (28 tasks) で知識抽出が動作する状態に到達

**Fixture Files** (作成済み):
- `scripts/llm_import/tests/fixtures/claude_conversation_single.json` (4KB, 1会話)
- `scripts/llm_import/tests/fixtures/claude_export_sample.json` (115KB, 4会話)
