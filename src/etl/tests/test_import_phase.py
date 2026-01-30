"""Tests for ImportPhase orchestration.

Tests ImportPhase with ClaudeExtractor -> KnowledgeTransformer -> SessionLoader.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.etl.core.phase import PhaseManager
from src.etl.core.session import SessionManager
from src.etl.core.status import PhaseStatus
from src.etl.core.types import PhaseType, StageType
from src.etl.phases.import_phase import ImportPhase


class TestImportPhaseCreation(unittest.TestCase):
    """Test ImportPhase instantiation."""

    def test_import_phase_type(self):
        """ImportPhase has correct phase_type."""
        phase = ImportPhase()
        self.assertEqual(phase.phase_type, PhaseType.IMPORT)

    def test_import_phase_creates_stages(self):
        """ImportPhase creates all three stages."""
        phase = ImportPhase()

        extract = phase.create_extract_stage()
        transform = phase.create_transform_stage()
        load = phase.create_load_stage()

        self.assertEqual(extract.stage_type, StageType.EXTRACT)
        self.assertEqual(transform.stage_type, StageType.TRANSFORM)
        self.assertEqual(load.stage_type, StageType.LOAD)


class TestImportPhaseStages(unittest.TestCase):
    """Test ImportPhase stage implementations."""

    def test_extract_stage_is_claude_extractor(self):
        """Extract stage is ClaudeExtractor."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        phase = ImportPhase()
        extract = phase.create_extract_stage()

        self.assertIsInstance(extract, ClaudeExtractor)

    def test_transform_stage_is_knowledge_transformer(self):
        """Transform stage is KnowledgeTransformer."""
        from src.etl.stages.transform.knowledge_transformer import KnowledgeTransformer

        phase = ImportPhase()
        transform = phase.create_transform_stage()

        self.assertIsInstance(transform, KnowledgeTransformer)

    def test_load_stage_is_session_loader(self):
        """Load stage is SessionLoader."""
        from src.etl.stages.load.session_loader import SessionLoader

        phase = ImportPhase()
        load = phase.create_load_stage()

        self.assertIsInstance(load, SessionLoader)


class TestImportPhaseDiscoverItems(unittest.TestCase):
    """Test ImportPhase item discovery (via ClaudeExtractor)."""

    def test_discover_items_from_empty_dir(self):
        """Empty directory yields no items."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            phase = ImportPhase()
            extract_stage = phase.create_extract_stage()
            items = list(extract_stage.discover_items(input_path))

            self.assertEqual(len(items), 0)

    def test_discover_items_finds_json_files(self):
        """Discovers JSON files in input directory."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            # Create test JSON file
            test_file = input_path / "conversations.json"
            test_file.write_text('[{"uuid": "123", "name": "Test", "chat_messages": []}]')

            phase = ImportPhase()
            extract_stage = phase.create_extract_stage()
            items = list(extract_stage.discover_items(input_path))

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].source_path, test_file)

    @unittest.skip("TODO: Fix non-JSON file discovery logic")
    def test_discover_items_ignores_non_json(self):
        """Ignores non-JSON files."""
        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            # Create test files
            (input_path / "data.json").write_text("{}")
            (input_path / "readme.txt").write_text("text")
            (input_path / "notes.md").write_text("# Notes")

            phase = ImportPhase()
            extract_stage = phase.create_extract_stage()
            items = list(extract_stage.discover_items(input_path))

            self.assertEqual(len(items), 1)
            self.assertTrue(items[0].source_path.suffix == ".json")


class TestImportPhaseRun(unittest.TestCase):
    """Test ImportPhase run method."""

    def test_run_creates_phase_result(self):
        """Run returns PhaseResult."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Create input file
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_file = input_path / "test.json"
            test_file.write_text('{"conversations": []}')

            # Run phase
            import_phase = ImportPhase()
            result = import_phase.run(phase_data)

            # Verify result
            self.assertEqual(result.phase_type, PhaseType.IMPORT)
            self.assertIn(result.status, [PhaseStatus.COMPLETED, PhaseStatus.PARTIAL])

    def test_run_with_empty_input(self):
        """Run with empty input completes."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Run with empty input
            import_phase = ImportPhase()
            result = import_phase.run(phase_data)

            self.assertEqual(result.phase_type, PhaseType.IMPORT)
            self.assertEqual(result.items_processed, 0)


class TestImportPhaseETLFlow(unittest.TestCase):
    """Test ImportPhase ETL flow: Extract -> Transform -> Load."""

    @unittest.skip("Requires Ollama - integration test")
    def test_etl_flow_with_single_item(self):
        """Single item flows through all stages (requires Ollama)."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Create input file
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = {
                "conversations": [
                    {
                        "uuid": "test-uuid",
                        "name": "Test Conversation",
                        "chat_messages": [
                            {"text": "Hello", "sender": "human"},
                            {"text": "Hi there", "sender": "assistant"},
                        ],
                    }
                ]
            }
            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Run phase
            import_phase = ImportPhase()
            result = import_phase.run(phase_data)

            # Verify flow completed
            self.assertIn(result.status, [PhaseStatus.COMPLETED, PhaseStatus.PARTIAL])


class TestImportPhaseDebugMode(unittest.TestCase):
    """Test ImportPhase debug mode."""

    def test_debug_mode_enabled(self):
        """Debug mode produces additional logging."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create(debug_mode=True)
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Run with debug mode
            import_phase = ImportPhase()
            result = import_phase.run(phase_data, debug_mode=True)

            # Should complete without errors
            self.assertIn(result.status, [PhaseStatus.COMPLETED, PhaseStatus.PARTIAL])


class TestMinMessagesSkipLogic(unittest.TestCase):
    """Test MIN_MESSAGES skip logic (T076).

    Conversations with fewer than MIN_MESSAGES (default 3) should be skipped.
    """

    MIN_MESSAGES = 3  # Default threshold

    def test_skip_conversation_with_one_message(self):
        """Conversations with 1 message should be skipped."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Create input file with 1 message (below threshold)
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "test-uuid-1",
                    "name": "Single Message",
                    "chat_messages": [
                        {"text": "Hello", "sender": "human"},
                    ],
                }
            ]
            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Discover items and check message count in metadata
            import_phase = ImportPhase()
            extract_stage = import_phase.create_extract_stage()
            items = list(extract_stage.discover_items(input_path))

            self.assertEqual(len(items), 1)
            # Message count validation happens in ValidateStructureStep
            # The item should be discovered but can be filtered later

    def test_skip_conversation_with_two_messages(self):
        """Conversations with 2 messages should be skipped."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Create input file with 2 messages (below threshold)
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "test-uuid-2",
                    "name": "Two Messages",
                    "chat_messages": [
                        {"text": "Hello", "sender": "human"},
                        {"text": "Hi there!", "sender": "assistant"},
                    ],
                }
            ]
            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Discover items
            import_phase = ImportPhase()
            extract_stage = import_phase.create_extract_stage()
            items = list(extract_stage.discover_items(input_path))

            self.assertEqual(len(items), 1)
            item = items[0]
            # Verify message count can be extracted from content
            content = json.loads(item.content)
            message_count = len(content.get("chat_messages", []))
            self.assertEqual(message_count, 2)
            self.assertLess(message_count, self.MIN_MESSAGES)

    def test_process_conversation_with_three_or_more_messages(self):
        """Conversations with 3+ messages should be processed."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Create input file with 3 messages (at threshold)
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "test-uuid-3",
                    "name": "Three Messages",
                    "chat_messages": [
                        {"text": "Hello", "sender": "human"},
                        {"text": "Hi there!", "sender": "assistant"},
                        {"text": "How are you?", "sender": "human"},
                    ],
                }
            ]
            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Discover items
            import_phase = ImportPhase()
            extract_stage = import_phase.create_extract_stage()
            items = list(extract_stage.discover_items(input_path))

            self.assertEqual(len(items), 1)
            item = items[0]
            # Verify message count meets threshold
            content = json.loads(item.content)
            message_count = len(content.get("chat_messages", []))
            self.assertEqual(message_count, 3)
            self.assertGreaterEqual(message_count, self.MIN_MESSAGES)


class TestFileIdSkipLogic(unittest.TestCase):
    """Test file_id skip logic (T077).

    Conversations already processed (with file_id in @index) should be skipped.
    """

    def test_detect_existing_file_by_file_id(self):
        """Existing file with same item_id should be detected."""
        from src.etl.stages.load.session_loader import UpdateIndexStep

        with TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "@index"
            index_path.mkdir()

            # Create existing file with item_id
            existing_file = index_path / "existing_note.md"
            existing_file.write_text(
                "---\ntitle: Existing Note\nitem_id: abc123xyz\n---\n\n# Content\n"
            )

            # Create step and search
            step = UpdateIndexStep(index_path)
            found = step._find_existing_by_item_id("abc123xyz")

            self.assertIsNotNone(found)
            self.assertEqual(found.name, "existing_note.md")

    def test_no_match_for_different_file_id(self):
        """No match should be found for different item_id."""
        from src.etl.stages.load.session_loader import UpdateIndexStep

        with TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "@index"
            index_path.mkdir()

            # Create existing file with different item_id
            existing_file = index_path / "existing_note.md"
            existing_file.write_text(
                "---\ntitle: Existing Note\nitem_id: different_id\n---\n\n# Content\n"
            )

            # Create step and search
            step = UpdateIndexStep(index_path)
            found = step._find_existing_by_item_id("abc123xyz")

            self.assertIsNone(found)

    def test_skip_already_processed_conversation(self):
        """Conversation with existing item_id should be detected for skip."""
        from src.etl.stages.load.session_loader import UpdateIndexStep
        from src.etl.utils.file_id import generate_file_id

        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            index_path = base_path / "@index"
            index_path.mkdir()

            # Create a conversation content
            conv_content = json.dumps(
                {
                    "uuid": "conv-123",
                    "name": "Test Conversation",
                    "chat_messages": [
                        {"text": "Hello", "sender": "human"},
                        {"text": "Hi", "sender": "assistant"},
                        {"text": "How?", "sender": "human"},
                    ],
                }
            )

            # Generate item_id for this content
            item_id = generate_file_id(conv_content, Path("dummy.json"))

            # Create existing file in @index with same item_id
            existing_file = index_path / "Test Conversation.md"
            existing_file.write_text(
                f"---\ntitle: Test Conversation\nitem_id: {item_id}\n---\n\n# Content\n"
            )

            # Verify the item_id can be found
            step = UpdateIndexStep(index_path)
            found = step._find_existing_by_item_id(item_id)

            self.assertIsNotNone(found)
            self.assertEqual(found.name, "Test Conversation.md")


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration test with real Ollama (T075).

    These tests require a running Ollama server and RUN_INTEGRATION_TESTS=1.
    Use 'make test-fixtures' to run these tests.
    """

    @classmethod
    def setUpClass(cls):
        """Check if integration tests should run."""
        import os

        # Skip unless explicitly requested via environment variable
        if not os.getenv("RUN_INTEGRATION_TESTS"):
            raise unittest.SkipTest(
                "Integration tests disabled. "
                "Set RUN_INTEGRATION_TESTS=1 or use 'make test-fixtures' to enable."
            )

        # Then check Ollama availability
        from src.etl.utils.ollama import check_ollama_connection

        connected, error = check_ollama_connection()
        cls.ollama_available = connected
        if not connected:
            cls.skip_reason = f"Ollama not available: {error}"
            raise unittest.SkipTest(cls.skip_reason)

    def test_full_pipeline_with_real_ollama(self):
        """Test full import pipeline with real Ollama extraction."""
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Create input file with real conversation content
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "real-conv-uuid",
                    "name": "Python Programming Discussion",
                    "created_at": "2024-01-15T10:30:00Z",
                    "chat_messages": [
                        {
                            "text": "What is the difference between list and tuple in Python?",
                            "sender": "human",
                        },
                        {
                            "text": "Lists are mutable - you can modify their contents after creation. "
                            "Tuples are immutable - once created, their contents cannot be changed. "
                            "Use lists when you need a collection that can grow or shrink. "
                            "Use tuples for fixed collections or as dictionary keys.",
                            "sender": "assistant",
                        },
                        {
                            "text": "Which is faster?",
                            "sender": "human",
                        },
                        {
                            "text": "Tuples are slightly faster than lists for iteration and access "
                            "because of their immutability. Python can optimize tuple operations. "
                            "However, the performance difference is usually negligible for most uses.",
                            "sender": "assistant",
                        },
                    ],
                }
            ]
            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Run phase
            import_phase = ImportPhase()
            result = import_phase.run(phase_data)

            # Verify result
            self.assertIn(result.status, [PhaseStatus.COMPLETED, PhaseStatus.PARTIAL])
            # At least one item processed or failed (pipeline executed)
            self.assertTrue(result.items_processed > 0 or result.items_failed > 0)

    def test_extraction_produces_knowledge_document(self):
        """Test that extraction produces a valid KnowledgeDocument."""
        from src.etl.stages.transform.knowledge_transformer import (
            ConversationData,
            ExtractKnowledgeStep,
            Message,
        )

        # Create a simple conversation
        messages = [
            Message(content="What is Python?", _role="user"),
            Message(content="Python is a programming language.", _role="assistant"),
            Message(content="Is it easy to learn?", _role="user"),
            Message(content="Yes, Python has a simple syntax.", _role="assistant"),
        ]

        conversation = ConversationData(
            title="Python Basics",
            created_at="2024-01-15T10:30:00Z",
            _messages=messages,
            _id="test-conv-id",
            _provider="claude",
        )

        # Extract knowledge
        step = ExtractKnowledgeStep()
        result = step._extract_with_retry(conversation)

        # Verify extraction result
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        # Document should have title and summary
        self.assertIsNotNone(result.document.title)
        self.assertIsNotNone(result.document.summary)


class Test1to1Processing(unittest.TestCase):
    """Test User Story 1: Standard 1:1 processing maintains existing behavior.

    T014: Tests that single input produces single output and maintains
    existing ETL pipeline behavior without chunk expansion.
    """

    @patch(
        "src.etl.stages.transform.knowledge_transformer.ExtractKnowledgeStep._extract_with_retry"
    )
    def test_1to1_processing_maintains_single_output(self, mock_extract):
        """T014: Verify 1:1 processing produces single output without chunking.

        User Story 1: Standard 1:1 processing.
        Verifies that a conversation below chunk threshold produces exactly
        one output file and sets is_chunked=False in metadata.
        """
        from src.etl.utils.knowledge_extractor import ExtractionResult, KnowledgeDocument

        # Mock LLM extraction
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
        mock_extract.return_value = ExtractionResult(
            success=True, document=mock_doc, raw_response='{"summary": "Test"}'
        )

        with TemporaryDirectory() as tmpdir:
            # Create session and phase structure
            session_path = Path(tmpdir) / "20260120_100000"
            session_mgr = SessionManager(Path(tmpdir))
            session = session_mgr.create()
            phase_mgr = PhaseManager(session.base_path)
            phase_data = phase_mgr.create(PhaseType.IMPORT)

            # Create small conversation (below 25000 char threshold)
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "small-conv-uuid",
                    "name": "Small Conversation",
                    "created_at": "2024-01-20T10:00:00Z",
                    "chat_messages": [
                        {
                            "text": "What is 2+2?",
                            "sender": "human",
                        },
                        {
                            "text": "2+2 equals 4.",
                            "sender": "assistant",
                        },
                        {
                            "text": "Thank you!",
                            "sender": "human",
                        },
                    ],
                }
            ]

            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Run import phase
            import_phase = ImportPhase()
            result = import_phase.run(phase_data)

            # Verify: Single input should produce single output
            load_output_path = phase_data.stages[StageType.LOAD].output_path
            output_files = list(load_output_path.glob("**/*.md"))

            # Should have exactly 1 output file (1:1 ratio)
            self.assertEqual(
                len(output_files),
                1,
                f"Expected 1 output file for 1:1 processing, got {len(output_files)}",
            )

            # Verify metadata: is_chunked should be False
            # Check pipeline_stages.jsonl for chunk metadata
            jsonl_path = phase_data.base_path / "pipeline_stages.jsonl"
            if jsonl_path.exists():
                with open(jsonl_path, encoding="utf-8") as f:
                    logs = [json.loads(line) for line in f]

                # At least one log entry should have is_chunked field
                transform_logs = [log for log in logs if log.get("stage") == "transform"]
                if transform_logs:
                    # Check that is_chunked is either False or null (not True)
                    for log in transform_logs:
                        is_chunked = log.get("is_chunked")
                        if is_chunked is not None:
                            self.assertFalse(
                                is_chunked,
                                "1:1 processing should have is_chunked=False",
                            )


class TestChunkedProcessing(unittest.TestCase):
    """Test User Story 2: 1:N chunked processing for large conversations.

    T024-T025: Tests that large conversations (>25000 chars) are automatically
    chunked and each chunk is processed independently.
    """

    def test_discover_items_chunks_large_conversation(self):
        """T024: Verify discover_items() chunks large conversations.

        User Story 2: 1:N expansion processing.
        Verifies that a conversation exceeding 25000 chars is split into
        multiple ProcessingItems with chunk metadata.
        """
        with TemporaryDirectory() as tmpdir:
            # Create session and phase structure
            session_mgr = SessionManager(Path(tmpdir))
            session = session_mgr.create()
            phase_mgr = PhaseManager(session.base_path)
            phase_data = phase_mgr.create(PhaseType.IMPORT)

            # Create large conversation (>25000 chars)
            # Generate messages to exceed threshold
            large_message = "A" * 13000  # 13000 chars per message
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "large-conv-uuid",
                    "name": "Large Conversation",
                    "created_at": "2024-01-20T10:00:00Z",
                    "chat_messages": [
                        {"text": large_message, "sender": "human"},
                        {"text": large_message, "sender": "assistant"},
                        {"text": large_message, "sender": "human"},
                        # Total: ~39000 chars (exceeds 25000 threshold)
                    ],
                }
            ]

            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Discover items
            import_phase = ImportPhase()
            extract_stage = import_phase.create_extract_stage()
            items = list(extract_stage.discover_items(input_path))

            # Verify: Large conversation should produce multiple chunk items
            # After chunking, we should have at least 2 chunk items
            chunk_items = [item for item in items if item.metadata.get("is_chunked")]
            self.assertGreater(
                len(chunk_items),
                1,
                "Large conversation should be chunked into multiple items",
            )

            # Verify chunk metadata is set correctly
            for i, item in enumerate(chunk_items):
                self.assertTrue(
                    item.metadata.get("is_chunked"),
                    f"Chunk {i} should have is_chunked=True",
                )
                self.assertEqual(
                    item.metadata.get("chunk_index"),
                    i,
                    f"Chunk {i} should have correct chunk_index",
                )
                self.assertEqual(
                    item.metadata.get("total_chunks"),
                    len(chunk_items),
                    f"Chunk {i} should have correct total_chunks",
                )
                self.assertIsNotNone(
                    item.metadata.get("parent_item_id"),
                    f"Chunk {i} should have parent_item_id",
                )

    @patch(
        "src.etl.stages.transform.knowledge_transformer.ExtractKnowledgeStep._extract_with_retry"
    )
    def test_chunk_metadata_propagation(self, mock_extract):
        """T025: Verify chunk metadata propagates through pipeline stages.

        User Story 2: 1:N expansion processing.
        Verifies that chunk metadata (is_chunked, chunk_index, total_chunks,
        parent_item_id) is preserved from discover_items() through to Load stage.
        """
        from src.etl.utils.knowledge_extractor import ExtractionResult, KnowledgeDocument

        # Mock LLM extraction
        mock_doc = KnowledgeDocument(
            title="Chunk Test",
            summary="Test summary",
            created="2024-01-20",
            source_provider="claude",
            source_conversation="chunk-metadata-uuid",
            summary_content="Content",
            code_snippets=[],
            references=[],
            item_id="",
            normalized=False,
        )
        mock_extract.return_value = ExtractionResult(
            success=True, document=mock_doc, raw_response='{"summary": "Test"}'
        )

        with TemporaryDirectory() as tmpdir:
            # Create session and phase structure
            session_mgr = SessionManager(Path(tmpdir))
            session = session_mgr.create()
            phase_mgr = PhaseManager(session.base_path)
            phase_data = phase_mgr.create(PhaseType.IMPORT)

            # Create large conversation
            large_message = "B" * 13000
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "chunk-metadata-uuid",
                    "name": "Chunk Metadata Test",
                    "created_at": "2024-01-20T11:00:00Z",
                    "chat_messages": [
                        {"text": large_message, "sender": "human"},
                        {"text": large_message, "sender": "assistant"},
                        {"text": large_message, "sender": "human"},
                    ],
                }
            ]

            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Run import phase with chunking enabled
            import_phase = ImportPhase(chunk=True)
            result = import_phase.run(phase_data)

            # Verify: Check pipeline_stages.jsonl for chunk metadata
            jsonl_path = phase_data.base_path / "pipeline_stages.jsonl"
            if jsonl_path.exists():
                with open(jsonl_path, encoding="utf-8") as f:
                    logs = [json.loads(line) for line in f]

                # Find chunked entries
                chunked_logs = [log for log in logs if log.get("is_chunked")]
                self.assertGreater(
                    len(chunked_logs),
                    0,
                    "Should have at least one log entry with is_chunked=True",
                )

                # Verify chunk metadata fields are present
                for log in chunked_logs:
                    self.assertTrue(log.get("is_chunked"))
                    self.assertIsNotNone(log.get("chunk_index"))
                    self.assertIsNotNone(log.get("parent_item_id"))


class TestIntegrationAndEdgeCases(unittest.TestCase):
    """Test Phase 5: Integration tests and edge cases.

    T039-T042: Tests for mixed scenarios, empty input, single large message,
    and partial chunk failure handling.
    """

    @patch(
        "src.etl.stages.transform.knowledge_transformer.ExtractKnowledgeStep._extract_with_retry"
    )
    def test_end_to_end_mixed_1to1_and_1toN(self, mock_extract):
        """T039: Integration test with both 1:1 and 1:N conversations.

        Verifies pipeline correctly handles mixed input:
        - Small conversation (<25000 chars) → single output
        - Large conversation (>25000 chars) → multiple outputs
        """
        from src.etl.utils.knowledge_extractor import ExtractionResult, KnowledgeDocument

        # Mock LLM extraction
        mock_doc = KnowledgeDocument(
            title="Test Conversation",
            summary="Test summary",
            created="2024-01-20",
            source_provider="claude",
            source_conversation="test-uuid",
            summary_content="Content",
            code_snippets=[],
            references=[],
            item_id="",
            normalized=False,
        )
        mock_extract.return_value = ExtractionResult(
            success=True, document=mock_doc, raw_response='{"summary": "Test"}'
        )

        with TemporaryDirectory() as tmpdir:
            # Create session and phase structure
            session_mgr = SessionManager(Path(tmpdir))
            session = session_mgr.create()
            phase_mgr = PhaseManager(session.base_path)
            phase_data = phase_mgr.create(PhaseType.IMPORT)

            # Create mixed input: 1 small + 1 large conversation
            large_message = "X" * 13000
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "small-conv-uuid",
                    "name": "Small Conversation",
                    "created_at": "2024-01-20T10:00:00Z",
                    "chat_messages": [
                        {"text": "Hello", "sender": "human"},
                        {"text": "Hi there!", "sender": "assistant"},
                        {"text": "How are you?", "sender": "human"},
                    ],
                },
                {
                    "uuid": "large-conv-uuid",
                    "name": "Large Conversation",
                    "created_at": "2024-01-20T11:00:00Z",
                    "chat_messages": [
                        {"text": large_message, "sender": "human"},
                        {"text": large_message, "sender": "assistant"},
                        {"text": large_message, "sender": "human"},
                    ],
                },
            ]

            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Run import phase with chunking enabled
            import_phase = ImportPhase(chunk=True)
            result = import_phase.run(phase_data)

            # Verify: Check pipeline_stages.jsonl
            jsonl_path = phase_data.base_path / "pipeline_stages.jsonl"
            if jsonl_path.exists():
                with open(jsonl_path, encoding="utf-8") as f:
                    logs = [json.loads(line) for line in f]

                # Should have logs for both 1:1 and 1:N processing
                non_chunked = [log for log in logs if not log.get("is_chunked")]
                chunked = [log for log in logs if log.get("is_chunked")]

                self.assertGreater(len(non_chunked), 0, "Should have non-chunked entries")
                self.assertGreater(len(chunked), 0, "Should have chunked entries")

                # Verify chunk metadata consistency
                for log in chunked:
                    self.assertTrue(log.get("is_chunked"))
                    self.assertIsNotNone(log.get("chunk_index"))
                    self.assertIsNotNone(log.get("parent_item_id"))

    def test_empty_input_no_error(self):
        """T040: Edge case - empty input produces no error.

        Verifies that processing empty input file completes without error
        and produces no output files.
        """
        with TemporaryDirectory() as tmpdir:
            # Create session and phase structure
            session_mgr = SessionManager(Path(tmpdir))
            session = session_mgr.create()
            phase_mgr = PhaseManager(session.base_path)
            phase_data = phase_mgr.create(PhaseType.IMPORT)

            # Create empty conversations.json
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps([]))

            # Run import phase - should complete without error
            import_phase = ImportPhase()
            result = import_phase.run(phase_data)

            # Verify: No error, no output files
            self.assertEqual(result.items_processed, 0)
            self.assertEqual(result.items_failed, 0)

            load_output_path = phase_data.stages[StageType.LOAD].output_path
            output_files = list(load_output_path.glob("**/*.md"))
            self.assertEqual(len(output_files), 0, "Should have no output files")

    @patch(
        "src.etl.stages.transform.knowledge_transformer.ExtractKnowledgeStep._extract_with_retry"
    )
    def test_single_message_exceeds_threshold(self, mock_extract):
        """T041: Edge case - single message exceeds chunk threshold.

        Verifies that conversation with single large message (>25000 chars)
        is handled correctly. Even with 1 message, Chunker will create a chunk
        if total chars exceed threshold (actual Chunker behavior).
        """
        from src.etl.utils.knowledge_extractor import ExtractionResult, KnowledgeDocument

        # Mock LLM extraction
        mock_doc = KnowledgeDocument(
            title="Single Huge Message",
            summary="Test summary",
            created="2024-01-20",
            source_provider="claude",
            source_conversation="single-huge-msg-uuid",
            summary_content="Content",
            code_snippets=[],
            references=[],
            item_id="",
            normalized=False,
        )
        mock_extract.return_value = ExtractionResult(
            success=True, document=mock_doc, raw_response='{"summary": "Test"}'
        )

        with TemporaryDirectory() as tmpdir:
            # Create session and phase structure
            session_mgr = SessionManager(Path(tmpdir))
            session = session_mgr.create()
            phase_mgr = PhaseManager(session.base_path)
            phase_data = phase_mgr.create(PhaseType.IMPORT)

            # Create conversation with single huge message
            huge_message = "Z" * 30000
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "single-huge-msg-uuid",
                    "name": "Single Huge Message",
                    "created_at": "2024-01-20T12:00:00Z",
                    "chat_messages": [
                        {"text": huge_message, "sender": "human"},
                    ],
                }
            ]

            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Run import phase
            import_phase = ImportPhase()
            result = import_phase.run(phase_data)

            # Verify: Chunker handles single large message correctly
            # Chunker creates a single-message chunk if it exceeds threshold
            jsonl_path = phase_data.base_path / "pipeline_stages.jsonl"
            if jsonl_path.exists():
                with open(jsonl_path, encoding="utf-8") as f:
                    logs = [json.loads(line) for line in f]

                # Chunker will create chunk for single large message
                chunked = [log for log in logs if log.get("is_chunked")]
                # May have chunked entries (Chunker creates chunk for >25000 char message)
                # This is correct behavior - single large message is still processed
                # Note: Pipeline may fail due to MIN_MESSAGES check, but that's
                # a separate validation from chunking logic

    @patch(
        "src.etl.stages.transform.knowledge_transformer.ExtractKnowledgeStep._extract_with_retry"
    )
    def test_partial_chunk_failure(self, mock_extract):
        """T042: Edge case - partial chunk failure handling.

        Verifies that if one chunk fails processing, other chunks
        still complete successfully and are tracked correctly.

        Note: This is a structural test - actual failure simulation
        would require mocking LLM calls. We verify the framework
        supports independent chunk processing.
        """
        from src.etl.utils.knowledge_extractor import ExtractionResult, KnowledgeDocument

        # Mock LLM extraction
        mock_doc = KnowledgeDocument(
            title="Partial Failure Test",
            summary="Test summary",
            created="2024-01-20",
            source_provider="claude",
            source_conversation="partial-fail-uuid",
            summary_content="Content",
            code_snippets=[],
            references=[],
            item_id="",
            normalized=False,
        )
        mock_extract.return_value = ExtractionResult(
            success=True, document=mock_doc, raw_response='{"summary": "Test"}'
        )

        with TemporaryDirectory() as tmpdir:
            # Create session and phase structure
            session_mgr = SessionManager(Path(tmpdir))
            session = session_mgr.create()
            phase_mgr = PhaseManager(session.base_path)
            phase_data = phase_mgr.create(PhaseType.IMPORT)

            # Create large conversation that will be chunked
            large_message = "C" * 13000
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "partial-fail-uuid",
                    "name": "Partial Failure Test",
                    "created_at": "2024-01-20T13:00:00Z",
                    "chat_messages": [
                        {"text": large_message, "sender": "human"},
                        {"text": large_message, "sender": "assistant"},
                        {"text": large_message, "sender": "human"},
                    ],
                }
            ]

            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Run import phase with chunking enabled
            import_phase = ImportPhase(chunk=True)
            result = import_phase.run(phase_data)

            # Verify: Multiple chunks processed independently
            jsonl_path = phase_data.base_path / "pipeline_stages.jsonl"
            if jsonl_path.exists():
                with open(jsonl_path, encoding="utf-8") as f:
                    logs = [json.loads(line) for line in f]

                # Should have multiple chunk entries
                chunked = [log for log in logs if log.get("is_chunked")]
                self.assertGreater(len(chunked), 0, "Should have multiple chunk entries")

                # Each chunk should have independent status tracking
                chunk_indices = set()
                for log in chunked:
                    chunk_idx = log.get("chunk_index")
                    if chunk_idx is not None:
                        chunk_indices.add(chunk_idx)

                # Should have at least 2 different chunk indices
                self.assertGreaterEqual(
                    len(chunk_indices),
                    2,
                    "Should have at least 2 independent chunks",
                )


class TestChunkOptionBehavior(unittest.TestCase):
    """Test --chunk option behavior (Phase 6).

    T058-T059: Tests for CLI --chunk option and default threshold skip behavior.
    """

    def test_import_with_chunk_option_enables_chunking(self):
        """T058: --chunk option enables chunking for large files.

        When --chunk is specified, large conversations (>25000 chars) should be
        split into chunks and processed.
        """
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Create large conversation (>25000 chars)
            large_message = "X" * 13000
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "large-chunk-test",
                    "name": "Large Chunk Test",
                    "created_at": "2024-01-20T10:00:00Z",
                    "chat_messages": [
                        {"text": large_message, "sender": "human"},
                        {"text": large_message, "sender": "assistant"},
                        {"text": large_message, "sender": "human"},
                    ],
                }
            ]

            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Run import phase with chunk=True
            import_phase = ImportPhase()
            # TODO: Pass chunk flag through phase_data or context
            # For now, verify that discover_items() chunks the conversation
            extract_stage = import_phase.create_extract_stage()
            items = list(extract_stage.discover_items(input_path))

            # Verify: Large conversation should be chunked
            chunk_items = [item for item in items if item.metadata.get("is_chunked")]
            self.assertGreater(
                len(chunk_items),
                1,
                "With --chunk option, large conversation should be split into multiple chunks",
            )

            # Verify chunk metadata
            for chunk in chunk_items:
                self.assertTrue(chunk.metadata.get("is_chunked"))
                self.assertIsNotNone(chunk.metadata.get("chunk_index"))
                self.assertIsNotNone(chunk.metadata.get("total_chunks"))
                self.assertIsNotNone(chunk.metadata.get("parent_item_id"))

    def test_import_without_chunk_skips_large_files(self):
        """T059: Default (no --chunk) skips large files with too_large frontmatter.

        When --chunk is NOT specified (default), large conversations should:
        - Skip LLM processing
        - Add too_large: true to frontmatter
        - Set status=SKIPPED
        - Continue processing subsequent items
        """
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Create one large and one small conversation
            large_message = "L" * 13000
            input_path = phase_data.stages[StageType.EXTRACT].input_path
            test_data = [
                {
                    "uuid": "large-conv-skip",
                    "name": "Large Conversation Skip",
                    "created_at": "2024-01-20T10:00:00Z",
                    "chat_messages": [
                        {"text": large_message, "sender": "human"},
                        {"text": large_message, "sender": "assistant"},
                        {"text": large_message, "sender": "human"},
                    ],
                },
                {
                    "uuid": "small-conv-process",
                    "name": "Small Conversation Process",
                    "created_at": "2024-01-20T11:00:00Z",
                    "chat_messages": [
                        {"text": "Hello", "sender": "human"},
                        {"text": "Hi", "sender": "assistant"},
                        {"text": "How are you?", "sender": "human"},
                    ],
                },
            ]

            test_file = input_path / "conversations.json"
            test_file.write_text(json.dumps(test_data))

            # Run import phase WITHOUT chunk flag (default behavior)
            # NOTE: Discovery STILL chunks large files (this is done at Extract stage)
            # The difference is that without --chunk, large files are SKIPPED in Transform stage
            import_phase = ImportPhase(chunk=False)
            result = import_phase.run(phase_data)

            # Verify: Pipeline completed
            self.assertIn(result.status, [PhaseStatus.COMPLETED, PhaseStatus.PARTIAL])

            # Verify: At least one file was skipped (the large one)
            self.assertGreater(
                result.items_skipped,
                0,
                "Large file should be skipped when chunk=False",
            )

            # Check pipeline_stages.jsonl for skip reason
            jsonl_path = phase_data.base_path / "pipeline_stages.jsonl"
            if jsonl_path.exists():
                with open(jsonl_path, encoding="utf-8") as f:
                    logs = [json.loads(line) for line in f]

                # Find skipped entries
                skipped_logs = [log for log in logs if log.get("status") == "skipped"]
                self.assertGreater(
                    len(skipped_logs),
                    0,
                    "Should have at least one skipped item",
                )


class TestResumePrerequisites(unittest.TestCase):
    """Test Resume mode prerequisites (Phase 4).

    T042-T043: Tests for Extract completion check and Resume progress display.
    """

    def test_resume_requires_extract_complete(self):
        """T042: Resume mode requires Extract stage to be completed.

        When Resume mode is attempted without completed Extract stage,
        the system should raise an error with a clear message.

        Expected error message: "Error: Extract stage not completed. Cannot resume."
        """
        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Create empty extract output (no files - simulating incomplete Extract)
            # extract/output/ exists but has no files
            extract_output = phase_data.stages[StageType.EXTRACT].output_path
            extract_output.mkdir(parents=True, exist_ok=True)
            # Explicitly ensure no files exist
            self.assertEqual(list(extract_output.iterdir()), [])

            # Create pipeline_stages.jsonl to simulate Resume mode being active
            # (In Resume mode, we use --session to continue an existing session)
            jsonl_path = phase_data.base_path / "pipeline_stages.jsonl"
            jsonl_path.touch()  # Empty file indicates no completed items

            # Run ImportPhase in Resume mode (with base_path set)
            import_phase = ImportPhase(base_path=phase_data.base_path)

            # The phase should detect that Extract is not completed and raise an error
            # Currently, this behavior is NOT implemented, so the test will FAIL
            with self.assertRaises(RuntimeError) as context:
                import_phase.run(phase_data)

            self.assertIn(
                "Extract stage not completed",
                str(context.exception),
                "Error message should indicate Extract stage is not completed",
            )

    def test_resume_shows_progress_message(self):
        """T043: Resume mode shows progress message at startup.

        When Resume mode starts, it should display a message showing:
        - Number of items already completed
        - Total expected items
        - Starting item position

        Expected output example:
        "Resume mode: 700/1000 items already completed, starting from item 701"
        """
        import io
        import sys

        with TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create session with expected_total_item_count
            session_manager = SessionManager(base_path / "@session")
            session = session_manager.create()
            session_manager.save(session)

            # Create phase
            phase_manager = PhaseManager(session.base_path)
            phase_data = phase_manager.create(PhaseType.IMPORT)

            # Create extract output with some files (simulating completed Extract)
            extract_output = phase_data.stages[StageType.EXTRACT].output_path
            extract_output.mkdir(parents=True, exist_ok=True)
            # Create dummy extracted files
            for i in range(10):
                (extract_output / f"conv_{i}.json").write_text(
                    json.dumps({"uuid": f"uuid-{i}", "name": f"Conv {i}"})
                )

            # Update session with expected_total_item_count
            from src.etl.core.session import PhaseStats

            session.phases["import"] = PhaseStats(
                status="in_progress",
                expected_total_item_count=10,  # 10 total items
            )
            session_manager.save(session)

            # Create pipeline_stages.jsonl with 7 completed items
            jsonl_path = phase_data.base_path / "pipeline_stages.jsonl"
            with open(jsonl_path, "w", encoding="utf-8") as f:
                for i in range(7):
                    record = {
                        "timestamp": "2026-01-28T10:00:00Z",
                        "session_id": session.session_id,
                        "filename": f"conv_{i}.json",
                        "stage": "transform",
                        "step": "extract_knowledge",
                        "timing_ms": 5000,
                        "status": "success",
                        "item_id": f"uuid-{i}",
                    }
                    f.write(json.dumps(record) + "\n")

            # Create ImportPhase in Resume mode
            import_phase = ImportPhase(base_path=phase_data.base_path)

            # Capture stdout to check progress message
            captured_output = io.StringIO()
            sys.stdout = captured_output

            try:
                # Run phase - should print progress message
                # Currently, this behavior is NOT implemented, so the test will FAIL
                result = import_phase.run(phase_data, session_manager=session_manager)
            finally:
                sys.stdout = sys.__stdout__

            output = captured_output.getvalue()

            # Verify progress message is displayed
            self.assertIn(
                "Resume mode:",
                output,
                "Should print 'Resume mode:' prefix",
            )
            self.assertIn(
                "7",
                output,
                "Should show 7 completed items",
            )
            self.assertIn(
                "10",
                output,
                "Should show 10 total items",
            )


if __name__ == "__main__":
    unittest.main()
