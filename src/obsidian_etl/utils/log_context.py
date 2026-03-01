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

import logging
from contextvars import ContextVar

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
