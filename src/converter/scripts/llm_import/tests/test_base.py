"""
llm_import.tests.test_base - 基底クラスのテスト
"""
from __future__ import annotations

import unittest
from dataclasses import dataclass
from pathlib import Path

from scripts.llm_import.base import (
    BaseMessage,
    BaseConversation,
    BaseParser,
    sanitize_filename,
)


# =============================================================================
# Concrete Implementations for Testing
# =============================================================================


@dataclass
class TestMessage(BaseMessage):
    """テスト用メッセージ実装"""
    sender: str  # "user" | "assistant"

    @property
    def role(self) -> str:
        return self.sender


@dataclass
class TestConversation(BaseConversation):
    """テスト用会話実装"""
    uuid: str
    _messages: list = None

    def __post_init__(self):
        if self._messages is None:
            self._messages = []

    @property
    def messages(self) -> list:
        return self._messages

    @property
    def id(self) -> str:
        return self.uuid

    @property
    def provider(self) -> str:
        return "test"


class TestParser(BaseParser):
    """テスト用パーサー実装"""

    @property
    def provider_name(self) -> str:
        return "test"

    def parse(self, export_path: Path) -> list[BaseConversation]:
        return []

    def to_markdown(self, conversation: BaseConversation) -> str:
        return f"# {conversation.title}"


# =============================================================================
# Test Cases
# =============================================================================


class TestBaseMessage(unittest.TestCase):
    """BaseMessage のテスト"""

    def test_message_creation(self):
        """メッセージが正しく作成されること"""
        msg = TestMessage(
            content="Hello",
            timestamp="2026-01-16T10:00:00",
            sender="user",
        )
        self.assertEqual(msg.content, "Hello")
        self.assertEqual(msg.timestamp, "2026-01-16T10:00:00")
        self.assertEqual(msg.role, "user")

    def test_assistant_role(self):
        """アシスタントのロールが正しく返ること"""
        msg = TestMessage(
            content="Hi there",
            timestamp="2026-01-16T10:00:01",
            sender="assistant",
        )
        self.assertEqual(msg.role, "assistant")


class TestBaseConversation(unittest.TestCase):
    """BaseConversation のテスト"""

    def test_conversation_creation(self):
        """会話が正しく作成されること"""
        conv = TestConversation(
            title="Test Conversation",
            created_at="2026-01-16T10:00:00",
            uuid="test-uuid-1234",
        )
        self.assertEqual(conv.title, "Test Conversation")
        self.assertEqual(conv.id, "test-uuid-1234")
        self.assertEqual(conv.provider, "test")

    def test_conversation_with_messages(self):
        """メッセージ付き会話が正しく作成されること"""
        messages = [
            TestMessage(content="Hello", timestamp="2026-01-16T10:00:00", sender="user"),
            TestMessage(content="Hi!", timestamp="2026-01-16T10:00:01", sender="assistant"),
        ]
        conv = TestConversation(
            title="Chat",
            created_at="2026-01-16T10:00:00",
            uuid="conv-1",
            _messages=messages,
        )
        self.assertEqual(len(conv.messages), 2)
        self.assertEqual(conv.messages[0].content, "Hello")
        self.assertEqual(conv.messages[1].content, "Hi!")


class TestBaseParser(unittest.TestCase):
    """BaseParser のテスト"""

    def test_provider_name(self):
        """プロバイダー名が正しく返ること"""
        parser = TestParser()
        self.assertEqual(parser.provider_name, "test")

    def test_get_output_dir(self):
        """出力ディレクトリパスが正しく生成されること"""
        parser = TestParser()
        base_dir = Path("/home/user/obsidian/@index/llm_exports")
        output_dir = parser.get_output_dir(base_dir)
        expected = Path("/home/user/obsidian/@index/llm_exports/test/parsed/conversations")
        self.assertEqual(output_dir, expected)

    def test_to_markdown(self):
        """Markdown 変換が動作すること"""
        parser = TestParser()
        conv = TestConversation(
            title="My Chat",
            created_at="2026-01-16T10:00:00",
            uuid="test-1",
        )
        result = parser.to_markdown(conv)
        self.assertEqual(result, "# My Chat")


class TestSanitizeFilename(unittest.TestCase):
    """sanitize_filename のテスト"""

    def test_basic_sanitization(self):
        """基本的なサニタイズが動作すること"""
        self.assertEqual(sanitize_filename("Hello World"), "Hello World")

    def test_forbidden_chars(self):
        """禁止文字が置換されること"""
        self.assertEqual(sanitize_filename("file<name>test"), "file_name_test")
        self.assertEqual(sanitize_filename('file:name/test'), "file_name_test")
        self.assertEqual(sanitize_filename("file|name?test"), "file_name_test")

    def test_consecutive_underscores(self):
        """連続アンダースコアが単一になること"""
        self.assertEqual(sanitize_filename("file__name___test"), "file_name_test")

    def test_trim_edges(self):
        """先頭/末尾の空白・アンダースコアが除去されること"""
        self.assertEqual(sanitize_filename("  _title_  "), "title")
        self.assertEqual(sanitize_filename("___test___"), "test")

    def test_max_length(self):
        """最大長で切り詰められること"""
        long_title = "a" * 100
        result = sanitize_filename(long_title, max_length=80)
        self.assertEqual(len(result), 80)

    def test_empty_result(self):
        """空になった場合は untitled が返ること"""
        self.assertEqual(sanitize_filename("___"), "untitled")
        self.assertEqual(sanitize_filename(""), "untitled")

    def test_japanese_title(self):
        """日本語タイトルが正しく処理されること"""
        self.assertEqual(sanitize_filename("Pythonの基礎"), "Pythonの基礎")
        # 全角コロン（：）は禁止文字ではない、半角コロン（:）が禁止
        self.assertEqual(sanitize_filename("テスト：サンプル"), "テスト：サンプル")
        self.assertEqual(sanitize_filename("テスト:サンプル"), "テスト_サンプル")


if __name__ == "__main__":
    unittest.main()
