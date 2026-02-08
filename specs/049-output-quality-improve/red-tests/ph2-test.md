# Phase 2 RED Tests

## Summary

- Phase: Phase 2 - User Story 1: 空コンテンツファイルの除外
- FAIL テスト数: 3
- テストファイル: tests/pipelines/transform/test_nodes.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_skips_empty_content | summary_content が空文字列の場合、アイテムが出力から除外される |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_skips_whitespace_only_content | summary_content が空白文字のみの場合、アイテムが出力から除外される |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_logs_skip_count | 空コンテンツでスキップされたアイテム数がログに記録される |

## テストコード

```python
class TestExtractKnowledgeEmptyContent(unittest.TestCase):
    """extract_knowledge: Empty summary_content -> item excluded from output.

    Tests for User Story 1 - 空コンテンツファイルの除外
    LLM が summary_content を空で返した場合、そのアイテムを出力から除外する。
    """

    def setUp(self):
        """Clean up streaming output files before each test."""
        from obsidian_etl.pipelines.transform.nodes import STREAMING_OUTPUT_DIR

        output_dir = Path.cwd() / STREAMING_OUTPUT_DIR
        if output_dir.exists():
            for pattern in [
                "conv-*.json",
                "item-*.json",
                "db-*.json",
                "empty-*.json",
                "whitespace-*.json",
            ]:
                for f in output_dir.glob(pattern):
                    f.unlink()

    def tearDown(self):
        self.setUp()

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_skips_empty_content(self, mock_llm_extract):
        """summary_content が空文字列の場合、アイテムが出力から除外されること。

        FR-001: システムは summary_content が空のアイテムを出力から除外しなければならない
        """
        # LLM returns valid title and summary but empty summary_content
        mock_llm_extract.return_value = (
            {
                "title": "テストタイトル",
                "summary": "テスト要約。",
                "summary_content": "",  # Empty content
                "tags": ["テスト"],
            },
            None,
        )

        parsed_item = _make_parsed_item(item_id="empty-content", file_id="empty12345678")
        partitioned_input = _make_partitioned_input({"empty-content": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Item with empty summary_content should be excluded
        self.assertEqual(len(result), 0)

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_skips_whitespace_only_content(self, mock_llm_extract):
        """summary_content が空白文字のみの場合、アイテムが出力から除外されること。

        Whitespace-only content (spaces, tabs, newlines) is considered empty.
        """
        # LLM returns whitespace-only summary_content
        mock_llm_extract.return_value = (
            {
                "title": "空白コンテンツ",
                "summary": "空白のみの内容。",
                "summary_content": "   \n\t  ",  # Whitespace only
                "tags": ["空白"],
            },
            None,
        )

        parsed_item = _make_parsed_item(item_id="whitespace-content", file_id="ws123456789012")
        partitioned_input = _make_partitioned_input({"whitespace-content": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Item with whitespace-only summary_content should be excluded
        self.assertEqual(len(result), 0)

    @patch("obsidian_etl.pipelines.transform.nodes.logger")
    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_logs_skip_count(self, mock_llm_extract, mock_logger):
        """空コンテンツでスキップされたアイテム数がログに記録されること。

        FR-002: システムはスキップされたアイテムの件数をログに記録しなければならない
        """
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First item: valid content
                return (
                    {
                        "title": "有効なアイテム",
                        "summary": "有効な要約。",
                        "summary_content": "有効な内容。",
                        "tags": ["有効"],
                    },
                    None,
                )
            elif call_count[0] == 2:
                # Second item: empty content
                return (
                    {
                        "title": "空コンテンツ1",
                        "summary": "要約1。",
                        "summary_content": "",
                        "tags": [],
                    },
                    None,
                )
            else:
                # Third item: whitespace-only content
                return (
                    {
                        "title": "空コンテンツ2",
                        "summary": "要約2。",
                        "summary_content": "  \n  ",
                        "tags": [],
                    },
                    None,
                )

        mock_llm_extract.side_effect = side_effect

        items = {
            "item-valid": _make_parsed_item(item_id="valid", file_id="valid1234567"),
            "item-empty1": _make_parsed_item(item_id="empty1", file_id="empty1234567"),
            "item-empty2": _make_parsed_item(item_id="empty2", file_id="empty2345678"),
        }
        partitioned_input = _make_partitioned_input(items)
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Only 1 item should succeed
        self.assertEqual(len(result), 1)

        # Log should contain skipped_empty count (2 items skipped for empty content)
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        log_messages = " ".join(log_calls)
        self.assertIn("skipped_empty=2", log_messages)
```

## 実装ヒント

1. `src/obsidian_etl/pipelines/transform/nodes.py` の `extract_knowledge` 関数を修正

2. 空コンテンツ判定関数を追加:
   ```python
   def _is_empty_content(content: str | None) -> bool:
       """Return True if content is empty or whitespace-only."""
       if content is None:
           return True
       return not content.strip()
   ```

3. LLM 抽出後に空コンテンツチェックを追加（L116 付近）:
   ```python
   # Check for empty summary_content
   summary_content = knowledge.get("summary_content", "")
   if _is_empty_content(summary_content):
       logger.warning(f"Empty summary_content for {partition_id}. Item excluded.")
       skipped_empty += 1
       continue
   ```

4. サマリーログに `skipped_empty` カウントを追加（L147 付近）:
   ```python
   logger.info(
       f"extract_knowledge: total={total}, skipped={skipped} "
       f"(existing={skipped_existing}, file={skipped_file}), "
       f"processed={processed}, succeeded={len(output)}, failed={failed}, "
       f"skipped_empty={skipped_empty} ({node_elapsed:.1f}s)"
   )
   ```

## FAIL 出力例

```
======================================================================
FAIL: test_extract_knowledge_skips_empty_content (tests.pipelines.transform.test_nodes.TestExtractKnowledgeEmptyContent.test_extract_knowledge_skips_empty_content)
summary_content が空文字列の場合、アイテムが出力から除外されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/transform/test_nodes.py", line 821, in test_extract_knowledge_skips_empty_content
    self.assertEqual(len(result), 0)
AssertionError: 1 != 0

======================================================================
FAIL: test_extract_knowledge_skips_whitespace_only_content (tests.pipelines.transform.test_nodes.TestExtractKnowledgeEmptyContent.test_extract_knowledge_skips_whitespace_only_content)
summary_content が空白文字のみの場合、アイテムが出力から除外されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/transform/test_nodes.py", line 847, in test_extract_knowledge_skips_whitespace_only_content
    self.assertEqual(len(result), 0)
AssertionError: 1 != 0

======================================================================
FAIL: test_extract_knowledge_logs_skip_count (tests.pipelines.transform.test_nodes.TestExtractKnowledgeEmptyContent.test_extract_knowledge_logs_skip_count)
空コンテンツでスキップされたアイテム数がログに記録されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/transform/test_nodes.py", line 907, in test_extract_knowledge_logs_skip_count
    self.assertEqual(len(result), 1)
AssertionError: 3 != 1

----------------------------------------------------------------------
Ran 289 tests in 0.812s

FAILED (failures=3)
```

## 関連要件

- FR-001: システムは summary_content が空のアイテムを出力から除外しなければならない
- FR-002: システムはスキップされたアイテムの件数をログに記録しなければならない
