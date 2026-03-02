"""Tests for call_ollama exception-based error handling.

Phase 3 RED tests: call_ollama raises exceptions instead of returning error tuples.
These tests verify:
- Empty response raises OllamaEmptyResponseError
- Timeout raises OllamaTimeoutError
- Connection error raises OllamaConnectionError
- Successful call returns str (not tuple)
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class TestCallOllamaEmptyResponse(unittest.TestCase):
    """call_ollama: 空レスポンス時に OllamaEmptyResponseError をスロー。"""

    def setUp(self):
        """Reset warmup state before each test."""
        import obsidian_etl.utils.ollama

        obsidian_etl.utils.ollama._warmed_models.clear()

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_empty_response_raises_exception(self, mock_urlopen, mock_warmup):
        """空レスポンスの場合に OllamaEmptyResponseError がスローされること。

        FR-009: call_ollama 関数はエラー時にタプルではなく例外をスローしなければならない

        US2 Acceptance Scenario 1:
        Given: LLM が空のレスポンスを返した場合
        When: call_ollama が呼ばれるとき
        Then: OllamaEmptyResponseError がスローされる
        """
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError, call_ollama

        # Mock empty response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": ""}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with self.assertRaises(OllamaEmptyResponseError):
            call_ollama(
                system_prompt="system",
                user_message="user",
                model="gemma3:12b",
            )

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_whitespace_only_response_raises_exception(self, mock_urlopen, mock_warmup):
        """空白文字のみのレスポンスで OllamaEmptyResponseError がスローされること。

        Edge case from spec.md:
        LLM レスポンスが空白文字のみの場合 -> OllamaEmptyResponseError として扱う
        """
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError, call_ollama

        # Mock whitespace-only response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "   \\n\\t  "}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with self.assertRaises(OllamaEmptyResponseError):
            call_ollama(
                system_prompt="system",
                user_message="user",
                model="gemma3:12b",
            )

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_empty_response_error_has_context_len(self, mock_urlopen, mock_warmup):
        """空レスポンスエラーに context_len が含まれること。

        FR-011: 例外クラスは context_len 属性を保持しなければならない
        """
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError, call_ollama

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": ""}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        system_prompt = "You are a helper."
        user_message = "Please summarize this text."
        expected_context_len = len(system_prompt) + len(user_message)

        with self.assertRaises(OllamaEmptyResponseError) as ctx:
            call_ollama(
                system_prompt=system_prompt,
                user_message=user_message,
                model="gemma3:12b",
            )

        self.assertEqual(ctx.exception.context_len, expected_context_len)


class TestCallOllamaTimeout(unittest.TestCase):
    """call_ollama: タイムアウト時に OllamaTimeoutError をスロー。"""

    def setUp(self):
        """Reset warmup state before each test."""
        import obsidian_etl.utils.ollama

        obsidian_etl.utils.ollama._warmed_models.clear()

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_timeout_raises_exception(self, mock_urlopen, mock_warmup):
        """タイムアウト時に OllamaTimeoutError がスローされること。

        FR-009: call_ollama 関数はエラー時にタプルではなく例外をスローしなければならない

        US2 Acceptance Scenario 2:
        Given: リクエストがタイムアウトした場合
        When: call_ollama が呼ばれるとき
        Then: OllamaTimeoutError がスローされる
        """
        from obsidian_etl.utils.ollama import OllamaTimeoutError, call_ollama

        # Mock timeout
        mock_urlopen.side_effect = TimeoutError("Request timed out")

        with self.assertRaises(OllamaTimeoutError):
            call_ollama(
                system_prompt="system",
                user_message="user",
                model="gemma3:12b",
                timeout=120,
            )

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_timeout_error_has_context_len(self, mock_urlopen, mock_warmup):
        """タイムアウトエラーに context_len が含まれること。"""
        from obsidian_etl.utils.ollama import OllamaTimeoutError, call_ollama

        mock_urlopen.side_effect = TimeoutError("Request timed out")

        system_prompt = "Be concise."
        user_message = "Hello world"
        expected_context_len = len(system_prompt) + len(user_message)

        with self.assertRaises(OllamaTimeoutError) as ctx:
            call_ollama(
                system_prompt=system_prompt,
                user_message=user_message,
                model="gemma3:12b",
            )

        self.assertEqual(ctx.exception.context_len, expected_context_len)


class TestCallOllamaConnectionError(unittest.TestCase):
    """call_ollama: 接続エラー時に OllamaConnectionError をスロー。"""

    def setUp(self):
        """Reset warmup state before each test."""
        import obsidian_etl.utils.ollama

        obsidian_etl.utils.ollama._warmed_models.clear()

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_connection_error_raises_exception(self, mock_urlopen, mock_warmup):
        """接続エラー時に OllamaConnectionError がスローされること。

        Edge case from spec.md:
        ネットワーク接続エラーの場合 -> OllamaConnectionError
        """
        import urllib.error

        from obsidian_etl.utils.ollama import OllamaConnectionError, call_ollama

        # Mock connection error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        with self.assertRaises(OllamaConnectionError):
            call_ollama(
                system_prompt="system",
                user_message="user",
                model="gemma3:12b",
            )

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_connection_error_has_context_len(self, mock_urlopen, mock_warmup):
        """接続エラーに context_len が含まれること。"""
        import urllib.error

        from obsidian_etl.utils.ollama import OllamaConnectionError, call_ollama

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        system_prompt = "prompt"
        user_message = "message"
        expected_context_len = len(system_prompt) + len(user_message)

        with self.assertRaises(OllamaConnectionError) as ctx:
            call_ollama(
                system_prompt=system_prompt,
                user_message=user_message,
                model="gemma3:12b",
            )

        self.assertEqual(ctx.exception.context_len, expected_context_len)


class TestCallOllamaSuccessReturnsStr(unittest.TestCase):
    """call_ollama: 正常時に str を返す（tuple ではない）。"""

    def setUp(self):
        """Reset warmup state before each test."""
        import obsidian_etl.utils.ollama

        obsidian_etl.utils.ollama._warmed_models.clear()

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_success_returns_str(self, mock_urlopen, mock_warmup):
        """正常レスポンスの場合に str が返されること（tuple ではない）。

        FR-010: call_ollama 関数は成功時にレスポンス文字列のみを返さなければならない

        US2 Acceptance Scenario 3:
        Given: 正常なレスポンスを受け取った場合
        When: call_ollama が呼ばれるとき
        Then: レスポンス文字列が返される（例外はスローされない）
        """
        from obsidian_etl.utils.ollama import call_ollama

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "Hello, world!"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = call_ollama(
            system_prompt="system",
            user_message="user",
            model="gemma3:12b",
        )

        # Result should be a string, not a tuple
        self.assertIsInstance(result, str)
        self.assertEqual(result, "Hello, world!")

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_success_not_tuple(self, mock_urlopen, mock_warmup):
        """正常レスポンスの戻り値が tuple ではないこと。

        変更前: tuple[str, str | None]
        変更後: str
        """
        from obsidian_etl.utils.ollama import call_ollama

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "response text"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = call_ollama(
            system_prompt="system",
            user_message="user",
            model="gemma3:12b",
        )

        self.assertNotIsInstance(result, tuple)

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_success_with_unicode_response(self, mock_urlopen, mock_warmup):
        """Unicode を含むレスポンスが正しく返されること。

        Edge case: Unicode/特殊文字
        """
        from obsidian_etl.utils.ollama import call_ollama

        mock_response = MagicMock()
        content = "# AI技術の概要\n\n日本語の要約テスト"
        import json

        mock_response.read.return_value = json.dumps({"message": {"content": content}}).encode(
            "utf-8"
        )
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = call_ollama(
            system_prompt="system",
            user_message="user",
            model="gemma3:12b",
        )

        self.assertEqual(result, content)


if __name__ == "__main__":
    unittest.main()
