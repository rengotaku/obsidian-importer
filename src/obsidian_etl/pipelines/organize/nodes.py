"""Nodes for Organize pipeline.

This module implements the organize pipeline nodes:
- classify_genre: Keyword-based genre classification
- extract_topic: LLM-based topic extraction with lowercase normalization
- normalize_frontmatter: Clean up frontmatter fields
- clean_content: Remove excess blank lines and trailing whitespace
- embed_frontmatter_fields: Embed genre, topic, summary into frontmatter content
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path

import requests
import yaml

from obsidian_etl.utils.timing import timed_node

logger = logging.getLogger(__name__)


def _yaml_quote(value: str) -> str:
    """Quote a string value for YAML if it contains special characters.

    YAML special characters that need quoting: : # [ ] { } , & * ? | - < > = ! % @ `
    Also quotes strings that start/end with spaces or contain newlines.
    """
    if value is None:
        return '""'  # Empty quoted string for None

    if not isinstance(value, str):
        return str(value)

    # Characters that require quoting in YAML
    special_chars = set(":,[]{}#&*?|-><=!%@`\"'\n")

    needs_quoting = (
        any(c in value for c in special_chars)
        or value.startswith(" ")
        or value.endswith(" ")
        or value.startswith("-")
        or value.lower() in ("true", "false", "null", "yes", "no", "on", "off")
    )

    if needs_quoting:
        # Escape double quotes and wrap in double quotes
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    return value


@timed_node
def classify_genre(
    partitioned_input: dict[str, Callable],
    params: dict,
    existing_output: dict[str, callable] | None = None,
) -> dict[str, dict]:
    """Classify items into genres based on keyword matching.

    Args:
        partitioned_input: PartitionedDataset-style input (dict of callables)
        params: Parameters dict with genre_keywords mapping
        existing_output: Dict of partition_id -> callable (existing classified items to skip).
                        If None, all items are processed (backward compatibility).

    Returns:
        dict[str, dict]: Items with 'genre' field added.
        Items already in existing_output are skipped.

    Genre classification logic:
    - Check tags and content for genre keywords (from params)
    - First match wins (priority order: engineer, business, economy, daily)
    - No match -> 'other'
    """
    if existing_output is None:
        existing_output = {}

    genre_keywords = params.get("genre_keywords", {})
    result = {}

    for key, load_func in partitioned_input.items():
        # Skip if this partition already exists in output
        if key in existing_output:
            logger.debug(f"Skipping existing partition: {key}")
            continue

        item = load_func()

        # Handle both dict (unit tests) and string (real pipeline) inputs
        if isinstance(item, str):
            # Parse markdown frontmatter
            import re

            import yaml

            # Extract frontmatter
            original_content = item  # Keep original Markdown with frontmatter
            frontmatter_match = re.match(r"^---\n(.*?)\n---\n(.*)", item, re.DOTALL)
            if frontmatter_match:
                frontmatter_text = frontmatter_match.group(1)
                body = frontmatter_match.group(2)
                # Parse YAML frontmatter with error handling
                try:
                    frontmatter = yaml.safe_load(frontmatter_text) or {}
                except yaml.YAMLError as e:
                    # If YAML parse fails, try to extract key fields manually
                    logger.warning(f"YAML parse error for {key}: {e}")
                    frontmatter = {}
                    for line in frontmatter_text.split("\n"):
                        if line.startswith("title:"):
                            frontmatter["title"] = line.split(":", 1)[1].strip().strip('"')
                        elif line.startswith("tags:"):
                            frontmatter["tags"] = []
                # Convert date objects to strings for JSON serialization
                from datetime import date, datetime

                for fkey, fval in frontmatter.items():
                    if isinstance(fval, (date, datetime)):
                        frontmatter[fkey] = str(fval)
                tags = frontmatter.get("tags", [])
                content = body  # Use body for keyword matching
            else:
                tags = []
                frontmatter = {}
                content = original_content

            # Convert to dict format, preserving original content (with frontmatter)
            item = {
                "metadata": frontmatter,
                "content": original_content,
            }
        else:
            # Extract tags and content for matching (dict format)
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


@timed_node
def extract_topic(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, dict]:
    """Extract topic from content using LLM.

    Args:
        partitioned_input: Items with genre field and content
        params: Parameters dict with ollama settings

    Returns:
        dict[str, dict]: Items with 'topic' field added

    Topic extraction logic:
    - LLM extracts main topic from content
    - Normalize to lowercase (AWS -> aws)
    - Preserve spaces (React Native -> react native)
    - Empty string on extraction failure
    """
    result = {}

    for key, load_func_or_item in partitioned_input.items():
        # Handle both callable (real pipeline) and dict (memory dataset in tests)
        if callable(load_func_or_item):
            item = load_func_or_item()
        else:
            item = load_func_or_item

        content = item.get("content", "")

        # Extract topic via LLM
        topic = _extract_topic_via_llm(content, params)

        # Normalize topic to lowercase (preserve spaces)
        if topic:
            topic = topic.lower()
        else:
            topic = ""

        # Add topic to item
        item["topic"] = topic
        result[key] = item

    return result


def _extract_topic_via_llm(content: str, params: dict) -> str | None:
    """Helper to extract topic via LLM.

    Args:
        content: Markdown content with frontmatter
        params: Parameters dict with ollama settings

    Returns:
        str | None: Extracted topic or None on failure
    """
    ollama_config = params.get("ollama", {})
    model = ollama_config.get("model", "llama3.2:3b")
    base_url = ollama_config.get("base_url", "http://localhost:11434")

    # Extract body text (skip frontmatter)
    body = content
    if content.startswith("---\n"):
        try:
            end_idx = content.index("\n---\n", 4)
            body = content[end_idx + 5 :]
        except ValueError:
            pass

    # Build prompt
    prompt = f"""この会話から主題（トピック）を1つ抽出してください。

会話内容:
{body[:1000]}

主題をカテゴリレベル（1-3単語）で答えてください。
具体的な商品名・料理名・固有名詞ではなく、上位概念で答えてください。

例:
- バナナプリンの作り方 → 離乳食
- iPhone 15 Pro の設定 → スマートフォン
- Claude 3.5 Sonnet の使い方 → AI

抽出できない場合は空文字を返してください。"""

    # Call Ollama API
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        topic = result.get("response", "").strip()
        return topic if topic else None
    except Exception as e:
        logger.warning(f"Failed to extract topic via LLM: {e}")
        return None


@timed_node
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

    for key, load_func_or_item in partitioned_input.items():
        # Handle both callable (real pipeline) and dict (memory dataset in tests)
        if callable(load_func_or_item):
            item = load_func_or_item()
        else:
            item = load_func_or_item

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
                        fm_lines.append(f"  - {_yaml_quote(list_item)}")
                elif isinstance(v, bool):
                    fm_lines.append(f"{k}: {str(v).lower()}")
                else:
                    fm_lines.append(f"{k}: {_yaml_quote(v)}")
            fm_lines.append("---")

            normalized_content = "\n".join(fm_lines) + "\n" + body
            item["content"] = normalized_content

        except (ValueError, yaml.YAMLError) as e:
            logger.warning(f"Failed to parse frontmatter for {key}: {e}")

        result[key] = item

    return result


@timed_node
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

    for key, load_func_or_item in partitioned_input.items():
        # Handle both callable (real pipeline) and dict (memory dataset in tests)
        if callable(load_func_or_item):
            item = load_func_or_item()
        else:
            item = load_func_or_item

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


@timed_node
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


@timed_node
def embed_frontmatter_fields(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, str]:
    """Embed genre, topic, summary, review_reason into frontmatter content.

    Args:
        partitioned_input: Items with content, genre, topic, metadata, and optional review_reason
        params: Parameters dict (unused)

    Returns:
        dict[str, str]: Dict of filename -> markdown content with updated frontmatter

    No file I/O - replaces move_to_vault.
    Returns dict[filename, markdown_content].
    """
    result = {}

    for key, load_func_or_item in partitioned_input.items():
        # Handle both callable (real pipeline) and dict (memory dataset in tests)
        if callable(load_func_or_item):
            item = load_func_or_item()
        else:
            item = load_func_or_item

        content = item.get("content", "")
        genre = item.get("genre", "other")
        topic = item.get("topic", "")
        review_reason = item.get("review_reason")

        # Extract summary from metadata (may be in metadata or generated_metadata)
        summary = ""
        if "metadata" in item and "summary" in item["metadata"]:
            summary = item["metadata"]["summary"]
        elif "generated_metadata" in item and "summary" in item["generated_metadata"]:
            summary = item["generated_metadata"]["summary"]

        # Embed fields in frontmatter
        updated_content = _embed_fields_in_frontmatter(
            content, genre, topic, summary, review_reason
        )

        # Use partition key as output key (already sanitized filename from format_markdown)
        result[key] = updated_content

    return result


def _embed_fields_in_frontmatter(
    content: str,
    genre: str,
    topic: str,
    summary: str,
    review_reason: str | None = None,
) -> str:
    """Helper to embed fields into frontmatter.

    Args:
        content: Markdown with YAML frontmatter
        genre: Genre classification
        topic: Topic (may be empty)
        summary: Summary text (may be empty)
        review_reason: Review reason (optional, only for items flagged for review)

    Returns:
        str: Markdown with updated frontmatter
    """
    # Check if content has frontmatter
    if not content.startswith("---\n"):
        # No frontmatter, create one
        fm = {
            "summary": summary,
            "genre": genre,
            "topic": topic,
        }
        if review_reason:
            fm["review_reason"] = review_reason
        fm_lines = ["---"]
        for k, v in fm.items():
            fm_lines.append(f"{k}: {_yaml_quote(v)}")
        fm_lines.append("---")
        return "\n".join(fm_lines) + "\n" + content

    # Find frontmatter boundaries
    try:
        end_idx = content.index("\n---\n", 4)
        frontmatter_text = content[4:end_idx]  # Skip first "---\n"
        body = content[end_idx + 5 :]  # Skip "\n---\n"

        # Parse YAML
        frontmatter = yaml.safe_load(frontmatter_text) or {}

        # Add new fields
        frontmatter["summary"] = summary
        frontmatter["genre"] = genre
        frontmatter["topic"] = topic
        if review_reason:
            frontmatter["review_reason"] = review_reason

        # Rebuild content with updated frontmatter
        # Manual formatting to match expected format (2-space indent for list items)
        fm_lines = ["---"]
        for k, v in frontmatter.items():
            if isinstance(v, list):
                fm_lines.append(f"{k}:")
                for list_item in v:
                    fm_lines.append(f"  - {_yaml_quote(list_item)}")
            elif isinstance(v, bool):
                fm_lines.append(f"{k}: {str(v).lower()}")
            else:
                fm_lines.append(f"{k}: {_yaml_quote(v)}")
        fm_lines.append("---")

        return "\n".join(fm_lines) + "\n" + body

    except (ValueError, yaml.YAMLError) as e:
        logger.warning(f"Failed to parse frontmatter: {e}")
        # Return original content if parsing fails
        return content


@timed_node
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
