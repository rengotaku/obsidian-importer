"""Tests for Ollama warmup functionality.

Warmup feature tests verify:
- _do_warmup is called on first invocation for each model
- Subsequent calls skip warmup
- Warmup happens per model (different models are warmed independently)
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, call, patch


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

        # First call to model
        call_ollama(
            system_prompt="test",
            user_message="test",
            model="gemma3:12b",
            base_url="http://localhost:11434",
        )

        # Warmup should be called
        mock_warmup.assert_called_once_with("gemma3:12b", "http://localhost:11434")

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

        # First call
        call_ollama(
            system_prompt="test",
            user_message="test",
            model="gemma3:12b",
            base_url="http://localhost:11434",
        )

        # Second call
        call_ollama(
            system_prompt="test",
            user_message="test",
            model="gemma3:12b",
            base_url="http://localhost:11434",
        )

        # Warmup should be called only once (on first call)
        mock_warmup.assert_called_once_with("gemma3:12b", "http://localhost:11434")

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

        # Call with model A
        call_ollama(
            system_prompt="test",
            user_message="test",
            model="gemma3:12b",
            base_url="http://localhost:11434",
        )

        # Call with model B
        call_ollama(
            system_prompt="test",
            user_message="test",
            model="llama3.2:3b",
            base_url="http://localhost:11434",
        )

        # Warmup should be called once for each model
        self.assertEqual(mock_warmup.call_count, 2)
        mock_warmup.assert_has_calls(
            [
                call("gemma3:12b", "http://localhost:11434"),
                call("llama3.2:3b", "http://localhost:11434"),
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

        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "hi"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        _do_warmup("gemma3:12b", "http://localhost:11434")

        # Verify urlopen was called
        self.assertEqual(mock_urlopen.call_count, 1)

        # Verify request payload (minimal request with num_predict=1)
        request_obj = mock_urlopen.call_args[0][0]
        self.assertEqual(request_obj.get_method(), "POST")
        self.assertIn("http://localhost:11434/api/chat", request_obj.full_url)

    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_warmup_handles_failure_gracefully(self, mock_urlopen):
        """_do_warmup がエラー時に例外を投げずに警告ログを出すこと。

        Given: Ollama API がエラーを返す
        When: _do_warmup が呼ばれる
        Then: 例外は発生せず、警告ログが出力される
        """
        from obsidian_etl.utils.ollama import _do_warmup

        # Mock connection error
        mock_urlopen.side_effect = ConnectionError("Connection failed")

        # Should not raise exception
        try:
            _do_warmup("gemma3:12b", "http://localhost:11434")
        except Exception as e:
            self.fail(f"_do_warmup should not raise exception: {e}")


if __name__ == "__main__":
    unittest.main()
