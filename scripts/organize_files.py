#!/usr/bin/env python3
"""Frontmatter-based file organizer for Obsidian vault.

Organizes Markdown files based on their frontmatter genre/topic
into a folder structure suitable for Obsidian.

Usage:
    # Preview mode (dry-run)
    python scripts/organize_files.py --dry-run

    # Execute mode
    python scripts/organize_files.py

    # Custom paths
    python scripts/organize_files.py --input /path/to/input --output /path/to/output
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml


def load_config(config_path: str | Path) -> dict:
    """Load YAML configuration file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        dict: Configuration dictionary with at least 'genre_mapping' key

    Raises:
        FileNotFoundError: If configuration file does not exist
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def parse_frontmatter(file_path: str | Path) -> dict:
    """Parse YAML frontmatter from Markdown file.

    Args:
        file_path: Path to Markdown file

    Returns:
        dict: Frontmatter fields as dictionary, empty dict if no valid frontmatter
    """
    path = Path(file_path)
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    # Check for frontmatter delimiters
    if not content.startswith("---\n"):
        return {}

    # Find the closing delimiter
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        return {}

    # Parse YAML frontmatter
    frontmatter_text = parts[1]
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        return frontmatter if isinstance(frontmatter, dict) else {}
    except yaml.YAMLError:
        return {}


def get_genre_mapping(config: dict, genre_en: str) -> str:
    """Get Japanese folder name for English genre.

    Args:
        config: Configuration dictionary with 'genre_mapping' key
        genre_en: English genre name

    Returns:
        str: Japanese folder name, 'その他' if genre not found
    """
    genre_mapping = config.get("genre_mapping", {})
    return genre_mapping.get(genre_en, "その他")


def sanitize_topic(topic: str) -> str:
    """Replace special characters with underscore for safe filenames.

    Args:
        topic: Topic string potentially containing special characters

    Returns:
        str: Sanitized topic with special chars replaced by underscore
    """
    if not topic:
        return ""

    # Replace OS-unsafe characters with underscore
    # Special chars: / \ : * ? " < > |
    unsafe_chars = r'[/\\:*?"<>|]'
    return re.sub(unsafe_chars, "_", topic)


def scan_files(input_dir: str | Path) -> list:
    """Scan directory for Markdown files with frontmatter.

    Args:
        input_dir: Directory to scan for .md files

    Returns:
        list: List of dicts with 'path' and 'frontmatter' keys
    """
    input_path = Path(input_dir)
    files = []

    if not input_path.exists():
        return files

    for md_file in input_path.glob("*.md"):
        frontmatter = parse_frontmatter(md_file)
        files.append({"path": md_file, "frontmatter": frontmatter})

    return files


def generate_preview(config: dict, input_dir: str | Path, output_dir: str | Path = None) -> str:
    """Generate preview of file organization plan.

    Args:
        config: Configuration dictionary
        input_dir: Input directory path
        output_dir: Output directory path (optional)

    Returns:
        str: Formatted preview text with genre counts and folder existence
    """
    files = scan_files(input_dir)

    if not files:
        return "対象ファイルが見つかりませんでした。"

    # Count files by genre
    genre_counts = {}
    for file_info in files:
        frontmatter = file_info["frontmatter"]
        genre_en = frontmatter.get("genre", "other")
        genre_ja = get_genre_mapping(config, genre_en)

        genre_counts[genre_ja] = genre_counts.get(genre_ja, 0) + 1

    # Build preview output
    lines = []
    lines.append("振り分けプレビュー:")
    lines.append("")
    lines.append(f"総ファイル数: {len(files)}")
    lines.append("")
    lines.append("ジャンル別件数:")
    for genre_ja, count in sorted(genre_counts.items()):
        lines.append(f"  {genre_ja}: {count}")

    # Check folder existence if output_dir provided
    if output_dir:
        lines.append("")
        lines.append("フォルダ存在確認:")
        output_path = Path(output_dir)
        for genre_ja in sorted(genre_counts.keys()):
            genre_dir = output_path / genre_ja
            exists = genre_dir.exists()
            status = "存在" if exists else "未作成"
            lines.append(f"  {genre_ja}: {status}")

    return "\n".join(lines)


def get_destination_path(config: dict, frontmatter: dict, filename: str, output_dir: Path) -> Path:
    """Calculate destination path based on frontmatter genre and topic.

    Args:
        config: Configuration dictionary with genre_mapping and unclassified_folder
        frontmatter: Parsed frontmatter dictionary
        filename: Filename to use for destination
        output_dir: Base output directory

    Returns:
        Path: Full destination path for the file
    """
    genre_en = frontmatter.get("genre", "")
    topic = frontmatter.get("topic", "")

    # Handle unclassified case (no genre or empty genre)
    if not genre_en:
        unclassified = config.get("unclassified_folder", "unclassified")
        return output_dir / unclassified / filename

    # Map genre to Japanese folder name
    genre_ja = get_genre_mapping(config, genre_en)

    # If no topic, place directly in genre folder
    if not topic:
        return output_dir / genre_ja / filename

    # Sanitize topic and create nested path
    topic_safe = sanitize_topic(topic)
    return output_dir / genre_ja / topic_safe / filename


def move_file(source: Path, dest: Path) -> str:
    """Move file from source to destination with safety checks.

    Args:
        source: Source file path
        dest: Destination file path

    Returns:
        str: Status - "success", "skipped", or "error"
    """
    # Check if source exists
    if not source.exists():
        return "error"

    # Check if destination already exists
    if dest.exists():
        return "skipped"

    # Create destination directory if needed
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Move the file
    try:
        shutil.move(str(source), str(dest))
        return "success"
    except Exception:
        return "error"


def organize_files(config: dict, input_dir: Path, output_dir: Path) -> dict:
    """Organize files based on frontmatter genre/topic.

    Args:
        config: Configuration dictionary
        input_dir: Input directory containing files
        output_dir: Output directory for organized files

    Returns:
        dict: ProcessingSummary with total, success, skipped, error, by_genre counts
    """
    files = scan_files(input_dir)

    summary = {
        "total": len(files),
        "success": 0,
        "skipped": 0,
        "error": 0,
        "by_genre": {},
    }

    for file_info in files:
        source_path = file_info["path"]
        frontmatter = file_info["frontmatter"]
        filename = source_path.name

        # Calculate destination path
        dest_path = get_destination_path(config, frontmatter, filename, output_dir)

        # Move file and track status
        status = move_file(source_path, dest_path)

        # Update counts
        if status == "success":
            summary["success"] += 1
        elif status == "skipped":
            summary["skipped"] += 1
        elif status == "error":
            summary["error"] += 1

        # Track by genre (for successful moves)
        if status == "success":
            genre_en = frontmatter.get("genre", "")
            if genre_en:
                genre_ja = get_genre_mapping(config, genre_en)
            else:
                genre_ja = config.get("unclassified_folder", "unclassified")

            summary["by_genre"][genre_ja] = summary["by_genre"].get(genre_ja, 0) + 1

    return summary


def resolve_paths(
    config: dict,
    input_path: str | None = None,
    output_path: str | None = None,
) -> tuple[Path, Path]:
    """Resolve input and output paths with defaults and ~ expansion.

    Args:
        config: Configuration dictionary with default_input and default_output keys
        input_path: Custom input path (overrides config default if provided)
        output_path: Custom output path (overrides config default if provided)

    Returns:
        tuple[Path, Path]: (input_path, output_path) as Path objects with ~ expanded
    """
    # Use custom path if provided, otherwise use config default
    final_input = input_path if input_path is not None else config.get("default_input", "")
    final_output = output_path if output_path is not None else config.get("default_output", "")

    # Convert to Path and expand ~
    input_p = Path(final_input).expanduser()
    output_p = Path(final_output).expanduser()

    return input_p, output_p


def execute_mode(args) -> int:
    """Handle execute mode (actual file movement).

    Args:
        args: Command-line arguments

    Returns:
        int: Exit code (0 for success)
    """
    try:
        # Load configuration
        config = load_config(args.config)

        # Resolve input/output paths with ~ expansion
        input_dir, output_dir = resolve_paths(config, args.input, args.output)

        # Execute organization
        summary = organize_files(config, input_dir, output_dir)

        # Print summary
        print("ファイル振り分け完了:")
        print(f"  総ファイル数: {summary['total']}")
        print(f"  成功: {summary['success']}")
        print(f"  スキップ: {summary['skipped']}")
        print(f"  エラー: {summary['error']}")

        if summary["by_genre"]:
            print("\nジャンル別件数:")
            for genre_ja, count in sorted(summary["by_genre"].items()):
                print(f"  {genre_ja}: {count}")

        return 0

    except FileNotFoundError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"予期しないエラー: {e}", file=sys.stderr)
        return 1


def preview_mode(args) -> int:
    """Handle preview mode (--dry-run).

    Args:
        args: Command-line arguments

    Returns:
        int: Exit code (0 for success)
    """
    try:
        # Load configuration
        config = load_config(args.config)

        # Resolve input/output paths with ~ expansion
        input_dir, output_dir = resolve_paths(config, args.input, args.output)

        # Generate and display preview
        preview_text = generate_preview(config, input_dir, output_dir)
        print(preview_text)

        return 0

    except FileNotFoundError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"予期しないエラー: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Organize Markdown files based on frontmatter genre/topic"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview mode: show what would be done without moving files",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Input directory containing Markdown files",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory (Obsidian vault root)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="conf/base/genre_mapping.yml",
        help="Path to genre mapping configuration file",
    )

    args = parser.parse_args()

    if args.dry_run:
        return preview_mode(args)

    return execute_mode(args)


if __name__ == "__main__":
    sys.exit(main())
