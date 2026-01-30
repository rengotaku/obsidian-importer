"""Core data models for ETL pipeline.

Defines ProcessingItem, StepResult, RetryConfig, and ContentMetrics dataclasses.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .status import ItemStatus
from .types import StageType

# Chunk Metadata Constants
CHUNK_METADATA_IS_CHUNKED = "is_chunked"
CHUNK_METADATA_CHUNK_INDEX = "chunk_index"
CHUNK_METADATA_TOTAL_CHUNKS = "total_chunks"
CHUNK_METADATA_PARENT_ITEM_ID = "parent_item_id"
CHUNK_METADATA_CHUNK_FILENAME = "chunk_filename"


def validate_chunk_metadata(metadata: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate chunk metadata fields.

    Args:
        metadata: ProcessingItem metadata dictionary.

    Returns:
        Tuple of (is_valid, error_message).
        - (True, None) if valid or not a chunked item
        - (False, error_message) if chunked but invalid
    """
    is_chunked = metadata.get(CHUNK_METADATA_IS_CHUNKED, False)

    if not is_chunked:
        return (True, None)

    # Required fields for chunked items
    chunk_index = metadata.get(CHUNK_METADATA_CHUNK_INDEX)
    total_chunks = metadata.get(CHUNK_METADATA_TOTAL_CHUNKS)
    parent_item_id = metadata.get(CHUNK_METADATA_PARENT_ITEM_ID)

    if chunk_index is None:
        return (False, "chunk_index is required for chunked items")
    if total_chunks is None:
        return (False, "total_chunks is required for chunked items")
    if parent_item_id is None:
        return (False, "parent_item_id is required for chunked items")

    # Validate chunk_index range
    if not isinstance(chunk_index, int) or chunk_index < 0:
        return (False, f"chunk_index must be >= 0, got {chunk_index}")
    if not isinstance(total_chunks, int) or total_chunks <= 0:
        return (False, f"total_chunks must be > 0, got {total_chunks}")
    if chunk_index >= total_chunks:
        return (
            False,
            f"chunk_index ({chunk_index}) must be < total_chunks ({total_chunks})",
        )

    return (True, None)


@dataclass
class ContentMetrics:
    """Metrics for content size changes during processing.

    Tracks size before and after transformation, with anomaly detection.

    delta is a change ratio (float):
      - 0.0: No change
      - -0.5: 50% compression (content reduced to half)
      - 1.0: 2x increase (content doubled)
      - -1.0: Complete deletion (size_out = 0)

    Anomaly detection examples:
      - delta <= -0.5: 50%+ compression -> review required
      - delta >= 2.0: 3x+ increase -> review required
    """

    size_in: int
    """Input content size in bytes."""

    size_out: int
    """Output content size in bytes."""

    delta: float
    """Change ratio: (size_out - size_in) / size_in, or -1.0 if size_in is 0."""

    unit: str = "bytes"
    """Unit of measurement (default: bytes)."""

    @classmethod
    def calculate(cls, size_in: int, size_out: int, unit: str = "bytes") -> "ContentMetrics":
        """Calculate ContentMetrics from input and output sizes.

        Args:
            size_in: Input size.
            size_out: Output size.
            unit: Unit of measurement.

        Returns:
            ContentMetrics instance with calculated delta.
        """
        if size_in == 0:
            delta = -1.0 if size_out == 0 else float(size_out)  # Arbitrary large value for 0 -> N
        else:
            delta = (size_out - size_in) / size_in
        return cls(size_in=size_in, size_out=size_out, delta=delta, unit=unit)

    @property
    def review_required(self) -> bool:
        """Check if delta indicates anomalous change requiring review.

        Returns:
            True if delta <= -0.5 (50%+ compression) or delta >= 2.0 (3x+ increase).
        """
        return self.delta <= -0.5 or self.delta >= 2.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation.
        """
        return {
            "size_in": self.size_in,
            "size_out": self.size_out,
            "delta": self.delta,
            "unit": self.unit,
            "review_required": self.review_required,
        }


@dataclass
class ProcessingItem:
    """Processing item that flows through the pipeline.

    Represents a single unit of work (e.g., a file or conversation)
    being processed through Extract -> Transform -> Load stages.

    Metadata Schema for Chunked Items:
        - is_chunked (bool): True if this item was created from chunk splitting
        - chunk_index (int): 0-based chunk index (0, 1, 2, ...)
        - total_chunks (int): Total number of chunks created from parent
        - parent_item_id (str): Original item ID before chunking
        - chunk_filename (str): Filename for this chunk

    Validation Rules:
        - If is_chunked=True, chunk_index, total_chunks, and parent_item_id are required
        - chunk_index must be >= 0 and < total_chunks
        - parent_item_id should reference the original conversation UUID
    """

    item_id: str
    """Unique identifier (file path or UUID)."""

    source_path: Path
    """Original source file path."""

    current_step: str
    """Name of the current processing step."""

    status: ItemStatus
    """Current processing status."""

    metadata: dict[str, Any]
    """Arbitrary metadata for the item.

    For chunked items, includes: is_chunked, chunk_index, total_chunks,
    parent_item_id, chunk_filename.
    """

    content: str | None = None
    """Raw content after extraction."""

    transformed_content: str | None = None
    """Content after transformation."""

    output_path: Path | None = None
    """Destination path after loading."""

    error: str | None = None
    """Error message if processing failed."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSONL output."""
        return {
            "item_id": self.item_id,
            "source_path": str(self.source_path),
            "current_step": self.current_step,
            "status": self.status.value,
            "metadata": self.metadata,
            "content": self.content,
            "transformed_content": self.transformed_content,
            "output_path": str(self.output_path) if self.output_path else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessingItem":
        """Deserialize from dictionary."""
        from pathlib import Path

        return cls(
            item_id=data["item_id"],
            source_path=Path(data["source_path"]),
            current_step=data["current_step"],
            status=ItemStatus(data["status"]),
            metadata=data.get("metadata", {}),
            content=data.get("content"),
            transformed_content=data.get("transformed_content"),
            output_path=Path(data["output_path"]) if data.get("output_path") else None,
            error=data.get("error"),
        )


@dataclass
class StepResult:
    """Result of a Step execution.

    Captures success/failure, output data, timing, and item counts.
    """

    success: bool
    """Whether the step completed successfully."""

    output: Any | None
    """Output data from the step (type depends on step)."""

    error: str | None
    """Error message if step failed."""

    duration_ms: int
    """Execution time in milliseconds."""

    items_processed: int
    """Number of items successfully processed."""

    items_failed: int
    """Number of items that failed processing."""


@dataclass
class RetryConfig:
    """Configuration for tenacity retry behavior.

    Supports exponential backoff with jitter for resilient API calls.
    """

    max_attempts: int = 3
    """Maximum number of retry attempts."""

    min_wait_seconds: float = 2.0
    """Minimum wait time between retries."""

    max_wait_seconds: float = 30.0
    """Maximum wait time between retries."""

    exponential_base: float = 2.0
    """Base for exponential backoff calculation."""

    jitter: bool = True
    """Whether to add random jitter to wait times."""

    retry_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (ConnectionError, TimeoutError)
    )
    """Exception types that trigger a retry."""


@dataclass
class StageLogRecord:
    """Log record for Stage processing in JSONL format.

    Each record represents a single item processed through a Stage.
    Used for pipeline_stages.jsonl output.

    Chunk tracking fields (is_chunked, parent_item_id, chunk_index) enable
    tracing output files back to their original input file in 1:N expansion scenarios.
    """

    timestamp: str
    """ISO8601 format timestamp."""

    session_id: str
    """Session identifier."""

    filename: str
    """Source filename being processed."""

    stage: str
    """Stage name (extract, transform, load)."""

    step: str
    """Current step name within the stage."""

    timing_ms: int
    """Processing time in milliseconds."""

    status: str
    """Processing status (success, failed, filtered)."""

    item_id: str | None = None
    """Unique item ID (ProcessingItem.item_id)."""

    file_id: str | None = None
    """File ID (hash) for successful processing."""

    skipped_reason: str | None = None
    """Reason for filtering (if status is filtered)."""

    before_chars: int | None = None
    """Character count before transformation."""

    after_chars: int | None = None
    """Character count after transformation."""

    diff_ratio: float | None = None
    """Ratio of after_chars / before_chars."""

    is_chunked: bool | None = None
    """True if this item was created from chunk splitting."""

    parent_item_id: str | None = None
    """Original item ID before chunking (for tracing 1:N expansion)."""

    chunk_index: int | None = None
    """0-based chunk index (0, 1, 2, ...)."""

    error_message: str | None = None
    """Error message if status is failed."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation (excludes None values).
        """
        result: dict[str, Any] = {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "filename": self.filename,
            "stage": self.stage,
            "step": self.step,
            "timing_ms": self.timing_ms,
            "status": self.status,
        }

        # Include optional fields only if set
        if self.item_id is not None:
            result["item_id"] = self.item_id
        if self.file_id is not None:
            result["file_id"] = self.file_id
        if self.skipped_reason is not None:
            result["skipped_reason"] = self.skipped_reason
        if self.before_chars is not None:
            result["before_chars"] = self.before_chars
        if self.after_chars is not None:
            result["after_chars"] = self.after_chars
        if self.diff_ratio is not None:
            result["diff_ratio"] = self.diff_ratio
        if self.is_chunked is not None:
            result["is_chunked"] = self.is_chunked
        if self.parent_item_id is not None:
            result["parent_item_id"] = self.parent_item_id
        if self.chunk_index is not None:
            result["chunk_index"] = self.chunk_index
        if self.error_message is not None:
            result["error_message"] = self.error_message

        return result


@dataclass
class ErrorDetailRecord:
    """Error detail record for error_details.jsonl.

    Contains detailed error information including backtrace for debugging.
    """

    timestamp: str
    """ISO8601 format timestamp."""

    session_id: str
    """Session identifier."""

    item_id: str
    """Item ID that caused the error."""

    stage: str
    """Stage name (extract, transform, load)."""

    step: str
    """Step name where error occurred."""

    error_type: str
    """Exception type name (e.g., ValueError, JSONDecodeError)."""

    error_message: str
    """Error message."""

    backtrace: str
    """Full exception backtrace."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata (conversation_title, llm_prompt, etc.)."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation.
        """
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "item_id": self.item_id,
            "stage": self.stage,
            "step": self.step,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "backtrace": self.backtrace,
            "metadata": self.metadata,
        }


@dataclass
class CompletedItemsCache:
    """Cache for completed items in Resume mode.

    Reads status="success" items from pipeline_stages.jsonl
    and stores them by stage for skip determination.
    """

    items: set[str]
    """Set of successful item_ids."""

    stage: StageType
    """Target stage (TRANSFORM or LOAD)."""

    @classmethod
    def from_jsonl(cls, jsonl_path: Path, stage: StageType) -> "CompletedItemsCache":
        """Load completed items from pipeline_stages.jsonl.

        Args:
            jsonl_path: Path to pipeline_stages.jsonl
            stage: Target stage (TRANSFORM or LOAD)

        Returns:
            CompletedItemsCache instance with successful items.
        """
        items: set[str] = set()

        # Handle non-existent file gracefully
        if not jsonl_path.exists():
            return cls(items=items, stage=stage)

        # Read JSONL file line by line
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                # Skip empty lines
                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse JSON
                    record = json.loads(line)

                    # Check required fields
                    if "stage" not in record:
                        logging.warning(f"Skipping line {line_num}: missing 'stage' field")
                        continue
                    if "status" not in record:
                        logging.warning(f"Skipping line {line_num}: missing 'status' field")
                        continue
                    if "item_id" not in record:
                        logging.warning(f"Skipping line {line_num}: missing 'item_id' field")
                        continue

                    # Filter by stage
                    if record["stage"] != stage.value:
                        continue

                    # Filter by status
                    if record["status"] != "success":
                        continue

                    # Add to items set
                    items.add(record["item_id"])

                except json.JSONDecodeError as e:
                    logging.warning(f"Skipping line {line_num}: corrupted JSON - {e}")
                    continue

        return cls(items=items, stage=stage)

    def is_completed(self, item_id: str) -> bool:
        """Check if item is completed.

        Args:
            item_id: Item ID to check.

        Returns:
            True if item is in the completed set, False otherwise.
        """
        return item_id in self.items

    def __len__(self) -> int:
        """Return number of completed items.

        Returns:
            Number of items in the cache.
        """
        return len(self.items)


@dataclass
class ChunkedItemsCache:
    """Cache for chunked items with parent tracking.

    Tracks parent_item_id -> chunk_item_ids relationship and requires
    ALL chunks to succeed for the parent to be considered complete.
    """

    items: set[str]
    """Set of successful item_ids (both regular and chunks)."""

    parent_chunks: dict[str, set[str]]
    """Map of parent_item_id -> set of all chunk_item_ids."""

    chunk_success: dict[str, set[str]]
    """Map of parent_item_id -> set of successful chunk_item_ids."""

    stage: StageType
    """Target stage (TRANSFORM or LOAD)."""

    @classmethod
    def from_jsonl(cls, jsonl_path: Path, stage: StageType) -> "ChunkedItemsCache":
        """Load chunked items from pipeline_stages.jsonl.

        Builds parent tracking for chunked items and determines which
        items/chunks can be skipped based on completion status.

        Args:
            jsonl_path: Path to pipeline_stages.jsonl
            stage: Target stage (TRANSFORM or LOAD)

        Returns:
            ChunkedItemsCache instance with tracking data.
        """
        items: set[str] = set()
        parent_chunks: dict[str, set[str]] = {}
        chunk_success: dict[str, set[str]] = {}

        # Handle non-existent file gracefully
        if not jsonl_path.exists():
            return cls(
                items=items,
                parent_chunks=parent_chunks,
                chunk_success=chunk_success,
                stage=stage,
            )

        # Read JSONL file line by line
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                # Skip empty lines
                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse JSON
                    record = json.loads(line)

                    # Check required fields
                    if "stage" not in record:
                        logging.warning(f"Skipping line {line_num}: missing 'stage' field")
                        continue
                    if "status" not in record:
                        logging.warning(f"Skipping line {line_num}: missing 'status' field")
                        continue
                    if "item_id" not in record:
                        logging.warning(f"Skipping line {line_num}: missing 'item_id' field")
                        continue

                    # Filter by stage
                    if record["stage"] != stage.value:
                        continue

                    item_id = record["item_id"]
                    status = record["status"]
                    is_chunked = record.get("is_chunked", False)
                    parent_item_id = record.get("parent_item_id")

                    # Track chunk relationships
                    if is_chunked and parent_item_id:
                        # Initialize parent tracking
                        if parent_item_id not in parent_chunks:
                            parent_chunks[parent_item_id] = set()
                        if parent_item_id not in chunk_success:
                            chunk_success[parent_item_id] = set()

                        # Add chunk to parent tracking
                        parent_chunks[parent_item_id].add(item_id)

                        # Track success
                        if status == "success":
                            chunk_success[parent_item_id].add(item_id)
                            items.add(item_id)  # Also add to items set
                    else:
                        # Regular item (non-chunked)
                        if status == "success":
                            items.add(item_id)

                except json.JSONDecodeError as e:
                    logging.warning(f"Skipping line {line_num}: corrupted JSON - {e}")
                    continue

        return cls(
            items=items,
            parent_chunks=parent_chunks,
            chunk_success=chunk_success,
            stage=stage,
        )

    def is_completed(self, item_id: str) -> bool:
        """Check if item (or all its chunks) completed.

        For regular items, checks items set.
        For chunked items, checks if parent has all chunks successful.

        Args:
            item_id: Item ID to check.

        Returns:
            True if item/parent is completed, False otherwise.
        """
        # Check if this is a chunk by looking for it in parent_chunks values
        for parent_id, chunks in self.parent_chunks.items():
            if item_id in chunks:
                # This is a chunk - check if parent is fully completed
                return self.is_parent_completed(parent_id)

        # Regular item - check items set
        return item_id in self.items

    def is_parent_completed(self, parent_item_id: str) -> bool:
        """Check if all chunks of parent completed.

        Args:
            parent_item_id: Parent item ID to check.

        Returns:
            True if all chunks succeeded, False otherwise.
        """
        all_chunks = self.parent_chunks.get(parent_item_id, set())
        successful_chunks = self.chunk_success.get(parent_item_id, set())

        # Parent is completed only if:
        # 1. It has chunks (len(all_chunks) > 0)
        # 2. All chunks succeeded (all_chunks == successful_chunks)
        return len(all_chunks) > 0 and all_chunks == successful_chunks

    def get_incomplete_chunks(self, parent_item_id: str) -> set[str]:
        """Get chunks that need reprocessing.

        Args:
            parent_item_id: Parent item ID.

        Returns:
            Set of chunk_item_ids that are not completed.
        """
        all_chunks = self.parent_chunks.get(parent_item_id, set())
        successful_chunks = self.chunk_success.get(parent_item_id, set())
        return all_chunks - successful_chunks

    def __len__(self) -> int:
        """Return number of completed items (excluding partial chunks).

        Returns:
            Number of fully completed items.
        """
        # Count regular items
        regular_items = len(self.items)

        # Subtract chunks from regular_items (they're already counted)
        for chunks in self.parent_chunks.values():
            regular_items -= len(chunks & self.items)

        # Count fully completed parents
        completed_parents = sum(
            1 for parent_id in self.parent_chunks if self.is_parent_completed(parent_id)
        )

        return regular_items + completed_parents
