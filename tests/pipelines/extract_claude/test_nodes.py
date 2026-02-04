"""Tests for Claude Extract pipeline nodes.

Phase 2 RED tests: parse_claude_json node and related validation/chunking logic.
These tests verify:
- Basic JSON parsing to ParsedItem dict
- Chunking of large conversations (25000+ chars)
- Skipping short conversations (messages < 3)
- Fallback for missing conversation name
- Structure validation (uuid, chat_messages required)
- Content validation (empty messages excluded)
- SHA256 file_id generation
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from obsidian_etl.pipelines.extract_claude.nodes import parse_claude_json

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


class TestParseCaudeJsonBasic(unittest.TestCase):
    """parse_claude_json: valid JSON -> ParsedItem dict."""

    def setUp(self):
        """Load test fixture."""
        with open(FIXTURES_DIR / "claude_input.json", encoding="utf-8") as f:
            self.raw_conversations = json.load(f)
        # Expected output reference
        with open(
            FIXTURES_DIR / "expected_outputs" / "parsed_claude_item.json",
            encoding="utf-8",
        ) as f:
            self.expected_item = json.load(f)

    def test_parse_claude_json_basic(self):
        """正常な Claude JSON から ParsedItem dict が生成されること。"""
        result = parse_claude_json(self.raw_conversations)

        # Should return dict of partition_id -> ParsedItem dict
        self.assertIsInstance(result, dict)

        # Should have 2 valid conversations (3rd has < 3 messages)
        self.assertEqual(len(result), 2)

        # Check first conversation
        first_key = list(result.keys())[0]
        first_item = result[first_key]

        # Verify ParsedItem structure
        self.assertEqual(first_item["item_id"], "conv-001-uuid-abcdef")
        self.assertEqual(first_item["source_provider"], "claude")
        self.assertEqual(first_item["conversation_name"], "Python asyncio discussion")
        self.assertEqual(first_item["created_at"], "2026-01-15T10:30:00.000000+00:00")
        self.assertIsInstance(first_item["messages"], list)
        self.assertEqual(len(first_item["messages"]), 4)
        self.assertIsInstance(first_item["content"], str)
        self.assertGreater(len(first_item["content"]), 10)
        self.assertIsInstance(first_item["file_id"], str)
        self.assertEqual(len(first_item["file_id"]), 12)  # SHA256 first 12 hex chars
        self.assertFalse(first_item["is_chunked"])
        self.assertIsNone(first_item["chunk_index"])
        self.assertIsNone(first_item["total_chunks"])
        self.assertIsNone(first_item["parent_item_id"])

    def test_parse_claude_json_message_format(self):
        """メッセージが {role, content} 形式に正規化されること。"""
        result = parse_claude_json(self.raw_conversations)

        first_item = list(result.values())[0]
        messages = first_item["messages"]

        # First message
        self.assertEqual(messages[0]["role"], "human")
        self.assertEqual(messages[0]["content"], "How does Python asyncio work?")

        # Second message
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertIn("asyncio", messages[1]["content"])

    def test_parse_claude_json_content_format(self):
        """content がフォーマット済み会話テキストであること。"""
        result = parse_claude_json(self.raw_conversations)

        first_item = list(result.values())[0]
        content = first_item["content"]

        # Content should contain formatted messages
        self.assertIn("Human:", content)
        self.assertIn("Assistant:", content)

    def test_parse_claude_json_second_conversation(self):
        """2つ目の会話も正しくパースされること。"""
        result = parse_claude_json(self.raw_conversations)

        items = list(result.values())
        second_item = items[1]

        self.assertEqual(second_item["item_id"], "conv-002-uuid-ghijkl")
        self.assertEqual(second_item["conversation_name"], "Database indexing strategies")
        self.assertEqual(len(second_item["messages"]), 4)


class TestParseCaudeJsonChunking(unittest.TestCase):
    """parse_claude_json: 25000+ char conversation -> multiple chunks."""

    def test_parse_claude_json_chunking(self):
        """25000文字以上の会話が複数チャンクに分割されること。"""
        # Create a conversation with messages exceeding 25000 chars
        long_text = "A" * 13000  # Each message ~13000 chars -> total ~26000
        conversations = [
            {
                "uuid": "conv-long-uuid",
                "name": "Long conversation",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T11:00:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-long-1",
                        "sender": "human",
                        "text": long_text,
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-long-2",
                        "sender": "assistant",
                        "text": long_text,
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-long-3",
                        "sender": "human",
                        "text": "Final question about the topic",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-long-4",
                        "sender": "assistant",
                        "text": "Here is my final answer to your question",
                        "created_at": "2026-01-20T10:01:30.000000+00:00",
                    },
                ],
            }
        ]

        result = parse_claude_json(conversations)

        # Should produce multiple chunks
        self.assertGreater(len(result), 1)

        # All chunks should have chunking metadata
        items = list(result.values())
        for item in items:
            self.assertTrue(item["is_chunked"])
            self.assertIsNotNone(item["chunk_index"])
            self.assertIsNotNone(item["total_chunks"])
            self.assertIsNotNone(item["parent_item_id"])
            self.assertEqual(item["total_chunks"], len(items))

        # Chunk indices should be sequential (0-based)
        chunk_indices = sorted(item["chunk_index"] for item in items)
        self.assertEqual(chunk_indices, list(range(len(items))))

        # All chunks share same parent_item_id
        parent_ids = {item["parent_item_id"] for item in items}
        self.assertEqual(len(parent_ids), 1)

        # Each chunk should have source_provider and conversation_name
        for item in items:
            self.assertEqual(item["source_provider"], "claude")
            self.assertEqual(item["conversation_name"], "Long conversation")


class TestParseCaudeJsonSkipShort(unittest.TestCase):
    """parse_claude_json: messages < 3 -> excluded from output."""

    def test_parse_claude_json_skip_short(self):
        """3件未満のメッセージの会話が出力から除外されること。"""
        conversations = [
            {
                "uuid": "conv-short-1",
                "name": "Too short - 1 message",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:00:30.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "Hello",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    }
                ],
            },
            {
                "uuid": "conv-short-2",
                "name": "Too short - 2 messages",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:01:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-2",
                        "sender": "human",
                        "text": "Hello",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "assistant",
                        "text": "Hi there!",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                ],
            },
            {
                "uuid": "conv-valid",
                "name": "Valid conversation",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:02:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-4",
                        "sender": "human",
                        "text": "How does X work?",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-5",
                        "sender": "assistant",
                        "text": "X works by doing Y and Z.",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-6",
                        "sender": "human",
                        "text": "Can you explain Y in detail?",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                ],
            },
        ]

        result = parse_claude_json(conversations)

        # Only the valid conversation (>= 3 messages) should be in output
        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        self.assertEqual(item["item_id"], "conv-valid")

    def test_parse_claude_json_empty_conversations(self):
        """空の会話リストの場合、空 dict が返ること。"""
        result = parse_claude_json([])
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)


class TestParseCaudeJsonMissingName(unittest.TestCase):
    """parse_claude_json: name=None -> fallback to first user message."""

    def test_parse_claude_json_missing_name(self):
        """conversation_name が None の場合、最初のユーザーメッセージにフォールバックすること。"""
        conversations = [
            {
                "uuid": "conv-noname-uuid",
                "name": None,
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:02:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "Tell me about Kubernetes networking",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-2",
                        "sender": "assistant",
                        "text": "Kubernetes networking provides a flat network model.",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "human",
                        "text": "What about services?",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                ],
            }
        ]

        result = parse_claude_json(conversations)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        # Should fallback to first user message (possibly truncated)
        self.assertIsNotNone(item["conversation_name"])
        self.assertIn("Kubernetes", item["conversation_name"])

    def test_parse_claude_json_name_missing_key(self):
        """name キーが存在しない場合も、最初のユーザーメッセージにフォールバックすること。"""
        conversations = [
            {
                "uuid": "conv-nokey-uuid",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:02:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "Explain Docker volumes",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-2",
                        "sender": "assistant",
                        "text": "Docker volumes are the preferred mechanism for persisting data.",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "human",
                        "text": "How about bind mounts?",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                ],
            }
        ]

        result = parse_claude_json(conversations)

        item = list(result.values())[0]
        self.assertIsNotNone(item["conversation_name"])
        self.assertIn("Docker", item["conversation_name"])


class TestValidateStructure(unittest.TestCase):
    """parse_claude_json: uuid, chat_messages required for valid structure."""

    def test_validate_structure_missing_uuid(self):
        """uuid が欠けている会話は除外されること。"""
        conversations = [
            {
                # No uuid field
                "name": "Missing UUID conversation",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "Hello",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-2",
                        "sender": "assistant",
                        "text": "Hi!",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "human",
                        "text": "Bye",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                ],
            }
        ]

        result = parse_claude_json(conversations)

        # Conversation without uuid should be excluded
        self.assertEqual(len(result), 0)

    def test_validate_structure_missing_chat_messages(self):
        """chat_messages が欠けている会話は除外されること。"""
        conversations = [
            {
                "uuid": "conv-no-messages",
                "name": "No messages conversation",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                # No chat_messages field
            }
        ]

        result = parse_claude_json(conversations)

        # Conversation without chat_messages should be excluded
        self.assertEqual(len(result), 0)

    def test_validate_structure_both_required_present(self):
        """uuid と chat_messages が両方ある会話は処理されること。"""
        conversations = [
            {
                "uuid": "conv-valid-struct",
                "name": "Valid structure",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:02:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "Question about Go interfaces?",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-2",
                        "sender": "assistant",
                        "text": "Go interfaces define method sets.",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "human",
                        "text": "What about embedding?",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                ],
            }
        ]

        result = parse_claude_json(conversations)
        self.assertEqual(len(result), 1)


class TestValidateContent(unittest.TestCase):
    """parse_claude_json: empty messages excluded."""

    def test_validate_content_empty_messages(self):
        """空メッセージのみの会話は除外されること。"""
        conversations = [
            {
                "uuid": "conv-empty-msgs",
                "name": "Empty messages",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:02:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-2",
                        "sender": "assistant",
                        "text": "",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "human",
                        "text": "",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                ],
            }
        ]

        result = parse_claude_json(conversations)

        # All-empty messages should be excluded (content < 10 chars)
        self.assertEqual(len(result), 0)

    def test_validate_content_mixed_empty_messages(self):
        """一部空メッセージは content に含まれず、残りの content が十分なら処理されること。"""
        conversations = [
            {
                "uuid": "conv-mixed-msgs",
                "name": "Mixed messages",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:02:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "Explain the observer pattern in detail please",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-2",
                        "sender": "assistant",
                        "text": "",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "human",
                        "text": "What about the publisher-subscriber variation?",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-4",
                        "sender": "assistant",
                        "text": "The pub-sub pattern decouples publishers and subscribers via a message broker.",
                        "created_at": "2026-01-20T10:01:30.000000+00:00",
                    },
                ],
            }
        ]

        result = parse_claude_json(conversations)

        # Should process (has enough non-empty messages)
        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        # Empty messages should be filtered from the messages list
        for msg in item["messages"]:
            self.assertGreater(len(msg["content"]), 0)


class TestFileIdGeneration(unittest.TestCase):
    """parse_claude_json: SHA256 file_id matches expected."""

    def test_file_id_generation(self):
        """file_id が SHA256 ハッシュの先頭12文字であること。"""
        conversations = [
            {
                "uuid": "conv-fileid-test",
                "name": "File ID test",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:02:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "What is hashing?",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-2",
                        "sender": "assistant",
                        "text": "Hashing maps data to fixed-size values.",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "human",
                        "text": "What are common hash algorithms?",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                ],
            }
        ]

        result = parse_claude_json(conversations)
        item = list(result.values())[0]

        file_id = item["file_id"]

        # file_id should be 12 hex chars
        self.assertEqual(len(file_id), 12)
        # Should be valid hex
        int(file_id, 16)  # Raises ValueError if not valid hex

    def test_file_id_deterministic(self):
        """同じ入力から同じ file_id が生成されること。"""
        conversations = [
            {
                "uuid": "conv-deterministic",
                "name": "Deterministic test",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:02:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "Test input",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-2",
                        "sender": "assistant",
                        "text": "Test response",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "human",
                        "text": "Another test input",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                ],
            }
        ]

        result1 = parse_claude_json(conversations)
        result2 = parse_claude_json(conversations)

        item1 = list(result1.values())[0]
        item2 = list(result2.values())[0]

        self.assertEqual(item1["file_id"], item2["file_id"])

    def test_file_id_different_for_different_content(self):
        """異なる入力からは異なる file_id が生成されること。"""
        conv_a = [
            {
                "uuid": "conv-a",
                "name": "Conv A",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:02:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "Content A",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-2",
                        "sender": "assistant",
                        "text": "Response A",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "human",
                        "text": "Follow-up A",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                ],
            }
        ]
        conv_b = [
            {
                "uuid": "conv-b",
                "name": "Conv B",
                "created_at": "2026-01-20T10:00:00.000000+00:00",
                "updated_at": "2026-01-20T10:02:00.000000+00:00",
                "chat_messages": [
                    {
                        "uuid": "msg-1",
                        "sender": "human",
                        "text": "Content B",
                        "created_at": "2026-01-20T10:00:00.000000+00:00",
                    },
                    {
                        "uuid": "msg-2",
                        "sender": "assistant",
                        "text": "Response B",
                        "created_at": "2026-01-20T10:00:30.000000+00:00",
                    },
                    {
                        "uuid": "msg-3",
                        "sender": "human",
                        "text": "Follow-up B",
                        "created_at": "2026-01-20T10:01:00.000000+00:00",
                    },
                ],
            }
        ]

        result_a = parse_claude_json(conv_a)
        result_b = parse_claude_json(conv_b)

        item_a = list(result_a.values())[0]
        item_b = list(result_b.values())[0]

        self.assertNotEqual(item_a["file_id"], item_b["file_id"])


# ============================================================
# Idempotent extract tests (Phase 6 - US2)
# ============================================================


class TestIdempotentExtract(unittest.TestCase):
    """parse_claude_json: existing output partitions -> skip items, no re-parse."""

    def _make_conversations(self) -> list[dict]:
        """Create 3 valid conversations for idempotent testing."""
        convs = []
        for i in range(3):
            convs.append(
                {
                    "uuid": f"conv-idem-{i:03d}",
                    "name": f"Idempotent test conversation {i}",
                    "created_at": f"2026-01-20T1{i}:00:00.000000+00:00",
                    "updated_at": f"2026-01-20T1{i}:30:00.000000+00:00",
                    "chat_messages": [
                        {
                            "uuid": f"msg-{i}-1",
                            "sender": "human",
                            "text": f"Question {i} about topic {i} in detail please?",
                            "created_at": f"2026-01-20T1{i}:00:00.000000+00:00",
                        },
                        {
                            "uuid": f"msg-{i}-2",
                            "sender": "assistant",
                            "text": f"Answer {i}: here is a detailed explanation of topic {i}.",
                            "created_at": f"2026-01-20T1{i}:00:30.000000+00:00",
                        },
                        {
                            "uuid": f"msg-{i}-3",
                            "sender": "human",
                            "text": f"Follow-up question {i} about sub-topic of topic {i}?",
                            "created_at": f"2026-01-20T1{i}:01:00.000000+00:00",
                        },
                    ],
                }
            )
        return convs

    def test_idempotent_extract_skips_existing(self):
        """existing_output パラメータは後方互換のため存在するが、parse はスキップしない。

        Parse stage always processes all conversations. Resume logic is handled
        by Transform nodes (extract_knowledge) instead.
        """
        conversations = self._make_conversations()

        # First run: parse all conversations
        first_result = parse_claude_json(conversations)
        self.assertEqual(len(first_result), 3)

        # Simulate existing output: 2 out of 3 items already exist
        existing_keys = list(first_result.keys())[:2]
        existing_output = {key: (lambda v=first_result[key]: v) for key in existing_keys}

        # Second run: existing_output is ignored, all conversations are parsed again
        second_result = parse_claude_json(conversations, existing_output=existing_output)

        # Parse always processes all input (no skip logic at Extract stage)
        self.assertEqual(len(second_result), 3)

    def test_idempotent_extract_all_existing_returns_empty(self):
        """existing_output パラメータは無視され、parse は常に全入力を処理する。"""
        conversations = self._make_conversations()

        # First run
        first_result = parse_claude_json(conversations)

        # All items exist
        existing_output = {key: (lambda v=val: v) for key, val in first_result.items()}

        # Second run: existing_output is ignored, all conversations are parsed again
        second_result = parse_claude_json(conversations, existing_output=existing_output)
        # Parse always processes all input
        self.assertEqual(len(second_result), 3)

    def test_idempotent_extract_empty_existing_processes_all(self):
        """existing_output が空の場合、全アイテムが処理されること。"""
        conversations = self._make_conversations()

        result = parse_claude_json(conversations, existing_output={})
        self.assertEqual(len(result), 3)

    def test_idempotent_extract_no_existing_output_arg(self):
        """existing_output 引数なし（デフォルト）で全アイテムが処理されること（後方互換性）。"""
        conversations = self._make_conversations()

        # Original signature without existing_output should still work
        result = parse_claude_json(conversations)
        self.assertEqual(len(result), 3)


# ============================================================
# Phase 2 (045-fix-kedro-input) RED tests: parse_claude_zip
# ============================================================


def _make_claude_zip_bytes(conversations: list[dict]) -> bytes:
    """Create a minimal Claude export ZIP containing conversations.json.

    Args:
        conversations: List of Claude conversation dicts.

    Returns:
        ZIP file content as bytes.
    """
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "conversations.json",
            json.dumps(conversations, ensure_ascii=False),
        )
    return buf.getvalue()


def _make_claude_partitioned_input(zip_map: dict[str, bytes]) -> dict[str, callable]:
    """Create a Kedro PartitionedDataset-style input dict.

    Each key is a ZIP filename, value is a callable returning bytes.

    Args:
        zip_map: Dict of filename -> ZIP bytes.

    Returns:
        Dict of filename -> callable returning bytes.
    """
    return {name: (lambda b=data: b) for name, data in zip_map.items()}


def _make_claude_conversation(
    conv_uuid: str = "conv-001-uuid",
    name: str = "Python asyncio discussion",
    created_at: str = "2026-01-15T10:30:00.000000+00:00",
    messages: list[dict] | None = None,
) -> dict:
    """Build a minimal Claude conversation dict.

    Args:
        conv_uuid: Conversation UUID.
        name: Conversation name.
        created_at: ISO timestamp.
        messages: Chat messages. If None, generates a default 4-message conversation.

    Returns:
        Claude conversation dict.
    """
    if messages is None:
        messages = [
            {
                "uuid": "msg-1",
                "sender": "human",
                "text": "How does Python asyncio work?",
                "created_at": created_at,
            },
            {
                "uuid": "msg-2",
                "sender": "assistant",
                "text": "Python asyncio is a library for writing concurrent code using the async/await syntax.",
                "created_at": created_at,
            },
            {
                "uuid": "msg-3",
                "sender": "human",
                "text": "Can you explain event loops in more detail?",
                "created_at": created_at,
            },
            {
                "uuid": "msg-4",
                "sender": "assistant",
                "text": "An event loop runs async tasks and callbacks, handles I/O events, and manages subprocesses.",
                "created_at": created_at,
            },
        ]

    return {
        "uuid": conv_uuid,
        "name": name,
        "created_at": created_at,
        "updated_at": created_at,
        "chat_messages": messages,
    }


class TestParseClaudeZipBasic(unittest.TestCase):
    """parse_claude_zip: valid ZIP -> ParsedItem dict."""

    def setUp(self):
        """Create a valid Claude export ZIP with 2 conversations."""
        from obsidian_etl.pipelines.extract_claude.nodes import parse_claude_zip

        self.parse_claude_zip = parse_claude_zip

        conv1 = _make_claude_conversation(
            conv_uuid="conv-zip-001",
            name="Python asyncio discussion",
        )
        conv2 = _make_claude_conversation(
            conv_uuid="conv-zip-002",
            name="Database indexing strategies",
            messages=[
                {
                    "uuid": "msg-db-1",
                    "sender": "human",
                    "text": "How do database indexes work?",
                    "created_at": "2026-01-15T11:00:00.000000+00:00",
                },
                {
                    "uuid": "msg-db-2",
                    "sender": "assistant",
                    "text": "Database indexes are data structures that improve the speed of data retrieval.",
                    "created_at": "2026-01-15T11:00:10.000000+00:00",
                },
                {
                    "uuid": "msg-db-3",
                    "sender": "human",
                    "text": "What about B-tree indexes specifically?",
                    "created_at": "2026-01-15T11:00:20.000000+00:00",
                },
                {
                    "uuid": "msg-db-4",
                    "sender": "assistant",
                    "text": "B-tree indexes organize data in a balanced tree structure for efficient lookups.",
                    "created_at": "2026-01-15T11:00:30.000000+00:00",
                },
            ],
        )

        zip_bytes = _make_claude_zip_bytes([conv1, conv2])
        self.partitioned_input = _make_claude_partitioned_input({"claude_export.zip": zip_bytes})

    def test_parse_claude_zip_returns_dict(self):
        """parse_claude_zip が dict を返すこと。"""
        result = self.parse_claude_zip(self.partitioned_input)
        self.assertIsInstance(result, dict)

    def test_parse_claude_zip_item_count(self):
        """2 会話から 2 ParsedItem が生成されること。"""
        result = self.parse_claude_zip(self.partitioned_input)
        self.assertEqual(len(result), 2)

    def test_parse_claude_zip_parsed_item_structure(self):
        """ParsedItem が必須フィールドを含むこと。"""
        result = self.parse_claude_zip(self.partitioned_input)

        first_item = list(result.values())[0]

        # Required fields
        self.assertIn("item_id", first_item)
        self.assertEqual(first_item["source_provider"], "claude")
        self.assertIn("source_path", first_item)
        self.assertIn("conversation_name", first_item)
        self.assertIn("created_at", first_item)
        self.assertIsInstance(first_item["messages"], list)
        self.assertGreater(len(first_item["messages"]), 0)
        self.assertIsInstance(first_item["content"], str)
        self.assertGreater(len(first_item["content"]), 10)
        self.assertIn("file_id", first_item)
        self.assertEqual(len(first_item["file_id"]), 12)
        self.assertFalse(first_item["is_chunked"])
        self.assertIsNone(first_item["chunk_index"])
        self.assertIsNone(first_item["total_chunks"])
        self.assertIsNone(first_item["parent_item_id"])

    def test_parse_claude_zip_conversation_name(self):
        """conversation_name がタイトルから正しく設定されること。"""
        result = self.parse_claude_zip(self.partitioned_input)

        items = list(result.values())
        names = {item["conversation_name"] for item in items}
        self.assertIn("Python asyncio discussion", names)
        self.assertIn("Database indexing strategies", names)

    def test_parse_claude_zip_message_format(self):
        """メッセージが {role, content} 形式に正規化されること。"""
        result = self.parse_claude_zip(self.partitioned_input)

        first_item = list(result.values())[0]
        messages = first_item["messages"]

        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0]["role"], "human")
        self.assertIn("asyncio", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "assistant")

    def test_parse_claude_zip_content_format(self):
        """content がフォーマット済み会話テキストであること。"""
        result = self.parse_claude_zip(self.partitioned_input)

        first_item = list(result.values())[0]
        content = first_item["content"]

        self.assertIn("Human:", content)
        self.assertIn("Assistant:", content)

    def test_parse_claude_zip_file_id_is_valid_hex(self):
        """file_id が 12 桁の16進数文字列であること。"""
        result = self.parse_claude_zip(self.partitioned_input)

        first_item = list(result.values())[0]
        file_id = first_item["file_id"]

        self.assertEqual(len(file_id), 12)
        int(file_id, 16)  # Raises ValueError if not valid hex

    def test_parse_claude_zip_source_provider(self):
        """全アイテムの source_provider が 'claude' であること。"""
        result = self.parse_claude_zip(self.partitioned_input)

        for item in result.values():
            self.assertEqual(item["source_provider"], "claude")


class TestParseClaudeZipFixture(unittest.TestCase):
    """parse_claude_zip: claude_test.zip fixture -> 3 parsed_items."""

    def setUp(self):
        """Load the real claude_test.zip fixture."""
        from obsidian_etl.pipelines.extract_claude.nodes import parse_claude_zip

        self.parse_claude_zip = parse_claude_zip

        zip_path = FIXTURES_DIR / "claude_test.zip"
        with open(zip_path, "rb") as f:
            self.zip_bytes = f.read()

        self.partitioned_input = _make_claude_partitioned_input({"claude_test.zip": self.zip_bytes})

    def test_parse_claude_zip_output_count(self):
        """claude_test.zip から 3 件の parsed_items が生成されること。"""
        result = self.parse_claude_zip(self.partitioned_input)
        self.assertEqual(len(result), 3)

    def test_parse_claude_zip_all_have_required_fields(self):
        """全 parsed_items に必須フィールドが存在すること。"""
        result = self.parse_claude_zip(self.partitioned_input)

        required_fields = [
            "item_id",
            "source_provider",
            "content",
            "file_id",
            "messages",
            "conversation_name",
            "created_at",
        ]

        for item in result.values():
            for field in required_fields:
                self.assertIn(field, item, f"Missing field: {field}")

    def test_parse_claude_zip_all_source_provider_claude(self):
        """全アイテムの source_provider が 'claude' であること。"""
        result = self.parse_claude_zip(self.partitioned_input)

        for item in result.values():
            self.assertEqual(item["source_provider"], "claude")

    def test_parse_claude_zip_all_have_4_messages(self):
        """各会話が 4 メッセージを持つこと（テストフィクスチャの仕様）。"""
        result = self.parse_claude_zip(self.partitioned_input)

        for item in result.values():
            self.assertEqual(len(item["messages"]), 4)

    def test_parse_claude_zip_content_not_empty(self):
        """全アイテムの content が空でないこと。"""
        result = self.parse_claude_zip(self.partitioned_input)

        for item in result.values():
            self.assertGreater(len(item["content"]), 10)

    def test_parse_claude_zip_not_chunked(self):
        """全会話が 25000 文字未満のためチャンクされないこと。"""
        result = self.parse_claude_zip(self.partitioned_input)

        for item in result.values():
            self.assertFalse(item["is_chunked"])


class TestParseClaudeZipInvalid(unittest.TestCase):
    """parse_claude_zip: broken/invalid ZIP -> error handling."""

    def setUp(self):
        """Import parse_claude_zip."""
        from obsidian_etl.pipelines.extract_claude.nodes import parse_claude_zip

        self.parse_claude_zip = parse_claude_zip

    def test_parse_claude_zip_invalid_bytes(self):
        """壊れた ZIP データでエラーが適切にハンドルされること。"""
        broken_bytes = b"this is not a valid zip file"
        partitioned = _make_claude_partitioned_input({"broken.zip": broken_bytes})

        # Should not raise, but return empty or handle gracefully
        result = self.parse_claude_zip(partitioned)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_parse_claude_zip_truncated_zip(self):
        """途中で切れた ZIP データでもエラーにならないこと。"""
        # Create valid ZIP then truncate
        zip_bytes = _make_claude_zip_bytes([_make_claude_conversation()])
        truncated = zip_bytes[: len(zip_bytes) // 2]
        partitioned = _make_claude_partitioned_input({"truncated.zip": truncated})

        result = self.parse_claude_zip(partitioned)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_parse_claude_zip_empty_bytes(self):
        """空の bytes でもエラーにならないこと。"""
        partitioned = _make_claude_partitioned_input({"empty.zip": b""})

        result = self.parse_claude_zip(partitioned)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)


class TestParseClaudeZipNoConversations(unittest.TestCase):
    """parse_claude_zip: ZIP without conversations.json -> skip with warning."""

    def setUp(self):
        """Import parse_claude_zip."""
        from obsidian_etl.pipelines.extract_claude.nodes import parse_claude_zip

        self.parse_claude_zip = parse_claude_zip

    def test_parse_claude_zip_no_conversations_json(self):
        """conversations.json が含まれない ZIP ではスキップされること。"""
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("other_file.txt", "not conversations")
        zip_bytes = buf.getvalue()

        partitioned = _make_claude_partitioned_input({"no_conv.zip": zip_bytes})
        result = self.parse_claude_zip(partitioned)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_parse_claude_zip_empty_conversations_json(self):
        """空の conversations.json の場合、空 dict が返ること。"""
        zip_bytes = _make_claude_zip_bytes([])
        partitioned = _make_claude_partitioned_input({"empty_conv.zip": zip_bytes})

        result = self.parse_claude_zip(partitioned)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_parse_claude_zip_empty_partitioned_input(self):
        """空の partitioned_input が空 dict を返すこと。"""
        result = self.parse_claude_zip({})
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)


class TestParseClaudeZipExistingOutput(unittest.TestCase):
    """parse_claude_zip: existing_output parameter (backward compat)."""

    def setUp(self):
        """Import parse_claude_zip and create valid input."""
        from obsidian_etl.pipelines.extract_claude.nodes import parse_claude_zip

        self.parse_claude_zip = parse_claude_zip

        convs = [
            _make_claude_conversation(conv_uuid=f"conv-eo-{i:03d}", name=f"Test conv {i}")
            for i in range(2)
        ]
        zip_bytes = _make_claude_zip_bytes(convs)
        self.partitioned_input = _make_claude_partitioned_input({"test.zip": zip_bytes})

    def test_existing_output_param_accepted(self):
        """existing_output パラメータが受け付けられること。"""
        result = self.parse_claude_zip(self.partitioned_input, existing_output={})
        self.assertEqual(len(result), 2)

    def test_no_existing_output_default(self):
        """existing_output なしで正常動作すること（後方互換）。"""
        result = self.parse_claude_zip(self.partitioned_input)
        self.assertEqual(len(result), 2)


class TestParseClaudeZipMultipleZips(unittest.TestCase):
    """parse_claude_zip: multiple ZIP files in partitioned input."""

    def setUp(self):
        """Import parse_claude_zip."""
        from obsidian_etl.pipelines.extract_claude.nodes import parse_claude_zip

        self.parse_claude_zip = parse_claude_zip

    def test_multiple_zips_combined(self):
        """複数 ZIP ファイルの会話が全て処理されること。"""
        conv1 = _make_claude_conversation(conv_uuid="conv-multi-1", name="Conversation A")
        conv2 = _make_claude_conversation(conv_uuid="conv-multi-2", name="Conversation B")

        zip1 = _make_claude_zip_bytes([conv1])
        zip2 = _make_claude_zip_bytes([conv2])

        partitioned = _make_claude_partitioned_input(
            {
                "export1.zip": zip1,
                "export2.zip": zip2,
            }
        )

        result = self.parse_claude_zip(partitioned)
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
