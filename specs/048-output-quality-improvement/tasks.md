# Tasks: 出力ファイル品質改善

**Input**: 出力ファイル分析結果（2026-02-08）
**Prerequisites**: 047-e2e-full-pipeline 完了後

**Organization**: 問題カテゴリごとにタスクをグループ化

## Format: `[ID] [P?] Description`

- **[P]**: No dependencies (parallel execution possible)

## 問題サマリー

| 問題 | 影響ファイル例 | 根本原因 |
|------|----------------|----------|
| 空 summary_content | `.placeholder.md`, `Android側.md` | LLM抽出失敗でも出力 |
| タイトルに絵文字/シンボル | `❌ 悪いパターン...`, `🍶 長岡旅行...` | サニタイズ不足 |
| タイトルがプレースホルダー | `[トピック名].md`, `(省略).md` | LLM が例文を採用 |
| タイトルにファイルパス記号 | `~.bashrc に追加.md`, `%演算子...` | サニタイズ不足 |
| トピックが細かすぎる | `9ヶ月赤ちゃん...` (バナナプリン→離乳食) | 粒度指示なし |
| summary と content 逆転 | `6ddf26dbfc5b.md` | LLM 出力構造ミス |
| file_id がファイル名に | `6ddf26dbfc5b.md` | タイトル空でフォールバック |

## Path Conventions

- **Source**: `src/obsidian_etl/` - Kedro パイプライン実装
- **Prompts**: `src/obsidian_etl/utils/prompts/` - LLM プロンプト
- **Tests**: `tests/` - ユニットテスト

---

## Phase 1: Setup (分析・調査) — NO TDD

**Purpose**: 現状把握と修正箇所の特定

- [ ] T001 Read transform nodes: src/obsidian_etl/pipelines/transform/nodes.py
- [ ] T002 [P] Read knowledge extractor: src/obsidian_etl/utils/knowledge_extractor.py
- [ ] T003 [P] Read knowledge extraction prompt: src/obsidian_etl/utils/prompts/knowledge_extraction.txt
- [ ] T004 [P] Read organize nodes: src/obsidian_etl/pipelines/organize/nodes.py
- [ ] T005 [P] Read ollama client: src/obsidian_etl/utils/ollama.py
- [ ] T006 Analyze problem files in data/07_model_output/organized/
- [ ] T007 Generate phase output: specs/048-output-quality-improvement/tasks/ph1-output.md

---

## Phase 2: 空コンテンツフィルタリング (Priority: P1)

**Goal**: summary_content が空のアイテムを出力しない

### テスト実装 (RED)

- [ ] T008 [P] Add test_extract_knowledge_skips_empty_summary_content in tests/pipelines/transform/test_nodes.py
- [ ] T009 [P] Add test_extract_knowledge_logs_skipped_empty_content in tests/pipelines/transform/test_nodes.py
- [ ] T010 Verify `make test` FAIL (RED)
- [ ] T011 Generate RED output: specs/048-output-quality-improvement/red-tests/ph2-test.md

### 実装 (GREEN)

- [ ] T012 Read RED tests: specs/048-output-quality-improvement/red-tests/ph2-test.md
- [ ] T013 Add validation in extract_knowledge node to skip empty summary_content in src/obsidian_etl/pipelines/transform/nodes.py
- [ ] T014 Verify `make test` PASS (GREEN)

### 検証

- [ ] T015 Verify `make test` passes all tests
- [ ] T016 Generate phase output: specs/048-output-quality-improvement/tasks/ph2-output.md

---

## Phase 3: タイトルサニタイズ強化 (Priority: P1)

**Goal**: タイトルから絵文字、シンボル、ファイルパス記号を除去

### テスト実装 (RED)

- [ ] T017 [P] Add test_sanitize_title_removes_emoji in tests/pipelines/transform/test_nodes.py
- [ ] T018 [P] Add test_sanitize_title_removes_brackets in tests/pipelines/transform/test_nodes.py
- [ ] T019 [P] Add test_sanitize_title_removes_tilde_prefix in tests/pipelines/transform/test_nodes.py
- [ ] T020 [P] Add test_sanitize_title_removes_percent in tests/pipelines/transform/test_nodes.py
- [ ] T021 Verify `make test` FAIL (RED)
- [ ] T022 Generate RED output: specs/048-output-quality-improvement/red-tests/ph3-test.md

### 実装 (GREEN)

- [ ] T023 Read RED tests: specs/048-output-quality-improvement/red-tests/ph3-test.md
- [ ] T024 Add _sanitize_title function in src/obsidian_etl/pipelines/transform/nodes.py
- [ ] T025 Integrate _sanitize_title in generate_metadata node
- [ ] T026 Verify `make test` PASS (GREEN)

### 検証

- [ ] T027 Verify `make test` passes all tests
- [ ] T028 Generate phase output: specs/048-output-quality-improvement/tasks/ph3-output.md

---

## Phase 4: プロンプト改善 (Priority: P2)

**Goal**: LLM がプレースホルダーや会話断片をタイトルとして採用しない

### 実装 (NO TDD - プロンプト変更)

- [ ] T029 Read current prompt: src/obsidian_etl/utils/prompts/knowledge_extraction.txt
- [ ] T030 Add title exclusion rules to prompt (exclude placeholders, emoji, symbols)
- [ ] T031 Add title quality guidelines to prompt

### 検証

- [ ] T032 Run `kedro run` on sample data
- [ ] T033 Verify improved title quality in output
- [ ] T034 Generate phase output: specs/048-output-quality-improvement/tasks/ph4-output.md

---

## Phase 5: トピック粒度改善 (Priority: P2)

**Goal**: トピック抽出が適切な抽象度（バナナプリン→離乳食）

### 実装 (NO TDD - プロンプト変更)

- [ ] T035 Read current topic extraction in organize/nodes.py
- [ ] T036 Update topic extraction prompt with granularity guidelines
- [ ] T037 Add examples of appropriate abstraction level

### 検証

- [ ] T038 Run `kedro run` on sample data
- [ ] T039 Verify improved topic abstraction in output
- [ ] T040 Generate phase output: specs/048-output-quality-improvement/tasks/ph5-output.md

---

## Phase 6: summary 長さチェック (Priority: P3)

**Goal**: summary が異常に長い（content と逆転）場合を検出

### テスト実装 (RED)

- [ ] T041 [P] Add test_detect_summary_content_swap in tests/pipelines/transform/test_nodes.py
- [ ] T042 [P] Add test_warn_long_summary in tests/pipelines/transform/test_nodes.py
- [ ] T043 Verify `make test` FAIL (RED)
- [ ] T044 Generate RED output: specs/048-output-quality-improvement/red-tests/ph6-test.md

### 実装 (GREEN)

- [ ] T045 Read RED tests: specs/048-output-quality-improvement/red-tests/ph6-test.md
- [ ] T046 Add summary length validation in extract_knowledge node
- [ ] T047 Log warning for abnormally long summaries (>500 chars)
- [ ] T048 Verify `make test` PASS (GREEN)

### 検証

- [ ] T049 Verify `make test` passes all tests
- [ ] T050 Generate phase output: specs/048-output-quality-improvement/tasks/ph6-output.md

---

## Phase 7: Polish & 最終検証 — NO TDD

**Purpose**: 全体検証と既存問題ファイルの再処理

- [ ] T051 Run `make test` to verify all tests pass
- [ ] T052 Run `kedro run` on full dataset
- [ ] T053 Verify problem files are improved or filtered
- [ ] T054 Update CLAUDE.md if needed
- [ ] T055 Generate phase output: specs/048-output-quality-improvement/tasks/ph7-output.md

---

## Dependencies

- **Phase 1**: No dependencies
- **Phase 2**: Depends on Phase 1
- **Phase 3**: Depends on Phase 1 (parallel with Phase 2)
- **Phase 4**: Depends on Phase 1
- **Phase 5**: Depends on Phase 1
- **Phase 6**: Depends on Phase 2
- **Phase 7**: Depends on all phases

---

## Notes

- [P] tasks = no dependencies, parallel execution possible
- Priority order: P1 (空コンテンツ, タイトルサニタイズ) > P2 (プロンプト) > P3 (summary 長さ)
- プロンプト変更は TDD 対象外（出力が非決定的）
- 既存テストの後方互換性を維持
