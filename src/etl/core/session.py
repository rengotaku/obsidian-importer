"""Session dataclass and SessionManager for ETL pipeline.

Manages Session lifecycle, folder creation, and persistence.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .status import SessionStatus


@dataclass
class CompletedInformation:
    """Information about completed phase processing.

    Contains final counts and completion timestamp.
    """

    success_count: int
    """Number of items successfully processed."""

    error_count: int
    """Number of items that failed processing."""

    skipped_count: int
    """Number of items skipped (already processed in Resume mode)."""

    completed_at: str
    """ISO format timestamp when the phase completed."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success_count": self.success_count,
            "error_count": self.error_count,
            "skipped_count": self.skipped_count,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CompletedInformation":
        """Create CompletedInformation from dictionary."""
        return cls(
            success_count=data["success_count"],
            error_count=data["error_count"],
            skipped_count=data["skipped_count"],
            completed_at=data["completed_at"],
        )


@dataclass
class PhaseStats:
    """Statistics for a phase.

    Records phase status, expected item count, and completion information.
    """

    status: str
    """Phase completion status: 'completed', 'partial', 'failed', 'crashed', or 'in_progress'."""

    expected_total_item_count: int = 0
    """Expected number of items to be processed (from Extract stage output)."""

    completed_information: CompletedInformation | None = None
    """Completion details (only present when phase completes)."""

    error: str | None = None
    """Error message if phase crashed with unhandled exception (optional)."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation (excludes None values).
        """
        result: dict[str, Any] = {
            "status": self.status,
            "expected_total_item_count": self.expected_total_item_count,
        }
        if self.completed_information is not None:
            result["completed_information"] = self.completed_information.to_dict()
        if self.error is not None:
            result["error"] = self.error
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PhaseStats":
        """Create PhaseStats from dictionary.

        Supports both new format (with completed_information) and legacy format
        (with top-level success_count, error_count, completed_at).

        Args:
            data: Dictionary with phase stats data.

        Returns:
            PhaseStats instance.
        """
        # New format: completed_information nested
        if "completed_information" in data:
            completed_info = CompletedInformation.from_dict(data["completed_information"])
            return cls(
                status=data["status"],
                expected_total_item_count=data.get("expected_total_item_count", 0),
                completed_information=completed_info,
                error=data.get("error"),
            )

        # Legacy format: top-level fields (backward compatibility)
        completed_info = None
        if "completed_at" in data:
            completed_info = CompletedInformation(
                success_count=data.get("success_count", 0),
                error_count=data.get("error_count", 0),
                skipped_count=data.get("skipped_count", 0),
                completed_at=data["completed_at"],
            )

        return cls(
            status=data["status"],
            expected_total_item_count=data.get("expected_total_item_count", 0),
            completed_information=completed_info,
            error=data.get("error"),
        )


# Session ID format: YYYYMMDD_HHMMSS
SESSION_ID_PATTERN = re.compile(r"^\d{8}_\d{6}$")


def generate_session_id() -> str:
    """Generate a new session ID.

    Returns:
        Session ID in YYYYMMDD_HHMMSS format.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def validate_session_id(session_id: str) -> bool:
    """Validate session ID format.

    Checks:
    - Format matches YYYYMMDD_HHMMSS
    - Values represent a valid datetime

    Args:
        session_id: Session ID to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not session_id or not SESSION_ID_PATTERN.match(session_id):
        return False

    # Check if it's a valid datetime
    try:
        datetime.strptime(session_id, "%Y%m%d_%H%M%S")
        return True
    except ValueError:
        return False


@dataclass
class Session:
    """A processing session in the ETL pipeline.

    Each session has a unique ID (timestamp) and contains multiple phases.
    Phases are tracked with statistics (success_count, error_count, status).
    """

    session_id: str
    """Unique identifier in YYYYMMDD_HHMMSS format."""

    base_path: Path
    """Path to the session folder."""

    created_at: datetime = field(default_factory=datetime.now)
    """When the session was created."""

    resumed_at: datetime | None = None
    """When the session was resumed (Resume mode only)."""

    status: SessionStatus = SessionStatus.PENDING
    """Current execution status."""

    phases: dict[str, PhaseStats] = field(default_factory=dict)
    """Dictionary of phase names to statistics."""

    debug_mode: bool = False
    """Whether debug mode is enabled."""

    provider: str | None = None
    """Source provider: 'claude', 'openai', or 'github' (Resume mode only)."""

    def to_dict(self) -> dict[str, Any]:
        """Convert Session to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the Session.
        """
        result = {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "phases": {name: stats.to_dict() for name, stats in self.phases.items()},
            "debug_mode": self.debug_mode,
        }
        if self.resumed_at is not None:
            result["resumed_at"] = self.resumed_at.isoformat()
        if self.provider is not None:
            result["provider"] = self.provider
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any], base_path: Path) -> "Session":
        """Create Session from dictionary.

        Supports both old format (list of phase names) and new format (dict of PhaseStats)
        for backward compatibility.

        Args:
            data: Dictionary with session data.
            base_path: Path to the session folder.

        Returns:
            Session instance.
        """
        created_at = datetime.fromisoformat(data["created_at"])
        resumed_at = datetime.fromisoformat(data["resumed_at"]) if "resumed_at" in data else None

        # Handle both old (list) and new (dict) phases format
        phases_data = data.get("phases", [])
        if isinstance(phases_data, list):
            # Old format: list of phase names -> convert to dict with default stats
            phases = {
                name: PhaseStats(
                    status="completed",
                    expected_total_item_count=0,
                    completed_information=CompletedInformation(
                        success_count=0,
                        error_count=0,
                        skipped_count=0,
                        completed_at=created_at.isoformat(),
                    ),
                )
                for name in phases_data
            }
        else:
            # New format: dict of PhaseStats
            phases = {name: PhaseStats.from_dict(stats) for name, stats in phases_data.items()}

        return cls(
            session_id=data["session_id"],
            base_path=base_path,
            created_at=created_at,
            resumed_at=resumed_at,
            status=SessionStatus(data["status"]),
            phases=phases,
            debug_mode=data.get("debug_mode", False),
            provider=data.get("provider"),  # Backward compatibility: None if not present
        )


class SessionManager:
    """Manages Session lifecycle and persistence.

    Handles:
    - Session folder creation
    - Status tracking in session.json
    - Loading and saving session state
    - Listing all sessions
    """

    def __init__(self, base_dir: Path):
        """Initialize SessionManager.

        Args:
            base_dir: Base directory for session folders (e.g., .staging/@session).
        """
        self.base_dir = base_dir

    def create(self, debug_mode: bool = False, provider: str | None = None) -> Session:
        """Create a new Session with folder.

        Args:
            debug_mode: Whether to enable debug mode.
            provider: Source provider ('claude', 'openai', 'github'). Required for new sessions.

        Returns:
            Session instance with folder created.
        """
        session_id = generate_session_id()
        session_path = self.base_dir / session_id

        # Create session folder
        session_path.mkdir(parents=True, exist_ok=True)

        session = Session(
            session_id=session_id,
            base_path=session_path,
            debug_mode=debug_mode,
            provider=provider,
        )

        return session

    def save(self, session: Session) -> None:
        """Save Session state to session.json.

        Args:
            session: Session instance to save.
        """
        session_file = session.base_path / "session.json"
        data = session.to_dict()

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, session_id: str) -> Session:
        """Load Session from session.json.

        Args:
            session_id: Session ID to load.

        Returns:
            Session instance loaded from disk.

        Raises:
            FileNotFoundError: If session.json doesn't exist.
        """
        session_path = self.base_dir / session_id
        session_file = session_path / "session.json"

        if not session_file.exists():
            raise FileNotFoundError(f"Session not found: {session_file}")

        with open(session_file, encoding="utf-8") as f:
            data = json.load(f)

        return Session.from_dict(data, session_path)

    def exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: Session ID to check.

        Returns:
            True if session.json exists.
        """
        session_path = self.base_dir / session_id
        session_file = session_path / "session.json"
        return session_file.exists()

    def list_sessions(self) -> list[str]:
        """List all session IDs.

        Returns:
            List of session IDs (folder names that match the pattern).
        """
        if not self.base_dir.exists():
            return []

        sessions = []
        for path in self.base_dir.iterdir():
            if path.is_dir() and validate_session_id(path.name):
                sessions.append(path.name)

        return sorted(sessions)
