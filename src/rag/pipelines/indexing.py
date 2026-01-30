"""
Indexing Pipeline - Vault ドキュメントのスキャン・チャンキング・インデックス作成
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from haystack import Document as HaystackDocument
from haystack import Pipeline
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack_integrations.components.embedders.ollama import OllamaDocumentEmbedder
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from src.rag.config import OllamaConfig, RAGConfig, VAULTS_DIR, ollama_config, rag_config
from src.rag.exceptions import IndexingError

if TYPE_CHECKING:
    pass


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class DocumentMeta:
    """Document metadata from frontmatter"""

    tags: list[str] = field(default_factory=list)
    created: str = ""
    normalized: bool = False
    file_id: str = ""


@dataclass
class Document:
    """Parsed document from vault"""

    file_path: Path
    title: str
    content: str
    metadata: DocumentMeta
    vault_name: str


@dataclass
class IndexingResult:
    """Result of indexing operation"""

    total_docs: int
    indexed_docs: int
    total_chunks: int
    errors: list[str] = field(default_factory=list)


# =============================================================================
# Frontmatter Parsing
# =============================================================================

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown content with potential frontmatter.

    Returns:
        Tuple of (frontmatter dict, body content without frontmatter).
        Returns empty dict if no frontmatter found.
    """
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content

    try:
        frontmatter_str = match.group(1)
        frontmatter = yaml.safe_load(frontmatter_str) or {}
        body = content[match.end() :]
        return frontmatter, body
    except yaml.YAMLError:
        return {}, content


def extract_metadata(frontmatter: dict) -> DocumentMeta:
    """
    Extract DocumentMeta from frontmatter dict.

    Args:
        frontmatter: Parsed YAML frontmatter.

    Returns:
        DocumentMeta instance.
    """
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    created = frontmatter.get("created", "")
    if created and not isinstance(created, str):
        created = str(created)

    return DocumentMeta(
        tags=tags or [],
        created=created,
        normalized=frontmatter.get("normalized", False) is True,
        file_id=frontmatter.get("file_id", ""),
    )


# =============================================================================
# Vault Scanning
# =============================================================================


def scan_vault(vault_path: Path, vault_name: str) -> list[Document]:
    """
    Scan vault for normalized markdown files.

    Only includes files with `normalized: true` in frontmatter.

    Args:
        vault_path: Path to vault directory.
        vault_name: Name of the vault (e.g., "エンジニア").

    Returns:
        List of Document objects for normalized files.

    Raises:
        IndexingError: If vault path does not exist.
    """
    if not vault_path.exists():
        raise IndexingError(
            f"Vault path does not exist: {vault_path}",
            file_path=str(vault_path),
            stage="scan",
        )

    documents: list[Document] = []

    for md_file in vault_path.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            frontmatter, body = parse_frontmatter(content)
            metadata = extract_metadata(frontmatter)

            # Skip non-normalized files
            if not metadata.normalized:
                continue

            # Extract title from frontmatter or filename
            title = frontmatter.get("title", md_file.stem)

            doc = Document(
                file_path=md_file,
                title=title,
                content=body.strip(),
                metadata=metadata,
                vault_name=vault_name,
            )
            documents.append(doc)

        except Exception as e:
            # Skip files that cannot be read but log the error
            # In production, this could be logged
            continue

    return documents


# =============================================================================
# Chunking
# =============================================================================


def chunk_document(
    doc: Document, chunk_size: int = 512, overlap: int = 50
) -> list[HaystackDocument]:
    """
    Split document into chunks with metadata.

    Uses Haystack DocumentSplitter with word-based splitting.

    Args:
        doc: Document to chunk.
        chunk_size: Target chunk size in words (default: 512).
        overlap: Overlap between chunks in words (default: 50).

    Returns:
        List of Haystack Document objects with metadata.
    """
    # Create a Haystack document for splitting
    haystack_doc = HaystackDocument(
        content=doc.content,
        meta={
            "file_path": str(doc.file_path),
            "title": doc.title,
            "vault": doc.vault_name,
            "tags": doc.metadata.tags,
            "created": doc.metadata.created,
            "file_id": doc.metadata.file_id,
        },
    )

    # Use DocumentSplitter
    splitter = DocumentSplitter(
        split_by="word",
        split_length=chunk_size,
        split_overlap=overlap,
    )

    result = splitter.run(documents=[haystack_doc])
    chunks = result["documents"]

    # Add position metadata to each chunk
    for i, chunk in enumerate(chunks):
        chunk.meta["position"] = i

    return chunks


def chunk_documents(
    docs: list[Document], config: RAGConfig | None = None
) -> list[HaystackDocument]:
    """
    Chunk multiple documents.

    Args:
        docs: List of documents to chunk.
        config: RAG configuration for chunk settings.

    Returns:
        List of all chunks from all documents.
    """
    if config is None:
        config = rag_config

    all_chunks: list[HaystackDocument] = []

    for doc in docs:
        chunks = chunk_document(doc, config.chunk_size, config.chunk_overlap)
        all_chunks.extend(chunks)

    return all_chunks


# =============================================================================
# Indexing Pipeline
# =============================================================================


def create_indexing_pipeline(
    store: QdrantDocumentStore, config: OllamaConfig | None = None
) -> Pipeline:
    """
    Create Haystack indexing pipeline.

    Pipeline components:
    1. OllamaDocumentEmbedder - Generate embeddings for documents
    2. DocumentWriter - Write documents to Qdrant store

    Args:
        store: QdrantDocumentStore instance.
        config: Ollama configuration for embedding server.

    Returns:
        Configured Haystack Pipeline.
    """
    if config is None:
        config = ollama_config

    pipeline = Pipeline()

    # Embedder component
    embedder = OllamaDocumentEmbedder(
        url=config.remote_url,
        model=config.embedding_model,
        timeout=config.embedding_timeout,
        batch_size=config.embedding_batch_size,
    )

    # Writer component
    writer = DocumentWriter(document_store=store)

    # Add components to pipeline
    pipeline.add_component("embedder", embedder)
    pipeline.add_component("writer", writer)

    # Connect components
    pipeline.connect("embedder.documents", "writer.documents")

    return pipeline


# =============================================================================
# Index Vault
# =============================================================================


def index_vault(
    pipeline: Pipeline,
    vault_path: Path,
    vault_name: str,
    dry_run: bool = False,
    rag_config_override: RAGConfig | None = None,
) -> IndexingResult:
    """
    Index all documents in a vault.

    Args:
        pipeline: Configured indexing pipeline.
        vault_path: Path to vault directory.
        vault_name: Name of the vault.
        dry_run: If True, scan and chunk but don't write to store.
        rag_config_override: Optional RAG config override.

    Returns:
        IndexingResult with statistics.

    Raises:
        IndexingError: If vault path does not exist or indexing fails.
    """
    config = rag_config_override or rag_config
    errors: list[str] = []

    # Scan vault for normalized documents
    try:
        documents = scan_vault(vault_path, vault_name)
    except IndexingError:
        raise
    except Exception as e:
        raise IndexingError(
            f"Failed to scan vault: {e}",
            file_path=str(vault_path),
            stage="scan",
        ) from e

    total_docs = len(documents)

    if total_docs == 0:
        return IndexingResult(
            total_docs=0,
            indexed_docs=0,
            total_chunks=0,
            errors=[],
        )

    # Chunk documents
    try:
        chunks = chunk_documents(documents, config)
    except Exception as e:
        raise IndexingError(
            f"Failed to chunk documents: {e}",
            stage="chunk",
        ) from e

    total_chunks = len(chunks)

    # Dry run - return without indexing
    if dry_run:
        return IndexingResult(
            total_docs=total_docs,
            indexed_docs=total_docs,
            total_chunks=total_chunks,
            errors=[],
        )

    # Run indexing pipeline
    try:
        pipeline.run({"embedder": {"documents": chunks}})
    except Exception as e:
        errors.append(f"Pipeline error: {e}")
        return IndexingResult(
            total_docs=total_docs,
            indexed_docs=0,
            total_chunks=total_chunks,
            errors=errors,
        )

    return IndexingResult(
        total_docs=total_docs,
        indexed_docs=total_docs,
        total_chunks=total_chunks,
        errors=[],
    )


def index_all_vaults(
    pipeline: Pipeline,
    vaults_dir: Path | None = None,
    vault_names: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, IndexingResult]:
    """
    Index all configured vaults.

    Args:
        pipeline: Configured indexing pipeline.
        vaults_dir: Base directory for vaults (default: VAULTS_DIR).
        vault_names: List of vault names to index (default: from config).
        dry_run: If True, scan and chunk but don't write to store.

    Returns:
        Dictionary mapping vault names to IndexingResult.
    """
    if vaults_dir is None:
        vaults_dir = VAULTS_DIR

    if vault_names is None:
        vault_names = rag_config.target_vaults

    results: dict[str, IndexingResult] = {}

    for vault_name in vault_names:
        vault_path = vaults_dir / vault_name
        try:
            result = index_vault(pipeline, vault_path, vault_name, dry_run=dry_run)
            results[vault_name] = result
        except IndexingError as e:
            results[vault_name] = IndexingResult(
                total_docs=0,
                indexed_docs=0,
                total_chunks=0,
                errors=[str(e)],
            )

    return results
