"""Session resolution utility for CLI commands.

Provides common logic for handling SESSION-only (Resume) mode across all commands.
"""

from datetime import datetime
from pathlib import Path

from src.etl.core.session import Session, SessionManager


class SessionResolver:
    """Resolve or create sessions for CLI commands.

    Responsibilities:
    - Load existing sessions (Resume mode)
    - Create new sessions
    - Validate existing input directories for Resume mode
    - Record resume timestamps
    """

    def __init__(self, session_base_dir: Path):
        """Initialize SessionResolver.

        Args:
            session_base_dir: Base directory for sessions (.staging/@session/)
        """
        self.manager = SessionManager(session_base_dir)

    def resolve_or_create(
        self, session_id: str | None, debug_mode: bool = True, **create_kwargs
    ) -> tuple[Session, bool]:
        """Resolve existing session or create new one.

        Args:
            session_id: Existing session ID (optional). If None, creates new session.
            debug_mode: Enable debug mode for new sessions.
            **create_kwargs: Additional kwargs for SessionManager.create() (e.g., provider).

        Returns:
            Tuple of (Session, is_resume).
            - Session: Loaded or newly created session.
            - is_resume: True if existing session was loaded, False if new session created.

        Raises:
            ValueError: If session_id specified but session not found.
        """
        if session_id:
            # Resume mode: load existing session
            if not self.manager.exists(session_id):
                raise ValueError(f"Session not found: {session_id}")

            session = self.manager.load(session_id)
            # Record resume time
            session.resumed_at = datetime.now()
            self.manager.save(session)
            return session, True
        else:
            # New session
            session = self.manager.create(debug_mode=debug_mode, **create_kwargs)
            self.manager.save(session)
            return session, False

    def validate_existing_input(self, session: Session, phase_type: str) -> Path | None:
        """Validate that extract/input/ exists in the session.

        Args:
            session: Session to validate.
            phase_type: Phase type ("import" or "organize").

        Returns:
            Path to extract/input/ if it exists and is non-empty.
            None otherwise.
        """
        extract_input = session.base_path / phase_type / "extract" / "input"
        if extract_input.exists() and any(extract_input.iterdir()):
            return extract_input
        return None
