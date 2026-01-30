"""
Tests for Indexing Pipeline - scan_vault, chunk_document, create_indexing_pipeline, index_vault
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from haystack import Document as HaystackDocument

from src.rag.config import OllamaConfig, RAGConfig
from src.rag.exceptions import IndexingError
from src.rag.pipelines.indexing import (
    Document,
    DocumentMeta,
    IndexingResult,
    chunk_document,
    chunk_documents,
    create_indexing_pipeline,
    extract_metadata,
    index_vault,
    parse_frontmatter,
    scan_vault,
)


class TestParseFrontmatter(unittest.TestCase):
    """Tests for parse_frontmatter function"""

    def test_parse_valid_frontmatter(self):
        """Valid frontmatter is parsed correctly"""
        content = """---
title: Test Document
tags:
  - test
  - demo
normalized: true
---

# Content here
"""
        frontmatter, body = parse_frontmatter(content)

        self.assertEqual(frontmatter["title"], "Test Document")
        self.assertEqual(frontmatter["tags"], ["test", "demo"])
        self.assertTrue(frontmatter["normalized"])
        self.assertIn("# Content here", body)

    def test_parse_no_frontmatter(self):
        """Content without frontmatter returns empty dict"""
        content = "# Just content\n\nNo frontmatter here."
        frontmatter, body = parse_frontmatter(content)

        self.assertEqual(frontmatter, {})
        self.assertEqual(body, content)

    def test_parse_empty_frontmatter(self):
        """Empty frontmatter returns empty dict"""
        content = """---
---

Content after empty frontmatter.
"""
        frontmatter, body = parse_frontmatter(content)

        self.assertEqual(frontmatter, {})
        self.assertIn("Content after empty frontmatter", body)

    def test_parse_invalid_yaml(self):
        """Invalid YAML returns empty dict"""
        content = """---
invalid: yaml: content: here
  bad indentation
---

Content
"""
        frontmatter, body = parse_frontmatter(content)

        # Should handle gracefully
        self.assertIsInstance(frontmatter, dict)


class TestExtractMetadata(unittest.TestCase):
    """Tests for extract_metadata function"""

    def test_extract_full_metadata(self):
        """Full metadata is extracted correctly"""
        frontmatter = {
            "tags": ["tech", "python"],
            "created": "2024-01-15",
            "normalized": True,
            "file_id": "abc123",
        }

        meta = extract_metadata(frontmatter)

        self.assertEqual(meta.tags, ["tech", "python"])
        self.assertEqual(meta.created, "2024-01-15")
        self.assertTrue(meta.normalized)
        self.assertEqual(meta.file_id, "abc123")

    def test_extract_empty_metadata(self):
        """Empty frontmatter returns default metadata"""
        meta = extract_metadata({})

        self.assertEqual(meta.tags, [])
        self.assertEqual(meta.created, "")
        self.assertFalse(meta.normalized)
        self.assertEqual(meta.file_id, "")

    def test_extract_string_tag(self):
        """Single string tag is converted to list"""
        frontmatter = {"tags": "single-tag"}
        meta = extract_metadata(frontmatter)

        self.assertEqual(meta.tags, ["single-tag"])

    def test_extract_normalized_false_explicit(self):
        """Explicit normalized: false is handled"""
        frontmatter = {"normalized": False}
        meta = extract_metadata(frontmatter)

        self.assertFalse(meta.normalized)

    def test_extract_normalized_string_value(self):
        """String value for normalized is handled as non-True"""
        frontmatter = {"normalized": "yes"}
        meta = extract_metadata(frontmatter)

        self.assertFalse(meta.normalized)  # Not exactly True

    def test_extract_created_date_object(self):
        """Date object is converted to string"""
        from datetime import date

        frontmatter = {"created": date(2024, 1, 15)}
        meta = extract_metadata(frontmatter)

        self.assertEqual(meta.created, "2024-01-15")


class TestScanVault(unittest.TestCase):
    """Tests for scan_vault function"""

    def setUp(self):
        """Create temporary vault directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scan_empty_vault(self):
        """Empty vault returns empty list"""
        docs = scan_vault(self.vault_path, "test-vault")
        self.assertEqual(docs, [])

    def test_scan_non_existent_vault(self):
        """Non-existent vault raises IndexingError"""
        with self.assertRaises(IndexingError) as ctx:
            scan_vault(Path("/non/existent/path"), "test")

        self.assertIn("does not exist", str(ctx.exception))

    def test_scan_only_normalized_files(self):
        """Only normalized files are included"""
        # Create normalized file
        normalized = self.vault_path / "normalized.md"
        normalized.write_text(
            """---
title: Normalized Doc
normalized: true
---

This is normalized content.
"""
        )

        # Create non-normalized file
        non_normalized = self.vault_path / "non-normalized.md"
        non_normalized.write_text(
            """---
title: Non-Normalized Doc
normalized: false
---

This should be skipped.
"""
        )

        # Create file without frontmatter
        no_frontmatter = self.vault_path / "no-frontmatter.md"
        no_frontmatter.write_text("# Just content\n\nNo frontmatter.")

        docs = scan_vault(self.vault_path, "test-vault")

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, "Normalized Doc")
        self.assertEqual(docs[0].vault_name, "test-vault")

    def test_scan_nested_directories(self):
        """Files in nested directories are found"""
        subdir = self.vault_path / "subdir" / "nested"
        subdir.mkdir(parents=True)

        nested_file = subdir / "nested-doc.md"
        nested_file.write_text(
            """---
title: Nested Document
normalized: true
---

Nested content.
"""
        )

        docs = scan_vault(self.vault_path, "test-vault")

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, "Nested Document")

    def test_scan_extracts_metadata(self):
        """Metadata is correctly extracted"""
        md_file = self.vault_path / "doc.md"
        md_file.write_text(
            """---
title: Full Metadata Doc
tags:
  - python
  - testing
created: 2024-01-15
normalized: true
file_id: xyz789
---

Content here.
"""
        )

        docs = scan_vault(self.vault_path, "test-vault")

        self.assertEqual(len(docs), 1)
        doc = docs[0]
        self.assertEqual(doc.title, "Full Metadata Doc")
        self.assertEqual(doc.metadata.tags, ["python", "testing"])
        self.assertEqual(doc.metadata.created, "2024-01-15")
        self.assertEqual(doc.metadata.file_id, "xyz789")
        self.assertTrue(doc.metadata.normalized)

    def test_scan_uses_filename_as_title_fallback(self):
        """Filename is used as title if not in frontmatter"""
        md_file = self.vault_path / "my-document.md"
        md_file.write_text(
            """---
normalized: true
---

Content without title.
"""
        )

        docs = scan_vault(self.vault_path, "test-vault")

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, "my-document")

    def test_scan_content_excludes_frontmatter(self):
        """Document content excludes frontmatter"""
        md_file = self.vault_path / "doc.md"
        md_file.write_text(
            """---
title: Test
normalized: true
---

Body content only.
"""
        )

        docs = scan_vault(self.vault_path, "test-vault")

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].content, "Body content only.")
        self.assertNotIn("---", docs[0].content)


class TestChunkDocument(unittest.TestCase):
    """Tests for chunk_document function"""

    def test_chunk_short_document(self):
        """Short document produces single chunk"""
        doc = Document(
            file_path=Path("/test/doc.md"),
            title="Test Doc",
            content="This is a short document.",
            metadata=DocumentMeta(tags=["test"], created="2024-01-15"),
            vault_name="test-vault",
        )

        chunks = chunk_document(doc, chunk_size=512, overlap=50)

        self.assertEqual(len(chunks), 1)
        self.assertIsInstance(chunks[0], HaystackDocument)
        self.assertEqual(chunks[0].meta["position"], 0)

    def test_chunk_long_document(self):
        """Long document produces multiple chunks"""
        # Create content with many words
        words = ["word"] * 1000
        content = " ".join(words)

        doc = Document(
            file_path=Path("/test/doc.md"),
            title="Long Doc",
            content=content,
            metadata=DocumentMeta(),
            vault_name="test-vault",
        )

        chunks = chunk_document(doc, chunk_size=100, overlap=10)

        self.assertGreater(len(chunks), 1)

        # Each chunk should have position metadata
        for i, chunk in enumerate(chunks):
            self.assertEqual(chunk.meta["position"], i)

    def test_chunk_preserves_metadata(self):
        """Chunk metadata includes document metadata"""
        doc = Document(
            file_path=Path("/test/doc.md"),
            title="Meta Doc",
            content="Content with metadata.",
            metadata=DocumentMeta(
                tags=["tech", "python"],
                created="2024-01-15",
                file_id="abc123",
            ),
            vault_name="engineering",
        )

        chunks = chunk_document(doc)

        self.assertEqual(len(chunks), 1)
        meta = chunks[0].meta

        self.assertEqual(meta["file_path"], "/test/doc.md")
        self.assertEqual(meta["title"], "Meta Doc")
        self.assertEqual(meta["vault"], "engineering")
        self.assertEqual(meta["tags"], ["tech", "python"])
        self.assertEqual(meta["created"], "2024-01-15")
        self.assertEqual(meta["file_id"], "abc123")
        self.assertEqual(meta["position"], 0)

    def test_chunk_overlap(self):
        """Chunks have overlapping content"""
        # Create content with distinct words
        words = [f"word{i}" for i in range(200)]
        content = " ".join(words)

        doc = Document(
            file_path=Path("/test/doc.md"),
            title="Overlap Doc",
            content=content,
            metadata=DocumentMeta(),
            vault_name="test",
        )

        chunks = chunk_document(doc, chunk_size=50, overlap=10)

        if len(chunks) >= 2:
            # Check that chunks have some overlapping words
            chunk1_words = set(chunks[0].content.split())
            chunk2_words = set(chunks[1].content.split())
            overlap = chunk1_words & chunk2_words
            self.assertGreater(len(overlap), 0)


class TestChunkDocuments(unittest.TestCase):
    """Tests for chunk_documents function"""

    def test_chunk_multiple_documents(self):
        """Multiple documents are chunked correctly"""
        docs = [
            Document(
                file_path=Path(f"/test/doc{i}.md"),
                title=f"Doc {i}",
                content=f"Content for document {i}.",
                metadata=DocumentMeta(),
                vault_name="test",
            )
            for i in range(3)
        ]

        chunks = chunk_documents(docs)

        self.assertEqual(len(chunks), 3)

    def test_chunk_uses_config(self):
        """Custom config is used for chunking"""
        config = RAGConfig(chunk_size=10, chunk_overlap=2)

        # Create document with many words
        words = ["word"] * 50
        content = " ".join(words)

        docs = [
            Document(
                file_path=Path("/test/doc.md"),
                title="Test",
                content=content,
                metadata=DocumentMeta(),
                vault_name="test",
            )
        ]

        chunks = chunk_documents(docs, config=config)

        # Should produce multiple chunks with small chunk size
        self.assertGreater(len(chunks), 1)


class TestCreateIndexingPipeline(unittest.TestCase):
    """Tests for create_indexing_pipeline function"""

    @patch("src.rag.pipelines.indexing.Pipeline")
    @patch("src.rag.pipelines.indexing.OllamaDocumentEmbedder")
    @patch("src.rag.pipelines.indexing.DocumentWriter")
    def test_pipeline_has_components(self, mock_writer_cls, mock_embedder_cls, mock_pipeline_cls):
        """Pipeline adds embedder and writer components"""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        pipeline = create_indexing_pipeline(mock_store)

        # Check add_component calls
        add_calls = mock_pipeline.add_component.call_args_list
        self.assertEqual(len(add_calls), 2)
        self.assertEqual(add_calls[0][0][0], "embedder")
        self.assertEqual(add_calls[1][0][0], "writer")

    @patch("src.rag.pipelines.indexing.Pipeline")
    @patch("src.rag.pipelines.indexing.OllamaDocumentEmbedder")
    @patch("src.rag.pipelines.indexing.DocumentWriter")
    def test_pipeline_uses_config(self, mock_writer_cls, mock_embedder_cls, mock_pipeline_cls):
        """Pipeline uses provided config"""
        mock_store = MagicMock()
        config = OllamaConfig(
            remote_url="http://custom:11434",
            embedding_model="custom-model",
            embedding_timeout=60,
        )

        pipeline = create_indexing_pipeline(mock_store, config)

        mock_embedder_cls.assert_called_once_with(
            url="http://custom:11434",
            model="custom-model",
            timeout=60,
        )

    @patch("src.rag.pipelines.indexing.Pipeline")
    @patch("src.rag.pipelines.indexing.OllamaDocumentEmbedder")
    @patch("src.rag.pipelines.indexing.DocumentWriter")
    def test_pipeline_uses_default_config(self, mock_writer_cls, mock_embedder_cls, mock_pipeline_cls):
        """Pipeline uses default config when not provided"""
        mock_store = MagicMock()

        pipeline = create_indexing_pipeline(mock_store)

        # Should use default ollama_config values
        call_kwargs = mock_embedder_cls.call_args[1]
        self.assertEqual(call_kwargs["url"], "http://ollama-server.local:11434")
        self.assertEqual(call_kwargs["model"], "bge-m3")

    @patch("src.rag.pipelines.indexing.Pipeline")
    @patch("src.rag.pipelines.indexing.OllamaDocumentEmbedder")
    @patch("src.rag.pipelines.indexing.DocumentWriter")
    def test_pipeline_connects_components(self, mock_writer_cls, mock_embedder_cls, mock_pipeline_cls):
        """Pipeline connects embedder to writer"""
        mock_store = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        pipeline = create_indexing_pipeline(mock_store)

        # Check connect call
        mock_pipeline.connect.assert_called_once_with("embedder.documents", "writer.documents")


class TestIndexVault(unittest.TestCase):
    """Tests for index_vault function"""

    def setUp(self):
        """Create temporary vault directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_index_empty_vault(self):
        """Empty vault returns zero counts"""
        mock_pipeline = MagicMock()

        result = index_vault(mock_pipeline, self.vault_path, "test-vault")

        self.assertEqual(result.total_docs, 0)
        self.assertEqual(result.indexed_docs, 0)
        self.assertEqual(result.total_chunks, 0)
        self.assertEqual(result.errors, [])

    def test_index_non_existent_vault(self):
        """Non-existent vault raises IndexingError"""
        mock_pipeline = MagicMock()

        with self.assertRaises(IndexingError):
            index_vault(mock_pipeline, Path("/non/existent"), "test")

    def test_index_vault_counts(self):
        """Indexing returns correct counts"""
        # Create test files
        for i in range(3):
            md_file = self.vault_path / f"doc{i}.md"
            md_file.write_text(
                f"""---
title: Document {i}
normalized: true
---

Content for document {i}.
"""
            )

        mock_pipeline = MagicMock()
        result = index_vault(mock_pipeline, self.vault_path, "test-vault")

        self.assertEqual(result.total_docs, 3)
        self.assertEqual(result.indexed_docs, 3)
        self.assertGreaterEqual(result.total_chunks, 3)
        self.assertEqual(result.errors, [])

    def test_index_vault_dry_run(self):
        """Dry run does not call pipeline"""
        md_file = self.vault_path / "doc.md"
        md_file.write_text(
            """---
title: Test Doc
normalized: true
---

Content here.
"""
        )

        mock_pipeline = MagicMock()
        result = index_vault(
            mock_pipeline, self.vault_path, "test-vault", dry_run=True
        )

        self.assertEqual(result.total_docs, 1)
        self.assertEqual(result.indexed_docs, 1)
        self.assertGreaterEqual(result.total_chunks, 1)
        mock_pipeline.run.assert_not_called()

    def test_index_vault_calls_pipeline(self):
        """Indexing calls pipeline with chunks"""
        md_file = self.vault_path / "doc.md"
        md_file.write_text(
            """---
title: Test Doc
normalized: true
---

Content to be indexed.
"""
        )

        mock_pipeline = MagicMock()
        result = index_vault(
            mock_pipeline, self.vault_path, "test-vault", dry_run=False
        )

        mock_pipeline.run.assert_called_once()
        call_args = mock_pipeline.run.call_args[0][0]
        self.assertIn("embedder", call_args)
        self.assertIn("documents", call_args["embedder"])

    def test_index_vault_pipeline_error(self):
        """Pipeline error is captured in result"""
        md_file = self.vault_path / "doc.md"
        md_file.write_text(
            """---
title: Test Doc
normalized: true
---

Content.
"""
        )

        mock_pipeline = MagicMock()
        mock_pipeline.run.side_effect = RuntimeError("Connection failed")

        result = index_vault(mock_pipeline, self.vault_path, "test-vault")

        self.assertEqual(result.indexed_docs, 0)
        self.assertGreater(len(result.errors), 0)
        self.assertIn("Connection failed", result.errors[0])

    def test_index_vault_only_normalized(self):
        """Only normalized files are indexed"""
        # Normalized file
        normalized = self.vault_path / "normalized.md"
        normalized.write_text(
            """---
title: Normalized
normalized: true
---

Include this.
"""
        )

        # Non-normalized file
        non_normalized = self.vault_path / "non-normalized.md"
        non_normalized.write_text(
            """---
title: Non-Normalized
normalized: false
---

Skip this.
"""
        )

        mock_pipeline = MagicMock()
        result = index_vault(
            mock_pipeline, self.vault_path, "test-vault", dry_run=True
        )

        self.assertEqual(result.total_docs, 1)


class TestIndexingResult(unittest.TestCase):
    """Tests for IndexingResult dataclass"""

    def test_default_errors_list(self):
        """Default errors is empty list"""
        result = IndexingResult(total_docs=5, indexed_docs=5, total_chunks=10)
        self.assertEqual(result.errors, [])

    def test_errors_preserved(self):
        """Errors list is preserved"""
        errors = ["Error 1", "Error 2"]
        result = IndexingResult(
            total_docs=5, indexed_docs=3, total_chunks=6, errors=errors
        )
        self.assertEqual(result.errors, errors)


if __name__ == "__main__":
    unittest.main()
