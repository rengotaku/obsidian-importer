"""Tests for ChatGPT deduplication fix (Phase 3 - US1).

Verifies that ChatGPT extractor processes N conversations to N output items
(not N^2), by ensuring:
- _discover_raw_items() yields content-ready ProcessingItems from ZIP
- steps property returns only [ValidateMinMessagesStep]
- _build_chunk_messages() returns ChatGPT format {uuid, text, sender, created_at}
- Edge cases: empty ZIP, malformed conversations
"""

import io
import json
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from src.etl.core.models import ProcessingItem
from src.etl.core.status import ItemStatus
from src.etl.stages.extract.chatgpt_extractor import (
    ChatGPTExtractor,
    ValidateMinMessagesStep,
)


def _make_chatgpt_conversation(
    conversation_id: str,
    title: str = "Test Conv",
    create_time: float = 1700000000.0,
    messages: list[dict] | None = None,
) -> dict:
    """Helper: build a minimal ChatGPT conversation dict with mapping tree.

    Args:
        conversation_id: Unique ID for the conversation.
        title: Conversation title.
        create_time: Unix timestamp.
        messages: List of dicts with keys {role, text}. Defaults to 2-message exchange.

    Returns:
        ChatGPT conversation dict with mapping/current_node structure.
    """
    if messages is None:
        messages = [
            {"role": "user", "text": "Hello from user"},
            {"role": "assistant", "text": "Hello from assistant"},
        ]

    # Build a linear mapping tree: root -> msg1 -> msg2 -> ...
    mapping = {}
    node_ids = []
    for i, msg in enumerate(messages):
        node_id = f"node-{conversation_id}-{i}"
        node_ids.append(node_id)
        parent = node_ids[i - 1] if i > 0 else None
        mapping[node_id] = {
            "id": node_id,
            "parent": parent,
            "message": {
                "id": f"msg-{conversation_id}-{i}",
                "author": {"role": msg["role"]},
                "content": {"parts": [msg["text"]]},
                "create_time": create_time + i,
            },
        }

    current_node = node_ids[-1] if node_ids else ""

    return {
        "conversation_id": conversation_id,
        "title": title,
        "create_time": create_time,
        "mapping": mapping,
        "current_node": current_node,
    }


def _create_chatgpt_zip(conversations: list[dict], tmp_dir: str) -> Path:
    """Helper: create a ChatGPT export ZIP with conversations.json.

    Args:
        conversations: List of ChatGPT conversation dicts.
        tmp_dir: Temporary directory path.

    Returns:
        Path to the created ZIP file.
    """
    zip_path = Path(tmp_dir) / "chatgpt_export.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "conversations.json",
            json.dumps(conversations, ensure_ascii=False),
        )
    zip_path.write_bytes(buf.getvalue())
    return zip_path


class TestChatGPTNItemsNOutput(unittest.TestCase):
    """T018: discover -> run produces N items for N conversations (not N^2)."""

    def test_discover_run_n_items_n_output(self):
        """N conversations in ZIP -> exactly N output items after discover + run.

        Given: ZIP with 3 conversations
        When: discover_items() -> run()
        Then: output count == 3 (not 9 = 3^2)
        """
        conversations = [
            _make_chatgpt_conversation(f"conv-{i}", title=f"Conv {i}") for i in range(3)
        ]

        with TemporaryDirectory() as tmp_dir:
            zip_path = _create_chatgpt_zip(conversations, tmp_dir)
            extractor = ChatGPTExtractor()

            # discover_items yields ProcessingItems
            discovered = list(extractor.discover_items(zip_path, chunk=False))

            # Must be exactly 3 items (not 9)
            self.assertEqual(len(discovered), 3)

            # Each item should have content set (Claude format)
            for item in discovered:
                self.assertIsNotNone(item.content)
                conv_data = json.loads(item.content)
                self.assertIn("chat_messages", conv_data)

    def test_discover_run_single_conversation_no_duplication(self):
        """1 conversation -> exactly 1 output item.

        Edge case: even with 1 conversation, no duplication should occur.
        """
        conversations = [_make_chatgpt_conversation("single-conv")]

        with TemporaryDirectory() as tmp_dir:
            zip_path = _create_chatgpt_zip(conversations, tmp_dir)
            extractor = ChatGPTExtractor()

            discovered = list(extractor.discover_items(zip_path, chunk=False))
            self.assertEqual(len(discovered), 1)


class TestChatGPTNoDuplicateUUIDs(unittest.TestCase):
    """T019: pipeline_stages.jsonl has no duplicate conversation_uuid."""

    def test_no_duplicate_conversation_uuid_in_discovered_items(self):
        """All discovered items have unique conversation_uuid in metadata.

        Given: ZIP with 5 conversations
        When: discover_items()
        Then: no duplicate conversation_uuid in metadata
        """
        conversations = [
            _make_chatgpt_conversation(f"uuid-{i}", title=f"Conv {i}") for i in range(5)
        ]

        with TemporaryDirectory() as tmp_dir:
            zip_path = _create_chatgpt_zip(conversations, tmp_dir)
            extractor = ChatGPTExtractor()

            discovered = list(extractor.discover_items(zip_path, chunk=False))

            # Collect conversation_uuid from metadata
            uuids = [item.metadata.get("conversation_uuid") for item in discovered]

            # All should be unique
            self.assertEqual(len(uuids), len(set(uuids)))
            # And match count
            self.assertEqual(len(uuids), 5)


class TestChatGPTStepsValidation(unittest.TestCase):
    """T020: ChatGPTExtractor.steps returns only [ValidateMinMessagesStep]."""

    def test_steps_returns_only_validate_min_messages(self):
        """After fix, ChatGPTExtractor.steps should have exactly 1 step.

        The redundant ReadZipStep, ParseConversationsStep, ConvertFormatStep
        should be removed. Only ValidateMinMessagesStep remains.
        """
        extractor = ChatGPTExtractor()
        steps = extractor.steps

        self.assertEqual(
            len(steps), 1, f"Expected 1 step, got {len(steps)}: {[type(s).__name__ for s in steps]}"
        )
        self.assertIsInstance(
            steps[0],
            ValidateMinMessagesStep,
            f"Expected ValidateMinMessagesStep, got {type(steps[0]).__name__}",
        )

    def test_steps_do_not_include_read_zip(self):
        """ReadZipStep should not be in steps (moved to _discover_raw_items)."""
        extractor = ChatGPTExtractor()
        step_names = [type(s).__name__ for s in extractor.steps]
        self.assertNotIn("ReadZipStep", step_names)

    def test_steps_do_not_include_parse_conversations(self):
        """ParseConversationsStep should not be in steps (moved to _discover_raw_items)."""
        extractor = ChatGPTExtractor()
        step_names = [type(s).__name__ for s in extractor.steps]
        self.assertNotIn("ParseConversationsStep", step_names)

    def test_steps_do_not_include_convert_format(self):
        """ConvertFormatStep should not be in steps (moved to _discover_raw_items)."""
        extractor = ChatGPTExtractor()
        step_names = [type(s).__name__ for s in extractor.steps]
        self.assertNotIn("ConvertFormatStep", step_names)


class TestChatGPTBuildChunkMessages(unittest.TestCase):
    """T021: _build_chunk_messages() returns ChatGPT format."""

    def test_build_chunk_messages_returns_chatgpt_format(self):
        """_build_chunk_messages() should return list of dicts with {uuid, text, sender, created_at}.

        This method is the provider-specific hook for chunking.
        ChatGPTExtractor must override it to include uuid and created_at fields.
        """
        extractor = ChatGPTExtractor()

        # Create a mock chunk with messages
        mock_chunk = MagicMock()
        mock_msg1 = MagicMock()
        mock_msg1.content = "Hello"
        mock_msg1.role = "human"
        mock_msg2 = MagicMock()
        mock_msg2.content = "Hi there"
        mock_msg2.role = "assistant"
        mock_chunk.messages = [mock_msg1, mock_msg2]

        conversation_dict = {
            "uuid": "test-uuid",
            "name": "Test",
            "created_at": "2024-01-01",
            "chat_messages": [],
        }

        result = extractor._build_chunk_messages(mock_chunk, conversation_dict)

        # Must not return None (ChatGPT needs custom chunk messages)
        self.assertIsNotNone(result, "_build_chunk_messages() should not return None for ChatGPT")

        # Must be a list
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Each message must have {uuid, text, sender, created_at}
        for msg in result:
            self.assertIn("uuid", msg, f"Message missing 'uuid' key: {msg}")
            self.assertIn("text", msg, f"Message missing 'text' key: {msg}")
            self.assertIn("sender", msg, f"Message missing 'sender' key: {msg}")
            self.assertIn("created_at", msg, f"Message missing 'created_at' key: {msg}")

        # Verify values
        self.assertEqual(result[0]["text"], "Hello")
        self.assertEqual(result[0]["sender"], "human")
        self.assertEqual(result[1]["text"], "Hi there")
        self.assertEqual(result[1]["sender"], "assistant")


class TestChatGPTDiscoverRawItems(unittest.TestCase):
    """T021b: _discover_raw_items() yields content-ready ProcessingItems from ZIP."""

    def test_discover_raw_items_yields_content_set_items(self):
        """Each yielded ProcessingItem must have content set (not None).

        _discover_raw_items() should read ZIP, parse conversations.json,
        convert to Claude format, and set content on each item.
        """
        conversations = [
            _make_chatgpt_conversation("discover-1", title="First"),
            _make_chatgpt_conversation("discover-2", title="Second"),
        ]

        with TemporaryDirectory() as tmp_dir:
            zip_path = _create_chatgpt_zip(conversations, tmp_dir)
            extractor = ChatGPTExtractor()

            items = list(extractor._discover_raw_items(zip_path))

            self.assertEqual(len(items), 2)

            for item in items:
                # Content must be set (JSON string, Claude format)
                self.assertIsNotNone(item.content, "content must be set by _discover_raw_items")
                conv_data = json.loads(item.content)
                self.assertIn(
                    "chat_messages",
                    conv_data,
                    "content must be in Claude format with chat_messages",
                )
                self.assertIn("uuid", conv_data)
                self.assertIn("name", conv_data)

    def test_discover_raw_items_sets_metadata(self):
        """Each yielded ProcessingItem must have required metadata fields.

        Metadata must include: conversation_uuid, source_provider, source_type,
        conversation_name, created_at, message_count, format.
        """
        conversations = [_make_chatgpt_conversation("meta-test", title="Meta Test")]

        with TemporaryDirectory() as tmp_dir:
            zip_path = _create_chatgpt_zip(conversations, tmp_dir)
            extractor = ChatGPTExtractor()

            items = list(extractor._discover_raw_items(zip_path))

            self.assertEqual(len(items), 1)
            item = items[0]

            # Required metadata fields
            self.assertEqual(item.metadata["conversation_uuid"], "meta-test")
            self.assertEqual(item.metadata["source_provider"], "openai")
            self.assertEqual(item.metadata["source_type"], "conversation")
            self.assertEqual(item.metadata["conversation_name"], "Meta Test")
            self.assertIn("created_at", item.metadata)
            self.assertIn("message_count", item.metadata)
            self.assertEqual(item.metadata["format"], "claude")

    def test_discover_raw_items_from_directory(self):
        """_discover_raw_items accepts directory containing ZIP file."""
        conversations = [_make_chatgpt_conversation("dir-test")]

        with TemporaryDirectory() as tmp_dir:
            _create_chatgpt_zip(conversations, tmp_dir)
            extractor = ChatGPTExtractor()

            items = list(extractor._discover_raw_items(Path(tmp_dir)))

            self.assertEqual(len(items), 1)


class TestChatGPTChunkingIntegration(unittest.TestCase):
    """T021c: Chunked chat_messages contain uuid, created_at fields."""

    def test_chunked_messages_have_uuid_and_created_at(self):
        """After chunking, each chat_message in chunk must have uuid and created_at.

        Given: conversation with >25000 chars (triggers chunking)
        When: discover_items(chunk=True)
        Then: chunked items' chat_messages contain uuid, created_at keys
        """
        # Build a conversation with many long messages to trigger chunking
        long_text = "A" * 5000  # Each message 5000 chars
        messages = [
            {"role": "user", "text": long_text},
            {"role": "assistant", "text": long_text},
            {"role": "user", "text": long_text},
            {"role": "assistant", "text": long_text},
            {"role": "user", "text": long_text},
            {"role": "assistant", "text": long_text},
        ]  # Total ~30000 chars, should trigger chunking

        conversations = [_make_chatgpt_conversation("chunk-test", messages=messages)]

        with TemporaryDirectory() as tmp_dir:
            zip_path = _create_chatgpt_zip(conversations, tmp_dir)
            extractor = ChatGPTExtractor()

            # Discover with chunking enabled
            discovered = list(extractor.discover_items(zip_path, chunk=True))

            # Should produce chunks (more than 1 item from 1 conversation)
            chunked_items = [item for item in discovered if item.metadata.get("is_chunked", False)]

            # We expect at least 2 chunks for >25000 chars
            self.assertGreater(
                len(chunked_items),
                0,
                "Expected chunking to produce multiple items for large conversation",
            )

            # Each chunk's chat_messages must have uuid, created_at
            for chunk_item in chunked_items:
                conv_data = json.loads(chunk_item.content)
                chat_msgs = conv_data.get("chat_messages", [])
                self.assertGreater(len(chat_msgs), 0, "Chunk should have messages")
                for msg in chat_msgs:
                    self.assertIn("uuid", msg, f"Chunked message missing 'uuid': {msg}")
                    self.assertIn("created_at", msg, f"Chunked message missing 'created_at': {msg}")


class TestChatGPTEmptyZip(unittest.TestCase):
    """T021d: Empty conversations.json (0 conversations) ZIP completes gracefully."""

    def test_empty_conversations_json_no_exception(self):
        """ZIP with empty conversations.json [] should return 0 items, no exception.

        Given: ZIP with conversations.json = []
        When: discover_items()
        Then: returns empty list, no exception raised
        """
        with TemporaryDirectory() as tmp_dir:
            zip_path = _create_chatgpt_zip([], tmp_dir)
            extractor = ChatGPTExtractor()

            # Should not raise any exception
            discovered = list(extractor.discover_items(zip_path, chunk=False))
            self.assertEqual(len(discovered), 0)

    def test_empty_conversations_json_discover_raw_items(self):
        """_discover_raw_items with empty conversations.json yields nothing."""
        with TemporaryDirectory() as tmp_dir:
            zip_path = _create_chatgpt_zip([], tmp_dir)
            extractor = ChatGPTExtractor()

            items = list(extractor._discover_raw_items(zip_path))
            self.assertEqual(len(items), 0)


class TestChatGPTMalformedConversation(unittest.TestCase):
    """T021e: Conversations with missing mapping/current_node are skipped."""

    def test_missing_mapping_skipped_others_processed(self):
        """Conversation without mapping is skipped; valid ones are processed.

        Given: 3 conversations, 1 with empty mapping
        When: discover_items()
        Then: only 2 items produced (malformed one skipped)
        """
        valid_conv_1 = _make_chatgpt_conversation("valid-1", title="Valid 1")
        valid_conv_2 = _make_chatgpt_conversation("valid-2", title="Valid 2")
        malformed_conv = {
            "conversation_id": "malformed-1",
            "title": "Malformed",
            "create_time": 1700000000.0,
            "mapping": {},  # Empty mapping
            "current_node": "",  # Empty current_node
        }

        conversations = [valid_conv_1, malformed_conv, valid_conv_2]

        with TemporaryDirectory() as tmp_dir:
            zip_path = _create_chatgpt_zip(conversations, tmp_dir)
            extractor = ChatGPTExtractor()

            discovered = list(extractor.discover_items(zip_path, chunk=False))

            # Only 2 valid conversations should be processed
            self.assertEqual(len(discovered), 2)

            # Verify UUIDs are the valid ones
            uuids = {item.metadata["conversation_uuid"] for item in discovered}
            self.assertIn("valid-1", uuids)
            self.assertIn("valid-2", uuids)
            self.assertNotIn("malformed-1", uuids)

    def test_missing_current_node_skipped(self):
        """Conversation without current_node is skipped."""
        valid_conv = _make_chatgpt_conversation("valid-only", title="Valid")
        no_current_node = _make_chatgpt_conversation("no-node", title="No Node")
        # Remove current_node
        no_current_node["current_node"] = ""
        # Keep mapping but empty it to trigger skip
        no_current_node["mapping"] = {}

        conversations = [valid_conv, no_current_node]

        with TemporaryDirectory() as tmp_dir:
            zip_path = _create_chatgpt_zip(conversations, tmp_dir)
            extractor = ChatGPTExtractor()

            discovered = list(extractor.discover_items(zip_path, chunk=False))

            self.assertEqual(len(discovered), 1)
            self.assertEqual(discovered[0].metadata["conversation_uuid"], "valid-only")


if __name__ == "__main__":
    unittest.main()
