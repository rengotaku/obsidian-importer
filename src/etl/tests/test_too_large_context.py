"""Tests for LLM context-based too_large judgment (Feature 038).

Tests for User Story 1 (accurate too_large judgment) and
User Story 2 (message content sum calculation).

These tests verify that the too_large judgment uses the actual LLM context
size (sum of message text fields) instead of the raw JSON size.
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.etl.core.models import ProcessingItem
from src.etl.core.status import ItemStatus
from src.etl.stages.transform.knowledge_transformer import ExtractKnowledgeStep
from src.etl.utils.knowledge_extractor import ExtractionResult, KnowledgeDocument


class TestCalculateLlmContextSize(unittest.TestCase):
    """Test _calculate_llm_context_size() method (US2).

    These tests verify the LLM context size calculation function
    that sums message text fields plus header and label overhead.

    Expected formula:
        LLM_context_size = 200 (header) + sum(msg.text) + 15 * msg_count
    """

    def test_calculate_llm_context_size_basic(self):
        """Basic message size calculation test (T009).

        Given: Conversation with 3 messages (text lengths: 100, 200, 150 chars)
        When: _calculate_llm_context_size() is called
        Then: Returns ~200 (header) + 450 (messages) + 45 (labels) = ~695 chars
        """
        step = ExtractKnowledgeStep()

        # Create conversation data with known message lengths
        conversation_data = {
            "uuid": "test-uuid",
            "name": "Test Conversation",
            "created_at": "2026-01-27T10:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "x" * 100},  # 100 chars
                {"sender": "assistant", "text": "y" * 200},  # 200 chars
                {"sender": "human", "text": "z" * 150},  # 150 chars
            ],
        }

        # Call the method (should fail - method doesn't exist yet)
        result = step._calculate_llm_context_size(conversation_data)

        # Expected: header(200) + messages(450) + labels(3*15=45) = 695
        # Allow 10% margin for actual header variation
        expected_min = 650
        expected_max = 750

        self.assertGreaterEqual(result, expected_min)
        self.assertLessEqual(result, expected_max)
        # More precise check: message content should be the bulk
        self.assertGreaterEqual(result, 450)  # At minimum, message text

    def test_calculate_llm_context_size_empty_messages(self):
        """Empty messages array size calculation test (T010).

        Given: Conversation with 0 messages
        When: _calculate_llm_context_size() is called
        Then: Returns ~200 (header only)
        """
        step = ExtractKnowledgeStep()

        conversation_data = {
            "uuid": "empty-uuid",
            "name": "Empty Conversation",
            "created_at": "2026-01-27T10:00:00Z",
            "chat_messages": [],  # No messages
        }

        result = step._calculate_llm_context_size(conversation_data)

        # Should be approximately header size only (~200 chars)
        # Allow reasonable margin
        self.assertGreaterEqual(result, 150)
        self.assertLessEqual(result, 300)

    def test_calculate_llm_context_size_null_text(self):
        """Null or empty text field handling test (T011).

        Given: Messages with null or empty text fields
        When: _calculate_llm_context_size() is called
        Then: Those messages contribute 0 chars to the message sum
        """
        step = ExtractKnowledgeStep()

        conversation_data = {
            "uuid": "null-text-uuid",
            "name": "Null Text Conversation",
            "created_at": "2026-01-27T10:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "x" * 100},  # 100 chars
                {"sender": "assistant", "text": None},  # null -> 0 chars
                {"sender": "human", "text": ""},  # empty -> 0 chars
                {"sender": "assistant", "text": "y" * 50},  # 50 chars
            ],
        }

        result = step._calculate_llm_context_size(conversation_data)

        # Expected: header(200) + messages(150) + labels(4*15=60) = 410
        # Messages with null/empty text should not add to message sum
        expected_min = 350
        expected_max = 500

        self.assertGreaterEqual(result, expected_min)
        self.assertLessEqual(result, expected_max)

    def test_calculate_llm_context_size_missing_text_field(self):
        """Missing text field handling test (edge case).

        Given: Messages without text field at all
        When: _calculate_llm_context_size() is called
        Then: Those messages contribute 0 chars
        """
        step = ExtractKnowledgeStep()

        conversation_data = {
            "uuid": "missing-text-uuid",
            "name": "Missing Text Conversation",
            "created_at": "2026-01-27T10:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "x" * 100},
                {"sender": "assistant"},  # No text field at all
                {"sender": "human", "text": "y" * 100},
            ],
        }

        result = step._calculate_llm_context_size(conversation_data)

        # Expected: header(200) + messages(200) + labels(3*15=45) = 445
        expected_min = 400
        expected_max = 550

        self.assertGreaterEqual(result, expected_min)
        self.assertLessEqual(result, expected_max)

    def test_calculate_llm_context_size_chatgpt_format(self):
        """Test _calculate_llm_context_size with ChatGPT export format (T025).

        ChatGPT exports use 'mapping' structure but ExtractKnowledgeStep
        receives normalized data with 'chat_messages' array after extraction.
        Both Claude and ChatGPT use 'text' field for message content.

        Given: ChatGPT conversation data (normalized to chat_messages format)
        When: _calculate_llm_context_size() is called
        Then: Returns correct LLM context size based on text fields
        """
        step = ExtractKnowledgeStep()

        # ChatGPT data after extraction (normalized to chat_messages format)
        # Note: ChatGPT extractor normalizes 'mapping' structure to 'chat_messages'
        chatgpt_data = {
            "uuid": "chatgpt-uuid",
            "name": "ChatGPT Conversation",
            "created_at": "2026-01-27T10:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "Hello ChatGPT"},  # 13 chars
                {"sender": "assistant", "text": "Hello! How can I help you?"},  # 26 chars
                {"sender": "human", "text": "What's the weather?"},  # 19 chars
            ],
        }

        size = step._calculate_llm_context_size(chatgpt_data)

        # Expected: HEADER (200) + text sum (13 + 26 + 19 = 58) + labels (3 * 15 = 45) = 303
        # Allow reasonable margin for header variation
        self.assertGreater(size, 250, "Size should be at least 250 (messages + labels + header)")
        self.assertLess(size, 350, "Size should not exceed 350 for small conversation")

        # More precise verification: message content is the key component
        expected_message_size = 13 + 26 + 19  # 58 chars ("Hello ChatGPT" is 13 chars)
        expected_label_size = 3 * 15  # 45 chars
        expected_header = 200
        expected_total = expected_header + expected_message_size + expected_label_size  # 303

        # Verify exact calculation matches our expectation
        self.assertEqual(size, expected_total, f"Expected {expected_total}, got {size}")


class TestTooLargeJudgmentWithLlmContext(unittest.TestCase):
    """Test too_large judgment using LLM context size (US1).

    These tests verify that the too_large judgment uses the calculated
    LLM context size instead of raw item.content size.
    """

    def test_too_large_judgment_with_llm_context(self):
        """Previously skipped item now processable with new judgment (T012).

        Given: item.content = 50,000 chars (JSON overhead)
               LLM context = 20,000 chars (actual messages)
        When: ExtractKnowledgeStep.process() is called
        Then: Item is NOT skipped (old: skipped, new: processable)

        This is the key test for User Story 1 - items that were incorrectly
        marked as too_large due to JSON overhead should now be processed.
        """
        step = ExtractKnowledgeStep()

        # Create conversation where JSON is large but actual messages are small
        # JSON overhead: metadata, duplicated text in content array, etc.
        message_text = "x" * 6000  # Each message ~6000 chars

        conversation_data = {
            "uuid": "overhead-test-uuid",
            "name": "JSON Overhead Test",
            "created_at": "2026-01-27T10:00:00Z",
            "updated_at": "2026-01-27T12:00:00Z",
            "summary": "Test summary",
            "account": {"uuid": "account-uuid", "name": "Test Account"},
            "chat_messages": [
                {
                    "uuid": "msg-1",
                    "sender": "human",
                    "text": message_text,
                    "content": [{"text": message_text, "type": "text"}],  # Duplicated!
                    "created_at": "2026-01-27T10:00:00Z",
                    "attachments": [],
                    "files": [],
                },
                {
                    "uuid": "msg-2",
                    "sender": "assistant",
                    "text": message_text,
                    "content": [{"text": message_text, "type": "text"}],  # Duplicated!
                    "created_at": "2026-01-27T10:01:00Z",
                    "attachments": [],
                    "files": [],
                },
                {
                    "uuid": "msg-3",
                    "sender": "human",
                    "text": message_text,
                    "content": [{"text": message_text, "type": "text"}],  # Duplicated!
                    "created_at": "2026-01-27T10:02:00Z",
                    "attachments": [],
                    "files": [],
                },
            ],
        }

        content_json = json.dumps(conversation_data)

        # Verify JSON size > 25000 (threshold) but LLM context < 25000
        # 3 messages * 6000 chars = 18000 chars (LLM context)
        # JSON with duplication and metadata should be > 25000
        self.assertGreater(
            len(content_json),
            25000,
            f"Test setup error: JSON should exceed threshold, got {len(content_json)}",
        )

        item = ProcessingItem(
            item_id="overhead-test-uuid",
            source_path=Path("/test/overhead.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
                "chunk_enabled": False,  # No chunking
            },
            content=content_json,
        )

        # Mock the extractor to return success
        mock_document = KnowledgeDocument(
            title="JSON Overhead Test",
            summary="Test summary",
            created="2026-01-27",
            source_provider="claude",
            source_conversation="overhead-test-uuid",
            summary_content="Content",
            code_snippets=[],
            references=[],
            item_id="",
            normalized=False,
        )

        mock_result = ExtractionResult(
            success=True,
            document=mock_document,
            raw_response='{"summary": "Test"}',
            user_prompt="Test prompt",
        )

        with patch.object(step, "_extractor", create=True):
            step._extractor = MagicMock()
            step._extractor.extract.return_value = mock_result
            step._extractor.should_chunk.return_value = False
            step._extractor.is_english_summary.return_value = False

            result = step.process(item)

            # Key assertion: Item should NOT be skipped as too_large
            # With the new LLM context-based judgment, this item is processable
            self.assertNotEqual(
                result.metadata.get("skipped_reason"),
                "too_large",
                "Item should NOT be skipped with new LLM context-based judgment",
            )
            self.assertFalse(
                result.metadata.get("too_large", False),
                "too_large should NOT be set for items within LLM context threshold",
            )

            # Verify extraction was called (not skipped)
            step._extractor.extract.assert_called_once()

    def test_too_large_judgment_still_skips_large(self):
        """Items with large LLM context are still skipped (T013).

        Given: item.content = 60,000 chars
               LLM context = 30,000 chars (exceeds 25000 threshold)
        When: ExtractKnowledgeStep.process() is called
        Then: Item is skipped as too_large
        """
        step = ExtractKnowledgeStep()

        # Create conversation with truly large message content
        large_message = "x" * 15000  # 15000 chars per message

        conversation_data = {
            "uuid": "large-content-uuid",
            "name": "Large Content Test",
            "created_at": "2026-01-27T10:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": large_message},  # 15000 chars
                {"sender": "assistant", "text": large_message},  # 15000 chars
            ],
        }

        content_json = json.dumps(conversation_data)

        item = ProcessingItem(
            item_id="large-content-uuid",
            source_path=Path("/test/large.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
                "chunk_enabled": False,  # No chunking
            },
            content=content_json,
        )

        result = step.process(item)

        # Should be skipped as too_large (LLM context > 25000)
        self.assertEqual(
            result.metadata.get("skipped_reason"),
            "too_large",
            "Item should be skipped when LLM context exceeds threshold",
        )
        self.assertTrue(result.metadata.get("too_large", False), "too_large flag should be set")
        self.assertEqual(result.status, ItemStatus.FILTERED)

    def test_chunk_enabled_bypasses_judgment(self):
        """chunk_enabled=True bypasses too_large judgment (T014).

        Given: Large content that would trigger too_large
               chunk_enabled = True
        When: ExtractKnowledgeStep.process() is called
        Then: Item is NOT skipped (chunk logic handles it)
        """
        step = ExtractKnowledgeStep()

        # Create large conversation
        large_message = "x" * 15000

        conversation_data = {
            "uuid": "chunked-uuid",
            "name": "Chunked Test",
            "created_at": "2026-01-27T10:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": large_message},
                {"sender": "assistant", "text": large_message},
            ],
        }

        content_json = json.dumps(conversation_data)

        item = ProcessingItem(
            item_id="chunked-uuid",
            source_path=Path("/test/chunked.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
                "chunk_enabled": True,  # Chunking enabled!
            },
            content=content_json,
        )

        # Mock the extractor to return success
        mock_document = KnowledgeDocument(
            title="Chunked Test",
            summary="Test summary",
            created="2026-01-27",
            source_provider="claude",
            source_conversation="chunked-uuid",
            summary_content="Content",
            code_snippets=[],
            references=[],
            item_id="",
            normalized=False,
        )

        mock_result = ExtractionResult(
            success=True,
            document=mock_document,
            raw_response='{"summary": "Test"}',
            user_prompt="Test prompt",
        )

        with patch.object(step, "_extractor", create=True):
            step._extractor = MagicMock()
            step._extractor.extract.return_value = mock_result
            step._extractor.should_chunk.return_value = False
            step._extractor.is_english_summary.return_value = False

            result = step.process(item)

            # Should NOT be skipped - chunk_enabled bypasses too_large check
            self.assertNotEqual(
                result.metadata.get("skipped_reason"),
                "too_large",
                "Item should NOT be skipped when chunk_enabled=True",
            )
            self.assertFalse(
                result.metadata.get("too_large", False),
                "too_large should NOT be set when chunk_enabled=True",
            )

    def test_is_chunked_bypasses_judgment(self):
        """is_chunked=True bypasses too_large judgment (edge case).

        Given: Large chunk item (already chunked)
               is_chunked = True
        When: ExtractKnowledgeStep.process() is called
        Then: Item is NOT skipped (already chunked)
        """
        step = ExtractKnowledgeStep()

        # This is a chunk that was split from a larger conversation
        chunk_message = "x" * 20000  # Large but already a chunk

        conversation_data = {
            "uuid": "chunk-part-uuid",
            "name": "Chunk Part (1/2)",
            "created_at": "2026-01-27T10:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": chunk_message},
            ],
        }

        content_json = json.dumps(conversation_data)

        item = ProcessingItem(
            item_id="chunk-part-uuid-0",
            source_path=Path("/test/chunk.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
                "chunk_enabled": False,  # Original flag doesn't matter
                "is_chunked": True,  # Already chunked!
                "chunk_index": 0,
                "total_chunks": 2,
            },
            content=content_json,
        )

        # Mock the extractor
        mock_document = KnowledgeDocument(
            title="Chunk Part (1/2)",
            summary="Test",
            created="2026-01-27",
            source_provider="claude",
            source_conversation="chunk-part-uuid",
            summary_content="Content",
            code_snippets=[],
            references=[],
            item_id="",
            normalized=False,
        )

        mock_result = ExtractionResult(
            success=True,
            document=mock_document,
            raw_response="{}",
            user_prompt="prompt",
        )

        with patch.object(step, "_extractor", create=True):
            step._extractor = MagicMock()
            step._extractor.extract.return_value = mock_result
            step._extractor.should_chunk.return_value = False
            step._extractor.is_english_summary.return_value = False

            result = step.process(item)

            # Should NOT be skipped - is_chunked bypasses check
            self.assertNotEqual(
                result.metadata.get("skipped_reason"),
                "too_large",
                "Already chunked items should NOT be skipped",
            )


if __name__ == "__main__":
    unittest.main()
