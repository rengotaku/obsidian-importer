"""OrganizePhase orchestration for ETL pipeline.

Orchestrates: FileExtractor -> NormalizerTransformer -> VaultLoader
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from src.etl.core.models import ProcessingItem
from src.etl.core.phase import Phase
from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
from src.etl.core.stage import BaseStage, StageContext
from src.etl.core.status import ItemStatus, PhaseStatus
from src.etl.core.types import PhaseType, StageType
from src.etl.stages.extract.file_extractor import FileExtractor
from src.etl.stages.load.vault_loader import VaultLoader
from src.etl.stages.transform.normalizer_transformer import NormalizerTransformer

if TYPE_CHECKING:
    from src.etl.core.session import SessionManager


@dataclass
class PhaseResult:
    """Result of Phase execution."""

    phase_type: PhaseType
    status: PhaseStatus
    items_processed: int
    items_failed: int
    duration_seconds: float


class OrganizePhase(BasePhaseOrchestrator):
    """Organize Phase orchestration.

    Processes Markdown files through:
    - Extract: FileExtractor (file reading, frontmatter parsing)
    - Transform: NormalizerTransformer (normalization, genre classification)
    - Load: VaultLoader (move to appropriate vault)
    """

    def __init__(self, vaults_path: Path | None = None):
        """Initialize OrganizePhase.

        Args:
            vaults_path: Base path for vault folders.
        """
        self._vaults_path = vaults_path

    @property
    def phase_type(self) -> PhaseType:
        """Phase type is ORGANIZE."""
        return PhaseType.ORGANIZE

    def create_extract_stage(self) -> BaseStage:
        """Create FileExtractor stage."""
        return FileExtractor()

    def create_transform_stage(self) -> BaseStage:
        """Create NormalizerTransformer stage."""
        return NormalizerTransformer()

    def create_load_stage(self) -> BaseStage:
        """Create VaultLoader stage."""
        return VaultLoader(vaults_path=self._vaults_path)

    def _run_extract_stage(self, ctx, items):
        """Execute Extract stage (hook for BasePhaseOrchestrator).

        Args:
            ctx: Stage context.
            items: Input items (usually empty iterator).

        Returns:
            Iterator of extracted ProcessingItem.
        """
        extract_stage = self.create_extract_stage()
        return extract_stage.run(ctx, items)

    def _run_transform_stage(self, ctx, items):
        """Execute Transform stage (hook for BasePhaseOrchestrator).

        Args:
            ctx: Stage context.
            items: Items from Extract stage.

        Returns:
            Iterator of transformed ProcessingItem.
        """
        transform_stage = self.create_transform_stage()
        return transform_stage.run(ctx, items)

    def _run_load_stage(self, ctx, items):
        """Execute Load stage (hook for BasePhaseOrchestrator).

        Args:
            ctx: Stage context.
            items: Items from Transform stage.

        Returns:
            Iterator of loaded ProcessingItem.
        """
        load_stage = self.create_load_stage()
        return load_stage.run(ctx, items)

    def discover_items(self, input_path: Path) -> Iterator[ProcessingItem]:
        """Discover Markdown files in input directory.

        Recursively searches for .md files.

        Args:
            input_path: Directory to search for Markdown files.

        Yields:
            ProcessingItem for each Markdown file found.
        """
        if not input_path.exists():
            return

        for md_file in input_path.rglob("*.md"):
            yield ProcessingItem(
                item_id=md_file.stem,
                source_path=md_file,
                current_step="init",
                status=ItemStatus.PENDING,
                metadata={"discovered_at": datetime.now().isoformat()},
            )

    def run(
        self,
        phase_data: Phase,
        debug_mode: bool = False,
        session_manager: SessionManager | None = None,
    ) -> PhaseResult:
        """Execute the Organize phase.

        Args:
            phase_data: Phase dataclass with folder structure.
            debug_mode: Whether to enable debug logging.
            session_manager: Optional SessionManager for tracking expected item count.

        Returns:
            PhaseResult with execution summary.
        """
        start_time = datetime.now()
        items_processed = 0
        items_failed = 0

        # Create stages
        extract_stage = self.create_extract_stage()
        transform_stage = self.create_transform_stage()
        load_stage = self.create_load_stage()

        # Get input path
        extract_data = phase_data.stages.get(StageType.EXTRACT)
        if extract_data is None:
            return PhaseResult(
                phase_type=self.phase_type,
                status=PhaseStatus.FAILED,
                items_processed=0,
                items_failed=0,
                duration_seconds=0,
            )

        input_path = extract_data.input_path

        # Discover items
        items = self.discover_items(input_path)

        # Run Extract stage
        extract_ctx = StageContext(
            phase=phase_data,
            stage=extract_data,
            debug_mode=debug_mode,
        )
        extracted = extract_stage.run(extract_ctx, items)

        # Calculate expected item count after Extract completes
        # This count represents how many items Transform/Load will process
        if session_manager:
            from src.etl.cli.utils.pipeline_stats import count_extract_items
            from src.etl.core.session import PhaseStats

            expected_count = count_extract_items(phase_data.base_path)

            # Load session and update PhaseStats
            # phase_data.base_path is session_dir/organize/, so parent is session_dir
            session_id = phase_data.base_path.parent.name
            session = session_manager.load(session_id)

            # Update or create PhaseStats for organize phase
            phase_stats = PhaseStats(
                status="in_progress",
                expected_total_item_count=expected_count,
                completed_information=None,  # Not completed yet
            )
            session.phases["organize"] = phase_stats
            session_manager.save(session)

        # Run Transform stage
        transform_data = phase_data.stages.get(StageType.TRANSFORM)
        if transform_data:
            transform_ctx = StageContext(
                phase=phase_data,
                stage=transform_data,
                debug_mode=debug_mode,
            )
            transformed = transform_stage.run(transform_ctx, extracted)
        else:
            transformed = extracted

        # Run Load stage
        load_data = phase_data.stages.get(StageType.LOAD)
        if load_data:
            # Create vault loader with paths
            load_stage = VaultLoader(vaults_path=self._vaults_path or load_data.output_path)
            load_ctx = StageContext(
                phase=phase_data,
                stage=load_data,
                debug_mode=debug_mode,
            )
            loaded = load_stage.run(load_ctx, transformed)
        else:
            loaded = transformed

        # Consume iterator and count results
        for item in loaded:
            if item.status == ItemStatus.COMPLETED:
                items_processed += 1
            elif item.status == ItemStatus.FAILED:
                items_failed += 1
            else:
                items_processed += 1  # Count SKIPPED as processed

        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Determine status
        if items_failed == 0 and items_processed > 0:
            status = PhaseStatus.COMPLETED
        elif items_processed > 0:
            status = PhaseStatus.PARTIAL
        elif items_failed > 0:
            status = PhaseStatus.FAILED
        else:
            status = PhaseStatus.COMPLETED  # Empty input is success

        return PhaseResult(
            phase_type=self.phase_type,
            status=status,
            items_processed=items_processed,
            items_failed=items_failed,
            duration_seconds=duration,
        )
