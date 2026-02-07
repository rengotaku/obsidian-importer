"""Timing utilities for pipeline nodes.

Provides decorators and context managers for measuring execution time.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


def timed_node(func: Callable) -> Callable:
    """Decorator to measure and log node execution time.

    Usage:
        @timed_node
        def my_node(input_data):
            ...
            return output_data

    Logs format:
        my_node: completed in 12.3s
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__}: completed in {elapsed:.1f}s")
        return result

    return wrapper


@contextmanager
def timed_item(item_id: str, index: int, total: int):
    """Context manager to measure and log item processing time.

    Usage:
        for i, (partition_id, load_func) in enumerate(items.items()):
            with timed_item(partition_id, i + 1, total):
                # process item
                ...

    Logs format:
        [1/100] Processing: item_id
        [1/100] Done: item_id (5.2s)
    """
    logger.info(f"[{index}/{total}] Processing: {item_id}")
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        logger.info(f"[{index}/{total}] Done: {item_id} ({elapsed:.1f}s)")


class ItemTimer:
    """Timer for tracking item processing with skip support.

    Usage:
        timer = ItemTimer(total_items=100)
        for partition_id, load_func in items.items():
            if should_skip:
                timer.skip()
                continue
            with timer.track(partition_id):
                # process item
                ...
        timer.summary("extract_knowledge")

    Logs format:
        [1/95] Processing: item_id
        [1/95] Done: item_id (5.2s)
        extract_knowledge: total=100, skipped=5, processed=95, succeeded=90, failed=5 (120.5s)
    """

    def __init__(self, total_items: int):
        self.total = total_items
        self.skipped = 0
        self.processed = 0
        self.succeeded = 0
        self.failed = 0
        self.start_time = time.time()
        self._current_success = False

    def skip(self) -> None:
        """Mark current item as skipped."""
        self.skipped += 1

    @contextmanager
    def track(self, item_id: str):
        """Track item processing time."""
        self.processed += 1
        self._current_success = False
        remaining = self.total - self.skipped
        logger.info(f"[{self.processed}/{remaining}] Processing: {item_id}")
        start = time.time()
        try:
            yield
            self._current_success = True
        finally:
            elapsed = time.time() - start
            if self._current_success:
                self.succeeded += 1
                logger.info(f"[{self.processed}/{remaining}] Done: {item_id} ({elapsed:.1f}s)")
            else:
                self.failed += 1
                logger.warning(f"[{self.processed}/{remaining}] Failed: {item_id} ({elapsed:.1f}s)")

    def mark_failed(self) -> None:
        """Mark current item as failed (call within track context)."""
        self._current_success = False

    def summary(self, node_name: str) -> None:
        """Log summary with total elapsed time."""
        elapsed = time.time() - self.start_time
        logger.info(
            f"{node_name}: total={self.total}, skipped={self.skipped}, "
            f"processed={self.processed}, succeeded={self.succeeded}, "
            f"failed={self.failed} ({elapsed:.1f}s)"
        )
