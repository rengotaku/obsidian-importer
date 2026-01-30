"""Tests for 1:N expanding step functionality.

Tests for:
- BaseStep.process() returning list[ProcessingItem] for 1:N expansion
- Empty list validation (must yield at least 1 item)
- Single item unchanged (1:1 processing)
- Expansion metadata tracking (parent_item_id, expansion_index, total_expanded)
"""

import tempfile
import unittest
from pathlib import Path


class TestExpandingStep(unittest.TestCase):
    """Test 1:N expansion step behavior (T018-T020)."""

    def test_step_returns_list_expands_items(self):
        """Step returning list expands 1 item to N items (T018)."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.stage import BaseStage, BaseStep, StageContext
        from src.etl.core.status import ItemStatus
        from src.etl.core.types import StageType

        # Create a step that expands 1 item to 3 items
        class ExpandStep(BaseStep):
            @property
            def name(self) -> str:
                return "expand_to_three"

            def process(self, item: ProcessingItem) -> list[ProcessingItem]:
                # Return 3 expanded items
                result = []
                for i in range(3):
                    expanded = ProcessingItem(
                        item_id=f"{item.item_id}_part{i}",
                        source_path=item.source_path,
                        current_step=self.name,
                        status=ItemStatus.PENDING,
                        metadata={
                            "parent_item_id": item.item_id,
                            "expansion_index": i,
                            "total_expanded": 3,
                        },
                        content=f"Expanded content {i}",
                    )
                    result.append(expanded)
                return result

        # Create a minimal stage using this step
        class ExpandStage(BaseStage):
            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return [ExpandStep()]

        # Create test context
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            output_path.mkdir()

            # Mock phase and stage for context
            from src.etl.core.stage import Stage

            stage_data = Stage(
                stage_type=StageType.TRANSFORM,
                input_path=Path(tmpdir) / "input",
                output_path=output_path,
            )

            # Mock minimal phase with base_path
            class MockPhase:
                def __init__(self):
                    self.base_path = Path(tmpdir) / "phase"
                    self.base_path.mkdir()
                    self.pipeline_stages_jsonl = self.base_path / "pipeline_stages.jsonl"

            ctx = StageContext(
                phase=MockPhase(),
                stage=stage_data,
                debug_mode=False,
            )

            # Run stage with 1 input item
            input_item = ProcessingItem(
                item_id="test_item",
                source_path=Path("test.txt"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={},
                content="Original content",
            )

            stage_impl = ExpandStage()
            results = list(stage_impl.run(ctx, iter([input_item])))

            # Should expand to 3 items
            self.assertEqual(len(results), 3)

            # Verify expansion metadata
            for i, result in enumerate(results):
                self.assertEqual(result.item_id, f"test_item_part{i}")
                self.assertEqual(result.metadata["parent_item_id"], "test_item")
                self.assertEqual(result.metadata["expansion_index"], i)
                self.assertEqual(result.metadata["total_expanded"], 3)
                self.assertEqual(result.content, f"Expanded content {i}")

    def test_step_returns_empty_list_raises(self):
        """Step returning empty list raises RuntimeError (T019)."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.stage import BaseStage, BaseStep, StageContext
        from src.etl.core.status import ItemStatus
        from src.etl.core.types import StageType

        # Create a step that returns empty list (invalid)
        class EmptyListStep(BaseStep):
            @property
            def name(self) -> str:
                return "empty_list"

            def process(self, item: ProcessingItem) -> list[ProcessingItem]:
                return []  # Invalid: must yield at least 1 item

        class EmptyListStage(BaseStage):
            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return [EmptyListStep()]

        # Create test context
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            output_path.mkdir()

            from src.etl.core.stage import Stage

            stage_data = Stage(
                stage_type=StageType.TRANSFORM,
                input_path=Path(tmpdir) / "input",
                output_path=output_path,
            )

            class MockPhase:
                def __init__(self):
                    self.base_path = Path(tmpdir) / "phase"
                    self.base_path.mkdir()
                    self.pipeline_stages_jsonl = self.base_path / "pipeline_stages.jsonl"

            ctx = StageContext(
                phase=MockPhase(),
                stage=stage_data,
                debug_mode=False,
            )

            input_item = ProcessingItem(
                item_id="test_item",
                source_path=Path("test.txt"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={},
                content="Original content",
            )

            stage_impl = EmptyListStage()

            # Should raise RuntimeError
            with self.assertRaises(RuntimeError) as cm:
                list(stage_impl.run(ctx, iter([input_item])))

            self.assertIn("empty list", str(cm.exception).lower())
            self.assertIn("empty_list", str(cm.exception))

    def test_step_returns_single_item_unchanged(self):
        """Step returning single item works as 1:1 processing (T020)."""
        from src.etl.core.models import ProcessingItem
        from src.etl.core.stage import BaseStage, BaseStep, StageContext
        from src.etl.core.status import ItemStatus
        from src.etl.core.types import StageType

        # Create a step that returns single item (1:1)
        class SingleItemStep(BaseStep):
            @property
            def name(self) -> str:
                return "single_item"

            def process(self, item: ProcessingItem) -> ProcessingItem:
                # Traditional 1:1 processing
                item.content = item.content + " processed"
                return item

        class SingleItemStage(BaseStage):
            @property
            def stage_type(self) -> StageType:
                return StageType.TRANSFORM

            @property
            def steps(self) -> list[BaseStep]:
                return [SingleItemStep()]

        # Create test context
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            output_path.mkdir()

            from src.etl.core.stage import Stage

            stage_data = Stage(
                stage_type=StageType.TRANSFORM,
                input_path=Path(tmpdir) / "input",
                output_path=output_path,
            )

            class MockPhase:
                def __init__(self):
                    self.base_path = Path(tmpdir) / "phase"
                    self.base_path.mkdir()
                    self.pipeline_stages_jsonl = self.base_path / "pipeline_stages.jsonl"

            ctx = StageContext(
                phase=MockPhase(),
                stage=stage_data,
                debug_mode=False,
            )

            input_item = ProcessingItem(
                item_id="test_item",
                source_path=Path("test.txt"),
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={},
                content="Original",
            )

            stage_impl = SingleItemStage()
            results = list(stage_impl.run(ctx, iter([input_item])))

            # Should return exactly 1 item
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].item_id, "test_item")
            self.assertEqual(results[0].content, "Original processed")

            # No expansion metadata added for 1:1 processing
            self.assertNotIn("parent_item_id", results[0].metadata)
            self.assertNotIn("expansion_index", results[0].metadata)
            self.assertNotIn("total_expanded", results[0].metadata)


if __name__ == "__main__":
    unittest.main()
