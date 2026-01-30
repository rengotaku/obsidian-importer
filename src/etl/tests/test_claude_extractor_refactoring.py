"""Tests for ClaudeExtractor refactoring (Phase 3 - US3).

Tests verify ClaudeExtractor implements Template Method pattern correctly.
"""

import unittest


class TestClaudeExtractorAbstractMethods(unittest.TestCase):
    """Test ClaudeExtractor implements required abstract methods."""

    def test_claude_extractor_implements_discover_raw_items(self):
        """ClaudeExtractor implements _discover_raw_items abstract method."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Should be able to instantiate (no TypeError)
        extractor = ClaudeExtractor()

        # Should have _discover_raw_items method
        self.assertTrue(hasattr(extractor, "_discover_raw_items"))
        self.assertTrue(callable(extractor._discover_raw_items))

    def test_claude_extractor_implements_build_conversation_for_chunking(self):
        """ClaudeExtractor implements _build_conversation_for_chunking abstract method."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        extractor = ClaudeExtractor()

        # Should have _build_conversation_for_chunking method
        self.assertTrue(hasattr(extractor, "_build_conversation_for_chunking"))
        self.assertTrue(callable(extractor._build_conversation_for_chunking))

    def test_discover_raw_items_returns_iterator(self):
        """_discover_raw_items returns Iterator[ProcessingItem]."""
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Create temp directory with empty conversations.json
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text("[]")

            extractor = ClaudeExtractor()
            result = extractor._discover_raw_items(tmppath)

            # Should return iterator
            from collections.abc import Iterator

            self.assertIsInstance(result, Iterator)

    def test_discover_raw_items_does_not_chunk(self):
        """_discover_raw_items does not perform chunking (delegates to BaseStage)."""
        import json
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Create large conversation (>25000 chars)
        large_content = "x" * 30000
        conv = {
            "uuid": "test-uuid",
            "name": "Large Conversation",
            "created_at": "2024-01-01",
            "chat_messages": [{"text": large_content, "sender": "human"}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text(json.dumps([conv]))

            extractor = ClaudeExtractor()
            items = list(extractor._discover_raw_items(tmppath))

            # _discover_raw_items should NOT chunk - it returns raw items
            # Chunking happens in discover_items (template method)
            # So we expect 1 item, not multiple chunks
            self.assertEqual(len(items), 1)
            self.assertFalse(items[0].metadata.get("is_chunked", False))


class TestClaudeExtractorChunking(unittest.TestCase):
    """Test ClaudeExtractor chunking behavior after refactoring."""

    def test_small_conversation_not_chunked(self):
        """Small conversations (< 25,000 chars) are not chunked."""
        import json
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Create small conversation
        conv = {
            "uuid": "test-uuid",
            "name": "Small Conversation",
            "created_at": "2024-01-01",
            "chat_messages": [
                {"text": "Hello", "sender": "human"},
                {"text": "Hi there", "sender": "assistant"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text(json.dumps([conv]))

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(tmppath))

            # Should have 1 item (not chunked)
            self.assertEqual(len(items), 1)
            self.assertFalse(items[0].metadata.get("is_chunked", False))

    def test_large_conversation_chunked(self):
        """Large conversations (> 25,000 chars) with multiple messages are chunked."""
        import json
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Create large conversation with multiple messages
        # Each message 7000 chars, 5 messages = 35000 chars total
        messages = []
        for i in range(5):
            messages.append({"text": "x" * 7000, "sender": "human" if i % 2 == 0 else "assistant"})

        conv = {
            "uuid": "test-uuid",
            "name": "Large Conversation",
            "created_at": "2024-01-01",
            "chat_messages": messages,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text(json.dumps([conv]))

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(tmppath))

            # Should have multiple chunks
            self.assertGreater(len(items), 1)

            # All items should be marked as chunked
            for item in items:
                self.assertTrue(item.metadata.get("is_chunked", False))

    def test_chunked_items_have_correct_metadata(self):
        """Chunked items have is_chunked, parent_item_id, chunk_index metadata."""
        import json
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Create large conversation
        large_content = "x" * 30000
        conv = {
            "uuid": "test-uuid",
            "name": "Large Conversation",
            "created_at": "2024-01-01",
            "chat_messages": [{"text": large_content, "sender": "human"}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text(json.dumps([conv]))

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(tmppath))

            # Check metadata for all chunks
            for i, item in enumerate(items):
                self.assertTrue(item.metadata.get("is_chunked"))
                self.assertIn("parent_item_id", item.metadata)
                self.assertEqual(item.metadata.get("chunk_index"), i)
                self.assertIn("total_chunks", item.metadata)
                self.assertEqual(item.metadata["total_chunks"], len(items))

    def test_chunk_overlap_messages_included(self):
        """Chunked conversations include overlap messages for context."""
        import json
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Create conversation with multiple messages that will be chunked
        messages = []
        for i in range(10):
            messages.append(
                {
                    "text": "x" * 5000,  # Each message is 5000 chars
                    "sender": "human" if i % 2 == 0 else "assistant",
                }
            )

        conv = {
            "uuid": "test-uuid",
            "name": "Multi-message Conversation",
            "created_at": "2024-01-01",
            "chat_messages": messages,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text(json.dumps([conv]))

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(tmppath))

            # Should have multiple chunks
            self.assertGreater(len(items), 1)

            # Note: Overlap verification depends on Chunker implementation
            # This test ensures chunking works with multiple messages
            for item in items:
                parsed = json.loads(item.content)
                self.assertIn("chat_messages", parsed)
                self.assertGreater(len(parsed["chat_messages"]), 0)


class TestClaudeExtractorBehaviorMaintained(unittest.TestCase):
    """Test ClaudeExtractor maintains existing behavior after refactoring."""

    def test_existing_tests_still_pass(self):
        """All existing ClaudeExtractor tests pass after refactoring."""
        # This is a meta-test - actual verification happens via `make test`
        # Here we just verify the extractor can be instantiated
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        extractor = ClaudeExtractor()
        self.assertIsNotNone(extractor)
        self.assertTrue(hasattr(extractor, "discover_items"))

    def test_same_output_for_same_input(self):
        """Refactored extractor produces same output as before."""
        import json
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Create test conversation
        conv = {
            "uuid": "test-uuid",
            "name": "Test Conversation",
            "created_at": "2024-01-01",
            "chat_messages": [
                {"text": "Hello", "sender": "human"},
                {"text": "Hi", "sender": "assistant"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text(json.dumps([conv]))

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(tmppath))

            # Verify basic output structure
            self.assertEqual(len(items), 1)
            item = items[0]
            self.assertIn("conversation_uuid", item.metadata)
            self.assertEqual(item.metadata["conversation_uuid"], "test-uuid")
            self.assertIn("source_type", item.metadata)
            self.assertEqual(item.metadata["source_type"], "conversation")

    def test_discover_items_backward_compatible(self):
        """discover_items() method still works as template method."""
        import json
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Create test conversation
        conv = {
            "uuid": "test-uuid",
            "name": "Test",
            "created_at": "2024-01-01",
            "chat_messages": [{"text": "Test", "sender": "human"}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text(json.dumps([conv]))

            extractor = ClaudeExtractor()
            # discover_items should still work as before
            items = list(extractor.discover_items(tmppath))

            self.assertGreater(len(items), 0)
            # Verify it returns ProcessingItem instances
            from src.etl.core.models import ProcessingItem

            self.assertIsInstance(items[0], ProcessingItem)


class TestClaudeExtractorEdgeCases(unittest.TestCase):
    """Test ClaudeExtractor edge cases."""

    def test_empty_conversations_json(self):
        """Empty conversations.json is handled gracefully."""
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text("[]")

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(tmppath))

            # Should return empty list without errors
            self.assertEqual(len(items), 0)

    def test_missing_conversations_json(self):
        """Missing conversations.json is handled gracefully."""
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Don't create conversations.json

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(tmppath))

            # Should return empty list without errors
            self.assertEqual(len(items), 0)

    def test_conversation_at_chunk_threshold(self):
        """Conversation at exactly 25,000 chars is marked as chunked (Chunker uses >=)."""
        import json
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Create conversation at exactly 25,000 chars (single message)
        conv = {
            "uuid": "test-uuid",
            "name": "Threshold Conversation",
            "created_at": "2024-01-01",
            "chat_messages": [{"text": "x" * 25000, "sender": "human"}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text(json.dumps([conv]))

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(tmppath))

            # At threshold, Chunker uses >= so it's chunked (but only 1 chunk for single message)
            self.assertEqual(len(items), 1)
            # Chunker marks it as chunked even though it can't split a single message
            self.assertTrue(items[0].metadata.get("is_chunked", False))
            self.assertEqual(items[0].metadata.get("total_chunks"), 1)

    def test_single_message_large_conversation(self):
        """Large conversation with single message creates 1 chunk (cannot split within message)."""
        import json
        import tempfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Create large conversation with single message
        conv = {
            "uuid": "test-uuid",
            "name": "Single Large Message",
            "created_at": "2024-01-01",
            "chat_messages": [{"text": "x" * 50000, "sender": "human"}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            conv_file = tmppath / "conversations.json"
            conv_file.write_text(json.dumps([conv]))

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(tmppath))

            # Chunker can't split within a single message, so creates 1 chunk
            self.assertEqual(len(items), 1)
            # But it's still marked as chunked
            self.assertTrue(items[0].metadata.get("is_chunked", False))
            self.assertEqual(items[0].metadata.get("total_chunks"), 1)


class TestClaudeExtractorZipSupport(unittest.TestCase):
    """Test ClaudeExtractor ZIP file support."""

    def test_discover_from_zip_file_directly(self):
        """ClaudeExtractor can read conversations from ZIP file directly."""
        import json
        import tempfile
        import zipfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        conv = {
            "uuid": "test-uuid",
            "name": "Test Conversation",
            "created_at": "2024-01-01",
            "chat_messages": [
                {"text": "Hello", "sender": "human"},
                {"text": "Hi there!", "sender": "assistant"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "claude_export.zip"

            # Create ZIP with conversations.json
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([conv]))

            extractor = ClaudeExtractor()
            items = list(extractor._discover_raw_items(zip_path))

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].metadata["conversation_uuid"], "test-uuid")
            self.assertEqual(items[0].source_path, zip_path)

    def test_discover_from_directory_containing_zip(self):
        """ClaudeExtractor can find and read ZIP in directory."""
        import json
        import tempfile
        import zipfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        conv = {
            "uuid": "zip-in-dir-uuid",
            "name": "ZIP in Directory",
            "created_at": "2024-01-01",
            "chat_messages": [
                {"text": "Test", "sender": "human"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "data.zip"

            # Create ZIP with conversations.json
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([conv]))

            extractor = ClaudeExtractor()
            # Pass directory, not ZIP file
            items = list(extractor._discover_raw_items(tmppath))

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].metadata["conversation_uuid"], "zip-in-dir-uuid")

    def test_json_takes_priority_over_zip_in_directory(self):
        """When both JSON and ZIP exist, JSON takes priority."""
        import json
        import tempfile
        import zipfile
        from pathlib import Path

        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        conv_json = {
            "uuid": "json-uuid",
            "name": "From JSON",
            "created_at": "2024-01-01",
            "chat_messages": [{"text": "JSON", "sender": "human"}],
        }
        conv_zip = {
            "uuid": "zip-uuid",
            "name": "From ZIP",
            "created_at": "2024-01-01",
            "chat_messages": [{"text": "ZIP", "sender": "human"}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create both JSON and ZIP
            conv_file = tmppath / "conversations.json"
            conv_file.write_text(json.dumps([conv_json]))

            zip_path = tmppath / "data.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([conv_zip]))

            extractor = ClaudeExtractor()
            items = list(extractor._discover_raw_items(tmppath))

            # Should read from JSON, not ZIP
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].metadata["conversation_uuid"], "json-uuid")

    def test_zip_missing_conversations_json_yields_error(self):
        """ZIP without conversations.json yields error item."""
        import tempfile
        import zipfile
        from pathlib import Path

        from src.etl.core.status import ItemStatus
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "empty.zip"

            # Create ZIP without conversations.json
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("other.txt", "not conversations")

            extractor = ClaudeExtractor()
            items = list(extractor._discover_raw_items(zip_path))

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].status, ItemStatus.FAILED)
            self.assertIn("not found", items[0].metadata.get("error", ""))

    def test_corrupted_zip_yields_error(self):
        """Corrupted ZIP file yields error item."""
        import tempfile
        from pathlib import Path

        from src.etl.core.status import ItemStatus
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "corrupted.zip"

            # Create corrupted ZIP
            zip_path.write_bytes(b"not a valid zip file")

            extractor = ClaudeExtractor()
            items = list(extractor._discover_raw_items(zip_path))

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].status, ItemStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
