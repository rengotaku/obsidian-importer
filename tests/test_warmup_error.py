"""Tests for OllamaWarmupError and warmup failure behavior.

Phase 2 (US1): Warmup failure should raise OllamaWarmupError
instead of silently logging a warning.

Tests verify:
- OllamaWarmupError exception class exists with model/reason attributes
- _do_warmup raises OllamaWarmupError on timeout
- _do_warmup raises OllamaWarmupError on connection error
- call_ollama propagates OllamaWarmupError (does not catch it)
- _warmed_models is only updated on successful warmup
"""

from __future__ import annotations

import unittest
import urllib.error
from unittest.mock import MagicMock, patch


class TestOllamaWarmupError(unittest.TestCase):
    """OllamaWarmupError exception class tests."""

    def test_exception_class_exists(self):
        """OllamaWarmupError がインポートできること。"""
        from obsidian_etl.utils.ollama import OllamaWarmupError

        self.assertTrue(issubclass(OllamaWarmupError, Exception))

    def test_exception_has_model_attribute(self):
        """OllamaWarmupError が model 属性を持つこと。"""
        from obsidian_etl.utils.ollama import OllamaWarmupError

        error = OllamaWarmupError(model="gemma3:12b", reason="timeout")
        self.assertEqual(error.model, "gemma3:12b")

    def test_exception_has_reason_attribute(self):
        """OllamaWarmupError が reason 属性を持つこと。"""
        from obsidian_etl.utils.ollama import OllamaWarmupError

        error = OllamaWarmupError(model="gemma3:12b", reason="Connection refused")
        self.assertEqual(error.reason, "Connection refused")

    def test_exception_str_contains_model_and_reason(self):
        """OllamaWarmupError の文字列表現にモデル名と理由が含まれること。"""
        from obsidian_etl.utils.ollama import OllamaWarmupError

        error = OllamaWarmupError(model="gemma3:12b", reason="timeout")
        error_str = str(error)
        self.assertIn("gemma3:12b", error_str)
        self.assertIn("timeout", error_str)


class TestDoWarmupRaisesOnTimeout(unittest.TestCase):
    """_do_warmup raises OllamaWarmupError on timeout."""

    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_do_warmup_raises_on_timeout(self, mock_urlopen):
        """_do_warmup がタイムアウト時に OllamaWarmupError を raise すること。

        Given: Ollama API がタイムアウトする
        When: _do_warmup が呼ばれる
        Then: OllamaWarmupError が発生する
        """
        from obsidian_etl.utils.ollama import OllamaWarmupError, _do_warmup

        mock_urlopen.side_effect = TimeoutError("Connection timed out")

        with self.assertRaises(OllamaWarmupError) as ctx:
            _do_warmup("gemma3:12b", "http://localhost:11434")

        self.assertEqual(ctx.exception.model, "gemma3:12b")
        self.assertIn("timeout", ctx.exception.reason.lower())


class TestDoWarmupRaisesOnConnectionError(unittest.TestCase):
    """_do_warmup raises OllamaWarmupError on connection error."""

    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_do_warmup_raises_on_connection_refused(self, mock_urlopen):
        """_do_warmup が接続エラー時に OllamaWarmupError を raise すること。

        Given: Ollama サーバーに接続できない
        When: _do_warmup が呼ばれる
        Then: OllamaWarmupError が発生する
        """
        from obsidian_etl.utils.ollama import OllamaWarmupError, _do_warmup

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        with self.assertRaises(OllamaWarmupError) as ctx:
            _do_warmup("gemma3:12b", "http://localhost:11434")

        self.assertEqual(ctx.exception.model, "gemma3:12b")
        self.assertIn("Connection refused", ctx.exception.reason)

    @patch("obsidian_etl.utils.ollama.urllib.request.urlopen")
    def test_do_warmup_raises_on_generic_exception(self, mock_urlopen):
        """_do_warmup が一般的なエラー時にも OllamaWarmupError を raise すること。

        Given: 予期しないエラーが発生する
        When: _do_warmup が呼ばれる
        Then: OllamaWarmupError が発生する
        """
        from obsidian_etl.utils.ollama import OllamaWarmupError, _do_warmup

        mock_urlopen.side_effect = OSError("Network unreachable")

        with self.assertRaises(OllamaWarmupError) as ctx:
            _do_warmup("llama3.2:3b", "http://localhost:11434")

        self.assertEqual(ctx.exception.model, "llama3.2:3b")


class TestCallOllamaPropagatesWarmupError(unittest.TestCase):
    """call_ollama propagates OllamaWarmupError without catching it."""

    def setUp(self):
        """Reset warmup state before each test."""
        import obsidian_etl.utils.ollama

        obsidian_etl.utils.ollama._warmed_models.clear()

    @patch("obsidian_etl.utils.ollama._do_warmup")
    def test_call_ollama_propagates_warmup_error(self, mock_warmup):
        """call_ollama が OllamaWarmupError をキャッチせず伝播させること。

        Given: _do_warmup が OllamaWarmupError を raise する
        When: call_ollama が呼ばれる
        Then: OllamaWarmupError が呼び出し元に伝播する
        """
        from obsidian_etl.utils.ollama import OllamaWarmupError, call_ollama

        mock_warmup.side_effect = OllamaWarmupError(model="gemma3:12b", reason="Connection refused")

        with self.assertRaises(OllamaWarmupError):
            call_ollama(
                system_prompt="test",
                user_message="test",
                model="gemma3:12b",
                base_url="http://localhost:11434",
            )

    @patch("obsidian_etl.utils.ollama._do_warmup")
    def test_warmed_models_not_updated_on_failure(self, mock_warmup):
        """ウォームアップ失敗時に _warmed_models が更新されないこと。

        Given: _do_warmup が OllamaWarmupError を raise する
        When: call_ollama が呼ばれる
        Then: _warmed_models にモデルが追加されない
        """
        import obsidian_etl.utils.ollama
        from obsidian_etl.utils.ollama import OllamaWarmupError, call_ollama

        mock_warmup.side_effect = OllamaWarmupError(model="gemma3:12b", reason="timeout")

        with self.assertRaises(OllamaWarmupError):
            call_ollama(
                system_prompt="test",
                user_message="test",
                model="gemma3:12b",
                base_url="http://localhost:11434",
            )

        self.assertNotIn("gemma3:12b", obsidian_etl.utils.ollama._warmed_models)


if __name__ == "__main__":
    unittest.main()
