"""Configuration for ETL pipeline.

Provides:
- Config dataclass for pipeline settings
- Debug mode logging utilities
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Config:
    """Configuration for ETL pipeline.

    Controls debug mode, paths, and logging behavior.
    """

    debug_mode: bool = False
    """Whether debug mode is enabled.

    When True:
    - Detailed logs are written to Stage folders
    - Verbose output is enabled

    When False:
    - Only JSON status files are written
    - Minimal logging
    """

    session_dir: Path = field(
        default_factory=lambda: Path(".staging/@session")
    )
    """Base directory for session folders."""

    log_level: int = logging.INFO
    """Default log level."""

    log_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    """Log message format."""


class DebugLogger:
    """Debug-mode aware logger.

    Writes detailed logs to Stage folders when debug mode is enabled.
    """

    def __init__(
        self,
        name: str,
        config: Config,
        output_path: Path | None = None,
    ):
        """Initialize DebugLogger.

        Args:
            name: Logger name (typically module name).
            config: Pipeline configuration.
            output_path: Optional path for debug log files.
        """
        self.name = name
        self.config = config
        self.output_path = output_path
        self._logger = logging.getLogger(name)
        self._file_handler: logging.FileHandler | None = None

        self._setup_logger()

    def _setup_logger(self) -> None:
        """Configure logger based on debug mode."""
        self._logger.setLevel(self.config.log_level)

        # Remove existing handlers
        self._logger.handlers.clear()

        # Console handler (always present, but level varies)
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(self.config.log_format))

        if self.config.debug_mode:
            console.setLevel(logging.DEBUG)
        else:
            console.setLevel(logging.WARNING)

        self._logger.addHandler(console)

        # File handler (only in debug mode with output path)
        if self.config.debug_mode and self.output_path:
            self._setup_file_handler()

    def _setup_file_handler(self) -> None:
        """Set up file handler for debug logs."""
        if not self.output_path:
            return

        log_file = self.output_path / f"{self.name}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        self._file_handler = logging.FileHandler(log_file, encoding="utf-8")
        self._file_handler.setLevel(logging.DEBUG)
        self._file_handler.setFormatter(
            logging.Formatter(self.config.log_format)
        )
        self._logger.addHandler(self._file_handler)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log debug message (only in debug mode)."""
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(msg, *args, **kwargs)

    def close(self) -> None:
        """Close file handler if present."""
        if self._file_handler:
            self._file_handler.close()
            self._logger.removeHandler(self._file_handler)
            self._file_handler = None


def get_debug_logger(
    name: str,
    config: Config,
    stage_output_path: Path | None = None,
) -> DebugLogger:
    """Get a debug-aware logger.

    Args:
        name: Logger name.
        config: Pipeline configuration.
        stage_output_path: Optional path to Stage output folder for debug logs.

    Returns:
        DebugLogger instance.
    """
    return DebugLogger(name, config, stage_output_path)
