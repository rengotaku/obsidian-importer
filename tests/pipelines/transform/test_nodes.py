"""Tests for Transform pipeline nodes.

Phase 3 RED tests: extract_knowledge, generate_metadata, format_markdown nodes.
These tests verify:
- LLM knowledge extraction (title, summary, tags) with mocked Ollama
- English summary detection and Japanese translation
- Error handling when LLM fails (item excluded, logged)
- Metadata generation (file_id, created, normalized=True)
- Markdown formatting (YAML frontmatter + body)
- Output filename sanitization from title
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from obsidian_etl.pipelines.transform.nodes import (
    extract_knowledge,
    format_markdown,
    generate_metadata,
)

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


def _make_parsed_item(
    item_id: str = "conv-001-uuid-abcdef",
    source_provider: str = "claude",
    source_path: str = "conversations/conv-001-uuid-abcdef.md",
    conversation_name: str = "Python asyncio discussion",
    created_at: str = "2026-01-15T10:30:00.000000+00:00",
    content: str = "Human: How does Python asyncio work?\n\nAssistant: asyncio is a library for writing concurrent code.",
    file_id: str = "a1b2c3d4e5f6",
    messages: list | None = None,
    is_chunked: bool = False,
    chunk_index: int | None = None,
    total_chunks: int | None = None,
    parent_item_id: str | None = None,
) -> dict:
    """Helper to create a ParsedItem dict for testing."""
    if messages is None:
        messages = [
            {"role": "human", "content": "How does Python asyncio work?"},
            {"role": "assistant", "content": "asyncio is a library for writing concurrent code."},
            {"role": "human", "content": "Can you show me an example?"},
            {"role": "assistant", "content": "Sure, here is an example using async/await."},
        ]
    return {
        "item_id": item_id,
        "source_provider": source_provider,
        "source_path": source_path,
        "conversation_name": conversation_name,
        "created_at": created_at,
        "content": content,
        "file_id": file_id,
        "messages": messages,
        "is_chunked": is_chunked,
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
        "parent_item_id": parent_item_id,
    }


def _make_params() -> dict:
    """Helper to create default import params for testing."""
    return {
        "ollama": {
            "defaults": {
                "model": "gemma3:12b",
                "base_url": "http://localhost:11434",
                "timeout": 120,
                "temperature": 0.2,
            },
            "max_retries": 3,
        },
    }


def _make_partitioned_input(items: dict[str, dict]) -> dict[str, callable]:
    """Create PartitionedDataset-style input (dict of callables)."""
    return {key: (lambda v=val: v) for key, val in items.items()}


# ============================================================
# extract_knowledge node tests
# ============================================================


class TestExtractKnowledge(unittest.TestCase):
    """extract_knowledge: ParsedItem -> generated_metadata with title, summary, tags."""

    def setUp(self):
        """Clean up streaming output files before each test."""
        from obsidian_etl.pipelines.transform.nodes import STREAMING_OUTPUT_DIR

        output_dir = Path.cwd() / STREAMING_OUTPUT_DIR
        if output_dir.exists():
            # Remove test-generated files (conv-*, item-*, db-*)
            for pattern in ["conv-*.json", "item-*.json", "db-*.json"]:
                for f in output_dir.glob(pattern):
                    f.unlink()

    def tearDown(self):
        """Clean up streaming output files after each test."""
        self.setUp()  # Same cleanup

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge(self, mock_llm_extract):
        """ParsedItem から LLM で title, summary, tags が抽出されること。"""
        # Mock LLM response
        mock_llm_extract.return_value = (
            {
                "title": "Python asyncio の仕組み",
                "summary": "Python の asyncio について議論した。",
                "summary_content": "## asyncio の概要\n\nasyncio はイベントループベースの非同期フレームワーク。",
            },
            None,  # no error
        )

        parsed_item = _make_parsed_item()
        partitioned_input = _make_partitioned_input({"conv-001": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Should return dict of partition_id -> item with generated_metadata
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)

        item = list(result.values())[0]

        # generated_metadata should be present
        self.assertIn("generated_metadata", item)
        gm = item["generated_metadata"]
        self.assertEqual(gm["title"], "Python asyncio の仕組み")
        self.assertEqual(gm["summary"], "Python の asyncio について議論した。")
        self.assertIn("summary_content", gm)

        # Original fields should be preserved
        self.assertEqual(item["item_id"], "conv-001-uuid-abcdef")
        self.assertEqual(item["source_provider"], "claude")
        self.assertEqual(item["file_id"], "a1b2c3d4e5f6")

        # LLM should have been called
        mock_llm_extract.assert_called_once()

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_multiple_items(self, mock_llm_extract):
        """複数の ParsedItem がそれぞれ LLM 処理されること。"""
        mock_llm_extract.return_value = (
            {
                "title": "テスト",
                "summary": "テスト要約",
                "summary_content": "テスト内容",
            },
            None,
        )

        items = {
            "item-a": _make_parsed_item(item_id="a", file_id="aaa111bbb222"),
            "item-b": _make_parsed_item(item_id="b", file_id="ccc333ddd444"),
        }
        partitioned_input = _make_partitioned_input(items)
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        self.assertEqual(len(result), 2)
        self.assertEqual(mock_llm_extract.call_count, 2)

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_tags_from_llm(self, mock_llm_extract):
        """LLM 出力に tags が含まれる場合、generated_metadata に反映されること。"""
        mock_llm_extract.return_value = (
            {
                "title": "データベース設計",
                "summary": "RDB の正規化を議論した。",
                "summary_content": "正規化の基本と実践。",
                "tags": ["データベース", "正規化", "SQL"],
            },
            None,
        )

        parsed_item = _make_parsed_item(
            item_id="db-conv",
            conversation_name="Database design",
        )
        partitioned_input = _make_partitioned_input({"db-conv": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        item = list(result.values())[0]
        gm = item["generated_metadata"]
        self.assertIn("tags", gm)
        self.assertIsInstance(gm["tags"], list)
        self.assertGreater(len(gm["tags"]), 0)


class TestExtractKnowledgeEnglishSummaryTranslation(unittest.TestCase):
    """extract_knowledge: English summary -> Japanese translation."""

    def setUp(self):
        """Clean up streaming output files before each test."""
        from obsidian_etl.pipelines.transform.nodes import STREAMING_OUTPUT_DIR

        output_dir = Path.cwd() / STREAMING_OUTPUT_DIR
        if output_dir.exists():
            for pattern in ["conv-*.json", "item-*.json", "db-*.json"]:
                for f in output_dir.glob(pattern):
                    f.unlink()

    def tearDown(self):
        self.setUp()

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.translate_summary")
    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.is_english_summary")
    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_english_summary_translation(
        self, mock_llm_extract, mock_is_english, mock_translate
    ):
        """英語の summary が日本語に翻訳されること。"""
        mock_llm_extract.return_value = (
            {
                "title": "Python asyncio overview",
                "summary": "The user asked about Python asyncio and how event loops work.",
                "summary_content": "Discussion about asyncio.",
            },
            None,
        )
        mock_is_english.return_value = True
        mock_translate.return_value = (
            "ユーザーは Python asyncio とイベントループの仕組みについて質問した。",
            None,
        )

        parsed_item = _make_parsed_item()
        partitioned_input = _make_partitioned_input({"conv-en": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        item = list(result.values())[0]
        gm = item["generated_metadata"]

        # Summary should be translated to Japanese
        self.assertIn("summary", gm)
        # The translated summary should be in Japanese (not the English original)
        self.assertNotEqual(
            gm["summary"],
            "The user asked about Python asyncio and how event loops work.",
        )
        self.assertIn("asyncio", gm["summary"])

        # is_english_summary should have been called
        mock_is_english.assert_called()
        # translate_summary should have been called
        mock_translate.assert_called()

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.is_english_summary")
    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_japanese_summary_no_translation(
        self, mock_llm_extract, mock_is_english
    ):
        """日本語の summary は翻訳されないこと。"""
        mock_llm_extract.return_value = (
            {
                "title": "Python asyncio の仕組み",
                "summary": "Python の asyncio について議論した。",
                "summary_content": "asyncio の使い方。",
            },
            None,
        )
        mock_is_english.return_value = False

        parsed_item = _make_parsed_item()
        partitioned_input = _make_partitioned_input({"conv-jp": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        item = list(result.values())[0]
        gm = item["generated_metadata"]

        # Japanese summary should remain unchanged
        self.assertEqual(gm["summary"], "Python の asyncio について議論した。")


class TestExtractKnowledgeErrorHandling(unittest.TestCase):
    """extract_knowledge: LLM failure -> item excluded, logged."""

    def setUp(self):
        """Clean up streaming output files before each test."""
        from obsidian_etl.pipelines.transform.nodes import STREAMING_OUTPUT_DIR

        output_dir = Path.cwd() / STREAMING_OUTPUT_DIR
        if output_dir.exists():
            for pattern in ["conv-*.json", "item-*.json", "db-*.json"]:
                for f in output_dir.glob(pattern):
                    f.unlink()

    def tearDown(self):
        self.setUp()

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_error_handling(self, mock_llm_extract):
        """LLM 呼び出しが失敗した場合、review としてマークされること。"""
        mock_llm_extract.return_value = (None, "Connection error: refused")

        parsed_item = _make_parsed_item()
        partitioned_input = _make_partitioned_input({"conv-fail": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Failed item should be in result, marked for review
        self.assertEqual(len(result), 1)
        item = result["conv-fail"]
        self.assertIn("review_reason", item)
        self.assertIn("Connection error", item["review_reason"])
        self.assertEqual(item["review_node"], "extract_knowledge")

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_partial_failure(self, mock_llm_extract):
        """複数アイテムのうち一部が失敗した場合、成功分は通常出力、失敗分はreview出力されること。"""
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return (
                    {
                        "title": "成功アイテム",
                        "summary": "成功した。",
                        "summary_content": "内容。",
                    },
                    None,
                )
            else:
                return (None, "Timeout (120s)")

        mock_llm_extract.side_effect = side_effect

        items = {
            "item-ok": _make_parsed_item(item_id="ok", file_id="ok1234567890"),
            "item-fail": _make_parsed_item(item_id="fail", file_id="fail12345678"),
        }
        partitioned_input = _make_partitioned_input(items)
        params = _make_params()
        # Disable ratio check for this test (testing LLM failure handling, not ratio)
        params["transform"] = {"min_content_ratio": 0}

        result = extract_knowledge(partitioned_input, params)

        # Both items should be in result
        self.assertEqual(len(result), 2)
        # Find the LLM-processed item (may have compression ratio review, but not LLM failure)
        ok_item = result.get("item-ok")
        self.assertIsNotNone(ok_item)
        self.assertEqual(ok_item["generated_metadata"]["title"], "成功アイテム")
        # If review_reason exists, it should NOT be LLM failure (may be compression ratio)
        if "review_reason" in ok_item:
            self.assertNotIn("LLM extraction failed", ok_item["review_reason"])
        # Find the failed item (marked for review due to LLM failure)
        fail_item = result.get("item-fail")
        self.assertIsNotNone(fail_item)
        self.assertIn("review_reason", fail_item)
        self.assertIn("Timeout", fail_item["review_reason"])
        self.assertEqual(fail_item["review_node"], "extract_knowledge")

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_empty_response(self, mock_llm_extract):
        """LLM が空レスポンスを返した場合、review としてマークされること。"""
        mock_llm_extract.return_value = ({}, "Empty response")

        parsed_item = _make_parsed_item()
        partitioned_input = _make_partitioned_input({"conv-empty": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Item should be in result, marked for review
        self.assertEqual(len(result), 1)
        item = result["conv-empty"]
        self.assertIn("review_reason", item)
        self.assertIn("Empty response", item["review_reason"])
        self.assertEqual(item["review_node"], "extract_knowledge")


# ============================================================
# generate_metadata node tests
# ============================================================


class TestGenerateMetadata(unittest.TestCase):
    """generate_metadata: generated_metadata -> metadata dict with file_id, created, normalized=True."""

    def _make_knowledge_item(self, **overrides) -> dict:
        """Create an item with generated_metadata (output of extract_knowledge)."""
        item = _make_parsed_item()
        item["generated_metadata"] = {
            "title": "Python asyncio の仕組み",
            "summary": "Python の asyncio について議論した。",
            "summary_content": "asyncio の使い方。",
            "tags": ["Python", "asyncio"],
        }
        item.update(overrides)
        return item

    def test_generate_metadata(self):
        """generated_metadata から metadata dict が正しく生成されること。"""
        knowledge_item = self._make_knowledge_item()
        partitioned_input = _make_partitioned_input({"item-001": knowledge_item})
        params = _make_params()

        result = generate_metadata(partitioned_input, params)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)

        item = list(result.values())[0]
        self.assertIn("metadata", item)

        metadata = item["metadata"]
        # title from generated_metadata
        self.assertEqual(metadata["title"], "Python asyncio の仕組み")
        # created from created_at (date part only)
        self.assertEqual(metadata["created"], "2026-01-15")
        # tags from generated_metadata
        self.assertEqual(metadata["tags"], ["Python", "asyncio"])
        # source_provider preserved
        self.assertEqual(metadata["source_provider"], "claude")
        # file_id preserved
        self.assertEqual(metadata["file_id"], "a1b2c3d4e5f6")
        # normalized flag always True
        self.assertTrue(metadata["normalized"])

    def test_generate_metadata_missing_created_at(self):
        """created_at が None の場合、created がフォールバック値になること。"""
        knowledge_item = self._make_knowledge_item(created_at=None)
        partitioned_input = _make_partitioned_input({"item-no-date": knowledge_item})
        params = _make_params()

        result = generate_metadata(partitioned_input, params)

        item = list(result.values())[0]
        metadata = item["metadata"]

        # created should still be present (fallback to current date or empty)
        self.assertIn("created", metadata)
        # Should be a string, not None
        self.assertIsInstance(metadata["created"], str)
        self.assertGreater(len(metadata["created"]), 0)

    def test_generate_metadata_empty_tags(self):
        """tags が空リストの場合でも metadata が正しく生成されること。"""
        knowledge_item = self._make_knowledge_item()
        knowledge_item["generated_metadata"]["tags"] = []
        partitioned_input = _make_partitioned_input({"item-no-tags": knowledge_item})
        params = _make_params()

        result = generate_metadata(partitioned_input, params)

        item = list(result.values())[0]
        metadata = item["metadata"]

        self.assertIsInstance(metadata["tags"], list)
        self.assertEqual(len(metadata["tags"]), 0)

    def test_generate_metadata_preserves_original_fields(self):
        """metadata 生成後も元のフィールドが保持されること。"""
        knowledge_item = self._make_knowledge_item()
        partitioned_input = _make_partitioned_input({"item-preserve": knowledge_item})
        params = _make_params()

        result = generate_metadata(partitioned_input, params)

        item = list(result.values())[0]

        # Original ParsedItem fields preserved
        self.assertEqual(item["item_id"], "conv-001-uuid-abcdef")
        self.assertEqual(item["content"], knowledge_item["content"])
        self.assertEqual(item["messages"], knowledge_item["messages"])
        # generated_metadata preserved
        self.assertIn("generated_metadata", item)


# ============================================================
# format_markdown node tests
# ============================================================


class TestFormatMarkdown(unittest.TestCase):
    """format_markdown: metadata + content -> YAML frontmatter + body."""

    def _make_metadata_item(self, **overrides) -> dict:
        """Create an item with metadata (output of generate_metadata)."""
        item = _make_parsed_item()
        item["generated_metadata"] = {
            "title": "Python asyncio の仕組み",
            "summary": "Python の asyncio について議論した。",
            "summary_content": "## asyncio の概要\n\nasyncio はイベントループベースの非同期フレームワーク。",
            "tags": ["Python", "asyncio"],
        }
        item["metadata"] = {
            "title": "Python asyncio の仕組み",
            "created": "2026-01-15",
            "tags": ["Python", "asyncio"],
            "source_provider": "claude",
            "file_id": "a1b2c3d4e5f6",
            "normalized": True,
        }
        item.update(overrides)
        return item

    def test_format_markdown(self):
        """metadata + content から YAML frontmatter + body の Markdown が生成されること。"""
        metadata_item = self._make_metadata_item()
        partitioned_input = _make_partitioned_input({"item-fmt": metadata_item})

        result = format_markdown(partitioned_input)

        # Result should be a tuple (normal_dict, review_dict)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        normal_dict, review_dict = result

        # Item without review_reason should be in normal_dict
        self.assertEqual(len(normal_dict), 1)
        self.assertEqual(len(review_dict), 0)

        # Output key should be sanitized filename
        output_key = list(normal_dict.keys())[0]
        markdown = normal_dict[output_key]

        # Output should be a string (markdown content)
        self.assertIsInstance(markdown, str)

        # Should start with YAML frontmatter
        self.assertTrue(markdown.startswith("---\n"))
        # Should have closing frontmatter delimiter
        self.assertIn("\n---\n", markdown)

        # Frontmatter should contain metadata fields
        self.assertIn("title:", markdown)
        self.assertIn("created:", markdown)
        self.assertIn("tags:", markdown)
        self.assertIn("normalized: true", markdown)
        self.assertIn("file_id:", markdown)

        # Body should contain summary or content
        body_start = markdown.index("\n---\n", 4) + 5  # after second ---
        body = markdown[body_start:]
        self.assertGreater(len(body.strip()), 0)

    def test_format_markdown_frontmatter_values(self):
        """frontmatter の値が metadata と一致すること。"""
        metadata_item = self._make_metadata_item()
        partitioned_input = _make_partitioned_input({"item-vals": metadata_item})

        normal_dict, review_dict = format_markdown(partitioned_input)

        markdown = list(normal_dict.values())[0]

        # Extract frontmatter section
        parts = markdown.split("---\n", 2)
        self.assertEqual(len(parts), 3)  # empty, frontmatter, body

        frontmatter = parts[1]

        # Verify key values
        self.assertIn("Python asyncio", frontmatter)
        self.assertIn("2026-01-15", frontmatter)
        self.assertIn("a1b2c3d4e5f6", frontmatter)

    def test_format_markdown_includes_summary(self):
        """Markdown body に summary が含まれること。"""
        metadata_item = self._make_metadata_item()
        partitioned_input = _make_partitioned_input({"item-sum": metadata_item})

        normal_dict, review_dict = format_markdown(partitioned_input)

        markdown = list(normal_dict.values())[0]

        # Body should contain summary text
        self.assertIn("asyncio", markdown)

    def test_format_markdown_tags_list(self):
        """tags がリスト形式で frontmatter に出力されること。"""
        metadata_item = self._make_metadata_item()
        partitioned_input = _make_partitioned_input({"item-tags": metadata_item})

        normal_dict, review_dict = format_markdown(partitioned_input)

        markdown = list(normal_dict.values())[0]

        # Tags should be in YAML list format with quoted values
        self.assertIn('  - "Python"', markdown)
        self.assertIn('  - "asyncio"', markdown)


class TestFormatMarkdownOutputFilename(unittest.TestCase):
    """format_markdown: title -> sanitized filename."""

    def _make_metadata_item_with_title(self, title: str) -> dict:
        """Create item with specific title for filename testing."""
        item = _make_parsed_item()
        item["generated_metadata"] = {
            "title": title,
            "summary": "テスト要約。",
            "summary_content": "テスト内容。",
            "tags": [],
        }
        item["metadata"] = {
            "title": title,
            "created": "2026-01-15",
            "tags": [],
            "source_provider": "claude",
            "file_id": "a1b2c3d4e5f6",
            "normalized": True,
        }
        return item

    def test_format_markdown_output_filename_basic(self):
        """タイトルからサニタイズされたファイル名が生成されること。"""
        item = self._make_metadata_item_with_title("Python asyncio の仕組み")
        partitioned_input = _make_partitioned_input({"item-fn": item})

        normal_dict, review_dict = format_markdown(partitioned_input)

        output_key = list(normal_dict.keys())[0]
        # Output key should contain the title (extension added by PartitionedDataset)
        self.assertIn("Python asyncio", output_key)

    def test_format_markdown_output_filename_special_chars(self):
        """特殊文字を含むタイトルがサニタイズされること。"""
        item = self._make_metadata_item_with_title("C++ vs C#: パフォーマンス比較 (2026/01)")
        partitioned_input = _make_partitioned_input({"item-special": item})

        normal_dict, review_dict = format_markdown(partitioned_input)

        output_key = list(normal_dict.keys())[0]

        # Filename should not contain filesystem-unsafe characters
        unsafe_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        for char in unsafe_chars:
            self.assertNotIn(char, output_key, f"Filename contains unsafe char: {char}")

    def test_format_markdown_output_filename_unicode(self):
        """Unicode タイトル（日本語）が正しくファイル名になること。"""
        item = self._make_metadata_item_with_title("データベース正規化の基礎")
        partitioned_input = _make_partitioned_input({"item-unicode": item})

        normal_dict, review_dict = format_markdown(partitioned_input)

        output_key = list(normal_dict.keys())[0]

        # Should contain the Japanese title
        self.assertIn("データベース正規化", output_key)

    def test_format_markdown_output_filename_long_title(self):
        """非常に長いタイトルが適切に切り詰められること。"""
        long_title = "A" * 300
        item = self._make_metadata_item_with_title(long_title)
        partitioned_input = _make_partitioned_input({"item-long": item})

        normal_dict, review_dict = format_markdown(partitioned_input)

        output_key = list(normal_dict.keys())[0]

        # Filename should be reasonably short (< 255 chars for filesystem)
        self.assertLess(len(output_key), 256)

    def test_format_markdown_output_filename_empty_title(self):
        """空タイトルの場合、フォールバックのファイル名が生成されること。"""
        item = self._make_metadata_item_with_title("")
        partitioned_input = _make_partitioned_input({"item-empty": item})

        normal_dict, review_dict = format_markdown(partitioned_input)

        output_key = list(normal_dict.keys())[0]

        # Should have some fallback filename
        self.assertGreater(len(output_key), 0)


# ============================================================
# Idempotent transform tests (Phase 6 - US2)
# ============================================================


class TestIdempotentTransform(unittest.TestCase):
    """extract_knowledge: existing output partitions -> skip items, no LLM call."""

    def setUp(self):
        """Clean up streaming output files before each test."""
        from obsidian_etl.pipelines.transform.nodes import STREAMING_OUTPUT_DIR

        output_dir = Path.cwd() / STREAMING_OUTPUT_DIR
        if output_dir.exists():
            for pattern in ["conv-*.json", "item-*.json", "db-*.json"]:
                for f in output_dir.glob(pattern):
                    f.unlink()

    def tearDown(self):
        self.setUp()

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_idempotent_transform_skips_existing(self, mock_llm_extract):
        """existing_output に存在するアイテムは LLM 呼び出しなしでスキップされること。"""
        mock_llm_extract.return_value = (
            {
                "title": "新規アイテム",
                "summary": "新規アイテムの要約。",
                "summary_content": "新規アイテムの内容。",
                "tags": ["新規"],
            },
            None,
        )

        # 3 items in input
        items = {
            "item-a": _make_parsed_item(item_id="a", file_id="aaa111bbb222"),
            "item-b": _make_parsed_item(item_id="b", file_id="bbb222ccc333"),
            "item-c": _make_parsed_item(item_id="c", file_id="ccc333ddd444"),
        }
        partitioned_input = _make_partitioned_input(items)
        params = _make_params()

        # 2 items already exist in output
        existing_item_a = {**items["item-a"], "generated_metadata": {"title": "既存A"}}
        existing_item_b = {**items["item-b"], "generated_metadata": {"title": "既存B"}}
        existing_output = {
            "item-a": lambda: existing_item_a,
            "item-b": lambda: existing_item_b,
        }

        result = extract_knowledge(partitioned_input, params, existing_output=existing_output)

        # Only 1 new item should be processed
        self.assertEqual(len(result), 1)
        self.assertIn("item-c", result)

        # LLM should only be called once (for item-c)
        self.assertEqual(mock_llm_extract.call_count, 1)

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_idempotent_transform_all_existing_no_llm_call(self, mock_llm_extract):
        """全アイテムが existing_output にある場合、LLM が一切呼ばれないこと。"""
        items = {
            "item-a": _make_parsed_item(item_id="a", file_id="aaa111bbb222"),
            "item-b": _make_parsed_item(item_id="b", file_id="bbb222ccc333"),
        }
        partitioned_input = _make_partitioned_input(items)
        params = _make_params()

        # All items exist
        existing_output = {
            "item-a": lambda: {**items["item-a"], "generated_metadata": {"title": "既存A"}},
            "item-b": lambda: {**items["item-b"], "generated_metadata": {"title": "既存B"}},
        }

        result = extract_knowledge(partitioned_input, params, existing_output=existing_output)

        self.assertEqual(len(result), 0)
        mock_llm_extract.assert_not_called()

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_idempotent_transform_no_existing_output_processes_all(self, mock_llm_extract):
        """existing_output 引数なしで全アイテムが LLM 処理されること（後方互換性）。"""
        mock_llm_extract.return_value = (
            {
                "title": "テスト",
                "summary": "テスト要約",
                "summary_content": "テスト内容",
            },
            None,
        )

        items = {
            "item-a": _make_parsed_item(item_id="a", file_id="aaa111bbb222"),
            "item-b": _make_parsed_item(item_id="b", file_id="bbb222ccc333"),
        }
        partitioned_input = _make_partitioned_input(items)
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        self.assertEqual(len(result), 2)
        self.assertEqual(mock_llm_extract.call_count, 2)


# ============================================================
# Empty content filtering tests (Phase 2 - US1)
# ============================================================


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

        # Item with empty summary_content should be marked for review
        self.assertEqual(len(result), 1)
        item = result["empty-content"]
        self.assertIn("review_reason", item)
        self.assertIn("empty summary_content", item["review_reason"])
        self.assertEqual(item["review_node"], "extract_knowledge")

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_skips_whitespace_only_content(self, mock_llm_extract):
        """summary_content が空白文字のみの場合、review としてマークされること。

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

        # Item with whitespace-only summary_content should be marked for review
        self.assertEqual(len(result), 1)
        item = result["whitespace-content"]
        self.assertIn("review_reason", item)
        self.assertIn("empty summary_content", item["review_reason"])

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

        # All 3 items should be in result
        self.assertEqual(len(result), 3)
        # Check that 2 items are marked for review due to empty content specifically
        empty_review_items = [
            k
            for k, v in result.items()
            if v.get("review_reason", "").startswith("LLM returned empty")
        ]
        self.assertEqual(len(empty_review_items), 2)

        # Log should contain skipped_empty count (2 items marked for review due to empty content)
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        log_messages = " ".join(log_calls)
        self.assertIn("skipped_empty=2", log_messages)


# ============================================================
# Title sanitization tests (Phase 3 - US2)
# ============================================================


class TestSanitizeFilename(unittest.TestCase):
    """_sanitize_filename: title sanitization for filenames.

    Tests for User Story 2 - タイトルサニタイズ
    タイトルから絵文字、ブラケット、ファイルパス記号を除去する。
    """

    def test_sanitize_filename_removes_emoji(self):
        """タイトルから絵文字が除去されること。

        FR-003: システムはタイトルから絵文字を除去しなければならない

        Input: "🚀 Python入門 📚"
        Expected: "Python入門" (emoji removed, spaces normalized)
        """
        from obsidian_etl.pipelines.transform.nodes import _sanitize_filename

        title = "🚀 Python入門 📚"
        file_id = "abc123def456"

        result = _sanitize_filename(title, file_id)

        # Emoji should be removed
        self.assertNotIn("🚀", result)
        self.assertNotIn("📚", result)
        # Content should be preserved
        self.assertIn("Python入門", result)
        # Spaces should be normalized (no leading/trailing/multiple spaces)
        self.assertEqual(result.strip(), result)
        self.assertNotIn("  ", result)

    def test_sanitize_filename_removes_brackets(self):
        """タイトルからブラケット記号が除去されること。

        FR-004: システムはタイトルからブラケット記号（`[]`, `()`）を除去しなければならない

        Input: "React [入門] (2026)"
        Expected: "React 入門 2026" (brackets removed)
        """
        from obsidian_etl.pipelines.transform.nodes import _sanitize_filename

        title = "React [入門] (2026)"
        file_id = "abc123def456"

        result = _sanitize_filename(title, file_id)

        # Brackets should be removed
        self.assertNotIn("[", result)
        self.assertNotIn("]", result)
        self.assertNotIn("(", result)
        self.assertNotIn(")", result)
        # Content should be preserved
        self.assertIn("React", result)
        self.assertIn("入門", result)
        self.assertIn("2026", result)

    def test_sanitize_filename_removes_tilde_percent(self):
        """タイトルからチルダとパーセント記号が除去されること。

        FR-005: システムはタイトルからファイルパス記号（`~`, `%`）を除去しなければならない

        Input: "~/home/100% Complete"
        Expected: "home100 Complete" (tilde, slash, and percent removed)
        """
        from obsidian_etl.pipelines.transform.nodes import _sanitize_filename

        title = "~/home/100% Complete"
        file_id = "abc123def456"

        result = _sanitize_filename(title, file_id)

        # Tilde and percent should be removed
        self.assertNotIn("~", result)
        self.assertNotIn("%", result)
        # Slash should also be removed (existing behavior)
        self.assertNotIn("/", result)
        # Content should be preserved
        self.assertIn("home", result)
        self.assertIn("100", result)
        self.assertIn("Complete", result)

    def test_sanitize_filename_fallback_to_file_id(self):
        """サニタイズ後にタイトルが空になる場合、file_id[:12] がフォールバックとして使用されること。

        FR-006: システムはサニタイズ後に空になったタイトルに対して file_id ベースの代替タイトルを生成しなければならない

        Input: "🚀🚀🚀" (only emoji)
        Expected: file_id[:12] as fallback
        """
        from obsidian_etl.pipelines.transform.nodes import _sanitize_filename

        title = "🚀🚀🚀"  # Only emoji - should become empty after sanitization
        file_id = "abc123def456789"

        result = _sanitize_filename(title, file_id)

        # When title becomes empty, should fallback to file_id[:12]
        self.assertEqual(result, file_id[:12])
        self.assertEqual(result, "abc123def456")


# ============================================================
# Summary length warning tests (Phase 6 - US5)
# ============================================================


# ============================================================
# Review reason tests (Phase 4 - US2)
# ============================================================


class TestExtractKnowledgeReviewReason(unittest.TestCase):
    """extract_knowledge: Low compression ratio -> review_reason added.

    Tests for User Story 2 - 圧縮率検証
    圧縮率が基準未達の場合、アイテムを除外せず review_reason フラグを追加する。
    """

    def setUp(self):
        """Clean up streaming output files before each test."""
        from obsidian_etl.pipelines.transform.nodes import STREAMING_OUTPUT_DIR

        output_dir = Path.cwd() / STREAMING_OUTPUT_DIR
        if output_dir.exists():
            for pattern in ["conv-*.json", "item-*.json", "low-ratio-*.json", "valid-ratio-*.json"]:
                for f in output_dir.glob(pattern):
                    f.unlink()

    def tearDown(self):
        self.setUp()

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_adds_review_reason(self, mock_llm_extract):
        """圧縮率が基準未達の場合、item に review_reason が追加されること。

        FR-005: システムは圧縮率が基準未達のアイテムに review_reason を追加しなければならない

        When compression ratio is below threshold:
        - review_reason should be added to item
        - Format: "extract_knowledge: body_ratio=X.X% < threshold=Y.Y%"
        - Item should NOT be excluded (still in output)
        """
        # Create a large original content (10000+ chars -> threshold 5%)
        # LLM returns small summary_content that results in < 5% ratio
        large_content = "A" * 10000  # 10000 chars -> threshold = 5%
        small_summary = "B" * 400  # 400 chars = 4% of 10000 (below 5% threshold)

        mock_llm_extract.return_value = (
            {
                "title": "低圧縮率テスト",
                "summary": "テスト要約。",
                "summary_content": small_summary,
                "tags": ["テスト"],
            },
            None,
        )

        parsed_item = _make_parsed_item(
            item_id="low-ratio-item",
            file_id="lowratio12345",
            content=large_content,
        )
        partitioned_input = _make_partitioned_input({"low-ratio-item": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Item should NOT be excluded - it should be in the output
        self.assertEqual(len(result), 1)
        self.assertIn("low-ratio-item", result)

        item = result["low-ratio-item"]

        # review_reason should be added to the item
        self.assertIn("review_reason", item)

        # review_reason format: "extract_knowledge: body_ratio=X.X% < threshold=Y.Y%"
        review_reason = item["review_reason"]
        self.assertIn("extract_knowledge", review_reason)
        self.assertIn("body_ratio=", review_reason)
        self.assertIn("threshold=", review_reason)
        # Should contain actual percentages (4.0% < 5.0%)
        self.assertIn("4.0%", review_reason)
        self.assertIn("5.0%", review_reason)

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_no_review_reason_when_valid(self, mock_llm_extract):
        """圧縮率が基準達成の場合、review_reason がないこと。

        FR-006: システムは圧縮率が基準を満たすアイテムには review_reason を追加してはならない

        When compression ratio meets or exceeds threshold:
        - review_reason should NOT be present in item
        - Item should be included in output normally
        """
        # Create content where ratio meets threshold
        # 5000 chars -> threshold = 15%
        medium_content = "A" * 5000
        valid_summary = "B" * 1000  # 1000 chars = 20% of 5000 (meets 15% threshold)

        mock_llm_extract.return_value = (
            {
                "title": "正常圧縮率テスト",
                "summary": "テスト要約。",
                "summary_content": valid_summary,
                "tags": ["テスト"],
            },
            None,
        )

        parsed_item = _make_parsed_item(
            item_id="valid-ratio-item",
            file_id="validratio123",
            content=medium_content,
        )
        partitioned_input = _make_partitioned_input({"valid-ratio-item": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Item should be included in output
        self.assertEqual(len(result), 1)
        self.assertIn("valid-ratio-item", result)

        item = result["valid-ratio-item"]

        # review_reason should NOT be present
        self.assertNotIn("review_reason", item)

        # generated_metadata should be present as usual
        self.assertIn("generated_metadata", item)
        self.assertEqual(item["generated_metadata"]["title"], "正常圧縮率テスト")


# ============================================================
# format_markdown review output tests (Phase 5 - US2)
# ============================================================


class TestFormatMarkdownReviewOutput(unittest.TestCase):
    """format_markdown: Items with review_reason -> review dict, others -> normal dict.

    Tests for User Story 2 - レビューフォルダ出力
    format_markdown は tuple を返し、review_reason を持つアイテムは review dict に振り分ける。
    """

    def _make_metadata_item_with_review(
        self,
        title: str = "テストタイトル",
        review_reason: str | None = None,
    ) -> dict:
        """Create an item with metadata, optionally with review_reason."""
        item = _make_parsed_item()
        item["generated_metadata"] = {
            "title": title,
            "summary": "テスト要約。",
            "summary_content": "## テスト内容\n\nテストの詳細内容。",
            "tags": ["テスト"],
        }
        item["metadata"] = {
            "title": title,
            "created": "2026-01-15",
            "tags": ["テスト"],
            "source_provider": "claude",
            "file_id": "review12345678",
            "normalized": True,
        }
        if review_reason is not None:
            item["review_reason"] = review_reason
        return item

    def test_format_markdown_returns_tuple(self):
        """format_markdown が tuple (normal_dict, review_dict) を返すこと。

        FR-007: システムは format_markdown から (normal, review) の tuple を返さなければならない
        """
        item = self._make_metadata_item_with_review()
        partitioned_input = _make_partitioned_input({"item-normal": item})

        result = format_markdown(partitioned_input)

        # Result should be a tuple of two dicts
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        normal_dict, review_dict = result
        self.assertIsInstance(normal_dict, dict)
        self.assertIsInstance(review_dict, dict)

    def test_format_markdown_review_reason_to_review_dict(self):
        """review_reason を持つアイテムが review dict に含まれること。

        FR-008: システムは review_reason を持つアイテムを review dict に振り分けなければならない
        """
        item_with_review = self._make_metadata_item_with_review(
            title="要レビュー記事",
            review_reason="extract_knowledge: body_ratio=5.0% < threshold=10.0%",
        )
        partitioned_input = _make_partitioned_input({"item-review": item_with_review})

        result = format_markdown(partitioned_input)

        normal_dict, review_dict = result

        # Item with review_reason should be in review_dict, not in normal_dict
        self.assertEqual(len(normal_dict), 0)
        self.assertEqual(len(review_dict), 1)

        # Verify content is markdown
        review_content = list(review_dict.values())[0]
        self.assertIsInstance(review_content, str)
        self.assertTrue(review_content.startswith("---\n"))

    def test_format_markdown_no_review_reason_to_normal_dict(self):
        """review_reason を持たないアイテムが normal dict に含まれること。

        FR-009: システムは review_reason を持たないアイテムを normal dict に振り分けなければならない
        """
        item_without_review = self._make_metadata_item_with_review(
            title="通常記事",
            review_reason=None,
        )
        partitioned_input = _make_partitioned_input({"item-normal": item_without_review})

        result = format_markdown(partitioned_input)

        normal_dict, review_dict = result

        # Item without review_reason should be in normal_dict, not in review_dict
        self.assertEqual(len(normal_dict), 1)
        self.assertEqual(len(review_dict), 0)

        # Verify content is markdown
        normal_content = list(normal_dict.values())[0]
        self.assertIsInstance(normal_content, str)
        self.assertTrue(normal_content.startswith("---\n"))

    def test_format_markdown_mixed_items(self):
        """review_reason の有無で正しく振り分けられること（混在ケース）。

        複数アイテムがある場合、各アイテムは review_reason の有無で適切な dict に振り分けられる。
        """
        item_normal = self._make_metadata_item_with_review(
            title="通常記事",
            review_reason=None,
        )
        item_normal["file_id"] = "normal123456"

        item_review = self._make_metadata_item_with_review(
            title="要レビュー記事",
            review_reason="extract_knowledge: body_ratio=3.0% < threshold=10.0%",
        )
        item_review["file_id"] = "review123456"

        partitioned_input = _make_partitioned_input(
            {
                "item-normal": item_normal,
                "item-review": item_review,
            }
        )

        result = format_markdown(partitioned_input)

        normal_dict, review_dict = result

        # One item in each dict
        self.assertEqual(len(normal_dict), 1)
        self.assertEqual(len(review_dict), 1)


class TestExtractKnowledgeSummaryLength(unittest.TestCase):
    """extract_knowledge: Long summary -> warning logged.

    Tests for User Story 5 - summary/content 逆転の検出
    summary が 500 文字を超える場合に警告ログを出力する。
    """

    def setUp(self):
        """Clean up streaming output files before each test."""
        from obsidian_etl.pipelines.transform.nodes import STREAMING_OUTPUT_DIR

        output_dir = Path.cwd() / STREAMING_OUTPUT_DIR
        if output_dir.exists():
            for pattern in ["conv-*.json", "item-*.json", "long-*.json", "short-*.json"]:
                for f in output_dir.glob(pattern):
                    f.unlink()

    def tearDown(self):
        self.setUp()

    @patch("obsidian_etl.pipelines.transform.nodes.logger")
    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_warns_long_summary(self, mock_llm_extract, mock_logger):
        """summary が 500 文字を超える場合、警告ログが出力されること。

        FR-009: システムは 500 文字を超える summary に対して警告ログを出力しなければならない

        When LLM returns summary > 500 chars:
        - Warning should be logged with "Long summary" message
        - Item should still be included in output (not excluded)
        """
        # Generate a summary that exceeds 500 characters
        long_summary = "あ" * 501  # 501 chars (exceeds 500)

        mock_llm_extract.return_value = (
            {
                "title": "長いサマリーのテスト",
                "summary": long_summary,
                "summary_content": "有効な本文内容。",
                "tags": ["テスト"],
            },
            None,
        )

        parsed_item = _make_parsed_item(item_id="long-summary", file_id="long12345678")
        partitioned_input = _make_partitioned_input({"long-summary": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Item should still be included in output (not excluded)
        self.assertEqual(len(result), 1)
        self.assertIn("long-summary", result)

        # Warning should be logged with "Long summary" message
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        warning_messages = " ".join(warning_calls)
        self.assertIn("Long summary", warning_messages)
        self.assertIn("501", warning_messages)  # Character count
        self.assertIn("long-summary", warning_messages)  # Partition ID

    @patch("obsidian_etl.pipelines.transform.nodes.logger")
    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_no_warning_for_short_summary(self, mock_llm_extract, mock_logger):
        """summary が 500 文字以下の場合、警告ログが出力されないこと。

        When LLM returns summary <= 500 chars:
        - No warning should be logged for summary length
        - Item should be included in output
        """
        # Generate a summary that is exactly 500 characters (boundary case)
        short_summary = "あ" * 500  # Exactly 500 chars (not exceeding)

        mock_llm_extract.return_value = (
            {
                "title": "短いサマリーのテスト",
                "summary": short_summary,
                "summary_content": "有効な本文内容。",
                "tags": ["テスト"],
            },
            None,
        )

        parsed_item = _make_parsed_item(item_id="short-summary", file_id="short1234567")
        partitioned_input = _make_partitioned_input({"short-summary": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Item should be included in output
        self.assertEqual(len(result), 1)
        self.assertIn("short-summary", result)

        # No "Long summary" warning should be logged
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        warning_messages = " ".join(warning_calls)
        self.assertNotIn("Long summary", warning_messages)


# ============================================================
# Phase 5 RED Tests: Integration - extract_knowledge and translate_summary
# use get_ollama_config for parameter retrieval
# ============================================================


class TestExtractKnowledgeUsesOllamaConfig(unittest.TestCase):
    """extract_knowledge: Uses get_ollama_config for parameter retrieval.

    Tests for Phase 5 - Integration
    Verify that knowledge_extractor.extract_knowledge uses get_ollama_config
    to retrieve Ollama parameters instead of direct params.get("ollama", {}).
    """

    def setUp(self):
        """Clean up streaming output files before each test."""
        from obsidian_etl.pipelines.transform.nodes import STREAMING_OUTPUT_DIR

        output_dir = Path.cwd() / STREAMING_OUTPUT_DIR
        if output_dir.exists():
            for pattern in ["conv-*.json", "item-*.json", "config-*.json"]:
                for f in output_dir.glob(pattern):
                    f.unlink()

    def tearDown(self):
        self.setUp()

    @patch("obsidian_etl.utils.knowledge_extractor.get_ollama_config")
    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_extract_knowledge_uses_config(self, mock_call_ollama, mock_get_config):
        """extract_knowledge が get_ollama_config を使用してパラメーターを取得すること。

        Phase 5 - Integration:
        Verify that knowledge_extractor.extract_knowledge calls
        get_ollama_config(params, "extract_knowledge") to retrieve config.

        When extract_knowledge is called:
        - get_ollama_config should be called with params and "extract_knowledge"
        - The returned OllamaConfig should be used for call_ollama
        """
        from obsidian_etl.utils.knowledge_extractor import extract_knowledge
        from obsidian_etl.utils.ollama_config import OllamaConfig

        # Setup mock config
        mock_config = OllamaConfig(
            model="gemma3:12b",
            base_url="http://localhost:11434",
            timeout=300,
            temperature=0.2,
            num_predict=16384,
        )
        mock_get_config.return_value = mock_config

        # Setup mock call_ollama response
        mock_call_ollama.return_value = (
            "```yaml\ntitle: Test\nsummary: Test summary\n```\nTest content",
            None,
        )

        # Prepare params with function-specific config
        params = {
            "ollama": {
                "defaults": {
                    "model": "gemma3:12b",
                    "base_url": "http://localhost:11434",
                    "timeout": 120,
                    "temperature": 0.2,
                    "num_predict": -1,
                },
                "functions": {
                    "extract_knowledge": {
                        "num_predict": 16384,
                        "timeout": 300,
                    },
                },
            }
        }

        # Call extract_knowledge
        result, error = extract_knowledge(
            content="Human: Test\n\nAssistant: Response",
            conversation_name="Test conversation",
            created_at="2026-01-15T10:00:00",
            source_provider="claude",
            params=params,
        )

        # Verify get_ollama_config was called with correct arguments
        mock_get_config.assert_called_once_with(params, "extract_knowledge")

    @patch("obsidian_etl.utils.knowledge_extractor.get_ollama_config")
    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_extract_knowledge_num_predict_applied(self, mock_call_ollama, mock_get_config):
        """extract_knowledge が num_predict=16384 を Ollama API に渡すこと。

        Phase 5 - Integration:
        Verify that extract_knowledge passes the configured num_predict value
        (16384 for extract_knowledge) to call_ollama.

        From contracts/parameters.yml:
        - extract_knowledge.num_predict: 16384
        - This should be passed to call_ollama as num_predict parameter
        """
        from obsidian_etl.utils.knowledge_extractor import extract_knowledge
        from obsidian_etl.utils.ollama_config import OllamaConfig

        # Setup mock config with num_predict=16384
        mock_config = OllamaConfig(
            model="gemma3:12b",
            base_url="http://localhost:11434",
            timeout=300,
            temperature=0.2,
            num_predict=16384,
        )
        mock_get_config.return_value = mock_config

        # Setup mock call_ollama response
        mock_call_ollama.return_value = (
            "# Test\n\n## 要約\nTest summary\n\n## タグ\ntest\n\n## 内容\nTest content"
        )

        params = {
            "ollama": {
                "defaults": {"model": "gemma3:12b"},
                "functions": {
                    "extract_knowledge": {"num_predict": 16384, "timeout": 300},
                },
            }
        }

        # Call extract_knowledge
        result, error = extract_knowledge(
            content="Human: Test\n\nAssistant: Response",
            conversation_name="Test conversation",
            created_at="2026-01-15T10:00:00",
            source_provider="claude",
            params=params,
        )

        # Verify call_ollama was called with OllamaConfig containing correct values
        mock_call_ollama.assert_called_once()
        config = mock_call_ollama.call_args[0][2]

        self.assertEqual(config.num_predict, 16384)
        self.assertEqual(config.timeout, 300)
        self.assertEqual(config.model, "gemma3:12b")


class TestTranslateSummaryUsesOllamaConfig(unittest.TestCase):
    """translate_summary: Uses get_ollama_config for parameter retrieval.

    Tests for Phase 5 - Integration
    Verify that knowledge_extractor.translate_summary uses get_ollama_config
    to retrieve Ollama parameters instead of direct params.get("ollama", {}).
    """

    @patch("obsidian_etl.utils.knowledge_extractor.get_ollama_config")
    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_uses_config(self, mock_call_ollama, mock_get_config):
        """translate_summary が get_ollama_config を使用してパラメーターを取得すること。

        Phase 5 - Integration:
        Verify that knowledge_extractor.translate_summary calls
        get_ollama_config(params, "translate_summary") to retrieve config.

        When translate_summary is called:
        - get_ollama_config should be called with params and "translate_summary"
        - The returned OllamaConfig should be used for call_ollama
        """
        from obsidian_etl.utils.knowledge_extractor import translate_summary
        from obsidian_etl.utils.ollama_config import OllamaConfig

        # Setup mock config
        mock_config = OllamaConfig(
            model="gemma3:12b",
            base_url="http://localhost:11434",
            timeout=120,
            temperature=0.2,
            num_predict=1024,
        )
        mock_get_config.return_value = mock_config

        # Setup mock call_ollama response
        mock_call_ollama.return_value = "## 要約\nテスト要約"

        # Prepare params with function-specific config
        params = {
            "ollama": {
                "defaults": {
                    "model": "gemma3:12b",
                    "base_url": "http://localhost:11434",
                    "timeout": 120,
                    "temperature": 0.2,
                    "num_predict": -1,
                },
                "functions": {
                    "translate_summary": {
                        "num_predict": 1024,
                    },
                },
            }
        }

        # Call translate_summary
        result, error = translate_summary(
            summary="The user asked about Python asyncio.",
            params=params,
        )

        # Verify get_ollama_config was called with correct arguments
        mock_get_config.assert_called_once_with(params, "translate_summary")

    @patch("obsidian_etl.utils.knowledge_extractor.get_ollama_config")
    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_num_predict_applied(self, mock_call_ollama, mock_get_config):
        """translate_summary が num_predict=1024 を Ollama API に渡すこと。

        Phase 5 - Integration:
        Verify that translate_summary passes the configured num_predict value
        (1024 for translate_summary) to call_ollama via OllamaConfig.
        """
        from obsidian_etl.utils.knowledge_extractor import translate_summary
        from obsidian_etl.utils.ollama_config import OllamaConfig

        # Setup mock config with num_predict=1024
        mock_config = OllamaConfig(
            model="gemma3:12b",
            base_url="http://localhost:11434",
            timeout=120,
            temperature=0.2,
            num_predict=1024,
        )
        mock_get_config.return_value = mock_config

        # Setup mock call_ollama response
        mock_call_ollama.return_value = "## 要約\nテスト要約"

        params = {
            "ollama": {
                "defaults": {"model": "gemma3:12b"},
                "functions": {
                    "translate_summary": {"num_predict": 1024},
                },
            }
        }

        # Call translate_summary
        result, error = translate_summary(
            summary="The user asked about Python asyncio.",
            params=params,
        )

        # Verify call_ollama was called with OllamaConfig containing correct values
        mock_call_ollama.assert_called_once()
        config = mock_call_ollama.call_args[0][2]

        self.assertEqual(config.num_predict, 1024)
        self.assertEqual(config.model, "gemma3:12b")
        self.assertEqual(config.timeout, 120)


# ============================================================
# Phase 2 RED Tests: Prompt Quality Improvements (052-improve-summary-quality)
# ============================================================


class TestPromptQualityInstructions(unittest.TestCase):
    """Prompt quality tests for User Story 1 - まとめ品質の向上.

    Tests for FR-001, FR-003, FR-004, FR-005:
    - FR-001: Prompt includes "理由や背景も含めて説明する" instruction
    - FR-003: Prompt includes table preservation instruction
    - FR-004: Prompt includes specific values preservation (数値・日付・固有名詞)
    - FR-005: Prompt includes analysis/recommendation structuring instruction
    """

    def setUp(self):
        """Load the prompt file content."""
        prompt_path = (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "obsidian_etl"
            / "utils"
            / "prompts"
            / "knowledge_extraction.txt"
        )
        with open(prompt_path, encoding="utf-8") as f:
            self.prompt_content = f.read()

    def test_prompt_includes_reason_instruction(self):
        """プロンプトに「理由・背景」の説明指示が含まれること。

        FR-001: システムは、まとめ生成時に「理由や背景も含めて説明する」指示をプロンプトに含めなければならない

        Expected keywords in prompt:
        - 理由・背景 or 理由や背景
        - なぜそうなるか
        """
        # Check for reason/background instruction
        reason_keywords = ["理由・背景", "理由や背景", "なぜそうなるか"]
        has_reason_instruction = any(keyword in self.prompt_content for keyword in reason_keywords)

        self.assertTrue(
            has_reason_instruction,
            f"Prompt should include reason/background instruction. "
            f"Expected one of: {reason_keywords}. "
            f"Prompt content length: {len(self.prompt_content)} chars",
        )

    def test_prompt_includes_table_preservation(self):
        """プロンプトに表形式データの保持指示が含まれること。

        FR-003: システムは、表形式のデータがある場合、表形式を保持してまとめに含めなければならない

        Expected keywords in prompt:
        - 表形式データの保持 or 表形式を保持
        - Markdown 表形式
        """
        # Check for table preservation instruction
        table_keywords = ["表形式データの保持", "表形式を保持", "Markdown 表形式で保持"]
        has_table_instruction = any(keyword in self.prompt_content for keyword in table_keywords)

        self.assertTrue(
            has_table_instruction,
            f"Prompt should include table preservation instruction. "
            f"Expected one of: {table_keywords}. "
            f"Prompt content length: {len(self.prompt_content)} chars",
        )

    def test_prompt_includes_code_preservation(self):
        """プロンプトにコードブロック保持の強化指示が含まれること。

        Edge Case: コード主体の会話では、コードブロックを適切に保持しつつ解説を追加する

        Expected: Prompt should have explicit code block preservation instruction
        beyond the existing "省略禁止" section. Should include:
        - コードブロック保持 or コードブロックを完全に保持
        - 重要なコードは省略せず
        """
        # The prompt already has some code instructions, but we need explicit
        # preservation emphasis for code-heavy conversations
        code_preservation_keywords = [
            "コードブロック保持",
            "コードブロックを完全に保持",
            "重要なコードは省略せず",
            "コード主体",
        ]
        has_code_preservation = any(
            keyword in self.prompt_content for keyword in code_preservation_keywords
        )

        self.assertTrue(
            has_code_preservation,
            f"Prompt should include explicit code block preservation instruction. "
            f"Expected one of: {code_preservation_keywords}. "
            f"Prompt content length: {len(self.prompt_content)} chars",
        )

    def test_prompt_includes_analysis_structuring(self):
        """プロンプトに分析・推奨の構造化指示が含まれること。

        FR-005: システムは、元の会話に分析や推奨がある場合、それらを構造化してまとめに含めなければならない

        Expected keywords in prompt:
        - 分析・考察の記述 or 分析・推奨
        - パターン・傾向
        - 推奨・アドバイス
        """
        # Check for analysis/recommendation structuring instruction
        analysis_keywords = [
            "分析・考察の記述",
            "分析・推奨",
            "パターン・傾向",
            "推奨・アドバイス",
        ]
        has_analysis_instruction = any(
            keyword in self.prompt_content for keyword in analysis_keywords
        )

        self.assertTrue(
            has_analysis_instruction,
            f"Prompt should include analysis/recommendation structuring instruction. "
            f"Expected one of: {analysis_keywords}. "
            f"Prompt content length: {len(self.prompt_content)} chars",
        )

    def test_prompt_includes_specific_values_preservation(self):
        """プロンプトに数値・日付・固有名詞の省略禁止指示が含まれること。

        FR-004: システムは、具体的な数値・日付・固有名詞を省略せずにまとめに含めなければならない

        Expected keywords in prompt:
        - 数値・日付は省略せず or 数値・日付・固有名詞
        """
        # Check for specific values preservation instruction
        values_keywords = ["数値・日付は省略せず", "数値・日付・固有名詞", "具体的な数値"]
        has_values_instruction = any(keyword in self.prompt_content for keyword in values_keywords)

        self.assertTrue(
            has_values_instruction,
            f"Prompt should include specific values preservation instruction. "
            f"Expected one of: {values_keywords}. "
            f"Prompt content length: {len(self.prompt_content)} chars",
        )


if __name__ == "__main__":
    unittest.main()
