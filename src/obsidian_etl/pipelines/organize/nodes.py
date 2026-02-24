"""Nodes for Organize pipeline.

This module implements the organize pipeline nodes:
- extract_topic_and_genre: LLM-based topic and genre extraction
- normalize_frontmatter: Clean up frontmatter fields
- clean_content: Remove excess blank lines and trailing whitespace
- embed_frontmatter_fields: Embed genre, topic, summary into frontmatter content
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import yaml

from obsidian_etl.utils.ollama import call_ollama
from obsidian_etl.utils.ollama_config import get_ollama_config
from obsidian_etl.utils.timing import timed_node

logger = logging.getLogger(__name__)


def _parse_genre_config(genre_vault_mapping: dict) -> tuple[dict, set]:
    """Parse genre config to extract definitions and valid genres.

    Args:
        genre_vault_mapping: Config dict with structure:
            {
                "genre_key": {
                    "vault": "Vault Name",
                    "description": "Genre description"
                }
            }

    Returns:
        tuple[dict, set]: (genre_definitions, valid_genres)
            - genre_definitions: dict mapping genre_key -> description
            - valid_genres: set of valid genre keys (always includes "other")

    Raises:
        ValueError: If any genre is missing the required "vault" key
    """
    # Handle None or empty mapping
    if not genre_vault_mapping:
        logger.warning("genre_vault_mapping is empty, using 'other' only")
        return {"other": "other"}, {"other"}

    # Validate vault existence for all genres before processing
    for genre_key, genre_config in genre_vault_mapping.items():
        if "vault" not in genre_config:
            raise ValueError(f"Genre '{genre_key}' has no vault defined")

    genre_definitions = {}
    valid_genres = set()

    for genre_key, genre_config in genre_vault_mapping.items():
        # Extract description, fallback to genre_key if missing
        description = genre_config.get("description")
        if description is None:
            logger.warning(f"Genre '{genre_key}' has no description, using genre name only")
            description = genre_key

        genre_definitions[genre_key] = description
        valid_genres.add(genre_key)

    # Ensure "other" is always in valid_genres
    if "other" not in valid_genres:
        valid_genres.add("other")

    return genre_definitions, valid_genres


def _build_genre_prompt(genre_definitions: dict) -> str:
    """Build LLM prompt string from genre definitions.

    Args:
        genre_definitions: dict mapping genre_key -> description

    Returns:
        str: Formatted string for LLM prompt with "- key: description" format
             Returns empty string if genre_definitions is empty
    """
    if not genre_definitions:
        return ""

    lines = []
    for genre_key, description in genre_definitions.items():
        lines.append(f"- {genre_key}: {description}")

    return "\n".join(lines)


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
def extract_topic_and_genre(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, dict]:
    """Extract topic and classify genre using LLM.

    Args:
        partitioned_input: PartitionedDataset-style input (dict of callables)
        params: Parameters dict with ollama settings

    Returns:
        dict[str, dict]: Items with 'topic' and 'genre' fields added

    LLM extraction logic:
    - Single LLM call extracts both topic and genre as JSON
    - Topic: normalized to lowercase (1-3 words)
    - Genre: one of 11 predefined categories (ai, devops, engineer, economy, business, health, parenting, travel, lifestyle, daily, other)
    - Fallback: topic="", genre="other" on parsing failure
    """
    result = {}

    for key, load_func in partitioned_input.items():
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
                    if isinstance(fval, date | datetime):
                        frontmatter[fkey] = str(fval)
                content = body  # Use body for extraction
            else:
                frontmatter = {}
                content = original_content

            # Convert to dict format, preserving original content (with frontmatter)
            item = {
                "metadata": frontmatter,
                "content": original_content,
            }
        else:
            # Extract content for LLM (dict format)
            content = item.get("content", "")

        # Extract topic and genre via LLM
        topic, genre = _extract_topic_and_genre_via_llm(content, params)

        # Add fields to item
        item["topic"] = topic
        item["genre"] = genre
        result[key] = item

    return result


def _extract_topic_and_genre_via_llm(content: str, params: dict) -> tuple[str, str]:
    """Helper to extract topic and genre via LLM.

    Args:
        content: Markdown content with frontmatter
        params: Parameters dict with ollama settings and genre_vault_mapping

    Returns:
        tuple[str, str]: (topic, genre) - topic is lowercase, genre from config
                        Returns ("", "other") on extraction failure
    """
    config = get_ollama_config(params, "extract_topic_and_genre")

    # Parse genre config to get dynamic genre definitions
    genre_vault_mapping = params.get("genre_vault_mapping", {})
    genre_definitions, valid_genres = _parse_genre_config(genre_vault_mapping)
    genre_prompt = _build_genre_prompt(genre_definitions)

    # Extract body text (skip frontmatter)
    body = content
    if content.startswith("---\n"):
        try:
            end_idx = content.index("\n---\n", 4)
            body = content[end_idx + 5 :]
        except ValueError:
            pass

    # Build prompts with dynamic genre list
    system_prompt = f"""あなたはコンテンツ分類の専門家です。会話内容から主題とジャンルを抽出してください。

**主題 (topic)**: カテゴリレベル（1-3単語）で答え、具体的な商品名・料理名・固有名詞ではなく、上位概念で答えてください。
例:
- バナナプリンの作り方 → 離乳食
- iPhone 15 Pro の設定 → スマートフォン
- Claude 3.5 Sonnet の使い方 → AI

**ジャンル (genre)**: 以下のいずれか1つを選んでください（必ず小文字で）:
{genre_prompt}

JSON形式で回答してください:
{{"topic": "主題", "genre": "ジャンル"}}

抽出できない場合:
{{"topic": "", "genre": "other"}}"""

    user_message = f"""会話内容:
{body[:1000]}

主題とジャンルをJSON形式で答えてください。"""

    # Call Ollama API
    response, error = call_ollama(
        system_prompt,
        user_message,
        model=config.model,
        base_url=config.base_url,
        timeout=config.timeout,
        temperature=config.temperature,
        num_predict=config.num_predict,
    )

    if error:
        logger.warning(f"Failed to extract topic and genre via LLM: {error}")
        return "", "other"

    # Parse JSON response
    import json

    try:
        result = json.loads(response.strip())
        topic = result.get("topic", "").lower().strip()
        genre = result.get("genre", "other").lower().strip()

        # Validate genre using dynamic valid_genres from config
        if genre not in valid_genres:
            logger.warning(f"Invalid genre '{genre}', defaulting to 'other'")
            genre = "other"

        return topic, genre

    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
        return "", "other"


def _extract_topic_via_llm(content: str, params: dict) -> str | None:
    """Helper to extract topic via LLM.

    Args:
        content: Markdown content with frontmatter
        params: Parameters dict with ollama settings

    Returns:
        str | None: Extracted topic or None on failure
    """
    config = get_ollama_config(params, "extract_topic")

    # Extract body text (skip frontmatter)
    body = content
    if content.startswith("---\n"):
        try:
            end_idx = content.index("\n---\n", 4)
            body = content[end_idx + 5 :]
        except ValueError:
            pass

    # Build prompts
    system_prompt = """あなたはトピック分類の専門家です。会話内容から主題を1つ抽出してください。
主題はカテゴリレベル（1-3単語）で答え、具体的な商品名・料理名・固有名詞ではなく、上位概念で答えてください。

例:
- バナナプリンの作り方 → 離乳食
- iPhone 15 Pro の設定 → スマートフォン
- Claude 3.5 Sonnet の使い方 → AI

抽出できない場合は空文字を返してください。"""

    user_message = f"""会話内容:
{body[:1000]}

主題を1-3単語で答えてください。"""

    # Call Ollama API
    response, error = call_ollama(
        system_prompt,
        user_message,
        model=config.model,
        base_url=config.base_url,
        timeout=config.timeout,
        temperature=config.temperature,
        num_predict=config.num_predict,
    )

    if error:
        logger.warning(f"Failed to extract topic via LLM: {error}")
        return None

    topic = response.strip()
    return topic if topic else None


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
        item = load_func_or_item() if callable(load_func_or_item) else load_func_or_item

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
        item = load_func_or_item() if callable(load_func_or_item) else load_func_or_item

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
        item = load_func_or_item() if callable(load_func_or_item) else load_func_or_item

        content = item.get("content", "")
        genre = item.get("genre", "other")
        topic = item.get("topic", "")
        # Check for review_reason in item or in metadata (for review path)
        review_reason = item.get("review_reason")
        if not review_reason and "metadata" in item:
            review_reason = item["metadata"].get("review_reason")

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
def log_genre_distribution(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> dict[str, dict]:
    """Log genre distribution statistics.

    Args:
        partitioned_input: PartitionedDataset-style input (dict of callables)
        params: Pipeline parameters

    Returns:
        The input classified_items unchanged (for pipeline chaining)

    Genre distribution logging:
    - Count items per genre
    - Calculate percentages
    - Log in alphabetical order
    - Handle empty input gracefully
    """
    # Load all items first
    classified_items = {}
    for key, load_func_or_item in partitioned_input.items():
        # Handle both callable (real pipeline) and dict (memory dataset in tests)
        item = load_func_or_item() if callable(load_func_or_item) else load_func_or_item
        classified_items[key] = item

    if not classified_items:
        logger.info("Genre distribution: No items to process")
        return classified_items

    # Count genres
    genre_counts = {}
    for _item_id, item in classified_items.items():
        genre = item.get("genre", "other")
        genre_counts[genre] = genre_counts.get(genre, 0) + 1

    total = sum(genre_counts.values())

    # Log distribution
    lines = ["Genre distribution:"]
    for genre, count in sorted(genre_counts.items()):
        percentage = (count / total) * 100
        lines.append(f"  {genre}: {count} ({percentage:.1f}%)")

    logger.info("\n".join(lines))

    return classified_items


def _suggest_new_genres_via_llm(other_items: list[dict], params: dict) -> list[dict]:
    """Suggest new genres for other-classified items via LLM.

    Args:
        other_items: List of items with genre="other"
        params: Parameters dict with ollama settings

    Returns:
        list[dict]: List of GenreSuggestion dicts with structure:
            {
                "suggested_genre": str,
                "suggested_description": str,
                "sample_titles": list[str],
                "content_count": int,
            }
        Returns empty list on error or if no suggestions found.
    """
    if not other_items:
        return []

    config = get_ollama_config(params, "extract_topic_and_genre")

    # Collect titles and content samples for LLM analysis
    titles = []
    for item in other_items[:20]:  # Limit to first 20 for analysis
        metadata = item.get("metadata", {})
        title = metadata.get("title", "無題")
        titles.append(title)

    titles_text = "\n".join(f"- {t}" for t in titles)

    # Build prompt to suggest new genres
    system_prompt = """あなたはコンテンツ分類の専門家です。"other" に分類されたコンテンツのタイトルを分析し、新しいジャンルを提案してください。

複数の共通パターンがある場合は複数のジャンルを提案してください（最大3件）。
各提案には以下を含めてください:
- suggested_genre: ジャンル名（小文字英字、例: cooking, sports）
- suggested_description: ジャンルの説明（日本語、例: 料理/レシピ/食材）
- sample_titles: 該当するタイトルの例（最大5件）
- content_count: 該当するコンテンツの推定数

JSON配列形式で回答してください:
[
  {
    "suggested_genre": "ジャンル名",
    "suggested_description": "説明",
    "sample_titles": ["タイトル1", "タイトル2"],
    "content_count": 推定数
  }
]

明確なパターンが見つからない場合は空の配列 [] を返してください。"""

    user_message = f"""以下は "other" に分類されたコンテンツのタイトル一覧です:

{titles_text}

新しいジャンルを提案してください。"""

    # Call Ollama API
    response, error = call_ollama(
        system_prompt,
        user_message,
        model=config.model,
        base_url=config.base_url,
        timeout=config.timeout,
        temperature=config.temperature,
        num_predict=config.num_predict,
    )

    if error:
        logger.warning(f"Failed to suggest genres via LLM: {error}")
        return []

    # Parse JSON response
    import json

    try:
        suggestions = json.loads(response.strip())
        if not isinstance(suggestions, list):
            logger.warning("LLM response is not a list, returning empty suggestions")
            return []
        return suggestions
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
        return []


def _generate_suggestions_markdown(suggestions: list[dict], other_count: int) -> str:
    """Generate markdown report from genre suggestions.

    Args:
        suggestions: List of GenreSuggestion dicts
        other_count: Total count of items with genre="other"

    Returns:
        str: Markdown formatted report
    """
    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# ジャンル提案レポート",
        "",
        f"**生成日時**: {now}",
        f"**other 分類数**: {other_count}件",
        f"**提案数**: {len(suggestions)}件",
        "",
        "---",
        "",
    ]

    if not suggestions:
        lines.extend(
            [
                "## 提案なし",
                "",
                "明確なパターンが見つからなかったため、新ジャンルの提案はありません。",
            ]
        )
        return "\n".join(lines)

    for idx, suggestion in enumerate(suggestions, start=1):
        genre = suggestion.get("suggested_genre", "unknown")
        description = suggestion.get("suggested_description", "")
        sample_titles = suggestion.get("sample_titles", [])
        content_count = suggestion.get("content_count", 0)

        lines.extend(
            [
                f"## 提案 {idx}: {genre}",
                "",
                f"**Description**: {description}",
                "",
                f"**該当コンテンツ** ({content_count}件):",
            ]
        )

        for title in sample_titles[:5]:  # Max 5 titles
            lines.append(f"- {title}")

        lines.extend(
            [
                "",
                "**設定への追加例**:",
                "```yaml",
                f"{genre}:",
                '  vault: "適切なVault名"',
                f'  description: "{description}"',
                "```",
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines)


@timed_node
def analyze_other_genres(
    partitioned_input: dict[str, Callable],
    params: dict,
) -> str:
    """Analyze other-classified items and suggest new genres if needed.

    Args:
        partitioned_input: PartitionedDataset-style input (dict of callables)
        params: Parameters dict with ollama settings

    Returns:
        str: Markdown report of genre suggestions

    Analysis logic:
    - Count items with genre="other"
    - If >= 5: call LLM to suggest new genres, generate report
    - If < 5: return "no suggestions" message
    - Write report to data/07_model_output/genre_suggestions.md
    """
    # Load all items and count "other" items
    other_items = []
    for _key, load_func_or_item in partitioned_input.items():
        # Handle both callable (real pipeline) and dict (memory dataset in tests)
        item = load_func_or_item() if callable(load_func_or_item) else load_func_or_item

        if item.get("genre") == "other":
            other_items.append(item)

    other_count = len(other_items)

    # Check threshold
    if other_count < 5:
        logger.info(f"other 分類が {other_count} 件のため、ジャンル提案をスキップします（5件未満）")
        return (
            _generate_suggestions_markdown([], other_count)
            + "\n\nother 分類が5件未満のため、新ジャンルの提案はありません。"
        )

    # Suggest new genres via LLM
    logger.info(f"other 分類が {other_count} 件あります。LLM による新ジャンル提案を実行します。")
    suggestions = _suggest_new_genres_via_llm(other_items, params)

    # Generate markdown report
    report = _generate_suggestions_markdown(suggestions, other_count)

    # Write report to file
    import os

    output_dir = "data/07_model_output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "genre_suggestions.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info(f"ジャンル提案レポートを {output_path} に出力しました。")

    return report
