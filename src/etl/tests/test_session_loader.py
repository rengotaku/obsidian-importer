"""Tests for SessionLoader stage.

Tests WriteToSessionStep and UpdateIndexStep for the Load stage.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.etl.core.status import ItemStatus
from src.etl.core.types import StageType, PhaseType
from src.etl.core.models import ProcessingItem
from src.etl.core.stage import StageContext, Stage
from src.etl.core.phase import Phase
from src.etl.stages.load.session_loader import (
    WriteToSessionStep,
    UpdateIndexStep,
    SessionLoader,
)


class TestWriteToSessionStep(unittest.TestCase):
    """Test WriteToSessionStep file writing."""

    def test_writes_transformed_content_to_file(self):
        """WriteToSessionStep writes transformed_content to output file."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            output_path.mkdir()

            step = WriteToSessionStep(output_path=output_path)
            item = ProcessingItem(
                item_id="test-123",
                source_path=Path("/test/input.json"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={"source_type": "conversation", "conversation_name": "Test Conv"},
                transformed_content="# Test Content\n\nThis is a test.",
            )

            result = step.process(item)

            # Verify file was written
            expected_path = output_path / "conversations" / "Test Conv.md"
            self.assertTrue(expected_path.exists())
            self.assertEqual(expected_path.read_text(encoding="utf-8"), "# Test Content\n\nThis is a test.")
            self.assertEqual(result.output_path, expected_path)
            self.assertEqual(result.metadata["written_to"], str(expected_path))

    def test_sanitizes_filename(self):
        """WriteToSessionStep sanitizes problematic characters in filename."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            output_path.mkdir()

            step = WriteToSessionStep(output_path=output_path)
            item = ProcessingItem(
                item_id="test-123",
                source_path=Path("/test/input.json"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={"source_type": "conversation", "conversation_name": "Test/Conv:Special*Chars?"},
                content="Test content",
            )

            result = step.process(item)

            # Filename should have special chars replaced with underscore
            self.assertIn("Test_Conv_Special_Chars_", result.output_path.name)

    def test_uses_item_id_for_untitled_conversation(self):
        """WriteToSessionStep uses item_id when conversation_name is Untitled."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            output_path.mkdir()

            step = WriteToSessionStep(output_path=output_path)
            item = ProcessingItem(
                item_id="abc-123-def",
                source_path=Path("/test/input.json"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={"source_type": "conversation", "conversation_name": "Untitled"},
                content="Test content",
            )

            result = step.process(item)

            self.assertEqual(result.output_path.name, "abc-123-def.md")


class TestUpdateIndexStepFileCopy(unittest.TestCase):
    """Test UpdateIndexStep file copy to @index (US5 - T057)."""

    def test_copies_file_to_index_directory(self):
        """UpdateIndexStep copies processed file to @index directory."""
        with TemporaryDirectory() as tmpdir:
            # Setup: Create session output file
            session_output = Path(tmpdir) / "session" / "output" / "conversations"
            session_output.mkdir(parents=True)
            output_file = session_output / "test.md"
            output_file.write_text("---\nitem_id: abc123\ntitle: Test\n---\n\nContent", encoding="utf-8")

            # Setup: Create @index directory
            index_path = Path(tmpdir) / "@index"
            index_path.mkdir()

            # Create UpdateIndexStep with index_path
            step = UpdateIndexStep(index_path=index_path)
            item = ProcessingItem(
                item_id="test-123",
                source_path=Path("/test/input.json"),
                current_step="write_to_session",
                status=ItemStatus.PENDING,
                metadata={"item_id": "abc123"},
                output_path=output_file,
            )

            result = step.process(item)

            # Verify file was copied to @index
            index_file = index_path / "test.md"
            self.assertTrue(index_file.exists())
            self.assertEqual(index_file.read_text(encoding="utf-8"), output_file.read_text(encoding="utf-8"))
            self.assertTrue(result.metadata.get("indexed"))
            self.assertEqual(result.metadata.get("index_path"), str(index_file))

    def test_creates_index_directory_if_not_exists(self):
        """UpdateIndexStep creates @index directory if it does not exist."""
        with TemporaryDirectory() as tmpdir:
            # Setup: Create session output file
            session_output = Path(tmpdir) / "session" / "output"
            session_output.mkdir(parents=True)
            output_file = session_output / "test.md"
            output_file.write_text("---\nitem_id: def456\n---\n\nContent", encoding="utf-8")

            # Index path does not exist
            index_path = Path(tmpdir) / "@index" / "subdir"

            step = UpdateIndexStep(index_path=index_path)
            item = ProcessingItem(
                item_id="test-456",
                source_path=Path("/test/input.json"),
                current_step="write_to_session",
                status=ItemStatus.PENDING,
                metadata={"item_id": "def456"},
                output_path=output_file,
            )

            result = step.process(item)

            # Directory should be created
            self.assertTrue(index_path.exists())
            index_file = index_path / "test.md"
            self.assertTrue(index_file.exists())

    def test_skips_copy_when_no_output_path(self):
        """UpdateIndexStep skips copy when item has no output_path."""
        with TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "@index"
            index_path.mkdir()

            step = UpdateIndexStep(index_path=index_path)
            item = ProcessingItem(
                item_id="test-789",
                source_path=Path("/test/input.json"),
                current_step="write_to_session",
                status=ItemStatus.PENDING,
                metadata={"item_id": "ghi789"},
                # No output_path
            )

            result = step.process(item)

            # Should mark as indexed but not copy
            self.assertTrue(result.metadata.get("indexed"))
            self.assertNotIn("index_path", result.metadata)

    def test_skips_copy_when_no_index_path_configured(self):
        """UpdateIndexStep skips copy when index_path is None."""
        with TemporaryDirectory() as tmpdir:
            # Setup: Create session output file
            session_output = Path(tmpdir) / "session" / "output"
            session_output.mkdir(parents=True)
            output_file = session_output / "test.md"
            output_file.write_text("Content", encoding="utf-8")

            # No index_path configured (default behavior for backward compatibility)
            step = UpdateIndexStep(index_path=None)
            item = ProcessingItem(
                item_id="test-000",
                source_path=Path("/test/input.json"),
                current_step="write_to_session",
                status=ItemStatus.PENDING,
                metadata={},
                output_path=output_file,
            )

            result = step.process(item)

            # Should still mark as indexed
            self.assertTrue(result.metadata.get("indexed"))
            self.assertNotIn("index_path", result.metadata)


class TestUpdateIndexStepDuplicateDetection(unittest.TestCase):
    """Test UpdateIndexStep item_id duplicate detection (US5 - T058)."""

    def test_overwrites_existing_file_with_same_item_id(self):
        """UpdateIndexStep overwrites file in @index if same item_id exists."""
        with TemporaryDirectory() as tmpdir:
            # Setup: Create session output file with item_id
            session_output = Path(tmpdir) / "session" / "output"
            session_output.mkdir(parents=True)
            output_file = session_output / "new_name.md"
            output_file.write_text(
                "---\nitem_id: abc123\ntitle: Updated Title\n---\n\nUpdated content",
                encoding="utf-8"
            )

            # Setup: Create existing file in @index with same item_id but different name
            index_path = Path(tmpdir) / "@index"
            index_path.mkdir()
            existing_file = index_path / "old_name.md"
            existing_file.write_text(
                "---\nitem_id: abc123\ntitle: Old Title\n---\n\nOld content",
                encoding="utf-8"
            )

            step = UpdateIndexStep(index_path=index_path)
            item = ProcessingItem(
                item_id="test-123",
                source_path=Path("/test/input.json"),
                current_step="write_to_session",
                status=ItemStatus.PENDING,
                metadata={"item_id": "abc123"},
                output_path=output_file,
            )

            result = step.process(item)

            # Old file should be removed, new file should exist
            self.assertFalse(existing_file.exists())
            new_index_file = index_path / "new_name.md"
            self.assertTrue(new_index_file.exists())
            self.assertIn("Updated content", new_index_file.read_text(encoding="utf-8"))
            self.assertEqual(result.metadata.get("index_overwritten"), True)
            self.assertEqual(result.metadata.get("index_overwritten_file"), "old_name.md")

    def test_creates_new_file_for_different_item_id(self):
        """UpdateIndexStep creates new file in @index when item_id differs."""
        with TemporaryDirectory() as tmpdir:
            # Setup: Create session output file
            session_output = Path(tmpdir) / "session" / "output"
            session_output.mkdir(parents=True)
            output_file = session_output / "new_file.md"
            output_file.write_text(
                "---\nitem_id: xyz999\ntitle: New File\n---\n\nNew content",
                encoding="utf-8"
            )

            # Setup: Create existing file in @index with different item_id
            index_path = Path(tmpdir) / "@index"
            index_path.mkdir()
            existing_file = index_path / "existing.md"
            existing_file.write_text(
                "---\nitem_id: abc123\ntitle: Existing\n---\n\nExisting content",
                encoding="utf-8"
            )

            step = UpdateIndexStep(index_path=index_path)
            item = ProcessingItem(
                item_id="test-999",
                source_path=Path("/test/input.json"),
                current_step="write_to_session",
                status=ItemStatus.PENDING,
                metadata={"item_id": "xyz999"},
                output_path=output_file,
            )

            result = step.process(item)

            # Both files should exist
            self.assertTrue(existing_file.exists())
            new_index_file = index_path / "new_file.md"
            self.assertTrue(new_index_file.exists())
            self.assertNotIn("index_overwritten", result.metadata)

    def test_detects_item_id_in_frontmatter(self):
        """UpdateIndexStep correctly detects item_id from YAML frontmatter."""
        with TemporaryDirectory() as tmpdir:
            # Setup: Create @index with multiple files
            index_path = Path(tmpdir) / "@index"
            index_path.mkdir()

            # File 1: has item_id abc123
            file1 = index_path / "file1.md"
            file1.write_text(
                "---\ntitle: File 1\nitem_id: abc123\ntags:\n  - test\n---\n\nContent 1",
                encoding="utf-8"
            )

            # File 2: has item_id def456
            file2 = index_path / "file2.md"
            file2.write_text(
                "---\nitem_id: def456\ntitle: File 2\n---\n\nContent 2",
                encoding="utf-8"
            )

            # File 3: no item_id
            file3 = index_path / "file3.md"
            file3.write_text(
                "---\ntitle: File 3\n---\n\nContent 3",
                encoding="utf-8"
            )

            step = UpdateIndexStep(index_path=index_path)

            # Test: find abc123
            found = step._find_existing_by_item_id("abc123")
            self.assertEqual(found, file1)

            # Test: find def456
            found = step._find_existing_by_item_id("def456")
            self.assertEqual(found, file2)

            # Test: not found
            found = step._find_existing_by_item_id("notfound")
            self.assertIsNone(found)

    def test_handles_malformed_frontmatter(self):
        """UpdateIndexStep handles files with malformed frontmatter gracefully."""
        with TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "@index"
            index_path.mkdir()

            # File with invalid YAML but valid item_id line
            # Note: We use regex-based extraction, so this will still find item_id
            bad_file = index_path / "bad.md"
            bad_file.write_text(
                "---\ntitle: [invalid yaml\nitem_id: abc123\n---\n\nContent",
                encoding="utf-8"
            )

            # File with no frontmatter
            no_fm_file = index_path / "no_fm.md"
            no_fm_file.write_text("Just content, no frontmatter", encoding="utf-8")

            # File with no closing frontmatter marker
            unclosed_file = index_path / "unclosed.md"
            unclosed_file.write_text("---\nitem_id: xyz789\nSome content", encoding="utf-8")

            step = UpdateIndexStep(index_path=index_path)

            # bad_file has valid item_id line, so it will be found (regex-based)
            found = step._find_existing_by_item_id("abc123")
            self.assertEqual(found, bad_file)

            # no_fm_file has no frontmatter
            found = step._find_existing_by_item_id("nonexistent")
            self.assertIsNone(found)

            # unclosed_file has no closing ---, so not found
            found = step._find_existing_by_item_id("xyz789")
            self.assertIsNone(found)


class TestSessionLoaderIntegration(unittest.TestCase):
    """Test SessionLoader stage integration."""

    def test_session_loader_default_steps(self):
        """SessionLoader has default steps: WriteToSession, UpdateIndex."""
        loader = SessionLoader()
        self.assertEqual(len(loader.steps), 2)
        self.assertIsInstance(loader.steps[0], WriteToSessionStep)
        self.assertIsInstance(loader.steps[1], UpdateIndexStep)

    def test_session_loader_with_index_path(self):
        """SessionLoader can be configured with index_path."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            index_path = Path(tmpdir) / "@index"

            loader = SessionLoader(output_path=output_path, index_path=index_path)

            # Second step should have index_path configured
            update_step = loader.steps[1]
            self.assertIsInstance(update_step, UpdateIndexStep)
            self.assertEqual(update_step._index_path, index_path)

    def test_session_loader_runs_both_steps(self):
        """SessionLoader runs WriteToSession then UpdateIndex."""
        with TemporaryDirectory() as tmpdir:
            # Setup
            output_path = Path(tmpdir) / "session" / "output"
            output_path.mkdir(parents=True)
            index_path = Path(tmpdir) / "@index"
            index_path.mkdir()

            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.LOAD, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=False,
            )

            # Create loader with both paths
            loader = SessionLoader(output_path=output_path, index_path=index_path)

            items = [
                ProcessingItem(
                    item_id="test-123",
                    source_path=Path("/test/input.json"),
                    current_step="transform",
                    status=ItemStatus.PENDING,
                    metadata={
                        "source_type": "conversation",
                        "conversation_name": "Integration Test",
                        "item_id": "inttest123",
                    },
                    transformed_content="---\nitem_id: inttest123\ntitle: Integration Test\n---\n\nTest content",
                )
            ]

            results = list(loader.run(ctx, iter(items)))

            # Verify results
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, ItemStatus.COMPLETED)

            # Verify session output
            session_file = output_path / "conversations" / "Integration Test.md"
            self.assertTrue(session_file.exists())

            # Verify @index output
            index_file = index_path / "Integration Test.md"
            self.assertTrue(index_file.exists())


class TestErrorDetailFileCreation(unittest.TestCase):
    """Test error detail file creation (US6 - T066)."""

    def test_error_detail_file_created_in_errors_folder(self):
        """BaseStage._handle_error creates error detail file in errors/ folder."""
        from datetime import datetime
        from src.etl.utils.error_writer import ErrorDetail, write_error_file

        with TemporaryDirectory() as tmpdir:
            # Setup: Create phase directory structure
            session_path = Path(tmpdir) / "20260119_140000"
            session_path.mkdir()
            phase_path = session_path / "import"
            phase_path.mkdir()
            errors_path = phase_path / "errors"

            # Create ErrorDetail
            error = ErrorDetail(
                session_id="20260119_140000",
                conversation_id="abc-123-def",
                conversation_title="Test Conversation",
                timestamp=datetime(2026, 1, 19, 14, 0, 0),
                error_type="json_parse",
                error_message="JSON parse error at position 42",
                original_content='{"invalid": json}',
                llm_prompt="Extract knowledge from: ...",
                stage="extract_knowledge",
            )

            # Write error file
            output_path = write_error_file(error, errors_path)

            # Verify
            self.assertTrue(errors_path.exists())
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.parent, errors_path)
            self.assertEqual(output_path.name, "abc-123-def.md")

    def test_error_file_with_timestamp_in_filename(self):
        """Error detail file uses conversation_id as filename."""
        from datetime import datetime
        from src.etl.utils.error_writer import ErrorDetail, write_error_file

        with TemporaryDirectory() as tmpdir:
            errors_path = Path(tmpdir) / "errors"

            error = ErrorDetail(
                session_id="20260119_140000",
                conversation_id="uuid-with-dashes-456",
                conversation_title="Another Test",
                timestamp=datetime(2026, 1, 19, 14, 30, 0),
                error_type="timeout",
                error_message="Ollama timeout after 60s",
                original_content="Long conversation content...",
                llm_prompt="Prompt text...",
                stage="transform",
            )

            output_path = write_error_file(error, errors_path)

            # Filename is conversation_id.md
            self.assertEqual(output_path.name, "uuid-with-dashes-456.md")


class TestErrorDetailFields(unittest.TestCase):
    """Test ErrorDetail fields in output file (US6 - T067)."""

    def test_error_file_contains_all_required_fields(self):
        """Error detail file contains all required fields from ErrorDetail."""
        from datetime import datetime
        from src.etl.utils.error_writer import ErrorDetail, write_error_file

        with TemporaryDirectory() as tmpdir:
            errors_path = Path(tmpdir) / "errors"

            error = ErrorDetail(
                session_id="20260119_150000",
                conversation_id="test-conv-789",
                conversation_title="Field Test Conversation",
                timestamp=datetime(2026, 1, 19, 15, 0, 0),
                error_type="no_json",
                error_message="LLM response did not contain valid JSON",
                original_content="Original conversation content here",
                llm_prompt="Extract knowledge prompt here",
                stage="extract_knowledge",
                error_position=150,
                error_context="...near 'some context'...",
                llm_output="Invalid LLM output without JSON",
            )

            output_path = write_error_file(error, errors_path)
            content = output_path.read_text(encoding="utf-8")

            # Verify all fields are present in output
            self.assertIn("Session**: 20260119_150000", content)
            self.assertIn("Conversation ID**: test-conv-789", content)
            self.assertIn("Field Test Conversation", content)
            self.assertIn("2026-01-19 15:00:00", content)
            self.assertIn("Error Type**: no_json", content)
            self.assertIn("Error Position**: 150", content)
            self.assertIn("Stage**: extract_knowledge", content)
            self.assertIn("LLM response did not contain valid JSON", content)
            self.assertIn("Original conversation content here", content)
            self.assertIn("Extract knowledge prompt here", content)
            self.assertIn("Invalid LLM output without JSON", content)
            self.assertIn("near 'some context'", content)

    def test_error_file_handles_optional_fields(self):
        """Error detail file handles optional fields (None values)."""
        from datetime import datetime
        from src.etl.utils.error_writer import ErrorDetail, write_error_file

        with TemporaryDirectory() as tmpdir:
            errors_path = Path(tmpdir) / "errors"

            # ErrorDetail with optional fields as None
            error = ErrorDetail(
                session_id="20260119_160000",
                conversation_id="optional-test",
                conversation_title="Optional Fields Test",
                timestamp=datetime(2026, 1, 19, 16, 0, 0),
                error_type="json_parse",
                error_message="Parse error",
                original_content="Content",
                llm_prompt="Prompt",
                stage="transform",
                # Optional fields not set (None)
            )

            output_path = write_error_file(error, errors_path)
            content = output_path.read_text(encoding="utf-8")

            # Optional fields should show N/A or (no output)
            self.assertIn("Error Position**: N/A", content)
            self.assertIn("(no output)", content)
            # Context section should not appear when error_context is None
            self.assertNotIn("## Context", content)

    def test_error_file_markdown_structure(self):
        """Error detail file has correct Markdown structure."""
        from datetime import datetime
        from src.etl.utils.error_writer import ErrorDetail, write_error_file

        with TemporaryDirectory() as tmpdir:
            errors_path = Path(tmpdir) / "errors"

            error = ErrorDetail(
                session_id="20260119_170000",
                conversation_id="structure-test",
                conversation_title="Structure Test",
                timestamp=datetime(2026, 1, 19, 17, 0, 0),
                error_type="timeout",
                error_message="Timeout error",
                original_content="Content",
                llm_prompt="Prompt",
                stage="load",
                error_context="Context around error",
            )

            output_path = write_error_file(error, errors_path)
            content = output_path.read_text(encoding="utf-8")

            # Verify Markdown headers
            self.assertIn("# Error Detail:", content)
            self.assertIn("## Error Message", content)
            self.assertIn("## Original Content", content)
            self.assertIn("## LLM Prompt", content)
            self.assertIn("## LLM Raw Output", content)
            self.assertIn("## Context", content)

            # Verify code blocks
            self.assertIn("```text", content)
            self.assertIn("```", content)


if __name__ == "__main__":
    unittest.main()
