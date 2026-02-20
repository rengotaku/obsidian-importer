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


def resolve_vault_destination(
    organized_files: dict[str, Callable] | dict[str, str],
    params: dict,
) -> dict[str, dict]:
    """Resolve Vault destination paths for organized files.

    Args:
        organized_files: PartitionedDataset-style input (dict of callables or strings)
        params: Parameters dict with vault_base_path and genre_vault_mapping

    Returns:
        dict[partition_key, VaultDestination]: Destination information for each file.
        VaultDestination dict contains:
        - vault_name: Target Vault name
        - subfolder: Subfolder (topic), or empty string
        - file_name: Output file name
        - full_path: Complete destination path
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

    Args:
        destinations: dict[partition_key, VaultDestination]

    Returns:
        list[ConflictInfo]: List of conflict information dicts.
        ConflictInfo dict contains:
        - source_file: Source partition key
        - destination: Destination path
        - conflict_type: "exists"
        - existing_size: File size in bytes
        - existing_mtime: File modification timestamp
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

    Args:
        destinations: dict[partition_key, VaultDestination]
        conflicts: list[ConflictInfo]

    Returns:
        dict: Summary information with:
        - total_files: Total number of files
        - total_conflicts: Number of conflicts detected
        - vault_distribution: dict[vault_name, count]
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
