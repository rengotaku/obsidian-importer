"""Phase dataclass and PhaseManager for ETL pipeline.

Manages Phase lifecycle, folder creation, and status tracking.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .status import PhaseStatus
from .types import PhaseType, StageType
from .stage import Stage
from .step import Step


@dataclass
class Phase:
    """A processing phase in the ETL pipeline.

    Each phase (IMPORT, ORGANIZE) contains multiple stages (Extract, Transform, Load).
    Status is tracked in phase.json.
    """

    phase_type: PhaseType
    """Type of the phase (IMPORT, ORGANIZE)."""

    base_path: Path
    """Path to the phase folder."""

    status: PhaseStatus = PhaseStatus.PENDING
    """Current execution status."""

    stages: dict[StageType, Stage] = field(default_factory=dict)
    """Stages within this phase, keyed by StageType."""

    steps: list[Step] = field(default_factory=list)
    """All steps across all stages (for phase-level tracking)."""

    started_at: datetime | None = None
    """When the phase started execution."""

    completed_at: datetime | None = None
    """When the phase completed (success or failure)."""

    error_count: int = 0
    """Number of items that failed processing."""

    success_count: int = 0
    """Number of items successfully processed."""

    @property
    def status_file(self) -> Path:
        """Path to phase.json status file."""
        return self.base_path / "phase.json"

    @property
    def pipeline_stages_jsonl(self) -> Path:
        """Path to pipeline_stages.jsonl log file.

        This file contains JSONL records for all items processed through this phase.
        Used by BaseStage._write_jsonl_log() for automatic logging.
        """
        return self.base_path / "pipeline_stages.jsonl"

    def to_dict(self) -> dict[str, Any]:
        """Convert Phase to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the Phase.
        """
        return {
            "phase_type": self.phase_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_count": self.error_count,
            "success_count": self.success_count,
            "stages": {k.value: v.to_dict() for k, v in self.stages.items()},
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], base_path: Path) -> "Phase":
        """Create Phase from dictionary.

        Args:
            data: Dictionary with phase data.
            base_path: Path to the phase folder.

        Returns:
            Phase instance.
        """
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])

        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        stages = {}
        for stage_key, stage_data in data.get("stages", {}).items():
            stage_type = StageType(stage_key)
            stages[stage_type] = Stage.from_dict(stage_data)

        steps = [Step.from_dict(s) for s in data.get("steps", [])]

        return cls(
            phase_type=PhaseType(data["phase_type"]),
            base_path=base_path,
            status=PhaseStatus(data["status"]),
            stages=stages,
            steps=steps,
            started_at=started_at,
            completed_at=completed_at,
            error_count=data.get("error_count", 0),
            success_count=data.get("success_count", 0),
        )


class PhaseManager:
    """Manages Phase lifecycle and persistence.

    Handles:
    - Phase folder creation with stage subfolders
    - Status tracking in phase.json
    - Loading and saving phase state
    """

    def __init__(self, session_path: Path):
        """Initialize PhaseManager.

        Args:
            session_path: Path to the session folder.
        """
        self.session_path = session_path

    def create(self, phase_type: PhaseType) -> Phase:
        """Create a new Phase with folder structure.

        Creates:
        - Phase folder (import/ or organize/)
        - Stage folders (extract/, transform/, load/)
        - Stage subfolders (input/, output/)

        Args:
            phase_type: Type of phase to create.

        Returns:
            Phase instance with folders created.
        """
        phase_path = self.session_path / phase_type.value
        phase_path.mkdir(parents=True, exist_ok=True)

        phase = Phase(
            phase_type=phase_type,
            base_path=phase_path,
        )

        # Create stages with folder structure
        for stage_type in StageType:
            stage = Stage.create_for_phase(stage_type, phase_path)
            stage.ensure_folders()
            phase.stages[stage_type] = stage

        return phase

    def save(self, phase: Phase) -> None:
        """Save Phase state to phase.json.

        Args:
            phase: Phase instance to save.
        """
        data = phase.to_dict()

        with open(phase.status_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, phase_type: PhaseType) -> Phase:
        """Load Phase from phase.json.

        Args:
            phase_type: Type of phase to load.

        Returns:
            Phase instance loaded from disk.

        Raises:
            FileNotFoundError: If phase.json doesn't exist.
        """
        phase_path = self.session_path / phase_type.value
        status_file = phase_path / "phase.json"

        if not status_file.exists():
            raise FileNotFoundError(f"Phase not found: {status_file}")

        with open(status_file, encoding="utf-8") as f:
            data = json.load(f)

        return Phase.from_dict(data, phase_path)

    def exists(self, phase_type: PhaseType) -> bool:
        """Check if a phase exists.

        Args:
            phase_type: Type of phase to check.

        Returns:
            True if phase.json exists.
        """
        phase_path = self.session_path / phase_type.value
        status_file = phase_path / "phase.json"
        return status_file.exists()
