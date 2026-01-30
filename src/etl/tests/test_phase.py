"""Tests for Phase and Stage management.

Tests for:
- Phase folder creation
- Stage folder creation (input/, output/)
- phase.json status tracking
- PhaseManager operations
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


class TestPhaseFolderCreation(unittest.TestCase):
    """Test Phase folder creation."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_phase_folder_created(self):
        """PhaseManager.create() creates phase folder."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType

        manager = PhaseManager(session_path=self.session_dir)
        phase = manager.create(PhaseType.IMPORT)

        # Phase folder exists
        self.assertTrue(phase.base_path.exists())
        self.assertTrue(phase.base_path.is_dir())
        self.assertEqual(phase.base_path.name, "import")

    def test_phase_folder_name_matches_type(self):
        """Phase folder name matches PhaseType value."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType

        manager = PhaseManager(session_path=self.session_dir)

        import_phase = manager.create(PhaseType.IMPORT)
        self.assertEqual(import_phase.base_path.name, "import")

        organize_phase = manager.create(PhaseType.ORGANIZE)
        self.assertEqual(organize_phase.base_path.name, "organize")

    def test_phase_has_status_file_path(self):
        """Phase has correct status_file path."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType

        manager = PhaseManager(session_path=self.session_dir)
        phase = manager.create(PhaseType.IMPORT)

        expected = phase.base_path / "phase.json"
        self.assertEqual(phase.status_file, expected)


class TestStageFolderCreation(unittest.TestCase):
    """Test Stage folder creation."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_stage_folders_created(self):
        """PhaseManager.create() creates all stage folders."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType, StageType

        manager = PhaseManager(session_path=self.session_dir)
        phase = manager.create(PhaseType.IMPORT)

        # All stage folders exist
        for stage_type in StageType:
            stage_path = phase.base_path / stage_type.value
            self.assertTrue(stage_path.exists(), f"{stage_type.value} folder missing")
            self.assertTrue(stage_path.is_dir())

    def test_extract_stage_has_input_output(self):
        """Extract stage has both input/ and output/ folders."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType, StageType

        manager = PhaseManager(session_path=self.session_dir)
        phase = manager.create(PhaseType.IMPORT)

        extract_path = phase.base_path / StageType.EXTRACT.value
        input_path = extract_path / "input"
        output_path = extract_path / "output"

        self.assertTrue(input_path.exists())
        self.assertTrue(output_path.exists())

    def test_transform_stage_has_output_only(self):
        """Transform stage has output/ folder only."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType, StageType

        manager = PhaseManager(session_path=self.session_dir)
        phase = manager.create(PhaseType.IMPORT)

        transform_path = phase.base_path / StageType.TRANSFORM.value
        output_path = transform_path / "output"

        # output exists
        self.assertTrue(output_path.exists())
        # input does NOT exist for transform
        input_path = transform_path / "input"
        self.assertFalse(input_path.exists())

    def test_load_stage_has_output_only(self):
        """Load stage has output/ folder only."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType, StageType

        manager = PhaseManager(session_path=self.session_dir)
        phase = manager.create(PhaseType.IMPORT)

        load_path = phase.base_path / StageType.LOAD.value
        output_path = load_path / "output"

        # output exists
        self.assertTrue(output_path.exists())
        # input does NOT exist for load
        input_path = load_path / "input"
        self.assertFalse(input_path.exists())


class TestPhaseJsonStatusTracking(unittest.TestCase):
    """Test phase.json status tracking."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_phase_json_created_on_save(self):
        """PhaseManager.save() creates phase.json."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType

        manager = PhaseManager(session_path=self.session_dir)
        phase = manager.create(PhaseType.IMPORT)
        manager.save(phase)

        self.assertTrue(phase.status_file.exists())

    def test_phase_json_contains_required_fields(self):
        """phase.json contains all required fields."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType
        from src.etl.core.status import PhaseStatus

        manager = PhaseManager(session_path=self.session_dir)
        phase = manager.create(PhaseType.IMPORT)
        phase.status = PhaseStatus.RUNNING
        manager.save(phase)

        with open(phase.status_file) as f:
            data = json.load(f)

        # Required fields
        self.assertIn("phase_type", data)
        self.assertIn("status", data)
        self.assertIn("started_at", data)
        self.assertIn("completed_at", data)
        self.assertIn("error_count", data)
        self.assertIn("success_count", data)

    def test_phase_json_tracks_step_status(self):
        """phase.json tracks step-level status."""
        from src.etl.core.phase import Phase, PhaseManager
        from src.etl.core.types import PhaseType
        from src.etl.core.step import Step
        from src.etl.core.status import StepStatus

        manager = PhaseManager(session_path=self.session_dir)
        phase = manager.create(PhaseType.IMPORT)

        # Add steps to phase
        step1 = Step(step_name="parse_json", status=StepStatus.COMPLETED)
        step2 = Step(step_name="validate", status=StepStatus.RUNNING)
        phase.steps.append(step1)
        phase.steps.append(step2)

        manager.save(phase)

        with open(phase.status_file) as f:
            data = json.load(f)

        self.assertIn("steps", data)
        self.assertEqual(len(data["steps"]), 2)
        self.assertEqual(data["steps"][0]["step_name"], "parse_json")
        self.assertEqual(data["steps"][0]["status"], "completed")
        self.assertEqual(data["steps"][1]["step_name"], "validate")
        self.assertEqual(data["steps"][1]["status"], "running")

    def test_phase_status_update_persists(self):
        """Phase status changes are persisted to phase.json."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType
        from src.etl.core.status import PhaseStatus

        manager = PhaseManager(session_path=self.session_dir)
        phase = manager.create(PhaseType.IMPORT)

        # Initial save
        phase.status = PhaseStatus.PENDING
        manager.save(phase)

        # Update status
        phase.status = PhaseStatus.RUNNING
        phase.error_count = 1
        phase.success_count = 5
        manager.save(phase)

        # Verify persistence
        with open(phase.status_file) as f:
            data = json.load(f)

        self.assertEqual(data["status"], "running")
        self.assertEqual(data["error_count"], 1)
        self.assertEqual(data["success_count"], 5)

    def test_phase_load_from_json(self):
        """PhaseManager.load() reads phase from phase.json."""
        from src.etl.core.phase import PhaseManager
        from src.etl.core.types import PhaseType
        from src.etl.core.status import PhaseStatus

        manager = PhaseManager(session_path=self.session_dir)

        # Create and save
        original = manager.create(PhaseType.IMPORT)
        original.status = PhaseStatus.COMPLETED
        original.error_count = 2
        original.success_count = 10
        manager.save(original)

        # Load
        loaded = manager.load(PhaseType.IMPORT)

        self.assertEqual(loaded.phase_type, PhaseType.IMPORT)
        self.assertEqual(loaded.status, PhaseStatus.COMPLETED)
        self.assertEqual(loaded.error_count, 2)
        self.assertEqual(loaded.success_count, 10)


class TestPhaseDataclass(unittest.TestCase):
    """Test Phase dataclass."""

    def test_phase_creation_with_defaults(self):
        """Phase can be created with minimal arguments."""
        from src.etl.core.phase import Phase
        from src.etl.core.types import PhaseType
        from src.etl.core.status import PhaseStatus

        phase = Phase(
            phase_type=PhaseType.IMPORT,
            base_path=Path("/tmp/test/import"),
        )

        self.assertEqual(phase.phase_type, PhaseType.IMPORT)
        self.assertEqual(phase.status, PhaseStatus.PENDING)
        self.assertEqual(phase.stages, {})
        self.assertIsNone(phase.started_at)
        self.assertIsNone(phase.completed_at)
        self.assertEqual(phase.error_count, 0)
        self.assertEqual(phase.success_count, 0)

    def test_phase_status_file_path(self):
        """Phase.status_file returns correct path."""
        from src.etl.core.phase import Phase
        from src.etl.core.types import PhaseType

        phase = Phase(
            phase_type=PhaseType.IMPORT,
            base_path=Path("/tmp/test/import"),
        )

        self.assertEqual(phase.status_file, Path("/tmp/test/import/phase.json"))

    def test_phase_to_dict(self):
        """Phase.to_dict() returns correct dictionary."""
        from src.etl.core.phase import Phase
        from src.etl.core.types import PhaseType
        from src.etl.core.status import PhaseStatus

        started = datetime(2026, 1, 19, 14, 30, 52)
        phase = Phase(
            phase_type=PhaseType.IMPORT,
            status=PhaseStatus.RUNNING,
            started_at=started,
            error_count=1,
            success_count=5,
            base_path=Path("/tmp/test/import"),
        )

        d = phase.to_dict()

        self.assertEqual(d["phase_type"], "import")
        self.assertEqual(d["status"], "running")
        self.assertEqual(d["started_at"], "2026-01-19T14:30:52")
        self.assertIsNone(d["completed_at"])
        self.assertEqual(d["error_count"], 1)
        self.assertEqual(d["success_count"], 5)


class TestStageDataclass(unittest.TestCase):
    """Test Stage dataclass."""

    def test_stage_creation(self):
        """Stage can be created with required arguments."""
        from src.etl.core.stage import Stage
        from src.etl.core.types import StageType
        from src.etl.core.status import StageStatus

        stage = Stage(
            stage_type=StageType.EXTRACT,
            input_path=Path("/tmp/extract/input"),
            output_path=Path("/tmp/extract/output"),
        )

        self.assertEqual(stage.stage_type, StageType.EXTRACT)
        self.assertEqual(stage.status, StageStatus.PENDING)
        self.assertEqual(stage.steps, [])
        self.assertEqual(stage.items, [])

    def test_stage_paths(self):
        """Stage has correct input/output paths."""
        from src.etl.core.stage import Stage
        from src.etl.core.types import StageType

        stage = Stage(
            stage_type=StageType.EXTRACT,
            input_path=Path("/tmp/session/import/extract/input"),
            output_path=Path("/tmp/session/import/extract/output"),
        )

        self.assertEqual(stage.input_path.name, "input")
        self.assertEqual(stage.output_path.name, "output")


class TestStepDataclass(unittest.TestCase):
    """Test Step dataclass."""

    def test_step_creation_with_defaults(self):
        """Step can be created with minimal arguments."""
        from src.etl.core.step import Step
        from src.etl.core.status import StepStatus

        step = Step(step_name="parse_json")

        self.assertEqual(step.step_name, "parse_json")
        self.assertEqual(step.status, StepStatus.PENDING)
        self.assertIsNone(step.started_at)
        self.assertIsNone(step.completed_at)
        self.assertIsNone(step.duration_ms)
        self.assertIsNone(step.error)
        self.assertEqual(step.items_processed, 0)
        self.assertEqual(step.items_failed, 0)

    def test_step_to_dict(self):
        """Step.to_dict() returns correct dictionary."""
        from src.etl.core.step import Step
        from src.etl.core.status import StepStatus

        started = datetime(2026, 1, 19, 14, 30, 52)
        completed = datetime(2026, 1, 19, 14, 31, 0)
        step = Step(
            step_name="validate",
            status=StepStatus.COMPLETED,
            started_at=started,
            completed_at=completed,
            duration_ms=8000,
            items_processed=10,
            items_failed=0,
        )

        d = step.to_dict()

        self.assertEqual(d["step_name"], "validate")
        self.assertEqual(d["status"], "completed")
        self.assertEqual(d["started_at"], "2026-01-19T14:30:52")
        self.assertEqual(d["completed_at"], "2026-01-19T14:31:00")
        self.assertEqual(d["duration_ms"], 8000)
        self.assertEqual(d["items_processed"], 10)
        self.assertEqual(d["items_failed"], 0)


class TestStepTracker(unittest.TestCase):
    """Test StepTracker for timing and status updates."""

    def test_step_tracker_start(self):
        """StepTracker.start() sets started_at and status."""
        from src.etl.core.step import Step, StepTracker
        from src.etl.core.status import StepStatus

        step = Step(step_name="test_step")
        tracker = StepTracker(step)

        tracker.start()

        self.assertIsNotNone(step.started_at)
        self.assertEqual(step.status, StepStatus.RUNNING)

    def test_step_tracker_complete_success(self):
        """StepTracker.complete() sets completed_at and duration."""
        from src.etl.core.step import Step, StepTracker
        from src.etl.core.status import StepStatus
        import time

        step = Step(step_name="test_step")
        tracker = StepTracker(step)

        tracker.start()
        time.sleep(0.01)  # 10ms
        tracker.complete(items_processed=5, items_failed=0)

        self.assertIsNotNone(step.completed_at)
        self.assertEqual(step.status, StepStatus.COMPLETED)
        self.assertGreater(step.duration_ms, 0)
        self.assertEqual(step.items_processed, 5)
        self.assertEqual(step.items_failed, 0)

    def test_step_tracker_fail(self):
        """StepTracker.fail() sets error and status."""
        from src.etl.core.step import Step, StepTracker
        from src.etl.core.status import StepStatus

        step = Step(step_name="test_step")
        tracker = StepTracker(step)

        tracker.start()
        tracker.fail(error="Connection timeout", items_processed=3, items_failed=2)

        self.assertEqual(step.status, StepStatus.FAILED)
        self.assertEqual(step.error, "Connection timeout")
        self.assertEqual(step.items_processed, 3)
        self.assertEqual(step.items_failed, 2)


if __name__ == "__main__":
    unittest.main()
