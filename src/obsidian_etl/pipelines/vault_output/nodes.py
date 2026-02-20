"""Nodes for Vault Output pipeline.

This module implements the vault_output pipeline nodes:
- sanitize_topic: Clean topic for folder name usage
- resolve_vault_destination: Map genre to Vault and construct destination paths
- check_conflicts: Detect existing files at destination paths
- log_preview_summary: Generate and log preview summary information
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def sanitize_topic(topic: str) -> str:
    r"""Sanitize topic for use as folder name.

    Args:
        topic: Topic string from frontmatter

    Returns:
        Sanitized topic with / and \ replaced by _, stripped of whitespace.
        Empty string if topic is empty.
    """
    if not topic:
        return ""
    sanitized = topic.replace("/", "_").replace("\\", "_")
    return sanitized.strip()


def find_incremented_path(dst: Path) -> Path:
    """Find next available incremented path.

    Args:
        dst: Original destination path (e.g., /path/to/file.md)

    Returns:
        Path: Next available incremented path (e.g., file_1.md, file_2.md, ...)
    """
    stem = dst.stem  # "file"
    suffix = dst.suffix  # ".md"
    parent = dst.parent

    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def resolve_vault_destination(
    organized_files: dict[str, Callable] | dict[str, str],
    params: dict,
) -> dict[str, dict]:
    """Resolve Vault destination paths for organized files.

    This function maps genre metadata to Vault directories and constructs
    full destination paths including topic subfolders.

    Args:
        organized_files: PartitionedDataset-style input (dict of callables or strings).
                        Each value is either a callable returning markdown content
                        or markdown content string with frontmatter.
        params: Parameters dict with vault_base_path and genre_vault_mapping.
                vault_base_path: Root directory for all Vaults
                genre_vault_mapping: dict mapping genre to Vault name

    Returns:
        dict[partition_key, VaultDestination]: Destination information for each file.
        VaultDestination dict contains:
        - vault_name: Target Vault name (from genre_vault_mapping)
        - subfolder: Subfolder path (sanitized topic), or empty string
        - file_name: Output file name (title.md)
        - full_path: Complete destination path string

    Example:
        Input file with genre="ai", topic="machine-learning", title="ML Guide"
        → vault_name="エンジニア", subfolder="machine-learning",
          full_path="/path/to/Vaults/エンジニア/machine-learning/ML Guide.md"
    """
    vault_base_path = params.get("vault_base_path", "")
    genre_vault_mapping = params.get("genre_vault_mapping", {})

    destinations = {}

    for key, content_or_func in organized_files.items():
        # Handle both callable (PartitionedDataset) and string (unit tests)
        if callable(content_or_func):
            content = content_or_func()
        else:
            content = content_or_func

        # Parse frontmatter
        if not content.startswith("---"):
            logger.warning(f"File {key} has no frontmatter, skipping")
            continue

        parts = content.split("---", 2)
        if len(parts) < 3:
            logger.warning(f"File {key} has invalid frontmatter, skipping")
            continue

        frontmatter_str = parts[1]
        frontmatter = yaml.safe_load(frontmatter_str)

        # Extract fields
        title = frontmatter.get("title", "Untitled")
        genre = frontmatter.get("genre", "other")
        topic = frontmatter.get("topic", "")

        # Map genre to vault
        vault_name = genre_vault_mapping.get(genre, "その他")

        # Sanitize topic for folder name
        sanitized_topic = sanitize_topic(topic)

        # Construct file name
        file_name = f"{title}.md"

        # Construct full path
        if sanitized_topic:
            full_path = Path(vault_base_path) / vault_name / sanitized_topic / file_name
            subfolder = sanitized_topic
        else:
            full_path = Path(vault_base_path) / vault_name / file_name
            subfolder = ""

        destinations[key] = {
            "vault_name": vault_name,
            "subfolder": subfolder,
            "file_name": file_name,
            "full_path": str(full_path),
        }

    return destinations


def check_conflicts(destinations: dict[str, dict]) -> list[dict]:
    """Check for conflicts at destination paths.

    Detects existing files at destination paths that would be
    overwritten during copy operations.

    Args:
        destinations: dict[partition_key, VaultDestination] from resolve_vault_destination

    Returns:
        list[ConflictInfo]: List of conflict information dicts.
        Empty list if no conflicts found.
        ConflictInfo dict contains:
        - source_file: Source partition key (e.g., "note1")
        - destination: Destination path string
        - conflict_type: Always "exists" for existing files
        - existing_size: File size in bytes (from os.stat)
        - existing_mtime: File modification timestamp (from os.stat)

    Note:
        Only checks for file existence. Directory creation conflicts
        are not checked as they are handled automatically during copy.
    """
    conflicts = []

    for key, dest in destinations.items():
        full_path = Path(dest["full_path"])

        if full_path.exists():
            stat = os.stat(full_path)
            conflicts.append(
                {
                    "source_file": key,
                    "destination": str(full_path),
                    "conflict_type": "exists",
                    "existing_size": stat.st_size,
                    "existing_mtime": stat.st_mtime,
                }
            )

    return conflicts


def log_preview_summary(
    destinations: dict[str, dict],
    conflicts: list[dict],
) -> dict:
    """Generate and log preview summary.

    Logs destination distribution and conflicts to logger.info.
    Used by organize_preview pipeline for pre-copy validation.

    Args:
        destinations: dict[partition_key, VaultDestination] from resolve_vault_destination
        conflicts: list[ConflictInfo] from check_conflicts

    Returns:
        dict: Summary information with:
        - total_files: Total number of files to copy
        - total_conflicts: Number of conflicts detected
        - vault_distribution: dict[vault_name, count] showing file counts per Vault

    Side effects:
        Logs formatted summary table to logger.info, including:
        - Total file count
        - Conflict count
        - Vault distribution table
        - First 10 conflicts (if any)
    """
    total_files = len(destinations)
    total_conflicts = len(conflicts)

    # Calculate vault distribution
    vault_distribution = {}
    for dest in destinations.values():
        vault_name = dest["vault_name"]
        vault_distribution[vault_name] = vault_distribution.get(vault_name, 0) + 1

    # Log summary
    logger.info("=" * 80)
    logger.info("Vault Output Preview Summary")
    logger.info("=" * 80)
    logger.info(f"Total files: {total_files}")
    logger.info(f"Total conflicts: {total_conflicts}")
    logger.info("")
    logger.info("Vault distribution:")
    for vault_name, count in sorted(vault_distribution.items()):
        logger.info(f"  {vault_name}: {count} files")
    logger.info("")

    if conflicts:
        logger.info("Conflicts detected:")
        for conflict in conflicts[:10]:  # Show first 10
            logger.info(f"  - {conflict['source_file']} -> {conflict['destination']}")
        if len(conflicts) > 10:
            logger.info(f"  ... and {len(conflicts) - 10} more")
    else:
        logger.info("No conflicts detected")

    logger.info("=" * 80)

    return {
        "total_files": total_files,
        "total_conflicts": total_conflicts,
        "vault_distribution": vault_distribution,
    }


def copy_to_vault(
    organized_files: dict[str, Callable] | dict[str, str],
    destinations: dict[str, dict],
    params: dict,
) -> list[dict]:
    """Copy organized files to Vault destinations.

    Handles file copying with conflict resolution strategies:
    - skip: Skip existing files (default)
    - overwrite: Replace existing files
    - increment: Save as file_1.md, file_2.md, etc.

    Args:
        organized_files: PartitionedDataset-style input (dict of callables or strings).
                        Keys must match destinations keys.
        destinations: dict[partition_key, VaultDestination] from resolve_vault_destination
        params: Parameters dict with conflict_handling mode.
                conflict_handling: "skip" (default), "overwrite", or "increment"

    Returns:
        list[CopyResult]: Results for each copy operation.
        CopyResult dict contains:
        - source: Source partition key
        - destination: Destination path string (or None if skipped/error)
        - status: "copied", "skipped", "overwritten", "incremented", or "error"
        - error_message: Error description (or None if successful)

    Side effects:
        - Creates destination directories as needed (parents=True)
        - Writes files to destination paths
        - Logs copy operations to logger.info
        - Logs errors to logger.warning

    Error handling:
        - PermissionError: Caught and returned as error status, does not raise
        - Missing source: Returned as error status
        - Creates parent directories automatically
    """
    conflict_handling = params.get("conflict_handling", "skip")
    results = []

    for key, dest in destinations.items():
        content_or_func = organized_files.get(key)
        if content_or_func is None:
            results.append(
                {
                    "source": key,
                    "destination": None,
                    "status": "error",
                    "error_message": f"Source file {key} not found",
                }
            )
            continue

        content = content_or_func() if callable(content_or_func) else content_or_func
        full_path = Path(dest["full_path"])

        # Handle existing file (conflict)
        try:
            file_exists = full_path.exists()
        except PermissionError:
            file_exists = False  # Can't check, will fail on write anyway

        is_incremented = False
        if file_exists:
            if conflict_handling == "skip":
                results.append(
                    {
                        "source": key,
                        "destination": None,
                        "status": "skipped",
                        "error_message": None,
                    }
                )
                logger.info(f"Skipped existing file: {full_path}")
                continue
            elif conflict_handling == "overwrite":
                # Will overwrite below, mark as overwritten
                pass
            elif conflict_handling == "increment":
                # Find next available incremented path
                full_path = find_incremented_path(full_path)
                is_incremented = True

        # Create parent directory if needed
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            results.append(
                {
                    "source": key,
                    "destination": None,
                    "status": "error",
                    "error_message": str(e),
                }
            )
            logger.warning(f"Permission error creating directory for {key}: {e}")
            continue

        # Write file
        try:
            full_path.write_text(content, encoding="utf-8")
            # Determine status based on conflict handling
            if is_incremented:
                status = "incremented"
                logger.info(f"Incremented {key} -> {full_path}")
            elif file_exists and conflict_handling == "overwrite":
                status = "overwritten"
                logger.info(f"Overwritten {key} -> {full_path}")
            else:
                status = "copied"
                logger.info(f"Copied {key} -> {full_path}")
            results.append(
                {
                    "source": key,
                    "destination": str(full_path),
                    "status": status,
                    "error_message": None,
                }
            )
        except PermissionError as e:
            results.append(
                {
                    "source": key,
                    "destination": None,
                    "status": "error",
                    "error_message": str(e),
                }
            )
            logger.warning(f"Permission error writing {key}: {e}")

    return results


def log_copy_summary(copy_results: list[dict]) -> dict:
    """Generate and log copy summary.

    Aggregates copy operation results and logs summary statistics.
    Used by organize_to_vault pipeline for post-copy reporting.

    Args:
        copy_results: list[CopyResult] from copy_to_vault

    Returns:
        dict: Summary information with:
        - total: Total number of operations
        - copied: Count of newly copied files
        - overwritten: Count of replaced files
        - incremented: Count of files saved with incremented names
        - skipped: Count of skipped files (existing files in skip mode)
        - errors: Count of failed operations

    Side effects:
        Logs formatted summary table to logger.info, including:
        - Operation counts for each status
        - Error details (source and error_message) for failed operations
    """
    total = len(copy_results)
    copied = sum(1 for r in copy_results if r["status"] == "copied")
    overwritten = sum(1 for r in copy_results if r["status"] == "overwritten")
    incremented = sum(1 for r in copy_results if r["status"] == "incremented")
    skipped = sum(1 for r in copy_results if r["status"] == "skipped")
    errors = sum(1 for r in copy_results if r["status"] == "error")

    logger.info("=" * 80)
    logger.info("Vault Output Copy Summary")
    logger.info("=" * 80)
    logger.info(f"Total files: {total}")
    logger.info(f"  Copied: {copied}")
    if overwritten > 0:
        logger.info(f"  Overwritten: {overwritten}")
    if incremented > 0:
        logger.info(f"  Incremented: {incremented}")
    logger.info(f"  Skipped: {skipped}")
    if errors > 0:
        logger.info(f"  Errors: {errors}")
        for r in copy_results:
            if r["status"] == "error":
                logger.warning(f"    {r['source']}: {r['error_message']}")
    logger.info("=" * 80)

    return {
        "total": total,
        "copied": copied,
        "overwritten": overwritten,
        "incremented": incremented,
        "skipped": skipped,
        "errors": errors,
    }
