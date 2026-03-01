# Tasks: call_ollama 例外ベースリファクタリング + 汎用ログコンテキスト

**Input**: `/specs/063-ollama-exception-refactor/` の設計ドキュメント
**Prerequisites**: plan.md (必須), spec.md (必須), research.md, data-model.md, quickstart.md

**Tests**: TDD は User Story フェーズで必須。各フェーズは Test Implementation (RED) → Implementation (GREEN) → Verification のワークフローに従う。

**Language**: 日本語

**Organization**: タスクは User Story ごとにグループ化され、各ストーリーを独立して実装・テスト可能にする。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: どの User Story に属するか (例: US1, US2, US3)
- 説明には正確なファイルパスを含める

## User Story サマリー

| ID | タイトル | 優先度 | FR | シナリオ |
|----|---------|--------|-----|----------|
| US1 | エラー発生時のファイル特定 | P1 | FR-001〜005 | ログに [file_id] プレフィックスが自動付与 |
| US2 | 例外による明確なエラーハンドリング | P2 | FR-006〜012 | call_ollama が例外をスロー |
| US3 | エラー詳細情報の保持 | P3 | FR-011 | 例外から context_len 取得可能 |

**注**: US3 は US2 の実装に含まれるため、Phase 3 で統合して実装する。

## パス規約

- **プロジェクトタイプ**: Single project (Kedro パイプライン)
- **ソース**: `src/obsidian_etl/`
- **テスト**: `tests/`
- **設定**: `conf/base/`

---

## Phase 1: Setup (既存コード確認) — NO TDD

**目的**: 現状の実装を確認し、影響範囲を特定する

- [x] T001 現在の call_ollama 実装を確認: src/obsidian_etl/utils/ollama.py
- [x] T002 [P] 呼び出し元を確認: src/obsidian_etl/utils/knowledge_extractor.py (2箇所)
- [x] T003 [P] 呼び出し元を確認: src/obsidian_etl/pipelines/organize/nodes.py (3箇所 + 手動プレフィックス)
- [x] T004 [P] パーティション処理を確認: src/obsidian_etl/pipelines/transform/nodes.py
- [x] T005 [P] パーティション処理を確認: src/obsidian_etl/pipelines/extract_claude/nodes.py
- [x] T006 [P] パーティション処理を確認: src/obsidian_etl/pipelines/extract_openai/nodes.py
- [x] T007 [P] 既存の Ollama テストを確認: tests/utils/test_ollama*.py
- [x] T008 [P] 既存の logging 設定を確認: conf/base/logging.yml
- [x] T009 Edit: specs/063-ollama-exception-refactor/tasks/ph1-output.md

---

## Phase 2: User Story 1 - エラー発生時のファイル特定 (Priority: P1) MVP

**Goal**: パーティション処理中のすべてのログに `[file_id]` プレフィックスが自動付与される

**Independent Test**: `set_file_id("abc123")` 後にログ出力し、出力に `[abc123]` が含まれることを検証

### Input

- [x] T010 Read previous phase output: specs/063-ollama-exception-refactor/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T011 [P] [US1] set_file_id/get_file_id/clear_file_id のテストを実装: tests/utils/test_log_context.py
- [x] T012 [P] [US1] ContextAwareFormatter のテストを実装（file_id ありの場合）: tests/utils/test_log_context.py
- [x] T013 [P] [US1] ContextAwareFormatter のテストを実装（file_id なしの場合）: tests/utils/test_log_context.py
- [x] T014 Verify `make test` FAIL (RED)
- [x] T015 Generate RED output: specs/063-ollama-exception-refactor/red-tests/ph2-test.md

### Implementation (GREEN)

- [x] T016 Read RED tests: specs/063-ollama-exception-refactor/red-tests/ph2-test.md
- [x] T017 [P] [US1] log_context モジュールを作成（contextvars 定義）: src/obsidian_etl/utils/log_context.py
- [x] T018 [P] [US1] ContextAwareFormatter を実装: src/obsidian_etl/utils/log_context.py
- [x] T019 [US1] logging.yml にカスタムフォーマッターを設定: conf/base/logging.yml
- [x] T020 Verify `make test` PASS (GREEN)

### Verification

- [x] T021 Verify `make test` passes all tests (no regressions)
- [x] T022 Edit: specs/063-ollama-exception-refactor/tasks/ph2-output.md

**Checkpoint**: ログコンテキスト機能が独立して動作することを確認

---

## Phase 3: User Story 2 + 3 - 例外による明確なエラーハンドリング (Priority: P2)

**Goal**: call_ollama が例外をスローし、呼び出し元で適切にキャッチできる。例外から context_len を取得できる。

**Independent Test**: call_ollama に空レスポンスを返すモックを設定し、OllamaEmptyResponseError がスローされ、context_len 属性が取得できることを検証

### Input

- [x] T023 Read setup analysis: specs/063-ollama-exception-refactor/tasks/ph1-output.md
- [x] T024 Read previous phase output: specs/063-ollama-exception-refactor/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T025 [P] [US2] OllamaError 基底クラスのテストを実装: tests/utils/test_ollama_exceptions.py
- [x] T026 [P] [US2] OllamaEmptyResponseError のテストを実装: tests/utils/test_ollama_exceptions.py
- [x] T027 [P] [US2] OllamaTimeoutError のテストを実装: tests/utils/test_ollama_exceptions.py
- [x] T028 [P] [US2] OllamaConnectionError のテストを実装: tests/utils/test_ollama_exceptions.py
- [x] T029 [P] [US3] context_len 属性のテストを実装: tests/utils/test_ollama_exceptions.py
- [x] T030 [P] [US2] call_ollama 空レスポンス時の例外スローテストを実装: tests/utils/test_ollama.py
- [x] T031 [P] [US2] call_ollama タイムアウト時の例外スローテストを実装: tests/utils/test_ollama.py
- [x] T032 [P] [US2] call_ollama 正常時の戻り値テストを実装: tests/utils/test_ollama.py
- [x] T033 Verify `make test` FAIL (RED)
- [x] T034 Generate RED output: specs/063-ollama-exception-refactor/red-tests/ph3-test.md

### Implementation (GREEN)

- [x] T035 Read RED tests: specs/063-ollama-exception-refactor/red-tests/ph3-test.md
- [x] T036 [P] [US2] OllamaError 基底クラスを実装: src/obsidian_etl/utils/ollama.py
- [x] T037 [P] [US2] OllamaEmptyResponseError を実装: src/obsidian_etl/utils/ollama.py
- [x] T038 [P] [US2] OllamaTimeoutError を実装: src/obsidian_etl/utils/ollama.py
- [x] T039 [P] [US2] OllamaConnectionError を実装: src/obsidian_etl/utils/ollama.py
- [x] T040 [US2] call_ollama を例外ベースに変更: src/obsidian_etl/utils/ollama.py
- [x] T041 Verify `make test` PASS (GREEN) - 新規テストのみ

### Verification

- [x] T042 Verify `make test` passes all tests
- [x] T043 Edit: specs/063-ollama-exception-refactor/tasks/ph3-output.md

**Checkpoint**: 例外クラスと call_ollama の例外スローが独立して動作することを確認

---

## Phase 4: 呼び出し元の更新 — TDD (既存テスト更新)

**Goal**: すべての call_ollama 呼び出し元が例外ベースのエラーハンドリングに移行

**Independent Test**: 呼び出し元で OllamaError をキャッチし、処理が継続されることを検証

### Input

- [x] T044 Read setup analysis: specs/063-ollama-exception-refactor/tasks/ph1-output.md
- [x] T045 Read previous phase output: specs/063-ollama-exception-refactor/tasks/ph3-output.md

### Test Implementation (RED)

- [x] T046 [P] [US2] knowledge_extractor の例外ハンドリングテストを更新: tests/utils/test_knowledge_extractor.py
- [x] T047 [P] [US2] organize/nodes の例外ハンドリングテストを更新: tests/pipelines/organize/test_nodes.py
- [x] T048 Verify `make test` FAIL (RED)
- [x] T049 Generate RED output: specs/063-ollama-exception-refactor/red-tests/ph4-test.md

### Implementation (GREEN)

- [x] T050 Read RED tests: specs/063-ollama-exception-refactor/red-tests/ph4-test.md
- [x] T051 [P] [US2] translate_summary の呼び出し元を更新: src/obsidian_etl/utils/knowledge_extractor.py
- [x] T052 [P] [US2] extract_knowledge の呼び出し元を更新: src/obsidian_etl/utils/knowledge_extractor.py
- [x] T053 [P] [US2] _extract_topic_and_genre_via_llm の呼び出し元を更新: src/obsidian_etl/pipelines/organize/nodes.py
- [x] T054 [P] [US2] _extract_topic_via_llm の呼び出し元を更新: src/obsidian_etl/pipelines/organize/nodes.py
- [x] T055 [P] [US2] _suggest_new_genres_via_llm の呼び出し元を更新: src/obsidian_etl/pipelines/organize/nodes.py
- [x] T056 Verify `make test` PASS (GREEN)

### Verification

- [x] T057 Verify `make test` passes all tests (no regressions)
- [x] T058 Edit: specs/063-ollama-exception-refactor/tasks/ph4-output.md

**Checkpoint**: すべての呼び出し元が例外ベースに移行し、処理が継続することを確認

---

## Phase 5: パーティション処理での file_id 設定 — TDD

**Goal**: パーティション処理開始時に file_id がコンテキストに設定され、ログに自動付与される

**Independent Test**: パーティション処理のモックを実行し、ログに [file_id] が含まれることを検証

### Input

- [x] T059 Read setup analysis: specs/063-ollama-exception-refactor/tasks/ph1-output.md
- [x] T060 Read previous phase output: specs/063-ollama-exception-refactor/tasks/ph4-output.md

### Test Implementation (RED)

- [x] T061 [P] [US1] transform/nodes での file_id 設定テストを実装: tests/pipelines/transform/test_nodes.py
- [x] T062 [P] [US1] organize/nodes での file_id 設定テストを実装: tests/pipelines/organize/test_nodes.py
- [x] T063 Verify `make test` FAIL (RED)
- [x] T064 Generate RED output: specs/063-ollama-exception-refactor/red-tests/ph5-test.md

### Implementation (GREEN)

- [ ] T065 Read RED tests: specs/063-ollama-exception-refactor/red-tests/ph5-test.md
- [ ] T066 [P] [US1] transform/nodes のパーティションループに set_file_id を追加: src/obsidian_etl/pipelines/transform/nodes.py
- [ ] T067 [P] [US1] organize/nodes のパーティションループに set_file_id を追加: src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T068 [P] [US1] extract_claude/nodes のパーティションループに set_file_id を追加: src/obsidian_etl/pipelines/extract_claude/nodes.py
- [ ] T069 [P] [US1] extract_openai/nodes のパーティションループに set_file_id を追加: src/obsidian_etl/pipelines/extract_openai/nodes.py
- [ ] T070 Verify `make test` PASS (GREEN)

### Verification

- [ ] T071 Verify `make test` passes all tests (no regressions)
- [ ] T072 Edit: specs/063-ollama-exception-refactor/tasks/ph5-output.md

**Checkpoint**: パーティション処理中のログに [file_id] が自動付与されることを確認

---

## Phase 6: Polish & Cross-Cutting Concerns — NO TDD

**目的**: 手動プレフィックス削除、コード品質確認、最終検証

### Input

- [ ] T073 Read setup analysis: specs/063-ollama-exception-refactor/tasks/ph1-output.md
- [ ] T074 Read previous phase output: specs/063-ollama-exception-refactor/tasks/ph5-output.md

### Implementation

- [ ] T075 [P] organize/nodes の手動 `[{file_id}]` プレフィックスを削除: src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T076 [P] 不要になった変数・インポートを削除
- [ ] T077 `make ruff` でコード品質を確認
- [ ] T078 `make pylint` でコード品質を確認

### Verification

- [ ] T079 Run `make test` to verify all tests pass after cleanup
- [ ] T080 Run `make coverage` to verify ≥80% coverage
- [ ] T081 quickstart.md の手順を手動検証
- [ ] T082 Edit: specs/063-ollama-exception-refactor/tasks/ph6-output.md

---

## Dependencies & Execution Order

### Phase 依存関係

- **Phase 1 (Setup)**: 依存なし - メインエージェント直接実行
- **Phase 2 (US1 - ログコンテキスト)**: Phase 1 完了後 - TDD フロー
- **Phase 3 (US2+US3 - 例外クラス)**: Phase 2 完了後 - TDD フロー
- **Phase 4 (呼び出し元更新)**: Phase 3 完了後 - TDD フロー
- **Phase 5 (file_id 設定)**: Phase 4 完了後 - TDD フロー
- **Phase 6 (Polish)**: Phase 5 完了後 - speckit:phase-executor のみ

### User Story 依存関係

```
US1 (ログコンテキスト) ←─┐
                         │
US2 (例外クラス) ────────┼─→ 呼び出し元更新
                         │
US3 (context_len) ───────┘   (US2 に統合)
```

### エージェント委任

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-5 (User Stories)**: speckit:tdd-generator (RED) → speckit:phase-executor (GREEN + Verification)
- **Phase 6 (Polish)**: speckit:phase-executor のみ

### [P] マーカー（依存関係なし）

`[P]` は「他タスクへの依存がなく、実行順序が自由」を示す。並列実行を保証するものではない。

- Setup タスク [P]: 異なるファイル/ディレクトリの確認で相互依存なし
- RED テスト [P]: 異なるテストファイルへの書き込みで相互依存なし
- GREEN 実装 [P]: 異なるソースファイルへの書き込みで相互依存なし

---

## Phase Output & RED Test Artifacts

### ディレクトリ構造

```
specs/063-ollama-exception-refactor/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力 (Setup 結果)
│   ├── ph2-output.md           # Phase 2 出力 (US1 GREEN 結果)
│   ├── ph3-output.md           # Phase 3 出力 (US2+US3 GREEN 結果)
│   ├── ph4-output.md           # Phase 4 出力 (呼び出し元更新結果)
│   ├── ph5-output.md           # Phase 5 出力 (file_id 設定結果)
│   └── ph6-output.md           # Phase 6 出力 (Polish 結果)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED テスト結果
    ├── ph3-test.md             # Phase 3 RED テスト結果
    ├── ph4-test.md             # Phase 4 RED テスト結果
    └── ph5-test.md             # Phase 5 RED テスト結果
```

### Phase Output フォーマット

| Output Type | Template File |
|-------------|---------------|
| `ph1-output.md` | `.specify/templates/ph1-output-template.md` |
| `phN-output.md` | `.specify/templates/phN-output-template.md` |
| `phN-test.md` | `.specify/templates/red-test-template.md` |

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: Setup（既存コード確認）
2. Phase 2 完了: User Story 1（ログコンテキスト機能）
3. **STOP and VALIDATE**: `make test` ですべてのテストがパスすることを確認
4. 手動テストで検証（set_file_id 後のログ出力確認）

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
2. 各フェーズでコミット: `feat(phase-N): description`

---

## Test Coverage Rules

**境界テスト原則**: データ変換が発生するすべての境界でテストを書く

```
[Input] → [Parse] → [Transform] → [Output] → [Log]
   ↓         ↓          ↓           ↓         ↓
 Test      Test       Test        Test      Test
```

**チェックリスト**:
- [x] 入力パースのテスト (contextvars 設定)
- [x] 変換ロジックのテスト (例外スロー)
- [x] 出力生成のテスト (ログフォーマット)
- [x] E2E テスト (パーティション処理 → ログ出力)

---

## Notes

- [P] タスク = 依存関係なし、実行順序自由
- [Story] ラベルはタスクを特定の User Story にマッピング
- 各 User Story は独立して完了・テスト可能
- TDD: Test Implementation (RED) → Verify FAIL → Implementation (GREEN) → Verify PASS
- RED 出力は実装開始前に生成必須
- 各フェーズ完了後にコミット
- 任意のチェックポイントで停止し、ストーリーを独立して検証可能
- 回避: 曖昧なタスク、同一ファイル競合、独立性を壊すクロスストーリー依存
