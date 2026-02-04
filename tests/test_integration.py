"""E2E integration tests for Claude import pipeline.

Phase 5 RED tests: SequentialRunner with test DataCatalog.
These tests verify:
- Full pipeline execution: raw_claude_conversations -> organized_items
- All intermediate datasets are produced
- Ollama is mocked (no real LLM calls)
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
    """Create a mock Ollama LLM response for knowledge extraction."""
    return {
        "title": title,
        "summary": "Python asyncio ライブラリの非同期処理について",
        "summary_content": "## asyncio の概要\n\nasyncio は Python の非同期 I/O フレームワークです。",
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

        # Create test conversations (raw input)
        self.conversations = [
            _make_claude_conversation(uuid="conv-001", name="asyncio 解説"),
            _make_claude_conversation(uuid="conv-002", name="Django REST framework"),
        ]

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
                "normalized_items": PartitionedMemoryDataset(),
                "cleaned_items": PartitionedMemoryDataset(),
                "vault_determined_items": PartitionedMemoryDataset(),
                "organized_items": PartitionedMemoryDataset(),
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
                        "vaults": {
                            "engineer": "Vaults/エンジニア/",
                            "business": "Vaults/ビジネス/",
                            "economy": "Vaults/経済/",
                            "daily": "Vaults/日常/",
                            "other": "Vaults/その他/",
                        },
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
    def test_e2e_claude_import_produces_organized_items(self, mock_extract):
        """raw_claude_conversations から organized_items まで一気通貫で処理されること。"""
        mock_extract.return_value = (_make_mock_ollama_response(), None)

        pipeline = self.pipelines["import_claude"]
        catalog = self._build_catalog()

        self.runner.run(pipeline, catalog)

        # Verify organized_items was produced (load returns dict of callables)
        organized_callables = catalog.load("organized_items")
        self.assertIsInstance(organized_callables, dict)
        self.assertGreater(len(organized_callables), 0, "organized_items should not be empty")

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

        organized_callables = catalog.load("organized_items")
        # 2 conversations should produce 2 organized items
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
    def test_e2e_organized_item_has_required_fields(self, mock_extract):
        """organized_items の各アイテムが必須フィールドを持つこと。"""
        mock_extract.return_value = (_make_mock_ollama_response(), None)

        pipeline = self.pipelines["import_claude"]
        catalog = self._build_catalog()

        self.runner.run(pipeline, catalog)

        organized_callables = catalog.load("organized_items")
        # Unwrap callables to get actual items
        for partition_id, load_func in organized_callables.items():
            item = load_func()
            self.assertIn("item_id", item, f"Missing item_id in {partition_id}")
            self.assertIn("genre", item, f"Missing genre in {partition_id}")
            self.assertIn("vault_path", item, f"Missing vault_path in {partition_id}")
            self.assertIn("final_path", item, f"Missing final_path in {partition_id}")

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

        # Create 3 conversations
        self.conversations = [
            _make_claude_conversation(uuid="conv-resume-001", name="asyncio 解説"),
            _make_claude_conversation(uuid="conv-resume-002", name="Django REST"),
            _make_claude_conversation(uuid="conv-resume-003", name="Flask チュートリアル"),
        ]

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
                        "vaults": {
                            "engineer": "Vaults/エンジニア/",
                            "business": "Vaults/ビジネス/",
                            "economy": "Vaults/経済/",
                            "daily": "Vaults/日常/",
                            "other": "Vaults/その他/",
                        },
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
        """1回目で一部失敗、2回目で失敗分のみ再処理されること。"""
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

        # First run: 3 items parsed, but 1 fails at extract_knowledge
        self.runner.run(pipeline, catalog)

        # After first run: 2 items succeed through to organized_items
        first_run_organized = catalog.load("organized_items")
        self.assertEqual(len(first_run_organized), 2, "First run should produce 2 organized items")

        first_run_llm_calls = mock_extract.call_count
        self.assertEqual(first_run_llm_calls, 3, "First run should call LLM 3 times")

        # Reset mock for second run: all items succeed
        mock_extract.reset_mock()
        mock_extract.return_value = (
            _make_mock_ollama_response(title="リカバリアイテム"),
            None,
        )

        # Second run with same catalog (existing outputs are preserved)
        # The failed item should be re-processed, succeeded items should be skipped
        self.runner.run(pipeline, catalog)

        # LLM should only be called for the 1 failed item (not for the 2 that already succeeded)
        self.assertEqual(
            mock_extract.call_count,
            1,
            "Second run should only call LLM for the 1 failed item",
        )

        # After second run: all 3 items should be organized
        second_run_organized = catalog.load("organized_items")
        self.assertEqual(
            len(second_run_organized),
            3,
            "Second run should produce 3 organized items total",
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
            "normalize_frontmatter",
            "clean_content",
            "determine_vault_path",
            "move_to_vault",
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
            "normalize_frontmatter",
            "clean_content",
            "determine_vault_path",
            "move_to_vault",
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
            "normalize_frontmatter",
            "clean_content",
            "determine_vault_path",
            "move_to_vault",
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
                "normalized_items": PartitionedMemoryDataset(),
                "cleaned_items": PartitionedMemoryDataset(),
                "vault_determined_items": PartitionedMemoryDataset(),
                "organized_items": PartitionedMemoryDataset(),
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
                        "vaults": {
                            "engineer": "Vaults/エンジニア/",
                            "business": "Vaults/ビジネス/",
                            "economy": "Vaults/経済/",
                            "daily": "Vaults/日常/",
                            "other": "Vaults/その他/",
                        },
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

        # Organize should NOT have run (organized_items should be empty)
        organized_callables = catalog.load("organized_items")
        self.assertEqual(
            len(organized_callables),
            0,
            "organized_items should be empty when running Transform only",
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

        organized_callables = catalog2.load("organized_items")
        self.assertIsInstance(organized_callables, dict)
        self.assertGreater(
            len(organized_callables),
            0,
            "organized_items should be produced by Organize-only partial run",
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


if __name__ == "__main__":
    unittest.main()
