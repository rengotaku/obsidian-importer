"""Data layer migration script.

This script migrates JSON files from data/07_model_output/ to data/05_model_input/
to separate intermediate JSON data from final Markdown output.

Usage:
    python scripts/migrate_data_layers.py [--dry-run]

The script:
- Moves *.json files from 07_model_output/{subdir} to 05_model_input/{subdir}
- Skips existing files (no overwrite)
- Creates target directories as needed
- Preserves *.md files in 07_model_output/
- Supports dry-run mode for safe preview
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path


# Subdirectories to migrate (JSON only)
_MIGRATION_SUBDIRS = [
    "classified",
    "cleaned",
    "normalized",
    "topic_extracted",
    "vault_determined",
    "organized",
]


@dataclass
class MigrationResult:
    """Result of data layer migration operation.

    Attributes:
        migrated: Number of files successfully migrated
        skipped: Number of files skipped (already exist at target)
        errors: List of error messages encountered during migration
        details: Per-subdirectory migration statistics
    """

    migrated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    details: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def total(self) -> int:
        """Total number of files processed (migrated + skipped)."""
        return self.migrated + self.skipped


def migrate_json_to_model_input(
    source_base: Path | str,
    target_base: Path | str,
    dry_run: bool = False,
) -> MigrationResult:
    """Migrate JSON files from 07_model_output to 05_model_input.

    Args:
        source_base: Base directory containing JSON files (e.g., data/07_model_output)
        target_base: Target directory for migrated files (e.g., data/05_model_input)
        dry_run: If True, count files but don't move them

    Returns:
        MigrationResult with migration statistics
    """
    source_base = Path(source_base)
    target_base = Path(target_base)

    result = MigrationResult()

    # If source doesn't exist, return early
    if not source_base.exists():
        return result

    # Process each subdirectory
    for subdir in _MIGRATION_SUBDIRS:
        source_dir = source_base / subdir
        target_dir = target_base / subdir

        # Initialize per-subdir stats
        subdir_stats = {"migrated": 0, "skipped": 0}

        # Skip if source subdirectory doesn't exist
        if not source_dir.exists():
            continue

        # Find all JSON files in this subdirectory
        json_files = list(source_dir.glob("*.json"))

        for json_file in json_files:
            target_file = target_dir / json_file.name

            # Check if target already exists
            if target_file.exists():
                result.skipped += 1
                subdir_stats["skipped"] += 1
                continue

            # Migrate the file (or simulate in dry-run mode)
            if not dry_run:
                # Create target directory if needed
                target_dir.mkdir(parents=True, exist_ok=True)
                # Move the file
                shutil.move(str(json_file), str(target_file))

            result.migrated += 1
            subdir_stats["migrated"] += 1

        # Store subdirectory stats if any files were processed
        if subdir_stats["migrated"] > 0 or subdir_stats["skipped"] > 0:
            result.details[subdir] = subdir_stats

    return result


def _print_summary(result: MigrationResult, dry_run: bool = False) -> None:
    """Print migration summary to stdout.

    Args:
        result: Migration result to summarize
        dry_run: Whether this was a dry-run operation
    """
    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{mode}Migration Summary")
    print("=" * 50)
    print(f"Total files processed: {result.total}")
    print(f"  Migrated: {result.migrated}")
    print(f"  Skipped:  {result.skipped}")

    if result.details:
        print("\nPer-directory breakdown:")
        for subdir, stats in sorted(result.details.items()):
            print(f"  {subdir}:")
            print(f"    Migrated: {stats['migrated']}")
            print(f"    Skipped:  {stats['skipped']}")

    if result.errors:
        print(f"\nErrors encountered: {len(result.errors)}")
        for error in result.errors:
            print(f"  - {error}")

    if dry_run:
        print("\nNo files were moved (dry-run mode).")
    print()


def main() -> int:
    """CLI entry point for migration script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse command line arguments
    dry_run = "--dry-run" in sys.argv

    # Default paths relative to project root
    project_root = Path(__file__).parent.parent
    source_base = project_root / "data" / "07_model_output"
    target_base = project_root / "data" / "05_model_input"

    print(f"Migrating JSON files from:")
    print(f"  Source: {source_base}")
    print(f"  Target: {target_base}")
    if dry_run:
        print("  Mode: DRY RUN (no files will be moved)")
    print()

    # Perform migration
    result = migrate_json_to_model_input(
        source_base=source_base,
        target_base=target_base,
        dry_run=dry_run,
    )

    # Print summary
    _print_summary(result, dry_run=dry_run)

    # Return success
    return 0


if __name__ == "__main__":
    sys.exit(main())
