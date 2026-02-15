"""E2E integration tests for import pipelines.

Phase 5 RED tests: SequentialRunner with test DataCatalog.
Phase 4 RED tests: OpenAI pipeline E2E with ZIP input.

These tests verify:
- Full pipeline execution: raw_claude_conversations -> organized_items
- All intermediate datasets are produced
- Ollama is mocked (no real LLM calls)
- [Phase 4] OpenAI pipeline E2E with ZIP input fixtures
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from kedro.io import AbstractDataset, DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner

from obsidian_etl.pipeline_registry import register_pipelines


class PartitionedMemoryDataset(AbstractDataset):
    """Memory dataset that mimics PartitionedDataset behavior.

    When saving dict[str, dict], it MERGES with existing data (accumulates across runs).
    When loading, it returns dict[str, Callable] where each callable returns the item.
    This mimics PartitionedDataset with overwrite=false.
    """

    def __init__(self):
        self._data = {}

    def _save(self, data: dict[str, dict]) -> None:
        """Save dictionary data, merging with existing data (accumulate)."""
        if self._data is None:
            self._data = {}
        # Merge new data with existing data (mimics overwrite=false)
        self._data.update(data)

    def _load(self) -> dict[str, callable]:
        """Load data as dict of callables (PartitionedDataset pattern)."""
        if self._data is None or len(self._data) == 0:
            return {}
        # Wrap each item in a callable
        return {key: (lambda v=val: v) for key, val in self._data.items()}

    def _describe(self) -> dict:
        return {"type": "PartitionedMemoryDataset"}


class ZipMemoryDataset(AbstractDataset):
    """Memory dataset that provides ZIP bytes in PartitionedDataset format.

    Used for integration tests to provide Claude ZIP input.
    """

    def __init__(self, conversations: list[dict]):
        """Initialize with a list of conversations.

        Args:
            conversations: List of Claude conversation dicts.
        """
        self._zip_bytes = _make_claude_zip_bytes(conversations)

    def _save(self, data) -> None:
        """Not used in tests."""
        pass

    def _load(self) -> dict[str, callable]:
        """Return dict[str, Callable] that returns ZIP bytes.

        This mimics PartitionedDataset with BinaryDataset.
        """
        return {"test_export.zip": lambda: self._zip_bytes}

    def _describe(self) -> dict:
        return {"type": "ZipMemoryDataset"}


def _make_claude_conversation(
    uuid: str = "conv-001-uuid",
    name: str = "Python asyncio 解説",
    messages_count: int = 4,
) -> dict:
    """Create a minimal Claude conversation for testing."""
    messages = []
    for i in range(messages_count):
        role = "human" if i % 2 == 0 else "assistant"
        messages.append(
            {
                "uuid": f"msg-{i:03d}",
                "sender": role,
                "text": f"Message {i} about Python asyncio and frameworks." * 5,
                "created_at": f"2026-01-15T10:{i:02d}:00.000000+00:00",
            }
        )
    return {
        "uuid": uuid,
        "name": name,
        "created_at": "2026-01-15T10:00:00.000000+00:00",
        "updated_at": "2026-01-15T10:30:00.000000+00:00",
        "chat_messages": messages,
    }


def _make_mock_ollama_response(title: str = "Python asyncio の仕組み") -> dict:
    """Create a mock Ollama LLM response for knowledge extraction.

    The summary_content must be large enough to pass compression ratio check.
    For content <5000 chars, threshold is 20%. Input is ~800 chars per conversation,
    so we need at least 160 chars of body content.
    """
    # Make body content large enough to pass 20% threshold
    body_content = """## asyncio の概要

asyncio は Python の非同期 I/O フレームワークです。イベントループを使用して、
並行処理を効率的に実行します。

### 主な特徴

- async/await 構文による直感的な非同期プログラミング
- イベントループによる効率的なタスク管理
- Future と Task による並行処理の制御
- コルーチンベースの設計パターン

### 使用例

```python
import asyncio

async def main():
    await asyncio.sleep(1)
    print("Hello, asyncio!")

asyncio.run(main())
```

この例では、非同期関数 main を定義し、asyncio.run で実行しています。"""

    return {
        "title": title,
        "summary": "Python asyncio ライブラリの非同期処理について",
        "summary_content": body_content,
        "tags": ["Python", "asyncio", "非同期処理"],
    }


def _make_claude_zip_bytes(conversations: list[dict]) -> bytes:
    """Create a ZIP file containing conversations.json from a list of conversations.

    Args:
        conversations: List of Claude conversation dicts.

    Returns:
        ZIP file bytes containing conversations.json.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        conversations_json = json.dumps(conversations)
        zf.writestr("conversations.json", conversations_json)
    return buf.getvalue()


class TestE2EClaudeImport(unittest.TestCase):
    """E2E test: SequentialRunner with Claude import pipeline (mocked Ollama)."""

    def setUp(self):
        """Set up test pipeline, catalog, and runner."""
        self.pipelines = register_pipelines()
        self.runner = SequentialRunner()
        self.tmp_dir = tempfile.mkdtemp()

        # Patch STREAMING_OUTPUT_DIR to use temp directory (avoid collision with real data)
        self.streaming_patcher = patch(
            "obsidian_etl.pipelines.transform.nodes.STREAMING_OUTPUT_DIR",
            Path(self.tmp_dir) / "streaming",
        )
        self.streaming_patcher.start()

        # Create test conversations (raw input)
        self.conversations = [
            _make_claude_conversation(uuid="conv-001", name="asyncio 解説"),
            _make_claude_conversation(uuid="conv-002", name="Django REST framework"),
        ]

    def tearDown(self):
        """Clean up patchers."""
        self.streaming_patcher.stop()

    def _build_catalog(self) -> DataCatalog:
        """Build a test DataCatalog with MemoryDatasets."""
        # Create shared instances for resume behavior (Phase 6)
        transformed_knowledge_ds = PartitionedMemoryDataset()
        classified_items_ds = PartitionedMemoryDataset()

        return DataCatalog(
            datasets={
                "raw_claude_conversations": ZipMemoryDataset(self.conversations),
                "parsed_items": PartitionedMemoryDataset(),
                "transformed_items_with_knowledge": transformed_knowledge_ds,
                "existing_transformed_items_with_knowledge": transformed_knowledge_ds,  # Resume support
                "transformed_items_with_metadata": PartitionedMemoryDataset(),
                "markdown_notes": PartitionedMemoryDataset(),
                "classified_items": classified_items_ds,
                "existing_classified_items": classified_items_ds,  # Resume support
                "topic_extracted_items": PartitionedMemoryDataset(),
                "normalized_items": PartitionedMemoryDataset(),
                "cleaned_items": PartitionedMemoryDataset(),
                "organized_notes": PartitionedMemoryDataset(),  # Phase 2: renamed from organized_items
                "organized_items": PartitionedMemoryDataset(),  # Legacy compatibility
                "review_notes": PartitionedMemoryDataset(),  # Review folder output (final)
                "params:import": MemoryDataset(
                    {
                        "provider": "claude",
                        "min_messages": 3,
                        "chunk_size": 25000,
                        "chunk_enabled": True,
                        "ollama": {
                            "model": "gemma3:12b",
                            "base_url": "http://localhost:11434",
                            "timeout": 120,
                            "temperature": 0.2,
                            "max_retries": 3,
                        },
                    }
                ),
                "params:organize": MemoryDataset(
                    {
                        "genre_keywords": {
                            "engineer": ["Python", "asyncio", "フレームワーク", "API"],
                            "business": ["ビジネス", "マネジメント"],
                            "economy": ["経済", "投資"],
                            "daily": ["日常", "趣味"],
                        },
                        "base_path": self.tmp_dir,
                    }
                ),
            }
        )

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_e2e_claude_import_produces_organized_notes(self, mock_extract):
        """raw_claude_conversations から organized_notes まで一気通貫で処理されること。"""
        mock_extract.return_value = (_make_mock_ollama_response(), None)

        pipeline = self.pipelines["import_claude"]
        catalog = self._build_catalog()

        self.runner.run(pipeline, catalog)

        # Verify organized_notes was produced (load returns dict of callables)
        organized_callables = catalog.load("organized_notes")
        self.assertIsInstance(organized_callables, dict)
        self.assertGreater(len(organized_callables), 0, "organized_notes should not be empty")

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_e2e_claude_import_all_conversations_processed(self, mock_extract):
        """全会話が最終出力に含まれること。"""
        # Return different titles for each conversation to avoid filename collision
        mock_extract.side_effect = [
            (_make_mock_ollama_response(title="asyncio 解説"), None),
            (_make_mock_ollama_response(title="Django REST framework"), None),
        ]

        pipeline = self.pipelines["import_claude"]
        catalog = self._build_catalog()

        self.runner.run(pipeline, catalog)

        organized_callables = catalog.load("organized_notes")
        # 2 conversations should produce 2 organized notes
        self.assertEqual(len(organized_callables), 2)

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_e2e_claude_import_intermediate_datasets(self, mock_extract):
        """中間データセット（parsed_items, markdown_notes）が生成されること。"""
        mock_extract.return_value = (_make_mock_ollama_response(), None)

        pipeline = self.pipelines["import_claude"]
        catalog = self._build_catalog()

        self.runner.run(pipeline, catalog)

        # Check intermediate datasets were populated (returns dict of callables)
        parsed_callables = catalog.load("parsed_items")
        self.assertIsInstance(parsed_callables, dict)
        self.assertGreater(len(parsed_callables), 0, "parsed_items should not be empty")

        markdown_callables = catalog.load("markdown_notes")
        self.assertIsInstance(markdown_callables, dict)
        self.assertGreater(len(markdown_callables), 0, "markdown_notes should not be empty")

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_e2e_organized_note_has_required_frontmatter(self, mock_extract):
        """organized_notes の各ノートが必須 frontmatter フィールドを持つこと。"""
        mock_extract.return_value = (_make_mock_ollama_response(), None)

        pipeline = self.pipelines["import_claude"]
        catalog = self._build_catalog()

        self.runner.run(pipeline, catalog)

        organized_callables = catalog.load("organized_notes")
        # Unwrap callables to get actual Markdown content
        for partition_id, load_func in organized_callables.items():
            content = load_func()
            self.assertIsInstance(content, str, f"Content should be string in {partition_id}")
            # Verify frontmatter structure
            self.assertTrue(
                content.startswith("---\n"), f"Missing frontmatter start in {partition_id}"
            )
            # Extract frontmatter
            parts = content.split("---\n", 2)
            self.assertGreaterEqual(len(parts), 3, f"Invalid frontmatter format in {partition_id}")
            frontmatter = parts[1]
            # Check required fields exist in frontmatter
            self.assertIn("genre:", frontmatter, f"Missing genre in {partition_id}")
            self.assertIn("topic:", frontmatter, f"Missing topic in {partition_id}")

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_e2e_ollama_mock_called(self, mock_extract):
        """Ollama LLM が各アイテムに対して呼び出されること。"""
        mock_extract.return_value = (_make_mock_ollama_response(), None)

        pipeline = self.pipelines["import_claude"]
        catalog = self._build_catalog()

        self.runner.run(pipeline, catalog)

        # LLM should be called for each parsed item
        self.assertGreaterEqual(mock_extract.call_count, 2)


class TestResumeAfterFailure(unittest.TestCase):
    """E2E test: first run with partial failure, second run processes only failed items."""

    def setUp(self):
        """Set up test pipeline, catalog, and runner."""
        self.pipelines = register_pipelines()
        self.runner = SequentialRunner()
        self.tmp_dir = tempfile.mkdtemp()

        # Patch STREAMING_OUTPUT_DIR to use temp directory
        self.streaming_patcher = patch(
            "obsidian_etl.pipelines.transform.nodes.STREAMING_OUTPUT_DIR",
            Path(self.tmp_dir) / "streaming",
        )
        self.streaming_patcher.start()

        # Create 3 conversations
        self.conversations = [
            _make_claude_conversation(uuid="conv-resume-001", name="asyncio 解説"),
            _make_claude_conversation(uuid="conv-resume-002", name="Django REST"),
            _make_claude_conversation(uuid="conv-resume-003", name="Flask チュートリアル"),
        ]

    def tearDown(self):
        """Clean up patchers."""
        self.streaming_patcher.stop()

    def _build_catalog(self) -> DataCatalog:
        """Build a test DataCatalog with PartitionedMemoryDatasets."""
        # Create shared instances for resume behavior
        parsed_items_ds = PartitionedMemoryDataset()
        transformed_knowledge_ds = PartitionedMemoryDataset()
        classified_items_ds = PartitionedMemoryDataset()

        return DataCatalog(
            datasets={
                "raw_claude_conversations": ZipMemoryDataset(self.conversations),
                "parsed_items": parsed_items_ds,
                "existing_parsed_items": parsed_items_ds,  # Same instance for resume
                "transformed_items_with_knowledge": transformed_knowledge_ds,
                "existing_transformed_items_with_knowledge": transformed_knowledge_ds,  # Same instance
                "transformed_items_with_metadata": PartitionedMemoryDataset(),
                "markdown_notes": PartitionedMemoryDataset(),
                "classified_items": classified_items_ds,
                "existing_classified_items": classified_items_ds,  # Same instance
                "normalized_items": PartitionedMemoryDataset(),
                "cleaned_items": PartitionedMemoryDataset(),
                "vault_determined_items": PartitionedMemoryDataset(),
                "organized_items": PartitionedMemoryDataset(),
                "organized_notes": PartitionedMemoryDataset(),
                "review_notes": PartitionedMemoryDataset(),  # Review folder output (final)
                "topic_extracted_items": PartitionedMemoryDataset(),
                "params:import": MemoryDataset(
                    {
                        "provider": "claude",
                        "min_messages": 3,
                        "chunk_size": 25000,
                        "chunk_enabled": True,
                        "ollama": {
                            "model": "gemma3:12b",
                            "base_url": "http://localhost:11434",
                            "timeout": 120,
                            "temperature": 0.2,
                            "max_retries": 3,
                        },
                    }
                ),
                "params:organize": MemoryDataset(
                    {
                        "genre_keywords": {
                            "engineer": ["Python", "asyncio", "フレームワーク", "API"],
                            "business": ["ビジネス", "マネジメント"],
                            "economy": ["経済", "投資"],
                            "daily": ["日常", "趣味"],
                        },
                        "base_path": self.tmp_dir,
                    }
                ),
            }
        )

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_resume_after_failure(self, mock_extract):
        """1回目で一部失敗、2回目は全てスキップ（失敗分はreviewに出力済み）。"""
        call_count = [0]

        def first_run_side_effect(*args, **kwargs):
            """First run: 2 succeed, 1 fails."""
            call_count[0] += 1
            if call_count[0] == 2:
                # Second item fails
                return (None, "LLM timeout error")
            title = f"成功アイテム {call_count[0]}"
            return (_make_mock_ollama_response(title=title), None)

        mock_extract.side_effect = first_run_side_effect

        pipeline = self.pipelines["import_claude"]
        catalog = self._build_catalog()

        # First run: 3 items parsed, 1 fails at extract_knowledge
        self.runner.run(pipeline, catalog)

        # After first run: 2 items succeed through to organized_notes
        first_run_organized = catalog.load("organized_notes")
        self.assertEqual(len(first_run_organized), 2, "First run should produce 2 organized notes")

        # Failed item goes to review_notes
        first_run_review = catalog.load("review_notes")
        self.assertEqual(len(first_run_review), 1, "First run should produce 1 review note")

        first_run_llm_calls = mock_extract.call_count
        self.assertEqual(first_run_llm_calls, 3, "First run should call LLM 3 times")

        # Reset mock for second run
        mock_extract.reset_mock()
        mock_extract.return_value = (
            _make_mock_ollama_response(title="リカバリアイテム"),
            None,
        )

        # Second run with same catalog (existing outputs are preserved)
        # All items are already processed (2 success + 1 review), so no LLM calls
        self.runner.run(pipeline, catalog)

        # LLM should NOT be called - all items already processed
        self.assertEqual(
            mock_extract.call_count,
            0,
            "Second run should not call LLM - all items already processed (including review)",
        )

        # After second run: counts remain the same
        second_run_organized = catalog.load("organized_notes")
        self.assertEqual(
            len(second_run_organized),
            2,
            "Second run should still have 2 organized notes",
        )
        second_run_review = catalog.load("review_notes")
        self.assertEqual(
            len(second_run_review),
            1,
            "Second run should still have 1 review note",
        )


class TestPipelineNodeNames(unittest.TestCase):
    """US5: 全パイプラインのノード名が期待通りに登録されていることを検証する。"""

    def setUp(self):
        """Set up pipelines from registry."""
        self.pipelines = register_pipelines()

    def test_import_claude_node_names(self):
        """import_claude パイプラインのノード名が正しいこと。"""
        pipeline = self.pipelines["import_claude"]
        node_names = {n.name for n in pipeline.nodes}
        expected_names = {
            # Extract
            "parse_claude_zip",
            # Transform
            "extract_knowledge",
            "generate_metadata",
            "format_markdown",
            # Organize
            "classify_genre",
            "extract_topic",
            "normalize_frontmatter",
            "clean_content",
            "embed_frontmatter_fields",
        }
        self.assertEqual(
            node_names,
            expected_names,
            f"import_claude node names mismatch.\n"
            f"Expected: {sorted(expected_names)}\n"
            f"Actual:   {sorted(node_names)}",
        )

    def test_import_openai_node_names(self):
        """import_openai パイプラインのノード名が正しいこと。"""
        pipeline = self.pipelines["import_openai"]
        node_names = {n.name for n in pipeline.nodes}
        expected_names = {
            # Extract
            "parse_chatgpt_zip",
            # Transform
            "extract_knowledge",
            "generate_metadata",
            "format_markdown",
            # Organize
            "classify_genre",
            "extract_topic",
            "normalize_frontmatter",
            "clean_content",
            "embed_frontmatter_fields",
        }
        self.assertEqual(
            node_names,
            expected_names,
            f"import_openai node names mismatch.\n"
            f"Expected: {sorted(expected_names)}\n"
            f"Actual:   {sorted(node_names)}",
        )

    def test_import_github_node_names(self):
        """import_github パイプラインのノード名が正しいこと。"""
        pipeline = self.pipelines["import_github"]
        node_names = {n.name for n in pipeline.nodes}
        expected_names = {
            # Extract
            "clone_github_repo",
            "parse_jekyll",
            "convert_frontmatter",
            # Transform
            "extract_knowledge",
            "generate_metadata",
            "format_markdown",
            # Organize
            "classify_genre",
            "extract_topic",
            "normalize_frontmatter",
            "clean_content",
            "embed_frontmatter_fields",
        }
        self.assertEqual(
            node_names,
            expected_names,
            f"import_github node names mismatch.\n"
            f"Expected: {sorted(expected_names)}\n"
            f"Actual:   {sorted(node_names)}",
        )

    def test_all_node_names_are_unique_within_pipeline(self):
        """各パイプライン内でノード名が重複しないこと。"""
        for pipeline_name in ["import_claude", "import_openai", "import_github"]:
            pipeline = self.pipelines[pipeline_name]
            node_names = [n.name for n in pipeline.nodes]
            self.assertEqual(
                len(node_names),
                len(set(node_names)),
                f"Duplicate node names found in {pipeline_name}: {node_names}",
            )


class TestPartialRunFromTo(unittest.TestCase):
    """US5: from_nodes / to_nodes でノード範囲を指定して部分実行できることを検証する。"""

    def setUp(self):
        """Set up test pipeline, catalog, and runner."""
        self.pipelines = register_pipelines()
        self.runner = SequentialRunner()
        self.tmp_dir = tempfile.mkdtemp()

        # Patch STREAMING_OUTPUT_DIR to use temp directory
        self.streaming_patcher = patch(
            "obsidian_etl.pipelines.transform.nodes.STREAMING_OUTPUT_DIR",
            Path(self.tmp_dir) / "streaming",
        )
        self.streaming_patcher.start()

    def tearDown(self):
        """Clean up patchers."""
        self.streaming_patcher.stop()

    def _build_catalog_with_intermediate_data(self) -> DataCatalog:
        """Build a test DataCatalog pre-populated with parsed_items (Extract output).

        This simulates running only Transform+Organize by providing
        pre-existing Extract output.
        """
        # Pre-populate parsed_items as if Extract already ran
        parsed_items_ds = PartitionedMemoryDataset()
        parsed_items_ds._save(
            {
                "conv-partial-001": {
                    "item_id": "conv-partial-001",
                    "file_id": "abc123def456",
                    "title": "Python asyncio 解説",
                    "content": "## asyncio\n\nasyncio は Python の非同期処理フレームワーク。\n\n### 使い方\n\nawait を使って非同期関数を呼び出す。",
                    "messages": [
                        {"role": "human", "content": "asyncio について教えて"},
                        {"role": "assistant", "content": "asyncio は非同期処理のライブラリです"},
                        {"role": "human", "content": "もっと詳しく"},
                        {"role": "assistant", "content": "await キーワードを使います"},
                    ],
                    "created_at": "2026-01-15T10:00:00.000000+00:00",
                    "source_provider": "claude",
                    "is_chunked": False,
                    "chunk_index": None,
                    "total_chunks": None,
                    "parent_item_id": None,
                },
            }
        )

        transformed_knowledge_ds = PartitionedMemoryDataset()
        classified_items_ds = PartitionedMemoryDataset()

        return DataCatalog(
            datasets={
                "raw_claude_conversations": MemoryDataset([]),
                "parsed_items": parsed_items_ds,
                "transformed_items_with_knowledge": transformed_knowledge_ds,
                "existing_transformed_items_with_knowledge": transformed_knowledge_ds,
                "transformed_items_with_metadata": PartitionedMemoryDataset(),
                "markdown_notes": PartitionedMemoryDataset(),
                "classified_items": classified_items_ds,
                "existing_classified_items": classified_items_ds,
                "topic_extracted_items": PartitionedMemoryDataset(),
                "normalized_items": PartitionedMemoryDataset(),
                "cleaned_items": PartitionedMemoryDataset(),
                "organized_notes": PartitionedMemoryDataset(),
                "review_notes": PartitionedMemoryDataset(),  # Review folder output (final)
                "params:import": MemoryDataset(
                    {
                        "provider": "claude",
                        "min_messages": 3,
                        "chunk_size": 25000,
                        "chunk_enabled": True,
                        "ollama": {
                            "model": "gemma3:12b",
                            "base_url": "http://localhost:11434",
                            "timeout": 120,
                            "temperature": 0.2,
                            "max_retries": 3,
                        },
                    }
                ),
                "params:organize": MemoryDataset(
                    {
                        "genre_keywords": {
                            "engineer": ["Python", "asyncio", "フレームワーク", "API"],
                            "business": ["ビジネス", "マネジメント"],
                            "economy": ["経済", "投資"],
                            "daily": ["日常", "趣味"],
                        },
                        "base_path": self.tmp_dir,
                    }
                ),
            }
        )

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_partial_run_transform_only(self, mock_extract):
        """from_nodes=extract_knowledge, to_nodes=format_markdown で Transform のみ実行されること。"""
        mock_extract.return_value = (_make_mock_ollama_response(), None)

        full_pipeline = self.pipelines["import_claude"]

        # Use Pipeline.from_nodes() and .to_nodes() for partial execution
        partial_pipeline = full_pipeline.from_nodes("extract_knowledge").to_nodes("format_markdown")

        catalog = self._build_catalog_with_intermediate_data()

        self.runner.run(partial_pipeline, catalog)

        # Transform should have produced markdown_notes
        markdown_callables = catalog.load("markdown_notes")
        self.assertIsInstance(markdown_callables, dict)
        self.assertGreater(
            len(markdown_callables), 0, "markdown_notes should be produced by partial run"
        )

        # Organize should NOT have run (organized_notes should be empty)
        organized_callables = catalog.load("organized_notes")
        self.assertEqual(
            len(organized_callables),
            0,
            "organized_notes should be empty when running Transform only",
        )

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_partial_run_organize_only(self, mock_extract):
        """from_nodes=classify_genre で Organize のみ実行されること。"""
        mock_extract.return_value = (_make_mock_ollama_response(), None)

        full_pipeline = self.pipelines["import_claude"]

        # First run full pipeline to populate intermediate data
        catalog = self._build_catalog_with_intermediate_data()
        self.runner.run(full_pipeline, catalog)

        # Now run only Organize part
        organize_pipeline = full_pipeline.from_nodes("classify_genre")
        catalog2 = self._build_catalog_with_intermediate_data()

        # Pre-populate markdown_notes from previous run
        markdown_data = catalog.load("markdown_notes")
        # Convert callables back to data for saving
        markdown_ds = PartitionedMemoryDataset()
        for key, load_func in markdown_data.items():
            markdown_ds._save({key: load_func()})
        catalog2._datasets["markdown_notes"] = markdown_ds

        self.runner.run(organize_pipeline, catalog2)

        organized_callables = catalog2.load("organized_notes")
        self.assertIsInstance(organized_callables, dict)
        self.assertGreater(
            len(organized_callables),
            0,
            "organized_notes should be produced by Organize-only partial run",
        )

    def test_partial_run_invalid_node_raises_error(self):
        """存在しないノード名を指定した場合にエラーが発生すること。"""
        full_pipeline = self.pipelines["import_claude"]

        with self.assertRaises(ValueError):
            full_pipeline.from_nodes("nonexistent_node")

    def test_from_nodes_to_nodes_subset_node_count(self):
        """from_nodes/to_nodes で取得したパイプラインのノード数が元より少ないこと。"""
        full_pipeline = self.pipelines["import_claude"]
        full_node_count = len(full_pipeline.nodes)

        partial_pipeline = full_pipeline.from_nodes("extract_knowledge").to_nodes("format_markdown")
        partial_node_count = len(partial_pipeline.nodes)

        self.assertLess(
            partial_node_count,
            full_node_count,
            f"Partial pipeline ({partial_node_count} nodes) should have fewer nodes "
            f"than full pipeline ({full_node_count} nodes)",
        )
        # Transform has exactly 3 nodes
        self.assertEqual(
            partial_node_count,
            3,
            "Transform-only partial pipeline should have exactly 3 nodes",
        )


def _make_openai_conversation(
    conv_id: str = "conv-openai-001",
    title: str = "Python asyncio 解説",
    messages_count: int = 4,
) -> dict:
    """Create a minimal OpenAI/ChatGPT conversation for testing.

    ChatGPT uses a mapping tree structure where each message is a node
    with parent references, forming a chain.
    """
    # Build mapping tree: root -> msg_0 -> msg_1 -> ... -> msg_N
    mapping = {}
    previous_node_id = None

    # Root node (no message)
    root_id = "root-node"
    mapping[root_id] = {
        "id": root_id,
        "parent": None,
        "children": [],
        "message": None,
    }
    previous_node_id = root_id

    current_node_id = None
    for i in range(messages_count):
        node_id = f"node-{i:03d}"
        role = "user" if i % 2 == 0 else "assistant"
        mapping[node_id] = {
            "id": node_id,
            "parent": previous_node_id,
            "children": [],
            "message": {
                "id": f"msg-{i:03d}",
                "author": {"role": role},
                "content": {
                    "content_type": "text",
                    "parts": [f"OpenAI message {i} about Python asyncio." * 3],
                },
                "create_time": 1706000000 + i * 60,
            },
        }
        mapping[previous_node_id]["children"].append(node_id)
        previous_node_id = node_id
        current_node_id = node_id

    return {
        "id": conv_id,
        "title": title,
        "create_time": 1706000000,
        "mapping": mapping,
        "current_node": current_node_id,
    }


def _make_openai_zip_bytes(conversations: list[dict]) -> bytes:
    """Create a ZIP file containing conversations.json from OpenAI conversations."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        conversations_json = json.dumps(conversations)
        zf.writestr("conversations.json", conversations_json)
    return buf.getvalue()


class OpenAIZipMemoryDataset(AbstractDataset):
    """Memory dataset that provides OpenAI ZIP bytes in PartitionedDataset format."""

    def __init__(self, conversations: list[dict]):
        self._zip_bytes = _make_openai_zip_bytes(conversations)

    def _save(self, data) -> None:
        pass

    def _load(self) -> dict[str, callable]:
        return {"chatgpt_export.zip": lambda: self._zip_bytes}

    def _describe(self) -> dict:
        return {"type": "OpenAIZipMemoryDataset"}


class TestE2EOpenAIImport(unittest.TestCase):
    """E2E test: SequentialRunner with OpenAI import pipeline (mocked Ollama).

    Phase 4: OpenAI パイプラインが ZIP 入力から E2E で動作することを検証する。
    """

    def setUp(self):
        """Set up test pipeline, catalog, and runner."""
        self.pipelines = register_pipelines()
        self.runner = SequentialRunner()
        self.tmp_dir = tempfile.mkdtemp()

        # Patch STREAMING_OUTPUT_DIR to use temp directory
        self.streaming_patcher = patch(
            "obsidian_etl.pipelines.transform.nodes.STREAMING_OUTPUT_DIR",
            Path(self.tmp_dir) / "streaming",
        )
        self.streaming_patcher.start()

        # Create test OpenAI conversations
        self.conversations = [
            _make_openai_conversation(conv_id="openai-conv-001", title="asyncio 解説"),
            _make_openai_conversation(conv_id="openai-conv-002", title="Django REST framework"),
        ]

    def tearDown(self):
        """Clean up patchers."""
        self.streaming_patcher.stop()

    def _build_catalog(self) -> DataCatalog:
        """Build a test DataCatalog with MemoryDatasets for OpenAI pipeline."""
        transformed_knowledge_ds = PartitionedMemoryDataset()
        classified_items_ds = PartitionedMemoryDataset()

        return DataCatalog(
            datasets={
                "raw_openai_conversations": OpenAIZipMemoryDataset(self.conversations),
                "parsed_items": PartitionedMemoryDataset(),
                "transformed_items_with_knowledge": transformed_knowledge_ds,
                "existing_transformed_items_with_knowledge": transformed_knowledge_ds,
                "transformed_items_with_metadata": PartitionedMemoryDataset(),
                "markdown_notes": PartitionedMemoryDataset(),
                "classified_items": classified_items_ds,
                "existing_classified_items": classified_items_ds,
                "topic_extracted_items": PartitionedMemoryDataset(),
                "normalized_items": PartitionedMemoryDataset(),
                "cleaned_items": PartitionedMemoryDataset(),
                "organized_notes": PartitionedMemoryDataset(),
                "review_notes": PartitionedMemoryDataset(),  # Review folder output (final)
                "params:import": MemoryDataset(
                    {
                        "provider": "openai",
                        "min_messages": 3,
                        "chunk_size": 25000,
                        "chunk_enabled": True,
                        "ollama": {
                            "model": "gemma3:12b",
                            "base_url": "http://localhost:11434",
                            "timeout": 120,
                            "temperature": 0.2,
                            "max_retries": 3,
                        },
                    }
                ),
                "params:organize": MemoryDataset(
                    {
                        "genre_keywords": {
                            "engineer": ["Python", "asyncio", "フレームワーク", "API"],
                            "business": ["ビジネス", "マネジメント"],
                            "economy": ["経済", "投資"],
                            "daily": ["日常", "趣味"],
                        },
                        "base_path": self.tmp_dir,
                    }
                ),
            }
        )

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_e2e_openai_import_produces_organized_notes(self, mock_extract):
        """OpenAI パイプラインが ZIP 入力から organized_notes まで一気通貫で処理されること。"""
        mock_extract.return_value = (_make_mock_ollama_response(), None)

        pipeline = self.pipelines["import_openai"]
        catalog = self._build_catalog()

        self.runner.run(pipeline, catalog)

        organized_callables = catalog.load("organized_notes")
        self.assertIsInstance(organized_callables, dict)
        self.assertGreater(len(organized_callables), 0, "organized_notes should not be empty")

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_e2e_openai_import_all_conversations_processed(self, mock_extract):
        """OpenAI の全会話が最終出力に含まれること。"""
        mock_extract.side_effect = [
            (_make_mock_ollama_response(title="asyncio 解説"), None),
            (_make_mock_ollama_response(title="Django REST framework"), None),
        ]

        pipeline = self.pipelines["import_openai"]
        catalog = self._build_catalog()

        self.runner.run(pipeline, catalog)

        organized_callables = catalog.load("organized_notes")
        self.assertEqual(
            len(organized_callables), 2, "2 conversations should produce 2 organized notes"
        )

    @patch("obsidian_etl.utils.knowledge_extractor.extract_knowledge")
    def test_e2e_openai_parsed_items_have_openai_provider(self, mock_extract):
        """OpenAI パースアイテムの source_provider が 'openai' であること。"""
        mock_extract.return_value = (_make_mock_ollama_response(), None)

        pipeline = self.pipelines["import_openai"]
        catalog = self._build_catalog()

        self.runner.run(pipeline, catalog)

        parsed_callables = catalog.load("parsed_items")
        for partition_id, load_func in parsed_callables.items():
            item = load_func()
            self.assertEqual(
                item["source_provider"],
                "openai",
                f"source_provider should be 'openai' for {partition_id}",
            )


if __name__ == "__main__":
    unittest.main()
