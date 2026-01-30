"""Step dataclass and StepTracker for ETL pipeline.

Represents individual processing steps within a Stage.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .status import StepStatus


@dataclass
class Step:
    """A single processing step within a Stage.

    Tracks execution state, timing, and item counts.
    """

    step_name: str
    """Unique name of the step (e.g., 'parse_json', 'validate')."""

    status: StepStatus = StepStatus.PENDING
    """Current execution status."""

    started_at: datetime | None = None
    """When the step started execution."""

    completed_at: datetime | None = None
    """When the step completed (success or failure)."""

    duration_ms: int | None = None
    """Execution time in milliseconds."""

    error: str | None = None
    """Error message if step failed."""

    items_processed: int = 0
    """Number of items successfully processed."""

    items_failed: int = 0
    """Number of items that failed processing."""

    def to_dict(self) -> dict[str, Any]:
        """Convert Step to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the Step.
        """
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "items_processed": self.items_processed,
            "items_failed": self.items_failed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Step":
        """Create Step from dictionary.

        Args:
            data: Dictionary with step data.

        Returns:
            Step instance.
        """
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])

        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        return cls(
            step_name=data["step_name"],
            status=StepStatus(data["status"]),
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=data.get("duration_ms"),
            error=data.get("error"),
            items_processed=data.get("items_processed", 0),
            items_failed=data.get("items_failed", 0),
        )


class StepTracker:
    """Tracks execution of a Step with timing and status updates.

    Usage:
        step = Step(step_name="validate")
        tracker = StepTracker(step)

        tracker.start()
        try:
            # ... processing ...
            tracker.complete(items_processed=10, items_failed=0)
        except Exception as e:
            tracker.fail(error=str(e))
    """

    def __init__(self, step: Step):
        """Initialize tracker for a Step.

        Args:
            step: The Step instance to track.
        """
        self.step = step
        self._start_time: datetime | None = None

    def start(self) -> None:
        """Mark step as started.

        Sets started_at and status to RUNNING.
        """
        self._start_time = datetime.now()
        self.step.started_at = self._start_time
        self.step.status = StepStatus.RUNNING

    def complete(self, items_processed: int = 0, items_failed: int = 0) -> None:
        """Mark step as completed successfully.

        Args:
            items_processed: Number of items successfully processed.
            items_failed: Number of items that failed (for partial success).
        """
        now = datetime.now()
        self.step.completed_at = now
        self.step.status = StepStatus.COMPLETED
        self.step.items_processed = items_processed
        self.step.items_failed = items_failed

        if self._start_time:
            delta = now - self._start_time
            self.step.duration_ms = int(delta.total_seconds() * 1000)

    def fail(
        self,
        error: str,
        items_processed: int = 0,
        items_failed: int = 0,
    ) -> None:
        """Mark step as failed.

        Args:
            error: Error message describing the failure.
            items_processed: Number of items processed before failure.
            items_failed: Number of items that failed.
        """
        now = datetime.now()
        self.step.completed_at = now
        self.step.status = StepStatus.FAILED
        self.step.error = error
        self.step.items_processed = items_processed
        self.step.items_failed = items_failed

        if self._start_time:
            delta = now - self._start_time
            self.step.duration_ms = int(delta.total_seconds() * 1000)

    def skip(self, reason: str | None = None) -> None:
        """Mark step as skipped.

        Args:
            reason: Optional reason for skipping.
        """
        self.step.status = StepStatus.SKIPPED
        if reason:
            self.step.error = f"Skipped: {reason}"
