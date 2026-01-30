# Tasks: Jekyll ブログインポート

**Input**: Design documents from `/specs/034-jekyll-import/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: テストは含まれる（既存パターンに従う）

**Organization**: タスクはユーザーストーリーごとにグループ化

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: 所属するユーザーストーリー（US1, US2）
- ファイルパスを含む

## Path Conventions

- **Single project**: `src/etl/` - 既存 ETL パイプライン拡張
- **Tests**: `src/etl/tests/`

---

## Phase 1: Setup

**Purpose**: 新規ファイル作成と基本構造

- [X] T001 [P] Create GitHub URL parser utility in src/etl/utils/github_url.py
- [X] T002 [P] Create GitHubExtractor skeleton in src/etl/stages/extract/github_extractor.py
- [X] T003 Add GitHubExtractor export to src/etl/stages/extract/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: US1/US2 で共通して必要なコア機能

**⚠️ CRITICAL**: ユーザーストーリー実装前に完了必須

- [X] T004 Implement parse_github_url() with regex pattern in src/etl/utils/github_url.py
- [X] T005 [P] Implement clone_repo() with subprocess + sparse-checkout in src/etl/utils/github_url.py
- [X] T006 [P] Implement parse_frontmatter() with YAML parsing in src/etl/utils/github_url.py
- [X] T007 [P] Implement extract_date() with priority fallback in src/etl/utils/github_url.py
- [X] T008 [P] Implement extract_tags() with hashtag extraction in src/etl/utils/github_url.py
- [X] T009 [P] Implement convert_frontmatter() for Jekyll → Obsidian in src/etl/utils/github_url.py
- [X] T010 Add --provider github option to CLI in src/etl/cli.py
- [X] T011 Add GitHubExtractor selection logic to ImportPhase in src/etl/phases/import_phase.py

**Checkpoint**: Foundation ready - ユーザーストーリー実装開始可能

---

## Phase 3: User Story 1 - GitHub からの Jekyll ブログインポート (Priority: P1) 🎯 MVP

**Goal**: GitHub URL から Jekyll ブログ記事を取得し、Obsidian 形式に変換してインポート

**Independent Test**: `make import INPUT=https://github.com/example-user/example-user.github.io/tree/master/_posts PROVIDER=github LIMIT=5` で5件インポート成功

### Tests for User Story 1

- [X] T012 [P] [US1] Unit test for parse_github_url() in src/etl/tests/test_github_url.py
- [X] T013 [P] [US1] Unit test for clone_repo() with mock subprocess in src/etl/tests/test_github_url.py
- [X] T014 [P] [US1] Unit test for parse_frontmatter() in src/etl/tests/test_github_url.py
- [X] T015 [P] [US1] Unit test for extract_date() with all priority levels in src/etl/tests/test_github_url.py
- [X] T016 [P] [US1] Unit test for extract_tags() with hashtag cases in src/etl/tests/test_github_url.py
- [X] T017 [P] [US1] Unit test for convert_frontmatter() in src/etl/tests/test_github_url.py
- [X] T018 [P] [US1] Unit test for GitHubExtractor.discover_items() in src/etl/tests/test_github_extractor.py
- [X] T019 [P] [US1] Integration test for GitHubExtractor steps in src/etl/tests/test_github_extractor.py

### Implementation for User Story 1

- [X] T020 [US1] Implement CloneRepoStep in src/etl/stages/extract/github_extractor.py
- [X] T021 [US1] Implement DiscoverMarkdownStep in src/etl/stages/extract/github_extractor.py
- [X] T022 [US1] Implement ParseJekyllStep in src/etl/stages/extract/github_extractor.py
- [X] T023 [US1] Implement ConvertFrontmatterStep in src/etl/stages/extract/github_extractor.py
- [X] T024 [US1] Implement GitHubExtractor.discover_items() in src/etl/stages/extract/github_extractor.py
- [X] T025 [US1] Implement GitHubExtractor.steps property in src/etl/stages/extract/github_extractor.py
- [X] T026 [US1] Handle edge cases: empty dir, invalid URL, git clone failure in src/etl/stages/extract/github_extractor.py
- [X] T027 [US1] Handle edge cases: draft/private skip, missing title, YAML error in src/etl/stages/extract/github_extractor.py

**Checkpoint**: User Story 1 完了 - GitHub インポートが動作確認可能

---

## Phase 4: User Story 2 - Resume モードでの大量ファイル処理 (Priority: P2)

**Goal**: 処理中断時に --session オプションで続行可能

**Independent Test**: 50件処理後に中断し、--session で再開して処理済みファイルがスキップされることを確認

### Tests for User Story 2

- [X] T028 [P] [US2] Unit test for Resume mode with existing session in src/etl/tests/test_github_extractor.py

### Implementation for User Story 2

- [X] T029 [US2] Integrate GitHubExtractor with existing session management in src/etl/stages/extract/github_extractor.py
- [X] T030 [US2] Implement file_id generation for processed item tracking in src/etl/stages/extract/github_extractor.py
- [X] T031 [US2] Verify --session option works with GitHubExtractor in src/etl/cli.py
- [X] T032 [US2] Verify make retry works with GitHub provider in src/etl/cli.py

**Checkpoint**: User Story 2 完了 - Resume モードが動作確認可能

---

## Phase 5: Polish & Final Verification

**Purpose**: 全体の品質向上と最終確認

- [ ] T033 [P] Run full import test with 500+ files from target repository
- [ ] T034 [P] Verify Obsidian displays all imported files without frontmatter errors
- [X] T035 [P] Update CLAUDE.md with PROVIDER=github documentation
- [X] T036 Run make test to ensure all tests pass
- [ ] T037 Run quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし - 即時開始可能
- **Foundational (Phase 2)**: Setup 完了後 - すべてのユーザーストーリーをブロック
- **User Story 1 (Phase 3)**: Foundational 完了後
- **User Story 2 (Phase 4)**: Foundational 完了後（US1 と並列可能だが、US1 完了後推奨）
- **Polish (Phase 5)**: 全ユーザーストーリー完了後

### User Story Dependencies

- **User Story 1 (P1)**: Foundational 完了後 - 他ストーリーへの依存なし
- **User Story 2 (P2)**: Foundational 完了後 - US1 と独立してテスト可能

### Within Each User Story

- テストは実装前に書き、FAIL することを確認
- Steps 実装 → Extractor 統合 → エッジケース処理
- 各ストーリー完了後に独立テスト可能

### Parallel Opportunities

- T001, T002: 並列実行可能
- T004-T009: Foundation の utility 関数は並列実行可能
- T012-T019: US1 テストは並列実行可能
- T028: US2 テストは US1 テストと並列実行可能

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for parse_github_url() in src/etl/tests/test_github_url.py"
Task: "Unit test for clone_repo() with mock subprocess in src/etl/tests/test_github_url.py"
Task: "Unit test for parse_frontmatter() in src/etl/tests/test_github_url.py"
Task: "Unit test for extract_date() with all priority levels in src/etl/tests/test_github_url.py"
Task: "Unit test for extract_tags() with hashtag cases in src/etl/tests/test_github_url.py"
Task: "Unit test for convert_frontmatter() in src/etl/tests/test_github_url.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `make import INPUT=<url> PROVIDER=github LIMIT=10` でテスト
5. 動作確認後、Phase 4 へ進む

### Incremental Delivery

1. Setup + Foundational → 基盤完成
2. User Story 1 → 独立テスト → MVP 完成
3. User Story 2 → 独立テスト → Resume 機能追加
4. Polish → 最終検証

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[GitHub URL] → [git clone] → [Markdown発見] → [frontmatter解析] → [変換] → [出力]
     ↓            ↓              ↓                 ↓              ↓        ↓
   T012         T013           T018              T014          T017     T019
```

**チェックリスト**:
- [x] URL パースのテスト (T012)
- [x] git clone のテスト (T013)
- [x] frontmatter 解析のテスト (T014)
- [x] 日付抽出のテスト (T015)
- [x] タグ抽出のテスト (T016)
- [x] frontmatter 変換のテスト (T017)
- [x] Extractor 統合テスト (T018, T019)

---

## Notes

- [P] tasks = 異なるファイル、依存関係なし
- [Story] ラベルはトレーサビリティ用
- 各ユーザーストーリーは独立して完了・テスト可能
- コミットは各タスクまたは論理グループ完了後
- チェックポイントで独立検証を実施
