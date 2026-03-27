"""Tests for Ollama warmup functionality.

Warmup feature tests verify:
- _do_warmup is called on first invocation for each model
- Subsequent calls skip warmup
- Warmup happens per model (different models are warmed independently)
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, call, patch

from obsidian_etl.utils.ollama_config import OllamaConfig


class TestOllamaWarmup(unittest.TestCase):
    """Test warmup behavior in call_ollama."""

    def setUp(self):
        """Reset warmup state before each test."""
        # Reset the module-level _warmed_models set
        import obsidian_etl.utils.ollama

        obsidian_etl.utils.ollama._warmed_models.clear()

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_warmup_called_on_first_invocation(self, mock_urlopen, mock_warmup):
        """初回呼び出し時に _do_warmup が呼ばれること。

        Given: モデルが一度も使用されていない
        When: call_ollama が呼ばれる
        Then: _do_warmup が実行される
        """
        from obsidian_etl.utils.ollama import call_ollama

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "test"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        config = OllamaConfig(model="gemma3:12b")

        # First call to model
        call_ollama("test", "test", config)

        # Warmup should be called (with default warmup_timeout=30)
        mock_warmup.assert_called_once_with("gemma3:12b", "http://localhost:11434", 30)

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_warmup_skipped_on_second_invocation(self, mock_urlopen, mock_warmup):
        """2回目以降の呼び出し時に _do_warmup がスキップされること。

        Given: モデルが既に使用されている
        When: 同じモデルで call_ollama が再度呼ばれる
        Then: _do_warmup は実行されない
        """
        from obsidian_etl.utils.ollama import call_ollama

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "test"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        config = OllamaConfig(model="gemma3:12b")

        # First call
        call_ollama("test", "test", config)

        # Second call
        call_ollama("test", "test", config)

        # Warmup should be called only once (on first call, with default warmup_timeout=30)
        mock_warmup.assert_called_once_with("gemma3:12b", "http://localhost:11434", 30)

    @patch("obsidian_etl.utils.ollama._do_warmup")
    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_warmup_per_model(self, mock_urlopen, mock_warmup):
        """異なるモデルは個別にウォームアップされること。

        Given: 複数の異なるモデルが使用される
        When: call_ollama が異なるモデルで呼ばれる
        Then: 各モデルで _do_warmup が実行される
        """
        from obsidian_etl.utils.ollama import call_ollama

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "test"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        config_a = OllamaConfig(model="gemma3:12b")
        config_b = OllamaConfig(model="llama3.2:3b")

        # Call with model A
        call_ollama("test", "test", config_a)

        # Call with model B
        call_ollama("test", "test", config_b)

        # Warmup should be called once for each model (with default warmup_timeout=30)
        self.assertEqual(mock_warmup.call_count, 2)
        mock_warmup.assert_has_calls(
            [
                call("gemma3:12b", "http://localhost:11434", 30),
                call("llama3.2:3b", "http://localhost:11434", 30),
            ]
        )


class TestDoWarmup(unittest.TestCase):
    """Test _do_warmup helper function."""

    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_warmup_sends_minimal_request(self, mock_urlopen):
        """_do_warmup が最小限のリクエストを送信すること。

        Given: モデル名とベースURLが与えられる
        When: _do_warmup が呼ばれる
        Then: num_predict=1 の最小限のリクエストが送信される
        """
        from obsidian_etl.utils.ollama import _do_warmup

        # Mock responses for warmup (POST /api/chat) and device check (GET /api/ps)
        mock_warmup_response = MagicMock()
        mock_warmup_response.read.return_value = b'{"message": {"content": "hi"}}'

        mock_ps_response = MagicMock()
        mock_ps_response.read.return_value = (
            b'{"models": [{"name": "gemma3:12b", "size": 1000, "size_vram": 1000}]}'
        )

        # Return different responses for different calls
        mock_urlopen.return_value.__enter__.side_effect = [mock_warmup_response, mock_ps_response]

        _do_warmup("gemma3:12b", "http://localhost:11434")

        # Verify urlopen was called twice (warmup + device check)
        self.assertEqual(mock_urlopen.call_count, 2)

        # Verify first request (warmup) payload
        request_obj = mock_urlopen.call_args_list[0][0][0]
        self.assertEqual(request_obj.get_method(), "POST")
        self.assertIn("http://localhost:11434/api/chat", request_obj.full_url)

    @patch("urllib.request.urlopen")
    def test_warmup_raises_error_on_cpu_fallback(self, mock_urlopen: MagicMock) -> None:
        """CPU フォールバック時に OllamaCPUFallbackError が発生すること。"""
        from obsidian_etl.utils.ollama import OllamaCPUFallbackError, _do_warmup

        # Mock responses: warmup succeeds, but device check shows CPU
        mock_warmup_response = MagicMock()
        mock_warmup_response.read.return_value = b'{"message": {"content": "hi"}}'

        mock_ps_response = MagicMock()
        # size_vram = 0 means 100% CPU
        mock_ps_response.read.return_value = (
            b'{"models": [{"name": "gemma3:12b", "size": 1000, "size_vram": 0}]}'
        )

        mock_urlopen.return_value.__enter__.side_effect = [
            mock_warmup_response,
            mock_ps_response,
        ]

        with self.assertRaises(OllamaCPUFallbackError) as ctx:
            _do_warmup("gemma3:12b", "http://localhost:11434")

        self.assertIn("CPU", str(ctx.exception))
        self.assertEqual(ctx.exception.gpu_percent, 0.0)


if __name__ == "__main__":
    unittest.main()
