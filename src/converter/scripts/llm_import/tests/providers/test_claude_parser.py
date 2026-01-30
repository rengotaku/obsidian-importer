"""
llm_import.tests.providers.test_claude_parser - ClaudeParser のテスト
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

# テスト対象モジュールは後で実装される
# from scripts.llm_import.providers.claude.parser import ClaudeParser, ClaudeConversation, ClaudeMessage


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestClaudeParser(unittest.TestCase):
    """ClaudeParser のテスト"""

    def setUp(self):
        """テストセットアップ"""
        # 実装後にコメント解除
        from scripts.llm_import.providers.claude.parser import ClaudeParser
        self.parser = ClaudeParser()
        self.single_fixture = FIXTURES_DIR / "claude_conversation_single.json"
        self.multi_fixture = FIXTURES_DIR / "claude_export_sample.json"

    def test_parser_provider_name(self):
        """プロバイダー名が 'claude' であること"""
        self.assertEqual(self.parser.provider_name, "claude")

    def test_parse_single_conversation(self):
        """単一会話のパースが正しく動作すること"""
        conversations = self.parser.parse(self.single_fixture)

        self.assertEqual(len(conversations), 1)

        conv = conversations[0]
        self.assertEqual(conv.uuid, "154457f7-2ec2-4c8d-9751-0bbfe6d64fa9")
        self.assertEqual(conv.title, "卓上IHでピザを保温する方法")
        self.assertEqual(conv.provider, "claude")
        self.assertEqual(len(conv.messages), 2)

    def test_parse_multiple_conversations(self):
        """複数会話のパースが正しく動作すること"""
        conversations = self.parser.parse(self.multi_fixture)

        # 4会話がfixtureにあるはず
        self.assertEqual(len(conversations), 4)

        # 各会話がClaudeConversationであることを確認
        for conv in conversations:
            self.assertEqual(conv.provider, "claude")
            self.assertTrue(len(conv.uuid) > 0)

    def test_conversation_has_summary(self):
        """サマリーが正しく抽出されること"""
        conversations = self.parser.parse(self.single_fixture)
        conv = conversations[0]

        self.assertIsNotNone(conv.summary)
        self.assertIn("Conversation Overview", conv.summary)

    def test_message_structure(self):
        """メッセージ構造が正しいこと"""
        conversations = self.parser.parse(self.single_fixture)
        conv = conversations[0]

        # 最初のメッセージ（ユーザー）
        user_msg = conv.messages[0]
        self.assertEqual(user_msg.role, "user")
        self.assertIn("ピザ", user_msg.content)

        # 2番目のメッセージ（アシスタント）
        assistant_msg = conv.messages[1]
        self.assertEqual(assistant_msg.role, "assistant")
        self.assertIn("IH対応", assistant_msg.content)

    def test_to_markdown_basic(self):
        """Markdown変換の基本機能"""
        conversations = self.parser.parse(self.single_fixture)
        conv = conversations[0]

        md = self.parser.to_markdown(conv)

        # 基本構造を確認
        self.assertIn("---", md)  # frontmatter
        self.assertIn("title:", md)
        self.assertIn("created:", md)
        self.assertIn("## 会話", md)  # 会話セクション

    def test_to_markdown_contains_messages(self):
        """Markdown にメッセージが含まれること"""
        conversations = self.parser.parse(self.single_fixture)
        conv = conversations[0]

        md = self.parser.to_markdown(conv)

        self.assertIn("**User**:", md)
        self.assertIn("**Assistant**:", md)
        self.assertIn("ピザ", md)

    def test_to_markdown_with_file_id(self):
        """file_id が frontmatter に含まれること (T007: US1)"""
        conversations = self.parser.parse(self.single_fixture)
        conv = conversations[0]

        test_file_id = "a1b2c3d4e5f6"
        md = self.parser.to_markdown(conv, file_id=test_file_id)

        # file_id が frontmatter に含まれる
        self.assertIn("file_id: a1b2c3d4e5f6", md)

        # frontmatter 内の正しい位置にあること（uuid の後）
        lines = md.split("\n")
        uuid_line = next(i for i, line in enumerate(lines) if line.startswith("uuid:"))
        file_id_line = next(i for i, line in enumerate(lines) if line.startswith("file_id:"))
        self.assertEqual(file_id_line, uuid_line + 1)

    def test_to_markdown_without_file_id(self):
        """file_id なしの場合、frontmatter に file_id が含まれないこと (T007: US1)"""
        conversations = self.parser.parse(self.single_fixture)
        conv = conversations[0]

        md = self.parser.to_markdown(conv)

        # file_id が含まれない
        self.assertNotIn("file_id:", md)

    def test_to_markdown_file_id_none_explicitly(self):
        """file_id=None の場合、frontmatter に file_id が含まれないこと (T007: US1)"""
        conversations = self.parser.parse(self.single_fixture)
        conv = conversations[0]

        md = self.parser.to_markdown(conv, file_id=None)

        # file_id が含まれない
        self.assertNotIn("file_id:", md)

    def test_empty_conversations_file(self):
        """空の会話配列を処理できること"""
        # 一時的なテストファイル作成
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_path = Path(f.name)

        try:
            conversations = self.parser.parse(temp_path)
            self.assertEqual(len(conversations), 0)
        finally:
            temp_path.unlink()

    def test_conversation_with_no_messages(self):
        """メッセージがない会話をスキップすること"""
        import tempfile
        data = [{
            "uuid": "test-uuid",
            "name": "Empty conversation",
            "summary": None,
            "created_at": "2026-01-16T10:00:00Z",
            "updated_at": "2026-01-16T10:00:00Z",
            "chat_messages": []
        }]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            conversations = self.parser.parse(temp_path)
            # メッセージがない会話も含める（スキップはextractor側で判断）
            self.assertEqual(len(conversations), 1)
        finally:
            temp_path.unlink()


class TestClaudeConversation(unittest.TestCase):
    """ClaudeConversation のテスト"""

    def test_conversation_id_is_uuid(self):
        """会話IDがUUIDと一致すること"""
        from scripts.llm_import.providers.claude.parser import ClaudeConversation, ClaudeMessage

        msg = ClaudeMessage(
            uuid="msg-1",
            content="Hello",
            timestamp="2026-01-16T10:00:00",
            sender="human",
        )
        conv = ClaudeConversation(
            uuid="conv-uuid-1234",
            title="Test",
            created_at="2026-01-16T10:00:00",
            updated_at="2026-01-16T10:00:00",
            summary=None,
            _messages=[msg],
        )

        self.assertEqual(conv.id, "conv-uuid-1234")
        self.assertEqual(conv.provider, "claude")


class TestClaudeMessage(unittest.TestCase):
    """ClaudeMessage のテスト"""

    def test_human_role(self):
        """human sender が user role になること"""
        from scripts.llm_import.providers.claude.parser import ClaudeMessage

        msg = ClaudeMessage(
            uuid="msg-1",
            content="Hello",
            timestamp="2026-01-16T10:00:00",
            sender="human",
        )
        self.assertEqual(msg.role, "user")

    def test_assistant_role(self):
        """assistant sender が assistant role になること"""
        from scripts.llm_import.providers.claude.parser import ClaudeMessage

        msg = ClaudeMessage(
            uuid="msg-1",
            content="Hi there",
            timestamp="2026-01-16T10:00:00",
            sender="assistant",
        )
        self.assertEqual(msg.role, "assistant")


if __name__ == "__main__":
    unittest.main()
