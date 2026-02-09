"""Nodes for Transform pipeline.

These nodes apply LLM knowledge extraction, metadata generation, and Markdown formatting
to ParsedItem data from the Extract pipeline.

Node Signatures (PartitionedDataset pattern):
- Input: dict[str, Callable] - each Callable returns an item dict
- Output: dict[str, dict] - partition_id -> transformed item

Streaming Output:
- extract_knowledge writes each item immediately after LLM processing
- This ensures partial progress is saved even if the node fails midway
- Kedro's PartitionedDataset with overwrite=false handles deduplication
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from obsidian_etl.utils import knowledge_extractor
from obsidian_etl.utils.compression_validator import validate_compression
from obsidian_etl.utils.timing import timed_node

logger = logging.getLogger(__name__)

# Emoji ranges from Unicode 15.1
EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # Emoticons
    "\U0001f300-\U0001f5ff"  # Misc Symbols and Pictographs
    "\U0001f680-\U0001f6ff"  # Transport and Map
    "\U0001f1e0-\U0001f1ff"  # Flags
    "\U00002702-\U000027b0"  # Dingbats
    "\U0001f900-\U0001f9ff"  # Supplemental Symbols
    "\U0001fa00-\U0001fa6f"  # Chess Symbols
    "\U0001fa70-\U0001faff"  # Symbols and Pictographs Extended-A
    "\U00002600-\U000026ff"  # Misc symbols
    "]+",
    flags=re.UNICODE,
)

# Streaming output directory (relative to project root)
# Respects KEDRO_ENV=test for test environment
import os

_env = os.getenv("KEDRO_ENV", "base")
_data_prefix = "data/test" if _env == "test" else "data"
STREAMING_OUTPUT_DIR = Path(f"{_data_prefix}/03_primary/transformed_knowledge")


def _is_empty_content(content: str | None) -> bool:
    """Return True if content is empty or whitespace-only."""
    if content is None:
        return True
    return not content.strip()


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

    STREAMING: Each successfully processed item is immediately saved to disk.
    This ensures partial progress is preserved even if the node fails midway.

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

    node_start = time.time()
    output = {}
    processed = 0
    skipped = 0
    failed = 0
    skipped_empty = 0

    # Ensure streaming output directory exists
    output_dir = Path.cwd() / STREAMING_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    total = len(partitioned_input)

    # Pre-calculate items to process (for accurate progress display)
    to_process = []
    skipped_existing = 0
    skipped_file = 0
    for partition_id, load_func in partitioned_input.items():
        if partition_id in existing_output:
            skipped += 1
            skipped_existing += 1
        elif (output_dir / f"{partition_id}.json").exists():
            skipped += 1
            skipped_file += 1
        else:
            to_process.append((partition_id, load_func))

    remaining = len(to_process)
    logger.info(
        f"extract_knowledge: total={total}, skipped={skipped} "
        f"(existing={skipped_existing}, file={skipped_file}), to_process={remaining}"
    )

    for partition_id, load_func in to_process:
        item = load_func()
        processed += 1
        start_time = time.time()

        logger.info(f"[{processed}/{remaining}] Processing: {partition_id}")

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
            failed += 1
            continue

        # Check for empty summary_content
        summary_content = knowledge.get("summary_content", "")
        if _is_empty_content(summary_content):
            logger.warning(f"Empty summary_content for {partition_id}. Item excluded.")
            skipped_empty += 1
            continue

        # Check content compression ratio using compression_validator
        compression_result = validate_compression(
            original_content=item["content"],
            output_content=summary_content,
            body_content=summary_content,  # For extract_knowledge, body = summary_content
            node_name="extract_knowledge",
        )

        if not compression_result.is_valid:
            # Add review_reason to item (don't exclude)
            review_reason = (
                f"{compression_result.node_name}: "
                f"body_ratio={compression_result.body_ratio:.1%} < "
                f"threshold={compression_result.threshold:.1%}"
            )
            item["review_reason"] = review_reason
            logger.warning(
                f"Low content ratio for {partition_id}: {review_reason}. Item marked for review."
            )
            # DO NOT continue - process the item normally

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
                summary = translated  # Update summary reference for length check

        # Check summary length and warn if too long
        if len(summary) > 500:
            logger.warning(f"Long summary ({len(summary)} chars) for {partition_id}")

        # Add generated_metadata to item
        item["generated_metadata"] = {
            "title": knowledge.get("title", ""),
            "summary": knowledge.get("summary", ""),
            "summary_content": knowledge.get("summary_content", ""),
            "tags": knowledge.get("tags", []),
        }

        # STREAMING: Save immediately to disk
        streaming_file = output_dir / f"{partition_id}.json"
        streaming_file.write_text(json.dumps(item, ensure_ascii=False, indent=2))
        elapsed = time.time() - start_time
        logger.info(f"[{processed}/{remaining}] Done: {partition_id} ({elapsed:.1f}s)")

        output[partition_id] = item

    node_elapsed = time.time() - node_start
    logger.info(
        f"extract_knowledge: total={total}, skipped={skipped} "
        f"(existing={skipped_existing}, file={skipped_file}), "
        f"processed={processed}, succeeded={len(output)}, failed={failed}, "
        f"skipped_empty={skipped_empty} ({node_elapsed:.1f}s)"
    )

    return output


@timed_node
def generate_metadata(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, dict]:
    """Generate metadata dict from generated_metadata.

    Creates the final metadata structure for Obsidian frontmatter:
    - title: from generated_metadata.title
    - created: YYYY-MM-DD from created_at (fallback to current date)
    - tags: from generated_metadata.tags
    - summary: from generated_metadata.summary (for frontmatter)
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

        # Skip placeholder or incomplete items
        if "file_id" not in item:
            logger.debug(f"Skipping incomplete item: {partition_id}")
            continue

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
            "summary": gm.get("summary", ""),
            "source_provider": item["source_provider"],
            "file_id": item["file_id"],
            "normalized": True,
        }

        output[partition_id] = item

    logger.info(f"generate_metadata: processed {len(output)} items")

    return output


@timed_node
def format_markdown(
    partitioned_input: dict[str, Callable],
) -> tuple[dict[str, str], dict[str, str]]:
    """Format items as Markdown with YAML frontmatter.

    Creates final Markdown output:
    - YAML frontmatter from metadata (including summary)
    - Body from generated_metadata.summary_content
    - Output filename from sanitized title
    - Split by review_reason: items with review_reason go to review dict

    Args:
        partitioned_input: Dict of partition_id -> callable that loads item with metadata.

    Returns:
        Tuple of (normal_output, review_output):
        - normal_output: Dict of sanitized_filename -> markdown content (no review_reason)
        - review_output: Dict of sanitized_filename -> markdown content (with review_reason)
    """
    normal_output = {}
    review_output = {}

    for partition_id, load_func in partitioned_input.items():
        item = load_func()

        metadata = item.get("metadata", {})
        gm = item.get("generated_metadata", {})

        # Generate YAML frontmatter
        # Note: We manually format tags to ensure proper indentation
        # Quote all tags to safely handle numeric values (e.g., "8080") as strings
        tags = metadata.get("tags", [])

        def _escape_tag(tag: str) -> str:
            """Escape tag for YAML double-quoted string."""
            return str(tag).replace("\\", "\\\\").replace('"', '\\"')

        tags_yaml = (
            "tags:\n" + "\n".join(f'  - "{_escape_tag(tag)}"' for tag in tags)
            if tags
            else "tags: []"
        )

        # Sanitize title for YAML and filename safety
        # Replace backslashes with forward slashes (common in file paths)
        # Then escape remaining special chars for YAML double-quoted string
        title = metadata.get("title", "")
        title = title.replace("\\", "/")  # Normalize path separators
        title = title.replace('"', '\\"')  # Escape quotes for YAML

        # Get summary for frontmatter (may be empty)
        summary = metadata.get("summary", "")
        # Always quote summary to safely handle special chars (`, :, #, etc.)
        if summary:
            summary_escaped = summary.replace("\\", "\\\\").replace('"', '\\"')
            summary_yaml = f'summary: "{summary_escaped}"'
        else:
            summary_yaml = "summary:"

        frontmatter_parts = [
            f'title: "{title}"',
            f"created: {metadata.get('created', '')}",
            tags_yaml,
            summary_yaml,
            f"source_provider: {metadata.get('source_provider', '')}",
            f"file_id: {metadata.get('file_id', '')}",
            f"normalized: {str(metadata.get('normalized', True)).lower()}",
        ]

        frontmatter_yaml = "\n".join(frontmatter_parts) + "\n"

        # Build body (only summary_content now, summary is in frontmatter)
        body_parts = []
        if gm.get("summary_content"):
            body_parts.append(gm["summary_content"])

        body = "\n\n".join(body_parts)

        # Combine frontmatter + body
        markdown_content = f"---\n{frontmatter_yaml}---\n\n{body}"

        # Sanitize filename
        title = metadata.get("title", "")
        filename = _sanitize_filename(title, item["file_id"])

        # Split by review_reason
        if item.get("review_reason"):
            review_output[filename] = markdown_content
        else:
            normal_output[filename] = markdown_content

    logger.info(
        f"format_markdown: processed {len(normal_output) + len(review_output)} items "
        f"(normal={len(normal_output)}, review={len(review_output)})"
    )

    return normal_output, review_output


def _sanitize_filename(title: str, file_id: str) -> str:
    """Sanitize title to create a valid filename.

    Removes filesystem-unsafe characters and truncates long titles.
    Does NOT add file extension (handled by Kedro's PartitionedDataset filename_suffix).

    Args:
        title: Title string.
        file_id: Fallback file ID if title is empty.

    Returns:
        Sanitized filename without extension.
    """
    if not title or not title.strip():
        # Fallback to file_id
        return file_id[:12]

    # 1. Remove emojis first
    sanitized = EMOJI_PATTERN.sub("", title)

    # 2. Remove unsafe characters (extended to include []()~%)
    unsafe_chars = r'[/\\:*?"<>|\[\]()~%]'
    sanitized = re.sub(unsafe_chars, "", sanitized)

    # 3. Collapse multiple spaces
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    # 4. Truncate to prevent filesystem limits (255 chars including extension)
    max_length = 250
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()

    # 5. Fallback to file_id if empty after sanitization
    if not sanitized:
        return file_id[:12]

    return sanitized
