"""
E2E Tests for Indexing Pipeline

Tests the complete indexing flow from vault scanning to document store.
Uses tempfile for test fixtures and mocks external services.
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.rag.config import RAGConfig
from src.rag.pipelines.indexing import (
    Document,
    DocumentMeta,
    IndexingResult,
    chunk_documents,
    create_indexing_pipeline,
    index_all_vaults,
    index_vault,
    scan_vault,
)


class TestE2EIndexing(unittest.TestCase):
    """E2E tests for indexing pipeline."""

    @classmethod
    def setUpClass(cls):
        """Create temp vault with test fixtures."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.vaults_dir = Path(cls.temp_dir) / "Vaults"
        cls.vaults_dir.mkdir()

        # Create test vault: エンジニア
        cls.engineer_vault = cls.vaults_dir / "エンジニア"
        cls.engineer_vault.mkdir()

        # Create normalized markdown files
        cls._create_test_file(
            cls.engineer_vault / "kubernetes.md",
            title="Kubernetes基礎",
            content="Kubernetes はコンテナオーケストレーションプラットフォームです。Pod、Service、Deployment などのリソースを管理します。",
            tags=["kubernetes", "container"],
            normalized=True,
        )

        cls._create_test_file(
            cls.engineer_vault / "docker.md",
            title="Docker入門",
            content="Docker はコンテナ技術の代表的な実装です。イメージとコンテナの概念を理解することが重要です。",
            tags=["docker", "container"],
            normalized=True,
        )

        # Create non-normalized file (should be skipped)
        cls._create_test_file(
            cls.engineer_vault / "draft.md",
            title="Draft Document",
            content="This is a draft and should not be indexed.",
            tags=["draft"],
            normalized=False,
        )

        # Create nested directory with file
        subdir = cls.engineer_vault / "advanced"
        subdir.mkdir()
        cls._create_test_file(
            subdir / "helm.md",
            title="Helm Charts",
            content="Helm は Kubernetes のパッケージマネージャーです。Charts を使ってアプリケーションをデプロイできます。",
            tags=["kubernetes", "helm"],
            normalized=True,
        )

        # Create second vault: ビジネス
        cls.business_vault = cls.vaults_dir / "ビジネス"
        cls.business_vault.mkdir()

        cls._create_test_file(
            cls.business_vault / "management.md",
            title="マネジメント基礎",
            content="マネジメントとは組織を効果的に運営するためのスキルです。",
            tags=["management"],
            normalized=True,
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    @staticmethod
    def _create_test_file(
        path: Path,
        title: str,
        content: str,
        tags: list[str],
        normalized: bool,
    ) -> None:
        """Helper to create test markdown files."""
        tags_yaml = "\n".join(f"  - {tag}" for tag in tags)
        file_content = f"""---
title: {title}
tags:
{tags_yaml}
normalized: {str(normalized).lower()}
created: 2024-01-15
---

{content}
"""
        path.write_text(file_content, encoding="utf-8")

    def test_scan_vault_finds_normalized_files(self):
        """Vault scan finds all normalized files."""
        docs = scan_vault(self.engineer_vault, "エンジニア")

        # Should find 3 normalized files (kubernetes, docker, helm)
        self.assertEqual(len(docs), 3)

        # Check titles
        titles = {doc.title for doc in docs}
        self.assertIn("Kubernetes基礎", titles)
        self.assertIn("Docker入門", titles)
        self.assertIn("Helm Charts", titles)

        # Should NOT include draft
        self.assertNotIn("Draft Document", titles)

    def test_scan_vault_extracts_metadata(self):
        """Vault scan extracts correct metadata."""
        docs = scan_vault(self.engineer_vault, "エンジニア")

        k8s_doc = next(d for d in docs if d.title == "Kubernetes基礎")

        self.assertEqual(k8s_doc.vault_name, "エンジニア")
        self.assertEqual(k8s_doc.metadata.tags, ["kubernetes", "container"])
        self.assertEqual(k8s_doc.metadata.created, "2024-01-15")
        self.assertTrue(k8s_doc.metadata.normalized)

    def test_chunk_documents_creates_haystack_docs(self):
        """Chunking creates Haystack documents with metadata."""
        docs = scan_vault(self.engineer_vault, "エンジニア")
        config = RAGConfig(chunk_size=512, chunk_overlap=50)

        chunks = chunk_documents(docs, config=config)

        # All docs are short, should have 3 chunks (one per doc)
        self.assertEqual(len(chunks), 3)

        # Each chunk should have metadata
        for chunk in chunks:
            self.assertIn("file_path", chunk.meta)
            self.assertIn("title", chunk.meta)
            self.assertIn("vault", chunk.meta)
            self.assertIn("tags", chunk.meta)
            self.assertIn("position", chunk.meta)

    def test_index_vault_dry_run(self):
        """Index vault dry run returns correct counts without calling pipeline."""
        mock_pipeline = MagicMock()

        result = index_vault(
            mock_pipeline,
            self.engineer_vault,
            "エンジニア",
            dry_run=True,
        )

        self.assertIsInstance(result, IndexingResult)
        self.assertEqual(result.total_docs, 3)
        self.assertEqual(result.indexed_docs, 3)
        self.assertGreaterEqual(result.total_chunks, 3)
        self.assertEqual(result.errors, [])

        # Pipeline should NOT be called in dry_run
        mock_pipeline.run.assert_not_called()

    def test_index_vault_respects_normalized_filter(self):
        """Only normalized=true files are indexed."""
        mock_pipeline = MagicMock()

        result = index_vault(
            mock_pipeline,
            self.engineer_vault,
            "エンジニア",
            dry_run=True,
        )

        # 3 normalized files, 1 non-normalized (draft)
        self.assertEqual(result.total_docs, 3)

    def test_index_all_vaults_dry_run(self):
        """Index all vaults processes multiple vaults."""
        mock_pipeline = MagicMock()

        results = index_all_vaults(
            mock_pipeline,
            vaults_dir=self.vaults_dir,
            vault_names=["エンジニア", "ビジネス"],
            dry_run=True,
        )

        self.assertIn("エンジニア", results)
        self.assertIn("ビジネス", results)

        self.assertEqual(results["エンジニア"].total_docs, 3)
        self.assertEqual(results["ビジネス"].total_docs, 1)

    def test_index_vault_calls_pipeline(self):
        """Index vault calls pipeline with correct data."""
        mock_pipeline = MagicMock()

        result = index_vault(
            mock_pipeline,
            self.engineer_vault,
            "エンジニア",
            dry_run=False,
        )

        # Pipeline should be called
        mock_pipeline.run.assert_called_once()

        # Check call arguments
        call_args = mock_pipeline.run.call_args[0][0]
        self.assertIn("embedder", call_args)
        self.assertIn("documents", call_args["embedder"])

        # Should have chunks
        documents = call_args["embedder"]["documents"]
        self.assertEqual(len(documents), 3)

    def test_index_vault_handles_pipeline_error(self):
        """Pipeline errors are captured in result."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.side_effect = RuntimeError("Connection timeout")

        result = index_vault(
            mock_pipeline,
            self.engineer_vault,
            "エンジニア",
            dry_run=False,
        )

        self.assertEqual(result.indexed_docs, 0)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("Connection timeout", result.errors[0])

    @patch("src.rag.pipelines.indexing.Pipeline")
    @patch("src.rag.pipelines.indexing.OllamaDocumentEmbedder")
    @patch("src.rag.pipelines.indexing.DocumentWriter")
    def test_create_indexing_pipeline_structure(
        self, mock_writer_cls, mock_embedder_cls, mock_pipeline_cls
    ):
        """Indexing pipeline has correct structure."""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        pipeline = create_indexing_pipeline(mock_store)

        # Embedder should be configured
        mock_embedder_cls.assert_called_once()
        call_kwargs = mock_embedder_cls.call_args[1]
        self.assertEqual(call_kwargs["model"], "bge-m3")

        # Writer should use the store
        mock_writer_cls.assert_called_once_with(document_store=mock_store)

    def test_index_empty_vault(self):
        """Empty vault returns zero counts."""
        empty_vault = self.vaults_dir / "empty"
        empty_vault.mkdir()

        mock_pipeline = MagicMock()
        result = index_vault(mock_pipeline, empty_vault, "empty")

        self.assertEqual(result.total_docs, 0)
        self.assertEqual(result.indexed_docs, 0)
        self.assertEqual(result.total_chunks, 0)

        # Clean up
        empty_vault.rmdir()

    def test_index_all_vaults_missing_vault(self):
        """Missing vault is handled gracefully."""
        mock_pipeline = MagicMock()

        results = index_all_vaults(
            mock_pipeline,
            vaults_dir=self.vaults_dir,
            vault_names=["エンジニア", "存在しないVault"],
            dry_run=True,
        )

        self.assertIn("エンジニア", results)
        self.assertIn("存在しないVault", results)

        self.assertEqual(results["エンジニア"].total_docs, 3)
        self.assertGreater(len(results["存在しないVault"].errors), 0)


class TestE2EIndexingWithJapaneseContent(unittest.TestCase):
    """E2E tests for indexing Japanese content."""

    def setUp(self):
        """Create temp vault with Japanese content."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir)

        # Create file with Japanese content
        self._create_file(
            "日本語テスト.md",
            title="日本語ドキュメント",
            content="これは日本語のテストドキュメントです。UTF-8エンコーディングが正しく処理されることを確認します。",
            tags=["日本語", "テスト"],
        )

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_file(
        self, filename: str, title: str, content: str, tags: list[str]
    ) -> None:
        tags_yaml = "\n".join(f"  - {tag}" for tag in tags)
        file_content = f"""---
title: {title}
tags:
{tags_yaml}
normalized: true
---

{content}
"""
        (self.vault_path / filename).write_text(file_content, encoding="utf-8")

    def test_japanese_filename_and_content(self):
        """Japanese filenames and content are handled correctly."""
        docs = scan_vault(self.vault_path, "テスト")

        self.assertEqual(len(docs), 1)
        doc = docs[0]

        self.assertEqual(doc.title, "日本語ドキュメント")
        self.assertIn("日本語", doc.metadata.tags)
        self.assertIn("UTF-8エンコーディング", doc.content)


if __name__ == "__main__":
    unittest.main()
