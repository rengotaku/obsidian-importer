"""Tests for KnowledgeTransformer stage.

Tests for US1 (Ollama knowledge extraction) and US2 (item_id generation).
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.etl.core.errors import StepError
from src.etl.core.models import ProcessingItem
from src.etl.core.status import ItemStatus
from src.etl.core.types import StageType
from src.etl.stages.transform.knowledge_transformer import (
    ExtractKnowledgeStep,
    FormatMarkdownStep,
    GenerateMetadataStep,
    KnowledgeTransformer,
)
from src.etl.utils.knowledge_extractor import ExtractionResult, KnowledgeDocument


class TestExtractKnowledgeStepWithMockedOllama(unittest.TestCase):
    """Test ExtractKnowledgeStep with mocked Ollama (US1)."""

    def test_extract_knowledge_calls_extractor(self):
        """ExtractKnowledgeStep calls KnowledgeExtractor.extract()."""
        step = ExtractKnowledgeStep()

        # Create a mock KnowledgeDocument
        mock_document = KnowledgeDocument(
            title="Test Title",
            summary="Test summary",
            created="2026-01-19",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="Test content",
            code_snippets=[],
            references=[],
            item_id="abc123def456",
            normalized=False,
        )

        mock_result = ExtractionResult(
            success=True,
            document=mock_document,
            raw_response='{"summary": "Test"}',
            user_prompt="Test prompt",
        )

        # Create item with conversation data
        conversation_data = {
            "uuid": "test-uuid",
            "name": "Test Conversation",
            "created_at": "2026-01-19T10:00:00Z",
            "updated_at": "2026-01-19T12:00:00Z",
            "summary": "English summary",
            "chat_messages": [
                {"sender": "human", "text": "Hello"},
                {"sender": "assistant", "text": "Hi there!"},
                {"sender": "human", "text": "How are you?"},
                {"sender": "assistant", "text": "I'm fine!"},
            ],
        }

        item = ProcessingItem(
            item_id="test-uuid",
            source_path=Path("/test/conversation.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "conversation_uuid": "test-uuid",
                "conversation_name": "Test Conversation",
                "message_count": 4,
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        # Mock the extractor
        with patch.object(step, "_extractor", create=True) as mock_extractor_attr:
            # Set up the mock on the step's extractor
            step._extractor = MagicMock()
            step._extractor.extract.return_value = mock_result
            # Mock should_chunk to return False (small conversation)
            step._extractor.should_chunk.return_value = False
            # Mock is_english_summary to return False (no translation needed)
            step._extractor.is_english_summary.return_value = False

            result = step.process(item)

            # Verify extraction was called
            step._extractor.extract.assert_called_once()

            # Verify metadata is set
            self.assertTrue(result.metadata.get("knowledge_extracted"))
            self.assertIn("knowledge_document", result.metadata)

    def test_extract_knowledge_handles_extraction_failure(self):
        """ExtractKnowledgeStep handles extraction failure gracefully."""
        step = ExtractKnowledgeStep()

        mock_result = ExtractionResult(
            success=False,
            document=None,
            error="Ollama connection failed",
            raw_response="",
            user_prompt="Test prompt",
        )

        conversation_data = {
            "uuid": "test-uuid",
            "name": "Test Conversation",
            "created_at": "2026-01-19T10:00:00Z",
            "updated_at": "2026-01-19T12:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "Hello"},
                {"sender": "assistant", "text": "Hi!"},
                {"sender": "human", "text": "Test"},
                {"sender": "assistant", "text": "Response"},
            ],
        }

        item = ProcessingItem(
            item_id="test-uuid",
            source_path=Path("/test/conversation.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        with patch.object(step, "_extractor", create=True):
            step._extractor = MagicMock()
            step._extractor.extract.return_value = mock_result
            # Mock should_chunk to return False (small conversation)
            step._extractor.should_chunk.return_value = False
            # Mock is_english_summary to return False (no translation needed)
            step._extractor.is_english_summary.return_value = False

            # Should raise StepError on failure
            from src.etl.core.errors import StepError

            with self.assertRaises(StepError) as ctx:
                step.process(item)

            self.assertIn("Ollama connection failed", str(ctx.exception))

    def test_extract_knowledge_sets_metadata_keys(self):
        """ExtractKnowledgeStep sets knowledge_extracted and item_id in metadata."""
        step = ExtractKnowledgeStep()

        mock_document = KnowledgeDocument(
            title="Test",
            summary="Summary",
            created="2026-01-19",
            source_provider="claude",
            source_conversation="uuid-123",
            summary_content="Content",
            code_snippets=[],
            references=[],
            item_id="",  # Will be set by GenerateMetadataStep
            normalized=False,
        )

        mock_result = ExtractionResult(
            success=True,
            document=mock_document,
            raw_response="{}",
            user_prompt="prompt",
        )

        conversation_data = {
            "uuid": "uuid-123",
            "name": "Test",
            "created_at": "2026-01-19T10:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "Q1"},
                {"sender": "assistant", "text": "A1"},
                {"sender": "human", "text": "Q2"},
                {"sender": "assistant", "text": "A2"},
            ],
        }

        item = ProcessingItem(
            item_id="uuid-123",
            source_path=Path("/test/test.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        with patch.object(step, "_extractor", create=True):
            step._extractor = MagicMock()
            step._extractor.extract.return_value = mock_result
            # Mock should_chunk to return False (small conversation)
            step._extractor.should_chunk.return_value = False
            # Mock is_english_summary to return False (no translation needed)
            step._extractor.is_english_summary.return_value = False

            result = step.process(item)

            # T032: knowledge_extracted metadata key
            self.assertTrue(result.metadata.get("knowledge_extracted"))
            # knowledge_document should be stored
            self.assertIsNotNone(result.metadata.get("knowledge_document"))


class TestGenerateMetadataStepFileId(unittest.TestCase):
    """Test GenerateMetadataStep item_id generation (US2)."""

    def test_item_id_generated_for_conversation(self):
        """GenerateMetadataStep generates item_id for conversation."""
        step = GenerateMetadataStep()

        # Create item with knowledge_document in metadata
        mock_document = KnowledgeDocument(
            title="Test Title",
            summary="Test summary",
            created="2026-01-19",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="Content here",
            code_snippets=[],
            references=[],
            item_id="",  # Not yet set
            normalized=False,
        )

        item = ProcessingItem(
            item_id="test-uuid",
            source_path=Path("/test/conversation.json"),
            current_step="extract_knowledge",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "conversation_name": "Test Title",
                "conversation_uuid": "test-uuid",
                "knowledge_extracted": True,
                "knowledge_document": mock_document,
                "source_provider": "claude",
            },
            content="Some content",
            transformed_content="Transformed content",
        )

        result = step.process(item)

        # Verify item_id is set in metadata
        self.assertIn("item_id", result.metadata)
        item_id = result.metadata["item_id"]
        self.assertEqual(item_id, "test-uuid")  # Should use item.item_id

        # Verify knowledge_document.item_id is updated
        doc = result.metadata.get("knowledge_document")
        if doc:
            self.assertEqual(doc.item_id, item_id)

    def test_item_id_deterministic(self):
        """item_id is deterministic for same content and path."""
        step = GenerateMetadataStep()

        mock_document = KnowledgeDocument(
            title="Test",
            summary="Summary",
            created="2026-01-19",
            source_provider="claude",
            source_conversation="uuid-1",
            summary_content="Content",
            code_snippets=[],
            references=[],
            item_id="",
            normalized=False,
        )

        content = "Same content"
        path = Path("/test/same.json")

        item1 = ProcessingItem(
            item_id="uuid-1",
            source_path=path,
            current_step="extract_knowledge",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "knowledge_extracted": True,
                "knowledge_document": mock_document,
                "source_provider": "claude",
            },
            content=content,
            transformed_content=content,
        )

        item2 = ProcessingItem(
            item_id="uuid-1",
            source_path=path,
            current_step="extract_knowledge",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "knowledge_extracted": True,
                "knowledge_document": KnowledgeDocument(
                    title="Test",
                    summary="Summary",
                    created="2026-01-19",
                    source_provider="claude",
                    source_conversation="uuid-1",
                    summary_content="Content",
                    code_snippets=[],
                    item_id="",
                    normalized=False,
                ),
                "source_provider": "claude",
            },
            content=content,
            transformed_content=content,
        )

        result1 = step.process(item1)
        result2 = step.process(item2)

        # Same content + path = same item_id
        self.assertEqual(
            result1.metadata["item_id"],
            result2.metadata["item_id"],
        )

    def test_item_id_different_for_different_content(self):
        """item_id differs for different content."""
        step = GenerateMetadataStep()

        path = Path("/test/file.json")

        item1 = ProcessingItem(
            item_id="uuid-1",
            source_path=path,
            current_step="extract_knowledge",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "knowledge_extracted": True,
                "knowledge_document": KnowledgeDocument(
                    title="Test",
                    summary="",
                    created="",
                    source_provider="",
                    source_conversation="",
                    summary_content="",
                    code_snippets=[],
                    references=[],
                    item_id="",
                    normalized=False,
                ),
                "source_provider": "claude",
            },
            content="Content A",
            transformed_content="Content A",
        )

        item2 = ProcessingItem(
            item_id="uuid-2",
            source_path=path,
            current_step="extract_knowledge",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "knowledge_extracted": True,
                "knowledge_document": KnowledgeDocument(
                    title="Test",
                    summary="",
                    created="",
                    source_provider="",
                    source_conversation="",
                    summary_content="",
                    code_snippets=[],
                    references=[],
                    item_id="",
                    normalized=False,
                ),
                "source_provider": "claude",
            },
            content="Content B",
            transformed_content="Content B",
        )

        result1 = step.process(item1)
        result2 = step.process(item2)

        self.assertNotEqual(
            result1.metadata["item_id"],
            result2.metadata["item_id"],
        )


class TestFormatMarkdownStepOutput(unittest.TestCase):
    """Test FormatMarkdownStep output format (US1)."""

    def test_format_markdown_uses_knowledge_document(self):
        """FormatMarkdownStep uses KnowledgeDocument.to_markdown()."""
        step = FormatMarkdownStep()

        mock_document = KnowledgeDocument(
            title="Test Title",
            summary="This is a test summary",
            created="2026-01-19",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="## Summary Content\n\nDetailed summary here.",
            code_snippets=[],
            references=[],
            item_id="abc123def456",
            normalized=False,
        )

        item = ProcessingItem(
            item_id="test-uuid",
            source_path=Path("/test/conversation.json"),
            current_step="generate_metadata",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "knowledge_extracted": True,
                "knowledge_document": mock_document,
                "item_id": "abc123def456",
                "source_provider": "claude",
            },
            content="{}",
            transformed_content="{}",
        )

        result = step.process(item)

        # Verify markdown was generated
        markdown = result.transformed_content
        self.assertIsNotNone(markdown)

        # Verify frontmatter
        self.assertIn("---", markdown)
        self.assertIn("title: Test Title", markdown)
        self.assertIn("item_id: abc123def456", markdown)

        # Verify content sections
        self.assertIn("Summary Content", markdown)

    def test_format_markdown_includes_code_snippets(self):
        """FormatMarkdownStep includes code within summary_content."""
        step = FormatMarkdownStep()

        # コードは summary_content 内に含まれる（新仕様）
        mock_document = KnowledgeDocument(
            title="Code Example",
            summary="Example with code",
            created="2026-01-19",
            source_provider="claude",
            source_conversation="uuid-code",
            summary_content="""## Hello World Example

以下のコードで実現できます。

```python
print('Hello')
```""",
            code_snippets=[],  # 空配列（後方互換性のため）
            references=[],
            item_id="code123",
            normalized=False,
        )

        item = ProcessingItem(
            item_id="uuid-code",
            source_path=Path("/test/code.json"),
            current_step="generate_metadata",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "knowledge_extracted": True,
                "knowledge_document": mock_document,
                "item_id": "code123",
                "source_provider": "claude",
            },
            content="{}",
            transformed_content="{}",
        )

        result = step.process(item)

        markdown = result.transformed_content

        # Verify code is in summary_content
        self.assertIn("```python", markdown)
        self.assertIn("print('Hello')", markdown)
        self.assertIn("Hello World Example", markdown)

    def test_format_markdown_fallback_for_non_conversation(self):
        """FormatMarkdownStep handles non-conversation items."""
        step = FormatMarkdownStep()

        item = ProcessingItem(
            item_id="memories",
            source_path=Path("/test/memories.json"),
            current_step="generate_metadata",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "memories",
                "generated_metadata": {
                    "title": "Memories",
                    "tags": ["claude-export", "memories"],
                },
            },
            content='{"items": []}',
            transformed_content='{"items": []}',
        )

        result = step.process(item)

        markdown = result.transformed_content
        self.assertIn("---", markdown)
        self.assertIn("title: Memories", markdown)
        self.assertIn("normalized: true", markdown)


class TestKnowledgeTransformerStage(unittest.TestCase):
    """Test KnowledgeTransformer stage integration."""

    def test_knowledge_transformer_has_correct_steps(self):
        """KnowledgeTransformer has the expected steps."""
        transformer = KnowledgeTransformer()

        self.assertEqual(transformer.stage_type, StageType.TRANSFORM)
        self.assertEqual(len(transformer.steps), 3)

        step_names = [step.name for step in transformer.steps]
        self.assertEqual(
            step_names,
            ["extract_knowledge", "generate_metadata", "format_markdown"],
        )


@unittest.skip("_should_chunk() method removed - chunking now at ImportPhase level")
class TestShouldChunk(unittest.TestCase):
    """Test _should_chunk() method in ExtractKnowledgeStep (US3)."""

    def test_should_chunk_returns_true_for_large_conversation(self):
        """_should_chunk() returns True for conversation exceeding threshold."""
        step = ExtractKnowledgeStep()

        # Create large conversation (> 25000 chars)
        large_messages = [
            {"sender": "human", "text": "x" * 10000},
            {"sender": "assistant", "text": "y" * 10000},
            {"sender": "human", "text": "z" * 10000},
        ]

        conversation_data = {
            "uuid": "large-uuid",
            "name": "Large Conversation",
            "created_at": "2026-01-19T10:00:00Z",
            "chat_messages": large_messages,
        }

        item = ProcessingItem(
            item_id="large-uuid",
            source_path=Path("/test/large.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        result = step._should_chunk(item)
        self.assertTrue(result)

    def test_should_chunk_returns_false_for_small_conversation(self):
        """_should_chunk() returns False for conversation under threshold."""
        step = ExtractKnowledgeStep()

        small_messages = [
            {"sender": "human", "text": "Hello!"},
            {"sender": "assistant", "text": "Hi there!"},
        ]

        conversation_data = {
            "uuid": "small-uuid",
            "name": "Small Conversation",
            "created_at": "2026-01-19T10:00:00Z",
            "chat_messages": small_messages,
        }

        item = ProcessingItem(
            item_id="small-uuid",
            source_path=Path("/test/small.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        result = step._should_chunk(item)
        self.assertFalse(result)

    def test_should_chunk_returns_false_for_non_conversation(self):
        """_should_chunk() returns False for non-conversation items."""
        step = ExtractKnowledgeStep()

        item = ProcessingItem(
            item_id="memories",
            source_path=Path("/test/memories.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={"source_type": "memories"},
            content='{"items": []}',
        )

        result = step._should_chunk(item)
        self.assertFalse(result)


@unittest.skip("_handle_chunked_conversation() method removed - chunking now at ImportPhase level")
class TestChunkSplittingMultipleOutputs(unittest.TestCase):
    """Test chunk splitting with multiple outputs (US3)."""

    def test_chunked_conversation_produces_multiple_items(self):
        """Chunked conversation produces multiple ProcessingItems."""
        step = ExtractKnowledgeStep()

        # Create conversation with multiple chunks (3 chunks at 25000 chars each)
        large_messages = []
        for i in range(9):
            large_messages.append(
                {"sender": "human" if i % 2 == 0 else "assistant", "text": "x" * 10000}
            )

        conversation_data = {
            "uuid": "chunked-uuid",
            "name": "Chunked Conversation",
            "created_at": "2026-01-19T10:00:00Z",
            "chat_messages": large_messages,
        }

        item = ProcessingItem(
            item_id="chunked-uuid",
            source_path=Path("/test/chunked.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        # Mock the extractor to return success for each chunk
        mock_document = KnowledgeDocument(
            title="Test",
            summary="Summary",
            created="2026-01-19",
            source_provider="claude",
            source_conversation="test-uuid",
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
            # Also mock extract_chunked
            step._extractor.should_chunk.return_value = True
            step._extractor.extract_chunked.return_value = [
                ("Chunked Conversation_001.md", mock_result),
                ("Chunked Conversation_002.md", mock_result),
                ("Chunked Conversation_003.md", mock_result),
            ]

            # Call the chunked handler
            results = step._handle_chunked_conversation(item)

            # Verify multiple items returned
            self.assertEqual(len(results), 3)

            # Verify chunk metadata
            for i, result_item in enumerate(results):
                self.assertTrue(result_item.metadata.get("is_chunked"))
                self.assertEqual(result_item.metadata.get("chunk_index"), i)
                self.assertEqual(result_item.metadata.get("total_chunks"), 3)

    def test_chunk_items_have_unique_ids(self):
        """Each chunk item has a unique item_id."""
        step = ExtractKnowledgeStep()

        large_messages = [
            {"sender": "human", "text": "x" * 15000},
            {"sender": "assistant", "text": "y" * 15000},
        ]

        conversation_data = {
            "uuid": "chunk-id-test",
            "name": "ID Test",
            "created_at": "2026-01-19T10:00:00Z",
            "chat_messages": large_messages,
        }

        item = ProcessingItem(
            item_id="chunk-id-test",
            source_path=Path("/test/idtest.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        mock_document = KnowledgeDocument(
            title="Test",
            summary="Summary",
            created="2026-01-19",
            source_provider="claude",
            source_conversation="test-uuid",
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
            step._extractor.should_chunk.return_value = True
            step._extractor.extract_chunked.return_value = [
                ("ID Test_001.md", mock_result),
                ("ID Test_002.md", mock_result),
            ]

            results = step._handle_chunked_conversation(item)

            # Verify unique IDs
            ids = [r.item_id for r in results]
            self.assertEqual(len(ids), len(set(ids)))  # All unique

            # Verify ID format includes chunk number
            self.assertIn("#chunk0", ids[0])
            self.assertIn("#chunk1", ids[1])


@unittest.skip("_handle_chunked_conversation() method removed - chunking now at ImportPhase level")
class TestPartialChunkFailureHandling(unittest.TestCase):
    """Test partial chunk failure handling (US3)."""

    def test_partial_failure_returns_successful_chunks(self):
        """Partial chunk failure returns successful chunks."""
        step = ExtractKnowledgeStep()

        large_messages = [
            {"sender": "human", "text": "x" * 15000},
            {"sender": "assistant", "text": "y" * 15000},
        ]

        conversation_data = {
            "uuid": "partial-fail-uuid",
            "name": "Partial Fail Test",
            "created_at": "2026-01-19T10:00:00Z",
            "chat_messages": large_messages,
        }

        item = ProcessingItem(
            item_id="partial-fail-uuid",
            source_path=Path("/test/partial.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        mock_doc_success = KnowledgeDocument(
            title="Success",
            summary="Success summary",
            created="2026-01-19",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="Content",
            code_snippets=[],
            references=[],
            item_id="",
            normalized=False,
        )

        success_result = ExtractionResult(
            success=True,
            document=mock_doc_success,
            raw_response="{}",
            user_prompt="prompt",
        )

        fail_result = ExtractionResult(
            success=False,
            document=None,
            error="Ollama timeout",
            raw_response="",
            user_prompt="prompt",
        )

        with patch.object(step, "_extractor", create=True):
            step._extractor = MagicMock()
            step._extractor.should_chunk.return_value = True
            step._extractor.extract_chunked.return_value = [
                ("Partial Fail Test_001.md", success_result),
                ("Partial Fail Test_002.md", fail_result),
            ]

            results = step._handle_chunked_conversation(item)

            # Should return 2 items (one success, one failed)
            self.assertEqual(len(results), 2)

            # First item is successful
            self.assertTrue(results[0].metadata.get("knowledge_extracted"))

            # Second item failed
            self.assertFalse(results[1].metadata.get("knowledge_extracted"))
            self.assertIn("Ollama timeout", results[1].metadata.get("extraction_error", ""))

    def test_all_chunks_fail_returns_failed_items(self):
        """All chunks failing returns all failed items."""
        step = ExtractKnowledgeStep()

        large_messages = [
            {"sender": "human", "text": "x" * 15000},
            {"sender": "assistant", "text": "y" * 15000},
        ]

        conversation_data = {
            "uuid": "all-fail-uuid",
            "name": "All Fail Test",
            "created_at": "2026-01-19T10:00:00Z",
            "chat_messages": large_messages,
        }

        item = ProcessingItem(
            item_id="all-fail-uuid",
            source_path=Path("/test/allfail.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        fail_result = ExtractionResult(
            success=False,
            document=None,
            error="API error",
            raw_response="",
            user_prompt="prompt",
        )

        with patch.object(step, "_extractor", create=True):
            step._extractor = MagicMock()
            step._extractor.should_chunk.return_value = True
            step._extractor.extract_chunked.return_value = [
                ("All Fail Test_001.md", fail_result),
                ("All Fail Test_002.md", fail_result),
            ]

            results = step._handle_chunked_conversation(item)

            # All items should have failed
            self.assertEqual(len(results), 2)
            for result_item in results:
                self.assertFalse(result_item.metadata.get("knowledge_extracted"))


class TestIsEnglishSummaryDetection(unittest.TestCase):
    """Test is_english_summary() detection (US4)."""

    def test_detects_english_summary_with_conversation_overview(self):
        """is_english_summary() detects English with 'Conversation Overview' pattern."""
        step = ExtractKnowledgeStep()

        english_summary = """**Conversation Overview**
The user asked about Python best practices and the assistant
provided detailed recommendations for code organization."""

        result = step._extractor.is_english_summary(english_summary)
        self.assertTrue(result)

    def test_detects_english_summary_with_high_ascii_ratio(self):
        """is_english_summary() detects English with high ASCII ratio."""
        step = ExtractKnowledgeStep()

        english_summary = (
            "The user discussed TypeScript configuration options and debugging techniques."
        )

        result = step._extractor.is_english_summary(english_summary)
        self.assertTrue(result)

    def test_returns_false_for_japanese_summary(self):
        """is_english_summary() returns False for Japanese summary."""
        step = ExtractKnowledgeStep()

        japanese_summary = "ユーザーはPythonのベストプラクティスについて質問し、アシスタントはコード構成に関する詳細な推奨事項を提供しました。"

        result = step._extractor.is_english_summary(japanese_summary)
        self.assertFalse(result)

    def test_returns_false_for_none_summary(self):
        """is_english_summary() returns False for None."""
        step = ExtractKnowledgeStep()

        result = step._extractor.is_english_summary(None)
        self.assertFalse(result)

    def test_returns_false_for_empty_summary(self):
        """is_english_summary() returns False for empty string."""
        step = ExtractKnowledgeStep()

        result = step._extractor.is_english_summary("")
        self.assertFalse(result)


class TestTranslateSummaryWithMockedOllama(unittest.TestCase):
    """Test translate_summary() with mocked Ollama (US4)."""

    def test_translate_summary_calls_ollama(self):
        """translate_summary() calls Ollama and returns translated text."""
        step = ExtractKnowledgeStep()

        english_summary = "The user discussed Python testing strategies."
        expected_japanese = "ユーザーはPythonのテスト戦略について議論しました。"

        with patch("src.etl.utils.knowledge_extractor.call_ollama") as mock_ollama:
            mock_ollama.return_value = (
                f"## 要約\n{expected_japanese}\n",
                None,
            )

            translated, error = step._extractor.translate_summary(english_summary)

            # Verify Ollama was called
            mock_ollama.assert_called_once()

            # Verify result
            self.assertIsNone(error)
            self.assertEqual(translated, expected_japanese)

    def test_translate_summary_handles_ollama_error(self):
        """translate_summary() handles Ollama error gracefully."""
        step = ExtractKnowledgeStep()

        english_summary = "Test summary"

        with patch("src.etl.utils.knowledge_extractor.call_ollama") as mock_ollama:
            mock_ollama.return_value = (None, "Connection refused")

            translated, error = step._extractor.translate_summary(english_summary)

            # Verify error is returned
            self.assertIsNone(translated)
            self.assertIn("Connection refused", error)

    def test_translate_summary_handles_parse_error(self):
        """translate_summary() handles parse error gracefully."""
        step = ExtractKnowledgeStep()

        english_summary = "Test summary"

        with patch("src.etl.utils.knowledge_extractor.call_ollama") as mock_ollama:
            # Return empty response (triggers parse error)
            mock_ollama.return_value = ("", None)

            translated, error = step._extractor.translate_summary(english_summary)

            # Verify error is returned
            self.assertIsNone(translated)
            self.assertIsNotNone(error)


class TestTranslationErrorFallback(unittest.TestCase):
    """Test translation error behavior - now raises StepError."""

    def test_translation_failure_raises_step_error(self):
        """Translation failure should raise StepError (hard error)."""
        step = ExtractKnowledgeStep()

        english_summary = "The user discussed system architecture."

        mock_document = KnowledgeDocument(
            title="Test Title",
            summary=english_summary,
            created="2026-01-19",
            source_provider="claude",
            source_conversation="test-uuid",
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

        conversation_data = {
            "uuid": "test-uuid",
            "name": "Test Conversation",
            "created_at": "2026-01-19T10:00:00Z",
            "summary": english_summary,
            "chat_messages": [
                {"sender": "human", "text": "Hello"},
                {"sender": "assistant", "text": "Hi there!"},
                {"sender": "human", "text": "Test"},
                {"sender": "assistant", "text": "Response"},
            ],
        }

        item = ProcessingItem(
            item_id="test-uuid",
            source_path=Path("/test/conversation.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        with patch.object(step, "_extractor", create=True):
            step._extractor = MagicMock()
            step._extractor.is_english_summary.return_value = True
            step._extractor.should_chunk.return_value = False
            # Translation fails
            step._extractor.translate_summary.return_value = (None, "Ollama error")
            step._extractor.extract.return_value = mock_result

            # Translation failure now raises StepError
            with self.assertRaises(StepError) as context:
                step.process(item)

            # Error message should contain the Ollama error
            self.assertIn("Ollama error", str(context.exception))

    def test_successful_translation_sets_metadata(self):
        """Successful translation sets summary_translated and original_summary metadata."""
        step = ExtractKnowledgeStep()

        english_summary = "The user asked about Python."
        japanese_summary = "ユーザーはPythonについて質問しました。"

        mock_document = KnowledgeDocument(
            title="Test Title",
            summary=japanese_summary,  # Translated
            created="2026-01-19",
            source_provider="claude",
            source_conversation="test-uuid",
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

        conversation_data = {
            "uuid": "test-uuid",
            "name": "Test Conversation",
            "created_at": "2026-01-19T10:00:00Z",
            "summary": english_summary,
            "chat_messages": [
                {"sender": "human", "text": "Hello"},
                {"sender": "assistant", "text": "Hi"},
                {"sender": "human", "text": "Test"},
                {"sender": "assistant", "text": "Response"},
            ],
        }

        item = ProcessingItem(
            item_id="test-uuid",
            source_path=Path("/test/conversation.json"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={
                "source_type": "conversation",
                "source_provider": "claude",
            },
            content=json.dumps(conversation_data),
        )

        with patch.object(step, "_extractor", create=True):
            step._extractor = MagicMock()
            step._extractor.is_english_summary.return_value = True
            step._extractor.should_chunk.return_value = False
            # Translation succeeds
            step._extractor.translate_summary.return_value = (japanese_summary, None)
            step._extractor.extract.return_value = mock_result

            result = step.process(item)

            # Verify translation metadata
            self.assertTrue(result.metadata.get("summary_translated"))
            self.assertEqual(result.metadata.get("original_summary"), english_summary)


class TestTooLargeFrontmatterAddition(unittest.TestCase):
    """Test too_large frontmatter addition (Phase 6).

    T060: Tests that when --chunk is NOT specified and files exceed threshold,
    too_large: true is added to frontmatter.
    """

    def test_too_large_frontmatter_added_to_skipped_files(self):
        """T060: Verify too_large: true is added to frontmatter for threshold-exceeding files.

        When --chunk is NOT specified (default) and conversation exceeds 25000 chars:
        - LLM processing should be skipped
        - Frontmatter should contain too_large: true
        - File should still be written to output
        - Status should be SKIPPED in metadata
        """
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            # Create a large conversation item
            large_content = "X" * 30000  # Exceeds 25000 char threshold
            large_message = json.dumps(
                {
                    "uuid": "large-conv-uuid",
                    "name": "Large Conversation",
                    "created_at": "2024-01-20T10:00:00Z",
                    "chat_messages": [
                        {"text": large_content, "sender": "human"},
                        {"text": "Response", "sender": "assistant"},
                        {"text": "Follow-up", "sender": "human"},
                    ],
                }
            )

            item = ProcessingItem(
                item_id="large-conv-uuid",
                source_path=Path(tmpdir) / "conversation.json",
                current_step="extract",
                status=ItemStatus.PENDING,
                metadata={
                    "source_type": "conversation",
                    "conversation_uuid": "large-conv-uuid",
                    "conversation_name": "Large Conversation",
                    "message_count": 3,
                    "source_provider": "claude",
                    "chunk_enabled": False,  # Default: no --chunk flag
                },
                content=large_message,
            )

            # Process through KnowledgeTransformer
            # ExtractKnowledgeStep should detect threshold and skip LLM
            step = ExtractKnowledgeStep()
            result = step.process(item)

            # Verify: LLM processing was skipped
            self.assertFalse(
                result.metadata.get("knowledge_extracted", False),
                "LLM processing should be skipped for large files without --chunk",
            )

            # Verify: too_large flag is set in metadata
            self.assertTrue(
                result.metadata.get("too_large", False),
                "too_large should be set for threshold-exceeding files",
            )

            # Verify: Status should indicate skip
            # (Actual status handling may vary - verify metadata at minimum)
            self.assertIn(
                "too_large",
                result.metadata,
                "Metadata should contain too_large indicator",
            )

    def test_too_large_frontmatter_not_added_when_chunk_enabled(self):
        """Verify too_large is not added when --chunk is enabled.

        When --chunk is specified and conversation exceeds 25000 chars:
        - Conversation should be chunked
        - All chunks should be LLM processed
        - No too_large frontmatter should appear
        """
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            # Create a large conversation chunk item (chunked by Extractor)
            large_content = "Y" * 30000
            chunk_message = json.dumps(
                {
                    "uuid": "chunked-conv-uuid",
                    "name": "Chunked Conversation (1/2)",
                    "created_at": "2024-01-20T10:00:00Z",
                    "chat_messages": [
                        {"text": large_content, "sender": "human"},
                        {"text": "Response", "sender": "assistant"},
                    ],
                }
            )

            item = ProcessingItem(
                item_id="chunked-conv-uuid-0",
                source_path=Path(tmpdir) / "conversation.json",
                current_step="extract",
                status=ItemStatus.PENDING,
                metadata={
                    "source_type": "conversation",
                    "conversation_uuid": "chunked-conv-uuid",
                    "conversation_name": "Chunked Conversation",
                    "message_count": 2,
                    "source_provider": "claude",
                    "is_chunked": True,
                    "chunk_index": 0,
                    "total_chunks": 2,
                    "parent_item_id": "chunked-conv-uuid",
                    "chunk_enabled": True,  # --chunk flag was passed
                },
                content=chunk_message,
            )

            # Process through KnowledgeTransformer
            # With chunk_enabled=True, LLM should process even large chunks
            step = ExtractKnowledgeStep()

            # Mock the extractor to simulate successful extraction
            with patch.object(step, "_extractor", create=True):
                from src.etl.utils.knowledge_extractor import (
                    ExtractionResult,
                    KnowledgeDocument,
                )

                mock_doc = KnowledgeDocument(
                    title="Chunked Conversation (1/2)",
                    summary="Test summary",
                    created="2024-01-20",
                    source_provider="claude",
                    source_conversation="chunked-conv-uuid",
                    summary_content="Content",
                    code_snippets=[],
                    references=[],
                    item_id="",
                    normalized=False,
                )
                step._extractor = MagicMock()
                step._extractor.extract.return_value = ExtractionResult(
                    success=True, document=mock_doc, raw_response='{"summary": "Test"}'
                )
                step._extractor.should_chunk.return_value = False
                step._extractor.is_english_summary.return_value = False

                result = step.process(item)

                # Verify: LLM extraction was performed (not skipped)
                self.assertTrue(
                    result.metadata.get("knowledge_extracted", False),
                    "With --chunk enabled, LLM should process chunked items",
                )

                # Verify: too_large should NOT be set
                self.assertFalse(
                    result.metadata.get("too_large", False),
                    "too_large should NOT be set when --chunk is enabled",
                )

    def test_too_large_frontmatter_not_added_for_small_files(self):
        """Verify too_large is not added for files below threshold.

        When conversation is below 25000 chars (regardless of --chunk):
        - LLM processing should proceed normally
        - No too_large frontmatter should be added
        """
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            # Create a small conversation item
            small_message = json.dumps(
                {
                    "uuid": "small-conv-uuid",
                    "name": "Small Conversation",
                    "created_at": "2024-01-20T10:00:00Z",
                    "chat_messages": [
                        {"text": "Hello", "sender": "human"},
                        {"text": "Hi there!", "sender": "assistant"},
                        {"text": "How are you?", "sender": "human"},
                    ],
                }
            )

            item = ProcessingItem(
                item_id="small-conv-uuid",
                source_path=Path(tmpdir) / "conversation.json",
                current_step="extract",
                status=ItemStatus.PENDING,
                metadata={
                    "source_type": "conversation",
                    "conversation_uuid": "small-conv-uuid",
                    "conversation_name": "Small Conversation",
                    "message_count": 3,
                    "source_provider": "claude",
                    "chunk_enabled": False,  # Default: no --chunk flag
                },
                content=small_message,
            )

            # Process through KnowledgeTransformer
            step = ExtractKnowledgeStep()

            # Mock the extractor to simulate successful extraction
            with patch.object(step, "_extractor", create=True):
                from src.etl.utils.knowledge_extractor import (
                    ExtractionResult,
                    KnowledgeDocument,
                )

                mock_doc = KnowledgeDocument(
                    title="Small Conversation",
                    summary="Test summary",
                    created="2024-01-20",
                    source_provider="claude",
                    source_conversation="small-conv-uuid",
                    summary_content="Content",
                    code_snippets=[],
                    references=[],
                    item_id="",
                    normalized=False,
                )
                step._extractor = MagicMock()
                step._extractor.extract.return_value = ExtractionResult(
                    success=True, document=mock_doc, raw_response='{"summary": "Test"}'
                )
                step._extractor.should_chunk.return_value = False
                step._extractor.is_english_summary.return_value = False

                result = step.process(item)

                # Verify: LLM extraction was performed
                self.assertTrue(
                    result.metadata.get("knowledge_extracted", False),
                    "Small files should be LLM processed normally",
                )

                # Verify: too_large should NOT be set
                self.assertFalse(
                    result.metadata.get("too_large", False),
                    "too_large should NOT be set for small files",
                )


if __name__ == "__main__":
    unittest.main()
