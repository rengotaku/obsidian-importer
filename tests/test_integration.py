"""E2E integration tests for Claude import pipeline.

Phase 5 RED tests: SequentialRunner with test DataCatalog.
These tests verify:
- Full pipeline execution: raw_claude_conversations -> organized_items
- All intermediate datasets are produced
- Ollama is mocked (no real LLM calls)
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from kedro.io import AbstractDataset, DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner

from obsidian_etl.pipeline_registry import register_pipelines


class PartitionedMemoryDataset(AbstractDataset):
    """Memory dataset that mimics PartitionedDataset behavior.

    When saving dict[str, dict], it stores as-is.
    When loading, it returns dict[str, Callable] where each callable returns the item.
    """

    def __init__(self):
        self._data = None

    def _save(self, data: dict[str, dict]) -> None:
        """Save dictionary data."""
        self._data = data

    def _load(self) -> dict[str, callable]:
        """Load data as dict of callables (PartitionedDataset pattern)."""
        if self._data is None:
            return {}
        # Wrap each item in a callable
        return {key: (lambda v=val: v) for key, val in self._data.items()}

    def _describe(self) -> dict:
        return {"type": "PartitionedMemoryDataset"}


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
        return DataCatalog(
            datasets={
                "raw_claude_conversations": MemoryDataset(self.conversations),
                "parsed_items": PartitionedMemoryDataset(),
                "transformed_items_with_knowledge": PartitionedMemoryDataset(),
                "transformed_items_with_metadata": PartitionedMemoryDataset(),
                "markdown_notes": PartitionedMemoryDataset(),
                "classified_items": PartitionedMemoryDataset(),
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


if __name__ == "__main__":
    unittest.main()
