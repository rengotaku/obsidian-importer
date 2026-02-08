"""Tests for pipeline registry.

Phase 5 RED tests: register_pipelines should return import_claude and __default__.
Phase 4 RED tests: dispatch-based __default__ pipeline selection via OmegaConf.

These tests verify:
- register_pipelines returns import_claude pipeline combining extract_claude + transform + organize
- register_pipelines returns __default__ pipeline (same as import_claude or non-empty)
- Registered pipelines contain expected node names
- [Phase 4] dispatch: __default__ is set dynamically based on import.provider in parameters.yml
- [Phase 4] dispatch: invalid provider raises clear error
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

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
        """import_claude が parse_claude_zip ノードを含むこと。"""
        pipeline = self.pipelines["import_claude"]
        node_names = {n.name for n in pipeline.nodes}
        self.assertIn(
            "parse_claude_zip",
            node_names,
            f"Expected 'parse_claude_zip' in node names: {node_names}",
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
            "extract_topic",
            "normalize_frontmatter",
            "clean_content",
            "embed_frontmatter_fields",
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


class TestDispatchPipeline(unittest.TestCase):
    """Phase 4: dispatch 型パイプライン選択テスト。

    register_pipelines() が OmegaConf で parameters.yml の import.provider を読み、
    __default__ パイプラインを動的に設定することを検証する。
    """

    def _mock_omegaconf_load(self, provider: str):
        """OmegaConf.load() をモックして指定 provider を返すヘルパー。

        Args:
            provider: import.provider の値（claude, openai, github）

        Returns:
            Mock patcher context manager.
        """
        mock_config = MagicMock()
        mock_config.get.return_value = {"provider": provider}
        # OmegaConf.load() が返す設定オブジェクトをモック
        # import セクションへのアクセスをサポート
        mock_config.__getitem__ = (
            lambda self_inner, key: {"provider": provider} if key == "import" else {}
        )
        mock_config.__contains__ = lambda self_inner, key: key == "import"
        return patch("obsidian_etl.pipeline_registry.OmegaConf.load", return_value=mock_config)

    def test_default_is_import_claude_when_provider_claude(self):
        """import.provider=claude の場合、__default__ が import_claude と同じノード群であること。"""
        with self._mock_omegaconf_load("claude"):
            pipelines = register_pipelines()

        default_nodes = {n.name for n in pipelines["__default__"].nodes}
        claude_nodes = {n.name for n in pipelines["import_claude"].nodes}
        self.assertEqual(
            default_nodes,
            claude_nodes,
            f"__default__ should match import_claude.\n"
            f"__default__: {sorted(default_nodes)}\n"
            f"import_claude: {sorted(claude_nodes)}",
        )

    def test_default_is_import_openai_when_provider_openai(self):
        """import.provider=openai の場合、__default__ が import_openai と同じノード群であること。"""
        with self._mock_omegaconf_load("openai"):
            pipelines = register_pipelines()

        default_nodes = {n.name for n in pipelines["__default__"].nodes}
        openai_nodes = {n.name for n in pipelines["import_openai"].nodes}
        self.assertEqual(
            default_nodes,
            openai_nodes,
            f"__default__ should match import_openai.\n"
            f"__default__: {sorted(default_nodes)}\n"
            f"import_openai: {sorted(openai_nodes)}",
        )

    def test_default_is_import_github_when_provider_github(self):
        """import.provider=github の場合、__default__ が import_github と同じノード群であること。"""
        with self._mock_omegaconf_load("github"):
            pipelines = register_pipelines()

        default_nodes = {n.name for n in pipelines["__default__"].nodes}
        github_nodes = {n.name for n in pipelines["import_github"].nodes}
        self.assertEqual(
            default_nodes,
            github_nodes,
            f"__default__ should match import_github.\n"
            f"__default__: {sorted(default_nodes)}\n"
            f"import_github: {sorted(github_nodes)}",
        )

    def test_default_contains_parse_claude_zip_when_provider_claude(self):
        """import.provider=claude の場合、__default__ に parse_claude_zip ノードが含まれること。"""
        with self._mock_omegaconf_load("claude"):
            pipelines = register_pipelines()

        default_nodes = {n.name for n in pipelines["__default__"].nodes}
        self.assertIn("parse_claude_zip", default_nodes)

    def test_default_contains_parse_chatgpt_zip_when_provider_openai(self):
        """import.provider=openai の場合、__default__ に parse_chatgpt_zip ノードが含まれること。"""
        with self._mock_omegaconf_load("openai"):
            pipelines = register_pipelines()

        default_nodes = {n.name for n in pipelines["__default__"].nodes}
        self.assertIn("parse_chatgpt_zip", default_nodes)

    def test_default_contains_clone_github_repo_when_provider_github(self):
        """import.provider=github の場合、__default__ に clone_github_repo ノードが含まれること。"""
        with self._mock_omegaconf_load("github"):
            pipelines = register_pipelines()

        default_nodes = {n.name for n in pipelines["__default__"].nodes}
        self.assertIn("clone_github_repo", default_nodes)

    def test_individual_pipeline_names_still_work(self):
        """dispatch 後も個別パイプライン名 (import_claude, import_openai, import_github) でアクセスできること。"""
        with self._mock_omegaconf_load("openai"):
            pipelines = register_pipelines()

        # All three individual pipeline names should be present regardless of provider
        self.assertIn("import_claude", pipelines)
        self.assertIn("import_openai", pipelines)
        self.assertIn("import_github", pipelines)

        # Each should be a Pipeline instance with nodes
        for name in ["import_claude", "import_openai", "import_github"]:
            self.assertIsInstance(pipelines[name], Pipeline)
            self.assertGreater(
                len(pipelines[name].nodes),
                0,
                f"{name} pipeline should have nodes",
            )


class TestDispatchError(unittest.TestCase):
    """Phase 4: 無効な provider 指定時のエラーテスト。

    存在しない provider を指定した場合、明確なエラーメッセージが表示されること。
    """

    def _mock_omegaconf_load(self, provider: str):
        """OmegaConf.load() をモックして指定 provider を返すヘルパー。"""
        mock_config = MagicMock()
        mock_config.get.return_value = {"provider": provider}
        mock_config.__getitem__ = (
            lambda self_inner, key: {"provider": provider} if key == "import" else {}
        )
        mock_config.__contains__ = lambda self_inner, key: key == "import"
        return patch("obsidian_etl.pipeline_registry.OmegaConf.load", return_value=mock_config)

    def test_invalid_provider_raises_value_error(self):
        """無効な provider を指定した場合、ValueError が発生すること。"""
        with self._mock_omegaconf_load("invalid_provider"):
            with self.assertRaises(ValueError) as ctx:
                register_pipelines()

        error_msg = str(ctx.exception)
        self.assertIn(
            "invalid_provider",
            error_msg,
            f"Error message should contain the invalid provider name: {error_msg}",
        )

    def test_invalid_provider_error_message_lists_valid_providers(self):
        """無効な provider のエラーメッセージに有効な provider 一覧が含まれること。"""
        with self._mock_omegaconf_load("nonexistent"), self.assertRaises(ValueError) as ctx:
            register_pipelines()

        error_msg = str(ctx.exception)
        # Error message should mention valid providers
        for valid_provider in ["claude", "openai", "github"]:
            self.assertIn(
                valid_provider,
                error_msg,
                f"Error message should list valid provider '{valid_provider}': {error_msg}",
            )

    def test_empty_provider_raises_value_error(self):
        """空文字列の provider を指定した場合、ValueError が発生すること。"""
        with self._mock_omegaconf_load(""), self.assertRaises(ValueError) as ctx:
            register_pipelines()

        error_msg = str(ctx.exception)
        # Should still list valid providers
        self.assertIn("claude", error_msg)


if __name__ == "__main__":
    unittest.main()
