"""Tests for OpenAI (ChatGPT) Extract pipeline nodes.

Phase 7 RED tests: parse_chatgpt_zip node and related logic.
These tests verify:
- ZIP extraction and conversations.json parsing to ParsedItem dict
- ChatGPT mapping tree traversal to chronological messages
- Multimodal handling (image -> [Image: id], audio -> [Audio: name])
- Role conversion (user->human, assistant->assistant, system/tool excluded)
- Chunking of large conversations (25000+ chars)
- Empty conversations.json handling (warning, no output)
- Idempotent existing_output parameter (backward compat, ignored)
"""

from __future__ import annotations

import io
import json
import unittest
import zipfile
from pathlib import Path

from obsidian_etl.pipelines.extract_openai.nodes import parse_chatgpt_zip

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


def _make_zip_bytes(conversations: list[dict]) -> bytes:
    """Create a minimal ChatGPT export ZIP containing conversations.json.

    Args:
        conversations: List of ChatGPT conversation dicts.

    Returns:
        ZIP file content as bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "conversations.json",
            json.dumps(conversations, ensure_ascii=False),
        )
    return buf.getvalue()


def _make_partitioned_input(zip_map: dict[str, bytes]) -> dict[str, callable]:
    """Create a Kedro PartitionedDataset-style input dict.

    Each key is a ZIP filename, value is a callable returning bytes.

    Args:
        zip_map: Dict of filename -> ZIP bytes.

    Returns:
        Dict of filename -> callable returning bytes.
    """
    return {name: (lambda b=data: b) for name, data in zip_map.items()}


def _make_chatgpt_conversation(
    conversation_id: str = "openai-conv-001",
    title: str = "Python asyncio discussion",
    create_time: float = 1736933400.0,
    messages: list[dict] | None = None,
) -> dict:
    """Build a minimal ChatGPT conversation dict with mapping tree structure.

    Args:
        conversation_id: Unique conversation ID.
        title: Conversation title.
        create_time: Unix timestamp for creation time.
        messages: List of message dicts with keys: node_id, role, content, create_time.
                  If None, generates a default 4-message conversation.

    Returns:
        ChatGPT conversation dict with mapping tree and current_node.
    """
    if messages is None:
        messages = [
            {
                "node_id": "node-1",
                "role": "user",
                "content": "How does Python asyncio work?",
                "create_time": create_time + 0,
            },
            {
                "node_id": "node-2",
                "role": "assistant",
                "content": "Python asyncio is a library for writing concurrent code using the async/await syntax. It provides an event loop that manages coroutines.",
                "create_time": create_time + 10,
            },
            {
                "node_id": "node-3",
                "role": "user",
                "content": "Can you explain event loops in more detail?",
                "create_time": create_time + 20,
            },
            {
                "node_id": "node-4",
                "role": "assistant",
                "content": "An event loop runs async tasks and callbacks, handles I/O events, and manages subprocesses. It is the core of every asyncio application.",
                "create_time": create_time + 30,
            },
        ]

    # Build mapping tree: linear chain root -> node-1 -> node-2 -> ...
    mapping = {}
    root_id = "root-node"
    mapping[root_id] = {
        "message": None,
        "parent": None,
        "children": [messages[0]["node_id"]] if messages else [],
    }

    for i, msg in enumerate(messages):
        parent_id = root_id if i == 0 else messages[i - 1]["node_id"]
        children = [messages[i + 1]["node_id"]] if i < len(messages) - 1 else []

        mapping[msg["node_id"]] = {
            "message": {
                "id": msg["node_id"],
                "author": {"role": msg["role"]},
                "content": {
                    "parts": msg.get("parts", [msg["content"]]),
                },
                "create_time": msg.get("create_time", create_time),
            },
            "parent": parent_id,
            "children": children,
        }

    # current_node is the last message node
    current_node = messages[-1]["node_id"] if messages else root_id

    return {
        "id": conversation_id,
        "title": title,
        "create_time": create_time,
        "mapping": mapping,
        "current_node": current_node,
    }


class TestParseChatgptZipBasic(unittest.TestCase):
    """parse_chatgpt_zip: valid ZIP -> ParsedItem dict."""

    def setUp(self):
        """Create a valid ChatGPT export ZIP with 2 conversations."""
        conv1 = _make_chatgpt_conversation(
            conversation_id="openai-conv-001",
            title="Python asyncio discussion",
            create_time=1736933400.0,
        )
        conv2 = _make_chatgpt_conversation(
            conversation_id="openai-conv-002",
            title="Database indexing strategies",
            create_time=1736934000.0,
            messages=[
                {
                    "node_id": "n-1",
                    "role": "user",
                    "content": "How do database indexes work?",
                    "create_time": 1736934000.0,
                },
                {
                    "node_id": "n-2",
                    "role": "assistant",
                    "content": "Database indexes are data structures that improve the speed of data retrieval.",
                    "create_time": 1736934010.0,
                },
                {
                    "node_id": "n-3",
                    "role": "user",
                    "content": "What about B-tree indexes specifically?",
                    "create_time": 1736934020.0,
                },
                {
                    "node_id": "n-4",
                    "role": "assistant",
                    "content": "B-tree indexes organize data in a balanced tree structure for efficient lookups.",
                    "create_time": 1736934030.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv1, conv2])
        self.partitioned_input = _make_partitioned_input({"chatgpt_export.zip": zip_bytes})

        # Load expected output reference
        with open(
            FIXTURES_DIR / "expected_outputs" / "parsed_openai_item.json",
            encoding="utf-8",
        ) as f:
            self.expected_item = json.load(f)

    def test_parse_chatgpt_zip_returns_dict(self):
        """parse_chatgpt_zip が dict を返すこと。"""
        result = parse_chatgpt_zip(self.partitioned_input)
        self.assertIsInstance(result, dict)

    def test_parse_chatgpt_zip_item_count(self):
        """2 会話から 2 ParsedItem が生成されること。"""
        result = parse_chatgpt_zip(self.partitioned_input)
        self.assertEqual(len(result), 2)

    def test_parse_chatgpt_zip_parsed_item_structure(self):
        """ParsedItem が E-2 スキーマに準拠すること。"""
        result = parse_chatgpt_zip(self.partitioned_input)

        first_item = list(result.values())[0]

        # Required fields from E-2 data model
        self.assertIn("item_id", first_item)
        self.assertEqual(first_item["source_provider"], "openai")
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

    def test_parse_chatgpt_zip_conversation_name(self):
        """conversation_name がタイトルから正しく設定されること。"""
        result = parse_chatgpt_zip(self.partitioned_input)

        items = list(result.values())
        names = {item["conversation_name"] for item in items}
        self.assertIn("Python asyncio discussion", names)
        self.assertIn("Database indexing strategies", names)

    def test_parse_chatgpt_zip_message_format(self):
        """メッセージが {role, content} 形式に正規化されること。"""
        result = parse_chatgpt_zip(self.partitioned_input)

        first_item = list(result.values())[0]
        messages = first_item["messages"]

        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0]["role"], "human")
        self.assertIn("asyncio", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "assistant")

    def test_parse_chatgpt_zip_content_format(self):
        """content がフォーマット済み会話テキストであること。"""
        result = parse_chatgpt_zip(self.partitioned_input)

        first_item = list(result.values())[0]
        content = first_item["content"]

        self.assertIn("Human:", content)
        self.assertIn("Assistant:", content)

    def test_parse_chatgpt_zip_file_id_is_valid_hex(self):
        """file_id が 12 桁の16進数文字列であること。"""
        result = parse_chatgpt_zip(self.partitioned_input)

        first_item = list(result.values())[0]
        file_id = first_item["file_id"]

        self.assertEqual(len(file_id), 12)
        int(file_id, 16)  # Raises ValueError if not valid hex

    def test_parse_chatgpt_zip_golden_data_match(self):
        """期待出力（ゴールデンデータ）との部分一致を確認。"""
        result = parse_chatgpt_zip(self.partitioned_input)

        # Find the item matching the expected conversation name
        matching_items = [
            item
            for item in result.values()
            if item["conversation_name"] == self.expected_item["conversation_name"]
        ]
        self.assertEqual(len(matching_items), 1)

        item = matching_items[0]
        self.assertEqual(item["source_provider"], self.expected_item["source_provider"])
        self.assertEqual(item["is_chunked"], self.expected_item["is_chunked"])
        self.assertEqual(len(item["messages"]), len(self.expected_item["messages"]))

        # Verify each message matches
        for actual_msg, expected_msg in zip(item["messages"], self.expected_item["messages"]):
            self.assertEqual(actual_msg["role"], expected_msg["role"])
            self.assertEqual(actual_msg["content"], expected_msg["content"])


class TestChatgptTreeTraversal(unittest.TestCase):
    """parse_chatgpt_zip: mapping tree -> chronological messages."""

    def test_linear_tree_traversal(self):
        """線形ツリー構造が正しい時系列順に変換されること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="tree-linear",
            title="Linear tree test",
            messages=[
                {"node_id": "a", "role": "user", "content": "First message", "create_time": 100.0},
                {
                    "node_id": "b",
                    "role": "assistant",
                    "content": "Second message",
                    "create_time": 101.0,
                },
                {"node_id": "c", "role": "user", "content": "Third message", "create_time": 102.0},
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        messages = item["messages"]

        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["content"], "First message")
        self.assertEqual(messages[1]["content"], "Second message")
        self.assertEqual(messages[2]["content"], "Third message")

    def test_branching_tree_follows_current_node(self):
        """分岐ツリーで current_node から辿ったパスのみが使用されること。

        Tree structure:
            root -> A(user) -> B(assistant) -> C(user)   [main branch]
                                             -> D(user)   [side branch]
        current_node = C (main branch)
        """
        conv = {
            "id": "tree-branch",
            "title": "Branching tree test",
            "create_time": 100.0,
            "mapping": {
                "root": {
                    "message": None,
                    "parent": None,
                    "children": ["A"],
                },
                "A": {
                    "message": {
                        "id": "A",
                        "author": {"role": "user"},
                        "content": {"parts": ["Question one"]},
                        "create_time": 100.0,
                    },
                    "parent": "root",
                    "children": ["B"],
                },
                "B": {
                    "message": {
                        "id": "B",
                        "author": {"role": "assistant"},
                        "content": {"parts": ["Answer one"]},
                        "create_time": 101.0,
                    },
                    "parent": "A",
                    "children": ["C", "D"],
                },
                "C": {
                    "message": {
                        "id": "C",
                        "author": {"role": "user"},
                        "content": {"parts": ["Follow-up on main branch"]},
                        "create_time": 102.0,
                    },
                    "parent": "B",
                    "children": [],
                },
                "D": {
                    "message": {
                        "id": "D",
                        "author": {"role": "user"},
                        "content": {"parts": ["Side branch question"]},
                        "create_time": 103.0,
                    },
                    "parent": "B",
                    "children": [],
                },
            },
            "current_node": "C",
        }

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        messages = item["messages"]

        # Should contain A, B, C (not D)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["content"], "Question one")
        self.assertEqual(messages[1]["content"], "Answer one")
        self.assertEqual(messages[2]["content"], "Follow-up on main branch")

    def test_system_node_in_tree_excluded(self):
        """ツリー内の system ノードが除外されること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="tree-system",
            title="System node test",
            messages=[
                {
                    "node_id": "sys",
                    "role": "system",
                    "content": "You are a helpful assistant.",
                    "create_time": 100.0,
                },
                {
                    "node_id": "u1",
                    "role": "user",
                    "content": "Hello, can you help me?",
                    "create_time": 101.0,
                },
                {
                    "node_id": "a1",
                    "role": "assistant",
                    "content": "Of course! What do you need?",
                    "create_time": 102.0,
                },
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "I need help with Python asyncio.",
                    "create_time": 103.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        messages = item["messages"]

        # system message should be excluded
        roles = [msg["role"] for msg in messages]
        self.assertNotIn("system", roles)
        self.assertEqual(len(messages), 3)


class TestChatgptMultimodal(unittest.TestCase):
    """parse_chatgpt_zip: multimodal content handling."""

    def test_image_placeholder(self):
        """画像パーツが [Image: asset_pointer] プレースホルダーに変換されること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="multimodal-img",
            title="Image test",
            messages=[
                {
                    "node_id": "u1",
                    "role": "user",
                    "content": "Look at this image",
                    "parts": [
                        "Look at this image",
                        {"content_type": "image_asset_pointer", "asset_pointer": "file-abc123"},
                    ],
                    "create_time": 100.0,
                },
                {
                    "node_id": "a1",
                    "role": "assistant",
                    "content": "I can see the image you shared.",
                    "create_time": 101.0,
                },
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "What do you think about it?",
                    "create_time": 102.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]

        # First message should contain image placeholder
        first_msg_content = item["messages"][0]["content"]
        self.assertIn("[Image: file-abc123]", first_msg_content)

    def test_audio_placeholder(self):
        """音声パーツが [Audio: filename] プレースホルダーに変換されること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="multimodal-audio",
            title="Audio test",
            messages=[
                {
                    "node_id": "u1",
                    "role": "user",
                    "content": "Listen to this",
                    "parts": [
                        "Listen to this",
                        {"content_type": "audio_asset_pointer", "filename": "recording.ogg"},
                    ],
                    "create_time": 100.0,
                },
                {
                    "node_id": "a1",
                    "role": "assistant",
                    "content": "I heard the audio recording.",
                    "create_time": 101.0,
                },
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "Can you transcribe it?",
                    "create_time": 102.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]

        first_msg_content = item["messages"][0]["content"]
        self.assertIn("[Audio: recording.ogg]", first_msg_content)

    def test_mixed_multimodal_parts(self):
        """テキスト+画像+音声の混在パーツが正しく処理されること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="multimodal-mixed",
            title="Mixed multimodal test",
            messages=[
                {
                    "node_id": "u1",
                    "role": "user",
                    "content": "Check these",
                    "parts": [
                        "Here is my question:",
                        {"content_type": "image_asset_pointer", "asset_pointer": "file-img-001"},
                        "And also this audio:",
                        {"content_type": "audio_asset_pointer", "filename": "voice.mp3"},
                    ],
                    "create_time": 100.0,
                },
                {
                    "node_id": "a1",
                    "role": "assistant",
                    "content": "I see both the image and heard the audio.",
                    "create_time": 101.0,
                },
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "Great, thanks!",
                    "create_time": 102.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]

        first_msg_content = item["messages"][0]["content"]
        self.assertIn("[Image: file-img-001]", first_msg_content)
        self.assertIn("[Audio: voice.mp3]", first_msg_content)
        self.assertIn("Here is my question:", first_msg_content)


class TestChatgptRoleConversion(unittest.TestCase):
    """parse_chatgpt_zip: role conversion (user->human, system/tool excluded)."""

    def test_user_becomes_human(self):
        """user ロールが human に変換されること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="role-user",
            title="Role conversion test",
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        item = list(result.values())[0]
        user_messages = [msg for msg in item["messages"] if msg["role"] == "human"]
        self.assertGreater(len(user_messages), 0)
        # No "user" role should remain
        roles = {msg["role"] for msg in item["messages"]}
        self.assertNotIn("user", roles)

    def test_assistant_remains_assistant(self):
        """assistant ロールがそのまま維持されること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="role-assistant",
            title="Assistant role test",
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        item = list(result.values())[0]
        assistant_messages = [msg for msg in item["messages"] if msg["role"] == "assistant"]
        self.assertGreater(len(assistant_messages), 0)

    def test_system_excluded(self):
        """system ロールのメッセージが除外されること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="role-system",
            title="System exclusion test",
            messages=[
                {
                    "node_id": "sys",
                    "role": "system",
                    "content": "System prompt text",
                    "create_time": 100.0,
                },
                {
                    "node_id": "u1",
                    "role": "user",
                    "content": "Hello, I need help with Python.",
                    "create_time": 101.0,
                },
                {
                    "node_id": "a1",
                    "role": "assistant",
                    "content": "Sure! What do you need?",
                    "create_time": 102.0,
                },
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "Explain decorators in Python.",
                    "create_time": 103.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        roles = {msg["role"] for msg in item["messages"]}
        self.assertNotIn("system", roles)

    def test_tool_excluded(self):
        """tool ロールのメッセージが除外されること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="role-tool",
            title="Tool exclusion test",
            messages=[
                {
                    "node_id": "u1",
                    "role": "user",
                    "content": "Search for Python asyncio docs",
                    "create_time": 100.0,
                },
                {
                    "node_id": "t1",
                    "role": "tool",
                    "content": "search_results: [...]",
                    "create_time": 101.0,
                },
                {
                    "node_id": "a1",
                    "role": "assistant",
                    "content": "Here are the asyncio documentation results.",
                    "create_time": 102.0,
                },
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "Thanks, that is helpful!",
                    "create_time": 103.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        roles = {msg["role"] for msg in item["messages"]}
        self.assertNotIn("tool", roles)
        # Should have 3 messages (user, assistant, user) - tool excluded
        self.assertEqual(len(item["messages"]), 3)

    def test_only_valid_roles_in_output(self):
        """出力に含まれるロールが human と assistant のみであること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="role-valid-only",
            title="Valid roles only test",
            messages=[
                {
                    "node_id": "sys",
                    "role": "system",
                    "content": "System init",
                    "create_time": 100.0,
                },
                {
                    "node_id": "u1",
                    "role": "user",
                    "content": "What is a closure in Python?",
                    "create_time": 101.0,
                },
                {
                    "node_id": "t1",
                    "role": "tool",
                    "content": "code_search: closure",
                    "create_time": 102.0,
                },
                {
                    "node_id": "a1",
                    "role": "assistant",
                    "content": "A closure is a function that captures variables from its scope.",
                    "create_time": 103.0,
                },
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "Can you give an example?",
                    "create_time": 104.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        item = list(result.values())[0]
        all_roles = {msg["role"] for msg in item["messages"]}
        self.assertEqual(all_roles, {"human", "assistant"})


class TestChatgptChunking(unittest.TestCase):
    """parse_chatgpt_zip: 25000+ chars -> multiple chunks."""

    def test_large_conversation_chunked(self):
        """25000 文字以上の会話が複数チャンクに分割されること。"""
        long_text = "A" * 13000  # Each message ~13000 chars -> total ~26000

        conv = _make_chatgpt_conversation(
            conversation_id="chunk-test",
            title="Chunking test conversation",
            messages=[
                {"node_id": "u1", "role": "user", "content": long_text, "create_time": 100.0},
                {"node_id": "a1", "role": "assistant", "content": long_text, "create_time": 101.0},
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "Final question about the topic",
                    "create_time": 102.0,
                },
                {
                    "node_id": "a2",
                    "role": "assistant",
                    "content": "Here is my final answer to your question",
                    "create_time": 103.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        # Should produce multiple chunks
        self.assertGreater(len(result), 1)

    def test_chunk_metadata_fields(self):
        """チャンクに正しいメタデータが設定されること。"""
        long_text = "B" * 13000

        conv = _make_chatgpt_conversation(
            conversation_id="chunk-meta",
            title="Chunk metadata test",
            messages=[
                {"node_id": "u1", "role": "user", "content": long_text, "create_time": 100.0},
                {"node_id": "a1", "role": "assistant", "content": long_text, "create_time": 101.0},
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "Short follow-up question",
                    "create_time": 102.0,
                },
                {
                    "node_id": "a2",
                    "role": "assistant",
                    "content": "Short answer for testing",
                    "create_time": 103.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        items = list(result.values())
        for item in items:
            self.assertTrue(item["is_chunked"])
            self.assertIsNotNone(item["chunk_index"])
            self.assertIsNotNone(item["total_chunks"])
            self.assertIsNotNone(item["parent_item_id"])
            self.assertEqual(item["total_chunks"], len(items))

    def test_chunk_indices_sequential(self):
        """チャンクインデックスが 0 始まりで連番であること。"""
        long_text = "C" * 13000

        conv = _make_chatgpt_conversation(
            conversation_id="chunk-idx",
            title="Chunk index test",
            messages=[
                {"node_id": "u1", "role": "user", "content": long_text, "create_time": 100.0},
                {"node_id": "a1", "role": "assistant", "content": long_text, "create_time": 101.0},
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "Follow-up on chunk test",
                    "create_time": 102.0,
                },
                {
                    "node_id": "a2",
                    "role": "assistant",
                    "content": "Additional info on topic",
                    "create_time": 103.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        items = list(result.values())
        chunk_indices = sorted(item["chunk_index"] for item in items)
        self.assertEqual(chunk_indices, list(range(len(items))))

    def test_chunks_share_parent_item_id(self):
        """全チャンクが同一の parent_item_id を共有すること。"""
        long_text = "D" * 13000

        conv = _make_chatgpt_conversation(
            conversation_id="chunk-parent",
            title="Chunk parent test",
            messages=[
                {"node_id": "u1", "role": "user", "content": long_text, "create_time": 100.0},
                {"node_id": "a1", "role": "assistant", "content": long_text, "create_time": 101.0},
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "Final question here",
                    "create_time": 102.0,
                },
                {
                    "node_id": "a2",
                    "role": "assistant",
                    "content": "Final answer for you",
                    "create_time": 103.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        items = list(result.values())
        parent_ids = {item["parent_item_id"] for item in items}
        self.assertEqual(len(parent_ids), 1)

    def test_chunks_have_openai_provider(self):
        """チャンクの source_provider が openai であること。"""
        long_text = "E" * 13000

        conv = _make_chatgpt_conversation(
            conversation_id="chunk-provider",
            title="Chunk provider test",
            messages=[
                {"node_id": "u1", "role": "user", "content": long_text, "create_time": 100.0},
                {"node_id": "a1", "role": "assistant", "content": long_text, "create_time": 101.0},
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "Short follow-up text",
                    "create_time": 102.0,
                },
                {
                    "node_id": "a2",
                    "role": "assistant",
                    "content": "Response to follow-up",
                    "create_time": 103.0,
                },
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        for item in result.values():
            self.assertEqual(item["source_provider"], "openai")

    def test_short_conversation_not_chunked(self):
        """25000 文字未満の会話がチャンクされないこと。"""
        conv = _make_chatgpt_conversation(
            conversation_id="no-chunk",
            title="Short conversation",
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        self.assertFalse(item["is_chunked"])


class TestChatgptEmptyConversations(unittest.TestCase):
    """parse_chatgpt_zip: edge cases for empty/invalid input."""

    def test_empty_conversations_json(self):
        """空の conversations.json が空 dict を返すこと。"""
        zip_bytes = _make_zip_bytes([])
        partitioned = _make_partitioned_input({"empty.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_no_zip_files_in_input(self):
        """空の partitioned_input が空 dict を返すこと。"""
        result = parse_chatgpt_zip({})
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_short_conversation_skipped(self):
        """3 件未満のメッセージの会話がスキップされること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="short-conv",
            title="Too short",
            messages=[
                {"node_id": "u1", "role": "user", "content": "Hi", "create_time": 100.0},
                {"node_id": "a1", "role": "assistant", "content": "Hello!", "create_time": 101.0},
            ],
        )

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        # Less than 3 messages -> should be skipped
        self.assertEqual(len(result), 0)

    def test_missing_title_fallback(self):
        """タイトルが None の場合、最初のユーザーメッセージにフォールバックすること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="no-title",
            title=None,
        )
        # Override title to None in the dict
        conv["title"] = None

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        self.assertIsNotNone(item["conversation_name"])
        # Should contain part of the first user message
        self.assertIn("asyncio", item["conversation_name"])

    def test_missing_timestamp_fallback(self):
        """create_time が None の場合、created_at にフォールバック値が設定されること。"""
        conv = _make_chatgpt_conversation(
            conversation_id="no-timestamp",
            title="No timestamp test",
            create_time=None,
            messages=[
                {
                    "node_id": "u1",
                    "role": "user",
                    "content": "Question about Python generators",
                    "create_time": None,
                },
                {
                    "node_id": "a1",
                    "role": "assistant",
                    "content": "Generators use yield to produce values lazily.",
                    "create_time": None,
                },
                {
                    "node_id": "u2",
                    "role": "user",
                    "content": "How do they compare to iterators?",
                    "create_time": None,
                },
            ],
        )
        conv["create_time"] = None

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 1)
        item = list(result.values())[0]
        # Should have a non-None created_at (fallback to current datetime)
        self.assertIsNotNone(item["created_at"])

    def test_conversation_without_mapping(self):
        """mapping がない会話がスキップされること。"""
        conv = {
            "id": "no-mapping",
            "title": "No mapping",
            "create_time": 100.0,
            # No mapping field
        }

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 0)

    def test_conversation_without_id(self):
        """id がない会話がスキップされること。"""
        conv = {
            # No id field
            "title": "No id conversation",
            "create_time": 100.0,
            "mapping": {"root": {"message": None, "parent": None, "children": []}},
            "current_node": "root",
        }

        zip_bytes = _make_zip_bytes([conv])
        partitioned = _make_partitioned_input({"test.zip": zip_bytes})
        result = parse_chatgpt_zip(partitioned)

        self.assertEqual(len(result), 0)


class TestIdempotentExtractOpenai(unittest.TestCase):
    """parse_chatgpt_zip: existing_output parameter (backward compat, ignored)."""

    def _make_valid_input(self) -> dict[str, callable]:
        """Create valid partitioned input with 2 conversations."""
        convs = [
            _make_chatgpt_conversation(
                conversation_id=f"idem-{i:03d}",
                title=f"Idempotent test {i}",
                create_time=1736933400.0 + i * 100,
            )
            for i in range(2)
        ]
        zip_bytes = _make_zip_bytes(convs)
        return _make_partitioned_input({"test.zip": zip_bytes})

    def test_existing_output_ignored(self):
        """existing_output が渡されても parse は全アイテムを処理すること。"""
        partitioned = self._make_valid_input()

        # First run
        first_result = parse_chatgpt_zip(partitioned)
        self.assertEqual(len(first_result), 2)

        # Simulate existing output
        existing_output = {key: (lambda v=val: v) for key, val in first_result.items()}

        # Second run: existing_output should be ignored
        second_result = parse_chatgpt_zip(partitioned, existing_output=existing_output)
        self.assertEqual(len(second_result), 2)

    def test_no_existing_output_arg(self):
        """existing_output 引数なし（デフォルト）で正常に動作すること（後方互換性）。"""
        partitioned = self._make_valid_input()
        result = parse_chatgpt_zip(partitioned)
        self.assertEqual(len(result), 2)

    def test_empty_existing_output(self):
        """existing_output が空 dict の場合、全アイテムが処理されること。"""
        partitioned = self._make_valid_input()
        result = parse_chatgpt_zip(partitioned, existing_output={})
        self.assertEqual(len(result), 2)


# ============================================================
# Phase 2 (045-fix-kedro-input) RED tests: BinaryDataset compatibility
# ============================================================


class TestParseChatgptZipFixture(unittest.TestCase):
    """parse_chatgpt_zip: openai_test.zip fixture -> BinaryDataset compatibility."""

    def setUp(self):
        """Load the real openai_test.zip fixture via raw bytes (BinaryDataset path)."""
        zip_path = FIXTURES_DIR / "openai_test.zip"
        with open(zip_path, "rb") as f:
            self.zip_bytes = f.read()

        self.partitioned_input = _make_partitioned_input({"openai_test.zip": self.zip_bytes})

    def test_fixture_zip_produces_items(self):
        """openai_test.zip から parsed_items が生成されること。"""
        result = parse_chatgpt_zip(self.partitioned_input)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_fixture_zip_output_count(self):
        """openai_test.zip から 2 件の parsed_items が生成されること（3会話中1件はメッセージ数不足でスキップ）。"""
        result = parse_chatgpt_zip(self.partitioned_input)
        self.assertEqual(len(result), 2)

    def test_fixture_zip_all_have_required_fields(self):
        """全 parsed_items に必須フィールドが存在すること。"""
        result = parse_chatgpt_zip(self.partitioned_input)

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

    def test_fixture_zip_all_source_provider_openai(self):
        """全アイテムの source_provider が 'openai' であること。"""
        result = parse_chatgpt_zip(self.partitioned_input)

        for item in result.values():
            self.assertEqual(item["source_provider"], "openai")

    def test_fixture_zip_content_not_empty(self):
        """全アイテムの content が空でないこと。"""
        result = parse_chatgpt_zip(self.partitioned_input)

        for item in result.values():
            self.assertGreater(len(item["content"]), 10)

    def test_fixture_zip_messages_not_empty(self):
        """全アイテムに少なくとも 3 メッセージがあること。"""
        result = parse_chatgpt_zip(self.partitioned_input)

        for item in result.values():
            self.assertGreaterEqual(len(item["messages"]), 3)

    def test_fixture_zip_binary_dataset_load_path(self):
        """BinaryDataset 経由で ZIP bytes を読み込み、パースできること。"""
        import shutil
        import tempfile

        from obsidian_etl.datasets import BinaryDataset

        # Simulate BinaryDataset load: write ZIP then read back
        tmpdir = tempfile.mkdtemp()
        try:
            zip_path = Path(tmpdir) / "openai_test.zip"
            zip_path.write_bytes(self.zip_bytes)

            ds = BinaryDataset(filepath=str(zip_path))
            loaded_bytes = ds._load()

            partitioned = _make_partitioned_input({"openai_test.zip": loaded_bytes})
            result = parse_chatgpt_zip(partitioned)

            self.assertIsInstance(result, dict)
            self.assertGreater(len(result), 0)
        finally:
            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    unittest.main()
