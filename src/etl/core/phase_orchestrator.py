"""BasePhaseOrchestrator - Template Method pattern for Phase execution.

Provides centralized Resume logic and ETL flow control for all Phase implementations.
"""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from src.etl.core.models import ProcessingItem
from src.etl.core.phase import Phase
from src.etl.core.types import PhaseType

logger = logging.getLogger(__name__)


class BasePhaseOrchestrator(ABC):
    """Base class for Phase execution using Template Method pattern.

    Responsibilities:
    - FW controls the ETL flow: Extract -> Transform -> Load
    - Resume detection and Extract output reuse
    - Subclasses implement only concrete stage hooks

    Subclass Requirements:
    - Implement phase_type property (PhaseType)
    - Implement _run_extract_stage() hook
    - Implement _run_transform_stage() hook
    - Implement _run_load_stage() hook

    Example:
        class ImportPhase(BasePhaseOrchestrator):
            @property
            def phase_type(self) -> PhaseType:
                return PhaseType.IMPORT

            def _run_extract_stage(self, ctx, items):
                extractor = ClaudeExtractor()
                return extractor.run(ctx, items)

            def _run_transform_stage(self, ctx, items):
                transformer = KnowledgeTransformer()
                return transformer.run(ctx, items)

            def _run_load_stage(self, ctx, items):
                loader = SessionLoader()
                return loader.run(ctx, items)
    """

    @property
    @abstractmethod
    def phase_type(self) -> PhaseType:
        """Phase type (IMPORT or ORGANIZE).

        Returns:
            PhaseType enum value.
        """
        ...

    @abstractmethod
    def _run_extract_stage(self, ctx, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
        """Execute Extract stage (hook for subclasses).

        Args:
            ctx: Stage context with phase, session, debug mode.
            items: Input items (usually empty iterator for discovery).

        Returns:
            Iterator of extracted ProcessingItem.
        """
        ...

    @abstractmethod
    def _run_transform_stage(
        self, ctx, items: Iterator[ProcessingItem]
    ) -> Iterator[ProcessingItem]:
        """Execute Transform stage (hook for subclasses).

        Args:
            ctx: Stage context.
            items: Items from Extract stage.

        Returns:
            Iterator of transformed ProcessingItem.
        """
        ...

    @abstractmethod
    def _run_load_stage(self, ctx, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
        """Execute Load stage (hook for subclasses).

        Args:
            ctx: Stage context.
            items: Items from Transform stage.

        Returns:
            Iterator of loaded ProcessingItem.
        """
        ...

    def _should_load_extract_from_output(self, phase_data: Phase) -> bool:
        """Check if Extract output exists (Resume mode detection).

        Args:
            phase_data: Phase data with base_path.

        Returns:
            True if data-dump-*.jsonl files exist in extract/output/.
            False otherwise.

        Exclusions:
            - steps.jsonl
            - error_details.jsonl
            - pipeline_stages.jsonl
        """
        extract_output = phase_data.base_path / "extract" / "output"
        if not extract_output.exists():
            return False

        # Find data-dump-*.jsonl files
        data_dump_files = list(extract_output.glob("data-dump-*.jsonl"))
        return len(data_dump_files) > 0

    def _load_extract_items_from_output(self, phase_data: Phase) -> Iterator[ProcessingItem]:
        """Restore ProcessingItem from Extract output JSONL files.

        Reads data-dump-*.jsonl in sorted order, deserializes each line to ProcessingItem.
        Skips corrupted JSON records.

        Args:
            phase_data: Phase data with base_path.

        Yields:
            ProcessingItem restored from JSONL.

        Exclusions:
            - steps.jsonl
            - error_details.jsonl
            - pipeline_stages.jsonl
        """
        extract_output = phase_data.base_path / "extract" / "output"
        if not extract_output.exists():
            return

        # Find data-dump-*.jsonl files and sort
        data_dump_files = sorted(extract_output.glob("data-dump-*.jsonl"))

        for jsonl_file in data_dump_files:
            with open(jsonl_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)
                        yield ProcessingItem.from_dict(record)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping corrupted JSON record in {jsonl_file}")
                        continue
                    except (KeyError, ValueError) as e:
                        logger.warning(
                            f"Skipping invalid ProcessingItem record in {jsonl_file}: {e}"
                        )
                        continue

    def run(self, phase_data: Phase, debug_mode: bool = False) -> "PhaseResult":
        """Execute Phase with Template Method pattern.

        Flow:
        1. Check if Extract output exists (Resume mode)
        2. Extract: Run _run_extract_stage() OR load from output
        3. Transform: Run _run_transform_stage()
        4. Load: Run _run_load_stage()
        5. Return PhaseResult

        Args:
            phase_data: Phase data with base_path, status, etc.
            debug_mode: Enable debug logging.

        Returns:
            PhaseResult with execution summary.
        """
        from src.etl.core.status import PhaseStatus
        from src.etl.phases.import_phase import PhaseResult

        # Mock context for stages (minimal implementation for tests)
        ctx = type(
            "StageContext",
            (),
            {
                "phase": phase_data,
                "debug_mode": debug_mode,
            },
        )()

        # Step 1: Check Resume mode
        should_resume = self._should_load_extract_from_output(phase_data)

        # Step 2: Extract (or Resume)
        if should_resume:
            logger.info("Resume mode: Loading from extract/output/*.jsonl")
            items = self._load_extract_items_from_output(phase_data)
        else:
            logger.info("Extract output not found, processing from input/")
            items = self._run_extract_stage(ctx, iter([]))

        # Step 3: Transform
        items = self._run_transform_stage(ctx, items)

        # Step 4: Load
        items = self._run_load_stage(ctx, items)

        # Consume iterator to complete execution
        _ = list(items)

        # Return PhaseResult (mock values for now)
        return PhaseResult(
            phase_type=self.phase_type,
            status=PhaseStatus.COMPLETED,
            items_processed=0,
            items_failed=0,
            items_skipped=0,
            duration_seconds=0.0,
        )
