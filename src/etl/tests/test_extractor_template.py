"""Tests for BaseExtractor Template Method pattern (Phase 2).

Tests verify:
- _build_chunk_messages() hook exists and returns None by default
- _chunk_if_needed() integrates with _build_chunk_messages() hook
- stage_type returns EXTRACT from BaseExtractor (no override needed)
"""

import json
import unittest
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.etl.core.extractor import BaseExtractor
from src.etl.core.models import ProcessingItem
from src.etl.core.status import ItemStatus
from src.etl.core.types import StageType


class ConcreteExtractor(BaseExtractor):
    """Minimal concrete implementation for testing BaseExtractor."""

    def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        yield ProcessingItem(
            item_id="test-item-1",
            source_path=input_path,
            current_step="discover",
            status=ItemStatus.PENDING,
            content=json.dumps(
                {
                    "chat_messages": [
                        {"text": "Hello", "sender": "human"},
                        {"text": "Hi there", "sender": "assistant"},
                    ],
                    "title": "Test Conversation",
                },
                ensure_ascii=False,
            ),
            metadata={"source_provider": "test"},
        )

    def _build_conversation_for_chunking(self, item):
        return None

    @property
    def steps(self):
        return []


class ConcreteExtractorWithChunkMessages(BaseExtractor):
    """Concrete extractor that overrides _build_chunk_messages()."""

    def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        yield ProcessingItem(
            item_id="test-item-1",
            source_path=input_path,
            current_step="discover",
            status=ItemStatus.PENDING,
            content=json.dumps(
                {
                    "chat_messages": [
                        {"text": "Hello", "sender": "human"},
                        {"text": "Hi there", "sender": "assistant"},
                    ],
                    "title": "Test Conversation",
                },
                ensure_ascii=False,
            ),
            metadata={"source_provider": "test"},
        )

    def _build_conversation_for_chunking(self, item):
        """Return a conversation object that triggers chunking."""
        from src.etl.stages.extract.claude_extractor import (
            SimpleConversation,
            SimpleMessage,
        )

        content = json.loads(item.content)
        messages = [
            SimpleMessage(content=m["text"], _role=m["sender"])
            for m in content.get("chat_messages", [])
        ]
        return SimpleConversation(
            title=content.get("title", ""),
            created_at="2026-01-30",
            _messages=messages,
            _id="test-conv-1",
            _provider="test",
        )

    def _build_chunk_messages(self, chunk, conversation_dict: dict) -> list[dict] | None:
        """Override hook: build custom messages for chunk."""
        return [
            {"text": msg.content, "sender": msg.role, "custom_field": "test"}
            for msg in chunk.messages
        ]

    @property
    def steps(self):
        return []


class TestBuildChunkMessagesHook(unittest.TestCase):
    """T006: Test _build_chunk_messages() hook in BaseExtractor."""

    def test_base_extractor_has_build_chunk_messages_method(self):
        """BaseExtractor has _build_chunk_messages() method."""
        extractor = ConcreteExtractor()
        self.assertTrue(
            hasattr(extractor, "_build_chunk_messages"),
            "BaseExtractor should have _build_chunk_messages method",
        )
        self.assertTrue(callable(extractor._build_chunk_messages))

    def test_build_chunk_messages_returns_none_by_default(self):
        """_build_chunk_messages() returns None by default (no-op hook)."""
        extractor = ConcreteExtractor()
        result = extractor._build_chunk_messages(
            chunk=MagicMock(),
            conversation_dict={"title": "test"},
        )
        self.assertIsNone(
            result,
            "_build_chunk_messages() should return None by default",
        )

    def test_child_class_can_override_build_chunk_messages(self):
        """Child class can override _build_chunk_messages() with custom logic."""
        extractor = ConcreteExtractorWithChunkMessages()
        mock_chunk = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = "Hello"
        mock_msg.role = "human"
        mock_chunk.messages = [mock_msg]

        result = extractor._build_chunk_messages(
            chunk=mock_chunk,
            conversation_dict={"title": "test"},
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "Hello")
        self.assertEqual(result[0]["sender"], "human")
        self.assertEqual(result[0]["custom_field"], "test")


class TestChunkIfNeededWithHook(unittest.TestCase):
    """T007: Test _chunk_if_needed() uses _build_chunk_messages() hook."""

    def _make_large_item(self, char_count: int = 30000) -> ProcessingItem:
        """Create a ProcessingItem with content exceeding chunk threshold."""
        long_text = "x" * char_count
        content = {
            "chat_messages": [
                {"text": long_text, "sender": "human"},
                {"text": "Short reply", "sender": "assistant"},
            ],
            "title": "Large Conversation",
        }
        return ProcessingItem(
            item_id="large-item",
            source_path=Path("/tmp/test"),
            current_step="discover",
            status=ItemStatus.PENDING,
            content=json.dumps(content, ensure_ascii=False),
            metadata={"source_provider": "test"},
        )

    def test_chunk_if_needed_calls_build_chunk_messages(self):
        """_chunk_if_needed() calls _build_chunk_messages() for each chunk."""
        extractor = ConcreteExtractorWithChunkMessages(chunk_size=100)
        item = self._make_large_item(char_count=500)

        # When chunking occurs, _build_chunk_messages should be called
        # and the returned messages should be set in chunk_conv["chat_messages"]
        result = extractor._chunk_if_needed(item)

        # Should produce chunked items
        self.assertGreater(
            len(result),
            0,
            "Chunking a large conversation should produce items",
        )

        # Each chunked item should have chat_messages built by the hook
        for chunk_item in result:
            if chunk_item.metadata.get("is_chunked"):
                content = json.loads(chunk_item.content)
                # The hook adds "custom_field" to each message
                for msg in content.get("chat_messages", []):
                    self.assertIn(
                        "custom_field",
                        msg,
                        "chat_messages should be built by _build_chunk_messages() hook",
                    )

    def test_chunk_if_needed_preserves_content_when_hook_returns_none(self):
        """_chunk_if_needed() preserves original content when hook returns None."""
        extractor = ConcreteExtractor(chunk_size=100)
        item = self._make_large_item(char_count=500)

        # ConcreteExtractor._build_conversation_for_chunking returns None
        # so no chunking happens - item returned as-is
        result = extractor._chunk_if_needed(item)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].content, item.content)


class TestStageTypeInheritance(unittest.TestCase):
    """T008: Test stage_type returns EXTRACT from BaseExtractor."""

    def test_base_extractor_stage_type_is_extract(self):
        """BaseExtractor.stage_type returns StageType.EXTRACT."""
        extractor = ConcreteExtractor()
        self.assertEqual(
            extractor.stage_type,
            StageType.EXTRACT,
            "BaseExtractor.stage_type should return StageType.EXTRACT",
        )

    def test_child_extractor_inherits_stage_type(self):
        """Child extractor inherits stage_type without override."""
        extractor = ConcreteExtractorWithChunkMessages()
        self.assertEqual(
            extractor.stage_type,
            StageType.EXTRACT,
            "Child extractor should inherit StageType.EXTRACT from BaseExtractor",
        )

    def test_stage_type_not_overridden_in_child(self):
        """Verify stage_type is defined on BaseExtractor, not re-defined on child."""
        # The stage_type property should come from BaseExtractor
        self.assertIn(
            "stage_type",
            vars(BaseExtractor),
            "stage_type should be defined on BaseExtractor class",
        )


###############################################################################
# Phase 4: ClaudeExtractor Template Unification Tests (US2)
###############################################################################


class TestClaudeBuildChunkMessages(unittest.TestCase):
    """T035: ClaudeExtractor._build_chunk_messages() returns {text, sender} format."""

    def setUp(self):
        """Set up ClaudeExtractor instance and test data."""
        from src.etl.stages.extract.claude_extractor import (
            ClaudeExtractor,
            SimpleConversation,
            SimpleMessage,
        )

        self.ClaudeExtractor = ClaudeExtractor
        self.SimpleConversation = SimpleConversation
        self.SimpleMessage = SimpleMessage

    def test_build_chunk_messages_returns_list_of_dicts(self):
        """_build_chunk_messages() returns a list of dicts."""
        extractor = self.ClaudeExtractor()
        chunk = MagicMock()
        chunk.messages = [
            self.SimpleMessage(content="Hello", _role="human"),
            self.SimpleMessage(content="Hi there", _role="assistant"),
        ]
        conv_dict = {"name": "Test", "created_at": "2026-01-30"}

        result = extractor._build_chunk_messages(chunk, conv_dict)

        self.assertIsNotNone(result, "_build_chunk_messages() should not return None")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_build_chunk_messages_has_text_field(self):
        """Each message dict has 'text' field with message content."""
        extractor = self.ClaudeExtractor()
        chunk = MagicMock()
        chunk.messages = [
            self.SimpleMessage(content="Test message", _role="human"),
        ]
        conv_dict = {"name": "Test"}

        result = extractor._build_chunk_messages(chunk, conv_dict)

        self.assertIsNotNone(result)
        self.assertEqual(result[0]["text"], "Test message")

    def test_build_chunk_messages_has_sender_field(self):
        """Each message dict has 'sender' field with role."""
        extractor = self.ClaudeExtractor()
        chunk = MagicMock()
        chunk.messages = [
            self.SimpleMessage(content="Hello", _role="assistant"),
        ]
        conv_dict = {"name": "Test"}

        result = extractor._build_chunk_messages(chunk, conv_dict)

        self.assertIsNotNone(result)
        self.assertEqual(result[0]["sender"], "assistant")

    def test_build_chunk_messages_no_uuid_field(self):
        """Claude format does NOT include 'uuid' field (ChatGPT-specific)."""
        extractor = self.ClaudeExtractor()
        chunk = MagicMock()
        chunk.messages = [
            self.SimpleMessage(content="Hello", _role="human"),
        ]
        conv_dict = {"name": "Test"}

        result = extractor._build_chunk_messages(chunk, conv_dict)

        self.assertIsNotNone(result)
        self.assertNotIn(
            "uuid",
            result[0],
            "Claude format should NOT include 'uuid' (ChatGPT-specific)",
        )

    def test_build_chunk_messages_no_created_at_field(self):
        """Claude format does NOT include 'created_at' field (ChatGPT-specific)."""
        extractor = self.ClaudeExtractor()
        chunk = MagicMock()
        chunk.messages = [
            self.SimpleMessage(content="Hello", _role="human"),
        ]
        conv_dict = {"name": "Test", "created_at": "2026-01-30"}

        result = extractor._build_chunk_messages(chunk, conv_dict)

        self.assertIsNotNone(result)
        self.assertNotIn(
            "created_at",
            result[0],
            "Claude format should NOT include 'created_at' (ChatGPT-specific)",
        )

    def test_build_chunk_messages_only_text_and_sender_keys(self):
        """Claude format messages contain exactly {text, sender} keys only."""
        extractor = self.ClaudeExtractor()
        chunk = MagicMock()
        chunk.messages = [
            self.SimpleMessage(content="Hello", _role="human"),
            self.SimpleMessage(content="Hi", _role="assistant"),
        ]
        conv_dict = {"name": "Test"}

        result = extractor._build_chunk_messages(chunk, conv_dict)

        self.assertIsNotNone(result)
        for msg in result:
            self.assertEqual(
                set(msg.keys()),
                {"text", "sender"},
                f"Claude message should have exactly {{text, sender}} keys, got {set(msg.keys())}",
            )


class TestClaudeNoChunkIfNeededOverride(unittest.TestCase):
    """T036: ClaudeExtractor does NOT override _chunk_if_needed()."""

    def test_chunk_if_needed_not_defined_on_claude_extractor(self):
        """_chunk_if_needed() should NOT be defined directly on ClaudeExtractor class."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        self.assertNotIn(
            "_chunk_if_needed",
            vars(ClaudeExtractor),
            "ClaudeExtractor should NOT override _chunk_if_needed() - "
            "should use BaseExtractor template method",
        )

    def test_chunk_if_needed_is_inherited_from_base(self):
        """ClaudeExtractor._chunk_if_needed should be BaseExtractor._chunk_if_needed."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        self.assertIs(
            ClaudeExtractor._chunk_if_needed,
            BaseExtractor._chunk_if_needed,
            "ClaudeExtractor._chunk_if_needed should be inherited from BaseExtractor",
        )


class TestClaudeNoStageTypeOverride(unittest.TestCase):
    """T037: ClaudeExtractor does NOT override stage_type property."""

    def test_stage_type_not_defined_on_claude_extractor(self):
        """stage_type should NOT be defined directly on ClaudeExtractor class."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        self.assertNotIn(
            "stage_type",
            vars(ClaudeExtractor),
            "ClaudeExtractor should NOT override stage_type - should inherit from BaseExtractor",
        )

    def test_stage_type_returns_extract_via_inheritance(self):
        """ClaudeExtractor.stage_type returns EXTRACT via BaseExtractor inheritance."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        extractor = ClaudeExtractor()
        self.assertEqual(
            extractor.stage_type,
            StageType.EXTRACT,
            "ClaudeExtractor should return StageType.EXTRACT via inheritance",
        )


###############################################################################
# Phase 5: GitHubExtractor Template Unification Tests (US3)
###############################################################################


class TestGitHubNoDiscoverItemsOverride(unittest.TestCase):
    """T049: GitHubExtractor does NOT override discover_items().

    GitHubExtractor currently overrides discover_items() which bypasses
    the BaseExtractor template method pattern (_discover_raw_items() ->
    _chunk_if_needed()). This override should be removed so that the
    template method is used consistently across all extractors.
    """

    def test_discover_items_not_defined_on_github_extractor(self):
        """discover_items() should NOT be defined directly on GitHubExtractor class."""
        from src.etl.stages.extract.github_extractor import GitHubExtractor

        self.assertNotIn(
            "discover_items",
            vars(GitHubExtractor),
            "GitHubExtractor should NOT override discover_items() - "
            "should use BaseExtractor template method",
        )

    def test_discover_items_is_inherited_from_base(self):
        """GitHubExtractor.discover_items should be BaseExtractor.discover_items."""
        from src.etl.stages.extract.github_extractor import GitHubExtractor

        self.assertIs(
            GitHubExtractor.discover_items,
            BaseExtractor.discover_items,
            "GitHubExtractor.discover_items should be inherited from BaseExtractor",
        )


class TestGitHubNoStageTypeOverride(unittest.TestCase):
    """T050: GitHubExtractor does NOT override stage_type property.

    GitHubExtractor currently overrides stage_type to return StageType.EXTRACT,
    which is the same value that BaseExtractor already returns. This redundant
    override should be removed.
    """

    def test_stage_type_not_defined_on_github_extractor(self):
        """stage_type should NOT be defined directly on GitHubExtractor class."""
        from src.etl.stages.extract.github_extractor import GitHubExtractor

        self.assertNotIn(
            "stage_type",
            vars(GitHubExtractor),
            "GitHubExtractor should NOT override stage_type - should inherit from BaseExtractor",
        )

    def test_stage_type_returns_extract_via_inheritance(self):
        """GitHubExtractor.stage_type returns EXTRACT via BaseExtractor inheritance."""
        from src.etl.stages.extract.github_extractor import GitHubExtractor

        extractor = GitHubExtractor()
        self.assertEqual(
            extractor.stage_type,
            StageType.EXTRACT,
            "GitHubExtractor should return StageType.EXTRACT via inheritance",
        )


class TestGitHubDiscoverRawItemsReturnsIterator(unittest.TestCase):
    """T051: GitHubExtractor._discover_raw_items() returns Iterator.

    The _discover_raw_items() method should return an Iterator (generator),
    not a list. This is consistent with the BaseExtractor template pattern
    where discover_items() consumes the Iterator from _discover_raw_items().

    Note: We also verify that the public discover_items() API returns an
    Iterator (not a list), which fails when discover_items() is overridden
    to return a list.
    """

    def test_discover_raw_items_is_generator_function(self):
        """_discover_raw_items() should be a generator function (uses yield)."""
        import inspect

        from src.etl.stages.extract.github_extractor import GitHubExtractor

        method = GitHubExtractor._discover_raw_items
        # Unwrap if it's a bound method descriptor
        func = getattr(method, "__func__", method)
        self.assertTrue(
            inspect.isgeneratorfunction(func),
            "_discover_raw_items() should be a generator function (use yield, not return list)",
        )

    def test_discover_items_returns_iterator_not_list(self):
        """discover_items() public API should return Iterator, not list.

        When discover_items() is overridden to return list, this test fails.
        After removing the override, BaseExtractor.discover_items() returns Iterator.
        """
        import inspect

        from src.etl.stages.extract.github_extractor import GitHubExtractor

        # Check the return annotation of discover_items on GitHubExtractor
        # If overridden, return type is list; if inherited, return type is Iterator
        method = GitHubExtractor.discover_items
        func = getattr(method, "__func__", method)
        hints = getattr(func, "__annotations__", {})

        # The overridden discover_items() returns list[ProcessingItem]
        # BaseExtractor.discover_items() returns Iterator[ProcessingItem]
        # Verify it's the BaseExtractor version (not overridden)
        self.assertIs(
            func,
            BaseExtractor.discover_items,
            "GitHubExtractor.discover_items should be BaseExtractor.discover_items "
            "(inherited, returning Iterator), not an override returning list",
        )


if __name__ == "__main__":
    unittest.main()
