"""Nodes for Organize pipeline.

This module implements the organize pipeline nodes:
- classify_genre: Keyword-based genre classification
- normalize_frontmatter: Clean up frontmatter fields
- clean_content: Remove excess blank lines and trailing whitespace
- determine_vault_path: Map genre to vault directory
- move_to_vault: Write files to vault directories
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def classify_genre(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]:
    """Classify items into genres based on keyword matching.

    Args:
        partitioned_input: PartitionedDataset-style input (dict of callables)
        params: Parameters dict with genre_keywords mapping

    Returns:
        dict[str, dict]: Items with 'genre' field added

    Genre classification logic:
    - Check tags and content for genre keywords (from params)
    - First match wins (priority order: engineer, business, economy, daily)
    - No match -> 'other'
    """
    genre_keywords = params.get("genre_keywords", {})
    result = {}

    for key, load_func in partitioned_input.items():
        item = load_func()

        # Extract tags and content for matching
        tags = item.get("metadata", {}).get("tags", [])
        content = item.get("content", "")

        # Check tags first (higher priority)
        tags_text = " ".join(tags)

        # Try to match genre keywords in tags first (priority order)
        genre = "other"  # default
        for genre_name in ["engineer", "business", "economy", "daily"]:
            keywords = genre_keywords.get(genre_name, [])
            matched = False
            for keyword in keywords:
                if keyword in tags_text:
                    genre = genre_name
                    matched = True
                    break
            if matched:
                break

        # If no match in tags, check content
        if genre == "other":
            for genre_name in ["engineer", "business", "economy", "daily"]:
                keywords = genre_keywords.get(genre_name, [])
                matched = False
                for keyword in keywords:
                    if keyword in content:
                        genre = genre_name
                        matched = True
                        break
                if matched:
                    break

        # Add genre to item
        item["genre"] = genre
        result[key] = item

    return result


def normalize_frontmatter(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]:
    """Normalize frontmatter by removing unnecessary fields and ensuring normalized=True.

    Args:
        partitioned_input: Items with content containing YAML frontmatter
        params: Parameters dict (unused)

    Returns:
        dict[str, dict]: Items with normalized frontmatter

    Removes: draft, private, slug, lastmod, keywords
    Ensures: normalized: true is present
    """
    result = {}

    # Fields to remove from frontmatter
    unnecessary_fields = {"draft", "private", "slug", "lastmod", "keywords"}

    for key, load_func in partitioned_input.items():
        item = load_func()
        content = item.get("content", "")

        # Parse frontmatter
        if not content.startswith("---\n"):
            # No frontmatter, skip
            result[key] = item
            continue

        # Find frontmatter boundaries
        try:
            end_idx = content.index("\n---\n", 4)
            frontmatter_text = content[4:end_idx]  # Skip first "---\n"
            body = content[end_idx + 5 :]  # Skip "\n---\n"

            # Parse YAML
            frontmatter = yaml.safe_load(frontmatter_text) or {}

            # Remove unnecessary fields
            for field in unnecessary_fields:
                frontmatter.pop(field, None)

            # Ensure normalized=True
            frontmatter["normalized"] = True

            # Rebuild content with normalized frontmatter
            # Manual formatting to match expected format (2-space indent for list items)
            fm_lines = ["---"]
            for k, v in frontmatter.items():
                if isinstance(v, list):
                    fm_lines.append(f"{k}:")
                    for list_item in v:
                        fm_lines.append(f"  - {list_item}")
                elif isinstance(v, bool):
                    fm_lines.append(f"{k}: {str(v).lower()}")
                else:
                    fm_lines.append(f"{k}: {v}")
            fm_lines.append("---")

            normalized_content = "\n".join(fm_lines) + "\n" + body
            item["content"] = normalized_content

        except (ValueError, yaml.YAMLError) as e:
            logger.warning(f"Failed to parse frontmatter for {key}: {e}")

        result[key] = item

    return result


def clean_content(partitioned_input: dict[str, Callable]) -> dict[str, dict]:
    """Clean content by removing excess blank lines and trailing whitespace.

    Args:
        partitioned_input: Items with content to clean

    Returns:
        dict[str, dict]: Items with cleaned content

    Cleaning logic:
    - Reduce 3+ consecutive blank lines to 1
    - Strip trailing whitespace from lines (except in frontmatter)
    - Preserve frontmatter section as-is
    """
    result = {}

    for key, load_func in partitioned_input.items():
        item = load_func()
        content = item.get("content", "")

        if not content.startswith("---\n"):
            # No frontmatter, clean entire content
            cleaned_content = _clean_text(content)
            item["content"] = cleaned_content
            result[key] = item
            continue

        # Find frontmatter boundaries
        try:
            end_idx = content.index("\n---\n", 4)
            frontmatter_section = content[: end_idx + 5]  # Include "\n---\n"
            body = content[end_idx + 5 :]

            # Clean only the body (preserve frontmatter)
            cleaned_body = _clean_text(body)
            item["content"] = frontmatter_section + cleaned_body

        except ValueError:
            # No closing frontmatter delimiter, clean entire content
            item["content"] = _clean_text(content)

        result[key] = item

    return result


def _clean_text(text: str) -> str:
    """Helper to clean text content.

    Args:
        text: Text to clean

    Returns:
        str: Cleaned text
    """
    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]

    # Reduce consecutive blank lines to max 1
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        is_blank = len(line) == 0
        if is_blank and prev_blank:
            # Skip consecutive blank line
            continue
        cleaned_lines.append(line)
        prev_blank = is_blank

    return "\n".join(cleaned_lines)


def determine_vault_path(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]:
    """Determine vault path based on genre.

    Args:
        partitioned_input: Items with genre field
        params: Parameters dict with vaults mapping

    Returns:
        dict[str, dict]: Items with vault_path and final_path fields

    Mapping:
    - genre -> vault_path (from params["vaults"])
    - final_path = vault_path + output_filename
    - Unknown genre -> fallback to 'other' vault
    """
    vaults = params.get("vaults", {})
    result = {}

    for key, load_func in partitioned_input.items():
        item = load_func()
        genre = item.get("genre", "other")
        output_filename = item.get("output_filename", "unknown.md")

        # Map genre to vault path (fallback to 'other')
        vault_path = vaults.get(genre, vaults.get("other", "Vaults/その他/"))

        # Construct final path
        final_path = vault_path + output_filename

        item["vault_path"] = vault_path
        item["final_path"] = final_path
        result[key] = item

    return result


def move_to_vault(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]:
    """Write files to vault directories.

    Args:
        partitioned_input: Items with final_path and content
        params: Parameters dict with base_path

    Returns:
        dict[str, dict]: OrganizedItem dicts (E-4 data model)

    File writing logic:
    - Write content to base_path + final_path
    - Create directories if they don't exist (mkdir -p)
    - Use UTF-8 encoding
    - Return OrganizedItem dict with required fields
    """
    base_path = Path(params.get("base_path", "."))
    result = {}

    for key, load_func in partitioned_input.items():
        item = load_func()
        final_path = item.get("final_path", "")
        content = item.get("content", "")

        if not final_path:
            logger.warning(f"Item {key} has no final_path, skipping")
            continue

        # Construct full file path
        full_path = base_path / final_path

        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file (UTF-8 encoding)
        try:
            full_path.write_text(content, encoding="utf-8")
            logger.info(f"Wrote file: {full_path}")
        except Exception as e:
            logger.error(f"Failed to write {full_path}: {e}")
            continue

        # Return OrganizedItem (E-4 data model)
        organized_item = {
            "item_id": item.get("item_id", key),
            "file_id": item.get("file_id", ""),
            "genre": item.get("genre", "other"),
            "vault_path": item.get("vault_path", ""),
            "final_path": final_path,
            "output_filename": item.get("output_filename", ""),
            "content": content,  # Include content in case it's needed downstream
        }

        # Preserve metadata if present
        if "metadata" in item:
            organized_item["metadata"] = item["metadata"]

        result[key] = organized_item

    return result
