# Tasks: LLM レスポンス形式をマークダウンに変更

**Input**: Design documents from `/specs/042-llm-markdown-response/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Organization**: US1（プロンプト変更）と US2（パーサー実装）は密結合のため Phase 2 で一括 TDD 実装。US3（後方互換性）は Phase 3 で統合検証。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: 既存コードの確認と変更準備

- [ ] T001 Read current prompt templates: src/etl/prompts/knowledge_extraction.txt and src/etl/prompts/summary_translation.txt
- [ ] T002 Read current parser functions in src/etl/utils/ollama.py (parse_json_response, extract_json_from_code_block, extract_first_json_object)
- [ ] T003 Read current knowledge extractor calls in src/etl/utils/knowledge_extractor.py (extract method, translate_summary method)
- [ ] T004 Read existing tests in src/etl/tests/test_ollama.py and src/etl/tests/test_knowledge_extractor.py
- [ ] T005 Generate phase output: specs/042-llm-markdown-response/tasks/ph1-output.md

---

## Phase 2: User Story 1 + 2 - マークダウンパーサー実装 & プロンプト変更 (Priority: P1)

**Goal**: LLM レスポンス形式を JSON → マークダウンに切り替え。`parse_markdown_response()` を実装し、プロンプトテンプレートを更新する。

**Independent Test**: `parse_markdown_response()` に各種マークダウン入力を与え、正しい dict が返ることを確認する。

### 入力
- [ ] T006 Read previous phase output: specs/042-llm-markdown-response/tasks/ph1-output.md

### テスト実装 (RED)
- [x] T007 [P] [US2] Implement tests for parse_markdown_response() in src/etl/tests/test_ollama.py: 標準マークダウン入力（# タイトル + ## 要約 + ## 内容）→ dict 変換
- [x] T008 [P] [US2] Implement tests for parse_markdown_response() edge cases in src/etl/tests/test_ollama.py: コードブロックフェンス除去、見出しレベル違い（## や ### をタイトルとして扱う）、プレーンテキストフォールバック、空入力エラー
- [x] T009 [P] [US2] Implement tests for summary translation markdown parse in src/etl/tests/test_ollama.py: `## 要約` セクションのみの最小マークダウン → dict{"summary": ...} 変換
- [x] T010 [P] [US1] Implement tests for updated knowledge_extractor in src/etl/tests/test_knowledge_extractor.py: extract() が parse_markdown_response を使用し、マークダウンレスポンスから KnowledgeDocument を生成することを確認
- [x] T011 [P] [US1] Implement tests for translate_summary markdown response in src/etl/tests/test_knowledge_extractor.py: translate_summary() がマークダウン形式のレスポンスを正しくパースすることを確認
- [x] T012 Verify `make test` FAIL (RED)
- [x] T013 Generate RED output: specs/042-llm-markdown-response/red-tests/ph2-test.md

### 実装 (GREEN)
- [x] T014 Read RED tests: specs/042-llm-markdown-response/red-tests/ph2-test.md
- [x] T015 [P] [US2] Implement parse_markdown_response() in src/etl/utils/ollama.py: 前処理（コードブロックフェンス除去）→ セクション分割（# / ## 見出し検出）→ dict 構築（title, summary, summary_content）。戻り値は tuple[dict, str | None] で parse_json_response() と同一
- [x] T016 [P] [US1] Update knowledge_extraction.txt prompt in src/etl/prompts/knowledge_extraction.txt: JSON 出力指示をマークダウン出力指示に変更（# タイトル + ## 要約 + ## 内容 の構造を指示）
- [x] T017 [P] [US1] Update summary_translation.txt prompt in src/etl/prompts/summary_translation.txt: JSON 出力指示をマークダウン出力指示に変更（## 要約 セクションのみ）
- [x] T018 [US1] Update knowledge_extractor.py in src/etl/utils/knowledge_extractor.py: parse_json_response() 呼び出しを parse_markdown_response() に置き換え（extract メソッド内および translate_summary メソッド内）
- [x] T019 Verify `make test` PASS (GREEN)

### 検証
- [x] T020 Run `make test` to verify all tests pass
- [x] T021 Generate phase output: specs/042-llm-markdown-response/tasks/ph2-output.md

---

## Phase 3: User Story 3 - 後方互換性検証 (Priority: P2)

**Goal**: 変更後も既存パイプライン（transform → load）が正常に動作することを確認。全既存テストが通過すること。

**Independent Test**: `make test` で全テストが通過し、既存の integration テストも含めて回帰がないことを確認。

### 入力
- [x] T022 Read previous phase output: specs/042-llm-markdown-response/tasks/ph2-output.md

### テスト実装 (RED)
- [x] T023 [US3] Implement integration test in src/etl/tests/test_knowledge_extractor.py: マークダウンレスポンスを受け取った KnowledgeExtractor が to_markdown() で従来と同じフォーマットの Markdown ファイルを生成することを確認（frontmatter title/summary/created、本文の見出しレベル正規化）
- [x] T024 Verify `make test` FAIL (RED) -- 全テスト PASS（Phase 2 実装が既に後方互換）
- [x] T025 Generate RED output: specs/042-llm-markdown-response/red-tests/ph3-test.md

### 実装 (GREEN)
- [x] T026 Read RED tests: specs/042-llm-markdown-response/red-tests/ph3-test.md
- [x] T027 [US3] Fix any issues found in integration test to ensure end-to-end compatibility in src/etl/utils/ollama.py and src/etl/utils/knowledge_extractor.py
- [x] T028 Verify `make test` PASS (GREEN)

### 検証
- [x] T029 Run `make test` to verify all tests pass (including existing tests unchanged from before)
- [x] T030 Generate phase output: specs/042-llm-markdown-response/tasks/ph3-output.md

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: ドキュメント更新、不要コードの整理

- [x] T031 Read previous phase output: specs/042-llm-markdown-response/tasks/ph3-output.md
- [x] T032 [P] Remove or deprecate parse_json_response() related functions in src/etl/utils/ollama.py if no longer referenced (extract_json_from_code_block, extract_first_json_object, format_parse_error)
- [x] T033 [P] Remove JSON parse tests from src/etl/tests/test_ollama.py that are no longer needed
- [x] T034 Run `make test` to verify all tests pass after cleanup
- [x] T035 Generate phase output: specs/042-llm-markdown-response/tasks/ph4-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - メインエージェント直接実行
- **Phase 2 (US1+US2)**: Depends on Phase 1 - TDD フロー (tdd-generator → phase-executor)
- **Phase 3 (US3)**: Depends on Phase 2 - TDD フロー (tdd-generator → phase-executor)
- **Phase 4 (Polish)**: Depends on Phase 3 - phase-executor のみ

### User Story Dependencies

- **US1 (プロンプト変更)** + **US2 (パーサー実装)**: 密結合のため Phase 2 で同時実装
- **US3 (後方互換性)**: US1+US2 完了後に統合検証

### Within Phase 2

- T007-T011: テスト実装（並列可）
- T015-T017: 実装（並列可 — 異なるファイル）
- T018: 統合（T015-T017 完了後）

### Parallel Opportunities

```bash
# Phase 2 テスト実装（並列）:
Task: T007 "parse_markdown_response tests" in tests/test_ollama.py
Task: T008 "edge case tests" in tests/test_ollama.py
Task: T009 "translation parse tests" in tests/test_ollama.py
Task: T010 "knowledge_extractor tests" in tests/test_knowledge_extractor.py
Task: T011 "translate_summary tests" in tests/test_knowledge_extractor.py

# Phase 2 実装（並列）:
Task: T015 "parse_markdown_response()" in utils/ollama.py
Task: T016 "knowledge_extraction.txt prompt" in prompts/
Task: T017 "summary_translation.txt prompt" in prompts/
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup（既存コード確認）
2. Complete Phase 2: US1+US2（パーサー + プロンプト）
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. `make import INPUT=... PROVIDER=claude LIMIT=3 DEBUG=1` で動作確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4
2. Each phase commits: `feat(phase-N): description`

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[LLM レスポンス(MD)] → [前処理] → [セクション分割] → [dict 構築] → [KnowledgeDocument]
         ↓                ↓            ↓                ↓               ↓
       テスト           テスト        テスト           テスト          テスト
```

**チェックリスト**:
- [ ] マークダウン入力パース部分のテスト（T007-T009）
- [ ] フォールバック/エッジケースのテスト（T008）
- [ ] KnowledgeExtractor 統合のテスト（T010-T011）
- [ ] **出力生成部分のテスト**（T023: to_markdown() 結果検証）
- [ ] End-to-End テスト（T023: マークダウン入力→最終 Markdown 出力）

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1+US2 は密結合のため Phase 2 に統合（プロンプトとパーサーは一体で動作）
- parse_json_response() の旧関数は Phase 4 で整理（Phase 2-3 では残存させて安全に移行）
- `make test` は unittest ベース
