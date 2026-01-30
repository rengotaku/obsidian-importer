"""Stage dataclass and BaseStage for ETL pipeline.

Represents a single ETL stage (Extract, Transform, Load) within a Phase.
Includes abstract base classes for Stage and Step implementations.
"""

import json
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from itertools import islice
from pathlib import Path
from typing import Any

# Import error logging and hierarchy
from .models import CompletedItemsCache, ProcessingItem, StageLogRecord
from .status import ItemStatus, StageStatus
from .step import Step
from .types import StageType


@dataclass
class Stage:
    """A single ETL stage within a Phase.

    Each stage has:
    - A type (EXTRACT, TRANSFORM, LOAD)
    - Input/output paths for file operations
    - Steps for detailed processing
    - Items being processed
    """

    stage_type: StageType
    """Type of the stage (EXTRACT, TRANSFORM, LOAD)."""

    input_path: Path
    """Path for input files (only used by EXTRACT)."""

    output_path: Path
    """Path for output files."""

    status: StageStatus = StageStatus.PENDING
    """Current execution status."""

    steps: list[Step] = field(default_factory=list)
    """Processing steps within this stage."""

    items: list[ProcessingItem] = field(default_factory=list)
    """Items being processed in this stage."""

    def to_dict(self) -> dict[str, Any]:
        """Convert Stage to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the Stage.
        """
        return {
            "stage_type": self.stage_type.value,
            "status": self.status.value,
            "input_path": str(self.input_path),
            "output_path": str(self.output_path),
            "steps": [step.to_dict() for step in self.steps],
            "items_count": len(self.items),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Stage":
        """Create Stage from dictionary.

        Args:
            data: Dictionary with stage data.

        Returns:
            Stage instance.
        """
        steps = [Step.from_dict(s) for s in data.get("steps", [])]

        return cls(
            stage_type=StageType(data["stage_type"]),
            status=StageStatus(data["status"]),
            input_path=Path(data["input_path"]),
            output_path=Path(data["output_path"]),
            steps=steps,
            items=[],  # Items are not serialized in stage data
        )

    @classmethod
    def create_for_phase(
        cls,
        stage_type: StageType,
        phase_path: Path,
    ) -> "Stage":
        """Create a Stage with standard folder structure.

        Args:
            stage_type: Type of stage to create.
            phase_path: Path to the parent phase folder.

        Returns:
            Stage instance with paths configured.
        """
        stage_path = phase_path / stage_type.value

        # Extract stage has input/ folder, others only have output/
        if stage_type == StageType.EXTRACT:
            input_path = stage_path / "input"
            output_path = stage_path / "output"
        else:
            input_path = stage_path  # Not used, but set for consistency
            output_path = stage_path / "output"

        return cls(
            stage_type=stage_type,
            input_path=input_path,
            output_path=output_path,
        )

    def ensure_folders(self) -> None:
        """Create the stage folders if they don't exist."""
        if self.stage_type == StageType.EXTRACT:
            self.input_path.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)


# Forward reference for Phase (used in StageContext)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .phase import Phase


@dataclass
class StageContext:
    """Context for Stage execution.

    Provides access to phase, stage data, and configuration.
    """

    phase: "Phase"
    """Parent Phase containing this stage."""

    stage: Stage
    """Stage data (paths, status, etc.)."""

    debug_mode: bool = True
    """Whether debug mode is enabled (FR-012: always True)."""

    limit: int | None = None
    """Maximum number of items to process (None = unlimited)."""

    chunk: bool = False
    """Whether chunking is enabled for large files (default: False)."""

    completed_cache: "CompletedItemsCache | None" = None
    """Cache of completed items for Resume mode (None = no skip)."""

    @property
    def input_path(self) -> Path:
        """Input path for this stage."""
        return self.stage.input_path

    @property
    def output_path(self) -> Path:
        """Output path for this stage."""
        return self.stage.output_path


class BaseStep(ABC):
    """Abstract base class for processing steps.

    A Step is the smallest unit of processing in the ETL pipeline.
    Each Step processes a single ProcessingItem.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Step identifier name.

        Returns:
            Unique name for this step (e.g., 'parse_json', 'validate').
        """
        ...

    @abstractmethod
    def process(self, item: ProcessingItem) -> ProcessingItem | list[ProcessingItem]:
        """Process a single item.

        Args:
            item: Item to process.

        Returns:
            Processed item (may be the same instance, modified),
            or a list of items for 1:N expansion.

        Raises:
            Exception: If processing fails.
            RuntimeError: If returning an empty list (1:N expansion must yield at least 1 item).
        """
        ...

    def validate_input(self, item: ProcessingItem) -> bool:
        """Validate input before processing.

        Override to implement custom validation.

        Args:
            item: Item to validate.

        Returns:
            True if valid, False to skip this item.
        """
        return True

    def on_error(self, item: ProcessingItem, error: Exception) -> ProcessingItem | None:
        """Handle processing error.

        Override to provide fallback behavior.

        Args:
            item: Item that caused the error.
            error: Exception that occurred.

        Returns:
            Fallback item to continue with, or None to mark as failed.
        """
        return None


class BaseStage(ABC):
    """Abstract base class for ETL stages.

    A Stage contains multiple Steps and processes items through them.
    Stages are: Extract, Transform, Load.
    """

    def __init__(self):
        """Initialize BaseStage with output file tracking attributes."""
        # US3: Track output file index and record count for splitting
        self._output_file_index: int = 1  # 1-indexed (data-dump-0001.jsonl)
        self._output_record_count: int = 0  # Current file record count
        self._max_records_per_file: int = 5000  # Records per file (default: 5000)

    @property
    @abstractmethod
    def stage_type(self) -> StageType:
        """Type of this stage.

        Returns:
            StageType (EXTRACT, TRANSFORM, or LOAD).
        """
        ...

    @property
    @abstractmethod
    def steps(self) -> list[BaseStep]:
        """List of steps to execute.

        Returns:
            Ordered list of steps for this stage.
        """
        ...

    def run(
        self,
        ctx: StageContext,
        items: Iterator[ProcessingItem],
    ) -> Iterator[ProcessingItem]:
        """Execute the stage on items.

        Processes each item through all steps in order.
        Supports 1:N expansion: if steps expand an item, all expanded items are yielded.
        Automatically writes JSONL log after each item.

        Error handling:
        - StepError: Logged to errors.jsonl, processing continues
        - StageError/PhaseError: Immediately re-raised
        - Other exceptions: Converted to StageError
        - Threshold: 20% error rate triggers StageError

        Args:
            ctx: Stage context with paths and configuration.
            items: Input items to process.

        Yields:
            Processed items (may be more than input if 1:N expansion occurred).

        Raises:
            StageError: If error rate exceeds 20% or unexpected error occurs.
            PhaseError: If phase-level error occurs.
        """
        # Import here to avoid circular dependency
        from ..utils.error_logger import ErrorLogger
        from .errors import PhaseError, StageError, StepError

        # Initialize error logger
        errors_file = ctx.phase.base_path / "errors.jsonl"
        error_logger = ErrorLogger(errors_file)

        # Track success/error counts
        success_count = 0
        error_count = 0

        # Load stage: Filter only COMPLETED items from Transform
        # Failed/Skipped items should not be persisted
        if self.stage_type == StageType.LOAD:
            items = (item for item in items if item.status == ItemStatus.COMPLETED)

        # Resume mode: Filter out already completed items (no yield, no status change)
        if ctx.completed_cache:
            items = (item for item in items if not ctx.completed_cache.is_completed(item.item_id))

        # Apply limit AFTER skip check (so limit applies to non-skipped items)
        if ctx.limit is not None:
            items = islice(items, ctx.limit)

        for item in items:
            # Propagate chunk flag from context to item metadata
            # This allows Steps to check if chunking is enabled
            item.metadata["chunk_enabled"] = ctx.chunk

            start_time = time.perf_counter()
            start_content_len = len(item.content) if item.content else None

            try:
                results = self._process_item(ctx, item)
                if results:
                    # _process_item returns a list of items (1:1 or 1:N)
                    for result in results:
                        # Track success/failure
                        if result.status == ItemStatus.COMPLETED:
                            success_count += 1
                        elif result.status == ItemStatus.FAILED:
                            error_count += 1

                        # Calculate timing
                        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                        end_content_len = None
                        if result.transformed_content:
                            end_content_len = len(result.transformed_content)
                        elif result.content:
                            end_content_len = len(result.content)

                        # Write JSONL log (framework automatic output)
                        self._write_jsonl_log(
                            ctx,
                            result,
                            step_name=result.current_step,
                            timing_ms=elapsed_ms,
                            start_content_len=start_content_len,
                            end_content_len=end_content_len,
                        )

                        # Write ProcessingItem to output/ (Transform stage only)
                        if result.status == ItemStatus.COMPLETED:
                            self._write_output_item(ctx, result)

                        yield result

            except StepError as e:
                # StepError: Log and continue
                error_count += 1
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                # Log to errors.jsonl
                error_logger.log_error(
                    item_id=item.item_id,
                    step=item.current_step,
                    error=e,
                    conversation_title=item.metadata.get("conversation_name"),
                    llm_prompt=item.metadata.get("llm_prompt"),
                    llm_output=item.metadata.get("llm_raw_response"),
                )

                # Mark item as failed
                item.status = ItemStatus.FAILED
                item.error = str(e)

                # Write JSONL log
                self._write_jsonl_log(
                    ctx,
                    item,
                    step_name=item.current_step,
                    timing_ms=elapsed_ms,
                    start_content_len=start_content_len,
                )

                yield item

            except (StageError, PhaseError):
                # Stage/Phase errors: Re-raise immediately
                raise

            except RuntimeError:
                # Re-raise validation errors (empty list, etc.)
                raise

            except Exception as e:
                # Unexpected error: Convert to StageError
                raise StageError(f"Unexpected error in stage: {e}") from e

        # Threshold check after all items processed
        total = success_count + error_count
        if total > 0:
            error_rate = error_count / total
            if error_rate > 0.20:  # 20% threshold
                raise StageError(
                    f"Error rate {error_rate:.1%} exceeds 20% threshold: "
                    f"{error_count}/{total} items failed"
                )

    def _process_item(
        self,
        ctx: StageContext,
        item: ProcessingItem,
    ) -> list[ProcessingItem]:
        """Process a single item through all steps.

        Supports 1:N expansion: if a step returns a list of items, subsequent steps
        are applied to each expanded item individually.

        Args:
            ctx: Stage context.
            item: Item to process.

        Returns:
            List of processed items (may be 1:1 or 1:N expansion).

        Raises:
            RuntimeError: If a step returns an empty list (1:N expansion must yield at least 1 item).
        """
        current_items = [item]  # Start with single item, may expand

        for step_index, step in enumerate(self.steps):
            next_items = []

            for idx, current in enumerate(current_items):
                current.current_step = step.name

                # Validate input
                if not step.validate_input(current):
                    current.status = ItemStatus.FILTERED
                    next_items.append(current)
                    continue

                # Measure step timing and content length
                step_start = time.perf_counter()
                before_chars = len(current.content) if current.content else None

                # Process
                try:
                    result = step.process(current)

                    # Handle 1:N expansion or 1:1 processing
                    if isinstance(result, list):
                        # 1:N expansion: validate non-empty
                        if not result:
                            raise RuntimeError(
                                f"Step '{step.name}' returned empty list. "
                                "1:N expansion must yield at least 1 item."
                            )

                        # Track expansion metadata
                        total_expanded = len(result)

                        for expansion_index, expanded_item in enumerate(result):
                            # Only set parent_item_id if this is chunking (is_chunked=True in metadata)
                            # Do NOT set parent_item_id for parsing expansion (e.g., ZIP→conversations)
                            if expanded_item.metadata.get("is_chunked"):
                                expanded_item.metadata["parent_item_id"] = current.item_id

                            expanded_item.metadata["expansion_index"] = expansion_index
                            expanded_item.metadata["total_expanded"] = total_expanded

                            # Calculate metrics for this expanded item
                            after_chars = None
                            if expanded_item.transformed_content:
                                after_chars = len(expanded_item.transformed_content)
                            elif expanded_item.content:
                                after_chars = len(expanded_item.content)
                            timing_ms = int((time.perf_counter() - step_start) * 1000)

                            # Write step-level debug output for each expanded item
                            self._write_debug_step_output(
                                ctx,
                                expanded_item,
                                step_index,
                                step.name,
                                timing_ms=timing_ms,
                                before_chars=before_chars,
                                after_chars=after_chars,
                            )

                        next_items.extend(result)
                    else:
                        # 1:1 processing: single item returned
                        # Calculate metrics after processing
                        after_chars = None
                        if result.transformed_content:
                            after_chars = len(result.transformed_content)
                        elif result.content:
                            after_chars = len(result.content)
                        timing_ms = int((time.perf_counter() - step_start) * 1000)

                        # Write step-level debug output after successful step (DEBUG mode)
                        self._write_debug_step_output(
                            ctx,
                            result,
                            step_index,
                            step.name,
                            timing_ms=timing_ms,
                            before_chars=before_chars,
                            after_chars=after_chars,
                        )

                        next_items.append(result)

                except RuntimeError:
                    # Re-raise validation errors (empty list, etc.) without catching
                    raise
                except Exception as e:
                    # Calculate timing even on failure
                    timing_ms = int((time.perf_counter() - step_start) * 1000)
                    after_chars = None
                    if current.transformed_content:
                        after_chars = len(current.transformed_content)
                    elif current.content:
                        after_chars = len(current.content)

                    # Write step-level debug output on failure (DEBUG mode)
                    self._write_debug_step_output(
                        ctx,
                        current,
                        step_index,
                        step.name,
                        timing_ms=timing_ms,
                        before_chars=before_chars,
                        after_chars=after_chars,
                        error=e,
                    )

                    # Write error details to error_details.jsonl
                    self._write_error_detail_jsonl(ctx, current, e)

                    # Try fallback
                    fallback = step.on_error(current, e)
                    if fallback is None:
                        current.status = ItemStatus.FAILED
                        current.error = str(e)
                        next_items.append(current)
                    else:
                        next_items.append(fallback)

            current_items = next_items

        # After all steps, mark all items as completed
        for processed_item in current_items:
            if processed_item.status == ItemStatus.PENDING:
                processed_item.status = ItemStatus.COMPLETED

        return current_items

    def _handle_error(
        self,
        ctx: StageContext,
        item: ProcessingItem,
        error: Exception,
    ) -> None:
        """Handle stage-level error.

        T068: Writes error detail file to errors/ folder.
        Also writes debug output in debug mode.

        Args:
            ctx: Stage context.
            item: Item that caused the error.
            error: Exception that occurred.
        """
        # T068: Write error detail file
        self._write_error_detail(ctx, item, error)

    def _write_error_detail(
        self,
        ctx: StageContext,
        item: ProcessingItem,
        error: Exception,
    ) -> None:
        """Write error detail file to errors/ folder.

        T068-T071: Creates ErrorDetail from ProcessingItem and writes to
        {phase_dir}/errors/{item_id}_{timestamp}.md

        Args:
            ctx: Stage context with phase and session info.
            item: Item that caused the error.
            error: Exception that occurred.
        """
        # T070: Ensure errors/ folder exists under phase directory
        errors_path = ctx.phase.base_path / "errors"

        # Get session_id from phase context
        session_id = ctx.phase.base_path.parent.name

        # T069: Create ErrorDetail from ProcessingItem
        # Determine error_type from exception
        error_type = self._classify_error(error)

        # Get conversation info from metadata
        conversation_id = item.metadata.get("conversation_uuid", item.item_id)
        conversation_title = item.metadata.get("conversation_name", "Untitled")

        # T071: Get llm_prompt and llm_output from metadata (captured in ExtractKnowledgeStep)
        llm_prompt = item.metadata.get("llm_prompt", "")
        llm_output = item.metadata.get("llm_raw_response")

        # Get original content
        original_content = item.content or item.transformed_content or ""

        # Create ErrorDetail
        error_detail = ErrorDetail(
            session_id=session_id,
            conversation_id=conversation_id,
            conversation_title=conversation_title,
            timestamp=datetime.now(UTC).replace(tzinfo=None),
            error_type=error_type,
            error_message=str(error),
            original_content=original_content,
            llm_prompt=llm_prompt,
            stage=item.current_step or self.stage_type.value,
            llm_output=llm_output,
        )

        # Write error file
        try:
            write_error_file(error_detail, errors_path)
        except Exception:
            # Silently ignore write errors to avoid masking original error
            pass

    def _classify_error(self, error: Exception) -> str:
        """Classify error type from exception.

        Args:
            error: Exception to classify.

        Returns:
            Error type string (json_parse, timeout, no_json, etc.)
        """
        error_msg = str(error).lower()
        error_type_name = type(error).__name__.lower()

        if "json" in error_msg or "json" in error_type_name:
            if "parse" in error_msg or "decode" in error_msg:
                return "json_parse"
            return "no_json"
        elif "timeout" in error_msg or "timeout" in error_type_name:
            return "timeout"
        elif "connection" in error_msg or "connection" in error_type_name:
            return "connection"
        elif "retry" in error_msg:
            return "retry_exhausted"
        else:
            return "unknown"

    def _write_error_detail_jsonl(
        self,
        ctx: StageContext,
        item: ProcessingItem,
        error: Exception,
    ) -> None:
        """Write error details to error_details.jsonl.

        Args:
            ctx: Stage context.
            item: Item that caused the error.
            error: Exception that occurred.
        """
        import traceback

        from .models import ErrorDetailRecord

        # Get session_id from phase context
        session_id = ctx.phase.base_path.parent.name

        # Get backtrace
        backtrace = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        # Build metadata
        metadata = {
            "conversation_title": item.metadata.get("conversation_name"),
            "llm_prompt": item.metadata.get("llm_prompt"),
            "llm_output": item.metadata.get("llm_raw_response"),
        }
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}

        record = ErrorDetailRecord(
            timestamp=datetime.now(UTC).isoformat(),
            session_id=session_id,
            item_id=item.item_id,
            stage=self.stage_type.value,
            step=item.current_step or "unknown",
            error_type=type(error).__name__,
            error_message=str(error),
            backtrace=backtrace,
            metadata=metadata,
        )

        # Write to error_details.jsonl
        error_details_path = ctx.phase.base_path / "error_details.jsonl"
        error_details_path.parent.mkdir(parents=True, exist_ok=True)
        with open(error_details_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def _write_jsonl_log(
        self,
        ctx: StageContext,
        item: ProcessingItem,
        step_name: str,
        timing_ms: int,
        start_content_len: int | None = None,
        end_content_len: int | None = None,
    ) -> None:
        """Write a JSONL log record for this item processing.

        Automatically called after each item is processed. Step implementers
        do not need to call this directly.

        Args:
            ctx: Stage context with phase and session info.
            item: Processed item.
            step_name: Name of the completed step.
            timing_ms: Processing time in milliseconds.
            start_content_len: Content length before processing (optional).
            end_content_len: Content length after processing (optional).
        """
        # Get session_id from phase context
        session_id = ctx.phase.base_path.parent.name

        # Determine status string
        if item.status == ItemStatus.COMPLETED:
            status = "success"
        elif item.status == ItemStatus.FILTERED:
            status = "skipped"
        else:
            status = "failed"

        # Calculate diff_ratio if both lengths provided
        diff_ratio = None
        if start_content_len and end_content_len and start_content_len > 0:
            diff_ratio = round(end_content_len / start_content_len, 3)

        # Get file_id from metadata if available
        file_id = item.metadata.get("file_id")

        # Get skipped_reason if available
        skipped_reason = None
        if status == "skipped":
            skipped_reason = item.metadata.get("skipped_reason")

        # T019: Get chunk metadata from item.metadata
        is_chunked = item.metadata.get("is_chunked")
        parent_item_id = item.metadata.get("parent_item_id")
        chunk_index = item.metadata.get("chunk_index")

        # Get error message if failed
        error_message = None
        if status == "failed" and item.error:
            error_message = str(item.error)

        record = StageLogRecord(
            timestamp=datetime.now(UTC).isoformat(),
            session_id=session_id,
            filename=item.source_path.name,
            stage=self.stage_type.value,
            step=step_name,
            timing_ms=timing_ms,
            status=status,
            item_id=item.item_id,
            file_id=file_id,
            skipped_reason=skipped_reason,
            before_chars=start_content_len,
            after_chars=end_content_len,
            diff_ratio=diff_ratio,
            is_chunked=is_chunked,
            parent_item_id=parent_item_id,
            chunk_index=chunk_index,
            error_message=error_message,
        )

        # Get JSONL log path from phase context
        jsonl_path = getattr(ctx.phase, "pipeline_stages_jsonl", None)
        if jsonl_path is None:
            jsonl_path = ctx.phase.base_path / "pipeline_stages.jsonl"

        # Append to JSONL file
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
            f.flush()  # FR-011: Ensure immediate write for crash recovery

    def _write_output_item(self, ctx: StageContext, item: ProcessingItem) -> None:
        """Write ProcessingItem to output/ folder as JSONL (Extract and Transform stages).

        US3: Uses fixed filename pattern data-dump-{番号4桁}.jsonl and splits at 1000 records.

        Args:
            ctx: Stage context.
            item: ProcessingItem to save.
        """
        # Only write for Extract and Transform stages (Load writes to final destination)
        if self.stage_type not in (StageType.EXTRACT, StageType.TRANSFORM):
            return

        # US3: Use fixed filename pattern data-dump-{番号4桁}.jsonl
        output_file = ctx.output_path / f"data-dump-{self._output_file_index:04d}.jsonl"

        # Serialize item with metadata serialization
        item_dict = item.to_dict()
        item_dict["metadata"] = self._serialize_metadata(item.metadata)

        # Write item as JSONL (one line per item)
        ctx.output_path.mkdir(parents=True, exist_ok=True)
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(item_dict, ensure_ascii=False) + "\n")
            f.flush()

        # US3: Increment record count and split if necessary
        self._output_record_count += 1

        # US3: Split to next file after reaching max records per file
        if self._output_record_count >= self._max_records_per_file:
            self._output_file_index += 1
            self._output_record_count = 0

    def _serialize_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Serialize metadata for JSON output.

        Recursively converts dataclass objects to dictionaries.

        Args:
            metadata: Metadata dictionary potentially containing dataclass objects.

        Returns:
            JSON-serializable metadata dictionary.
        """
        result = {}
        for key, value in metadata.items():
            if is_dataclass(value) and not isinstance(value, type):
                # Convert dataclass instance to dict
                result[key] = asdict(value)
            elif isinstance(value, dict):
                # Recursively serialize nested dicts
                result[key] = self._serialize_metadata(value)
            elif isinstance(value, list):
                # Serialize list items
                result[key] = [
                    asdict(item) if is_dataclass(item) and not isinstance(item, type) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def _write_debug_step_output(
        self,
        ctx: StageContext,
        item: ProcessingItem,
        step_index: int,
        step_name: str,
        timing_ms: int,
        before_chars: int | None = None,
        after_chars: int | None = None,
        error: Exception | None = None,
    ) -> None:
        """Write step-level output for this item (FR-012: always enabled).

        Writes intermediate processing state after each step to stage folder.
        Also writes step metrics to steps.jsonl for aggregated analysis.
        Output is in JSONL format (compact JSON, one line per file).

        Args:
            ctx: Stage context.
            item: Item being processed.
            step_index: 0-based index of the step (will be converted to 1-based).
            step_name: Name of the step.
            timing_ms: Processing time in milliseconds.
            before_chars: Content length before step processing (optional).
            after_chars: Content length after step processing (optional).
            error: Exception if step processing failed (optional).
        """
        # FR-012: Debug mode always enabled - no check needed

        # Write steps.jsonl to stage folder (parent of output/)
        stage_folder = ctx.output_path.parent
        steps_jsonl = stage_folder / "steps.jsonl"

        # Calculate diff_ratio for metrics
        diff_ratio = None
        if before_chars is not None and after_chars is not None and before_chars > 0:
            diff_ratio = round(after_chars / before_chars, 3)

        # Build debug data (unified: detailed debug + metrics)
        debug_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "item_id": item.item_id,
            "source_path": str(item.source_path),
            "current_step": item.current_step,
            "step_index": step_index + 1,  # Convert to 1-based
            "status": item.status.value,
            "timing_ms": timing_ms,
            "before_chars": before_chars,
            "after_chars": after_chars,
            "diff_ratio": diff_ratio,
        }

        # Include latest content only (transformed_content takes precedence)
        # Truncate to ~200 chars for readability
        output_content = item.transformed_content or item.content
        if output_content:
            truncated_content = (
                output_content[:200] + "..." if len(output_content) > 200 else output_content
            )
            debug_data["content"] = truncated_content

        # Include error details if present
        if error:
            debug_data["error"] = str(error)
        elif item.error:
            debug_data["error"] = item.error

        # Add metadata last (exclude knowledge_document to avoid duplication with content)
        debug_metadata = {k: v for k, v in item.metadata.items() if k != "knowledge_document"}
        debug_data["metadata"] = self._serialize_metadata(debug_metadata)

        # Ensure stage folder exists before writing
        stage_folder.mkdir(parents=True, exist_ok=True)

        # Write to unified steps.jsonl (compact format, no indentation, append mode)
        with open(steps_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(debug_data, ensure_ascii=False) + "\n")


class ResumableStage(BaseStage):
    """Stage with Resume mode support.

    Provides skip logic for completed items based on CompletedItemsCache.
    Concrete stages should inherit from this class if they support Resume mode.
    """

    def __init__(self):
        """Initialize ResumableStage with empty steps list."""
        super().__init__()
        self._steps: list[BaseStep] = []

    @property
    def stage_type(self) -> StageType:
        """Default stage type for testing."""
        return StageType.TRANSFORM

    @property
    def steps(self) -> list[BaseStep]:
        """Return steps list."""
        return self._steps

    def _process_item(self, item: ProcessingItem) -> ProcessingItem:
        """Mock process item (for testing).

        Can be overridden by tests.

        Args:
            item: Item to process.

        Returns:
            Unchanged item.
        """
        return item

    def run(
        self,
        ctx: StageContext,
        items: Iterator[ProcessingItem],
    ) -> Iterator[ProcessingItem]:
        """Execute the stage with skip logic for Resume mode.

        If ctx.completed_cache is set:
        - Skipped items are filtered out (not yielded, no status change)
        - Only non-skipped items are processed through steps

        Args:
            ctx: Stage context with optional completed_cache.
            items: Input items to process.

        Yields:
            Processed items (skipped items are filtered, not yielded).

        Raises:
            StageError: If error rate exceeds 20% or unexpected error occurs.
        """
        # Resume mode: Filter out already completed items (no yield, no status change)
        if ctx.completed_cache:
            items = (item for item in items if not ctx.completed_cache.is_completed(item.item_id))

        # Process each item (or delegate to BaseStage.run() if steps are defined)
        if self._steps:
            # Use BaseStage.run() if steps are defined
            yield from super().run(ctx, items)
        else:
            # Simple pass-through for testing
            for item in items:
                processed = self._process_item(item)
                if processed.status == ItemStatus.PENDING:
                    processed.status = ItemStatus.COMPLETED
                yield processed
