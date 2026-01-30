"""Calculate statistics from pipeline_stages.jsonl.

Provides functions to compute session and phase statistics dynamically
from the pipeline execution log (pipeline_stages.jsonl).
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PhaseStatistics:
    """Statistics calculated from pipeline_stages.jsonl."""

    success_count: int
    """Number of successfully processed items."""

    error_count: int
    """Number of failed items."""

    skipped_count: int
    """Number of skipped items."""

    total_count: int
    """Total number of items processed."""


def calculate_phase_stats(phase_dir: Path) -> PhaseStatistics:
    """Calculate phase statistics from pipeline_stages.jsonl.

    Args:
        phase_dir: Path to phase directory (e.g., .staging/@session/ID/import/)

    Returns:
        PhaseStatistics with counts calculated from pipeline log.
    """
    pipeline_log = phase_dir / "pipeline_stages.jsonl"

    if not pipeline_log.exists():
        return PhaseStatistics(
            success_count=0,
            error_count=0,
            skipped_count=0,
            total_count=0,
        )

    # Count unique items at load stage (final stage determines success/failure)
    load_items: dict[str, str] = {}  # item_id -> final_status

    try:
        with open(pipeline_log, encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    stage = record.get("stage", "")
                    status = record.get("status", "")

                    # Priority for unique conversation identification:
                    # 1. item_id (unique per conversation, available in new logs)
                    # 2. parent_item_id (for chunked items, original conversation ID)
                    # 3. file_id (SHA256 hash of conversation, if available)
                    # 4. filename (last resort, may not be unique for ZIP imports)
                    item_id = record.get("item_id")
                    if not item_id:
                        item_id = record.get("parent_item_id")
                    if not item_id:
                        item_id = record.get("file_id")
                    if not item_id:
                        item_id = record.get("filename", "unknown")

                    # Track load stage (final processing stage)
                    if stage == "load":
                        load_items[item_id] = status
                except json.JSONDecodeError:
                    continue  # Skip malformed lines
    except Exception:
        return PhaseStatistics(
            success_count=0,
            error_count=0,
            skipped_count=0,
            total_count=0,
        )

    # Count statuses
    success_count = sum(1 for status in load_items.values() if status == "success")
    error_count = sum(1 for status in load_items.values() if status == "failed")
    skipped_count = sum(1 for status in load_items.values() if status == "skipped")
    total_count = len(load_items)

    return PhaseStatistics(
        success_count=success_count,
        error_count=error_count,
        skipped_count=skipped_count,
        total_count=total_count,
    )


def count_extract_items(phase_dir: Path) -> int:
    """Count items extracted by Extract stage.

    Args:
        phase_dir: Path to phase directory (e.g., .staging/@session/ID/import/)

    Returns:
        Number of items successfully extracted (to be processed by Transform).
    """
    pipeline_log = phase_dir / "pipeline_stages.jsonl"

    if not pipeline_log.exists():
        return 0

    extract_items: set[str] = set()

    try:
        with open(pipeline_log, encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    stage = record.get("stage", "")
                    status = record.get("status", "")

                    # Only count successful extract items
                    if stage == "extract" and status == "success":
                        # Use item_id for unique counting
                        item_id = record.get("item_id")
                        if item_id:
                            extract_items.add(item_id)
                except json.JSONDecodeError:
                    continue
    except Exception:
        return 0

    return len(extract_items)


def has_failed_items(phase_dir: Path) -> bool:
    """Check if phase has any failed items.

    Args:
        phase_dir: Path to phase directory

    Returns:
        True if phase has failed items, False otherwise
    """
    stats = calculate_phase_stats(phase_dir)
    return stats.error_count > 0
