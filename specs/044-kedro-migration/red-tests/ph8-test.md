# Phase 8 RED Tests

## サマリー
- Phase: Phase 8 - US4 GitHub Jekyll プロバイダー
- FAIL テスト数: 38 メソッド (1 モジュール ImportError で全テストが FAIL)
- テストファイル: tests/pipelines/extract_github/test_nodes.py

## FAIL テスト一覧

| テストファイル | テストクラス | テストメソッド | 期待動作 |
|---------------|-------------|---------------|---------|
| test_nodes.py | TestCloneGithubRepo | test_clone_returns_dict_of_markdown_files | clone_github_repo が dict[str, Callable] を返す |
| test_nodes.py | TestCloneGithubRepo | test_clone_calls_git_with_depth_1 | git clone --depth 1 が呼ばれる |
| test_nodes.py | TestCloneGithubRepo | test_clone_calls_sparse_checkout | sparse-checkout set が呼ばれる |
| test_nodes.py | TestCloneGithubRepo | test_clone_invalid_url_returns_empty | 無効 URL で空 dict |
| test_nodes.py | TestCloneGithubRepo | test_clone_result_values_are_callable | 値が callable (PartitionedDataset) |
| test_nodes.py | TestParseJekyll | test_parse_jekyll_returns_dict | dict を返す |
| test_nodes.py | TestParseJekyll | test_parse_jekyll_item_count | 2 ファイル -> 2 ParsedItem |
| test_nodes.py | TestParseJekyll | test_parse_jekyll_parsed_item_structure | E-2 スキーマ準拠 (provider=github) |
| test_nodes.py | TestParseJekyll | test_parse_jekyll_title_extracted | frontmatter title -> conversation_name |
| test_nodes.py | TestParseJekyll | test_parse_jekyll_date_extracted | frontmatter date -> created_at |
| test_nodes.py | TestParseJekyll | test_parse_jekyll_content_is_body | content = frontmatter 除去後の本文 |
| test_nodes.py | TestParseJekyll | test_parse_jekyll_messages_empty_for_github | messages = [] (GitHub は会話でない) |
| test_nodes.py | TestParseJekyll | test_parse_jekyll_file_id_valid_hex | file_id = 12桁16進数 |
| test_nodes.py | TestParseJekyll | test_parse_jekyll_golden_data_match | ゴールデンデータ一致 |
| test_nodes.py | TestParseJekyll | test_parse_jekyll_no_frontmatter_in_content | content に frontmatter 非含有 |
| test_nodes.py | TestParseJekyllSkipDraft | test_draft_true_excluded | draft: true -> 除外 |
| test_nodes.py | TestParseJekyllSkipDraft | test_private_true_excluded | private: true -> 除外 |
| test_nodes.py | TestParseJekyllSkipDraft | test_draft_false_included | draft: false -> 含有 |
| test_nodes.py | TestParseJekyllSkipDraft | test_all_drafts_returns_empty | 全 draft -> 空 dict |
| test_nodes.py | TestConvertFrontmatter | test_date_becomes_created | date -> created 変換 |
| test_nodes.py | TestConvertFrontmatter | test_tags_categories_keywords_merged | tags/categories/keywords 統合 |
| test_nodes.py | TestConvertFrontmatter | test_removed_fields_not_in_output | layout/permalink/slug/lastmod 除外 |
| test_nodes.py | TestConvertFrontmatter | test_normalized_true_in_output | normalized: true 含有 |
| test_nodes.py | TestConvertFrontmatter | test_file_id_generated | SHA256 file_id 生成 |
| test_nodes.py | TestConvertFrontmatter | test_title_fallback_to_filename | title なし -> filename フォールバック |
| test_nodes.py | TestDateExtractionPriority | test_priority_1_frontmatter_date | frontmatter.date 最優先 |
| test_nodes.py | TestDateExtractionPriority | test_priority_2_filename_date | filename 日付 第2優先 |
| test_nodes.py | TestDateExtractionPriority | test_priority_3_body_regex | 本文 regex 第3優先 |
| test_nodes.py | TestDateExtractionPriority | test_priority_4_current_datetime_fallback | 現在日時フォールバック |
| test_nodes.py | TestDateExtractionPriority | test_iso8601_date_in_frontmatter | ISO 8601 -> YYYY-MM-DD |
| test_nodes.py | TestIdempotentExtractGithub | test_existing_output_ignored | existing_output 無視 |
| test_nodes.py | TestIdempotentExtractGithub | test_no_existing_output_arg | デフォルト引数で動作 |
| test_nodes.py | TestIdempotentExtractGithub | test_empty_existing_output | 空 existing_output で全処理 |
| test_nodes.py | TestEmptyInputGithub | test_empty_partitioned_input | 空入力 -> 空 dict |
| test_nodes.py | TestEmptyInputGithub | test_non_markdown_files_skipped | 非 .md スキップ |
| test_nodes.py | TestEmptyInputGithub | test_post_without_frontmatter | frontmatter なしでも処理 |
| test_nodes.py | TestEmptyInputGithub | test_unicode_content | Unicode 正常処理 |

## フィクスチャファイル

| ファイル | 用途 |
|----------|------|
| tests/fixtures/github_jekyll_post.md | Jekyll ポスト (frontmatter + body) のサンプル |
| tests/fixtures/expected_outputs/parsed_github_item.json | 期待される ParsedItem (provider=github) |

## 実装ヒント

- `src/obsidian_etl/pipelines/extract_github/nodes.py` に以下を実装:
  - `clone_github_repo(url: str, params: dict) -> dict[str, Callable]`: URL パース -> git clone --depth 1 -> sparse-checkout -> Markdown ファイル dict
  - `parse_jekyll(partitioned_input: dict[str, Callable], existing_output: dict = None) -> dict[str, dict]`: Markdown -> frontmatter パース -> ParsedItem dict
  - `convert_frontmatter(partitioned_input: dict[str, Callable]) -> dict[str, dict]`: Jekyll frontmatter -> Obsidian 形式変換
- 既存参照: `src/etl/utils/github_url.py` の `parse_github_url`, `clone_repo`, `parse_frontmatter`, `convert_frontmatter`, `extract_date`, `extract_tags`
- subprocess をモック可能にするため `import subprocess` をモジュールレベルで行う
- file_id: SHA256 の先頭 12 文字 (他プロバイダーと同じ)
- GitHub は会話ではないため messages = [] (data-model.md E-2 参照)
- draft: true / private: true のファイルは除外
- 日付抽出優先順位: frontmatter.date -> filename (YYYY-MM-DD-*) -> body regex -> 現在日時

## FAIL 出力例
```
ERROR: extract_github.test_nodes (unittest.loader._FailedTest.extract_github.test_nodes)
----------------------------------------------------------------------
ImportError: Failed to import test module: extract_github.test_nodes
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/extract_github/test_nodes.py", line 20, in <module>
    from obsidian_etl.pipelines.extract_github.nodes import (
        clone_github_repo,
        convert_frontmatter,
        parse_jekyll,
    )
ImportError: cannot import name 'clone_github_repo' from 'obsidian_etl.pipelines.extract_github.nodes'

----------------------------------------------------------------------
Ran 113 tests in 0.013s

FAILED (errors=1)
```
