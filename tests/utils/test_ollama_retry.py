"""Tests for Ollama retry functionality.

Retry feature tests verify:
- Retry on OllamaEmptyResponseError
- No retry on OllamaTimeoutError or OllamaConnectionError
- max_retries parameter is respected
- Successful response after retry
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from obsidian_etl.utils.ollama_config import OllamaConfig


class TestOllamaRetry(unittest.TestCase):
    """Test retry behavior in call_ollama."""

    def setUp(self):
        """Reset warmup state before each test."""
        import obsidian_etl.utils.ollama

        obsidian_etl.utils.ollama._warmed_models.clear()

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.time.sleep")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_retry_on_empty_response(self, mock_urlopen, mock_sleep, mock_warmup):
        """空レスポンス時にリトライすること。

        Given: LLM が最初は空レスポンスを返し、2回目は正常レスポンスを返す
        When: call_ollama が呼ばれる
        Then: リトライして成功
        """
        from obsidian_etl.utils.ollama import call_ollama

        # First call returns empty, second returns content
        mock_response_empty = MagicMock()
        mock_response_empty.read.return_value = b'{"message": {"content": ""}}'

        mock_response_ok = MagicMock()
        mock_response_ok.read.return_value = b'{"message": {"content": "success"}}'

        mock_urlopen.return_value.__enter__.side_effect = [
            mock_response_empty,
            mock_response_ok,
        ]

        config = OllamaConfig(model="gemma3:12b", max_retries=3, retry_delay=0.1)
        result = call_ollama("test", "test", config)

        self.assertEqual(result, "success")
        self.assertEqual(mock_urlopen.call_count, 2)
        mock_sleep.assert_called_once_with(0.1)

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.time.sleep")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_max_retries_exhausted(self, mock_urlopen, mock_sleep, mock_warmup):
        """リトライ上限に達したら例外を発生させること。

        Given: LLM が常に空レスポンスを返す
        When: call_ollama が max_retries=2 で呼ばれる
        Then: 3回試行後（初回 + 2回リトライ）に OllamaEmptyResponseError
        """
        from obsidian_etl.utils.ollama import OllamaEmptyResponseError, call_ollama

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": ""}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        config = OllamaConfig(model="gemma3:12b", max_retries=2, retry_delay=0.1)

        with self.assertRaises(OllamaEmptyResponseError):
            call_ollama("test", "test", config)

        # 1 initial + 2 retries = 3 total calls
        self.assertEqual(mock_urlopen.call_count, 3)
        # sleep called twice (after each failed attempt except the last)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.time.sleep")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_no_retry_on_timeout(self, mock_urlopen, mock_sleep, mock_warmup):
        """タイムアウト時はリトライしないこと。

        Given: LLM がタイムアウトする
        When: call_ollama が呼ばれる
        Then: リトライせずに OllamaTimeoutError
        """
        from obsidian_etl.utils.ollama import OllamaTimeoutError, call_ollama

        mock_urlopen.return_value.__enter__.side_effect = TimeoutError("timeout")

        config = OllamaConfig(model="gemma3:12b", max_retries=3)

        with self.assertRaises(OllamaTimeoutError):
            call_ollama("test", "test", config)

        # Only 1 call, no retries
        self.assertEqual(mock_urlopen.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.time.sleep")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_success_on_first_try(self, mock_urlopen, mock_sleep, mock_warmup):
        """初回成功時はリトライしないこと。

        Given: LLM が正常レスポンスを返す
        When: call_ollama が呼ばれる
        Then: リトライなしで成功
        """
        from obsidian_etl.utils.ollama import call_ollama

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "success"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        config = OllamaConfig(model="gemma3:12b", max_retries=3)
        result = call_ollama("test", "test", config)

        self.assertEqual(result, "success")
        self.assertEqual(mock_urlopen.call_count, 1)
        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
