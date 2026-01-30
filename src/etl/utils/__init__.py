"""
src.etl.utils - ETL パイプライン用ユーティリティモジュール

converter/scripts/llm_import/common/ からコピーし、
src.etl 内で独立して動作するように import パスを修正。
"""

from src.etl.utils.chunker import Chunk, ChunkedConversation, Chunker, ChunkResult
from src.etl.utils.error_writer import ErrorDetail, write_error_file
from src.etl.utils.file_id import generate_file_id
from src.etl.utils.knowledge_extractor import (
    CodeSnippet,
    ExtractionResult,
    KnowledgeDocument,
    KnowledgeExtractor,
    extract_item_id_from_frontmatter,
)
from src.etl.utils.ollama import (
    call_ollama,
    check_ollama_connection,
)

__all__ = [
    # ollama
    "call_ollama",
    "check_ollama_connection",
    # file_id
    "generate_file_id",
    # chunker
    "Chunker",
    "Chunk",
    "ChunkResult",
    "ChunkedConversation",
    # error_writer
    "ErrorDetail",
    "write_error_file",
    # knowledge_extractor
    "KnowledgeExtractor",
    "KnowledgeDocument",
    "ExtractionResult",
    "CodeSnippet",
    "extract_item_id_from_frontmatter",
]
