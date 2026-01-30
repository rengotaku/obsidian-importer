"""Tests for step-level debug output functionality.

Tests T013-T015: Debug output enabled, disabled, and on failure scenarios.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.etl.core.models import ProcessingItem
from src.etl.core.phase import Phase
from src.etl.core.stage import BaseStage, BaseStep, StageContext
from src.etl.core.status import ItemStatus
from src.etl.core.types import PhaseType, StageType


class TestDebugStepOutput(unittest.TestCase):
    """Test step-level debug output functionality."""

    def setUp(self):
        """Create test fixtures for debug output testing."""

        # Create a test step that processes items
        class ProcessStep(BaseStep):
            @property
            def name(self) -> str:
                return "process_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                item.transformed_content = f"processed: {item.content}"
                return item

        # Create a test step that transforms content
        class TransformStep(BaseStep):
            @property
            def name(self) -> str:
                return "transform_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                if item.transformed_content:
                    item.transformed_content = item.transformed_content.upper()
                return item

        # Create a test step that fails
        class FailingStep(BaseStep):
            @property
            def name(self) -> str:
                return "failing_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                from src.etl.core.errors import StepError

                raise StepError("Intentional test failure", item_id=item.item_id)

        # Create test stage with configurable steps
        class TestStage(BaseStage):
            def __init__(self, steps: list[BaseStep]):
                self._steps = steps

            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return self._steps

        self.ProcessStep = ProcessStep
        self.TransformStep = TransformStep
        self.FailingStep = FailingStep
        self.TestStage = TestStage

    def test_debug_step_output_enabled(self):
        """T013: Step-level debug output is written when debug_mode=True."""
        with TemporaryDirectory() as tmpdir:
            # Create phase folder
            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()
            phase_path = session_path / "import"
            phase_path.mkdir()

            # Create phase
            from src.etl.core.stage import Stage

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=phase_path,
            )

            # Create stage data
            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase_path)
            stage_data.ensure_folders()

            # Create stage with multiple steps
            stage = self.TestStage([self.ProcessStep(), self.TransformStep()])

            # Create stage context with debug mode enabled
            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=True,  # Enable debug mode
            )

            # Create test item
            item = ProcessingItem(
                item_id="test_001",
                source_path=Path("/fake/source.txt"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={},
                content="test content",
            )

            # Process item through stage
            items = [item]
            results = list(stage.run(ctx, iter(items)))

            # Verify item was processed successfully
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, ItemStatus.COMPLETED)

            # Verify output was written to steps.jsonl at stage level
            stage_path = stage_data.output_path.parent
            self.assertTrue(stage_path.exists(), "Stage folder should exist")

            # Check steps.jsonl file at stage level
            steps_file = stage_path / "steps.jsonl"
            self.assertTrue(steps_file.exists(), "steps.jsonl should exist")

            # Read all entries from steps.jsonl
            with open(steps_file, encoding="utf-8") as f:
                lines = f.readlines()

            # Should have 2 entries (one per step)
            self.assertEqual(len(lines), 2, "Should have 2 JSONL entries for 2 steps")

            # Verify step 1 data
            step1_data = json.loads(lines[0].strip())
            self.assertEqual(step1_data["item_id"], "test_001")
            self.assertEqual(step1_data["current_step"], "process_step")
            self.assertEqual(step1_data["step_index"], 1)
            # Content contains latest result (transformed_content), truncated to ~200 chars
            self.assertEqual(step1_data["content"], "processed: test content")
            # Metrics are included
            self.assertIn("timing_ms", step1_data)
            self.assertIn("before_chars", step1_data)
            self.assertIn("after_chars", step1_data)
            # transformed_content no longer output as separate key
            self.assertNotIn("transformed_content", step1_data)

            # Verify step 2 data
            step2_data = json.loads(lines[1].strip())
            self.assertEqual(step2_data["item_id"], "test_001")
            self.assertEqual(step2_data["current_step"], "transform_step")
            self.assertEqual(step2_data["step_index"], 2)
            # Content contains latest result (uppercased transformed_content)
            self.assertIn("PROCESSED:", step2_data["content"])
            # Metrics are included
            self.assertIn("timing_ms", step2_data)
            # transformed_content no longer output as separate key
            self.assertNotIn("transformed_content", step2_data)

    def test_debug_step_output_disabled(self):
        """T014: FR-012 - Debug mode is always enabled (deprecated test)."""
        # FR-012: Debug mode is now always enabled, so this test verifies
        # that debug output IS written even when debug_mode is explicitly set to False
        with TemporaryDirectory() as tmpdir:
            # Create phase folder
            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()
            phase_path = session_path / "import"
            phase_path.mkdir()

            # Create phase
            from src.etl.core.stage import Stage

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=phase_path,
            )

            # Create stage data
            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase_path)
            stage_data.ensure_folders()

            # Create stage with multiple steps
            stage = self.TestStage([self.ProcessStep(), self.TransformStep()])

            # Create stage context with debug mode explicitly False
            # (FR-012: this now defaults to True internally)
            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=False,  # Ignored - always True per FR-012
            )

            # Create test item
            item = ProcessingItem(
                item_id="test_002",
                source_path=Path("/fake/source.txt"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={},
                content="test content",
            )

            # Process item through stage
            items = [item]
            results = list(stage.run(ctx, iter(items)))

            # Verify item was processed successfully
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, ItemStatus.COMPLETED)

            # FR-012: Output SHOULD be written at stage level (debug mode always enabled)
            stage_path = stage_data.output_path.parent
            steps_file = stage_path / "steps.jsonl"
            self.assertTrue(
                steps_file.exists(), "steps.jsonl should exist (FR-012: debug always enabled)"
            )

    def test_debug_step_output_on_failure(self):
        """T015: Step-level debug output is written when step fails and debug_mode=True."""
        with TemporaryDirectory() as tmpdir:
            # Create phase folder
            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()
            phase_path = session_path / "import"
            phase_path.mkdir()

            # Create phase
            from src.etl.core.stage import Stage

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=phase_path,
            )

            # Create stage data
            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase_path)
            stage_data.ensure_folders()

            # Create conditional failing step (fails only for test_003)
            class ConditionalFailingStep(BaseStep):
                @property
                def name(self) -> str:
                    return "conditional_failing_step"

                def process(self, item: ProcessingItem) -> ProcessingItem:
                    from src.etl.core.errors import StepError

                    # Fail only test_003 (error rate: 1/6 = 16.7% < 20%)
                    if item.item_id == "test_003":
                        raise StepError("Intentional test failure", item_id=item.item_id)
                    return item

            # Create stage with process step and conditional failing step
            stage = self.TestStage([self.ProcessStep(), ConditionalFailingStep()])

            # Create stage context with debug mode enabled
            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=True,  # Enable debug mode
            )

            # Create 6 test items (1 will fail: 16.7% < 20% threshold)
            items = [
                ProcessingItem(
                    item_id=f"test_{i:03d}",
                    source_path=Path(f"/fake/source{i}.txt"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                    content=f"test content {i}",
                )
                for i in range(1, 7)
            ]

            # Process items through stage (test_003 should fail on step 2)
            results = list(stage.run(ctx, iter(items)))

            # Verify 6 items processed (5 completed, 1 failed)
            self.assertEqual(len(results), 6)
            failed_items = [r for r in results if r.status == ItemStatus.FAILED]
            self.assertEqual(len(failed_items), 1)
            self.assertEqual(failed_items[0].item_id, "test_003")

            # Verify output was written to steps.jsonl at stage level
            stage_path = stage_data.output_path.parent
            self.assertTrue(stage_path.exists(), "Stage folder should exist")

            steps_file = stage_path / "steps.jsonl"
            self.assertTrue(steps_file.exists(), "steps.jsonl should exist")

            # Read all entries from steps.jsonl
            with open(steps_file, encoding="utf-8") as f:
                lines = f.readlines()

            # Should have 12 entries (6 items × 2 steps each)
            self.assertEqual(len(lines), 12, "Should have 12 JSONL entries")

            # Find test_003 entries
            test_003_entries = [
                json.loads(line.strip())
                for line in lines
                if json.loads(line.strip())["item_id"] == "test_003"
            ]
            self.assertEqual(len(test_003_entries), 2, "test_003 should have 2 step entries")

            # Verify step 1 data for test_003 (successful)
            step1_data = test_003_entries[0]
            self.assertEqual(step1_data["item_id"], "test_003")
            self.assertEqual(step1_data["current_step"], "process_step")
            self.assertNotIn("error", step1_data, "Step 1 should not have error")

            # Verify step 2 data for test_003 (failed)
            step2_data = test_003_entries[1]
            self.assertEqual(step2_data["item_id"], "test_003")
            self.assertEqual(step2_data["current_step"], "conditional_failing_step")
            self.assertIn("error", step2_data, "Step 2 should have error field")
            self.assertIn("Intentional test failure", step2_data["error"])

    def test_multiple_items_append_to_single_file(self):
        """Verify multiple items are appended to the same consolidated debug file.

        Tests that when multiple items are processed through the same step,
        all debug outputs are written to a single JSONL file (one line per item).
        This verifies the append mode ("a") is working correctly.
        """
        with TemporaryDirectory() as tmpdir:
            # Create phase folder
            session_path = Path(tmpdir) / "20260120_100000"
            session_path.mkdir()
            phase_path = session_path / "import"
            phase_path.mkdir()

            # Create phase and stage
            from src.etl.core.stage import Stage

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=phase_path,
            )
            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase_path)
            stage_data.ensure_folders()

            # Create stage with single step
            stage = self.TestStage([self.ProcessStep()])

            # Create stage context with debug mode enabled
            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=True,  # Enable debug mode
            )

            # Process multiple items
            items = []
            for i in range(3):
                item = ProcessingItem(
                    item_id=f"test_multi_{i}",
                    source_path=Path(f"/fake/source_{i}.txt"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                    content=f"content {i}",
                )
                items.append(item)

            # Process all items
            results = list(stage.run(ctx, iter(items)))

            # Verify all items were processed
            self.assertEqual(len(results), 3)
            for result in results:
                self.assertEqual(result.status, ItemStatus.COMPLETED)

            # Verify steps.jsonl exists at stage level
            stage_path = stage_data.output_path.parent
            self.assertTrue(stage_path.exists(), "Stage folder should exist")

            steps_file = stage_path / "steps.jsonl"
            self.assertTrue(steps_file.exists(), "steps.jsonl should exist")

            # Read all lines from steps.jsonl
            with open(steps_file, encoding="utf-8") as f:
                lines = f.readlines()

            # Should have 3 entries (one per item)
            self.assertEqual(len(lines), 3, "Should have 3 JSONL entries for 3 items")

            # Verify each item's data
            for i, line in enumerate(lines):
                item_data = json.loads(line.strip())
                self.assertEqual(item_data["item_id"], f"test_multi_{i}")
                # Content contains latest result (transformed_content), truncated
                self.assertEqual(item_data["content"], f"processed: content {i}")
                # Metrics are included
                self.assertIn("timing_ms", item_data)
                # transformed_content no longer output as separate key
                self.assertNotIn("transformed_content", item_data)

    def test_debug_output_for_1to1_processing(self):
        """T015: Verify debug output for 1:1 processing includes correct metadata.

        User Story 1: Standard 1:1 processing.
        Verifies that debug output for non-chunked items has is_chunked=False
        and chunk-related fields are null or absent.
        """
        with TemporaryDirectory() as tmpdir:
            # Create phase folder
            session_path = Path(tmpdir) / "20260120_100000"
            session_path.mkdir()
            phase_path = session_path / "import"
            phase_path.mkdir()

            # Create phase
            from src.etl.core.stage import Stage

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=phase_path,
            )

            # Create stage data
            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase_path)
            stage_data.ensure_folders()

            # Create stage with test steps
            stage = self.TestStage([self.ProcessStep(), self.TransformStep()])

            # Create stage context with debug mode enabled
            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=True,  # Enable debug mode
            )

            # Create test item with non-chunked metadata
            item = ProcessingItem(
                item_id="test_1to1",
                source_path=Path("/fake/small_conversation.json"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={
                    "is_chunked": False,  # Explicitly mark as non-chunked
                },
                content="Small conversation content",
            )

            # Process item through stage
            items = [item]
            results = list(stage.run(ctx, iter(items)))

            # Verify item completed successfully
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, ItemStatus.COMPLETED)

            # Verify output exists at stage level
            stage_path = stage_data.output_path.parent
            self.assertTrue(stage_path.exists(), "Stage folder should exist")

            # Verify steps.jsonl exists at stage level
            steps_file = stage_path / "steps.jsonl"
            self.assertTrue(steps_file.exists(), "steps.jsonl should exist")

            # Read first entry from steps.jsonl
            with open(steps_file, encoding="utf-8") as f:
                debug_data = json.loads(f.readline().strip())

            # Verify is_chunked=False in metadata
            self.assertIn("metadata", debug_data, "Debug output should include metadata")
            self.assertIn("is_chunked", debug_data["metadata"])
            self.assertFalse(
                debug_data["metadata"]["is_chunked"],
                "1:1 processing should have is_chunked=False in debug output",
            )

            # Verify chunk-related fields are NOT present (or are None)
            chunk_index = debug_data["metadata"].get("chunk_index")
            total_chunks = debug_data["metadata"].get("total_chunks")
            parent_item_id = debug_data["metadata"].get("parent_item_id")

            # These fields should be absent for 1:1 processing
            self.assertIsNone(
                chunk_index,
                "chunk_index should be None for 1:1 processing",
            )
            self.assertIsNone(
                total_chunks,
                "total_chunks should be None for 1:1 processing",
            )
            self.assertIsNone(
                parent_item_id,
                "parent_item_id should be None for 1:1 processing",
            )

    def test_debug_output_for_chunked_items(self):
        """T026: Verify debug output for chunked items includes chunk metadata.

        User Story 2: 1:N expansion processing.
        Verifies that debug output for chunked items includes is_chunked=True,
        chunk_index, total_chunks, and parent_item_id fields.
        """
        with TemporaryDirectory() as tmpdir:
            # Create phase folder
            session_path = Path(tmpdir) / "20260120_110000"
            session_path.mkdir()
            phase_path = session_path / "import"
            phase_path.mkdir()

            # Create phase
            from src.etl.core.stage import Stage

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=phase_path,
            )

            # Create stage data
            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase_path)
            stage_data.ensure_folders()

            # Create stage with test steps
            stage = self.TestStage([self.ProcessStep(), self.TransformStep()])

            # Create stage context with debug mode enabled
            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=True,  # Enable debug mode
            )

            # Create test items with chunked metadata
            parent_id = "parent-conv-uuid"
            chunk_items = [
                ProcessingItem(
                    item_id=f"{parent_id}#chunk0",
                    source_path=Path("/fake/large_conversation.json"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={
                        "is_chunked": True,
                        "chunk_index": 0,
                        "total_chunks": 2,
                        "parent_item_id": parent_id,
                    },
                    content="Chunk 0 content",
                ),
                ProcessingItem(
                    item_id=f"{parent_id}#chunk1",
                    source_path=Path("/fake/large_conversation.json"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={
                        "is_chunked": True,
                        "chunk_index": 1,
                        "total_chunks": 2,
                        "parent_item_id": parent_id,
                    },
                    content="Chunk 1 content",
                ),
            ]

            # Process chunks through stage
            results = list(stage.run(ctx, iter(chunk_items)))

            # Verify both chunks completed successfully
            self.assertEqual(len(results), 2)
            for result in results:
                self.assertEqual(result.status, ItemStatus.COMPLETED)

            # Verify output exists at stage level
            stage_path = stage_data.output_path.parent
            self.assertTrue(stage_path.exists(), "Stage folder should exist")

            # Verify steps.jsonl for chunks at stage level
            steps_file = stage_path / "steps.jsonl"
            self.assertTrue(steps_file.exists(), "steps.jsonl should exist")

            # Read all lines from steps.jsonl
            with open(steps_file, encoding="utf-8") as f:
                lines = f.readlines()

            # Should have 4 entries: 2 chunks × 2 steps = 4
            self.assertEqual(len(lines), 4, "Should have 4 JSONL entries for 2 chunks × 2 steps")

            # Filter for step 1 (process_step) only
            step1_entries = [
                json.loads(line.strip())
                for line in lines
                if json.loads(line.strip())["step_index"] == 1
            ]
            self.assertEqual(len(step1_entries), 2, "Should have 2 entries for step 1")

            chunk0_data = step1_entries[0]
            chunk1_data = step1_entries[1]

            # Verify chunk metadata for chunk 0
            self.assertTrue(chunk0_data["metadata"]["is_chunked"])
            self.assertEqual(chunk0_data["metadata"]["chunk_index"], 0)
            self.assertEqual(chunk0_data["metadata"]["total_chunks"], 2)
            self.assertEqual(chunk0_data["metadata"]["parent_item_id"], parent_id)

            # Verify chunk metadata for chunk 1
            self.assertTrue(chunk1_data["metadata"]["is_chunked"])
            self.assertEqual(chunk1_data["metadata"]["chunk_index"], 1)
            self.assertEqual(chunk1_data["metadata"]["total_chunks"], 2)
            self.assertEqual(chunk1_data["metadata"]["parent_item_id"], parent_id)


class TestChatGPTExtractStepsJsonl(unittest.TestCase):
    """Test ChatGPT Extract stage generates steps.jsonl (User Story 1)."""

    def test_chatgpt_extract_generates_steps_jsonl(self):
        """ChatGPT Extract stage generates steps.jsonl in debug mode."""
        import zipfile

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        with TemporaryDirectory() as tmpdir:
            # Create test ZIP file with conversations.json
            zip_path = Path(tmpdir) / "test.zip"
            conversations_data = [
                {
                    "conversation_id": "conv1",
                    "title": "Test",
                    "create_time": 1609459200,
                    "mapping": {
                        "root": {"message": None, "parent": None},
                        "node1": {
                            "message": {
                                "id": "msg1",
                                "author": {"role": "user"},
                                "content": {"parts": ["Hello"]},
                                "create_time": 1609459200,
                            },
                            "parent": "root",
                        },
                        "node2": {
                            "message": {
                                "id": "msg2",
                                "author": {"role": "assistant"},
                                "content": {"parts": ["Hi there!"]},
                                "create_time": 1609459260,
                            },
                            "parent": "node1",
                        },
                    },
                    "current_node": "node2",
                }
            ]

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps(conversations_data))

            # Create phase folder
            session_path = Path(tmpdir) / "20260124_120000"
            session_path.mkdir()
            phase_path = session_path / "import"
            phase_path.mkdir()

            # Create phase
            from src.etl.core.stage import Stage

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=phase_path,
            )

            # Create extract stage data
            stage_data = Stage.create_for_phase(StageType.EXTRACT, phase_path)
            stage_data.ensure_folders()

            # Create ChatGPTExtractor with Steps
            extractor = ChatGPTExtractor()

            # Create stage context with debug mode enabled
            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=True,  # Enable debug mode
            )

            # Discover items (should yield 1 ZIP item with content=None)
            items = extractor.discover_items(zip_path)

            # Run stage (processes through all steps)
            results = list(extractor.run(ctx, items))

            # Verify results
            self.assertEqual(len(results), 1, "Should produce 1 conversation")

            # Verify steps.jsonl was generated at stage level
            steps_jsonl = stage_data.output_path.parent / "steps.jsonl"
            self.assertTrue(steps_jsonl.exists(), "steps.jsonl should be generated at stage level")

            # Read and verify steps.jsonl content
            with open(steps_jsonl) as f:
                lines = f.readlines()

            self.assertGreater(len(lines), 0, "steps.jsonl should contain step logs")

            # Parse JSONL lines
            steps = [json.loads(line) for line in lines]

            # Verify steps include ValidateMinMessagesStep (only remaining step)
            step_names = {step["current_step"] for step in steps}
            expected_steps = {
                "validate_min_messages",
            }
            self.assertTrue(
                expected_steps.issubset(step_names),
                f"steps.jsonl should contain validate_min_messages step: {expected_steps}",
            )

            # Verify each step has required fields
            for step in steps:
                self.assertIn("current_step", step)
                self.assertIn("timing_ms", step)
                self.assertIn("item_id", step)


if __name__ == "__main__":
    unittest.main()
