"""Shared utilities for CLI commands."""

import os
from enum import IntEnum
from pathlib import Path


class ExitCode(IntEnum):
    """CLI exit codes."""

    SUCCESS = 0
    ERROR = 1
    INPUT_NOT_FOUND = 2
    OLLAMA_ERROR = 3
    PARTIAL = 4
    ALL_FAILED = 5


# Default session directory
DEFAULT_SESSION_DIR = Path(".staging/@session")


def get_session_dir() -> Path:
    """Get session directory from environment or default."""
    env_dir = os.environ.get("ETL_SESSION_DIR")
    if env_dir:
        return Path(env_dir)
    return DEFAULT_SESSION_DIR
