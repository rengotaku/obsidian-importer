"""
E2E Tests for Q&A Pipeline

Tests question-answering functionality with mocked Ollama and Qdrant services.
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from haystack import Document as HaystackDocument

from src.rag.config import OllamaConfig
from src.rag.exceptions import QueryError
from src.rag.pipelines.query import (
    Answer,
    QueryFilters,
    create_qa_pipeline,
    ask,
)


class TestQAPipelineCreation(unittest.TestCase):
    """Tests for Q&A pipeline creation."""

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    @patch("src.rag.pipelines.query.PromptBuilder")
    @patch("src.rag.pipelines.query.OllamaGenerator")
    def test_create_qa_pipeline_structure(
        self,
        mock_generator_cls,
        mock_prompt_cls,
        mock_retriever_cls,
        mock_embedder_cls,
        mock_pipeline_cls,
    ):
        """Q&A pipeline has correct structure."""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        pipeline = create_qa_pipeline(mock_store)

        # Embedder (remote)
        mock_embedder_cls.assert_called_once()
        embedder_kwargs = mock_embedder_cls.call_args[1]
        self.assertEqual(embedder_kwargs["url"], "http://ollama-server.local:11434")
        self.assertEqual(embedder_kwargs["model"], "bge-m3")

        # Retriever
        mock_retriever_cls.assert_called_once_with(document_store=mock_store)

        # Prompt builder
        mock_prompt_cls.assert_called_once()

        # Generator (local)
        mock_generator_cls.assert_called_once()
        generator_kwargs = mock_generator_cls.call_args[1]
        self.assertEqual(generator_kwargs["url"], "http://localhost:11434")
        self.assertEqual(generator_kwargs["model"], "gpt-oss:20b")

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    @patch("src.rag.pipelines.query.PromptBuilder")
    @patch("src.rag.pipelines.query.OllamaGenerator")
    def test_create_qa_pipeline_custom_config(
        self,
        mock_generator_cls,
        mock_prompt_cls,
        mock_retriever_cls,
        mock_embedder_cls,
        mock_pipeline_cls,
    ):
        """Q&A pipeline uses custom config."""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        config = OllamaConfig(
            remote_url="http://remote:11434",
            local_url="http://local:11434",
            embedding_model="custom-embed",
            llm_model="custom-llm",
            llm_timeout=180,
            num_ctx=32768,
        )

        pipeline = create_qa_pipeline(mock_store, config=config)

        # Check embedder config
        embedder_kwargs = mock_embedder_cls.call_args[1]
        self.assertEqual(embedder_kwargs["url"], "http://remote:11434")
        self.assertEqual(embedder_kwargs["model"], "custom-embed")

        # Check generator config
        generator_kwargs = mock_generator_cls.call_args[1]
        self.assertEqual(generator_kwargs["url"], "http://local:11434")
        self.assertEqual(generator_kwargs["model"], "custom-llm")
        self.assertEqual(generator_kwargs["timeout"], 180)
        self.assertEqual(generator_kwargs["generation_kwargs"]["num_ctx"], 32768)


class TestE2EQA(unittest.TestCase):
    """E2E tests for Q&A functionality."""

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
    ) -> HaystackDocument:
        """Create mock Haystack document."""
        doc = MagicMock(spec=HaystackDocument)
        doc.content = content
        doc.score = score
        doc.meta = {
            "title": title,
            "file_path": file_path,
            "vault": vault,
            "tags": [],
            "position": 0,
        }
        return doc

    def test_ask_returns_answer(self):
        """Ask returns Answer with text and sources."""
        mock_docs = [
            self._create_mock_document(
                content="OAuth2 は認可のためのフレームワークです。",
                title="OAuth2入門",
                file_path="/Vaults/エンジニア/auth/oauth2.md",
                vault="エンジニア",
                score=0.91,
            ),
            self._create_mock_document(
                content="JWT はトークン形式の仕様です。",
                title="JWT解説",
                file_path="/Vaults/エンジニア/auth/jwt.md",
                vault="エンジニア",
                score=0.88,
            ),
        ]

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": mock_docs},
            "generator": {
                "replies": ["OAuth2は認可フレームワーク、JWTはトークン形式です。"]
            },
        }

        answer = ask(self.mock_pipeline, "OAuth2とJWTの違いは？")

        self.assertIsInstance(answer, Answer)
        self.assertIn("OAuth2", answer.text)
        self.assertEqual(len(answer.sources), 2)

    def test_answer_structure(self):
        """Answer has correct structure."""
        mock_doc = self._create_mock_document(
            content="Test content",
            title="Test Title",
            file_path="/test/path.md",
            vault="TestVault",
            score=0.9,
        )

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc]},
            "generator": {"replies": ["Test answer"]},
        }

        answer = ask(self.mock_pipeline, "Test question?")

        self.assertEqual(answer.text, "Test answer")
        self.assertEqual(len(answer.sources), 1)
        self.assertEqual(answer.sources[0].title, "Test Title")
        self.assertEqual(answer.sources[0].file_path, "/test/path.md")
        self.assertGreater(answer.confidence, 0)

    def test_ask_confidence_from_sources(self):
        """Answer confidence is calculated from source scores."""
        mock_docs = [
            self._create_mock_document(
                content="Content 1",
                title="Doc 1",
                file_path="/path/1.md",
                vault="Test",
                score=0.9,
            ),
            self._create_mock_document(
                content="Content 2",
                title="Doc 2",
                file_path="/path/2.md",
                vault="Test",
                score=0.8,
            ),
        ]

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": mock_docs},
            "generator": {"replies": ["Answer"]},
        }

        answer = ask(self.mock_pipeline, "Question?")

        # Confidence should be average of scores: (0.9 + 0.8) / 2 = 0.85
        self.assertAlmostEqual(answer.confidence, 0.85, places=2)

    def test_ask_no_sources_zero_confidence(self):
        """Answer with no sources has zero confidence."""
        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": []},
            "generator": {"replies": ["I don't know"]},
        }

        answer = ask(self.mock_pipeline, "Unknown question?")

        self.assertEqual(answer.confidence, 0.0)
        self.assertEqual(answer.sources, [])

    def test_ask_with_top_k(self):
        """Ask passes top_k to retriever."""
        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": []},
            "generator": {"replies": ["Answer"]},
        }

        ask(self.mock_pipeline, "Question?", top_k=10)

        call_args = self.mock_pipeline.run.call_args[0][0]
        self.assertEqual(call_args["retriever"]["top_k"], 10)

    def test_ask_empty_question_raises_error(self):
        """Empty question raises QueryError."""
        with self.assertRaises(QueryError) as ctx:
            ask(self.mock_pipeline, "")

        self.assertIn("Empty question", str(ctx.exception))

    def test_ask_whitespace_question_raises_error(self):
        """Whitespace-only question raises QueryError."""
        with self.assertRaises(QueryError):
            ask(self.mock_pipeline, "   ")

    def test_ask_pipeline_error_raises_query_error(self):
        """Pipeline errors are wrapped in QueryError."""
        self.mock_pipeline.run.side_effect = RuntimeError("LLM timeout")

        with self.assertRaises(QueryError) as ctx:
            ask(self.mock_pipeline, "Test question?")

        self.assertIn("Q&A failed", str(ctx.exception))

    def test_ask_empty_reply(self):
        """Empty LLM reply is handled."""
        mock_doc = self._create_mock_document(
            content="Content",
            title="Title",
            file_path="/path.md",
            vault="Test",
            score=0.8,
        )

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc]},
            "generator": {"replies": []},  # Empty replies
        }

        answer = ask(self.mock_pipeline, "Question?")

        self.assertEqual(answer.text, "")


class TestQAWithFilters(unittest.TestCase):
    """Tests for Q&A with filters."""

    def setUp(self):
        """Set up mock pipeline."""
        self.mock_pipeline = MagicMock()
        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": []},
            "generator": {"replies": ["Answer"]},
        }

    def test_ask_with_vault_filter(self):
        """Ask passes vault filter to retriever."""
        filters = QueryFilters(vaults=["エンジニア"])

        ask(self.mock_pipeline, "Question?", filters=filters)

        call_args = self.mock_pipeline.run.call_args[0][0]
        passed_filter = call_args["retriever"]["filters"]
        self.assertEqual(passed_filter["field"], "meta.vault")
        self.assertEqual(passed_filter["value"], "エンジニア")

    def test_ask_with_tag_filter(self):
        """Ask passes tag filter to retriever."""
        filters = QueryFilters(tags=["auth"])

        ask(self.mock_pipeline, "Question?", filters=filters)

        call_args = self.mock_pipeline.run.call_args[0][0]
        passed_filter = call_args["retriever"]["filters"]
        self.assertEqual(passed_filter["field"], "meta.tags")
        self.assertEqual(passed_filter["value"], "auth")


class TestQAWithJapaneseContent(unittest.TestCase):
    """Tests for Q&A with Japanese questions and answers."""

    def setUp(self):
        """Set up mock pipeline."""
        self.mock_pipeline = MagicMock()

    def test_japanese_question(self):
        """Japanese question is handled correctly."""
        mock_doc = MagicMock(spec=HaystackDocument)
        mock_doc.content = "Kubernetes はコンテナオーケストレーションプラットフォームです。"
        mock_doc.score = 0.9
        mock_doc.meta = {
            "title": "Kubernetes基礎",
            "file_path": "/Vaults/エンジニア/kubernetes.md",
            "vault": "エンジニア",
            "tags": [],
            "position": 0,
        }

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc]},
            "generator": {
                "replies": ["Kubernetes はコンテナを管理するためのプラットフォームです。"]
            },
        }

        answer = ask(self.mock_pipeline, "Kubernetesとは何ですか？")

        self.assertIn("Kubernetes", answer.text)
        self.assertEqual(answer.sources[0].title, "Kubernetes基礎")

    def test_japanese_answer_generation(self):
        """Japanese answer is returned correctly."""
        mock_doc = MagicMock(spec=HaystackDocument)
        mock_doc.content = "日本語のコンテンツ"
        mock_doc.score = 0.85
        mock_doc.meta = {
            "title": "日本語ドキュメント",
            "file_path": "/path/doc.md",
            "vault": "Test",
            "tags": [],
            "position": 0,
        }

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc]},
            "generator": {"replies": ["これは日本語の回答です。"]},
        }

        answer = ask(self.mock_pipeline, "質問")

        self.assertEqual(answer.text, "これは日本語の回答です。")


class TestQASourceCitation(unittest.TestCase):
    """Tests for Q&A source citation accuracy (SC-003)."""

    def setUp(self):
        """Set up mock pipeline."""
        self.mock_pipeline = MagicMock()

    def test_sources_match_retrieved_documents(self):
        """Sources in answer match retrieved documents."""
        mock_docs = [
            MagicMock(
                spec=HaystackDocument,
                content="OAuth2 content",
                score=0.9,
                meta={
                    "title": "OAuth2",
                    "file_path": "/auth/oauth2.md",
                    "vault": "エンジニア",
                    "tags": ["auth"],
                    "position": 0,
                },
            ),
            MagicMock(
                spec=HaystackDocument,
                content="JWT content",
                score=0.85,
                meta={
                    "title": "JWT",
                    "file_path": "/auth/jwt.md",
                    "vault": "エンジニア",
                    "tags": ["auth"],
                    "position": 0,
                },
            ),
        ]

        self.mock_pipeline.run.return_value = {
            "retriever": {"documents": mock_docs},
            "generator": {"replies": ["Answer referencing both"]},
        }

        answer = ask(self.mock_pipeline, "Question about auth?")

        # All retrieved docs should be in sources
        source_titles = {s.title for s in answer.sources}
        self.assertEqual(source_titles, {"OAuth2", "JWT"})

        # Sources should preserve scores
        source_scores = {s.title: s.score for s in answer.sources}
        self.assertAlmostEqual(source_scores["OAuth2"], 0.9)
        self.assertAlmostEqual(source_scores["JWT"], 0.85)


if __name__ == "__main__":
    unittest.main()
