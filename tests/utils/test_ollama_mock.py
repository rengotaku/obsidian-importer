"""Tests for ollama_mock module."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from obsidian_etl.utils.ollama_mock import (
    _detect_function,
    _load_golden_index,
    _lookup_golden_response,
    _user_message_hash,
    mock_call_ollama,
    mock_check_ollama_connection,
)


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


class TestDetectFunction(unittest.TestCase):
    """Test _detect_function correctly identifies the calling function."""

    def test_extract_topic_and_genre(self) -> None:
        """Should detect extract_topic_and_genre from system prompt."""
        prompt = "主題とジャンルをJSON形式で答えてください。"
        self.assertEqual(_detect_function(prompt), "extract_topic_and_genre")

    def test_extract_topic(self) -> None:
        """Should detect extract_topic from system prompt."""
        prompt = "トピック分類の専門家です。主題を1つ抽出してください。"
        self.assertEqual(_detect_function(prompt), "extract_topic")

    def test_suggest_genres(self) -> None:
        """Should detect suggest_genres from system prompt."""
        prompt = "新しいジャンルを提案してください。"
        self.assertEqual(_detect_function(prompt), "suggest_genres")

    def test_translate_summary(self) -> None:
        """Should detect translate_summary from system prompt."""
        prompt = "以下の英語を日本語に翻訳してください。"
        self.assertEqual(_detect_function(prompt), "translate_summary")

    def test_extract_knowledge_default(self) -> None:
        """Should default to extract_knowledge."""
        prompt = "会話ログから知識を抽出してください。"
        self.assertEqual(_detect_function(prompt), "extract_knowledge")


class TestUserMessageHash(unittest.TestCase):
    """Test _user_message_hash produces consistent hashes."""

    def test_deterministic(self) -> None:
        """Same input should produce same hash."""
        msg = "test message"
        self.assertEqual(_user_message_hash(msg), _user_message_hash(msg))

    def test_different_inputs(self) -> None:
        """Different inputs should produce different hashes."""
        self.assertNotEqual(_user_message_hash("a"), _user_message_hash("b"))

    def test_hash_length(self) -> None:
        """Hash should be 16 characters."""
        self.assertEqual(len(_user_message_hash("test")), 16)


class TestGoldenResponseLookup(unittest.TestCase):
    """Test golden response file lookup."""

    def setUp(self) -> None:
        """Reset golden cache before each test."""
        from obsidian_etl.utils import ollama_mock

        ollama_mock._golden_cache["index"] = None

    def test_load_golden_index(self) -> None:
        """Should load index from disk."""
        index = _load_golden_index()
        self.assertIsInstance(index, dict)

    def test_golden_index_cached(self) -> None:
        """Index should be loaded only once."""
        index1 = _load_golden_index()
        index2 = _load_golden_index()
        self.assertIs(index1, index2)

    def test_lookup_returns_none_for_unknown(self) -> None:
        """Should return None for unknown function/message combo."""
        result = _lookup_golden_response("extract_knowledge", "unknown_message_12345")
        self.assertIsNone(result)

    def test_golden_files_exist(self) -> None:
        """All golden files referenced in index should exist."""
        golden_dir = Path(__file__).parent.parent / "fixtures" / "golden_responses"
        index_path = golden_dir / "_index.json"
        if not index_path.exists():
            self.skipTest("Golden response index not found")

        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)

        for key, filename in index.items():
            golden_path = golden_dir / filename
            self.assertTrue(golden_path.exists(), f"Missing golden file: {filename} (key={key})")


class TestMockWithGoldenFallback(unittest.TestCase):
    """Test mock_call_ollama with golden file fallback."""

    def setUp(self) -> None:
        """Reset golden cache before each test."""
        from obsidian_etl.utils import ollama_mock

        ollama_mock._golden_cache["index"] = None

    def test_fallback_when_no_golden(self) -> None:
        """Should return fallback response when no golden file matches."""
        response = mock_call_ollama("ナレッジを抽出してください", "nonexistent_user_message")
        self.assertIn("## 要約", response)
        self.assertIn("モック", response)


class TestMockCheckOllamaConnection(unittest.TestCase):
    """Test mock_check_ollama_connection."""

    def test_always_returns_true(self) -> None:
        """Mock connection check should always succeed."""
        connected, error = mock_check_ollama_connection()
        self.assertTrue(connected)
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
