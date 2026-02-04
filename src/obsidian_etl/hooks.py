"""Kedro hooks for obsidian-etl.

ErrorHandlerHook: Catches node-level errors and logs details.
LoggingHook: Logs node execution timing.
"""

from __future__ import annotations

import logging

from kedro.framework.hooks import hook_impl

logger = logging.getLogger(__name__)


class ErrorHandlerHook:
    """Hook that handles node-level errors."""

    @hook_impl
    def on_node_error(
        self,
        error: Exception,
        node: object,
        catalog: object,
        inputs: dict,
        is_async: bool,
    ) -> None:
        """Log error details when a node fails."""
        logger.error(f"Node '{node}' failed: {error}")


class LoggingHook:
    """Hook that logs node execution timing."""

    def __init__(self) -> None:
        self._start_times: dict[str, float] = {}

    @hook_impl
    def before_node_run(self, node: object, catalog: object, inputs: dict) -> None:
        """Record start time before node execution."""
        import time

        self._start_times[str(node)] = time.time()

    @hook_impl
    def after_node_run(
        self,
        node: object,
        catalog: object,
        inputs: dict,
        outputs: dict,
        is_async: bool,
    ) -> None:
        """Log elapsed time after node execution."""
        import time

        node_name = str(node)
        start = self._start_times.pop(node_name, None)
        if start is not None:
            elapsed = time.time() - start
            logger.info(f"Node '{node_name}' completed in {elapsed:.2f}s")
