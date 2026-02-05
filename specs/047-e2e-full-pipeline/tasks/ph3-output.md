# Phase 3 Output - User Story 1: パイプライン最終出力のゴールデンファイル比較

## サマリー

- Phase: Phase 3 - User Story 1
- ステータス: **BLOCKED by Phase 2 Regressions**
- 完了タスク: T040-T042 (Makefile 更新完了)
- ブロック理由: Phase 2 で導入された integration test の regressions が未修正

## 作業概要

### 完了した作業

1. **Makefile `test-e2e` ターゲット更新** (T041, T042):
   - `--to-nodes=format_markdown` を削除してフルパイプライン実行に変更
   - 出力ディレクトリを `data/07_model_output/notes` → `data/07_model_output/organized` に変更
   - Line 141: `[3/5] Running pipeline to format_markdown...` → `[3/5] Running full pipeline...`
   - Line 142: `--to-nodes=format_markdown` 削除
   - Line 148: `--actual $(TEST_DATA_DIR)/07_model_output/notes` → `organized`

2. **Phase 2 Regressions の修正試行** (T043):
   - `classify_genre` を更新: markdown 文字列入力に対応（frontmatter パース追加）
   - 全 organize ノードを更新: `dict[str, Callable]` と `dict[str, dict]` の両方に対応
   - `extract_topic`, `normalize_frontmatter`, `clean_content`, `embed_frontmatter_fields` を修正
   - 統合テスト catalog を更新: `topic_extracted_items`, `organized_notes` 追加
   - `test_resume_after_failure` の `organized_items` 参照を `organized_notes` に変更

### ブロックされた作業

**T043, T044**: `make test` PASS 検証 - 以下の Phase 2 regressions により BLOCKED:

## Phase 2 Regressions 詳細

### 問題の根本原因

Phase 2 で organize パイプラインを変更した際、以下の互換性が破壊された:

1. **Dataset 名変更**: `organized_items` (JSON) → `organized_notes` (Markdown)
2. **出力形式変更**: `dict[str, dict]` → `dict[str, str]` (markdown content)
3. **フィールド変更**: `vault_path`, `final_path` 削除 → `genre`, `topic` に変更

### 影響を受けるテスト

**Integration Tests (6 failures)**:
```
FAIL: test_e2e_claude_import_all_conversations_processed
FAIL: test_e2e_claude_import_produces_organized_items
FAIL: test_e2e_openai_import_all_conversations_processed
FAIL: test_e2e_openai_import_produces_organized_items
FAIL: test_partial_run_organize_only
FAIL: test_resume_after_failure (partially fixed)
```

**問題点**:
- tests.test_integration.py が `organized_items` dataset を期待
- Phase 2 で `organized_items` が pipeline 出力から削除された
- テストが `vault_path`, `final_path` フィールドを期待 (line 278)
- 新しい `organized_notes` は markdown 文字列のため、dict フィールドアクセス不可

### 試行した修正

1. **organize ノード更新**: PartitionedDataset の callable と memory dataset の dict の両方に対応
2. **テスト catalog 更新**: `organized_notes` 追加、`topic_extracted_items` 追加
3. **一部テスト更新**: `test_resume_after_failure` の `organized_items` → `organized_notes` 変更

### 残課題

以下のテストが依然として `organized_items` を参照 (要更新):
- `test_e2e_claude_import_produces_organized_items` (line 212, 222)
- `test_e2e_claude_import_all_conversations_processed` (line 240)
- `test_e2e_organized_item_has_required_fields` (line 265, 273, 278)
- `test_e2e_openai_import_produces_organized_items` (line 863+)
- `test_partial_run_organize_only` (line 639, 640, 672, 677)

これらのテストは `organized_items` (JSON dict) に依存しているが、新パイプラインは `organized_notes` (Markdown string) を出力する。

## 修正ファイル一覧

### Makefile (Phase 3 本来の作業)
- **Makefile** (lines 141-148)
  - `test-e2e`: `--to-nodes=format_markdown` 削除、出力ディレクトリ変更

### Phase 2 Regression 修正試行

- **src/obsidian_etl/pipelines/organize/nodes.py**
  - `classify_genre`: markdown 文字列 frontmatter パース追加 (lines 61-88)
  - `extract_topic`: callable/dict 両対応 (lines 147-152)
  - `normalize_frontmatter`: callable/dict 両対応 (lines 233-239)
  - `clean_content`: callable/dict 両対応 (lines 310-317)
  - `embed_frontmatter_fields`: callable/dict 両対応 (lines 425-432)

- **tests/test_integration.py**
  - Test catalog に `topic_extracted_items`, `organized_notes` 追加 (lines 170, 173)
  - `test_resume_after_failure`: `organized_items` → `organized_notes` 変更 (lines 392, 418)

## テスト結果

### E2E Golden Comparator Tests

```
$ .venv/bin/python -m unittest tests.e2e.test_golden_comparator -v

...
Ran 40 tests in 0.029s

OK
```

**✅ PASS**: Phase 3 の主目的である golden_comparator は正常動作

### Organize Pipeline Tests

```
$ .venv/bin/python -m unittest tests.pipelines.organize.test_nodes -v

...
Ran 40 tests in 0.006s

OK
```

**✅ PASS**: organize ノードのユニットテストは全て PASS

### Integration Tests

```
$ make test

...
Ran 340 tests in 0.781s

FAILED (failures=9, errors=28)
```

**❌ FAIL**:
- 3 failures: RAG config tests (pre-existing)
- 6 failures: Integration tests (Phase 2 regressions)
- 28 errors: RAG import errors (pre-existing)

## 推奨対応

### Option 1: Phase 2 Revisit (推奨)

Phase 2 に戻り、integration tests を新パイプライン構造に合わせて更新:
1. `organized_items` を参照する全テストを `organized_notes` に変更
2. `vault_path`, `final_path` 期待を `genre`, `topic` に変更
3. Markdown 文字列出力を前提としたアサーションに変更

### Option 2: Backward Compatibility Layer

`organized_notes` → `organized_items` 変換ノードを追加:
- Markdown を parse して dict に戻す
- テスト互換性のためのみ使用
- 実パイプラインには影響なし

### Option 3: Phase 3 Scope 縮小

Integration tests を Phase 3 スコープ外と見なし、以下のみ検証:
- E2E golden_comparator tests (✅ PASS)
- Organize pipeline unit tests (✅ PASS)
- Makefile `test-e2e` ターゲット動作確認 (要 Ollama 起動)

## 次 Phase への影響

Phase 4 (ゴールデンファイル再生成) は Phase 3 Makefile 変更に依存するため、**Phase 2 regressions 修正後に再開すべき**。

Option 3 (Scope 縮小) を採用する場合、Phase 4 は Makefile 変更のみで進行可能。

## ステータス

- Phase 3 Makefile 変更: **Complete**
- Phase 3 全体: **BLOCKED by Phase 2 Regressions**

次アクション: ユーザー判断
- [ ] Phase 2 Revisit (Option 1)
- [ ] Backward Compatibility Layer (Option 2)
- [ ] Phase 3 Scope 縮小 → Phase 4 へ進行 (Option 3)
