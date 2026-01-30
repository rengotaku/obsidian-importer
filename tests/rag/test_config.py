"""
Tests for RAG Configuration module
"""
import unittest
from pathlib import Path


class TestOllamaConfig(unittest.TestCase):
    """OllamaConfig dataclass tests"""

    def test_default_values(self):
        """Default values match spec"""
        from src.rag.config import OllamaConfig

        config = OllamaConfig()

        self.assertEqual(config.local_url, "http://localhost:11434")
        self.assertEqual(config.remote_url, "http://ollama-server.local:11434")
        self.assertEqual(config.embedding_model, "bge-m3")
        self.assertEqual(config.llm_model, "gpt-oss:20b")
        self.assertEqual(config.embedding_timeout, 30)
        self.assertEqual(config.llm_timeout, 120)
        self.assertEqual(config.num_ctx, 65536)

    def test_custom_values(self):
        """Custom values can be set"""
        from src.rag.config import OllamaConfig

        config = OllamaConfig(
            local_url="http://custom:11434",
            embedding_model="custom-model",
        )

        self.assertEqual(config.local_url, "http://custom:11434")
        self.assertEqual(config.embedding_model, "custom-model")
        # Default values still work
        self.assertEqual(config.remote_url, "http://ollama-server.local:11434")


class TestRAGConfig(unittest.TestCase):
    """RAGConfig dataclass tests"""

    def test_default_values(self):
        """Default values match spec"""
        from src.rag.config import RAGConfig

        config = RAGConfig()

        self.assertEqual(config.chunk_size, 512)
        self.assertEqual(config.chunk_overlap, 50)
        self.assertEqual(config.top_k, 5)
        self.assertEqual(config.similarity_threshold, 0.5)
        self.assertEqual(config.embedding_dim, 1024)
        self.assertEqual(
            config.target_vaults,
            ["エンジニア", "ビジネス", "経済", "日常", "その他"],
        )

    def test_target_vaults_independent(self):
        """Each instance has independent target_vaults list"""
        from src.rag.config import RAGConfig

        config1 = RAGConfig()
        config2 = RAGConfig()

        config1.target_vaults.append("テスト")

        self.assertIn("テスト", config1.target_vaults)
        self.assertNotIn("テスト", config2.target_vaults)


class TestPathConstants(unittest.TestCase):
    """Path constant tests"""

    def test_base_paths_exist(self):
        """Path constants are defined"""
        from src.rag.config import BASE_DIR, DATA_DIR, QDRANT_PATH, VAULTS_DIR

        self.assertIsInstance(BASE_DIR, Path)
        self.assertIsInstance(DATA_DIR, Path)
        self.assertIsInstance(QDRANT_PATH, Path)
        self.assertIsInstance(VAULTS_DIR, Path)

    def test_path_hierarchy(self):
        """Path hierarchy is correct"""
        from src.rag.config import BASE_DIR, DATA_DIR, QDRANT_PATH, VAULTS_DIR

        self.assertEqual(DATA_DIR, BASE_DIR / "data")
        self.assertEqual(QDRANT_PATH, DATA_DIR / "qdrant")
        self.assertEqual(VAULTS_DIR, BASE_DIR / "Vaults")


class TestDefaultInstances(unittest.TestCase):
    """Default config instance tests"""

    def test_default_instances_exist(self):
        """Default instances are created"""
        from src.rag.config import OllamaConfig, RAGConfig, ollama_config, rag_config

        self.assertIsInstance(ollama_config, OllamaConfig)
        self.assertIsInstance(rag_config, RAGConfig)


if __name__ == "__main__":
    unittest.main()
