"""Log context management using contextvars.

This module provides a context-aware logging system that automatically
prepends file_id to log messages during partition processing.

US1: エラー発生時のファイル特定
- FR-001: contextvars を使用してログコンテキスト（file_id）を管理
- FR-002: パーティション処理のループ開始時に file_id を設定
- FR-003: file_id が設定されている場合のみ [file_id] プレフィックスを出力
- FR-004: file_id はスレッドローカル（contextvars は非同期対応）
- FR-005: 処理完了後に file_id をクリア可能
"""

from __future__ import annotations

import copy
import logging
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar

from kedro.logging import RichHandler

# ContextVar for file_id (default: empty string)
# Thread-safe and async-safe context storage
_file_id_var: ContextVar[str] = ContextVar("file_id", default="")


def set_file_id(file_id: str) -> None:
    """Set file_id in the current context.

    Args:
        file_id: File identifier (typically 12-char SHA256 prefix)

    Example:
        >>> set_file_id("abc123def456")
        >>> get_file_id()
        'abc123def456'
    """
    _file_id_var.set(file_id)


def get_file_id() -> str:
    """Get file_id from the current context.

    Returns:
        Current file_id, or empty string if not set

    Example:
        >>> get_file_id()  # When not set
        ''
        >>> set_file_id("test_id")
        >>> get_file_id()
        'test_id'
    """
    return _file_id_var.get()


def clear_file_id() -> None:
    """Clear file_id in the current context.

    Resets file_id to the default value (empty string).

    Example:
        >>> set_file_id("some_id")
        >>> clear_file_id()
        >>> get_file_id()
        ''
    """
    _file_id_var.set("")


def _extract_file_id_from_frontmatter(content: str) -> str | None:
    """Extract file_id from YAML frontmatter in Markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        file_id if found in frontmatter, None otherwise
    """
    if not content.startswith("---"):
        return None

    # Find the closing ---
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return None

    frontmatter = content[3:end_idx]

    # Simple YAML parsing for file_id line
    for line in frontmatter.split("\n"):
        line = line.strip()
        if line.startswith("file_id:"):
            # Extract value after colon
            value = line[8:].strip()
            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            return value if value else None

    return None


@contextmanager
def file_id_context(file_id: str) -> Generator[None, None, None]:
    """Context manager for file_id scope.

    Sets file_id at entry and clears it at exit, ensuring file_id
    is only active during the specific processing block.

    Args:
        file_id: File identifier to set for this context

    Example:
        >>> with file_id_context("abc123"):
        ...     logger.info("Processing file")  # [abc123] Processing file
        >>> logger.info("After processing")  # After processing (no prefix)
    """
    set_file_id(file_id)
    try:
        yield
    finally:
        clear_file_id()


def iter_with_file_id(
    partitioned_input: dict[str, callable] | list[tuple[str, callable]],
) -> Generator[tuple[str, any], None, None]:
    """Iterate partitions with file_id context automatically set.

    This utility ensures consistent file_id logging across all partition
    processing nodes. The file_id context is automatically set after
    loading the item, extracting file_id from appropriate source based
    on item type.

    Args:
        partitioned_input: Either:
            - Kedro PartitionedDataset-style dict (partition_key -> load_func)
            - Pre-filtered list of (partition_key, load_func) tuples

    Yields:
        tuple[str, any]: (partition_key, loaded_item) with file_id context active

    Example:
        >>> for key, item in iter_with_file_id(partitioned_input):
        ...     process(item)  # logs will have [file_id] prefix

    Note:
        - Supports both dict (JSON) and str (Markdown) input
        - For dict: extracts file_id from metadata.file_id or file_id field
        - For str: extracts file_id from frontmatter "file_id" field
        - Falls back to partition key if file_id not found
        - Use this instead of manually iterating with file_id_context
    """
    # Handle both dict and list of tuples
    items = partitioned_input.items() if isinstance(partitioned_input, dict) else partitioned_input

    for key, load_func in items:
        item = load_func()

        # Extract file_id from item, fallback to key
        file_id = key

        if isinstance(item, dict):
            # Extract from dict (JSON input)
            file_id = item.get("metadata", {}).get("file_id") or item.get("file_id") or key
        elif isinstance(item, str):
            # Parse frontmatter from Markdown content
            extracted = _extract_file_id_from_frontmatter(item)
            if extracted:
                file_id = extracted

        with file_id_context(file_id):
            yield key, item


class ContextAwareFormatter(logging.Formatter):
    """Logging formatter that prepends [file_id] to messages.

    This formatter automatically adds [file_id] prefix to log messages
    when file_id is set in the context. When file_id is not set,
    messages are formatted normally without any prefix.

    FR-003: file_id が設定されている場合のみ [file_id] プレフィックスを出力

    Example:
        >>> import logging
        >>> formatter = ContextAwareFormatter(fmt="%(message)s")
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(formatter)
        >>> logger = logging.getLogger("test")
        >>> logger.addHandler(handler)
        >>>
        >>> # Without file_id
        >>> logger.info("Processing started")
        Processing started
        >>>
        >>> # With file_id
        >>> set_file_id("abc123")
        >>> logger.info("Processing started")
        [abc123] Processing started
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional [file_id] prefix.

        Args:
            record: Log record to format

        Returns:
            Formatted log message with [file_id] prefix if file_id is set

        Note:
            This method modifies record.msg temporarily to add the prefix,
            then restores the original message to avoid side effects.
        """
        file_id = get_file_id()
        if file_id:
            # Save original message
            original_msg = record.msg
            # Prepend [file_id] prefix
            record.msg = f"[{file_id}] {original_msg}"
            # Format with prefix
            result = super().format(record)
            # Restore original message to avoid side effects
            record.msg = original_msg
            return result
        # No prefix when file_id is not set
        return super().format(record)


class ContextAwareRichHandler(RichHandler):
    """Rich logging handler that prepends [file_id] to messages.

    Extends Kedro's RichHandler to automatically add [file_id] prefix
    to log messages when file_id is set in the context, while preserving
    Rich's colored output formatting.

    FR-003: file_id が設定されている場合のみ [file_id] プレフィックスを出力

    Example:
        In logging.yml:
        ```yaml
        handlers:
          rich:
            class: obsidian_etl.utils.log_context.ContextAwareRichHandler
            rich_tracebacks: true
        ```
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record with optional [file_id] prefix.

        Only applies [file_id] prefix to obsidian_etl.* loggers to avoid
        polluting Kedro's internal log messages.

        Args:
            record: Log record to emit

        Note:
            Creates a copy of the record to avoid side effects on other handlers.
        """
        file_id = get_file_id()
        # Only apply prefix to obsidian_etl.* loggers
        if file_id and record.name.startswith("obsidian_etl"):
            # Create a copy to avoid affecting other handlers
            updated_record = copy.copy(record)
            updated_record.msg = f"[{file_id}] {record.msg}"
            super().emit(updated_record)
        else:
            super().emit(record)
