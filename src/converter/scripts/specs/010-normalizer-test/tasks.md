# Tasks: Normalizer Test Infrastructure

## Overview

| Item | Value |
|------|-------|
| Feature | 010-normalizer-test |
| Total Tasks | 9 |
| Phases | 3 |
| Status | ✅ COMPLETE |

## Phase 1: Setup (Infrastructure)

**Goal**: テストインフラの基盤を整備

- [x] T001 config.py に環境変数 NORMALIZER_INDEX_DIR 対応を追加 in normalizer/config.py
- [x] T002 tests/__init__.py を作成（テストユーティリティ含む）in normalizer/tests/__init__.py
- [x] T003 [P] テストフィクスチャを作成 in normalizer/tests/fixtures/

## Phase 2: Core Tests (FR-2)

**Goal**: 主要機能のユニットテストを実装

### ファイル操作テスト
- [x] T004 [P] test_files.py - read_markdown, write_markdown のテスト in normalizer/tests/test_files.py

### バリデーションテスト
- [x] T005 [P] test_validators.py - frontmatter 解析・生成テスト in normalizer/tests/test_validators.py

### パイプラインテスト
- [x] T006 [P] test_pipeline.py - ジャンル分類テスト（Ollamaモック）in normalizer/tests/test_pipeline.py

### 英語検出テスト
- [x] T007 [P] test_english.py - 英語文書検出テスト in normalizer/tests/test_english.py

### セッション管理テスト
- [x] T008 [P] test_session.py - StateManager, Session テスト in normalizer/tests/test_session.py

## Phase 3: Integration (Makefile)

**Goal**: make test でテスト実行可能にする

- [x] T009 Makefile に test, test-quick ターゲット追加 in Makefile

## Dependencies

```
T001 ─┬─→ T004, T005, T006, T007, T008 (並列可)
T002 ─┤
T003 ─┘
         └─→ T009
```

## Parallel Execution

| Group | Tasks | Condition |
|-------|-------|-----------|
| Setup | T001, T002, T003 | T001は先に完了必須（他モジュールが参照） |
| Tests | T004-T008 | Phase 1完了後、全て並列実行可能 |

## Test Fixtures (T003)

```
normalizer/tests/fixtures/
├── with_frontmatter.md      # 既存frontmatter付き
├── without_frontmatter.md   # frontmatterなし
├── english_doc.md           # 英語文書
├── japanese_doc.md          # 日本語文書
└── mixed_content.md         # 混合コンテンツ
```

## Validation Criteria

| Phase | Criteria | Status |
|-------|----------|--------|
| Phase 1 | `python -c "from normalizer.config import INDEX_DIR"` 成功 | ✅ PASS |
| Phase 2 | `python -m unittest discover -s normalizer/tests` 全テストPASS | ✅ 74 tests PASS |
| Phase 3 | `make test` 実行成功 | ✅ PASS |

## Implementation Summary

### Created Files

| File | Lines | Description |
|------|-------|-------------|
| `normalizer/config.py` | +4 | NORMALIZER_INDEX_DIR 環境変数対応 |
| `normalizer/tests/__init__.py` | 55 | テストユーティリティ（temp_index_dir, get_fixture_path, read_fixture） |
| `normalizer/tests/test_files.py` | ~150 | ファイル操作テスト（17 tests） |
| `normalizer/tests/test_validators.py` | ~230 | バリデーターテスト（16 tests） |
| `normalizer/tests/test_english.py` | ~130 | 英語検出テスト（15 tests） |
| `normalizer/tests/test_session.py` | ~180 | セッション管理テスト（14 tests） |
| `normalizer/tests/test_pipeline.py` | ~310 | パイプラインテスト（12 tests、Ollamaモック） |
| `normalizer/tests/fixtures/*.md` | 5 files | テストフィクスチャ |
| `Makefile` | +25 | test, test-quick, test-verbose ターゲット |

### Test Statistics

- Total: 74 tests
- Quick tests (excluding pipeline): 58 tests
- Test execution time: ~0.006s
