# Tasks: データレイヤー分離（JSON/MD混在解消）

**Input**: Design documents from `/specs/064-data-layer-separation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: TDD は User Story フェーズで必須。Test Implementation (RED) → Implementation (GREEN) → Verification のワークフローに従う。

**Organization**: タスクはユーザーストーリーごとにグループ化され、各ストーリーを独立して実装・テスト可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: タスクが属するユーザーストーリー（例: US1, US2, US3）
- 説明には正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | 独立テスト |
|----|-------|----------|----| ----------|
| US1 | パイプライン実行時のデータ整合性 | P1 | FR-001,002,003,008 | `kedro run` 後に JSON が `05_model_input/` のみに出力 |
| US2 | 既存データの移行 | P2 | FR-004,005 | 移行スクリプト実行後、JSON が新構造に移動 |
| US3 | ログ処理の簡素化 | P3 | FR-006 | `iter_with_file_id` が str のみ受け付ける |

## Path Conventions

- **Source**: `src/obsidian_etl/`
- **Tests**: `tests/`
- **Config**: `conf/base/`
- **Scripts**: `scripts/`

---

## Phase 1: Setup（既存コード確認）— NO TDD

**Purpose**: 現在の実装を理解し、変更の影響範囲を特定

- [X] T001 Read: `conf/base/catalog.yml` の現在のデータセット定義を確認
- [X] T002 [P] Read: `src/obsidian_etl/utils/log_context.py` の `iter_with_file_id` 実装を確認
- [X] T003 [P] Read: `tests/` 配下の関連テストファイルを確認
- [X] T004 [P] Read: `data/07_model_output/` の現在のディレクトリ構造を確認
- [X] T005 Edit: `specs/064-data-layer-separation/tasks/ph1-output.md` にセットアップ分析結果を記録

---

## Phase 2: User Story 1 - パイプライン実行時のデータ整合性 (Priority: P1) MVP

**Goal**: `catalog.yml` を更新し、JSON データセットが `05_model_input/` に出力されるようにする

**Independent Test**: `kedro run --params='{"import.limit": 1}'` 実行後、JSON が `05_model_input/` に、MD が `07_model_output/` にのみ出力される

### Input

- [ ] T006 Read: `specs/064-data-layer-separation/tasks/ph1-output.md`

### Test Implementation (RED)

- [ ] T007 [P] [US1] Implement: `tests/unit/test_catalog_paths.py` に JSON データセットのパス検証テストを作成
- [ ] T008 [P] [US1] Implement: `tests/unit/test_catalog_paths.py` に MD データセットのパス検証テストを作成
- [ ] T009 Verify: `make test` FAIL (RED) - 新パスがまだ設定されていないため
- [ ] T010 Edit: `specs/064-data-layer-separation/red-tests/ph2-test.md` に RED テスト結果を記録

### Implementation (GREEN)

- [ ] T011 Read: `specs/064-data-layer-separation/red-tests/ph2-test.md`
- [ ] T012 [US1] Edit: `conf/base/catalog.yml` の `classified_items` パスを `data/05_model_input/classified` に変更
- [ ] T013 [P] [US1] Edit: `conf/base/catalog.yml` の `existing_classified_items` パスを `data/05_model_input/classified` に変更
- [ ] T014 [P] [US1] Edit: `conf/base/catalog.yml` の `topic_extracted_items` パスを `data/05_model_input/topic_extracted` に変更
- [ ] T015 [P] [US1] Edit: `conf/base/catalog.yml` の `normalized_items` パスを `data/05_model_input/normalized` に変更
- [ ] T016 [P] [US1] Edit: `conf/base/catalog.yml` の `cleaned_items` パスを `data/05_model_input/cleaned` に変更
- [ ] T017 [P] [US1] Edit: `conf/base/catalog.yml` の `vault_determined_items` パスを `data/05_model_input/vault_determined` に変更
- [ ] T018 [P] [US1] Edit: `conf/base/catalog.yml` の `organized_items` パスを `data/05_model_input/organized` に変更
- [ ] T019 [US1] Create: `data/05_model_input/` ディレクトリ構造を作成（.gitkeep 含む）
- [ ] T020 Verify: `make test` PASS (GREEN)

### Verification

- [ ] T021 Verify: `make test` がすべてのテストを通過
- [ ] T022 Edit: `specs/064-data-layer-separation/tasks/ph2-output.md` に Phase 2 結果を記録

**Checkpoint**: catalog.yml の更新が完了し、パイプラインが新しいパスで動作可能

---

## Phase 3: User Story 2 - 既存データの移行 (Priority: P2)

**Goal**: 既存の `07_model_output/` にある JSON ファイルを `05_model_input/` に移行するスクリプトを作成

**Independent Test**: `python scripts/migrate_data_layers.py` 実行後、JSON ファイルが新構造に移動

### Input

- [ ] T023 Read: `specs/064-data-layer-separation/tasks/ph1-output.md`
- [ ] T024 Read: `specs/064-data-layer-separation/tasks/ph2-output.md`

### Test Implementation (RED)

- [ ] T025 [P] [US2] Implement: `tests/unit/test_migrate_data_layers.py` に移行元にファイルなしの場合のテストを作成
- [ ] T026 [P] [US2] Implement: `tests/unit/test_migrate_data_layers.py` に JSON ファイル移行テストを作成
- [ ] T027 [P] [US2] Implement: `tests/unit/test_migrate_data_layers.py` に既存ファイルスキップテストを作成
- [ ] T028 [P] [US2] Implement: `tests/unit/test_migrate_data_layers.py` にサマリー出力テストを作成
- [ ] T029 [P] [US2] Implement: `tests/unit/test_migrate_data_layers.py` に dry-run モードテストを作成
- [ ] T030 Verify: `make test` FAIL (RED) - 移行スクリプトがまだ存在しないため
- [ ] T031 Edit: `specs/064-data-layer-separation/red-tests/ph3-test.md` に RED テスト結果を記録

### Implementation (GREEN)

- [ ] T032 Read: `specs/064-data-layer-separation/red-tests/ph3-test.md`
- [ ] T033 [US2] Create: `scripts/migrate_data_layers.py` に `MigrationResult` データクラスを定義
- [ ] T034 [US2] Implement: `scripts/migrate_data_layers.py` に `migrate_json_to_model_input()` 関数を実装
- [ ] T035 [US2] Implement: `scripts/migrate_data_layers.py` に dry-run モードを実装
- [ ] T036 [US2] Implement: `scripts/migrate_data_layers.py` にサマリー出力機能を実装
- [ ] T037 [US2] Implement: `scripts/migrate_data_layers.py` に CLI インターフェースを追加
- [ ] T038 Verify: `make test` PASS (GREEN)

### Verification

- [ ] T039 Verify: `make test` がすべてのテストを通過（US1 のリグレッションなし）
- [ ] T040 Edit: `specs/064-data-layer-separation/tasks/ph3-output.md` に Phase 3 結果を記録

**Checkpoint**: 移行スクリプトが完成し、既存データを安全に移行可能

---

## Phase 4: User Story 3 - ログ処理の簡素化 (Priority: P3)

**Goal**: `iter_with_file_id` 関数を簡素化し、str 入力のみをサポート

**Independent Test**: `iter_with_file_id` に dict を渡すと TypeError が発生

### Input

- [ ] T041 Read: `specs/064-data-layer-separation/tasks/ph1-output.md`
- [ ] T042 Read: `specs/064-data-layer-separation/tasks/ph3-output.md`

### Test Implementation (RED)

- [ ] T043 [P] [US3] Implement: `tests/unit/test_log_context.py` に str パス入力の正常処理テストを追加
- [ ] T044 [P] [US3] Implement: `tests/unit/test_log_context.py` に dict 入力で TypeError テストを追加
- [ ] T045 [P] [US3] Implement: `tests/unit/test_log_context.py` に frontmatter から file_id 抽出テストを追加
- [ ] T046 Verify: `make test` FAIL (RED) - 現在の実装は dict も受け付けるため
- [ ] T047 Edit: `specs/064-data-layer-separation/red-tests/ph4-test.md` に RED テスト結果を記録

### Implementation (GREEN)

- [ ] T048 Read: `specs/064-data-layer-separation/red-tests/ph4-test.md`
- [ ] T049 [US3] Edit: `src/obsidian_etl/utils/log_context.py` の `iter_with_file_id` から dict 対応コードを削除
- [ ] T050 [US3] Edit: `src/obsidian_etl/utils/log_context.py` の `iter_with_file_id` に str 型チェックを追加
- [ ] T051 [US3] Edit: `src/obsidian_etl/utils/log_context.py` の docstring を更新
- [ ] T052 Verify: `make test` PASS (GREEN)

### Verification

- [ ] T053 Verify: `make test` がすべてのテストを通過（US1, US2 のリグレッションなし）
- [ ] T054 Verify: `make lint` が通過（ruff + pylint）
- [ ] T055 Edit: `specs/064-data-layer-separation/tasks/ph4-output.md` に Phase 4 結果を記録

**Checkpoint**: `iter_with_file_id` の簡素化が完了し、コードの複雑さが軽減

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: ドキュメント更新と最終検証

### Input

- [ ] T056 Read: `specs/064-data-layer-separation/tasks/ph1-output.md`
- [ ] T057 Read: `specs/064-data-layer-separation/tasks/ph4-output.md`

### Implementation

- [ ] T058 [P] Edit: `CLAUDE.md` のフォルダ構成セクションを更新（05_model_input 追加）
- [ ] T059 [P] Edit: `.gitignore` に `data/05_model_input/` を追加（必要に応じて）
- [ ] T060 [P] Edit: テストの fixture パス参照を新構造に更新
- [ ] T061 Run: `quickstart.md` の手順に従って検証
- [ ] T062 [P] Remove: 不要になった旧パス参照コードの削除

### Verification

- [ ] T063 Verify: `make test` がすべてのテストを通過
- [ ] T064 Verify: `make lint` が通過
- [ ] T065 Verify: `make coverage` が 80% 以上
- [ ] T066 Edit: `specs/064-data-layer-separation/tasks/ph5-output.md` に Phase 5 結果を記録

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存関係なし - Main agent 直接実行
- **Phase 2 (US1)**: Phase 1 に依存 - speckit:tdd-generator → speckit:phase-executor
- **Phase 3 (US2)**: Phase 2 に依存 - speckit:tdd-generator → speckit:phase-executor
- **Phase 4 (US3)**: Phase 3 に依存 - speckit:tdd-generator → speckit:phase-executor
- **Phase 5 (Polish)**: Phase 4 に依存 - speckit:phase-executor のみ

### User Story 依存関係

```
US1 (catalog.yml) ← 基盤、他すべての前提
    ↓
US2 (移行スクリプト) ← US1 の新構造に依存
    ↓
US3 (iter_with_file_id) ← US1, US2 完了後に実施可能
```

### Agent Delegation

- **Phase 1**: Main agent 直接実行
- **Phase 2-4**: speckit:tdd-generator (RED) → speckit:phase-executor (GREEN + Verification)
- **Phase 5**: speckit:phase-executor のみ

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/064-data-layer-separation/
├── tasks.md                    # 本ファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力 (Setup 結果)
│   ├── ph2-output.md           # Phase 2 出力 (US1 GREEN 結果)
│   ├── ph3-output.md           # Phase 3 出力 (US2 GREEN 結果)
│   ├── ph4-output.md           # Phase 4 出力 (US3 GREEN 結果)
│   └── ph5-output.md           # Phase 5 出力 (Polish 結果)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED テスト結果
    ├── ph3-test.md             # Phase 3 RED テスト結果
    └── ph4-test.md             # Phase 4 RED テスト結果
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: Setup（既存コード確認）
2. Phase 2 完了: US1（catalog.yml 更新）
3. **STOP and VALIDATE**: `make test` ですべてのテストが通過することを確認
4. 手動検証: `kedro run --params='{"import.limit": 1}'` で新パスに出力されることを確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズのコミット: `feat(phase-N): 説明`

---

## Notes

- [P] タスク = 依存関係なし、実行順序自由
- [Story] ラベルはタスクを特定のユーザーストーリーにマッピング
- 各ユーザーストーリーは独立して完了・テスト可能
- TDD: Test Implementation (RED) → Verify FAIL → Implementation (GREEN) → Verify PASS
- RED 出力は実装開始前に必ず生成
- 各フェーズ完了後にコミット
- どのチェックポイントでも停止してストーリーを独立検証可能
