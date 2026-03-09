"""Tests for ollama_mock module."""

from __future__ import annotations

import json
import unittest

from obsidian_etl.utils.ollama_mock import mock_call_ollama, mock_check_ollama_connection


class TestMockCallOllama(unittest.TestCase):
    """Test mock_call_ollama returns appropriate responses."""

    def test_extract_knowledge_response(self) -> None:
        """Default response should be knowledge extraction format."""
        response = mock_call_ollama("ナレッジを抽出してください", "テスト内容")
        self.assertIn("# ", response)
        self.assertIn("## 要約", response)
        self.assertIn("## タグ", response)
        self.assertIn("## 内容", response)

    def test_extract_topic_and_genre_response(self) -> None:
        """Should return JSON with topic and genre for topic/genre extraction."""
        system_prompt = "主題とジャンルをJSON形式で答えてください。"
        response = mock_call_ollama(system_prompt, "テスト")
        data = json.loads(response)
        self.assertIn("topic", data)
        self.assertIn("genre", data)

    def test_extract_topic_response(self) -> None:
        """Should return short topic string for topic extraction."""
        system_prompt = "トピック分類の専門家です。会話内容から主題を1つ抽出してください。"
        response = mock_call_ollama(system_prompt, "テスト")
        self.assertTrue(len(response) < 50)

    def test_suggest_genres_response(self) -> None:
        """Should return empty JSON array for genre suggestion."""
        system_prompt = "新しいジャンルを提案してください。"
        response = mock_call_ollama(system_prompt, "テスト")
        data = json.loads(response)
        self.assertIsInstance(data, list)

    def test_translate_summary_response(self) -> None:
        """Should return markdown format for translation."""
        system_prompt = "以下の英語サマリーを日本語に翻訳してください"
        response = mock_call_ollama(system_prompt, "Test summary")
        self.assertIn("要約", response)


class TestMockCheckOllamaConnection(unittest.TestCase):
    """Test mock_check_ollama_connection."""

    def test_always_returns_true(self) -> None:
        """Mock connection check should always succeed."""
        connected, error = mock_check_ollama_connection()
        self.assertTrue(connected)
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
