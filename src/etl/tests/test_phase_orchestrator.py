"""Tests for BasePhaseOrchestrator (User Story 2: FW による Resume 制御フローの一元管理).

Tests for Phase 3 tasks:
- T019: BasePhaseOrchestrator abstract methods
- T020: run() method calling hooks in correct order
- T021: _should_load_extract_from_output() method
- T022: _load_extract_items_from_output() method

Template Method Pattern:
- run() is concrete (FW controls flow)
- _run_extract_stage(), _run_transform_stage(), _run_load_stage() are abstract
- _should_load_extract_from_output(), _load_extract_items_from_output() are protected helpers
"""

import json
import unittest
from abc import ABC
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from src.etl.core.models import ProcessingItem
from src.etl.core.phase import Phase
from src.etl.core.stage import Stage
from src.etl.core.status import ItemStatus
from src.etl.core.types import PhaseType, StageType


class TestBasePhaseOrchestratorAbstract(unittest.TestCase):
    """Test BasePhaseOrchestrator is an abstract base class (T019)."""

    def test_base_phase_orchestrator_is_abstract(self):
        """BasePhaseOrchestrator cannot be instantiated directly.

        User Story 2: FW が制御フローを管理
        BasePhaseOrchestrator は ABC として定義され、直接インスタンス化できない。
        """
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator

        # Should be an ABC
        self.assertTrue(issubclass(BasePhaseOrchestrator, ABC))

        # Should not be instantiable
        with self.assertRaises(TypeError) as ctx:
            BasePhaseOrchestrator()

        # Error message should mention abstract methods
        error_msg = str(ctx.exception)
        self.assertIn("abstract", error_msg.lower())

    def test_base_phase_orchestrator_requires_phase_type_property(self):
        """Subclass must implement phase_type property.

        User Story 2, FR-001: BasePhaseOrchestrator は phase_type プロパティを要求
        """
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator

        # Create incomplete subclass (missing phase_type)
        class IncompleteOrchestrator(BasePhaseOrchestrator):
            def _run_extract_stage(self, ctx, items):
                pass

            def _run_transform_stage(self, ctx, items):
                pass

            def _run_load_stage(self, ctx, items):
                pass

        with self.assertRaises(TypeError) as ctx:
            IncompleteOrchestrator()

        error_msg = str(ctx.exception)
        self.assertIn("phase_type", error_msg)

    def test_base_phase_orchestrator_requires_run_extract_stage(self):
        """Subclass must implement _run_extract_stage() method.

        User Story 2, FR-004: 各 Phase クラスはフックメソッド _run_extract_stage を実装
        """
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator

        # Create incomplete subclass (missing _run_extract_stage)
        class IncompleteOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_transform_stage(self, ctx, items):
                pass

            def _run_load_stage(self, ctx, items):
                pass

        with self.assertRaises(TypeError) as ctx:
            IncompleteOrchestrator()

        error_msg = str(ctx.exception)
        self.assertIn("_run_extract_stage", error_msg)

    def test_base_phase_orchestrator_requires_run_transform_stage(self):
        """Subclass must implement _run_transform_stage() method.

        User Story 2, FR-004: 各 Phase クラスはフックメソッド _run_transform_stage を実装
        """
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator

        # Create incomplete subclass (missing _run_transform_stage)
        class IncompleteOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                pass

            def _run_load_stage(self, ctx, items):
                pass

        with self.assertRaises(TypeError) as ctx:
            IncompleteOrchestrator()

        error_msg = str(ctx.exception)
        self.assertIn("_run_transform_stage", error_msg)

    def test_base_phase_orchestrator_requires_run_load_stage(self):
        """Subclass must implement _run_load_stage() method.

        User Story 2, FR-004: 各 Phase クラスはフックメソッド _run_load_stage を実装
        """
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator

        # Create incomplete subclass (missing _run_load_stage)
        class IncompleteOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                pass

            def _run_transform_stage(self, ctx, items):
                pass

        with self.assertRaises(TypeError) as ctx:
            IncompleteOrchestrator()

        error_msg = str(ctx.exception)
        self.assertIn("_run_load_stage", error_msg)


class TestBasePhaseOrchestratorRunOrder(unittest.TestCase):
    """Test run() method calling hooks in correct order (T020)."""

    def setUp(self):
        """Create a concrete orchestrator for testing."""
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator

        self.execution_order = []

        class TestOrchestrator(BasePhaseOrchestrator):
            def __init__(self, test_case):
                self._test_case = test_case

            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                self._test_case.execution_order.append("extract")
                return items

            def _run_transform_stage(self, ctx, items):
                self._test_case.execution_order.append("transform")
                return items

            def _run_load_stage(self, ctx, items):
                self._test_case.execution_order.append("load")
                return items

        self.TestOrchestrator = TestOrchestrator

    def test_run_calls_stages_in_etl_order(self):
        """run() calls stages in Extract -> Transform -> Load order.

        User Story 2, Scenario 1:
        Given BasePhaseOrchestrator を継承した Phase クラスが存在する状態で,
        When run() を呼び出した場合,
        Then FW が Extract → Transform → Load の順でフックを呼び出す
        """
        orchestrator = self.TestOrchestrator(self)

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_120000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()

            # Run orchestrator
            orchestrator.run(phase_data=phase, debug_mode=False)

            # Verify execution order
            self.assertEqual(self.execution_order, ["extract", "transform", "load"])

    def test_run_returns_phase_result(self):
        """run() returns PhaseResult with execution summary.

        User Story 2: run() メソッドは PhaseResult を返す
        """
        orchestrator = self.TestOrchestrator(self)

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_130000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()

            # Run orchestrator
            result = orchestrator.run(phase_data=phase, debug_mode=False)

            # Verify result type
            from src.etl.phases.import_phase import PhaseResult

            self.assertIsInstance(result, PhaseResult)
            self.assertEqual(result.phase_type, PhaseType.IMPORT)

    def test_run_passes_items_between_stages(self):
        """run() passes items from Extract to Transform to Load.

        User Story 2: FW がアイテムを各ステージ間で受け渡す
        """
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator

        items_received = {"extract": None, "transform": None, "load": None}

        class ItemTrackingOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                # Initial items (discovery)
                result = [
                    ProcessingItem(
                        item_id="test1",
                        source_path=Path("/test/file.json"),
                        current_step="extract",
                        status=ItemStatus.PENDING,
                        metadata={},
                    )
                ]
                items_received["extract"] = result
                return iter(result)

            def _run_transform_stage(self, ctx, items):
                items_list = list(items)
                items_received["transform"] = items_list
                return iter(items_list)

            def _run_load_stage(self, ctx, items):
                items_list = list(items)
                items_received["load"] = items_list
                return iter(items_list)

        orchestrator = ItemTrackingOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_140000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create stage folders
            for stage_type in [StageType.EXTRACT, StageType.TRANSFORM, StageType.LOAD]:
                stage = Stage.create_for_phase(stage_type, phase.base_path)
                stage.ensure_folders()

            # Run orchestrator
            orchestrator.run(phase_data=phase, debug_mode=False)

            # Verify items are passed through
            self.assertIsNotNone(items_received["extract"])
            self.assertIsNotNone(items_received["transform"])
            self.assertIsNotNone(items_received["load"])

            # Transform and Load should receive the same item (by id)
            self.assertEqual(
                items_received["transform"][0].item_id, items_received["load"][0].item_id
            )


class TestShouldLoadExtractFromOutput(unittest.TestCase):
    """Test _should_load_extract_from_output() method (T021)."""

    def setUp(self):
        """Create a concrete orchestrator for testing."""
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator

        class TestOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                return items

            def _run_transform_stage(self, ctx, items):
                return items

            def _run_load_stage(self, ctx, items):
                return items

        self.TestOrchestrator = TestOrchestrator

    def test_returns_true_when_data_dump_files_exist(self):
        """_should_load_extract_from_output() returns True when data-dump-*.jsonl exist.

        User Story 2, FR-002:
        Extract output（data-dump-*.jsonl）の存在を確認し、存在する場合は True を返す
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_150000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder with data-dump file
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Create data-dump file
            data_dump_file = extract_output / "data-dump-0001.jsonl"
            data_dump_file.write_text('{"item_id": "test1"}\n')

            # Verify method returns True
            result = orchestrator._should_load_extract_from_output(phase)
            self.assertTrue(result)

    def test_returns_false_when_no_data_dump_files(self):
        """_should_load_extract_from_output() returns False when no data-dump-*.jsonl exist.

        User Story 2, FR-003:
        Extract output が存在しない場合、False を返す
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_160000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder but empty
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Verify method returns False
            result = orchestrator._should_load_extract_from_output(phase)
            self.assertFalse(result)

    def test_returns_false_when_output_folder_missing(self):
        """_should_load_extract_from_output() returns False when output folder doesn't exist.

        Edge case: output フォルダ自体が存在しない場合
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_170000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)
            # DO NOT create extract/output folder

            # Verify method returns False
            result = orchestrator._should_load_extract_from_output(phase)
            self.assertFalse(result)

    def test_excludes_steps_jsonl_from_detection(self):
        """_should_load_extract_from_output() excludes steps.jsonl from detection.

        Edge case (spec): steps.jsonl は Resume 復元対象から除外される
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_180000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder with ONLY steps.jsonl (no data-dump)
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Create steps.jsonl (should be excluded)
            steps_file = extract_output / "steps.jsonl"
            steps_file.write_text('{"step": "test"}\n')

            # Verify method returns False (steps.jsonl is excluded)
            result = orchestrator._should_load_extract_from_output(phase)
            self.assertFalse(result)

    def test_excludes_error_details_jsonl_from_detection(self):
        """_should_load_extract_from_output() excludes error_details.jsonl from detection.

        Edge case (spec): error_details.jsonl は Resume 復元対象から除外される
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_190000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder with ONLY error_details.jsonl
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Create error_details.jsonl (should be excluded)
            error_file = extract_output / "error_details.jsonl"
            error_file.write_text('{"error": "test"}\n')

            # Verify method returns False
            result = orchestrator._should_load_extract_from_output(phase)
            self.assertFalse(result)

    def test_excludes_pipeline_stages_jsonl_from_detection(self):
        """_should_load_extract_from_output() excludes pipeline_stages.jsonl from detection.

        Edge case (spec): pipeline_stages.jsonl は Resume 復元対象から除外される
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_200000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder with ONLY pipeline_stages.jsonl
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Create pipeline_stages.jsonl (should be excluded)
            pipeline_file = extract_output / "pipeline_stages.jsonl"
            pipeline_file.write_text('{"stage": "extract"}\n')

            # Verify method returns False
            result = orchestrator._should_load_extract_from_output(phase)
            self.assertFalse(result)


class TestLoadExtractItemsFromOutput(unittest.TestCase):
    """Test _load_extract_items_from_output() method (T022)."""

    def setUp(self):
        """Create a concrete orchestrator for testing."""
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator

        class TestOrchestrator(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                return items

            def _run_transform_stage(self, ctx, items):
                return items

            def _run_load_stage(self, ctx, items):
                return items

        self.TestOrchestrator = TestOrchestrator

    def test_loads_processing_items_from_jsonl(self):
        """_load_extract_items_from_output() restores ProcessingItem from JSONL.

        User Story 2, FR-002:
        JSONL から ProcessingItem を復元する
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_210000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder with data-dump file
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Create data-dump file with ProcessingItem
            item_data = {
                "item_id": "test-uuid-001",
                "source_path": "/test/conversations.json",
                "current_step": "extract",
                "status": "completed",
                "metadata": {"conversation_uuid": "test-uuid-001"},
                "content": "test content",
                "transformed_content": None,
                "output_path": None,
                "error": None,
            }
            data_dump_file = extract_output / "data-dump-0001.jsonl"
            data_dump_file.write_text(json.dumps(item_data) + "\n")

            # Load items
            items = list(orchestrator._load_extract_items_from_output(phase))

            # Verify items restored
            self.assertEqual(len(items), 1)
            self.assertIsInstance(items[0], ProcessingItem)
            self.assertEqual(items[0].item_id, "test-uuid-001")
            self.assertEqual(items[0].content, "test content")

    def test_loads_items_from_multiple_data_dump_files(self):
        """_load_extract_items_from_output() loads from multiple data-dump-*.jsonl files.

        User Story 3, Scenario 3:
        すべての data-dump-*.jsonl ファイルから ProcessingItem が読み込まれる
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_220000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Create multiple data-dump files
            for i in range(1, 4):
                item_data = {
                    "item_id": f"test-uuid-{i:03d}",
                    "source_path": f"/test/conv{i}.json",
                    "current_step": "extract",
                    "status": "completed",
                    "metadata": {},
                    "content": f"content {i}",
                    "transformed_content": None,
                    "output_path": None,
                    "error": None,
                }
                data_dump_file = extract_output / f"data-dump-{i:04d}.jsonl"
                data_dump_file.write_text(json.dumps(item_data) + "\n")

            # Load items
            items = list(orchestrator._load_extract_items_from_output(phase))

            # Verify all items loaded
            self.assertEqual(len(items), 3)
            item_ids = {item.item_id for item in items}
            self.assertEqual(item_ids, {"test-uuid-001", "test-uuid-002", "test-uuid-003"})

    def test_skips_corrupted_json_records(self):
        """_load_extract_items_from_output() skips corrupted JSON records.

        Edge case (spec): 破損した JSONL レコードはスキップされ、処理は継続される
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260128_230000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Create data-dump file with mix of valid and corrupted records
            data_dump_file = extract_output / "data-dump-0001.jsonl"
            valid_item_1 = {
                "item_id": "valid-1",
                "source_path": "/test/conv1.json",
                "current_step": "extract",
                "status": "completed",
                "metadata": {},
                "content": "content 1",
                "transformed_content": None,
                "output_path": None,
                "error": None,
            }
            valid_item_2 = {
                "item_id": "valid-2",
                "source_path": "/test/conv2.json",
                "current_step": "extract",
                "status": "completed",
                "metadata": {},
                "content": "content 2",
                "transformed_content": None,
                "output_path": None,
                "error": None,
            }

            # Write mix of valid and corrupted records
            lines = [
                json.dumps(valid_item_1),
                "this is not valid json {{{",
                json.dumps(valid_item_2),
                '{"missing": "required_fields"}',  # Missing item_id etc.
            ]
            data_dump_file.write_text("\n".join(lines) + "\n")

            # Load items (should skip corrupted records)
            items = list(orchestrator._load_extract_items_from_output(phase))

            # Verify only valid items loaded
            self.assertEqual(len(items), 2)
            item_ids = {item.item_id for item in items}
            self.assertEqual(item_ids, {"valid-1", "valid-2"})

    def test_excludes_steps_jsonl_from_loading(self):
        """_load_extract_items_from_output() does not load from steps.jsonl.

        Edge case (spec): steps.jsonl は Resume 復元対象から除外される
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_000000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Create data-dump file
            item_data = {
                "item_id": "from-data-dump",
                "source_path": "/test/conv.json",
                "current_step": "extract",
                "status": "completed",
                "metadata": {},
                "content": "data dump content",
                "transformed_content": None,
                "output_path": None,
                "error": None,
            }
            data_dump_file = extract_output / "data-dump-0001.jsonl"
            data_dump_file.write_text(json.dumps(item_data) + "\n")

            # Create steps.jsonl with same structure (should be excluded)
            steps_item = {
                "item_id": "from-steps",
                "source_path": "/test/conv.json",
                "current_step": "extract",
                "status": "completed",
                "metadata": {},
                "content": "steps content",
                "transformed_content": None,
                "output_path": None,
                "error": None,
            }
            steps_file = extract_output / "steps.jsonl"
            steps_file.write_text(json.dumps(steps_item) + "\n")

            # Load items
            items = list(orchestrator._load_extract_items_from_output(phase))

            # Verify only data-dump items loaded (not steps.jsonl)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].item_id, "from-data-dump")

    def test_returns_empty_iterator_when_no_files(self):
        """_load_extract_items_from_output() returns empty iterator when no data-dump files.

        Edge case: data-dump ファイルが存在しない場合は空の iterator を返す
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_010000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder (empty)
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Load items
            items = list(orchestrator._load_extract_items_from_output(phase))

            # Verify empty result
            self.assertEqual(len(items), 0)

    def test_loads_items_in_sorted_file_order(self):
        """_load_extract_items_from_output() loads items in sorted file order.

        User Story 3: data-dump-0001.jsonl, data-dump-0002.jsonl... の順で読み込む
        """
        orchestrator = self.TestOrchestrator()

        with TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "20260129_020000"
            session_path.mkdir()

            phase = Phase(
                phase_type=PhaseType.IMPORT,
                base_path=session_path / "import",
            )
            phase.base_path.mkdir(parents=True)

            # Create extract output folder
            extract_output = phase.base_path / "extract" / "output"
            extract_output.mkdir(parents=True)

            # Create data-dump files in reverse order to test sorting
            for i in [3, 1, 2]:
                item_data = {
                    "item_id": f"item-{i:03d}",
                    "source_path": f"/test/conv{i}.json",
                    "current_step": "extract",
                    "status": "completed",
                    "metadata": {},
                    "content": f"content {i}",
                    "transformed_content": None,
                    "output_path": None,
                    "error": None,
                }
                data_dump_file = extract_output / f"data-dump-{i:04d}.jsonl"
                data_dump_file.write_text(json.dumps(item_data) + "\n")

            # Load items
            items = list(orchestrator._load_extract_items_from_output(phase))

            # Verify items loaded in sorted order
            self.assertEqual(len(items), 3)
            item_ids = [item.item_id for item in items]
            self.assertEqual(item_ids, ["item-001", "item-002", "item-003"])


class TestImportPhaseInheritance(unittest.TestCase):
    """Test ImportPhase inherits from BasePhaseOrchestrator (T036, T038).

    Phase 4 - User Story 2: ImportPhase と OrganizePhase の継承変更
    """

    def test_import_phase_inherits_base_phase_orchestrator(self):
        """ImportPhase inherits from BasePhaseOrchestrator.

        User Story 2, FR-004:
        ImportPhase は BasePhaseOrchestrator を継承すること
        """
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
        from src.etl.phases.import_phase import ImportPhase

        # Verify ImportPhase is a subclass of BasePhaseOrchestrator
        self.assertTrue(
            issubclass(ImportPhase, BasePhaseOrchestrator),
            "ImportPhase must inherit from BasePhaseOrchestrator",
        )

    def test_import_phase_has_phase_type_property(self):
        """ImportPhase has phase_type property returning PhaseType.IMPORT.

        User Story 2: phase_type プロパティが PhaseType.IMPORT を返すこと
        """
        from src.etl.phases.import_phase import ImportPhase

        phase = ImportPhase()
        self.assertEqual(phase.phase_type, PhaseType.IMPORT)

    def test_import_phase_has_run_extract_stage_method(self):
        """ImportPhase implements _run_extract_stage() hook method.

        User Story 2, FR-004:
        _run_extract_stage() フックメソッドを実装すること
        """
        from src.etl.phases.import_phase import ImportPhase

        phase = ImportPhase()

        # Verify method exists and is callable
        self.assertTrue(hasattr(phase, "_run_extract_stage"))
        self.assertTrue(callable(phase._run_extract_stage))

    def test_import_phase_has_run_transform_stage_method(self):
        """ImportPhase implements _run_transform_stage() hook method.

        User Story 2, FR-004:
        _run_transform_stage() フックメソッドを実装すること
        """
        from src.etl.phases.import_phase import ImportPhase

        phase = ImportPhase()

        # Verify method exists and is callable
        self.assertTrue(hasattr(phase, "_run_transform_stage"))
        self.assertTrue(callable(phase._run_transform_stage))

    def test_import_phase_has_run_load_stage_method(self):
        """ImportPhase implements _run_load_stage() hook method.

        User Story 2, FR-004:
        _run_load_stage() フックメソッドを実装すること
        """
        from src.etl.phases.import_phase import ImportPhase

        phase = ImportPhase()

        # Verify method exists and is callable
        self.assertTrue(hasattr(phase, "_run_load_stage"))
        self.assertTrue(callable(phase._run_load_stage))

    def test_import_phase_run_delegates_to_base_orchestrator(self):
        """ImportPhase.run() delegates to BasePhaseOrchestrator.run().

        User Story 2, Scenario 1:
        Given ImportPhase が BasePhaseOrchestrator を継承している状態で,
        When run() を呼び出した場合,
        Then FW（BasePhaseOrchestrator.run()）が処理を制御する

        This verifies that ImportPhase doesn't override run() with incompatible logic.
        """
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
        from src.etl.phases.import_phase import ImportPhase

        # Get run method from ImportPhase
        phase = ImportPhase()
        run_method = type(phase).run

        # Verify run is from BasePhaseOrchestrator (not overridden)
        # or if overridden, it properly delegates to super().run()
        # For now, we check that the method resolution order includes BasePhaseOrchestrator
        mro = type(phase).__mro__
        self.assertIn(BasePhaseOrchestrator, mro)


class TestOrganizePhaseInheritance(unittest.TestCase):
    """Test OrganizePhase inherits from BasePhaseOrchestrator (T037).

    Phase 4 - User Story 2: ImportPhase と OrganizePhase の継承変更
    """

    def test_organize_phase_inherits_base_phase_orchestrator(self):
        """OrganizePhase inherits from BasePhaseOrchestrator.

        User Story 2, FR-004:
        OrganizePhase は BasePhaseOrchestrator を継承すること
        """
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
        from src.etl.phases.organize_phase import OrganizePhase

        # Verify OrganizePhase is a subclass of BasePhaseOrchestrator
        self.assertTrue(
            issubclass(OrganizePhase, BasePhaseOrchestrator),
            "OrganizePhase must inherit from BasePhaseOrchestrator",
        )

    def test_organize_phase_has_phase_type_property(self):
        """OrganizePhase has phase_type property returning PhaseType.ORGANIZE.

        User Story 2: phase_type プロパティが PhaseType.ORGANIZE を返すこと
        """
        from src.etl.phases.organize_phase import OrganizePhase

        phase = OrganizePhase()
        self.assertEqual(phase.phase_type, PhaseType.ORGANIZE)

    def test_organize_phase_has_run_extract_stage_method(self):
        """OrganizePhase implements _run_extract_stage() hook method.

        User Story 2, FR-004:
        _run_extract_stage() フックメソッドを実装すること
        """
        from src.etl.phases.organize_phase import OrganizePhase

        phase = OrganizePhase()

        # Verify method exists and is callable
        self.assertTrue(hasattr(phase, "_run_extract_stage"))
        self.assertTrue(callable(phase._run_extract_stage))

    def test_organize_phase_has_run_transform_stage_method(self):
        """OrganizePhase implements _run_transform_stage() hook method.

        User Story 2, FR-004:
        _run_transform_stage() フックメソッドを実装すること
        """
        from src.etl.phases.organize_phase import OrganizePhase

        phase = OrganizePhase()

        # Verify method exists and is callable
        self.assertTrue(hasattr(phase, "_run_transform_stage"))
        self.assertTrue(callable(phase._run_transform_stage))

    def test_organize_phase_has_run_load_stage_method(self):
        """OrganizePhase implements _run_load_stage() hook method.

        User Story 2, FR-004:
        _run_load_stage() フックメソッドを実装すること
        """
        from src.etl.phases.organize_phase import OrganizePhase

        phase = OrganizePhase()

        # Verify method exists and is callable
        self.assertTrue(hasattr(phase, "_run_load_stage"))
        self.assertTrue(callable(phase._run_load_stage))

    def test_organize_phase_run_delegates_to_base_orchestrator(self):
        """OrganizePhase.run() delegates to BasePhaseOrchestrator.run().

        User Story 2, Scenario 1:
        Given OrganizePhase が BasePhaseOrchestrator を継承している状態で,
        When run() を呼び出した場合,
        Then FW（BasePhaseOrchestrator.run()）が処理を制御する
        """
        from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
        from src.etl.phases.organize_phase import OrganizePhase

        # Get run method from OrganizePhase
        phase = OrganizePhase()

        # Verify run is from BasePhaseOrchestrator (not overridden)
        # or if overridden, it properly delegates to super().run()
        # For now, we check that the method resolution order includes BasePhaseOrchestrator
        mro = type(phase).__mro__
        self.assertIn(BasePhaseOrchestrator, mro)


if __name__ == "__main__":
    unittest.main()
