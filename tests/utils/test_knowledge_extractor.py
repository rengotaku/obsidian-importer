"""Tests for knowledge_extractor exception handling.

Phase 4 (063-ollama-exception-refactor): Verify that knowledge_extractor
functions handle OllamaError exceptions from call_ollama instead of
tuple unpacking.

Tests verify:
- translate_summary catches OllamaError and returns (None, error_message)
- extract_knowledge catches OllamaError and returns (None, error_message)
- Both functions work correctly on success (call_ollama returns str)
- Logging occurs on exception
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from obsidian_etl.utils.ollama import (
    OllamaConnectionError,
    OllamaEmptyResponseError,
    OllamaError,
    OllamaTimeoutError,
)


def _make_ollama_params() -> dict:
    """Helper to create params dict with Ollama config."""
    return {
        "ollama": {
            "defaults": {
                "model": "gemma3:12b",
                "base_url": "http://localhost:11434",
                "timeout": 120,
                "temperature": 0.2,
                "num_predict": -1,
            },
        },
    }


class TestTranslateSummaryExceptionHandling(unittest.TestCase):
    """translate_summary: OllamaError 例外ハンドリング。

    call_ollama が OllamaError をスローした場合、
    translate_summary は (None, error_message) を返し、処理を継続する。
    """

    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_catches_ollama_error(self, mock_call_ollama):
        """OllamaError 発生時に (None, error_message) を返すこと。"""
        from obsidian_etl.utils.knowledge_extractor import translate_summary

        mock_call_ollama.side_effect = OllamaError("Test error")
        params = _make_ollama_params()

        result, error = translate_summary("English summary text", params)

        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn("Test error", error)

    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_catches_empty_response_error(self, mock_call_ollama):
        """OllamaEmptyResponseError 発生時に (None, error_message) を返すこと。"""
        from obsidian_etl.utils.knowledge_extractor import translate_summary

        mock_call_ollama.side_effect = OllamaEmptyResponseError(
            "Empty response from LLM", context_len=500
        )
        params = _make_ollama_params()

        result, error = translate_summary("English summary text", params)

        self.assertIsNone(result)
        self.assertIsNotNone(error)

    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_catches_timeout_error(self, mock_call_ollama):
        """OllamaTimeoutError 発生時に (None, error_message) を返すこと。"""
        from obsidian_etl.utils.knowledge_extractor import translate_summary

        mock_call_ollama.side_effect = OllamaTimeoutError("Timeout (120s)", context_len=1000)
        params = _make_ollama_params()

        result, error = translate_summary("English summary text", params)

        self.assertIsNone(result)
        self.assertIsNotNone(error)

    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_catches_connection_error(self, mock_call_ollama):
        """OllamaConnectionError 発生時に (None, error_message) を返すこと。"""
        from obsidian_etl.utils.knowledge_extractor import translate_summary

        mock_call_ollama.side_effect = OllamaConnectionError("Connection refused")
        params = _make_ollama_params()

        result, error = translate_summary("English summary text", params)

        self.assertIsNone(result)
        self.assertIsNotNone(error)

    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_success_returns_translated(self, mock_call_ollama):
        """正常時に call_ollama が str を返し、翻訳結果を取得できること。"""
        from obsidian_etl.utils.knowledge_extractor import translate_summary

        # call_ollama now returns str directly (not tuple)
        mock_call_ollama.return_value = (
            "```\n"
            "# 翻訳タイトル\n"
            "## 要約\n"
            "日本語の要約テキスト\n"
            "## タグ\n"
            "タグ1, タグ2\n"
            "## 内容\n"
            "翻訳された内容\n"
            "```"
        )
        params = _make_ollama_params()

        result, error = translate_summary("English summary text", params)

        # Should not return error for successful call
        self.assertIsNone(error)

    @patch("obsidian_etl.utils.knowledge_extractor.logger")
    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_translate_summary_logs_on_error(self, mock_call_ollama, mock_logger):
        """OllamaError 発生時にログが出力されること。"""
        from obsidian_etl.utils.knowledge_extractor import translate_summary

        mock_call_ollama.side_effect = OllamaError("LLM connection failed")
        params = _make_ollama_params()

        translate_summary("English summary text", params)

        # Should log the error
        mock_logger.warning.assert_called()


class TestExtractKnowledgeExceptionHandling(unittest.TestCase):
    """extract_knowledge: OllamaError 例外ハンドリング。

    call_ollama が OllamaError をスローした場合、
    extract_knowledge は (None, error_message) を返し、処理を継続する。
    """

    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_extract_knowledge_catches_ollama_error(self, mock_call_ollama):
        """OllamaError 発生時に (None, error_message) を返すこと。"""
        from obsidian_etl.utils.knowledge_extractor import extract_knowledge

        mock_call_ollama.side_effect = OllamaError("Test error")
        params = _make_ollama_params()

        result, error = extract_knowledge(
            "conversation content",
            "conversation-name",
            "2026-01-15",
            "claude",
            params,
        )

        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIn("Test error", error)

    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_extract_knowledge_catches_empty_response_error(self, mock_call_ollama):
        """OllamaEmptyResponseError 発生時に (None, error_message) を返すこと。"""
        from obsidian_etl.utils.knowledge_extractor import extract_knowledge

        mock_call_ollama.side_effect = OllamaEmptyResponseError("Empty response", context_len=25000)
        params = _make_ollama_params()

        result, error = extract_knowledge(
            "conversation content",
            "conversation-name",
            "2026-01-15",
            "claude",
            params,
        )

        self.assertIsNone(result)
        self.assertIsNotNone(error)

    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_extract_knowledge_catches_timeout_error(self, mock_call_ollama):
        """OllamaTimeoutError 発生時に (None, error_message) を返すこと。"""
        from obsidian_etl.utils.knowledge_extractor import extract_knowledge

        mock_call_ollama.side_effect = OllamaTimeoutError("Timeout (120s)")
        params = _make_ollama_params()

        result, error = extract_knowledge(
            "conversation content",
            "conversation-name",
            "2026-01-15",
            "claude",
            params,
        )

        self.assertIsNone(result)
        self.assertIsNotNone(error)

    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_extract_knowledge_catches_connection_error(self, mock_call_ollama):
        """OllamaConnectionError 発生時に (None, error_message) を返すこと。"""
        from obsidian_etl.utils.knowledge_extractor import extract_knowledge

        mock_call_ollama.side_effect = OllamaConnectionError("Connection refused")
        params = _make_ollama_params()

        result, error = extract_knowledge(
            "conversation content",
            "conversation-name",
            "2026-01-15",
            "claude",
            params,
        )

        self.assertIsNone(result)
        self.assertIsNotNone(error)

    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_extract_knowledge_success_returns_data(self, mock_call_ollama):
        """正常時に call_ollama が str を返し、抽出結果を取得できること。"""
        from obsidian_etl.utils.knowledge_extractor import extract_knowledge

        # call_ollama now returns str directly (not tuple)
        mock_call_ollama.return_value = (
            "```\n"
            "# テストタイトル\n"
            "## 要約\n"
            "テストの要約\n"
            "## タグ\n"
            "Python, テスト\n"
            "## 内容\n"
            "テストの内容です。\n"
            "```"
        )
        params = _make_ollama_params()

        result, error = extract_knowledge(
            "conversation content",
            "conversation-name",
            "2026-01-15",
            "claude",
            params,
        )

        # Should return data dict on success
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("title"), "テストタイトル")

    @patch("obsidian_etl.utils.knowledge_extractor.logger")
    @patch("obsidian_etl.utils.knowledge_extractor.call_ollama")
    def test_extract_knowledge_logs_on_error(self, mock_call_ollama, mock_logger):
        """OllamaError 発生時にログが出力されること。"""
        from obsidian_etl.utils.knowledge_extractor import extract_knowledge

        mock_call_ollama.side_effect = OllamaError("LLM failed")
        params = _make_ollama_params()

        extract_knowledge(
            "conversation content",
            "conversation-name",
            "2026-01-15",
            "claude",
            params,
        )

        # Should log the error
        mock_logger.warning.assert_called()


if __name__ == "__main__":
    unittest.main()
