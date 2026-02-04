"""Nodes for Transform pipeline.

These nodes apply LLM knowledge extraction, metadata generation, and Markdown formatting
to ParsedItem data from the Extract pipeline.

Node Signatures (PartitionedDataset pattern):
- Input: dict[str, Callable] - each Callable returns an item dict
- Output: dict[str, dict] - partition_id -> transformed item
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from datetime import datetime

import yaml

from obsidian_etl.utils import knowledge_extractor

logger = logging.getLogger(__name__)


def extract_knowledge(
    partitioned_input: dict[str, Callable],
    params: dict,
    existing_output: dict[str, callable] | None = None,
) -> dict[str, dict]:
    """Extract knowledge from ParsedItems using LLM.

    Calls Ollama LLM for each item to extract:
    - Title (Japanese)
    - Summary (Japanese, with English translation if needed)
    - Summary content (detailed Markdown)
    - Tags (optional)

    Args:
        partitioned_input: Dict of partition_id -> callable that loads ParsedItem.
        params: Pipeline params including ollama settings.
        existing_output: Dict of partition_id -> callable (existing transformed items to skip).
                        If None, all items are processed (backward compatibility).

    Returns:
        Dict of partition_id -> item with generated_metadata added.
        Items that fail LLM extraction are excluded (logged).
        Items already in existing_output are skipped (no LLM call).
    """
    if existing_output is None:
        existing_output = {}

    output = {}

    for partition_id, load_func in partitioned_input.items():
        # Skip if this partition already exists in output
        if partition_id in existing_output:
            logger.debug(f"Skipping existing partition (no LLM call): {partition_id}")
            continue

        item = load_func()

        # Extract knowledge via LLM
        knowledge, error = knowledge_extractor.extract_knowledge(
            content=item["content"],
            conversation_name=item.get("conversation_name"),
            created_at=item.get("created_at"),
            source_provider=item["source_provider"],
            params=params,
        )

        if error or not knowledge:
            logger.warning(f"LLM extraction failed for {partition_id}: {error}. Item excluded.")
            continue

        # Check if summary is in English and translate if needed
        summary = knowledge.get("summary", "")
        if knowledge_extractor.is_english_summary(summary):
            logger.debug(f"English summary detected for {partition_id}, translating...")
            translated, trans_error = knowledge_extractor.translate_summary(summary, params)
            if trans_error:
                logger.warning(
                    f"Translation failed for {partition_id}: {trans_error}. Using original."
                )
            else:
                knowledge["summary"] = translated

        # Add generated_metadata to item
        item["generated_metadata"] = {
            "title": knowledge.get("title", ""),
            "summary": knowledge.get("summary", ""),
            "summary_content": knowledge.get("summary_content", ""),
            "tags": knowledge.get("tags", []),
        }

        output[partition_id] = item

    logger.info(
        f"extract_knowledge: processed {len(partitioned_input)} items, "
        f"{len(output)} succeeded, {len(partitioned_input) - len(output)} failed"
    )

    return output


def generate_metadata(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, dict]:
    """Generate metadata dict from generated_metadata.

    Creates the final metadata structure for Obsidian frontmatter:
    - title: from generated_metadata.title
    - created: YYYY-MM-DD from created_at (fallback to current date)
    - tags: from generated_metadata.tags
    - source_provider: preserved from ParsedItem
    - file_id: preserved from ParsedItem
    - normalized: always True

    Args:
        partitioned_input: Dict of partition_id -> callable that loads item with generated_metadata.
        params: Pipeline params (not used currently).

    Returns:
        Dict of partition_id -> item with metadata dict added.
    """
    output = {}

    for partition_id, load_func in partitioned_input.items():
        item = load_func()

        gm = item.get("generated_metadata", {})
        created_at = item.get("created_at")

        # Extract date from ISO 8601 or fallback to current date
        if created_at:
            try:
                # Parse ISO 8601 and extract date part
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                created_date = dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                created_date = datetime.now().strftime("%Y-%m-%d")
        else:
            created_date = datetime.now().strftime("%Y-%m-%d")

        item["metadata"] = {
            "title": gm.get("title", ""),
            "created": created_date,
            "tags": gm.get("tags", []),
            "source_provider": item["source_provider"],
            "file_id": item["file_id"],
            "normalized": True,
        }

        output[partition_id] = item

    logger.info(f"generate_metadata: processed {len(output)} items")

    return output


def format_markdown(
    partitioned_input: dict[str, Callable],
) -> dict[str, dict]:
    """Format items as Markdown with YAML frontmatter.

    Creates final Markdown output:
    - YAML frontmatter from metadata
    - Body from generated_metadata.summary_content
    - Output filename from sanitized title

    Args:
        partitioned_input: Dict of partition_id -> callable that loads item with metadata.

    Returns:
        Dict of sanitized_filename -> item with "content" field containing Markdown.
    """
    output = {}

    for partition_id, load_func in partitioned_input.items():
        item = load_func()

        metadata = item.get("metadata", {})
        gm = item.get("generated_metadata", {})

        # Generate YAML frontmatter
        # Note: We manually format tags to ensure proper indentation
        tags = metadata.get("tags", [])
        tags_yaml = "tags:\n" + "\n".join(f"  - {tag}" for tag in tags) if tags else "tags: []"

        frontmatter_parts = [
            f"title: {metadata.get('title', '')}",
            f"created: {metadata.get('created', '')}",
            tags_yaml,
            f"source_provider: {metadata.get('source_provider', '')}",
            f"file_id: {metadata.get('file_id', '')}",
            f"normalized: {str(metadata.get('normalized', True)).lower()}",
        ]

        frontmatter_yaml = "\n".join(frontmatter_parts) + "\n"

        # Build body (summary + summary_content)
        body_parts = []
        if gm.get("summary"):
            body_parts.append(f"## 要約\n\n{gm['summary']}")
        if gm.get("summary_content"):
            body_parts.append(gm["summary_content"])

        body = "\n\n".join(body_parts)

        # Combine frontmatter + body
        markdown_content = f"---\n{frontmatter_yaml}---\n\n{body}"

        # Sanitize filename
        title = metadata.get("title", "")
        filename = _sanitize_filename(title, item["file_id"])

        # Store with content key
        output[filename] = {
            **item,
            "content": markdown_content,
        }

    logger.info(f"format_markdown: processed {len(output)} items")

    return output


def _sanitize_filename(title: str, file_id: str) -> str:
    """Sanitize title to create a valid filename.

    Removes filesystem-unsafe characters and truncates long titles.

    Args:
        title: Title string.
        file_id: Fallback file ID if title is empty.

    Returns:
        Sanitized filename ending with .md
    """
    if not title or not title.strip():
        # Fallback to file_id
        return f"{file_id[:12]}.md"

    # Remove unsafe characters
    unsafe_chars = r'[/\\:*?"<>|]'
    sanitized = re.sub(unsafe_chars, "", title)

    # Collapse multiple spaces
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    # Truncate to prevent filesystem limits (255 chars including .md)
    max_length = 250
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()

    # Ensure non-empty after sanitization
    if not sanitized:
        return f"{file_id[:12]}.md"

    return f"{sanitized}.md"
