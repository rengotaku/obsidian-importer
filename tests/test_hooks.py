"""Tests for Kedro hooks.

Phase 5 RED tests: ErrorHandlerHook and LoggingHook.
These tests verify:
- ErrorHandlerHook.on_node_error logs error details and pipeline continues
- LoggingHook.before_node_run / after_node_run logs node name and timing
"""

from __future__ import annotations

import logging
import time
import unittest
from unittest.mock import MagicMock

from obsidian_etl.hooks import ErrorHandlerHook, LoggingHook


class TestErrorHandlerHook(unittest.TestCase):
    """ErrorHandlerHook: on_node_error logs error and allows pipeline to continue."""

    def setUp(self):
        """Create hook instance and mock node."""
        self.hook = ErrorHandlerHook()
        self.mock_node = MagicMock()
        self.mock_node.__str__ = MagicMock(return_value="parse_claude_json")
        self.mock_catalog = MagicMock()

    def test_on_node_error_logs_error(self):
        """on_node_error がエラー内容をログに記録すること。"""
        error = ValueError("Missing uuid field")

        with self.assertLogs("obsidian_etl.hooks", level="ERROR") as cm:
            self.hook.on_node_error(
                error=error,
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={"raw_data": {}},
                is_async=False,
            )

        # Verify error message is logged
        log_output = "\n".join(cm.output)
        self.assertIn("parse_claude_json", log_output)
        self.assertIn("Missing uuid field", log_output)

    def test_on_node_error_does_not_raise(self):
        """on_node_error が例外を再送出しないこと（パイプライン継続を許可）。"""
        error = RuntimeError("LLM timeout")

        # Should not raise - just log and return
        try:
            with self.assertLogs("obsidian_etl.hooks", level="ERROR"):
                self.hook.on_node_error(
                    error=error,
                    node=self.mock_node,
                    catalog=self.mock_catalog,
                    inputs={},
                    is_async=False,
                )
        except Exception:
            self.fail("on_node_error should not re-raise the exception")

    def test_on_node_error_logs_error_type(self):
        """on_node_error がエラー種別をログに含むこと。"""
        error = TypeError("Expected dict, got str")

        with self.assertLogs("obsidian_etl.hooks", level="ERROR") as cm:
            self.hook.on_node_error(
                error=error,
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                is_async=False,
            )

        log_output = "\n".join(cm.output)
        self.assertIn("Expected dict, got str", log_output)


class TestLoggingHook(unittest.TestCase):
    """LoggingHook: before_node_run / after_node_run logs timing."""

    def setUp(self):
        """Create hook instance and mock objects."""
        self.hook = LoggingHook()
        self.mock_node = MagicMock()
        self.mock_node.__str__ = MagicMock(return_value="extract_knowledge_node")
        self.mock_catalog = MagicMock()

    def test_before_node_run_records_start_time(self):
        """before_node_run が開始時刻を記録すること。"""
        self.hook.before_node_run(
            node=self.mock_node,
            catalog=self.mock_catalog,
            inputs={},
        )

        # Internal state should have recorded start time
        self.assertIn("extract_knowledge_node", self.hook._start_times)
        self.assertIsInstance(self.hook._start_times["extract_knowledge_node"], float)

    def test_after_node_run_logs_elapsed_time(self):
        """after_node_run が経過時間をログに記録すること。"""
        # First, record start time
        self.hook.before_node_run(
            node=self.mock_node,
            catalog=self.mock_catalog,
            inputs={},
        )

        # Small delay to ensure measurable elapsed time
        time.sleep(0.01)

        # Then, after_node_run should log
        with self.assertLogs("obsidian_etl.hooks", level="INFO") as cm:
            self.hook.after_node_run(
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                outputs={},
                is_async=False,
            )

        log_output = "\n".join(cm.output)
        self.assertIn("extract_knowledge_node", log_output)
        # Should contain some timing info (e.g., "completed in X.XXs")
        self.assertIn("completed in", log_output)

    def test_after_node_run_clears_start_time(self):
        """after_node_run 後に開始時刻がクリアされること。"""
        self.hook.before_node_run(
            node=self.mock_node,
            catalog=self.mock_catalog,
            inputs={},
        )

        with self.assertLogs("obsidian_etl.hooks", level="INFO"):
            self.hook.after_node_run(
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                outputs={},
                is_async=False,
            )

        self.assertNotIn("extract_knowledge_node", self.hook._start_times)

    def test_logging_hook_multiple_nodes(self):
        """複数ノードのタイミングが独立して記録されること。"""
        node_a = MagicMock()
        node_a.__str__ = MagicMock(return_value="node_a")
        node_b = MagicMock()
        node_b.__str__ = MagicMock(return_value="node_b")

        self.hook.before_node_run(node=node_a, catalog=self.mock_catalog, inputs={})
        self.hook.before_node_run(node=node_b, catalog=self.mock_catalog, inputs={})

        self.assertIn("node_a", self.hook._start_times)
        self.assertIn("node_b", self.hook._start_times)

        with self.assertLogs("obsidian_etl.hooks", level="INFO"):
            self.hook.after_node_run(
                node=node_a,
                catalog=self.mock_catalog,
                inputs={},
                outputs={},
                is_async=False,
            )

        # node_a cleared, node_b still present
        self.assertNotIn("node_a", self.hook._start_times)
        self.assertIn("node_b", self.hook._start_times)


if __name__ == "__main__":
    unittest.main()
