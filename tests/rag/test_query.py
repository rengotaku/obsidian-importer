"""
Tests for Query Pipeline - search, Q&A functionality
"""
from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from haystack import Document as HaystackDocument

from src.rag.config import OllamaConfig
from src.rag.exceptions import QueryError
from src.rag.pipelines.query import (
    Answer,
    QueryFilters,
    SearchResponse,
    SearchResult,
    ask,
    build_qdrant_filters,
    create_qa_pipeline,
    create_search_pipeline,
    search,
)


class TestQueryFilters(unittest.TestCase):
    """Tests for QueryFilters dataclass"""

    def test_default_values(self):
        """Default values are None"""
        filters = QueryFilters()
        self.assertIsNone(filters.vaults)
        self.assertIsNone(filters.tags)
        self.assertIsNone(filters.date_from)
        self.assertIsNone(filters.date_to)

    def test_with_vaults(self):
        """Vaults can be set"""
        filters = QueryFilters(vaults=["engineering", "business"])
        self.assertEqual(filters.vaults, ["engineering", "business"])

    def test_with_tags(self):
        """Tags can be set"""
        filters = QueryFilters(tags=["python", "kubernetes"])
        self.assertEqual(filters.tags, ["python", "kubernetes"])

    def test_with_date_range(self):
        """Date range can be set"""
        filters = QueryFilters(
            date_from=date(2024, 1, 1),
            date_to=date(2024, 12, 31),
        )
        self.assertEqual(filters.date_from, date(2024, 1, 1))
        self.assertEqual(filters.date_to, date(2024, 12, 31))


class TestSearchResult(unittest.TestCase):
    """Tests for SearchResult dataclass"""

    def test_creation(self):
        """SearchResult is created correctly"""
        result = SearchResult(
            content="Test content",
            score=0.95,
            file_path="/test/doc.md",
            title="Test Document",
            vault="engineering",
            position=0,
        )
        self.assertEqual(result.content, "Test content")
        self.assertEqual(result.score, 0.95)
        self.assertEqual(result.file_path, "/test/doc.md")
        self.assertEqual(result.title, "Test Document")
        self.assertEqual(result.vault, "engineering")
        self.assertEqual(result.position, 0)


class TestSearchResponse(unittest.TestCase):
    """Tests for SearchResponse dataclass"""

    def test_creation(self):
        """SearchResponse is created correctly"""
        results = [
            SearchResult(
                content="Content 1",
                score=0.9,
                file_path="/test/doc1.md",
                title="Doc 1",
                vault="test",
                position=0,
            ),
        ]
        response = SearchResponse(query="test query", results=results, total=1)
        self.assertEqual(response.query, "test query")
        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.total, 1)


class TestAnswer(unittest.TestCase):
    """Tests for Answer dataclass"""

    def test_creation(self):
        """Answer is created correctly"""
        sources = [
            SearchResult(
                content="Source content",
                score=0.85,
                file_path="/test/doc.md",
                title="Source Doc",
                vault="test",
                position=0,
            ),
        ]
        answer = Answer(text="Generated answer", sources=sources, confidence=0.85)
        self.assertEqual(answer.text, "Generated answer")
        self.assertEqual(len(answer.sources), 1)
        self.assertEqual(answer.confidence, 0.85)


class TestBuildQdrantFilters(unittest.TestCase):
    """Tests for build_qdrant_filters function"""

    def test_none_filters(self):
        """None filters returns None"""
        result = build_qdrant_filters(None)
        self.assertIsNone(result)

    def test_empty_filters(self):
        """Empty filters returns None"""
        filters = QueryFilters()
        result = build_qdrant_filters(filters)
        self.assertIsNone(result)

    def test_single_vault_filter(self):
        """Single vault filter is built correctly"""
        filters = QueryFilters(vaults=["engineering"])
        result = build_qdrant_filters(filters)
        self.assertEqual(result["field"], "meta.vault")
        self.assertEqual(result["operator"], "==")
        self.assertEqual(result["value"], "engineering")

    def test_multiple_vault_filter(self):
        """Multiple vault filter uses 'in' operator"""
        filters = QueryFilters(vaults=["engineering", "business"])
        result = build_qdrant_filters(filters)
        self.assertEqual(result["field"], "meta.vault")
        self.assertEqual(result["operator"], "in")
        self.assertEqual(result["value"], ["engineering", "business"])

    def test_single_tag_filter(self):
        """Single tag filter uses 'contains'"""
        filters = QueryFilters(tags=["python"])
        result = build_qdrant_filters(filters)
        self.assertEqual(result["field"], "meta.tags")
        self.assertEqual(result["operator"], "contains")
        self.assertEqual(result["value"], "python")

    def test_multiple_tags_filter(self):
        """Multiple tags filter creates AND conditions"""
        filters = QueryFilters(tags=["python", "kubernetes"])
        result = build_qdrant_filters(filters)
        self.assertEqual(result["operator"], "AND")
        self.assertEqual(len(result["conditions"]), 2)

    def test_date_from_filter(self):
        """Date from filter is built correctly"""
        filters = QueryFilters(date_from=date(2024, 1, 15))
        result = build_qdrant_filters(filters)
        self.assertEqual(result["field"], "meta.created")
        self.assertEqual(result["operator"], ">=")
        self.assertEqual(result["value"], "2024-01-15")

    def test_date_to_filter(self):
        """Date to filter is built correctly"""
        filters = QueryFilters(date_to=date(2024, 12, 31))
        result = build_qdrant_filters(filters)
        self.assertEqual(result["field"], "meta.created")
        self.assertEqual(result["operator"], "<=")
        self.assertEqual(result["value"], "2024-12-31")

    def test_combined_filters(self):
        """Combined filters create AND condition"""
        filters = QueryFilters(
            vaults=["engineering"],
            tags=["python"],
            date_from=date(2024, 1, 1),
        )
        result = build_qdrant_filters(filters)
        self.assertEqual(result["operator"], "AND")
        self.assertEqual(len(result["conditions"]), 3)


class TestCreateSearchPipeline(unittest.TestCase):
    """Tests for create_search_pipeline function"""

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    def test_pipeline_has_components(
        self, mock_retriever_cls, mock_embedder_cls, mock_pipeline_cls
    ):
        """Pipeline adds embedder and retriever components"""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        pipeline = create_search_pipeline(mock_store)

        # Check add_component calls
        add_calls = mock_pipeline.add_component.call_args_list
        self.assertEqual(len(add_calls), 2)
        self.assertEqual(add_calls[0][0][0], "embedder")
        self.assertEqual(add_calls[1][0][0], "retriever")

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    def test_pipeline_uses_config(
        self, mock_retriever_cls, mock_embedder_cls, mock_pipeline_cls
    ):
        """Pipeline uses provided config"""
        mock_store = MagicMock()
        config = OllamaConfig(
            remote_url="http://custom:11434",
            embedding_model="custom-model",
            embedding_timeout=60,
        )

        pipeline = create_search_pipeline(mock_store, config)

        mock_embedder_cls.assert_called_once_with(
            url="http://custom:11434",
            model="custom-model",
            timeout=60,
        )

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    def test_pipeline_uses_default_config(
        self, mock_retriever_cls, mock_embedder_cls, mock_pipeline_cls
    ):
        """Pipeline uses default config when not provided"""
        mock_store = MagicMock()

        pipeline = create_search_pipeline(mock_store)

        # Should use default ollama_config values
        call_kwargs = mock_embedder_cls.call_args[1]
        self.assertEqual(call_kwargs["url"], "http://ollama-server.local:11434")
        self.assertEqual(call_kwargs["model"], "bge-m3")

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    def test_pipeline_connects_components(
        self, mock_retriever_cls, mock_embedder_cls, mock_pipeline_cls
    ):
        """Pipeline connects embedder to retriever"""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        pipeline = create_search_pipeline(mock_store)

        # Check connect call
        mock_pipeline.connect.assert_called_once_with(
            "embedder.embedding", "retriever.query_embedding"
        )

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    def test_retriever_uses_store(
        self, mock_retriever_cls, mock_embedder_cls, mock_pipeline_cls
    ):
        """Retriever is created with document store"""
        mock_store = MagicMock()

        pipeline = create_search_pipeline(mock_store)

        mock_retriever_cls.assert_called_once_with(document_store=mock_store)


class TestSearch(unittest.TestCase):
    """Tests for search function"""

    def test_empty_query_raises_error(self):
        """Empty query raises QueryError"""
        mock_pipeline = MagicMock()

        with self.assertRaises(QueryError) as ctx:
            search(mock_pipeline, "")

        self.assertIn("Empty query", str(ctx.exception))

    def test_whitespace_query_raises_error(self):
        """Whitespace-only query raises QueryError"""
        mock_pipeline = MagicMock()

        with self.assertRaises(QueryError) as ctx:
            search(mock_pipeline, "   ")

        self.assertIn("Empty query", str(ctx.exception))

    def test_successful_search(self):
        """Successful search returns SearchResponse"""
        # Create mock documents
        mock_doc = MagicMock()
        mock_doc.content = "Test content"
        mock_doc.score = 0.95
        mock_doc.meta = {
            "file_path": "/test/doc.md",
            "title": "Test Doc",
            "vault": "engineering",
            "position": 0,
        }

        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc]},
        }

        response = search(mock_pipeline, "test query")

        self.assertIsInstance(response, SearchResponse)
        self.assertEqual(response.query, "test query")
        self.assertEqual(response.total, 1)
        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.results[0].content, "Test content")
        self.assertEqual(response.results[0].score, 0.95)

    def test_search_with_filters(self):
        """Search passes filters to pipeline"""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {"retriever": {"documents": []}}

        filters = QueryFilters(vaults=["engineering"])
        response = search(mock_pipeline, "test query", filters=filters)

        # Check pipeline was called with filters
        call_args = mock_pipeline.run.call_args[0][0]
        self.assertIn("retriever", call_args)
        self.assertIsNotNone(call_args["retriever"]["filters"])

    def test_search_with_top_k(self):
        """Search passes top_k to pipeline"""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {"retriever": {"documents": []}}

        response = search(mock_pipeline, "test query", top_k=10)

        # Check pipeline was called with top_k
        call_args = mock_pipeline.run.call_args[0][0]
        self.assertEqual(call_args["retriever"]["top_k"], 10)

    def test_search_pipeline_error(self):
        """Pipeline error is wrapped in QueryError"""
        mock_pipeline = MagicMock()
        mock_pipeline.run.side_effect = RuntimeError("Connection failed")

        with self.assertRaises(QueryError) as ctx:
            search(mock_pipeline, "test query")

        self.assertIn("Search failed", str(ctx.exception))
        self.assertIn("Connection failed", str(ctx.exception))

    def test_search_handles_missing_metadata(self):
        """Search handles documents with missing metadata"""
        mock_doc = MagicMock()
        mock_doc.content = "Content"
        mock_doc.score = 0.8
        mock_doc.meta = {}  # Empty metadata

        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc]},
        }

        response = search(mock_pipeline, "test query")

        self.assertEqual(response.results[0].file_path, "")
        self.assertEqual(response.results[0].title, "")
        self.assertEqual(response.results[0].vault, "")

    def test_search_handles_none_score(self):
        """Search handles documents with None score"""
        mock_doc = MagicMock()
        mock_doc.content = "Content"
        mock_doc.score = None
        mock_doc.meta = {"title": "Test"}

        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc]},
        }

        response = search(mock_pipeline, "test query")

        self.assertEqual(response.results[0].score, 0.0)


class TestCreateQAPipeline(unittest.TestCase):
    """Tests for create_qa_pipeline function"""

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    @patch("src.rag.pipelines.query.PromptBuilder")
    @patch("src.rag.pipelines.query.OllamaGenerator")
    def test_pipeline_has_four_components(
        self,
        mock_generator_cls,
        mock_prompt_cls,
        mock_retriever_cls,
        mock_embedder_cls,
        mock_pipeline_cls,
    ):
        """Q&A pipeline adds four components"""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        pipeline = create_qa_pipeline(mock_store)

        # Check add_component calls
        add_calls = mock_pipeline.add_component.call_args_list
        self.assertEqual(len(add_calls), 4)

        component_names = [call[0][0] for call in add_calls]
        self.assertIn("embedder", component_names)
        self.assertIn("retriever", component_names)
        self.assertIn("prompt_builder", component_names)
        self.assertIn("generator", component_names)

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    @patch("src.rag.pipelines.query.PromptBuilder")
    @patch("src.rag.pipelines.query.OllamaGenerator")
    def test_pipeline_uses_config(
        self,
        mock_generator_cls,
        mock_prompt_cls,
        mock_retriever_cls,
        mock_embedder_cls,
        mock_pipeline_cls,
    ):
        """Q&A pipeline uses provided config"""
        mock_store = MagicMock()
        config = OllamaConfig(
            remote_url="http://remote:11434",
            local_url="http://local:11434",
            embedding_model="embed-model",
            llm_model="llm-model",
            embedding_timeout=30,
            llm_timeout=180,
            num_ctx=32768,
        )

        pipeline = create_qa_pipeline(mock_store, config)

        # Check embedder config (remote)
        embedder_kwargs = mock_embedder_cls.call_args[1]
        self.assertEqual(embedder_kwargs["url"], "http://remote:11434")
        self.assertEqual(embedder_kwargs["model"], "embed-model")

        # Check generator config (local)
        generator_kwargs = mock_generator_cls.call_args[1]
        self.assertEqual(generator_kwargs["url"], "http://local:11434")
        self.assertEqual(generator_kwargs["model"], "llm-model")
        self.assertEqual(generator_kwargs["timeout"], 180)
        self.assertEqual(generator_kwargs["generation_kwargs"]["num_ctx"], 32768)

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    @patch("src.rag.pipelines.query.PromptBuilder")
    @patch("src.rag.pipelines.query.OllamaGenerator")
    def test_pipeline_connects_components(
        self,
        mock_generator_cls,
        mock_prompt_cls,
        mock_retriever_cls,
        mock_embedder_cls,
        mock_pipeline_cls,
    ):
        """Q&A pipeline connects all components"""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        pipeline = create_qa_pipeline(mock_store)

        # Check connect calls
        connect_calls = mock_pipeline.connect.call_args_list
        self.assertEqual(len(connect_calls), 3)

        connections = [(call[0][0], call[0][1]) for call in connect_calls]
        self.assertIn(("embedder.embedding", "retriever.query_embedding"), connections)
        self.assertIn(("retriever.documents", "prompt_builder.documents"), connections)
        self.assertIn(("prompt_builder.prompt", "generator.prompt"), connections)

    @patch("src.rag.pipelines.query.Pipeline")
    @patch("src.rag.pipelines.query.OllamaTextEmbedder")
    @patch("src.rag.pipelines.query.QdrantEmbeddingRetriever")
    @patch("src.rag.pipelines.query.PromptBuilder")
    @patch("src.rag.pipelines.query.OllamaGenerator")
    def test_prompt_builder_uses_template(
        self,
        mock_generator_cls,
        mock_prompt_cls,
        mock_retriever_cls,
        mock_embedder_cls,
        mock_pipeline_cls,
    ):
        """Prompt builder is created with template"""
        mock_store = MagicMock()

        pipeline = create_qa_pipeline(mock_store)

        # Check PromptBuilder was called with template
        mock_prompt_cls.assert_called_once()
        call_kwargs = mock_prompt_cls.call_args[1]
        self.assertIn("template", call_kwargs)
        self.assertIn("コンテキスト", call_kwargs["template"])


class TestAsk(unittest.TestCase):
    """Tests for ask function"""

    def test_empty_question_raises_error(self):
        """Empty question raises QueryError"""
        mock_pipeline = MagicMock()

        with self.assertRaises(QueryError) as ctx:
            ask(mock_pipeline, "")

        self.assertIn("Empty question", str(ctx.exception))

    def test_whitespace_question_raises_error(self):
        """Whitespace-only question raises QueryError"""
        mock_pipeline = MagicMock()

        with self.assertRaises(QueryError) as ctx:
            ask(mock_pipeline, "   ")

        self.assertIn("Empty question", str(ctx.exception))

    def test_successful_ask(self):
        """Successful ask returns Answer"""
        # Create mock documents
        mock_doc = MagicMock()
        mock_doc.content = "Source content"
        mock_doc.score = 0.9
        mock_doc.meta = {
            "file_path": "/test/doc.md",
            "title": "Source Doc",
            "vault": "engineering",
            "position": 0,
        }

        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc]},
            "generator": {"replies": ["Generated answer text"]},
        }

        answer = ask(mock_pipeline, "What is Kubernetes?")

        self.assertIsInstance(answer, Answer)
        self.assertEqual(answer.text, "Generated answer text")
        self.assertEqual(len(answer.sources), 1)
        self.assertEqual(answer.sources[0].content, "Source content")
        self.assertEqual(answer.confidence, 0.9)

    def test_ask_with_filters(self):
        """Ask passes filters to pipeline"""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {
            "retriever": {"documents": []},
            "generator": {"replies": ["Answer"]},
        }

        filters = QueryFilters(vaults=["engineering"])
        answer = ask(mock_pipeline, "Question?", filters=filters)

        # Check pipeline was called with filters
        call_args = mock_pipeline.run.call_args[0][0]
        self.assertIsNotNone(call_args["retriever"]["filters"])

    def test_ask_with_top_k(self):
        """Ask passes top_k to pipeline"""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {
            "retriever": {"documents": []},
            "generator": {"replies": ["Answer"]},
        }

        answer = ask(mock_pipeline, "Question?", top_k=10)

        call_args = mock_pipeline.run.call_args[0][0]
        self.assertEqual(call_args["retriever"]["top_k"], 10)

    def test_ask_passes_question_to_prompt_builder(self):
        """Ask passes question to prompt builder"""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {
            "retriever": {"documents": []},
            "generator": {"replies": ["Answer"]},
        }

        ask(mock_pipeline, "What is Kubernetes?")

        call_args = mock_pipeline.run.call_args[0][0]
        self.assertEqual(call_args["prompt_builder"]["query"], "What is Kubernetes?")

    def test_ask_pipeline_error(self):
        """Pipeline error is wrapped in QueryError"""
        mock_pipeline = MagicMock()
        mock_pipeline.run.side_effect = RuntimeError("LLM error")

        with self.assertRaises(QueryError) as ctx:
            ask(mock_pipeline, "Question?")

        self.assertIn("Q&A failed", str(ctx.exception))
        self.assertIn("LLM error", str(ctx.exception))

    def test_ask_empty_replies(self):
        """Ask handles empty replies"""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {
            "retriever": {"documents": []},
            "generator": {"replies": []},
        }

        answer = ask(mock_pipeline, "Question?")

        self.assertEqual(answer.text, "")

    def test_ask_no_sources(self):
        """Ask with no sources has zero confidence"""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {
            "retriever": {"documents": []},
            "generator": {"replies": ["Answer without sources"]},
        }

        answer = ask(mock_pipeline, "Question?")

        self.assertEqual(answer.confidence, 0.0)
        self.assertEqual(len(answer.sources), 0)

    def test_ask_confidence_calculation(self):
        """Ask calculates confidence as average of source scores"""
        mock_doc1 = MagicMock()
        mock_doc1.content = "Content 1"
        mock_doc1.score = 0.8
        mock_doc1.meta = {"title": "Doc 1", "file_path": "", "vault": "", "position": 0}

        mock_doc2 = MagicMock()
        mock_doc2.content = "Content 2"
        mock_doc2.score = 0.6
        mock_doc2.meta = {"title": "Doc 2", "file_path": "", "vault": "", "position": 0}

        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = {
            "retriever": {"documents": [mock_doc1, mock_doc2]},
            "generator": {"replies": ["Answer"]},
        }

        answer = ask(mock_pipeline, "Question?")

        # Average of 0.8 and 0.6 = 0.7
        self.assertAlmostEqual(answer.confidence, 0.7, places=2)


if __name__ == "__main__":
    unittest.main()
