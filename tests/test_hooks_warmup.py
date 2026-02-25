"""Tests for ErrorHandlerHook handling of OllamaWarmupError.

Phase 3 (US2): ErrorHandlerHook should catch OllamaWarmupError,
display a clear error message with model name and recommended actions,
and exit with code 3.

Tests verify:
- ErrorHandlerHook catches OllamaWarmupError in on_node_error
- sys.exit(3) is called for warmup errors
- Error message includes the failed model name
- Error message includes recommended actions (ollama serve, ollama pull)
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from obsidian_etl.hooks import ErrorHandlerHook
from obsidian_etl.utils.ollama import OllamaWarmupError


class TestErrorHandlerHookCatchesWarmupError(unittest.TestCase):
    """ErrorHandlerHook が OllamaWarmupError を個別にハンドリングすること。"""

    def setUp(self):
        """Create hook instance and mock objects."""
        self.hook = ErrorHandlerHook()
        self.mock_node = MagicMock()
        self.mock_node.__str__ = MagicMock(return_value="extract_knowledge")
        self.mock_catalog = MagicMock()

    @patch("obsidian_etl.hooks.sys.exit")
    def test_on_node_error_catches_warmup_error(self, mock_exit):
        """ErrorHandlerHook が OllamaWarmupError をキャッチして sys.exit を呼ぶこと。

        Given: OllamaWarmupError が発生する
        When: on_node_error が呼ばれる
        Then: sys.exit が呼ばれる（通常の ValueError 等とは異なる処理）
        """
        error = OllamaWarmupError(model="gemma3:12b", reason="Connection refused")

        with self.assertLogs("obsidian_etl.hooks", level="ERROR"):
            self.hook.on_node_error(
                error=error,
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                is_async=False,
            )

        mock_exit.assert_called_once()


class TestErrorHandlerHookExitCode(unittest.TestCase):
    """ErrorHandlerHook が OllamaWarmupError 時に終了コード 3 を返すこと。"""

    def setUp(self):
        """Create hook instance and mock objects."""
        self.hook = ErrorHandlerHook()
        self.mock_node = MagicMock()
        self.mock_node.__str__ = MagicMock(return_value="extract_knowledge")
        self.mock_catalog = MagicMock()

    @patch("obsidian_etl.hooks.sys.exit")
    def test_exit_code_3_on_warmup_error(self, mock_exit):
        """OllamaWarmupError 時に終了コード 3 で sys.exit すること。

        Given: OllamaWarmupError が発生する
        When: on_node_error が呼ばれる
        Then: sys.exit(3) が呼ばれる（Ollama 接続エラーの終了コード）
        """
        error = OllamaWarmupError(model="gemma3:12b", reason="Connection timed out")

        with self.assertLogs("obsidian_etl.hooks", level="ERROR"):
            self.hook.on_node_error(
                error=error,
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                is_async=False,
            )

        mock_exit.assert_called_once_with(3)

    @patch("obsidian_etl.hooks.sys.exit")
    def test_non_warmup_error_does_not_exit(self, mock_exit):
        """通常のエラーでは sys.exit が呼ばれないこと。

        Given: 通常の ValueError が発生する
        When: on_node_error が呼ばれる
        Then: sys.exit は呼ばれない（既存動作を維持）
        """
        error = ValueError("Missing uuid field")

        with self.assertLogs("obsidian_etl.hooks", level="ERROR"):
            self.hook.on_node_error(
                error=error,
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                is_async=False,
            )

        mock_exit.assert_not_called()


class TestErrorMessageContainsModelName(unittest.TestCase):
    """エラーメッセージにモデル名が含まれること。"""

    def setUp(self):
        """Create hook instance and mock objects."""
        self.hook = ErrorHandlerHook()
        self.mock_node = MagicMock()
        self.mock_node.__str__ = MagicMock(return_value="extract_knowledge")
        self.mock_catalog = MagicMock()

    @patch("obsidian_etl.hooks.sys.exit")
    def test_error_message_includes_model_name_timeout(self, mock_exit):
        """タイムアウト時のエラーメッセージにモデル名が含まれること。

        Given: gemma3:12b のウォームアップがタイムアウトする
        When: on_node_error が呼ばれる
        Then: ログメッセージに "gemma3:12b" が含まれる
        """
        error = OllamaWarmupError(model="gemma3:12b", reason="Connection timed out")

        with self.assertLogs("obsidian_etl.hooks", level="ERROR") as cm:
            self.hook.on_node_error(
                error=error,
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                is_async=False,
            )

        log_output = "\n".join(cm.output)
        self.assertIn("gemma3:12b", log_output)

    @patch("obsidian_etl.hooks.sys.exit")
    def test_error_message_includes_model_name_connection_error(self, mock_exit):
        """接続エラー時のエラーメッセージにモデル名が含まれること。

        Given: llama3.2:3b のウォームアップが接続エラーになる
        When: on_node_error が呼ばれる
        Then: ログメッセージに "llama3.2:3b" が含まれる
        """
        error = OllamaWarmupError(model="llama3.2:3b", reason="Connection refused")

        with self.assertLogs("obsidian_etl.hooks", level="ERROR") as cm:
            self.hook.on_node_error(
                error=error,
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                is_async=False,
            )

        log_output = "\n".join(cm.output)
        self.assertIn("llama3.2:3b", log_output)


class TestErrorMessageContainsRecommendedActions(unittest.TestCase):
    """エラーメッセージに推奨アクションが含まれること。"""

    def setUp(self):
        """Create hook instance and mock objects."""
        self.hook = ErrorHandlerHook()
        self.mock_node = MagicMock()
        self.mock_node.__str__ = MagicMock(return_value="extract_knowledge")
        self.mock_catalog = MagicMock()

    @patch("obsidian_etl.hooks.sys.exit")
    def test_error_message_includes_ollama_serve(self, mock_exit):
        """エラーメッセージに 'ollama serve' が含まれること。

        Given: ウォームアップが失敗する
        When: on_node_error が呼ばれる
        Then: ログメッセージに "ollama serve" が含まれる
        """
        error = OllamaWarmupError(model="gemma3:12b", reason="Connection refused")

        with self.assertLogs("obsidian_etl.hooks", level="ERROR") as cm:
            self.hook.on_node_error(
                error=error,
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                is_async=False,
            )

        log_output = "\n".join(cm.output)
        self.assertIn("ollama serve", log_output)

    @patch("obsidian_etl.hooks.sys.exit")
    def test_error_message_includes_ollama_pull(self, mock_exit):
        """エラーメッセージに 'ollama pull' が含まれること。

        Given: ウォームアップが失敗する
        When: on_node_error が呼ばれる
        Then: ログメッセージに "ollama pull" とモデル名が含まれる
        """
        error = OllamaWarmupError(model="gemma3:12b", reason="Connection timed out")

        with self.assertLogs("obsidian_etl.hooks", level="ERROR") as cm:
            self.hook.on_node_error(
                error=error,
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                is_async=False,
            )

        log_output = "\n".join(cm.output)
        self.assertIn("ollama pull", log_output)

    @patch("obsidian_etl.hooks.sys.exit")
    def test_error_message_includes_failure_reason(self, mock_exit):
        """エラーメッセージに失敗理由が含まれること。

        Given: ウォームアップが "Connection refused" で失敗する
        When: on_node_error が呼ばれる
        Then: ログメッセージに失敗理由が含まれる
        """
        error = OllamaWarmupError(model="gemma3:12b", reason="Connection refused")

        with self.assertLogs("obsidian_etl.hooks", level="ERROR") as cm:
            self.hook.on_node_error(
                error=error,
                node=self.mock_node,
                catalog=self.mock_catalog,
                inputs={},
                is_async=False,
            )

        log_output = "\n".join(cm.output)
        self.assertIn("Connection refused", log_output)


if __name__ == "__main__":
    unittest.main()
