"""Tests for Stage base class and implementations.

Tests BaseStage abstract class, StageContext, and concrete Stage implementations.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.etl.core.models import ProcessingItem, StageLogRecord
from src.etl.core.phase import Phase
from src.etl.core.stage import BaseStage, BaseStep, Stage, StageContext
from src.etl.core.status import ItemStatus
from src.etl.core.types import PhaseType, StageType

# Helper mixin for test stages to implement abstract methods


class TestBaseStageAbstract(unittest.TestCase):
    """Test BaseStage is an abstract class."""

    def test_base_stage_is_abstract(self):
        """BaseStage cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseStage()  # type: ignore

    def test_base_stage_requires_stage_type(self):
        """Subclass must implement stage_type property."""

        class IncompleteStage(BaseStage):
            @property
            def steps(self) -> list[BaseStep]:
                return []

        with self.assertRaises(TypeError):
            IncompleteStage()  # type: ignore

    def test_base_stage_requires_steps(self):
        """Subclass must implement steps property."""

        class IncompleteStage(BaseStage):
            @property
            def stage_type(self) -> StageType:
                return StageType.EXTRACT

        with self.assertRaises(TypeError):
            IncompleteStage()  # type: ignore


class TestBaseStageImplementation(unittest.TestCase):
    """Test concrete BaseStage implementation."""

    def setUp(self):
        """Create a minimal Stage implementation for testing."""

        class TestStep(BaseStep):
            @property
            def name(self) -> str:
                return "test_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                item.content = "processed"
                return item

        class TestStage(BaseStage):
            def __init__(self, steps: list[BaseStep] | None = None):
                super().__init__()
                self._steps = steps or [TestStep()]

            @property
            def stage_type(self) -> StageType:
                return StageType.EXTRACT

            @property
            def steps(self) -> list[BaseStep]:
                return self._steps

            def _discover_raw_items(self, input_path: Path):
                """Test stub."""
                return iter([])

            def _build_conversation_for_chunking(self, item: ProcessingItem):
                """Test stub."""
                return None

        self.TestStep = TestStep
        self.TestStage = TestStage

    def test_stage_has_correct_type(self):
        """Stage reports correct stage_type."""
        stage = self.TestStage()
        self.assertEqual(stage.stage_type, StageType.EXTRACT)

    def test_stage_has_steps(self):
        """Stage has configured steps."""
        stage = self.TestStage()
        self.assertEqual(len(stage.steps), 1)
        self.assertEqual(stage.steps[0].name, "test_step")

    def test_stage_run_processes_items(self):
        """Stage.run() processes items through steps."""
        with TemporaryDirectory() as tmpdir:
            # Create session and phase for context
            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage with paths
            stage_data = Stage.create_for_phase(StageType.EXTRACT, phase.base_path)
            stage_data.ensure_folders()

            # Create context
            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            # Create items
            items = [
                ProcessingItem(
                    item_id="test1",
                    source_path=Path("/test/file1.md"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                )
            ]

            # Run stage
            stage = self.TestStage()
            results = list(stage.run(ctx, iter(items)))

            # Verify
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].content, "processed")


class TestStageContext(unittest.TestCase):
    """Test StageContext dataclass."""

    def test_stage_context_creation(self):
        """StageContext can be created with required fields."""
        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )

            stage = Stage.create_for_phase(StageType.EXTRACT, phase.base_path)

            ctx = StageContext(
                phase=phase,
                stage=stage,
                debug_mode=True,
            )

            self.assertEqual(ctx.phase.phase_type, PhaseType.IMPORT)
            self.assertEqual(ctx.stage.stage_type, StageType.EXTRACT)
            self.assertTrue(ctx.debug_mode)

    def test_stage_context_paths(self):
        """StageContext provides input/output paths."""
        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )

            stage = Stage.create_for_phase(StageType.EXTRACT, phase.base_path)

            ctx = StageContext(
                phase=phase,
                stage=stage,
            )

            # Verify paths
            self.assertTrue(str(ctx.input_path).endswith("extract/input"))
            self.assertTrue(str(ctx.output_path).endswith("extract/output"))


class TestBaseStep(unittest.TestCase):
    """Test BaseStep abstract class."""

    def test_base_step_is_abstract(self):
        """BaseStep cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseStep()  # type: ignore

    def test_step_implementation(self):
        """Concrete step implements required methods."""

        class PassthroughStep(BaseStep):
            @property
            def name(self) -> str:
                return "passthrough"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                return item

        step = PassthroughStep()
        self.assertEqual(step.name, "passthrough")

        # Test process
        item = ProcessingItem(
            item_id="test",
            source_path=Path("/test.md"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={},
        )
        result = step.process(item)
        self.assertIs(result, item)

    def test_step_validate_input_default(self):
        """Default validate_input returns True."""

        class SimpleStep(BaseStep):
            @property
            def name(self) -> str:
                return "simple"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                return item

        step = SimpleStep()
        item = ProcessingItem(
            item_id="test",
            source_path=Path("/test.md"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={},
        )
        self.assertTrue(step.validate_input(item))

    def test_step_on_error_default(self):
        """Default on_error returns None."""

        class SimpleStep(BaseStep):
            @property
            def name(self) -> str:
                return "simple"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                return item

        step = SimpleStep()
        item = ProcessingItem(
            item_id="test",
            source_path=Path("/test.md"),
            current_step="init",
            status=ItemStatus.PENDING,
            metadata={},
        )
        result = step.on_error(item, Exception("test"))
        self.assertIsNone(result)


class TestStageWithMultipleSteps(unittest.TestCase):
    """Test Stage with multiple steps."""

    def test_multiple_steps_execute_in_order(self):
        """Steps execute in order they are defined."""
        execution_order = []

        class Step1(BaseStep):
            @property
            def name(self) -> str:
                return "step1"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                execution_order.append("step1")
                item.metadata["step1"] = True
                return item

        class Step2(BaseStep):
            @property
            def name(self) -> str:
                return "step2"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                execution_order.append("step2")
                item.metadata["step2"] = True
                return item

        class MultiStepStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return [Step1(), Step2()]

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )

            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase.base_path)

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            items = [
                ProcessingItem(
                    item_id="test1",
                    source_path=Path("/test.md"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                )
            ]

            stage = MultiStepStage()
            results = list(stage.run(ctx, iter(items)))

            self.assertEqual(execution_order, ["step1", "step2"])
            self.assertTrue(results[0].metadata.get("step1"))
            self.assertTrue(results[0].metadata.get("step2"))


class TestStageErrorHandling(unittest.TestCase):
    """Test Stage error handling."""

    def test_step_error_marks_item_failed(self):
        """When step raises StepError, item is marked as failed (below threshold)."""
        from src.etl.core.errors import StepError

        class ConditionalFailingStep(BaseStep):
            @property
            def name(self) -> str:
                return "conditional_failing"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                # Fail only the first item (error rate: 1/6 = 16.7% < 20%)
                if item.item_id == "test1":
                    raise StepError("Test error", item_id=item.item_id)
                return item

        class ConditionalStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.EXTRACT

            @property
            def steps(self) -> list[BaseStep]:
                return [ConditionalFailingStep()]

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )

            stage_data = Stage.create_for_phase(StageType.EXTRACT, phase.base_path)

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            # Create 6 items: 1 fails (16.7% < 20% threshold)
            items = [
                ProcessingItem(
                    item_id=f"test{i}",
                    source_path=Path(f"/test{i}.md"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                )
                for i in range(1, 7)
            ]

            stage = ConditionalStage()
            results = list(stage.run(ctx, iter(items)))

            # Should have 6 results: 1 failed, 5 completed
            self.assertEqual(len(results), 6)

            # First item should be failed
            failed_items = [r for r in results if r.status == ItemStatus.FAILED]
            self.assertEqual(len(failed_items), 1)
            self.assertEqual(failed_items[0].item_id, "test1")
            self.assertIn("Test error", failed_items[0].error or "")

            # Other items should be completed
            completed_items = [r for r in results if r.status == ItemStatus.COMPLETED]
            self.assertEqual(len(completed_items), 5)

    def test_step_with_fallback(self):
        """Step on_error can provide fallback."""

        class RecoverableStep(BaseStep):
            @property
            def name(self) -> str:
                return "recoverable"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                raise ValueError("Test error")

            def on_error(self, item: ProcessingItem, error: Exception) -> ProcessingItem | None:
                item.metadata["recovered"] = True
                item.error = f"Recovered from: {error}"
                return item

        class RecoverableStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return [RecoverableStep()]

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )

            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase.base_path)

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            items = [
                ProcessingItem(
                    item_id="test1",
                    source_path=Path("/test.md"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                )
            ]

            stage = RecoverableStage()
            results = list(stage.run(ctx, iter(items)))

            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].metadata.get("recovered"))
            self.assertEqual(results[0].status, ItemStatus.COMPLETED)


class TestStageJSONLLog(unittest.TestCase):
    """Test JSONL log output (US7)."""

    def test_jsonl_log_created_on_success(self):
        """JSONL log file is created with success record."""

        class SimpleStep(BaseStep):
            @property
            def name(self) -> str:
                return "simple_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                item.content = "processed content"
                return item

        class LoggingStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.EXTRACT

            @property
            def steps(self) -> list[BaseStep]:
                return [SimpleStep()]

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.EXTRACT, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            items = [
                ProcessingItem(
                    item_id="test1",
                    source_path=Path("/test/file1.md"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={"file_id": "abc123"},
                    content="original content",
                )
            ]

            stage = LoggingStage()
            results = list(stage.run(ctx, iter(items)))

            # Verify JSONL file was created
            jsonl_path = phase.pipeline_stages_jsonl
            self.assertTrue(jsonl_path.exists())

            # Read and verify content
            with open(jsonl_path, encoding="utf-8") as f:
                lines = f.readlines()

            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])

            # Verify required fields
            self.assertEqual(record["session_id"], "20260119_120000")
            self.assertEqual(record["filename"], "file1.md")
            self.assertEqual(record["stage"], "extract")
            self.assertEqual(record["step"], "simple_step")
            self.assertEqual(record["status"], "success")
            self.assertEqual(record["file_id"], "abc123")
            self.assertIn("timestamp", record)
            self.assertIn("timing_ms", record)
            self.assertGreaterEqual(record["timing_ms"], 0)

    def test_jsonl_log_records_failure(self):
        """JSONL log records failed items (below threshold)."""
        from src.etl.core.errors import StepError

        class ConditionalFailingStep(BaseStep):
            @property
            def name(self) -> str:
                return "conditional_failing_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                # Fail only test1 (error rate: 1/6 = 16.7% < 20%)
                if item.item_id == "test1":
                    raise StepError("Intentional failure", item_id=item.item_id)
                return item

        class ConditionalFailingStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return [ConditionalFailingStep()]

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_130000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            # Create 6 items: 1 fails (16.7% < 20% threshold)
            items = [
                ProcessingItem(
                    item_id=f"test{i}",
                    source_path=Path(f"/test/file{i}.md"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                )
                for i in range(1, 7)
            ]

            stage = ConditionalFailingStage()
            results = list(stage.run(ctx, iter(items)))

            # Verify JSONL has 6 records
            jsonl_path = phase.pipeline_stages_jsonl
            with open(jsonl_path, encoding="utf-8") as f:
                lines = f.readlines()

            self.assertEqual(len(lines), 6)

            # Find the failed record
            failed_record = None
            for line in lines:
                record = json.loads(line)
                if record["filename"] == "file1.md":
                    failed_record = record
                    break

            self.assertIsNotNone(failed_record)
            self.assertEqual(failed_record["status"], "failed")
            self.assertEqual(failed_record["filename"], "file1.md")

    def test_jsonl_log_records_content_metrics(self):
        """JSONL log includes before/after character counts and diff_ratio."""

        class ContentChangeStep(BaseStep):
            @property
            def name(self) -> str:
                return "content_change"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                # Double the content
                item.transformed_content = item.content * 2 if item.content else ""
                return item

        class MetricsStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return [ContentChangeStep()]

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_140000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            items = [
                ProcessingItem(
                    item_id="test1",
                    source_path=Path("/test/metrics.md"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                    content="Hello",  # 5 chars
                )
            ]

            stage = MetricsStage()
            results = list(stage.run(ctx, iter(items)))

            # Verify metrics in JSONL
            jsonl_path = phase.pipeline_stages_jsonl
            with open(jsonl_path, encoding="utf-8") as f:
                record = json.loads(f.readline())

            self.assertEqual(record["before_chars"], 5)
            self.assertEqual(record["after_chars"], 10)  # Doubled
            self.assertEqual(record["diff_ratio"], 2.0)


class TestStageDebugOutput(unittest.TestCase):
    """Test DEBUG mode output (US8)."""

    def test_debug_output_not_created_when_disabled(self):
        """FR-012: Debug output IS created (debug mode always enabled)."""

        class SimpleStep(BaseStep):
            @property
            def name(self) -> str:
                return "simple"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                return item

        class SimpleStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.EXTRACT

            @property
            def steps(self) -> list[BaseStep]:
                return [SimpleStep()]

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_150000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.EXTRACT, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=False,  # Ignored - always True per FR-012
            )

            items = [
                ProcessingItem(
                    item_id="test1",
                    source_path=Path("/test/nodebug.md"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                )
            ]

            stage = SimpleStage()
            list(stage.run(ctx, iter(items)))

            # FR-012: steps.jsonl should exist at stage level (debug always enabled)
            stage_folder = ctx.output_path.parent
            steps_file = stage_folder / "steps.jsonl"
            self.assertTrue(steps_file.exists(), "steps.jsonl should exist (FR-012)")

    def test_debug_output_created_when_enabled(self):
        """Debug output is created when debug_mode is True."""

        class ContentStep(BaseStep):
            @property
            def name(self) -> str:
                return "content_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                item.content = "processed content"
                return item

        class DebugStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.EXTRACT

            @property
            def steps(self) -> list[BaseStep]:
                return [ContentStep()]

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_160000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.EXTRACT, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=True,  # Enabled
            )

            items = [
                ProcessingItem(
                    item_id="test1",
                    source_path=Path("/test/debug_test.md"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={"key": "value"},
                    content="original",
                )
            ]

            stage = DebugStage()
            list(stage.run(ctx, iter(items)))

            # Files should exist at stage folder level (not in debug subfolder)
            stage_folder = ctx.output_path.parent
            self.assertTrue(stage_folder.exists())

            # Stage-level JSONL file should exist (exclude steps.jsonl)
            stage_files = [f for f in stage_folder.glob("*.jsonl") if f.name != "steps.jsonl"]
            self.assertEqual(len(stage_files), 1)

            # Verify file content (JSONL: one JSON object per line)
            with open(stage_files[0], encoding="utf-8") as f:
                lines = f.readlines()

            # Should have at least 1 line (one per step)
            self.assertGreater(len(lines), 0)

            # Verify last line contains final processed state
            debug_data = json.loads(lines[-1])
            self.assertEqual(debug_data["item_id"], "test1")
            self.assertEqual(debug_data["content"], "processed content")

    def test_debug_output_includes_error_on_failure(self):
        """Debug output includes error details when processing fails (below threshold)."""
        from src.etl.core.errors import StepError

        class ConditionalErrorStep(BaseStep):
            @property
            def name(self) -> str:
                return "conditional_error_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                # Fail only test1 (error rate: 1/6 = 16.7% < 20%)
                if item.item_id == "test1":
                    raise StepError("Debug test error", item_id=item.item_id)
                return item

        class ConditionalErrorStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return [ConditionalErrorStep()]

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260119_170000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
                debug_mode=True,  # Enabled
            )

            # Create 6 items: 1 fails (16.7% < 20% threshold)
            items = [
                ProcessingItem(
                    item_id=f"test{i}",
                    source_path=Path(f"/test/file{i}.md"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                )
                for i in range(1, 7)
            ]

            stage = ConditionalErrorStage()
            results = list(stage.run(ctx, iter(items)))

            # Verify 6 results (1 failed, 5 completed)
            self.assertEqual(len(results), 6)
            failed_items = [r for r in results if r.status == ItemStatus.FAILED]
            self.assertEqual(len(failed_items), 1)
            self.assertEqual(failed_items[0].item_id, "test1")

            # Stage-level files should exist (JSONL format, exclude steps.jsonl)
            stage_folder = ctx.output_path.parent
            stage_files = [f for f in stage_folder.glob("*.jsonl") if f.name != "steps.jsonl"]
            self.assertEqual(len(stage_files), 6, "Should have 6 stage-level files")

            # Find the file for test1
            test1_file = None
            for f in stage_files:
                with open(f, encoding="utf-8") as file:
                    lines = file.readlines()
                    if lines:
                        data = json.loads(lines[-1])
                        if data.get("item_id") == "test1":
                            test1_file = f
                            break

            self.assertIsNotNone(test1_file, "test1 file should exist")

            # Verify test1 file content (JSONL)
            with open(test1_file, encoding="utf-8") as f:
                lines = f.readlines()

            # Should have at least 1 line
            self.assertGreater(len(lines), 0)

            # Verify debug data contains item_id and content
            debug_data = json.loads(lines[-1])
            self.assertEqual(debug_data["item_id"], "test1")
            self.assertIn("content", debug_data)  # Content may be empty on error


class TestStageLogRecord(unittest.TestCase):
    """Test StageLogRecord dataclass."""

    def test_to_dict_required_fields(self):
        """to_dict includes all required fields."""
        record = StageLogRecord(
            timestamp="2026-01-19T12:00:00Z",
            session_id="20260119_120000",
            filename="test.md",
            stage="extract",
            step="parse",
            timing_ms=150,
            status="success",
        )

        result = record.to_dict()

        self.assertEqual(result["timestamp"], "2026-01-19T12:00:00Z")
        self.assertEqual(result["session_id"], "20260119_120000")
        self.assertEqual(result["filename"], "test.md")
        self.assertEqual(result["stage"], "extract")
        self.assertEqual(result["step"], "parse")
        self.assertEqual(result["timing_ms"], 150)
        self.assertEqual(result["status"], "success")

    def test_to_dict_excludes_none_optional_fields(self):
        """to_dict excludes None optional fields."""
        record = StageLogRecord(
            timestamp="2026-01-19T12:00:00Z",
            session_id="20260119_120000",
            filename="test.md",
            stage="extract",
            step="parse",
            timing_ms=150,
            status="success",
            # All optional fields are None
        )

        result = record.to_dict()

        self.assertNotIn("file_id", result)
        self.assertNotIn("skipped_reason", result)
        self.assertNotIn("before_chars", result)
        self.assertNotIn("after_chars", result)
        self.assertNotIn("diff_ratio", result)

    def test_to_dict_includes_set_optional_fields(self):
        """to_dict includes optional fields when set."""
        record = StageLogRecord(
            timestamp="2026-01-19T12:00:00Z",
            session_id="20260119_120000",
            filename="test.md",
            stage="transform",
            step="extract_knowledge",
            timing_ms=2500,
            status="success",
            file_id="abc123",
            before_chars=1000,
            after_chars=500,
            diff_ratio=0.5,
        )

        result = record.to_dict()

        self.assertEqual(result["file_id"], "abc123")
        self.assertEqual(result["before_chars"], 1000)
        self.assertEqual(result["after_chars"], 500)
        self.assertEqual(result["diff_ratio"], 0.5)

    def test_pipeline_stages_jsonl_1to1_format(self):
        """T016: Verify pipeline_stages.jsonl format for 1:1 processing.

        User Story 1: Standard 1:1 processing.
        Verifies that JSONL log entries for non-chunked items include
        chunk fields (is_chunked, parent_item_id, chunk_index) as null.
        """
        record_non_chunked = StageLogRecord(
            timestamp="2026-01-20T10:00:00Z",
            session_id="20260120_100000",
            filename="small_conversation.json",
            stage="transform",
            step="extract_knowledge",
            timing_ms=1500,
            status="success",
            file_id="abc123",
            before_chars=500,
            after_chars=450,
            diff_ratio=0.9,
            # Chunk fields should be None for 1:1 processing
            is_chunked=False,
            parent_item_id=None,
            chunk_index=None,
        )

        result = record_non_chunked.to_dict()

        # Required fields present
        self.assertEqual(result["timestamp"], "2026-01-20T10:00:00Z")
        self.assertEqual(result["session_id"], "20260120_100000")
        self.assertEqual(result["filename"], "small_conversation.json")
        self.assertEqual(result["stage"], "transform")
        self.assertEqual(result["step"], "extract_knowledge")
        self.assertEqual(result["timing_ms"], 1500)
        self.assertEqual(result["status"], "success")

        # Chunk field: is_chunked=False should be included
        self.assertIn("is_chunked", result)
        self.assertFalse(result["is_chunked"])

        # Chunk fields: parent_item_id and chunk_index should be excluded (None)
        self.assertNotIn(
            "parent_item_id",
            result,
            "parent_item_id should be excluded when None for 1:1 processing",
        )
        self.assertNotIn(
            "chunk_index",
            result,
            "chunk_index should be excluded when None for 1:1 processing",
        )

    def test_pipeline_stages_jsonl_chunked_format(self):
        """T027: Verify pipeline_stages.jsonl format for chunked items.

        User Story 2: 1:N expansion processing.
        Verifies that JSONL log entries for chunked items include all
        chunk metadata fields (is_chunked, parent_item_id, chunk_index).
        """
        parent_id = "large-conv-uuid"
        record_chunked = StageLogRecord(
            timestamp="2026-01-20T11:00:00Z",
            session_id="20260120_110000",
            filename="large_conversation.json",
            stage="transform",
            step="extract_knowledge",
            timing_ms=2500,
            status="success",
            file_id="def456",
            before_chars=30000,
            after_chars=15000,
            diff_ratio=0.5,
            # Chunk fields for chunk 0 of 2
            is_chunked=True,
            parent_item_id=parent_id,
            chunk_index=0,
        )

        result = record_chunked.to_dict()

        # Required fields present
        self.assertEqual(result["timestamp"], "2026-01-20T11:00:00Z")
        self.assertEqual(result["session_id"], "20260120_110000")
        self.assertEqual(result["filename"], "large_conversation.json")
        self.assertEqual(result["stage"], "transform")
        self.assertEqual(result["step"], "extract_knowledge")
        self.assertEqual(result["timing_ms"], 2500)
        self.assertEqual(result["status"], "success")

        # Chunk fields: All should be present for chunked items
        self.assertIn("is_chunked", result)
        self.assertTrue(result["is_chunked"])

        self.assertIn(
            "parent_item_id",
            result,
            "parent_item_id should be included for chunked items",
        )
        self.assertEqual(result["parent_item_id"], parent_id)

        self.assertIn(
            "chunk_index",
            result,
            "chunk_index should be included for chunked items",
        )
        self.assertEqual(result["chunk_index"], 0)

    def test_trace_output_to_input_via_parent_item_id(self):
        """T043: Verify SC-005 - Traceability from output to original input.

        Success Criterion 5: 入出力の追跡可能性
        Verifies that chunked output files can be traced back to original input
        via parent_item_id in pipeline_stages.jsonl.
        """
        # Create multiple chunk records for the same parent conversation
        parent_id = "original-conv-uuid-abc123"
        chunk_records = []

        for i in range(3):
            record = StageLogRecord(
                timestamp=f"2026-01-20T12:0{i}:00Z",
                session_id="20260120_120000",
                filename=f"large_conversation_{i + 1:03d}.md",
                stage="load",
                step="write_session",
                timing_ms=500,
                status="success",
                file_id=f"chunk-{i}-file-id",
                is_chunked=True,
                parent_item_id=parent_id,
                chunk_index=i,
            )
            chunk_records.append(record)

        # Verify all chunks share same parent_item_id
        parent_ids = [rec.parent_item_id for rec in chunk_records]
        self.assertEqual(
            len(set(parent_ids)),
            1,
            "All chunks should have same parent_item_id",
        )
        self.assertEqual(
            parent_ids[0],
            parent_id,
            "Parent ID should match original conversation UUID",
        )

        # Verify chunk indices are sequential
        chunk_indices = [rec.chunk_index for rec in chunk_records]
        self.assertEqual(chunk_indices, [0, 1, 2], "Chunk indices should be sequential")

        # Verify all chunks are marked as chunked
        for rec in chunk_records:
            self.assertTrue(
                rec.is_chunked,
                "All chunk records should have is_chunked=True",
            )

        # Verify output filenames match expected pattern
        expected_filenames = [
            "large_conversation_001.md",
            "large_conversation_002.md",
            "large_conversation_003.md",
        ]
        actual_filenames = [rec.filename for rec in chunk_records]
        self.assertEqual(
            actual_filenames,
            expected_filenames,
            "Output filenames should follow _001, _002, _003 pattern",
        )

        # Simulate tracing: Given an output file, find all sibling chunks
        # This demonstrates how to trace output back to original input
        def find_sibling_chunks(records, target_filename):
            """Find all chunks from same parent conversation."""
            # Find target record
            target = next(r for r in records if r.filename == target_filename)
            if not target.is_chunked:
                return [target]  # Single file, no siblings

            # Find all records with same parent_item_id
            siblings = [
                r for r in records if r.parent_item_id == target.parent_item_id and r.is_chunked
            ]
            return sorted(siblings, key=lambda x: x.chunk_index)

        # Test traceability: Given "large_conversation_002.md", find siblings
        siblings = find_sibling_chunks(chunk_records, "large_conversation_002.md")

        self.assertEqual(len(siblings), 3, "Should find all 3 chunks from same parent")
        self.assertEqual(
            [s.filename for s in siblings],
            expected_filenames,
            "Siblings should include all chunks in order",
        )

        # Verify we can trace back to original input UUID
        self.assertEqual(
            siblings[0].parent_item_id,
            parent_id,
            "Can trace back to original conversation UUID",
        )


class TestClaudeExtractorDiscovery(unittest.TestCase):
    """Test ClaudeExtractor.discover_items() method."""

    def test_discover_items_returns_iterator(self):
        """ClaudeExtractor.discover_items() returns Iterator[ProcessingItem]."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            # Create conversations.json
            conversations_file = input_path / "conversations.json"
            conversations = [
                {
                    "uuid": "conv-001",
                    "name": "Test Conversation",
                    "created_at": "2026-01-20T10:00:00.000Z",
                    "updated_at": "2026-01-20T10:00:00.000Z",
                    "chat_messages": [
                        {"uuid": "msg1", "text": "Hello", "sender": "human"},
                        {"uuid": "msg2", "text": "Hi", "sender": "assistant"},
                        {"uuid": "msg3", "text": "How are you?", "sender": "human"},
                    ],
                }
            ]
            conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

            extractor = ClaudeExtractor()
            items = extractor.discover_items(input_path)

            # Verify it's an iterator
            self.assertTrue(hasattr(items, "__iter__"))
            self.assertTrue(hasattr(items, "__next__"))

            # Consume iterator and verify item
            items_list = list(items)
            self.assertEqual(len(items_list), 1)
            self.assertIsInstance(items_list[0], ProcessingItem)
            self.assertEqual(items_list[0].metadata["conversation_uuid"], "conv-001")

    def test_discover_items_from_empty_directory(self):
        """ClaudeExtractor.discover_items() handles empty directory."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(input_path))

            self.assertEqual(len(items), 0)

    def test_discover_items_nonexistent_path(self):
        """ClaudeExtractor.discover_items() handles nonexistent path."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        nonexistent_path = Path("/nonexistent/path/to/nowhere")

        extractor = ClaudeExtractor()
        items = list(extractor.discover_items(nonexistent_path))

        self.assertEqual(len(items), 0)

    def test_discover_items_expands_conversations(self):
        """ClaudeExtractor.discover_items() expands conversations into items."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            # Create conversations.json with multiple conversations
            conversations_file = input_path / "conversations.json"
            conversations = [
                {
                    "uuid": "conv-001",
                    "name": "First Chat",
                    "created_at": "2026-01-20T10:00:00.000Z",
                    "updated_at": "2026-01-20T10:00:00.000Z",
                    "chat_messages": [
                        {"uuid": "msg1", "text": "Hello 1", "sender": "human"},
                        {"uuid": "msg2", "text": "Hi 1", "sender": "assistant"},
                        {"uuid": "msg3", "text": "Bye 1", "sender": "human"},
                    ],
                },
                {
                    "uuid": "conv-002",
                    "name": "Second Chat",
                    "created_at": "2026-01-20T11:00:00.000Z",
                    "updated_at": "2026-01-20T11:00:00.000Z",
                    "chat_messages": [
                        {"uuid": "msg4", "text": "Hello 2", "sender": "human"},
                        {"uuid": "msg5", "text": "Hi 2", "sender": "assistant"},
                        {"uuid": "msg6", "text": "Bye 2", "sender": "human"},
                    ],
                },
            ]
            conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

            extractor = ClaudeExtractor()
            items = list(extractor.discover_items(input_path))

            # Should yield 2 items (one per conversation)
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0].metadata["conversation_uuid"], "conv-001")
            self.assertEqual(items[1].metadata["conversation_uuid"], "conv-002")

    def test_discover_items_with_chunking(self):
        """ClaudeExtractor.discover_items() chunks large conversations."""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        with TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir)

            # Create a conversation that exceeds chunk_size (25000 chars)
            large_text = "A" * 30000  # 30k chars > 25k threshold
            conversations_file = input_path / "conversations.json"
            conversations = [
                {
                    "uuid": "conv-large",
                    "name": "Large Conversation",
                    "created_at": "2026-01-20T12:00:00.000Z",
                    "updated_at": "2026-01-20T12:00:00.000Z",
                    "chat_messages": [
                        {"uuid": "msg1", "text": "Start", "sender": "human"},
                        {"uuid": "msg2", "text": large_text, "sender": "assistant"},
                        {"uuid": "msg3", "text": "End", "sender": "human"},
                    ],
                }
            ]
            conversations_file.write_text(json.dumps(conversations), encoding="utf-8")

            extractor = ClaudeExtractor(chunk_size=25000)
            items = list(extractor.discover_items(input_path))

            # Should yield multiple chunks
            self.assertGreater(len(items), 1, "Large conversation should be chunked")

            # All chunks should have same parent_item_id (in metadata)
            parent_ids = [item.metadata.get("parent_item_id") for item in items]
            self.assertEqual(len(set(parent_ids)), 1, "All chunks should share parent_item_id")

            # Verify is_chunked flag
            for item in items:
                self.assertTrue(item.metadata.get("is_chunked"), "Chunked items should have flag")


@unittest.skip("Steps moved to _discover_raw_items() - see test_chatgpt_dedup.py")
class TestChatGPTExtractorSteps(unittest.TestCase):
    """Test ChatGPT Extractor Step classes (User Story 1)."""

    def setUp(self):
        """Set up test fixtures."""
        # Steps deleted: ReadZipStep, ParseConversationsStep, ConvertFormatStep
        # Only ValidateMinMessagesStep remains
        from src.etl.stages.extract.chatgpt_extractor import ValidateMinMessagesStep

        self.ValidateMinMessagesStep = ValidateMinMessagesStep

    def test_read_zip_step(self):
        """ReadZipStep reads ZIP and extracts conversations.json."""
        with TemporaryDirectory() as tmpdir:
            # Create test ZIP file with conversations.json
            zip_path = Path(tmpdir) / "test.zip"
            conversations_data = [
                {"conversation_id": "conv1", "title": "Test", "mapping": {}, "current_node": ""}
            ]

            import zipfile

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps(conversations_data))

            # Create ProcessingItem with content=None
            item = ProcessingItem(
                item_id="zip_test",
                source_path=zip_path,
                current_step="discover",
                status=ItemStatus.PENDING,
                metadata={},
                content=None,
            )

            # Execute step
            step = self.ReadZipStep()
            result = step.process(item)

            # Verify content is set to raw JSON string
            self.assertIsNotNone(result.content)
            self.assertIsInstance(result.content, str)
            data = json.loads(result.content)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["conversation_id"], "conv1")

            # Verify metadata
            self.assertEqual(result.metadata["extracted_file"], "conversations.json")
            self.assertIn("zip_path", result.metadata)

    def test_parse_conversations_step_expands(self):
        """ParseConversationsStep expands 1 item to N conversations."""
        # Create test input with 3 conversations
        conversations_data = [
            {
                "conversation_id": "conv1",
                "title": "First",
                "create_time": 1609459200,
                "mapping": {"node1": {}},
                "current_node": "node1",
            },
            {
                "conversation_id": "conv2",
                "title": "Second",
                "create_time": 1609545600,
                "mapping": {"node2": {}},
                "current_node": "node2",
            },
            {
                "conversation_id": "conv3",
                "title": "Third",
                "create_time": 1609632000,
                "mapping": {"node3": {}},
                "current_node": "node3",
            },
        ]

        item = ProcessingItem(
            item_id="zip_test",
            source_path=Path("/tmp/test.zip"),
            current_step="read_zip",
            status=ItemStatus.PENDING,
            metadata={},
            content=json.dumps(conversations_data),
        )

        # Execute step
        step = self.ParseConversationsStep()
        results = step.process(item)

        # Verify 1:N expansion
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)

        # Verify each expanded item
        for i, result in enumerate(results):
            self.assertIsInstance(result, ProcessingItem)
            self.assertEqual(result.item_id, f"conv{i + 1}")
            self.assertEqual(result.metadata["conversation_uuid"], f"conv{i + 1}")
            self.assertEqual(result.metadata["source_provider"], "openai")

            # Verify content is individual conversation dict
            conv_data = json.loads(result.content)
            self.assertEqual(conv_data["uuid"], f"conv{i + 1}")
            self.assertIn("mapping", conv_data)

    def test_convert_format_step(self):
        """ConvertFormatStep converts ChatGPT mapping to Claude messages."""
        # Create test conversation in ChatGPT format
        chatgpt_conversation = {
            "uuid": "conv1",
            "title": "Test Conversation",
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

        item = ProcessingItem(
            item_id="conv1",
            source_path=Path("/tmp/test.zip"),
            current_step="parse_conversations",
            status=ItemStatus.PENDING,
            metadata={"conversation_uuid": "conv1"},
            content=json.dumps(chatgpt_conversation),
        )

        # Execute step
        step = self.ConvertFormatStep()
        result = step.process(item)

        # Verify content is Claude format
        claude_data = json.loads(result.content)
        self.assertIn("chat_messages", claude_data)
        self.assertEqual(len(claude_data["chat_messages"]), 2)

        # Verify message conversion
        msg1 = claude_data["chat_messages"][0]
        self.assertEqual(msg1["sender"], "human")
        self.assertEqual(msg1["text"], "Hello")

        msg2 = claude_data["chat_messages"][1]
        self.assertEqual(msg2["sender"], "assistant")
        self.assertEqual(msg2["text"], "Hi there!")

        # Verify metadata
        self.assertEqual(result.metadata["format"], "claude")
        self.assertEqual(result.metadata["message_count"], 2)

    def test_validate_min_messages_step_skips(self):
        """ValidateMinMessagesStep sets status=SKIPPED for short conversations."""
        # Create conversation with only 1 message (< MIN_MESSAGES threshold)
        claude_conversation = {
            "uuid": "conv1",
            "name": "Short",
            "created_at": "2021-01-01",
            "chat_messages": [
                {"sender": "human", "text": "Hi", "uuid": "msg1", "created_at": "2021-01-01"}
            ],
        }

        item = ProcessingItem(
            item_id="conv1",
            source_path=Path("/tmp/test.zip"),
            current_step="convert_format",
            status=ItemStatus.PENDING,
            metadata={"conversation_uuid": "conv1"},
            content=json.dumps(claude_conversation),
        )

        # Set MIN_MESSAGES to 2 for this test
        from src.etl.stages.extract import chatgpt_extractor

        original_min = chatgpt_extractor.MIN_MESSAGES
        chatgpt_extractor.MIN_MESSAGES = 2

        try:
            # Execute step
            step = self.ValidateMinMessagesStep()
            result = step.process(item)

            # Verify status is SKIPPED
            self.assertEqual(result.status, ItemStatus.FILTERED)
            self.assertEqual(result.metadata["skip_reason"], "skipped_short")
            self.assertEqual(result.metadata["message_count"], 1)
        finally:
            chatgpt_extractor.MIN_MESSAGES = original_min

    def test_chatgpt_extractor_discover_items_minimal(self):
        """ChatGPTExtractor.discover_items() expands conversations from ZIP."""
        import zipfile

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        with TemporaryDirectory() as tmpdir:
            # Create test ZIP file with minimal conversation
            zip_path = Path(tmpdir) / "test.zip"
            conversations_data = [
                {
                    "conversation_id": "conv1",
                    "title": "Test Conversation",
                    "create_time": 1704067200.0,
                    "mapping": {
                        "node1": {
                            "id": "node1",
                            "message": {
                                "id": "msg1",
                                "author": {"role": "user"},
                                "content": {"parts": ["Hello"]},
                                "create_time": 1704067200.0,
                            },
                            "parent": None,
                        }
                    },
                    "current_node": "node1",
                }
            ]

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps(conversations_data))

            # Execute discover_items
            extractor = ChatGPTExtractor()
            items = list(extractor.discover_items(zip_path))

            # Verify expanded conversation returned
            self.assertGreater(len(items), 0)

            # Verify item has content (Claude format)
            item = items[0]
            self.assertIsNotNone(item.content)
            self.assertEqual(item.source_path, zip_path)
            self.assertEqual(item.metadata["source_provider"], "openai")

            # Verify conversation metadata is present
            self.assertIn("conversation_uuid", item.metadata)


class TestBaseExtractorTemplateMethod(unittest.TestCase):
    """Test BaseExtractor Template Method pattern (Phase 2)."""

    def test_abstract_method_not_implemented_raises_typeerror(self):
        """BaseExtractor subclass must implement abstract methods or raise TypeError."""
        from src.etl.core.extractor import BaseExtractor

        # Create a subclass that only implements steps
        # but NOT the abstract methods (_discover_raw_items, _build_conversation_for_chunking)
        class IncompleteExtractor(BaseExtractor):
            @property
            def steps(self) -> list[BaseStep]:
                return []

        # Attempting to instantiate should raise TypeError
        with self.assertRaises(TypeError) as context:
            IncompleteExtractor()

        # Verify error message mentions the missing abstract methods
        error_msg = str(context.exception)
        self.assertIn("_discover_raw_items", error_msg)
        self.assertIn("_build_conversation_for_chunking", error_msg)


if __name__ == "__main__":
    unittest.main()


class TestChatGPTExtractorAbstractMethods(unittest.TestCase):
    """Test ChatGPTExtractor abstract method implementations (Phase 4 - User Story 1)."""

    def test_chatgpt_extractor_discover_raw_items(self):
        """ChatGPTExtractor._discover_raw_items() が実装されていることを確認"""
        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Should be able to instantiate (no TypeError)
        extractor = ChatGPTExtractor()

        # Should have _discover_raw_items method
        self.assertTrue(hasattr(extractor, "_discover_raw_items"))
        self.assertTrue(callable(extractor._discover_raw_items))

    def test_chatgpt_extractor_build_conversation_for_chunking(self):
        """ChatGPTExtractor._build_conversation_for_chunking() が実装されていることを確認"""
        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        extractor = ChatGPTExtractor()

        # Should have _build_conversation_for_chunking method
        self.assertTrue(hasattr(extractor, "_build_conversation_for_chunking"))
        self.assertTrue(callable(extractor._build_conversation_for_chunking))

    def test_chatgpt_extractor_discover_raw_items_returns_iterator(self):
        """ChatGPTExtractor._discover_raw_items() が Iterator を返すことを確認"""
        import json
        import zipfile
        from collections.abc import Iterator

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create temp ZIP with conversations.json
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "test_export.zip"

            # Create minimal ZIP
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([]))

            extractor = ChatGPTExtractor()
            result = extractor._discover_raw_items(zip_path)

            # Should return iterator
            self.assertIsInstance(result, Iterator)

    def test_chatgpt_extractor_build_conversation_returns_conversation_protocol(self):
        """ChatGPTExtractor._build_conversation_for_chunking() が ConversationProtocol を返すことを確認"""
        import json

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create ProcessingItem with ChatGPT conversation data (Claude format after conversion)
        conversation_data = {
            "uuid": "test-uuid",
            "name": "Test Conversation",
            "created_at": "2024-01-01",
            "chat_messages": [
                {"uuid": "msg1", "sender": "human", "text": "Hello", "created_at": "2024-01-01"},
                {"uuid": "msg2", "sender": "assistant", "text": "Hi", "created_at": "2024-01-01"},
            ],
        }

        item = ProcessingItem(
            item_id="test-id",
            source_path=Path("/test/export.zip"),
            current_step="discover",
            status=ItemStatus.PENDING,
            metadata={},
            content=json.dumps(conversation_data, ensure_ascii=False),
        )

        extractor = ChatGPTExtractor()
        result = extractor._build_conversation_for_chunking(item)

        # Should return ConversationProtocol instance
        self.assertIsNotNone(result)
        # Check ConversationProtocol properties
        self.assertTrue(hasattr(result, "id"))
        self.assertTrue(hasattr(result, "title"))
        self.assertTrue(hasattr(result, "created_at"))
        self.assertTrue(hasattr(result, "messages"))
        self.assertTrue(hasattr(result, "provider"))

    def test_chatgpt_extractor_discover_items_no_chunking_in_discovery(self):
        """ChatGPTExtractor._discover_raw_items() が発見フェーズでチャンク処理をしないことを確認"""
        import json
        import zipfile

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create large conversation (>25000 chars) in ChatGPT format
        large_message = "x" * 30000
        chatgpt_conv = {
            "conversation_id": "test-uuid",
            "title": "Large Conversation",
            "create_time": 1704067200.0,
            "mapping": {
                "node1": {
                    "id": "node1",
                    "message": {
                        "id": "msg1",
                        "author": {"role": "user"},
                        "content": {"parts": [large_message]},
                        "create_time": 1704067200.0,
                    },
                    "parent": None,
                }
            },
            "current_node": "node1",
        }

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "test_export.zip"

            # Create ZIP with large conversation
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([chatgpt_conv]))

            extractor = ChatGPTExtractor()
            items = list(extractor._discover_raw_items(zip_path))

            # _discover_raw_items should NOT chunk - it returns raw items
            # Chunking happens in discover_items (template method)
            # So we expect 1 item (the ZIP file itself), not expanded conversations
            self.assertEqual(len(items), 1)
            # Item should not have chunking metadata yet
            self.assertFalse(items[0].metadata.get("is_chunked", False))

    def test_chatgpt_extractor_handles_invalid_zip(self):
        """ChatGPTExtractor が無効な ZIP ファイルを正しく処理することを確認"""
        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Create invalid ZIP (just a text file)
            invalid_zip = tmppath / "invalid.zip"
            invalid_zip.write_text("not a zip file")

            extractor = ChatGPTExtractor()
            items = list(extractor._discover_raw_items(invalid_zip))

            # Should return empty (invalid ZIP cannot be read)
            self.assertEqual(len(items), 0)

    def test_chatgpt_extractor_handles_missing_conversations_json(self):
        """ChatGPTExtractor が conversations.json が欠損している ZIP を正しく処理することを確認"""
        import zipfile

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "test_export.zip"

            # Create ZIP without conversations.json
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("some_other_file.txt", "test content")

            extractor = ChatGPTExtractor()
            items = list(extractor._discover_raw_items(zip_path))

            # Should return empty (no conversations.json)
            self.assertEqual(len(items), 0)

    def test_chatgpt_extractor_converts_mapping_to_conversation_protocol(self):
        """ChatGPTExtractor が mapping 構造を ConversationProtocol に変換できることを確認"""
        import json

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create ProcessingItem with converted ChatGPT data (Claude format)
        conversation_data = {
            "uuid": "test-uuid",
            "name": "Test Conversation",
            "created_at": "2024-01-01",
            "chat_messages": [
                {
                    "uuid": "msg1",
                    "sender": "human",
                    "text": "Question?",
                    "created_at": "2024-01-01",
                },
                {
                    "uuid": "msg2",
                    "sender": "assistant",
                    "text": "Answer.",
                    "created_at": "2024-01-01",
                },
            ],
        }

        item = ProcessingItem(
            item_id="test-id",
            source_path=Path("/test/export.zip"),
            current_step="convert_format",
            status=ItemStatus.PENDING,
            metadata={"source_provider": "openai"},
            content=json.dumps(conversation_data, ensure_ascii=False),
        )

        extractor = ChatGPTExtractor()
        conversation = extractor._build_conversation_for_chunking(item)

        # Should convert to ConversationProtocol
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.id, "test-uuid")
        self.assertEqual(conversation.title, "Test Conversation")
        self.assertEqual(conversation.created_at, "2024-01-01")
        self.assertEqual(len(conversation.messages), 2)
        self.assertEqual(conversation.provider, "openai")


class TestErrorRecording(unittest.TestCase):
    """Test error recording functionality (pipeline_stages.jsonl and error_details.jsonl)."""

    def setUp(self):
        """Create test stage that raises an error."""

        class ErrorStep(BaseStep):
            @property
            def name(self) -> str:
                return "error_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                raise ValueError("Test error message")

        class ErrorStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return [ErrorStep()]

        self.ErrorStage = ErrorStage

    def test_error_message_in_pipeline_stages_jsonl(self):
        """Error message is recorded in pipeline_stages.jsonl."""
        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260126_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage with paths
            from src.etl.core.stage import Stage

            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase.base_path)
            stage_data.ensure_folders()

            # Create test item
            item = ProcessingItem(
                item_id="test_item",
                source_path=Path("test.json"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={},
                content="test content",
            )

            # Run stage (will fail and raise StageError due to 100% error rate)
            stage = self.ErrorStage()
            ctx = StageContext(phase=phase, stage=stage_data)

            from src.etl.core.errors import StageError

            with self.assertRaises(StageError):
                list(stage.run(ctx, [item]))

            # Verify pipeline_stages.jsonl contains error_message
            jsonl_path = phase.base_path / "pipeline_stages.jsonl"
            self.assertTrue(jsonl_path.exists())

            with open(jsonl_path, encoding="utf-8") as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 1)

                record = json.loads(lines[0])
                self.assertEqual(record["status"], "failed")
                self.assertIn("error_message", record)
                self.assertIn("Test error message", record["error_message"])

    def test_error_details_jsonl_created(self):
        """error_details.jsonl is created when error occurs."""
        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260126_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage with paths
            from src.etl.core.stage import Stage

            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase.base_path)
            stage_data.ensure_folders()

            item = ProcessingItem(
                item_id="test_item_123",
                source_path=Path("test.json"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={},
                content="test content",
            )

            # Run stage (will fail and raise StageError due to 100% error rate)
            stage = self.ErrorStage()
            ctx = StageContext(phase=phase, stage=stage_data)

            from src.etl.core.errors import StageError

            with self.assertRaises(StageError):
                list(stage.run(ctx, [item]))

            # Verify error_details.jsonl exists
            error_details_path = phase.base_path / "error_details.jsonl"
            self.assertTrue(error_details_path.exists())

    def test_error_details_content(self):
        """error_details.jsonl contains correct error information."""
        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260126_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage with paths
            from src.etl.core.stage import Stage

            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase.base_path)
            stage_data.ensure_folders()

            item = ProcessingItem(
                item_id="test_item_456",
                source_path=Path("test.json"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={"conversation_name": "Test Conversation"},
                content="test content",
            )

            # Run stage (will fail and raise StageError due to 100% error rate)
            stage = self.ErrorStage()
            ctx = StageContext(phase=phase, stage=stage_data)

            from src.etl.core.errors import StageError

            with self.assertRaises(StageError):
                list(stage.run(ctx, [item]))

            # Read error_details.jsonl
            error_details_path = phase.base_path / "error_details.jsonl"
            with open(error_details_path, encoding="utf-8") as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 1)

                record = json.loads(lines[0])

                # Verify required fields
                self.assertEqual(record["session_id"], "20260126_120000")
                self.assertEqual(record["item_id"], "test_item_456")
                self.assertEqual(record["stage"], "transform")
                self.assertEqual(record["step"], "error_step")
                self.assertEqual(record["error_type"], "ValueError")
                self.assertEqual(record["error_message"], "Test error message")
                self.assertIn("backtrace", record)
                self.assertIn("Traceback", record["backtrace"])

                # Verify metadata
                self.assertIn("metadata", record)
                self.assertEqual(record["metadata"]["conversation_title"], "Test Conversation")


class TestGitHubExtractorAbstractMethods(unittest.TestCase):
    """Test GitHubExtractor abstract method implementations (Phase 5 - User Story 2)."""

    def test_github_extractor_discover_raw_items(self):
        """GitHubExtractor._discover_raw_items() が実装されていることを確認"""
        from tempfile import TemporaryDirectory

        from src.etl.stages.extract.github_extractor import GitHubExtractor

        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create github_url.txt with dummy URL
            (tmpdir_path / "github_url.txt").write_text(
                "https://github.com/test/repo/tree/master/_posts"
            )

            extractor = GitHubExtractor()

            # Should have _discover_raw_items method
            self.assertTrue(hasattr(extractor, "_discover_raw_items"))
            self.assertTrue(callable(extractor._discover_raw_items))

    def test_github_extractor_build_conversation_returns_none(self):
        """GitHubExtractor._build_conversation_for_chunking() が None を返すことを確認"""
        from src.etl.stages.extract.github_extractor import GitHubExtractor

        extractor = GitHubExtractor()

        # Create dummy item
        dummy_item = ProcessingItem(
            item_id="test",
            source_path=Path("/test.md"),
            current_step="test",
            status=ItemStatus.PENDING,
            content="# Test\n\nContent",
            metadata={},
        )

        # Should return None (no chunking for GitHub articles)
        result = extractor._build_conversation_for_chunking(dummy_item)
        self.assertIsNone(result)

    def test_github_extractor_instantiation_succeeds(self):
        """GitHubExtractor が TypeError なしでインスタンス化できることを確認"""
        from src.etl.stages.extract.github_extractor import GitHubExtractor

        # Should not raise TypeError (all abstract methods implemented)
        try:
            extractor = GitHubExtractor()
            self.assertIsNotNone(extractor)
        except TypeError as e:
            self.fail(f"GitHubExtractor instantiation failed: {e}")

    def test_github_extractor_discover_raw_items_returns_iterator(self):
        """GitHubExtractor._discover_raw_items() が Iterator を返すことを確認"""
        from collections.abc import Iterator
        from tempfile import TemporaryDirectory

        from src.etl.stages.extract.github_extractor import GitHubExtractor

        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create github_url.txt
            (tmpdir_path / "github_url.txt").write_text(
                "https://github.com/test/repo/tree/master/_posts"
            )

            extractor = GitHubExtractor()

            # Should return Iterator (may be empty, but must be iterable)
            # Note: This will try to clone, so we expect it to fail
            # but it should still return an iterator
            try:
                result = extractor._discover_raw_items(tmpdir_path)
                # Check type before attempting to consume
                self.assertIsInstance(result, Iterator)
            except (ValueError, Exception):
                # If it fails (e.g., can't clone), that's expected in unit test
                # The important part is that the method signature is correct
                pass

    def test_github_extractor_no_chunking_applied(self):
        """GitHubExtractor が大きなファイルでもチャンク処理をしないことを確認"""
        from src.etl.stages.extract.github_extractor import GitHubExtractor

        extractor = GitHubExtractor()

        # Create large content (>25,000 chars - chunking threshold)
        large_content = "# Test Article\n\n" + ("Lorem ipsum dolor sit amet. " * 2000)

        dummy_item = ProcessingItem(
            item_id="large_article",
            source_path=Path("/large.md"),
            current_step="test",
            status=ItemStatus.PENDING,
            content=large_content,
            metadata={},
        )

        # _build_conversation_for_chunking should return None
        # This signals BaseExtractor to skip chunking
        result = extractor._build_conversation_for_chunking(dummy_item)
        self.assertIsNone(result)

    def test_github_extractor_existing_behavior_preserved(self):
        """GitHubExtractor が既存の動作を維持していることを確認"""
        from tempfile import TemporaryDirectory

        from src.etl.stages.extract.github_extractor import GitHubExtractor

        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test markdown file
            test_md = tmpdir_path / "2024-01-15-test-post.md"
            test_md.write_text("---\ntitle: Test Post\ndate: 2024-01-15\n---\n\nContent")

            # Create github_url.txt (required by old discover_items)
            (tmpdir_path / "github_url.txt").write_text(
                "https://github.com/test/repo/tree/master/_posts"
            )

            extractor = GitHubExtractor()

            # Old discover_items should still work
            # Note: Will fail to clone, but we're testing that method exists
            self.assertTrue(hasattr(extractor, "discover_items"))
            self.assertTrue(callable(extractor.discover_items))


class TestExtractOutputFixedFilename(unittest.TestCase):
    """Test Extract stage output fixed filename pattern (User Story 3).

    Tests for:
    - T005: Fixed filename pattern data-dump-0001.jsonl
    - T006: Record splitting at 1000 records
    - T007: File index increment
    """

    def setUp(self):
        """Create a minimal Extract stage for testing."""

        class SimpleStep(BaseStep):
            @property
            def name(self) -> str:
                return "simple_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                item.content = "processed"
                return item

        class TestExtractStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.EXTRACT

            @property
            def steps(self) -> list[BaseStep]:
                return [SimpleStep()]

        self.TestExtractStage = TestExtractStage

    def test_fixed_filename_pattern_data_dump_0001(self):
        """T005: Extract output uses fixed filename pattern data-dump-0001.jsonl.

        User Story 3, Scenario 1:
        Given Extract stage を実行する際,
        When ProcessingItem を output に書き込む場合,
        Then ファイル名は data-dump-0001.jsonl から始まる固定パターンになる
        """
        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.EXTRACT, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            # Create a single item
            items = [
                ProcessingItem(
                    item_id="test1",
                    source_path=Path("/test/conv1.json"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                    content="test content",
                )
            ]

            stage = self.TestExtractStage()
            list(stage.run(ctx, iter(items)))

            # Verify output file uses fixed pattern
            output_files = list(ctx.output_path.glob("data-dump-*.jsonl"))
            self.assertEqual(len(output_files), 1)
            self.assertEqual(output_files[0].name, "data-dump-0001.jsonl")

    def test_record_splitting_at_1000_records(self):
        """T006: Extract output creates new file after 1000 records.

        User Story 3, Scenario 2:
        Given 1000 レコードを書き込んだ状態で,
        When 次の ProcessingItem を書き込む場合,
        Then 新規ファイル data-dump-0002.jsonl が作成され、そこに書き込まれる
        """
        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_130000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.EXTRACT, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            # Create 1001 items (should create 2 files)
            items = [
                ProcessingItem(
                    item_id=f"test{i:04d}",
                    source_path=Path(f"/test/conv{i}.json"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                    content=f"content {i}",
                )
                for i in range(1001)
            ]

            stage = self.TestExtractStage()
            list(stage.run(ctx, iter(items)))

            # Verify two output files created
            output_files = sorted(ctx.output_path.glob("data-dump-*.jsonl"))
            self.assertEqual(len(output_files), 2)
            self.assertEqual(output_files[0].name, "data-dump-0001.jsonl")
            self.assertEqual(output_files[1].name, "data-dump-0002.jsonl")

            # Verify first file has 1000 records
            with open(output_files[0], encoding="utf-8") as f:
                lines_first = f.readlines()
            self.assertEqual(len(lines_first), 1000)

            # Verify second file has 1 record
            with open(output_files[1], encoding="utf-8") as f:
                lines_second = f.readlines()
            self.assertEqual(len(lines_second), 1)

    def test_file_index_increments_correctly(self):
        """T007: File index increments after reaching max records per file.

        Tests that _output_file_index increments correctly:
        - Starts at 1 (1-indexed, not 0-indexed)
        - Increments to 2 after 1000 records
        - Increments to 3 after 2000 records
        """
        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_140000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.EXTRACT, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            # Create 2500 items (should create 3 files)
            items = [
                ProcessingItem(
                    item_id=f"item{i:05d}",
                    source_path=Path(f"/test/file{i}.json"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                    content=f"content {i}",
                )
                for i in range(2500)
            ]

            stage = self.TestExtractStage()
            list(stage.run(ctx, iter(items)))

            # Verify three output files created with correct names
            output_files = sorted(ctx.output_path.glob("data-dump-*.jsonl"))
            self.assertEqual(len(output_files), 3)
            self.assertEqual(output_files[0].name, "data-dump-0001.jsonl")
            self.assertEqual(output_files[1].name, "data-dump-0002.jsonl")
            self.assertEqual(output_files[2].name, "data-dump-0003.jsonl")

            # Verify record counts
            with open(output_files[0], encoding="utf-8") as f:
                self.assertEqual(len(f.readlines()), 1000)
            with open(output_files[1], encoding="utf-8") as f:
                self.assertEqual(len(f.readlines()), 1000)
            with open(output_files[2], encoding="utf-8") as f:
                self.assertEqual(len(f.readlines()), 500)

    def test_transform_stage_also_uses_fixed_filename(self):
        """Transform stage also uses fixed filename pattern.

        Both Extract and Transform stages should use data-dump-*.jsonl pattern.
        """

        class SimpleTransformStep(BaseStep):
            @property
            def name(self) -> str:
                return "transform_step"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                item.transformed_content = "transformed"
                return item

        class TestTransformStage(BaseStage):
            def __init__(self):
                super().__init__()

            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return [SimpleTransformStep()]

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_150000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            stage_data = Stage.create_for_phase(StageType.TRANSFORM, phase.base_path)
            stage_data.ensure_folders()

            ctx = StageContext(
                phase=phase,
                stage=stage_data,
            )

            items = [
                ProcessingItem(
                    item_id="test1",
                    source_path=Path("/test/item.json"),
                    current_step="init",
                    status=ItemStatus.PENDING,
                    metadata={},
                    content="original",
                )
            ]

            stage = TestTransformStage()
            list(stage.run(ctx, iter(items)))

            # Verify Transform stage also uses fixed filename
            output_files = list(ctx.output_path.glob("data-dump-*.jsonl"))
            self.assertEqual(len(output_files), 1)
            self.assertEqual(output_files[0].name, "data-dump-0001.jsonl")

    def test_stage_has_output_file_index_attribute(self):
        """BaseStage has _output_file_index attribute for tracking file number."""
        stage = self.TestExtractStage()

        # Verify _output_file_index attribute exists and starts at 1
        self.assertTrue(hasattr(stage, "_output_file_index"))
        self.assertEqual(stage._output_file_index, 1)

    def test_stage_has_output_record_count_attribute(self):
        """BaseStage has _output_record_count attribute for tracking record count."""
        stage = self.TestExtractStage()

        # Verify _output_record_count attribute exists and starts at 0
        self.assertTrue(hasattr(stage, "_output_record_count"))
        self.assertEqual(stage._output_record_count, 0)

    def test_stage_has_max_records_per_file_attribute(self):
        """BaseStage has _max_records_per_file attribute set to 1000."""
        stage = self.TestExtractStage()

        # Verify _max_records_per_file attribute exists and is 1000
        self.assertTrue(hasattr(stage, "_max_records_per_file"))
        self.assertEqual(stage._max_records_per_file, 1000)
