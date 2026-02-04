"""Tests for pipeline registry.

Phase 5 RED tests: register_pipelines should return import_claude and __default__.
These tests verify:
- register_pipelines returns import_claude pipeline combining extract_claude + transform + organize
- register_pipelines returns __default__ pipeline (same as import_claude or non-empty)
- Registered pipelines contain expected node names
"""

from __future__ import annotations

import unittest

from kedro.pipeline import Pipeline

from obsidian_etl.pipeline_registry import register_pipelines


class TestPipelineRegistry(unittest.TestCase):
    """register_pipelines returns import_claude and __default__."""

    def setUp(self):
        """Call register_pipelines once for all tests."""
        self.pipelines = register_pipelines()

    def test_register_pipelines_returns_dict(self):
        """register_pipelines が dict を返すこと。"""
        self.assertIsInstance(self.pipelines, dict)

    def test_register_pipelines_has_import_claude(self):
        """register_pipelines が import_claude パイプラインを含むこと。"""
        self.assertIn("import_claude", self.pipelines)
        self.assertIsInstance(self.pipelines["import_claude"], Pipeline)

    def test_register_pipelines_has_default(self):
        """register_pipelines が __default__ パイプラインを含むこと。"""
        self.assertIn("__default__", self.pipelines)
        self.assertIsInstance(self.pipelines["__default__"], Pipeline)

    def test_import_claude_pipeline_has_nodes(self):
        """import_claude パイプラインがノードを持つこと（空でないこと）。"""
        pipeline = self.pipelines["import_claude"]
        nodes = pipeline.nodes
        self.assertGreater(len(nodes), 0, "import_claude pipeline should have nodes")

    def test_import_claude_contains_extract_node(self):
        """import_claude が parse_claude_json ノードを含むこと。"""
        pipeline = self.pipelines["import_claude"]
        node_names = {n.name for n in pipeline.nodes}
        self.assertIn(
            "parse_claude_json",
            node_names,
            f"Expected 'parse_claude_json' in node names: {node_names}",
        )

    def test_import_claude_contains_transform_nodes(self):
        """import_claude が transform ノード群を含むこと。"""
        pipeline = self.pipelines["import_claude"]
        node_names = {n.name for n in pipeline.nodes}

        expected_transform_nodes = [
            "extract_knowledge",
            "generate_metadata",
            "format_markdown",
        ]
        for expected in expected_transform_nodes:
            self.assertIn(
                expected,
                node_names,
                f"Expected '{expected}' in node names: {node_names}",
            )

    def test_import_claude_contains_organize_nodes(self):
        """import_claude が organize ノード群を含むこと。"""
        pipeline = self.pipelines["import_claude"]
        node_names = {n.name for n in pipeline.nodes}

        expected_organize_nodes = [
            "classify_genre",
            "normalize_frontmatter",
            "clean_content",
            "determine_vault_path",
            "move_to_vault",
        ]
        for expected in expected_organize_nodes:
            self.assertIn(
                expected,
                node_names,
                f"Expected '{expected}' in node names: {node_names}",
            )

    def test_default_pipeline_is_not_empty(self):
        """__default__ パイプラインが空でないこと。"""
        pipeline = self.pipelines["__default__"]
        self.assertGreater(
            len(pipeline.nodes),
            0,
            "__default__ pipeline should not be empty",
        )


if __name__ == "__main__":
    unittest.main()
