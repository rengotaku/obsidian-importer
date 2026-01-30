"""
Tests for Qdrant Document Store module

All Qdrant operations are mocked - no running Qdrant server required.
"""
import unittest
from unittest.mock import MagicMock, patch


class TestGetDocumentStore(unittest.TestCase):
    """get_document_store() tests"""

    @patch("src.rag.stores.qdrant.QdrantDocumentStore")
    @patch("src.rag.stores.qdrant.QDRANT_PATH")
    def test_returns_qdrant_document_store(self, mock_path, mock_store_class):
        """Returns QdrantDocumentStore instance"""
        from src.rag.stores.qdrant import get_document_store

        mock_path.mkdir = MagicMock()
        mock_store = MagicMock()
        mock_store_class.return_value = mock_store

        result = get_document_store()

        self.assertEqual(result, mock_store)
        mock_store_class.assert_called_once()

    @patch("src.rag.stores.qdrant.QdrantDocumentStore")
    @patch("src.rag.stores.qdrant.QDRANT_PATH")
    def test_uses_default_config(self, mock_path, mock_store_class):
        """Uses default RAGConfig when config is None"""
        from src.rag.stores.qdrant import get_document_store

        mock_path.mkdir = MagicMock()
        mock_path.__str__ = MagicMock(return_value="/data/qdrant")
        mock_store_class.return_value = MagicMock()

        get_document_store(config=None)

        call_kwargs = mock_store_class.call_args[1]
        # Default config has embedding_dim=1024
        self.assertEqual(call_kwargs["embedding_dim"], 1024)

    @patch("src.rag.stores.qdrant.QdrantDocumentStore")
    @patch("src.rag.stores.qdrant.QDRANT_PATH")
    def test_uses_custom_config(self, mock_path, mock_store_class):
        """Uses provided RAGConfig"""
        from src.rag.config import RAGConfig
        from src.rag.stores.qdrant import get_document_store

        mock_path.mkdir = MagicMock()
        mock_path.__str__ = MagicMock(return_value="/data/qdrant")
        mock_store_class.return_value = MagicMock()

        custom_config = RAGConfig(embedding_dim=768)
        get_document_store(config=custom_config)

        call_kwargs = mock_store_class.call_args[1]
        self.assertEqual(call_kwargs["embedding_dim"], 768)

    @patch("src.rag.stores.qdrant.QdrantDocumentStore")
    @patch("src.rag.stores.qdrant.QDRANT_PATH")
    def test_collection_name(self, mock_path, mock_store_class):
        """Uses correct collection name (obsidian_knowledge)"""
        from src.rag.stores.qdrant import COLLECTION_NAME, get_document_store

        mock_path.mkdir = MagicMock()
        mock_path.__str__ = MagicMock(return_value="/data/qdrant")
        mock_store_class.return_value = MagicMock()

        get_document_store()

        call_kwargs = mock_store_class.call_args[1]
        self.assertEqual(call_kwargs["index"], COLLECTION_NAME)
        self.assertEqual(COLLECTION_NAME, "obsidian_knowledge")

    @patch("src.rag.stores.qdrant.QdrantDocumentStore")
    @patch("src.rag.stores.qdrant.QDRANT_PATH")
    def test_cosine_similarity(self, mock_path, mock_store_class):
        """Uses cosine similarity metric"""
        from src.rag.stores.qdrant import get_document_store

        mock_path.mkdir = MagicMock()
        mock_path.__str__ = MagicMock(return_value="/data/qdrant")
        mock_store_class.return_value = MagicMock()

        get_document_store()

        call_kwargs = mock_store_class.call_args[1]
        self.assertEqual(call_kwargs["similarity"], "cosine")

    @patch("src.rag.stores.qdrant.QdrantDocumentStore")
    @patch("src.rag.stores.qdrant.QDRANT_PATH")
    def test_local_persistence_path(self, mock_path, mock_store_class):
        """Uses local file path for persistence"""
        from src.rag.stores.qdrant import get_document_store

        mock_path.mkdir = MagicMock()
        mock_path.__str__ = MagicMock(return_value="/path/to/project/data/qdrant")
        mock_store_class.return_value = MagicMock()

        get_document_store()

        call_kwargs = mock_store_class.call_args[1]
        self.assertIn("qdrant", call_kwargs["path"])

    @patch("src.rag.stores.qdrant.QdrantDocumentStore")
    @patch("src.rag.stores.qdrant.QDRANT_PATH")
    def test_creates_data_directory(self, mock_path, mock_store_class):
        """Creates data directory if not exists"""
        from src.rag.stores.qdrant import get_document_store

        mock_path.mkdir = MagicMock()
        mock_store_class.return_value = MagicMock()

        get_document_store()

        mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("src.rag.stores.qdrant.QdrantDocumentStore")
    @patch("src.rag.stores.qdrant.QDRANT_PATH")
    def test_recreate_index_false(self, mock_path, mock_store_class):
        """Does not recreate index by default"""
        from src.rag.stores.qdrant import get_document_store

        mock_path.mkdir = MagicMock()
        mock_store_class.return_value = MagicMock()

        get_document_store()

        call_kwargs = mock_store_class.call_args[1]
        self.assertFalse(call_kwargs["recreate_index"])

    @patch("src.rag.stores.qdrant.QdrantDocumentStore")
    @patch("src.rag.stores.qdrant.QDRANT_PATH")
    def test_return_embedding_false(self, mock_path, mock_store_class):
        """Does not return embeddings in queries by default"""
        from src.rag.stores.qdrant import get_document_store

        mock_path.mkdir = MagicMock()
        mock_store_class.return_value = MagicMock()

        get_document_store()

        call_kwargs = mock_store_class.call_args[1]
        self.assertFalse(call_kwargs["return_embedding"])


class TestGetCollectionStats(unittest.TestCase):
    """get_collection_stats() tests"""

    def test_returns_document_count(self):
        """Returns document count from store"""
        from src.rag.stores.qdrant import get_collection_stats

        mock_store = MagicMock()
        mock_store.count_documents.return_value = 42
        mock_store.embedding_dim = 1024
        mock_store.similarity = "cosine"

        stats = get_collection_stats(mock_store)

        self.assertEqual(stats["document_count"], 42)

    def test_returns_collection_name(self):
        """Returns collection name"""
        from src.rag.stores.qdrant import COLLECTION_NAME, get_collection_stats

        mock_store = MagicMock()
        mock_store.count_documents.return_value = 0
        mock_store.embedding_dim = 1024
        mock_store.similarity = "cosine"

        stats = get_collection_stats(mock_store)

        self.assertEqual(stats["collection_name"], COLLECTION_NAME)

    def test_returns_embedding_dim(self):
        """Returns embedding dimension from store"""
        from src.rag.stores.qdrant import get_collection_stats

        mock_store = MagicMock()
        mock_store.count_documents.return_value = 0
        mock_store.embedding_dim = 1024
        mock_store.similarity = "cosine"

        stats = get_collection_stats(mock_store)

        self.assertEqual(stats["embedding_dim"], 1024)

    def test_returns_similarity_metric(self):
        """Returns similarity metric from store"""
        from src.rag.stores.qdrant import get_collection_stats

        mock_store = MagicMock()
        mock_store.count_documents.return_value = 0
        mock_store.embedding_dim = 1024
        mock_store.similarity = "cosine"

        stats = get_collection_stats(mock_store)

        self.assertEqual(stats["similarity"], "cosine")

    def test_empty_collection(self):
        """Handles empty collection correctly"""
        from src.rag.stores.qdrant import get_collection_stats

        mock_store = MagicMock()
        mock_store.count_documents.return_value = 0
        mock_store.embedding_dim = 1024
        mock_store.similarity = "cosine"

        stats = get_collection_stats(mock_store)

        self.assertEqual(stats["document_count"], 0)

    def test_calls_count_documents(self):
        """Calls count_documents() on store"""
        from src.rag.stores.qdrant import get_collection_stats

        mock_store = MagicMock()
        mock_store.count_documents.return_value = 100
        mock_store.embedding_dim = 1024
        mock_store.similarity = "cosine"

        get_collection_stats(mock_store)

        mock_store.count_documents.assert_called_once()


class TestImportFromPackage(unittest.TestCase):
    """Test imports from package level"""

    def test_import_from_stores_package(self):
        """Functions can be imported from stores package"""
        from src.rag.stores import (
            COLLECTION_NAME,
            get_collection_stats,
            get_document_store,
        )

        self.assertTrue(callable(get_document_store))
        self.assertTrue(callable(get_collection_stats))
        self.assertEqual(COLLECTION_NAME, "obsidian_knowledge")


if __name__ == "__main__":
    unittest.main()
