"""JSONL-based error logging for ETL pipeline.

Replaces the Markdown-based error_writer.py with a more efficient
JSONL format for error logging.

Output: errors.jsonl (1 line per error, appended)
"""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class ErrorLogEntry:
    """Single error log entry (1 JSONL line).

    Compact schema with essential fields only.
    Long text fields are truncated to keep file size manageable.

    Attributes:
        timestamp: ISO 8601 format timestamp
        item_id: Item identifier (12-char hex)
        step: Step name where error occurred
        error_type: Exception class name
        error_message: Error description
        conversation_title: Conversation title (optional)
        retry_count: Number of retries attempted (default: 0)
        llm_prompt: LLM prompt (truncated if > 5000 chars)
        llm_output: LLM raw output (truncated if > 5000 chars)
        error_position: Character position of error (optional)
        error_context: Context text around error (optional)
    """

    timestamp: str
    item_id: str
    step: str
    error_type: str
    error_message: str
    conversation_title: str | None = None
    retry_count: int = 0
    llm_prompt: str | None = None
    llm_output: str | None = None
    error_position: int | None = None
    error_context: str | None = None


class ErrorLogger:
    """JSONL-based error logger.

    Appends error entries to errors.jsonl file (1 line per error).
    Thread-safe for concurrent writes.

    Example:
        >>> logger = ErrorLogger(Path(".staging/@session/import/errors.jsonl"))
        >>> logger.log_error(
        ...     item_id="abc123def456",
        ...     step="extract_knowledge",
        ...     error=StepError("JSON parse error"),
        ...     conversation_title="Test",
        ...     llm_prompt="...",
        ... )
    """

    # Maximum length for text fields (truncated beyond this)
    MAX_TEXT_LENGTH = 5000

    def __init__(self, errors_file: Path):
        """Initialize ErrorLogger.

        Args:
            errors_file: Path to errors.jsonl file.
        """
        self.errors_file = errors_file
        self.errors_file.parent.mkdir(parents=True, exist_ok=True)

    def log_error(
        self,
        item_id: str,
        step: str,
        error: Exception,
        **extra_fields,
    ) -> None:
        """Log error to JSONL file.

        Appends a single JSON line to errors.jsonl.
        Long text fields are automatically truncated.

        Args:
            item_id: Item identifier.
            step: Step name.
            error: Exception object.
            **extra_fields: Additional fields (conversation_title, llm_prompt, etc.)
        """
        # Build base entry
        entry_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "item_id": item_id,
            "step": step,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        # Add optional fields
        entry_data["conversation_title"] = extra_fields.get("conversation_title")
        entry_data["retry_count"] = getattr(error, "retry_count", 0)
        entry_data["error_position"] = extra_fields.get("error_position")
        entry_data["error_context"] = extra_fields.get("error_context")

        # Truncate long text fields
        entry_data["llm_prompt"] = self._truncate(extra_fields.get("llm_prompt"))
        entry_data["llm_output"] = self._truncate(extra_fields.get("llm_output"))

        # Create entry
        entry = ErrorLogEntry(**entry_data)

        # Append to JSONL file (1 line per error)
        with self.errors_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def _truncate(self, text: str | None) -> str | None:
        """Truncate text to MAX_TEXT_LENGTH.

        Args:
            text: Text to truncate.

        Returns:
            Truncated text or None if input is None.
        """
        if text is None:
            return None

        if len(text) <= self.MAX_TEXT_LENGTH:
            return text

        return text[: self.MAX_TEXT_LENGTH] + "... (truncated)"

    def count_errors(self) -> int:
        """Count total errors in the log.

        Returns:
            Number of lines in errors.jsonl (0 if file doesn't exist).
        """
        if not self.errors_file.exists():
            return 0

        with self.errors_file.open("r", encoding="utf-8") as f:
            return sum(1 for _ in f)

    def load_errors(self) -> list[ErrorLogEntry]:
        """Load all errors from JSONL file.

        Returns:
            List of ErrorLogEntry objects.
        """
        if not self.errors_file.exists():
            return []

        errors = []
        with self.errors_file.open("r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                errors.append(ErrorLogEntry(**data))

        return errors
