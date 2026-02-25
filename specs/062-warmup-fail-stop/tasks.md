# Tasks: ウォームアップ失敗時に処理を停止する

**Input**: Design documents from `/specs/062-warmup-fail-stop/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: TDD フローを適用。各ユーザーストーリーフェーズは Test Implementation (RED) → Implementation (GREEN) → Verification の順序で実行。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: タスクが属するユーザーストーリー（US1, US2）
- ファイルパスを明記

## ユーザーストーリー概要

| ID | タイトル | 優先度 | FR | シナリオ |
|----|---------|--------|-----|---------|
| US1 | ウォームアップ失敗時の即時停止 | P1 | FR-001,002,003 | タイムアウト・接続エラー時に処理停止、終了コード 3 |
| US2 | 明確なエラーメッセージの表示 | P2 | FR-004,005 | モデル名・推奨アクションを含むエラーメッセージ |

## パス規約

- **ソース**: `src/obsidian_etl/`
- **テスト**: `tests/`
- **仕様**: `specs/062-warmup-fail-stop/`

---

## Phase 1: Setup（既存コード確認） — NO TDD

**Purpose**: 既存実装の確認と変更箇所の特定

- [x] T001 Read: src/obsidian_etl/utils/ollama.py（現在の _do_warmup 実装確認）
- [x] T002 [P] Read: src/obsidian_etl/hooks.py（ErrorHandlerHook 確認）
- [x] T003 [P] Read: tests/ 配下の既存テスト構造確認
- [x] T004 Edit: specs/062-warmup-fail-stop/tasks/ph1-output.md（セットアップ分析結果）

---

## Phase 2: User Story 1 - ウォームアップ失敗時の即時停止 (Priority: P1) MVP

**Goal**: ウォームアップ失敗時に処理を即座に停止し、終了コード 3 を返す

**Independent Test**: Ollama サーバー停止状態でパイプライン実行 → 終了コード 3 で停止することを確認

### Input

- [x] T005 Read: specs/062-warmup-fail-stop/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T006 [P] [US1] Implement: OllamaWarmupError 例外のユニットテスト in tests/test_warmup_error.py
- [x] T007 [P] [US1] Implement: _do_warmup タイムアウト時の例外発生テスト in tests/test_warmup_error.py
- [x] T008 [P] [US1] Implement: _do_warmup 接続エラー時の例外発生テスト in tests/test_warmup_error.py
- [x] T009 [P] [US1] Implement: call_ollama が例外を伝播するテスト in tests/test_warmup_error.py
- [x] T010 Verify: `make test` FAIL (RED)
- [x] T011 Edit: specs/062-warmup-fail-stop/red-tests/ph2-test.md

### Implementation (GREEN)

- [x] T012 Read: specs/062-warmup-fail-stop/red-tests/ph2-test.md
- [x] T013 [US1] Implement: OllamaWarmupError 例外クラス in src/obsidian_etl/utils/ollama.py
- [x] T014 [US1] Implement: _do_warmup で例外を raise（WARNING → ERROR 変更）in src/obsidian_etl/utils/ollama.py
- [x] T015 [US1] Implement: call_ollama で warmup 成功時のみ _warmed_models.add in src/obsidian_etl/utils/ollama.py
- [x] T016 Verify: `make test` PASS (GREEN)

### Verification

- [x] T017 Verify: `make test` 全テスト通過（既存テストの回帰なし）
- [x] T018 Edit: specs/062-warmup-fail-stop/tasks/ph2-output.md

**Checkpoint**: US1 完了 - ウォームアップ失敗時に例外が発生し、処理が停止する

---

## Phase 3: User Story 2 - 明確なエラーメッセージの表示 (Priority: P2)

**Goal**: エラーメッセージにモデル名と推奨アクションを含め、ユーザーが問題を特定・解決できるようにする

**Independent Test**: エラーメッセージにモデル名、推奨アクション（ollama serve, ollama pull）が含まれることを確認

### Input

- [x] T019 Read: specs/062-warmup-fail-stop/tasks/ph1-output.md
- [x] T020 Read: specs/062-warmup-fail-stop/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T021 [P] [US2] Implement: ErrorHandlerHook が OllamaWarmupError をキャッチするテスト in tests/test_hooks_warmup.py
- [x] T022 [P] [US2] Implement: 終了コード 3 で sys.exit するテスト in tests/test_hooks_warmup.py
- [x] T023 [P] [US2] Implement: エラーメッセージにモデル名が含まれるテスト in tests/test_hooks_warmup.py
- [x] T024 [P] [US2] Implement: エラーメッセージに推奨アクションが含まれるテスト in tests/test_hooks_warmup.py
- [x] T025 Verify: `make test` FAIL (RED)
- [x] T026 Edit: specs/062-warmup-fail-stop/red-tests/ph3-test.md

### Implementation (GREEN)

- [x] T027 Read: specs/062-warmup-fail-stop/red-tests/ph3-test.md
- [x] T028 [US2] Implement: ErrorHandlerHook に OllamaWarmupError ハンドリング追加 in src/obsidian_etl/hooks.py
- [x] T029 [US2] Implement: sys.exit(3) 呼び出し in src/obsidian_etl/hooks.py
- [x] T030 [US2] Implement: モデル名・推奨アクションを含むエラーメッセージ出力 in src/obsidian_etl/hooks.py
- [x] T031 Verify: `make test` PASS (GREEN) - 8/8 warmup hook tests passed

### Verification

- [x] T032 Verify: `make test` 全テスト通過（US1 含む回帰なし）- Phase 2: 9/9, Phase 3: 8/8 all passing
- [x] T033 Edit: specs/062-warmup-fail-stop/tasks/ph3-output.md

**Checkpoint**: US2 完了 - エラーメッセージが明確で、ユーザーが問題を特定できる

---

## Phase 4: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: コード品質の最終確認とドキュメント整備

### Input

- [ ] T034 Read: specs/062-warmup-fail-stop/tasks/ph1-output.md
- [ ] T035 Read: specs/062-warmup-fail-stop/tasks/ph3-output.md

### Implementation

- [ ] T036 [P] __all__ に OllamaWarmupError を追加（必要な場合）in src/obsidian_etl/utils/ollama.py
- [ ] T037 [P] docstring 追加・更新 in src/obsidian_etl/utils/ollama.py
- [ ] T038 quickstart.md の検証手順を実行して動作確認

### Verification

- [ ] T039 Verify: `make test` 全テスト通過
- [ ] T040 Verify: `make lint` 通過
- [ ] T041 Edit: specs/062-warmup-fail-stop/tasks/ph4-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし - メインエージェント直接実行
- **Phase 2 (US1)**: TDD フロー (speckit:tdd-generator → speckit:phase-executor)
- **Phase 3 (US2)**: Phase 2 完了後に実行 - TDD フロー
- **Phase 4 (Polish)**: Phase 3 完了後に実行 - speckit:phase-executor のみ

### Agent Delegation

| Phase | Agent | 役割 |
|-------|-------|------|
| Phase 1 | Main | Setup 分析 |
| Phase 2 (RED) | speckit:tdd-generator | テスト作成・FAIL 確認 |
| Phase 2 (GREEN) | speckit:phase-executor | 実装・PASS 確認 |
| Phase 3 (RED) | speckit:tdd-generator | テスト作成・FAIL 確認 |
| Phase 3 (GREEN) | speckit:phase-executor | 実装・PASS 確認 |
| Phase 4 | speckit:phase-executor | 最終確認 |

### [P] マーカー説明

- 同一フェーズ内で異なるファイルへの書き込み → [P] 適用可
- 同一ファイルへの書き込み → 順序依存、[P] 適用不可
- フェーズ間 → 前フェーズの出力に依存、[P] 適用不可

---

## Phase Output & RED Test Artifacts

### ディレクトリ構造

```
specs/062-warmup-fail-stop/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（Setup 結果）
│   ├── ph2-output.md           # Phase 2 出力（US1 GREEN 結果）
│   ├── ph3-output.md           # Phase 3 出力（US2 GREEN 結果）
│   └── ph4-output.md           # Phase 4 出力（最終確認）
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED テスト結果
    └── ph3-test.md             # Phase 3 RED テスト結果
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: 既存コード確認
2. Phase 2 完了: US1（ウォームアップ失敗時の即時停止）
3. **STOP and VALIDATE**: `make test` で全テスト通過確認
4. 手動テスト: Ollama 停止状態で `kedro run` → 終了コード 3 確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4
2. 各フェーズ完了時にコミット: `feat(phase-N): description`

---

## Notes

- US1 は US2 の前提条件（例外クラスが必要）
- US2 は US1 の例外を hooks.py でキャッチする
- 両ストーリーとも既存コードへの追加・修正のみで新規ファイル作成は最小限
- テストファイルは新規作成: `tests/test_warmup_error.py`, `tests/test_hooks_warmup.py`
