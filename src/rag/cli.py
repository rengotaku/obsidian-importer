"""
RAG CLI - Command Line Interface for RAG System

Entry point: python -m src.rag.cli

Subcommands:
- index: Index vault documents
- search: Semantic search
- ask: Q&A with LLM
- status: Show index status
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import TYPE_CHECKING

import structlog

from src.rag.clients import check_connection
from src.rag.config import VAULTS_DIR, OllamaConfig, ollama_config, rag_config
from src.rag.exceptions import ConnectionError as RAGConnectionError
from src.rag.exceptions import IndexingError, QueryError
from src.rag.pipelines import (
    Answer,
    IndexingResult,
    QueryFilters,
    SearchResponse,
    ask,
    create_indexing_pipeline,
    create_qa_pipeline,
    create_search_pipeline,
    index_all_vaults,
    search,
)
from src.rag.stores import COLLECTION_NAME, get_collection_stats, get_document_store

if TYPE_CHECKING:
    pass

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# =============================================================================
# Exit Codes
# =============================================================================

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_ARGS_ERROR = 2
EXIT_CONNECTION_ERROR = 3


# =============================================================================
# Argument Parser
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="python -m src.rag.cli",
        description="RAG System CLI - Semantic search and Q&A for Obsidian Knowledge Base",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
    )

    # ==========================================================================
    # index command
    # ==========================================================================
    index_parser = subparsers.add_parser(
        "index",
        help="Index vault documents",
        description="Index all normalized documents in vaults for semantic search",
    )
    index_parser.add_argument(
        "--vault",
        action="append",
        dest="vaults",
        help="Target vault (can be specified multiple times, default: all)",
    )
    index_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without actually indexing",
    )
    index_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    # ==========================================================================
    # search command
    # ==========================================================================
    search_parser = subparsers.add_parser(
        "search",
        help="Semantic search",
        description="Search documents using semantic similarity",
    )
    search_parser.add_argument(
        "query",
        help="Search query",
    )
    search_parser.add_argument(
        "--vault",
        action="append",
        dest="vaults",
        help="Filter by vault (can be specified multiple times)",
    )
    search_parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        help="Filter by tag (AND condition, can be specified multiple times)",
    )
    search_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results (default: 5)",
    )
    search_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # ==========================================================================
    # ask command
    # ==========================================================================
    ask_parser = subparsers.add_parser(
        "ask",
        help="Q&A with LLM",
        description="Ask a question and get an LLM-generated answer with sources",
    )
    ask_parser.add_argument(
        "question",
        help="Question to ask",
    )
    ask_parser.add_argument(
        "--vault",
        action="append",
        dest="vaults",
        help="Filter by vault (can be specified multiple times)",
    )
    ask_parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        help="Filter by tag (AND condition, can be specified multiple times)",
    )
    ask_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of source documents (default: 5)",
    )
    ask_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    ask_parser.add_argument(
        "--no-sources",
        action="store_true",
        help="Hide source citations",
    )

    # ==========================================================================
    # status command
    # ==========================================================================
    status_parser = subparsers.add_parser(
        "status",
        help="Show index status",
        description="Display index statistics and configuration",
    )
    status_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    status_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    return parser


# =============================================================================
# Connection Verification
# =============================================================================


def verify_connections(config: OllamaConfig, check_local: bool = False) -> None:
    """
    Verify connections to required servers.

    Args:
        config: Ollama configuration with server URLs.
        check_local: Also check local LLM server (for ask command).

    Raises:
        RAGConnectionError: If connection fails.
    """
    # Check remote embedding server
    success, error = check_connection(config.remote_url)
    if not success:
        raise RAGConnectionError(
            f"Cannot connect to embedding server: {error}",
            server=config.remote_url,
        )

    # Check local LLM server (only for ask command)
    if check_local:
        success, error = check_connection(config.local_url)
        if not success:
            raise RAGConnectionError(
                f"Cannot connect to LLM server: {error}",
                server=config.local_url,
            )


# =============================================================================
# Index Command
# =============================================================================


def cmd_index(args: argparse.Namespace) -> int:
    """
    Execute index command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    vaults = args.vaults or rag_config.target_vaults
    dry_run = args.dry_run
    verbose = args.verbose

    if verbose:
        logger.info("Starting indexing", vaults=vaults, dry_run=dry_run)

    try:
        # Verify connection (not needed for dry_run, but check anyway for consistency)
        if not dry_run:
            verify_connections(ollama_config)

        # Get document store
        store = get_document_store()

        # Create indexing pipeline
        pipeline = create_indexing_pipeline(store)

        # Index vaults
        start_time = time.time()
        results = index_all_vaults(
            pipeline=pipeline,
            vaults_dir=VAULTS_DIR,
            vault_names=vaults,
            dry_run=dry_run,
        )
        elapsed = time.time() - start_time

        # Output results
        _output_index_results(results, elapsed, dry_run, verbose)

        # Check for errors
        total_errors = sum(len(r.errors) for r in results.values())
        return EXIT_SUCCESS if total_errors == 0 else EXIT_ERROR

    except RAGConnectionError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        print(f"Server: {e.server}", file=sys.stderr)
        return EXIT_CONNECTION_ERROR
    except IndexingError as e:
        print(f"Indexing error: {e.message}", file=sys.stderr)
        if verbose and e.details:
            print(f"Details: {e.details}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def _output_index_results(
    results: dict[str, IndexingResult],
    elapsed: float,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Output indexing results to stdout."""
    mode = "[DRY RUN] " if dry_run else ""

    # Summary
    total_docs = sum(r.total_docs for r in results.values())
    indexed_docs = sum(r.indexed_docs for r in results.values())
    total_chunks = sum(r.total_chunks for r in results.values())
    total_errors = sum(len(r.errors) for r in results.values())

    print(f"\n{mode}Indexing Complete")
    print("=" * 50)
    print(f"Total documents: {total_docs}")
    print(f"Indexed documents: {indexed_docs}")
    print(f"Total chunks: {total_chunks}")
    print(f"Errors: {total_errors}")
    print(f"Elapsed: {elapsed:.2f}s")

    if verbose:
        print("\nBy Vault:")
        for vault_name, result in results.items():
            status = "OK" if not result.errors else "ERROR"
            print(f"  {vault_name}: {result.indexed_docs} docs, {result.total_chunks} chunks [{status}]")
            for error in result.errors:
                print(f"    - {error}")


# =============================================================================
# Search Command
# =============================================================================


def cmd_search(args: argparse.Namespace) -> int:
    """
    Execute search command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    query = args.query
    vaults = args.vaults
    tags = args.tags
    top_k = args.top_k
    output_format = args.format

    try:
        # Verify connection
        verify_connections(ollama_config)

        # Get document store
        store = get_document_store()

        # Create search pipeline
        pipeline = create_search_pipeline(store)

        # Build filters
        filters = QueryFilters(
            vaults=vaults,
            tags=tags,
        ) if vaults or tags else None

        # Execute search
        start_time = time.time()
        response = search(pipeline, query, filters=filters, top_k=top_k)
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Output results
        if output_format == "json":
            _output_search_json(response, elapsed_ms)
        else:
            _output_search_text(response)

        return EXIT_SUCCESS

    except RAGConnectionError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        return EXIT_CONNECTION_ERROR
    except QueryError as e:
        print(f"Search error: {e.message}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def _output_search_text(response: SearchResponse) -> None:
    """Output search results in text format."""
    print(f'\nFound {response.total} results for "{response.query}"\n')

    for i, result in enumerate(response.results, 1):
        print(f"{i}. [{result.score:.2f}] {result.title}")
        print(f"   {result.file_path}")
        # Truncate content for display
        snippet = result.content[:200].replace("\n", " ")
        if len(result.content) > 200:
            snippet += "..."
        print(f"   {snippet}")
        print()


def _output_search_json(response: SearchResponse, elapsed_ms: int) -> None:
    """Output search results in JSON format."""
    output = {
        "query": response.query,
        "results": [
            {
                "score": result.score,
                "title": result.title,
                "file_path": result.file_path,
                "vault": result.vault,
                "snippet": result.content[:200] + "..." if len(result.content) > 200 else result.content,
            }
            for result in response.results
        ],
        "total": response.total,
        "elapsed_ms": elapsed_ms,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# =============================================================================
# Ask Command
# =============================================================================


def cmd_ask(args: argparse.Namespace) -> int:
    """
    Execute ask command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    question = args.question
    vaults = args.vaults
    tags = args.tags
    top_k = args.top_k
    output_format = args.format
    no_sources = args.no_sources

    try:
        # Verify connection (including local LLM)
        verify_connections(ollama_config, check_local=True)

        # Get document store
        store = get_document_store()

        # Create Q&A pipeline
        pipeline = create_qa_pipeline(store)

        # Build filters
        filters = QueryFilters(
            vaults=vaults,
            tags=tags,
        ) if vaults or tags else None

        # Execute Q&A
        start_time = time.time()
        answer = ask(pipeline, question, filters=filters, top_k=top_k)
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Output results
        if output_format == "json":
            _output_ask_json(answer, question, elapsed_ms, no_sources)
        else:
            _output_ask_text(answer, question, no_sources)

        return EXIT_SUCCESS

    except RAGConnectionError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        return EXIT_CONNECTION_ERROR
    except QueryError as e:
        print(f"Q&A error: {e.message}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def _output_ask_text(answer: Answer, question: str, no_sources: bool) -> None:
    """Output Q&A result in text format."""
    print(f"\nQ: {question}\n")
    print(f"A: {answer.text}\n")

    if not no_sources and answer.sources:
        print("Sources:")
        for i, src in enumerate(answer.sources, 1):
            print(f"- [{i}] {src.title} ({src.file_path})")
        print()


def _output_ask_json(answer: Answer, question: str, elapsed_ms: int, no_sources: bool) -> None:
    """Output Q&A result in JSON format."""
    output = {
        "question": question,
        "answer": answer.text,
        "confidence": answer.confidence,
        "elapsed_ms": elapsed_ms,
    }

    if not no_sources:
        output["sources"] = [
            {
                "title": src.title,
                "file_path": src.file_path,
                "score": src.score,
                "snippet": src.content[:200] + "..." if len(src.content) > 200 else src.content,
            }
            for src in answer.sources
        ]

    print(json.dumps(output, ensure_ascii=False, indent=2))


# =============================================================================
# Status Command
# =============================================================================


def cmd_status(args: argparse.Namespace) -> int:
    """
    Execute status command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code.
    """
    output_format = args.format
    verbose = args.verbose

    try:
        # Get document store
        store = get_document_store()

        # Get stats
        stats = get_collection_stats(store)

        # Check connections if verbose
        connection_status = {}
        if verbose:
            success, _ = check_connection(ollama_config.remote_url)
            connection_status["embedding_server"] = "OK" if success else "OFFLINE"
            success, _ = check_connection(ollama_config.local_url)
            connection_status["llm_server"] = "OK" if success else "OFFLINE"

        # Output results
        if output_format == "json":
            _output_status_json(stats, connection_status, verbose)
        else:
            _output_status_text(stats, connection_status, verbose)

        return EXIT_SUCCESS

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_ERROR


def _output_status_text(stats: dict, connection_status: dict, verbose: bool) -> None:
    """Output status in text format."""
    print("\nRAG Index Status")
    print("=" * 50)
    print(f"Collection: {stats['collection_name']}")
    print(f"Total Chunks: {stats['document_count']:,}")
    print(f"Embedding Dim: {stats['embedding_dim']}")
    print(f"Similarity: {stats['similarity']}")

    if verbose:
        print(f"\nEmbedding Model: {ollama_config.embedding_model} @ {ollama_config.remote_url}")
        print(f"LLM Model: {ollama_config.llm_model} @ {ollama_config.local_url}")
        print("\nServer Status:")
        for server, status in connection_status.items():
            print(f"  {server}: {status}")

    print()


def _output_status_json(stats: dict, connection_status: dict, verbose: bool) -> None:
    """Output status in JSON format."""
    output = {
        "collection_name": stats["collection_name"],
        "document_count": stats["document_count"],
        "embedding_dim": stats["embedding_dim"],
        "similarity": stats["similarity"],
    }

    if verbose:
        output["config"] = {
            "embedding_model": ollama_config.embedding_model,
            "embedding_server": ollama_config.remote_url,
            "llm_model": ollama_config.llm_model,
            "llm_server": ollama_config.local_url,
        }
        output["connection_status"] = connection_status

    print(json.dumps(output, ensure_ascii=False, indent=2))


# =============================================================================
# Main
# =============================================================================


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for CLI.

    Args:
        argv: Command line arguments (default: sys.argv[1:]).

    Returns:
        Exit code.
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return EXIT_ARGS_ERROR

    # Dispatch to command handler
    handlers = {
        "index": cmd_index,
        "search": cmd_search,
        "ask": cmd_ask,
        "status": cmd_status,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return EXIT_ARGS_ERROR


if __name__ == "__main__":
    sys.exit(main())
