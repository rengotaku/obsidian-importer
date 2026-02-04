# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - US1 Transform パイプライン
- FAIL テスト数: 21
- テストファイル: tests/pipelines/transform/test_nodes.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge | ParsedItem から LLM で title, summary, tags が抽出される |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_multiple_items | 複数 ParsedItem がそれぞれ LLM 処理される |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_tags_from_llm | LLM 出力の tags が generated_metadata に反映される |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_english_summary_translation | 英語 summary が日本語に翻訳される |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_japanese_summary_no_translation | 日本語 summary は翻訳されない |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_error_handling | LLM 失敗時にアイテムが除外される |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_partial_failure | 一部失敗時に成功分のみ出力される |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_empty_response | LLM 空レスポンスでアイテムが除外される |
| tests/pipelines/transform/test_nodes.py | test_generate_metadata | generated_metadata から metadata dict が生成される |
| tests/pipelines/transform/test_nodes.py | test_generate_metadata_missing_created_at | created_at=None でフォールバック値が設定される |
| tests/pipelines/transform/test_nodes.py | test_generate_metadata_empty_tags | 空 tags でも metadata が正しく生成される |
| tests/pipelines/transform/test_nodes.py | test_generate_metadata_preserves_original_fields | metadata 生成後も元フィールドが保持される |
| tests/pipelines/transform/test_nodes.py | test_format_markdown | metadata + content から YAML frontmatter + body が生成される |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_frontmatter_values | frontmatter の値が metadata と一致する |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_includes_summary | body に summary が含まれる |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_tags_list | tags がリスト形式で出力される |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_output_filename_basic | タイトルからファイル名が生成される |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_output_filename_special_chars | 特殊文字がサニタイズされる |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_output_filename_unicode | 日本語タイトルが正しくファイル名になる |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_output_filename_long_title | 長いタイトルが切り詰められる |
| tests/pipelines/transform/test_nodes.py | test_format_markdown_output_filename_empty_title | 空タイトルでフォールバック名が生成される |

## テストクラス構成

| クラス | テスト数 | 対象ノード |
|--------|---------|-----------|
| TestExtractKnowledge | 3 | extract_knowledge |
| TestExtractKnowledgeEnglishSummaryTranslation | 2 | extract_knowledge (翻訳) |
| TestExtractKnowledgeErrorHandling | 3 | extract_knowledge (エラー) |
| TestGenerateMetadata | 4 | generate_metadata |
| TestFormatMarkdown | 4 | format_markdown |
| TestFormatMarkdownOutputFilename | 5 | format_markdown (ファイル名) |

## 実装ヒント

### extract_knowledge ノード
- `src/obsidian_etl/pipelines/transform/nodes.py` に `extract_knowledge(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]` を実装
- `obsidian_etl.utils.knowledge_extractor` を import して LLM 呼び出し
- PartitionedDataset パターン: 入力は `dict[str, Callable]`（各 Callable が ParsedItem dict を返す）
- 英語 summary 検出時は `is_english_summary()` + `translate_summary()` で翻訳
- LLM エラー時はアイテムを除外（ログ出力のみ）

### generate_metadata ノード
- `generate_metadata(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]` を実装
- `generated_metadata.title` -> `metadata.title`
- `created_at` (ISO 8601) -> `metadata.created` (YYYY-MM-DD)
- `created_at` が None の場合は現在日付にフォールバック
- `metadata.normalized = True` 固定

### format_markdown ノード
- `format_markdown(partitioned_input: dict[str, Callable]) -> dict[str, dict]` を実装
- 出力キーはサニタイズ済みファイル名（タイトルベース）
- YAML frontmatter + body の Markdown 文字列を生成
- ファイル名の unsafe 文字を除去: `/\:*?"<>|`
- 長いファイル名は 255 文字未満に切り詰め
- 空タイトルはフォールバック（file_id 等）

## FAIL 出力例
```
ERROR: test_nodes (unittest.loader._FailedTest.test_nodes)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_nodes
Traceback (most recent call last):
  File "tests/pipelines/transform/test_nodes.py", line 20, in <module>
    from obsidian_etl.pipelines.transform.nodes import (
        extract_knowledge,
        format_markdown,
        generate_metadata,
    )
ImportError: cannot import name 'extract_knowledge' from 'obsidian_etl.pipelines.transform.nodes'
```
