"""ETL pipeline error hierarchy.

Defines custom exception classes for different levels of the pipeline:
- StepError: Item-level errors (recorded, processing continues)
- StageError: Stage-level errors (processing stops)
- PhaseError: Phase-level errors (session stops)
"""


class StepError(Exception):
    """Step-level error for individual item processing.

    Raised when processing a single item fails. These errors are:
    - Recorded to errors.jsonl
    - Counted towards error threshold (20%)
    - Processing continues with next item

    If error rate exceeds 20%, escalates to StageError.

    Attributes:
        message: Error description
        item_id: ID of the failed item (optional)
        retry_count: Number of retries attempted (optional)

    Examples:
        - JSON parse error for single conversation
        - Ollama timeout after retries
        - Missing required field in item data
    """

    def __init__(
        self,
        message: str,
        item_id: str | None = None,
        retry_count: int = 0,
    ):
        """Initialize StepError.

        Args:
            message: Error description.
            item_id: ID of the failed item.
            retry_count: Number of retries attempted.
        """
        super().__init__(message)
        self.item_id = item_id
        self.retry_count = retry_count


class StageError(Exception):
    """Stage-level error that stops the current stage.

    Raised when:
    1. Error rate exceeds 20% threshold (StepError escalation)
    2. Stage initialization fails (e.g., output folder creation)
    3. Unexpected error occurs during stage processing

    Results in:
    - Phase status set to CRASHED
    - Processing stops immediately
    - Error recorded in phase.json

    Examples:
        - 25% of items failed (exceeds 20% threshold)
        - Cannot create output directory
        - Configuration error
    """

    pass


class PhaseError(Exception):
    """Phase-level error that stops the entire phase.

    Raised when:
    1. Phase initialization fails
    2. Invalid configuration (e.g., unknown provider)
    3. Session corruption

    Results in:
    - Session status set to FAILED
    - Exit code 1
    - Error recorded in session.json

    Examples:
        - Invalid provider specified
        - Session folder cannot be created
        - Missing required configuration
    """

    pass
