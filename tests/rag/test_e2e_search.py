"""
E2E Tests for Search Pipeline

Tests semantic search functionality with mocked Ollama and Qdrant services.
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from haystack import Document as HaystackDocument

from src.rag.config import OllamaConfig
from src.rag.exceptions import QueryError
from src.rag.pipelines.query import (
    QueryFilters,
    SearchResponse,
    SearchResult,
    build_qdrant_filters,
    create_search_pipeline,
    search,
)


class TestSearchPipelineCreation(unittest.TestCase):
    """Tests for search pipeline creation."""

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    def test_create_search_pipeline_structure(
        self, mock_retriever_cls, mock_embedder_cls, mock_pipeline_cls
    ):
        """Search pipeline has correct structure."""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        pipeline = create_search_pipeline(mock_store)

        # Embedder should be configured with remote URL
        mock_embedder_cls.assert_called_once()
        call_kwargs = mock_embedder_cls.call_args[1]
        self.assertEqual(call_kwargs["url"], "http://ollama-server.local:11434")
        self.assertEqual(call_kwargs["model"], "bge-m3")

        # Retriever should use the store
        mock_retriever_cls.assert_called_once_with(document_store=mock_store)

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    def test_create_search_pipeline_custom_config(
        self, mock_retriever_cls, mock_embedder_cls, mock_pipeline_cls
    ):
        """Search pipeline uses custom config."""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        config = OllamaConfig(
            remote_url="http://custom:11434",
            embedding_model="custom-model",
            embedding_timeout=60,
        )

        pipeline = create_search_pipeline(mock_store, config=config)

        call_kwargs = mock_embedder_cls.call_args[1]
        self.assertEqual(call_kwargs["url"], "http://custom:11434")
        self.assertEqual(call_kwargs["model"], "custom-model")
        self.assertEqual(call_kwargs["timeout"], 60)


class TestE2ESearch(unittest.TestCase):
    """E2E tests for search functionality."""

    def setUp(self):
        """Set up mock pipeline."""
        self.mock_pipeline = MagicMock()

    def _create_mock_document(
        self,
        content: str,
        title: str,
        file_path: str,
        vault: str,
        score: float,
        tags: list[str] | None = None,
        position: int = 0,
    ) -> HaystackDocument:
        """Create mock Haystack document."""
        doc = MagicMock(spec=HaystackDocument)
        doc.content = content
        doc.score = score
        doc.meta = {
            "title": title,
            "file_path": file_path,
            "vault": vault,
            "tags": tags or [],
            "position": position,
        }
        return doc

    def test_search_returns_results(self):
        """Search returns SearchResponse with results."""
        # Mock pipeline response
        mock_docs = [
            self._create_mock_document(
                content="Kubernetes is a container orchestration platform.",
                title="Kubernetes基礎",
                file_path="/Vaults/エンジニア/kubernetes.md",
                vault="エンジニア",
                score=0.92,
                tags=["kubernetes", "container"],
            ),
            self._create_mock_document(
                content="Docker provides container runtime.",
                title="Docker入門",
                file_path="/Vaults/エンジニア/docker.md",
                vault="エンジニア",
                score=0.85,
                tags=["docker", "container"],
            ),
        ]

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": mock_docs}
        }

        response = search(self.mock_pipeline, "container orchestration")

        self.assertIsInstance(response, SearchResponse)
        self.assertEqual(response.query, "container orchestration")
        self.assertEqual(response.total, 2)
        self.assertEqual(len(response.results), 2)

    def test_search_result_structure(self):
        """Search results have correct structure."""
        mock_doc = self._create_mock_document(
            content="Test content",
            title="Test Title",
            file_path="/test/path.md",
            vault="TestVault",
            score=0.9,
            tags=["test"],
            position=0,
        )

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc]}
        }

        response = search(self.mock_pipeline, "test query")

        result = response.results[0]
        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.content, "Test content")
        self.assertEqual(result.title, "Test Title")
        self.assertEqual(result.file_path, "/test/path.md")
        self.assertEqual(result.vault, "TestVault")
        self.assertAlmostEqual(result.score, 0.9)
        self.assertEqual(result.position, 0)

    def test_search_with_top_k(self):
        """Search passes top_k to retriever."""
        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": []}
        }

        search(self.mock_pipeline, "test", top_k=10)

        call_args = self.mock_pipeline.run.call_args[0][0]
        self.assertEqual(call_args["retriever"]["top_k"], 10)

    def test_search_empty_query_raises_error(self):
        """Empty query raises QueryError."""
        with self.assertRaises(QueryError) as ctx:
            search(self.mock_pipeline, "")

        self.assertIn("Empty query", str(ctx.exception))

    def test_search_whitespace_query_raises_error(self):
        """Whitespace-only query raises QueryError."""
        with self.assertRaises(QueryError):
            search(self.mock_pipeline, "   ")

    def test_search_pipeline_error_raises_query_error(self):
        """Pipeline errors are wrapped in QueryError."""
        self.mock_pipeline.run.side_effect = RuntimeError("Connection failed")

        with self.assertRaises(QueryError) as ctx:
            search(self.mock_pipeline, "test query")

        self.assertIn("Search failed", str(ctx.exception))

    def test_search_no_results(self):
        """Search with no results returns empty response."""
        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": []}
        }

        response = search(self.mock_pipeline, "nonexistent topic")

        self.assertEqual(response.total, 0)
        self.assertEqual(response.results, [])


class TestSearchFilters(unittest.TestCase):
    """Tests for search filters."""

    def setUp(self):
        """Set up mock pipeline."""
        self.mock_pipeline = MagicMock()
        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": []}
        }

    def test_build_single_vault_filter(self):
        """Single vault filter is built correctly."""
        filters = QueryFilters(vaults=["エンジニア"])
        qdrant_filter = build_qdrant_filters(filters)

        self.assertEqual(qdrant_filter["field"], "meta.vault")
        self.assertEqual(qdrant_filter["operator"], "==")
        self.assertEqual(qdrant_filter["value"], "エンジニア")

    def test_build_multiple_vault_filter(self):
        """Multiple vault filter uses 'in' operator."""
        filters = QueryFilters(vaults=["エンジニア", "ビジネス"])
        qdrant_filter = build_qdrant_filters(filters)

        self.assertEqual(qdrant_filter["field"], "meta.vault")
        self.assertEqual(qdrant_filter["operator"], "in")
        self.assertEqual(qdrant_filter["value"], ["エンジニア", "ビジネス"])

    def test_build_tag_filter(self):
        """Tag filter uses 'contains' operator."""
        filters = QueryFilters(tags=["kubernetes"])
        qdrant_filter = build_qdrant_filters(filters)

        self.assertEqual(qdrant_filter["field"], "meta.tags")
        self.assertEqual(qdrant_filter["operator"], "contains")
        self.assertEqual(qdrant_filter["value"], "kubernetes")

    def test_build_multiple_tags_filter(self):
        """Multiple tags create AND conditions."""
        filters = QueryFilters(tags=["kubernetes", "container"])
        qdrant_filter = build_qdrant_filters(filters)

        self.assertEqual(qdrant_filter["operator"], "AND")
        self.assertEqual(len(qdrant_filter["conditions"]), 2)

    def test_build_combined_filter(self):
        """Combined vault and tag filters use AND."""
        filters = QueryFilters(
            vaults=["エンジニア"],
            tags=["kubernetes"],
        )
        qdrant_filter = build_qdrant_filters(filters)

        self.assertEqual(qdrant_filter["operator"], "AND")
        self.assertEqual(len(qdrant_filter["conditions"]), 2)

    def test_build_no_filter(self):
        """None filters returns None."""
        qdrant_filter = build_qdrant_filters(None)
        self.assertIsNone(qdrant_filter)

    def test_build_empty_filter(self):
        """Empty filters returns None."""
        filters = QueryFilters()
        qdrant_filter = build_qdrant_filters(filters)
        self.assertIsNone(qdrant_filter)

    def test_search_with_vault_filter(self):
        """Search passes vault filter to retriever."""
        filters = QueryFilters(vaults=["エンジニア"])

        search(self.mock_pipeline, "test", filters=filters)

        call_args = self.mock_pipeline.run.call_args[0][0]
        passed_filter = call_args["retriever"]["filters"]
        self.assertEqual(passed_filter["field"], "meta.vault")
        self.assertEqual(passed_filter["value"], "エンジニア")

    def test_search_with_tag_filter(self):
        """Search passes tag filter to retriever."""
        filters = QueryFilters(tags=["container"])

        search(self.mock_pipeline, "test", filters=filters)

        call_args = self.mock_pipeline.run.call_args[0][0]
        passed_filter = call_args["retriever"]["filters"]
        self.assertEqual(passed_filter["field"], "meta.tags")
        self.assertEqual(passed_filter["value"], "container")


class TestSearchWithJapaneseQuery(unittest.TestCase):
    """Tests for search with Japanese queries."""

    def setUp(self):
        """Set up mock pipeline."""
        self.mock_pipeline = MagicMock()

    def test_japanese_query(self):
        """Japanese query is handled correctly."""
        mock_doc = MagicMock(spec=HaystackDocument)
        mock_doc.content = "Kubernetes はコンテナオーケストレーションプラットフォームです。"
        mock_doc.score = 0.88
        mock_doc.meta = {
            "title": "Kubernetes基礎",
            "file_path": "/Vaults/エンジニア/kubernetes.md",
            "vault": "エンジニア",
            "tags": [],
            "position": 0,
        }

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc]}
        }

        response = search(self.mock_pipeline, "コンテナオーケストレーション")

        self.assertEqual(response.query, "コンテナオーケストレーション")
        self.assertEqual(response.total, 1)

    def test_mixed_language_query(self):
        """Mixed ja/en query is handled correctly."""
        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": []}
        }

        # Should not raise error
        response = search(self.mock_pipeline, "Kubernetes デプロイメント戦略")

        self.assertEqual(response.query, "Kubernetes デプロイメント戦略")


class TestSearchResultOrdering(unittest.TestCase):
    """Tests for search result ordering."""

    def setUp(self):
        """Set up mock pipeline."""
        self.mock_pipeline = MagicMock()

    def test_results_preserve_score_order(self):
        """Results preserve retriever order (by score)."""
        mock_docs = []
        for i, score in enumerate([0.9, 0.8, 0.7]):
            doc = MagicMock(spec=HaystackDocument)
            doc.content = f"Content {i}"
            doc.score = score
            doc.meta = {
                "title": f"Doc {i}",
                "file_path": f"/path/doc{i}.md",
                "vault": "Test",
                "tags": [],
                "position": 0,
            }
            mock_docs.append(doc)

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": mock_docs}
        }

        response = search(self.mock_pipeline, "test")

        # Scores should be in descending order
        scores = [r.score for r in response.results]
        self.assertEqual(scores, [0.9, 0.8, 0.7])


if __name__ == "__main__":
    unittest.main()
