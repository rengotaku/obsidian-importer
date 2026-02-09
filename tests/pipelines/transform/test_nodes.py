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
            "model": "gemma3:12b",
            "base_url": "http://localhost:11434",
            "timeout": 120,
            "temperature": 0.2,
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
        """LLM 呼び出しが失敗した場合、そのアイテムは出力から除外されること。"""
        mock_llm_extract.return_value = (None, "Connection error: refused")

        parsed_item = _make_parsed_item()
        partitioned_input = _make_partitioned_input({"conv-fail": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        # Failed item should be excluded from output
        self.assertEqual(len(result), 0)

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_partial_failure(self, mock_llm_extract):
        """複数アイテムのうち一部が失敗した場合、成功分のみ出力されること。"""
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

        # Only the successful item should be in the result
        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        self.assertEqual(item["generated_metadata"]["title"], "成功アイテム")

    @patch("obsidian_etl.pipelines.transform.nodes.knowledge_extractor.extract_knowledge")
    def test_extract_knowledge_empty_response(self, mock_llm_extract):
        """LLM が空レスポンスを返した場合、アイテムが除外されること。"""
        mock_llm_extract.return_value = ({}, "Empty response")

        parsed_item = _make_parsed_item()
        partitioned_input = _make_partitioned_input({"conv-empty": parsed_item})
        params = _make_params()

        result = extract_knowledge(partitioned_input, params)

        self.assertEqual(len(result), 0)


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

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)

        # Output key should be sanitized filename
        output_key = list(result.keys())[0]
        markdown = result[output_key]

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

        result = format_markdown(partitioned_input)

        markdown = list(result.values())[0]

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

        result = format_markdown(partitioned_input)

        markdown = list(result.values())[0]

        # Body should contain summary text
        self.assertIn("asyncio", markdown)

    def test_format_markdown_tags_list(self):
        """tags がリスト形式で frontmatter に出力されること。"""
        metadata_item = self._make_metadata_item()
        partitioned_input = _make_partitioned_input({"item-tags": metadata_item})

        result = format_markdown(partitioned_input)

        markdown = list(result.values())[0]

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

        result = format_markdown(partitioned_input)

        output_key = list(result.keys())[0]
        # Output key should contain the title (extension added by PartitionedDataset)
        self.assertIn("Python asyncio", output_key)

    def test_format_markdown_output_filename_special_chars(self):
        """特殊文字を含むタイトルがサニタイズされること。"""
        item = self._make_metadata_item_with_title("C++ vs C#: パフォーマンス比較 (2026/01)")
        partitioned_input = _make_partitioned_input({"item-special": item})

        result = format_markdown(partitioned_input)

        output_key = list(result.keys())[0]

        # Filename should not contain filesystem-unsafe characters
        unsafe_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        for char in unsafe_chars:
            self.assertNotIn(char, output_key, f"Filename contains unsafe char: {char}")

    def test_format_markdown_output_filename_unicode(self):
        """Unicode タイトル（日本語）が正しくファイル名になること。"""
        item = self._make_metadata_item_with_title("データベース正規化の基礎")
        partitioned_input = _make_partitioned_input({"item-unicode": item})

        result = format_markdown(partitioned_input)

        output_key = list(result.keys())[0]

        # Should contain the Japanese title
        self.assertIn("データベース正規化", output_key)

    def test_format_markdown_output_filename_long_title(self):
        """非常に長いタイトルが適切に切り詰められること。"""
        long_title = "A" * 300
        item = self._make_metadata_item_with_title(long_title)
        partitioned_input = _make_partitioned_input({"item-long": item})

        result = format_markdown(partitioned_input)

        output_key = list(result.keys())[0]

        # Filename should be reasonably short (< 255 chars for filesystem)
        self.assertLess(len(output_key), 256)

    def test_format_markdown_output_filename_empty_title(self):
        """空タイトルの場合、フォールバックのファイル名が生成されること。"""
        item = self._make_metadata_item_with_title("")
        partitioned_input = _make_partitioned_input({"item-empty": item})

        result = format_markdown(partitioned_input)

        output_key = list(result.keys())[0]

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


if __name__ == "__main__":
    unittest.main()
