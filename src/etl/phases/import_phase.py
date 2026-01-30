"""ImportPhase orchestration for ETL pipeline.

Orchestrates: ClaudeExtractor -> KnowledgeTransformer -> SessionLoader
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from src.etl.core.models import CompletedItemsCache
from src.etl.core.phase import Phase
from src.etl.core.phase_orchestrator import BasePhaseOrchestrator
from src.etl.core.stage import BaseStage, StageContext
from src.etl.core.status import ItemStatus, PhaseStatus
from src.etl.core.types import PhaseType, StageType
from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor
from src.etl.stages.extract.claude_extractor import ClaudeExtractor
from src.etl.stages.extract.github_extractor import GitHubExtractor
from src.etl.stages.load.session_loader import SessionLoader
from src.etl.stages.transform.knowledge_transformer import KnowledgeTransformer

if TYPE_CHECKING:
    from src.etl.core.session import SessionManager


@dataclass
class PhaseResult:
    """Result of Phase execution."""

    phase_type: PhaseType
    status: PhaseStatus
    items_processed: int
    items_failed: int
    items_skipped: int
    duration_seconds: float


class ImportPhase(BasePhaseOrchestrator):
    """Import Phase orchestration.

    Processes Claude/ChatGPT export files through:
    - Extract: ClaudeExtractor or ChatGPTExtractor (JSON/ZIP parsing)
    - Transform: KnowledgeTransformer (knowledge extraction)
    - Load: SessionLoader (write to session)
    """

    def __init__(
        self,
        provider: str = "claude",
        fetch_titles: bool = True,
        chunk: bool = False,
        base_path: Path | None = None,
    ):
        """Initialize ImportPhase with provider.

        Args:
            provider: Source provider ("claude", "openai", or "github", default "claude").
            fetch_titles: Enable URL title fetching (default: True).
            chunk: Enable chunking for large files (>25000 chars, default: False).
            base_path: Base path for Resume mode (optional).
        """
        self._provider = provider
        self._fetch_titles = fetch_titles
        self._chunk = chunk
        self.base_path = base_path

    @property
    def phase_type(self) -> PhaseType:
        """Phase type is IMPORT."""
        return PhaseType.IMPORT

    def create_extract_stage(self) -> BaseStage:
        """Create Extractor stage based on provider.

        Returns:
            ClaudeExtractor for "claude", ChatGPTExtractor for "openai", GitHubExtractor for "github".

        Raises:
            ValueError: If provider is not supported.
        """
        if self._provider == "openai":
            return ChatGPTExtractor()
        elif self._provider == "claude":
            return ClaudeExtractor()
        elif self._provider == "github":
            return GitHubExtractor()
        else:
            raise ValueError(
                f"Unsupported provider: {self._provider}. Valid providers: claude, openai, github"
            )

    def create_transform_stage(self) -> BaseStage:
        """Create KnowledgeTransformer stage."""
        return KnowledgeTransformer(fetch_titles=self._fetch_titles)

    def create_load_stage(self) -> BaseStage:
        """Create SessionLoader stage."""
        return SessionLoader()

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

    def should_skip_extract_stage(self) -> bool:
        """Check if Extract output folder has results.

        Returns:
            True if Extract stage should be skipped (has output), False otherwise.
        """
        if self.base_path is None:
            return False

        extract_output = self.base_path / "extract" / "output"
        if extract_output.exists():
            return any(extract_output.iterdir())
        return False

    def run(
        self,
        phase_data: Phase,
        debug_mode: bool = False,
        limit: int | None = None,
        session_manager: SessionManager | None = None,
    ) -> PhaseResult:
        """Execute the Import phase.

        Args:
            phase_data: Phase dataclass with folder structure.
            debug_mode: Whether to enable debug logging.
            limit: Maximum number of items to process in Transform stage.

        Returns:
            PhaseResult with execution summary.
        """
        # Resume mode check: Extract stage must be completed
        if self.base_path is not None:
            extract_output = phase_data.stages[StageType.EXTRACT].output_path
            if not extract_output.exists() or not any(extract_output.iterdir()):
                raise RuntimeError("Error: Extract stage not completed. Cannot resume.")

        # Resume mode: Display progress message
        if self.base_path is not None and session_manager is not None:
            import json

            # Get expected total from session.json
            session_id = phase_data.base_path.parent.name
            session = session_manager.load(session_id)
            phase_stats = session.phases.get("import")
            expected_total = phase_stats.expected_total_item_count if phase_stats else 0

            # Count completed items from pipeline_stages.jsonl
            jsonl_path = phase_data.base_path / "pipeline_stages.jsonl"
            completed_count = 0
            if jsonl_path.exists():
                with open(jsonl_path, encoding="utf-8") as f:
                    for line in f:
                        try:
                            record = json.loads(line)
                            if (
                                record.get("status") == "success"
                                and record.get("stage") == "transform"
                            ):
                                completed_count += 1
                        except json.JSONDecodeError:
                            continue

            # Display progress message
            print(
                f"Resume mode: {completed_count}/{expected_total} items already completed, starting from item {completed_count + 1}"
            )

        start_time = datetime.now()
        items_processed = 0
        items_failed = 0
        items_skipped = 0

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
                items_skipped=0,
                duration_seconds=0,
            )

        input_path = extract_data.input_path

        # Check if Extract output exists (Resume mode)
        if self._should_load_extract_from_output(phase_data):
            print("Resume mode: Loading from extract/output/*.jsonl")
            extracted = list(self._load_extract_items_from_output(phase_data))
        else:
            print("Extract output not found, processing from input/")
            # Discover items - delegate to extract_stage
            # Pass chunk flag to control whether large files are chunked
            items = extract_stage.discover_items(input_path, chunk=self._chunk)

            # Run Extract stage
            extract_ctx = StageContext(
                phase=phase_data,
                stage=extract_data,
                debug_mode=debug_mode,
                chunk=self._chunk,
            )
            extracted_iter = extract_stage.run(extract_ctx, items)

            # Consume Extract iterator to complete extraction
            extracted = list(extracted_iter)

        # Calculate expected item count after Extract completes
        # This count represents how many items Transform/Load will process
        if session_manager:
            from src.etl.cli.utils.pipeline_stats import count_extract_items
            from src.etl.core.session import PhaseStats

            expected_count = count_extract_items(phase_data.base_path)

            # Load session and update PhaseStats
            # phase_data.base_path is session_dir/import/, so parent is session_dir
            session_id = phase_data.base_path.parent.name
            session = session_manager.load(session_id)

            phase_stats = PhaseStats(
                status="in_progress",
                expected_total_item_count=expected_count,
                completed_information=None,  # Not completed yet
            )
            session.phases["import"] = phase_stats
            session_manager.save(session)

        # Build completed_cache for Resume mode
        pipeline_stages_jsonl = phase_data.base_path / "pipeline_stages.jsonl"
        transform_cache = None
        load_cache = None
        if pipeline_stages_jsonl.exists():
            transform_cache = CompletedItemsCache.from_jsonl(
                pipeline_stages_jsonl, StageType.TRANSFORM
            )
            load_cache = CompletedItemsCache.from_jsonl(pipeline_stages_jsonl, StageType.LOAD)

        # Run Transform stage
        transform_data = phase_data.stages.get(StageType.TRANSFORM)
        if transform_data:
            transform_ctx = StageContext(
                phase=phase_data,
                stage=transform_data,
                debug_mode=debug_mode,
                limit=limit,  # Apply limit to Transform stage
                chunk=self._chunk,
                completed_cache=transform_cache,
            )
            transformed = transform_stage.run(transform_ctx, extracted)
        else:
            transformed = extracted

        # Run Load stage
        load_data = phase_data.stages.get(StageType.LOAD)
        if load_data:
            # Create session loader with output path
            load_stage = SessionLoader(output_path=load_data.output_path)
            load_ctx = StageContext(
                phase=phase_data,
                stage=load_data,
                debug_mode=debug_mode,
                chunk=self._chunk,
                completed_cache=load_cache,
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
            elif item.status == ItemStatus.FILTERED:
                items_skipped += 1
            else:
                items_processed += 1  # Count other statuses as processed

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
            items_skipped=items_skipped,
            duration_seconds=duration,
        )
