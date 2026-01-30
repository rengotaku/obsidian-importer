# Tasks: ChatGPT エクスポートインポート

**Input**: Design documents from `/specs/030-chatgpt-import/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: テスト要求なし - 回帰テストのみ実施（NFR-002: 既存 Claude インポートテストがパスすること）

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/etl/` at repository root (既存 ETL 構造を拡張)

---

## Phase 1: Setup

**Purpose**: Project initialization - 最小限（既存構造を拡張するため）

- [x] T001 Verify current branch is `030-chatgpt-import` and clean working tree
- [x] T002 Run `make test` to verify existing tests pass before changes
- [x] T003 Generate phase output: specs/030-chatgpt-import/tasks/ph1-output.md

---

## Phase 2: Foundational (ZIP ハンドリング)

**Purpose**: ChatGPT ZIP 展開の基盤 - User Story 1, 2 の前提条件

**⚠️ CRITICAL**: この Phase が完了するまで User Story の実装は開始できない

- [x] T004 Read previous phase output: specs/030-chatgpt-import/tasks/ph1-output.md
- [x] T005 [P] Create `src/etl/utils/zip_handler.py` with `read_conversations_from_zip()` function
- [x] T006 [P] Create `src/etl/stages/extract/chatgpt_extractor.py` with stub implementation
- [x] T007 Run `make test` to verify no regressions
- [x] T008 Generate phase output: specs/030-chatgpt-import/tasks/ph2-output.md

**Checkpoint**: ZIP 読み込み基盤完了 - User Story 実装開始可能

---

## Phase 3: User Story 1 - 基本インポート (Priority: P1) 🎯 MVP

**Goal**: ZIP ファイルから会話を抽出し、Markdown ファイルを生成

**Independent Test**: `make import INPUT=test.zip PROVIDER=openai` で Markdown ファイルが生成される

### Implementation for User Story 1

- [x] T009 Read previous phase output: specs/030-chatgpt-import/tasks/ph2-output.md
- [x] T010 [US1] Implement `traverse_messages()` in `src/etl/stages/extract/chatgpt_extractor.py` (mapping ツリー走査)
- [x] T011 [US1] Implement `ChatGPTExtractor.discover_items()` in `src/etl/stages/extract/chatgpt_extractor.py` (ZIP → ProcessingItem)
- [x] T012 [US1] Implement message content extraction (parts[] → text) in `src/etl/stages/extract/chatgpt_extractor.py`
- [x] T013 [US1] Implement role conversion (user→human, system/tool→除外) in `src/etl/stages/extract/chatgpt_extractor.py`
- [x] T014 [US1] Implement timestamp conversion (Unix→YYYY-MM-DD) per FR-003 in `src/etl/stages/extract/chatgpt_extractor.py`
- [x] T015 [US1] Add `source_provider: openai` to metadata in `src/etl/stages/extract/chatgpt_extractor.py`
- [x] T016 Run `make test` to verify no regressions
- [x] T017 Generate phase output: specs/030-chatgpt-import/tasks/ph3-output.md

**Checkpoint**: ChatGPT Extractor 完成 - 単体で動作可能

---

## Phase 4: User Story 2 - メタデータ抽出 (Priority: P1)

**Goal**: 既存 Transform ステージを使用して summary, tags を LLM 抽出

**Independent Test**: 生成された Markdown の frontmatter に title, summary, tags, created, source_provider, item_id が含まれる

### Implementation for User Story 2

- [x] T018 Read previous phase output: specs/030-chatgpt-import/tasks/ph3-output.md
- [x] T019 [US2] Verify ChatGPTExtractor output is compatible with KnowledgeTransformer input format
- [x] T020 [US2] Add integration test: ChatGPT ZIP → Transform → expected frontmatter fields
- [x] T021 Run `make test` to verify Transform integration works
- [x] T022 Generate phase output: specs/030-chatgpt-import/tasks/ph4-output.md

**Checkpoint**: Transform 統合完了 - LLM メタデータ抽出が動作

---

## Phase 5: User Story 3 - 既存パイプライン統合 (Priority: P2)

**Goal**: `--provider openai` オプションで Claude/ChatGPT を切り替え

**Independent Test**: `python -m src.etl import --input PATH --provider openai` が動作

### Implementation for User Story 3

- [x] T023 Read previous phase output: specs/030-chatgpt-import/tasks/ph4-output.md
- [x] T024 [US3] Add `provider` parameter to `ImportPhase.__init__()` in `src/etl/phases/import_phase.py`
- [x] T025 [US3] Implement provider branch in `ImportPhase.create_extract_stage()` in `src/etl/phases/import_phase.py`
- [x] T026 [US3] Add `--provider` option to `import` command in `src/etl/cli.py`
- [x] T027 [US3] Verify default behavior (no --provider) still uses Claude extractor
- [x] T028 Run `make test` to verify Claude import still works (CC-001〜CC-004 検証)
- [x] T029 Generate phase output: specs/030-chatgpt-import/tasks/ph5-output.md

**Checkpoint**: CLI 統合完了 - `--provider` オプションが動作

---

## Phase 6: User Story 4 - 短い会話のスキップ (Priority: P2)

**Goal**: メッセージ数 < MIN_MESSAGES の会話をスキップ

**Independent Test**: メッセージ数 2 以下の会話がスキップされ、ログに記録される

### Implementation for User Story 4

- [x] T030 Read previous phase output: specs/030-chatgpt-import/tasks/ph5-output.md
- [x] T031 [US4] Add message count validation in `ChatGPTExtractor.discover_items()` in `src/etl/stages/extract/chatgpt_extractor.py`
- [x] T032 [US4] Exclude system/tool messages from count in `src/etl/stages/extract/chatgpt_extractor.py`
- [x] T033 [US4] Log skipped conversations with reason `skipped_short`
- [x] T034 Run `make test` to verify no regressions
- [x] T035 Generate phase output: specs/030-chatgpt-import/tasks/ph6-output.md

**Checkpoint**: スキップロジック完了

---

## Phase 7: User Story 5 - 重複検出 (Priority: P2)

**Goal**: file_id で重複を検出し、上書き

**Independent Test**: 同じ会話を2回インポートしても、1ファイルのみ存在

### Implementation for User Story 5

- [x] T036 Read previous phase output: specs/030-chatgpt-import/tasks/ph6-output.md
- [x] T037 [US5] Generate file_id from conversation content hash in `src/etl/stages/extract/chatgpt_extractor.py`
- [x] T038 [US5] Verify existing file_id logic in SessionLoader handles overwrite
- [x] T039 Run `make test` to verify no regressions
- [x] T040 Generate phase output: specs/030-chatgpt-import/tasks/ph7-output.md

**Checkpoint**: 重複検出完了

---

## Phase 8: User Story 6 - 添付ファイル処理 (Priority: P3)

**Goal**: 画像・音声をプレースホルダーとして処理

**Independent Test**: 添付ファイルがある会話でもエラーにならない

### Implementation for User Story 6

- [x] T041 Read previous phase output: specs/030-chatgpt-import/tasks/ph7-output.md
- [x] T042 [US6] Handle `image_asset_pointer` in content.parts as `[Image: filename]` placeholder (format: `[Image: {asset_pointer}]`) - Already implemented
- [x] T043 [US6] Handle audio files as `[Audio: filename]` placeholder (format: `[Audio: {filename}]`)
- [x] T044 [US6] Ensure multimodal conversations don't cause errors (text extraction continues normally)
- [x] T045 Run `make test` to verify no regressions
- [x] T046 Generate phase output: specs/030-chatgpt-import/tasks/ph8-output.md

**Checkpoint**: マルチモーダル対応完了

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: ドキュメント更新、エッジケース対応

- [x] T047 Read previous phase output: specs/030-chatgpt-import/tasks/ph8-output.md
- [x] T048 [P] Handle edge case: empty conversations.json (warning log, exit 0)
- [x] T049 [P] Handle edge case: corrupted ZIP (error message, exit 2)
- [x] T050 [P] Handle edge case: missing title (generate from first user message)
- [x] T051 [P] Handle edge case: missing timestamp (fallback to current date)
- [x] T052 Update CLAUDE.md with ChatGPT import instructions
- [x] T053 Run `make test` to verify all tests pass (final regression check)
- [x] T054 Run quickstart.md validation with real ChatGPT export (Manual validation required)
- [x] T055 Generate phase output: specs/030-chatgpt-import/tasks/ph9-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: ZIP handling) ← BLOCKS all user stories
    ↓
Phase 3 (US1: 基本インポート) ← MVP
    ↓
Phase 4 (US2: メタデータ抽出)
    ↓
Phase 5 (US3: パイプライン統合)
    ↓
Phase 6 (US4: スキップ) ─┐
Phase 7 (US5: 重複検出) ─┼─ Can run in parallel after Phase 5
Phase 8 (US6: 添付)    ─┘
    ↓
Phase 9 (Polish)
```

### User Story Dependencies

- **US1 (基本インポート)**: Phase 2 完了後開始可能
- **US2 (メタデータ)**: US1 完了後（Transform 入力形式確認のため）
- **US3 (CLI統合)**: US1 完了後（Extractor が必要）
- **US4, US5, US6**: US3 完了後（独立して並列実行可能）

### Claude 互換性検証ポイント

| Task | 検証内容 |
|------|---------|
| T002 | 変更前のテスト全パス確認 |
| T027 | デフォルト動作が Claude のまま |
| T028 | 変更後も Claude テストがパス |
| T053 | 最終回帰テスト |

---

## Parallel Opportunities

### Phase 2 (Foundational)
```bash
# 並列実行可能:
T005: src/etl/utils/zip_handler.py
T006: src/etl/stages/extract/chatgpt_extractor.py (stub)
```

### Phase 6-8 (After Phase 5)
```bash
# US4, US5, US6 は並列実行可能（異なる機能）
Phase 6: 短い会話スキップ
Phase 7: 重複検出
Phase 8: 添付ファイル
```

### Phase 9 (Polish)
```bash
# エッジケース処理は並列実行可能:
T048: empty conversations.json
T049: corrupted ZIP
T050: missing title
T051: missing timestamp
```

---

## Implementation Strategy

### MVP First (User Story 1-3)

1. Phase 1-2: Setup + Foundational
2. Phase 3: US1 (基本インポート) ← **ここで動作確認可能**
3. Phase 4: US2 (メタデータ) ← **ここで実用レベル**
4. Phase 5: US3 (CLI統合) ← **ここで本番利用可能**
5. **STOP and VALIDATE**: 実際の ChatGPT エクスポートでテスト

### Incremental Delivery

| Phase | 成果物 | 価値 |
|-------|--------|------|
| 3 | Extractor 動作 | 技術検証完了 |
| 4 | LLM 抽出動作 | ナレッジ価値あり |
| 5 | CLI 統合 | ユーザー利用可能 |
| 6-8 | 品質向上 | 本番運用品質 |

---

## Test Coverage

**境界テスト対象**:
- [ ] 入力: ZIP → conversations.json パース
- [ ] 変換: mapping → フラットメッセージリスト
- [ ] 変換: Unix timestamp → YYYY-MM-DD
- [ ] 変換: author.role → sender
- [ ] 出力: ProcessingItem → Markdown (既存 Transform/Load)

**回帰テスト**:
- 既存の Claude インポートテストが 100% パス (NFR-002, SC-004)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- CC-001〜CC-004: Claude 互換性制約を遵守
- 各 Phase 終了時に `make test` で回帰確認必須
- Phase 出力ファイルは日本語で記述
